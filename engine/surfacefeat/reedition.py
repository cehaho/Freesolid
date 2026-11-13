"""Réédition de ce qu'une surface prend : l'esquisse du contour d'une
surface plane, la surface d'un décalage ou d'un épaississement, le bord
d'un prolongement, les arêtes d'un congé, les deux formes d'une courbe
d'intersection, l'esquisse et la face d'une courbe projetée, l'outil et
la partie gardée d'un ajustement, le contour d'une surface radiée, la
surface d'une forme libre.

Mixin de ``Kernel``. Pas d'import FreeCAD au niveau du module.
"""


class SurfaceReeditMixin:
    """``set_params`` des surfaces dont la source se re-choisit."""

    #: Clés de ``set_params`` par genre de surface à source re-choisie.
    _SURFACE_PICK_KEYS = {
        "planar": ("sketch",),
        "extend": ("source", "edge", "distance"),
        "fillet": ("source", "edges", "radius"),
        "intersection": ("first", "second", "body"),
        "project": ("sketch", "surface", "face"),
        "trim": ("source", "tool", "point"),
        "radiate": ("boundary", "distance"),
        "freeform": ("source", "pushes", "radius", "keep_edges", "moves",
                     "grid"),
        "flatten": ("surface", "face"),
    }

    def _surface_pick_kind(self, obj):
        """Genre de surface dont ``set_params`` re-choisit ce qu'elle prend
        (``_set_surface_params``), ou None. Le décalage et l'épaississement
        passent par les cotes, avec leur clé ``source``."""
        if not self._is_surface_obj(obj):
            return None
        if obj.TypeId == "Part::Face":
            return "planar"
        if (obj.TypeId == "Surface::Extend"
                and not getattr(obj, "FreeSolidUntrim", 0)):
            return "extend"
        if obj.TypeId == "Part::Fillet":
            return "fillet"
        if obj.TypeId == "Part::Section":
            return "intersection"
        if obj.TypeId == "Part::ProjectOnSurface":
            return "project"
        if getattr(obj, "FreeSolidKind", "") == "trim":
            return "trim"
        if getattr(obj, "FreeSolidFreesource", ""):
            return "freeform"
        if getattr(obj, "FreeSolidFlatsource", ""):
            return "flatten"
        return None

    def _refuse_later_source(self, obj, source):
        """Une source re-choisie vient avant ``obj`` et n'en dépend pas."""
        from engine.kernel import KernelError
        if source is obj or obj in (source.OutListRecursive or ()):
            raise KernelError("{} dépend de {}".format(source.Label,
                                                       obj.Label))
        order = self._tree_order()
        if order.get(source.Name, -1) > order.get(obj.Name, -1):
            raise KernelError("{} vient après {}".format(source.Label,
                                                         obj.Label))

    def _picked_surface(self, obj, name, faces=True):
        """La surface ``name`` re-choisie comme source de ``obj``."""
        from engine.kernel import KernelError
        source = self._get_surface(name)
        if faces and not source.Shape.Faces:
            raise KernelError("choisissez une surface, pas une courbe")
        self._refuse_later_source(obj, source)
        return source

    def _set_surface_params(self, obj, values, kind=None):
        """``set_params`` d'une surface à source re-choisie : tout ou rien,
        la surface d'avant revient sur refus. ``kind`` : le genre, quand
        seule une clé de ``values`` l'aiguille ici (le contour d'une
        surface radiée, dont la distance garde la voie des cotes)."""
        from engine.kernel import KernelError, _explain
        kind = kind or self._surface_pick_kind(obj)
        for key in values:
            if key not in self._SURFACE_PICK_KEYS[kind]:
                raise KernelError("propriété non éditable : {}".format(key))
        saved = self._surface_saved(obj, kind)
        try:
            if kind == "planar":
                if "sketch" in values:
                    sketch = self._surface_source(values["sketch"])
                    self._refuse_later_source(obj, sketch)
                    obj.Sources = [sketch]
            elif kind == "extend":
                self._set_extend_params(obj, values)
            elif kind == "fillet":
                self._set_surface_fillet_params(obj, values)
            elif kind == "intersection":
                self._set_intersection_params(obj, values)
            elif kind == "trim":
                self._set_trim_params(obj, values)
            elif kind == "radiate":
                self._set_radiate_params(obj, values)
            elif kind == "freeform":
                self._set_freeform_params(obj, values)
            elif kind == "flatten":
                self._set_flatten_params(obj, values)
            else:
                self._set_projection_params(obj, values)
            self._recompute()
            if kind in ("intersection", "project") and not obj.Shape.Edges:
                raise KernelError("les deux formes ne se coupent pas"
                                  if kind == "intersection" else
                                  "la projection ne touche pas la face")
        except Exception as exc:  # noqa: BLE001
            for owner, prop, value in saved:
                setattr(owner, prop, value)
            try:
                self._recompute()
            except KernelError:
                pass  # l'état d'avant était sain : ne pas masquer exc
            message = (str(exc) if isinstance(exc, KernelError)
                       else _explain(exc))
            raise KernelError(
                "{} — la pièce n'a pas été modifiée".format(message))
        return self.get_tree()

    @staticmethod
    def _surface_saved(obj, kind):
        """Ce qu'il faut remettre sur refus : (objet, propriété, valeur)."""
        if kind == "trim":
            slicer = obj.Base
            return [(slicer, "Base", slicer.Base),
                    (slicer, "Tools", list(slicer.Tools)),
                    (obj, "items", obj.items)]
        if kind == "radiate":
            return [(obj.Source, "Support", list(obj.Source.Support)),
                    (obj, "Value", obj.Value)]
        if kind in ("freeform", "flatten"):
            stem = "FreeSolidFree" if kind == "freeform" else "FreeSolidFlat"
            return [(obj, "Shape", obj.Shape.copy())] + [
                (obj, prop, getattr(obj, prop)) for prop in obj.PropertiesList
                if prop.startswith(stem)]
        props = {
            "planar": ("Sources",),
            "extend": ("Face", "ExtendUNeg", "ExtendUPos", "ExtendVNeg",
                       "ExtendVPos", "FreeSolidDistance", "FreeSolidEdge"),
            "fillet": ("Base", "Edges"),
            "intersection": ("Base", "Tool"),
            "project": ("SupportFace", "Projection", "Direction"),
        }[kind]
        return [(obj, prop, getattr(obj, prop)) for prop in props
                if prop in obj.PropertiesList]

    def _set_extend_params(self, obj, values):
        """Prolongement : sa surface (``source``), son bord (``edge``,
        base 0 ; None pour tous les bords) et sa distance. Une autre
        surface sans bord dit : tous ses bords."""
        src = obj.Face[0]
        if "source" in values:
            src = self._picked_surface(obj, values["source"])
        distance = values.get("distance",
                              float(getattr(obj, "FreeSolidDistance", 0)))
        stamped = int(getattr(obj, "FreeSolidEdge", 0) or 0)
        edge = (values["edge"] if "edge" in values
                else None if "source" in values
                else stamped - 1 if stamped else None)
        self._apply_extend(obj, src, *self._extend_plan(src, distance, edge))

    def _set_surface_fillet_params(self, obj, values):
        """Congé de surface : sa surface (``source``), ses arêtes
        (``edges``, base 0, entre deux faces) et son rayon. Une autre
        surface demande ses arêtes."""
        from engine.kernel import KernelError
        src = obj.Base
        if "source" in values:
            src = self._picked_surface(obj, values["source"])
            if "edges" not in values:
                raise KernelError("cliquez les arêtes à arrondir")
        current = list(obj.Edges or ())
        radius = values.get("radius",
                            float(current[0][1]) if current else 0.0)
        edges = values.get("edges", [int(e[0]) - 1 for e in current])
        radius, picked = self._surface_fillet_plan(src, edges, radius)
        obj.Base = src
        obj.Edges = [(e + 1, radius, radius) for e in picked]

    def _set_offset_source(self, obj, name, previous):
        """Surface décalée ou épaississement : sa surface re-choisie
        (``source``). Entre dans ``previous``, pour le refus."""
        source = self._picked_surface(obj, name, faces=not obj.Fill)
        previous.append(("Source", None, obj.Source))
        obj.Source = source

    def _set_intersection_params(self, obj, values):
        """Courbe d'intersection : sa première surface (``first``), la
        seconde (``second``) ou le solide du corps actif (``body``)."""
        from engine.kernel import KernelError
        base, tool = obj.Base, obj.Tool
        if "first" in values:
            base = self._picked_surface(obj, values["first"], faces=False)
        solid = bool(values.get("body", tool.TypeId == "PartDesign::Body"))
        if solid:
            tool = self._require_body()
            if not getattr(tool, "Shape", None) or not tool.Shape.Solids:
                raise KernelError("le corps n'a pas encore de solide")
        elif "second" in values:
            tool = self._picked_surface(obj, values["second"], faces=False)
        elif tool.TypeId == "PartDesign::Body":
            raise KernelError("choisissez une seconde surface")
        if tool is base:
            raise KernelError("choisissez deux surfaces différentes")
        obj.Base = base
        obj.Tool = tool

    def _set_flatten_params(self, obj, values):
        """Patron à plat : sa surface (``surface``) et sa face (``face``,
        base 0), comme à la création. Une autre surface sans face dit :
        sa première face."""
        from engine.kernel import KernelError
        stamps = self._frozen_stamps(obj)
        src = (self._picked_surface(obj, values["surface"])
               if "surface" in values
               else self._get_surface(stamps["flatsource"]))
        face = values.get("face")
        if face is None:
            face = (self._followed_flat_face(src.Shape, stamps)
                    if src.Name == stamps.get("flatsource") else 0)
        if type(face) is not int:
            raise KernelError("face inconnue : {}".format(face))
        target = self._source_face(src.Shape, face)
        obj.Shape = self._flat_shape(src.Shape, face)
        anchor = self._face_anchor(target)
        self._stamp(obj, flatsource=src.Name, flatface=face,
                    flatanchor="%.9g,%.9g,%.9g" % (anchor.x, anchor.y,
                                                   anchor.z))

    def _set_projection_params(self, obj, values):
        """Courbe projetée : son esquisse (``sketch``), la surface et la
        face où elle se projette (``surface``, ``face`` base 0). La
        direction suit la normale de l'esquisse, comme à la création."""
        from engine.kernel import KernelError
        App = self._app()
        sketch = next(iter(self._surface_sketch_objects(obj)), None)
        if "sketch" in values:
            sketch = self._get_sketch(str(values["sketch"]))
            self._refuse_later_source(obj, sketch)
        if sketch is None:
            raise KernelError("cliquez l'esquisse à projeter")
        support = obj.SupportFace
        src = support[0] if support else None
        subs = support[1] if support else ()
        face = int(subs[0][4:]) - 1 if subs else 0
        if "surface" in values:
            src = self._picked_surface(obj, values["surface"])
            face = 0
        if "face" in values:
            face = int(values["face"])
        if src is None:
            raise KernelError("projeter demande une surface, pas une courbe")
        if face < 0 or face >= len(src.Shape.Faces):
            raise KernelError("face inconnue : {}".format(face))
        normal = sketch.Placement.Rotation.multVec(App.Vector(0, 0, 1))
        obj.SupportFace = (src, ["Face%d" % (face + 1)])
        obj.Projection = [sketch]
        obj.Direction = normal * -1

    def _set_trim_params(self, obj, values):
        """Ajustement : la surface ajustée (``source``), l'outil
        (``tool``), la partie gardée, la plus proche de ``point``. Sans
        point, la partie gardée reste du même côté : la plus proche de
        celle d'avant."""
        from engine.kernel import KernelError
        slicer = obj.Base
        src, knife = slicer.Base, slicer.Tools[0]
        if "source" in values:
            src = self._picked_surface(obj, values["source"])
        if "tool" in values:
            knife = self._picked_surface(obj, values["tool"])
        if src is knife:
            raise KernelError("la surface et l'outil doivent être "
                              "différents")
        point = values.get("point") or self._trim_point(obj)
        pieces = self._trim_pieces(src.Shape, knife.Shape)
        if len(pieces) < 2:
            raise KernelError("l'outil ne coupe pas la surface")
        slicer.Base = src
        slicer.Tools = [knife]
        obj.items = str(self._nearest_piece(pieces, point))

    @staticmethod
    def _trim_point(obj):
        """Un point de la partie qu'un ajustement garde : celui de sa
        première face le plus proche de son centre (sur la face, même
        creuse ou en L)."""
        import Part
        faces = obj.Shape.Faces
        if not faces:
            return None
        center = Part.Vertex(faces[0].CenterOfMass)
        point = faces[0].distToShape(center)[1][0][0]
        return [point.x, point.y, point.z]

    def _set_radiate_params(self, obj, values):
        """Surface radiée : son contour (``boundary``, comme à la
        création : arêtes de surface, de courbe, du solide, esquisses
        entières) et sa distance signée."""
        from engine.kernel import KernelError
        if "distance" in values:
            distance = float(values["distance"])
            if distance == 0:
                raise KernelError("la distance ne peut pas être nulle")
            obj.Value = distance
        if "boundary" not in values:
            return
        groups, order = {}, []
        for linked, sub in self._boundary_links(values["boundary"]):
            if linked.Name not in groups:
                if linked.TypeId != "PartDesign::Body":
                    self._refuse_later_source(obj, linked)
                groups[linked.Name] = (linked, [])
                order.append(linked.Name)
            groups[linked.Name][1].append(sub)
        obj.Source.Support = [(groups[n][0], tuple(groups[n][1]))
                              for n in order]

    def _set_freeform_params(self, obj, values):
        """Forme libre : sa surface (``source`` ; les points poussés s'y
        reprojettent, les pôles déplacés gardent leurs indices), et ce que
        son panneau règle : points poussés, rayon, bords fixes — ou pôles
        déplacés et grille."""
        from engine.kernel import KernelError
        poles = bool(getattr(obj, "FreeSolidFreemoves", ""))
        allowed = (("source", "moves", "grid") if poles
                   else ("source", "pushes", "radius", "keep_edges"))
        for key in values:
            if key not in allowed:
                raise KernelError("propriété non éditable : {}".format(key))
        if "source" in values:
            src = self._picked_surface(obj, values["source"])
            if poles and src.Name != obj.FreeSolidFreesource:
                # Les repères décrivaient l'autre surface : les indices
                # restent, et de nouveaux repères seront pris.
                self._stamp(obj, freeanchors="")
            self._stamp(obj, freesource=src.Name)
        if poles:
            self._apply_freeform_edit(obj, moves=values.get("moves"),
                                      grid=values.get("grid"))
            return
        self._apply_freeform_edit(
            obj, radius=values.get("radius",
                                   float(obj.FreeSolidFreeradius)),
            pushes=values.get("pushes"),
            keep_edges=values.get("keep_edges"))
