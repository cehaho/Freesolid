"""Réédition de ce qu'une surface prend : l'esquisse du contour d'une
surface plane, la surface d'un décalage ou d'un épaississement, le bord
d'un prolongement, les arêtes d'un congé, les deux formes d'une courbe
d'intersection, l'esquisse et la face d'une courbe projetée, l'outil et
la partie gardée d'un ajustement, le contour d'une surface radiée, la
surface d'une forme libre, les profils d'une surface lissée, le profil et
la trajectoire d'une balayée, les courbes d'une réglée, d'une frontière,
d'un remplissage ou d'une courbe composite, la surface et la courbe d'une
division, la face d'un désajustement, les faces supprimées d'une surface.

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
        "loft": ("profiles",),
        "sweep": ("profile", "spine"),
        "ruled": ("boundary",),
        "boundary": ("boundary",),
        "fill": ("boundary",),
        "composite": ("boundary",),
        "split": ("source", "tool"),
        "untrim": ("source", "face"),
        "deleteface": ("source", "faces"),
    }

    #: Genres re-choisis par leurs propriétés de liens, sans autre réglage.
    _SURFACE_LINK_KINDS = {
        "Part::Loft": "loft",
        "Part::Sweep": "sweep",
        "Part::RuledSurface": "ruled",
        "Surface::GeomFillSurface": "boundary",
        "Surface::Filling": "fill",
    }

    def _surface_pick_kind(self, obj):
        """Genre de surface dont ``set_params`` re-choisit ce qu'elle prend
        (``_set_surface_params``), ou None. Le décalage et l'épaississement
        passent par les cotes, avec leur clé ``source``."""
        if not self._is_surface_obj(obj):
            return None
        if obj.TypeId == "Part::Face":
            return "planar"
        if obj.TypeId == "Surface::Extend":
            return "untrim" if getattr(obj, "FreeSolidUntrim", 0) else "extend"
        if obj.TypeId in self._SURFACE_LINK_KINDS:
            return self._SURFACE_LINK_KINDS[obj.TypeId]
        if getattr(obj, "FreeSolidCapedges", ""):
            return "fill"
        if getattr(obj, "FreeSolidComposite", False):
            return "composite"
        if getattr(obj, "FreeSolidKind", "") in ("split", "deleteface"):
            return obj.FreeSolidKind
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
            elif kind in ("loft", "sweep", "ruled", "boundary", "composite"):
                self._set_linked_surface_params(obj, kind, values)
            elif kind == "fill":
                self._set_fill_params(obj, values)
            elif kind == "split":
                self._set_split_params(obj, values)
            elif kind in ("untrim", "deleteface"):
                self._set_face_source_params(obj, kind, values)
            else:
                self._set_projection_params(obj, values)
            self._recompute()
            if kind in ("intersection", "project") and not obj.Shape.Edges:
                raise KernelError("les deux formes ne se coupent pas"
                                  if kind == "intersection" else
                                  "la projection ne touche pas la face")
            self._check_rechosen(obj, kind)
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
        if kind == "fill" and getattr(obj, "FreeSolidCapedges", ""):
            return [(obj, "Shape", obj.Shape.copy()),
                    (obj, "FreeSolidCapedges", obj.FreeSolidCapedges)]
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
            "loft": ("Sections",),
            "sweep": ("Sections", "Spine"),
            "ruled": ("Curve1", "Curve2"),
            "boundary": ("BoundaryList",),
            "fill": ("BoundaryEdges", "BoundaryFaces", "BoundaryOrder"),
            "composite": ("Support",),
            "split": ("Base", "Tools"),
            "untrim": ("Face",),
            "deleteface": ("Support",),
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

    def _rechosen_edges(self, obj, boundary):
        """Les liens d'un contour re-choisi (``boundary``, comme à la
        création) ; chaque forme vient avant ``obj`` et n'en dépend pas."""
        links = self._boundary_links(boundary)
        for linked, _ in links:
            if linked.TypeId != "PartDesign::Body":
                self._refuse_later_source(obj, linked)
        return links

    def _set_linked_surface_params(self, obj, kind, values):
        """Surfaces lissée (``profiles``), balayée (``profile``,
        ``spine``), réglée et frontière (``boundary``), courbe composite
        (``boundary``) : ce qu'elles prennent, re-choisi comme à la
        création."""
        from engine.kernel import KernelError
        if kind == "loft":
            names = [str(name) for name in values["profiles"] or ()]
            if len(names) < 2:
                raise KernelError("une surface lissée demande au moins deux "
                                  "profils")
            if len(set(names)) != len(names):
                raise KernelError("lissage : un profil ne se prend qu'une "
                                  "fois")
            sections = []
            for name in names:
                sketch = self._get_sketch(name)
                if not sketch.Shape.Edges:
                    raise KernelError("esquisse vide : {}".format(name))
                self._refuse_later_source(obj, sketch)
                sections.append(sketch)
            obj.Sections = sections
        elif kind == "sweep":
            section = obj.Sections[0]
            path = obj.Spine[0] if obj.Spine else None
            if "profile" in values:
                section = self._get_sketch(str(values["profile"]))
                self._refuse_later_source(obj, section)
            if "spine" in values:
                path = self._require_doc().getObject(str(values["spine"]))
                if (path is None or not getattr(path, "Shape", None)
                        or not path.Shape.Edges or path.Shape.Faces):
                    raise KernelError(
                        "trajectoire inconnue : {} (esquisse ou courbe "
                        "3D)".format(values["spine"]))
                self._refuse_later_source(obj, path)
            if path is None or section.Name == path.Name:
                raise KernelError("profil et trajectoire doivent être "
                                  "différents")
            obj.Sections = [section]
            obj.Spine = (path, ["Edge%d" % (i + 1)
                                for i in range(len(path.Shape.Edges))])
        else:
            links = self._rechosen_edges(obj, values["boundary"])
            if kind == "ruled":
                if len(links) != 2:
                    raise KernelError("une surface réglée relie exactement "
                                      "deux courbes")
                obj.Curve1 = (links[0][0], [links[0][1]])
                obj.Curve2 = (links[1][0], [links[1][1]])
            elif kind == "boundary":
                if not 2 <= len(links) <= 4:
                    raise KernelError("une surface frontière demande deux à "
                                      "quatre courbes")
                obj.BoundaryList = links
            else:
                groups, order = {}, []
                for linked, sub in links:
                    if linked.Name not in groups:
                        groups[linked.Name] = (linked, [])
                        order.append(linked.Name)
                    groups[linked.Name][1].append(sub)
                obj.Support = [(groups[n][0], tuple(groups[n][1]))
                               for n in order]

    def _check_rechosen(self, obj, kind):
        """Après le recalcul, ce que la création vérifiait aussi."""
        from engine.kernel import KernelError
        import Part
        if kind == "composite":
            edges = obj.Shape.Edges
            if not edges:
                raise KernelError("aucune arête retenue")
            if len(Part.sortEdges(list(edges))) != 1:
                raise KernelError("les arêtes ne se suivent pas bout à "
                                  "bout")
        elif kind == "split":
            if len(obj.Shape.Faces) <= len(obj.Base.Shape.Faces):
                raise KernelError("la courbe ne scinde pas la surface — "
                                  "elle doit être posée dessus, d'un bord à "
                                  "l'autre ou fermée")
        elif kind in ("loft", "sweep", "ruled", "boundary"):
            if obj.Shape.isNull() or not obj.Shape.Faces:
                raise KernelError("aucune surface produite")

    def _set_fill_params(self, obj, values):
        """Surface de remplissage : son contour (``boundary``), comme à la
        création. La tangence reste ce qu'elle était : un bouchon tangent
        se refait sur les faces que bordent les nouvelles arêtes."""
        from engine.kernel import KernelError
        links = self._rechosen_edges(obj, values["boundary"])
        if getattr(obj, "FreeSolidCapedges", ""):
            faces = [self._adjacent_face(o, sub) for o, sub in links]
            if not all(faces):
                raise KernelError("bouchon tangent : chaque arête doit "
                                  "border une face")
            spec = ";".join(":".join((o.Name, sub, face))
                            for (o, sub), face in zip(links, faces))
            obj.Shape = self._cap_shape(spec)
            self._stamp(obj, capedges=spec)
            return
        tangent = any(obj.BoundaryOrder or ())
        faces = [self._adjacent_face(o, sub) if tangent else ""
                 for o, sub in links]
        closed = any(o.Shape.Edges[int(sub[4:]) - 1].isClosed()
                     for o, sub in links)
        if tangent and closed and all(faces):
            raise KernelError("remplissage tangent : une arête fermée "
                              "demande un bouchon — refaites la surface")
        # Un objet auxiliaire par arête fermée, lié par ses deux moitiés.
        old = list({o.Name: o for o, _ in self._link_pairs(obj.BoundaryEdges)
                    if getattr(o, "FreeSolidHalvessource", "")}.values())
        before = (list(obj.BoundaryEdges), list(obj.BoundaryFaces or ()),
                  list(obj.BoundaryOrder or ()))
        links, faces = self._split_closed_links(
            links, [""] * len(links) if closed else faces)
        made = list({o.Name: o for o, _ in links
                     if getattr(o, "FreeSolidHalvessource", "")
                     and o not in old}.values())
        doc = self._require_doc()
        try:
            obj.BoundaryEdges = links
            obj.BoundaryFaces = faces if any(faces) else []
            obj.BoundaryOrder = ([1 if face else 0 for face in faces]
                                 if any(faces) else [])
            self._recompute()
            # Vérifié avant de défaire les anciennes moitiés d'arêtes : un
            # refus les remet en place.
            if obj.Shape.isNull() or not obj.Shape.Faces:
                raise KernelError("aucune surface produite")
        except Exception:
            obj.BoundaryEdges, obj.BoundaryFaces, obj.BoundaryOrder = before
            for helper in made:
                doc.removeObject(helper.Name)
            raise
        used = {o.Name for o, _ in links}
        for helper in old:
            if helper.Name not in used:
                doc.removeObject(helper.Name)

    @staticmethod
    def _link_pairs(links):
        """``[(objet, "EdgeN"), …]`` d'une liste de liens FreeCAD."""
        pairs = []
        for link in links or ():
            if not link or link[0] is None:
                continue
            subs = link[1] if len(link) > 1 else ()
            for sub in [subs] if isinstance(subs, str) else subs or ():
                pairs.append((link[0], sub))
        return pairs

    def _set_split_params(self, obj, values):
        """Diviser : sa surface (``source``) et sa courbe outil
        (``tool``)."""
        from engine.kernel import KernelError
        src = obj.Base
        tool = obj.Tools[0] if obj.Tools else None
        if "source" in values:
            src = self._picked_surface(obj, values["source"])
        if "tool" in values:
            tool = self._require_doc().getObject(str(values["tool"]))
            if tool is None or not getattr(tool, "Shape", None):
                raise KernelError("objet inconnu : {}".format(values["tool"]))
            self._refuse_later_source(obj, tool)
        if tool is None or tool.Name == src.Name:
            raise KernelError("la surface et l'outil doivent être différents")
        obj.Base = src
        obj.Tools = [tool]

    def _set_face_source_params(self, obj, kind, values):
        """Annuler l'ajustement (``source``, ``face``) et Supprimer la face
        d'une surface (``source``, ``faces``) : la surface et ses faces,
        base 0. Une autre surface demande ses faces."""
        from engine.kernel import KernelError
        current = obj.Face[0] if kind == "untrim" else obj.Support[0][0]
        src = current
        if "source" in values:
            src = self._picked_surface(obj, values["source"])
        count = len(src.Shape.Faces)
        if kind == "untrim":
            face = int(values.get("face", 0 if src is not current
                                  else int(obj.Face[1][0][4:]) - 1))
            if face < 0 or face >= count:
                raise KernelError("face inconnue : {}".format(face))
            obj.Face = (src, ["Face%d" % (face + 1)])
            return
        if "faces" not in values and src is not current:
            raise KernelError("cliquez les faces à supprimer")
        drop = ({int(f) for f in values["faces"] or ()} if "faces" in values
                else {i for i in range(count)} - {
                    int(sub[4:]) - 1 for sub in obj.Support[0][1]})
        if not drop:
            raise KernelError("cliquez les faces à supprimer")
        if any(f < 0 or f >= count for f in drop):
            raise KernelError("face inconnue : {}".format(sorted(drop)))
        keep = ["Face%d" % (i + 1) for i in range(count) if i not in drop]
        if not keep:
            raise KernelError("toutes les faces seraient supprimées")
        obj.Support = [(src, tuple(keep))]
