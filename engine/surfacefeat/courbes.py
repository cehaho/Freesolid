"""Courbes : intersection, projection, hélice, composite ; surface
radiale.

Sous-mixin de ``SurfaceMixin`` (voir ``__init__.py``). Pas d'import
FreeCAD au niveau du module : les méthodes importent le noyau à l'appel.
"""


class CurveMixin:
    def curve_intersection(self, first, second=None, body=False):
        """Courbe d'intersection de deux surfaces — ou d'une surface et du
        solide (``body``)."""
        from engine.kernel import KernelError
        doc = self._require_doc()
        base = self._get_surface(first)
        if body:
            tool = self._require_body()
            if not getattr(tool, "Shape", None) or not tool.Shape.Solids:
                raise KernelError("le corps n'a pas encore de solide")
        else:
            if second is None:
                raise KernelError("choisissez une seconde surface")
            tool = self._get_surface(second)
            if tool.Name == base.Name:
                raise KernelError("choisissez deux surfaces différentes")

        def configure(obj):
            obj.Base = base
            obj.Tool = tool
            obj.Approximation = False
            doc.recompute()
            if not obj.Shape.Edges:
                raise KernelError("les deux formes ne se coupent pas")

        return self._add_part_surface(
            "Part::Section", "Courbe d'intersection", configure)

    def curve_project(self, sketch, surface, face=0):
        """Courbe projetée : les traits d'une esquisse projetés sur une
        face de surface, selon la normale de l'esquisse."""
        from engine.kernel import KernelError
        sk = self._get_sketch(str(sketch))
        src = self._get_surface(surface)
        faces = src.Shape.Faces
        face = int(face)
        if not faces:
            raise KernelError("projeter demande une surface, pas une courbe")
        if face < 0 or face >= len(faces):
            raise KernelError("face inconnue : {}".format(face))
        App = self._app()
        normal = sk.Placement.Rotation.multVec(App.Vector(0, 0, 1))

        def configure(obj):
            obj.SupportFace = (src, ["Face%d" % (face + 1)])
            obj.Projection = [sk]
            obj.Mode = "Edges"
            obj.Direction = normal * -1
            self._recompute()
            if not obj.Shape.Edges:
                raise KernelError("la projection ne touche pas la face")

        return self._add_part_surface(
            "Part::ProjectOnSurface", "Courbe projetée", configure)

    def surface_radiate(self, boundary, distance):
        """Surface radiée : une bande plane qui part d'un contour plan (bords
        du solide, d'une surface, une esquisse), dans son plan."""
        from engine.kernel import (
            KernelError,
            _explain,
        )
        import PartDesign  # noqa: F401 — enregistre le lieur de forme
        doc = self._require_doc()
        distance = float(distance)
        if distance == 0:
            raise KernelError("la distance ne peut pas être nulle")
        links = self._boundary_links(boundary)
        groups, order = {}, []
        for obj, sub in links:
            if obj.Name not in groups:
                groups[obj.Name] = (obj, [])
                order.append(obj.Name)
            groups[obj.Name][1].append(sub)
        binder = doc.addObject("PartDesign::SubShapeBinder", "RadiateEdges")
        self._mark_internal(binder)
        try:
            binder.Support = [(groups[n][0], tuple(groups[n][1]))
                              for n in order]

            def configure(obj):
                obj.Source = binder
                obj.Value = distance
                obj.Join = "Intersection"
                obj.Fill = True

            return self._add_part_surface(
                "Part::Offset2D", "Surface radiée", configure)
        except Exception as exc:  # noqa: BLE001
            try:
                doc.removeObject(binder.Name)
            except Exception:
                pass
            if isinstance(exc, KernelError):
                raise KernelError("{} — le contour doit être plan".format(exc))
            raise KernelError(_explain(exc))

    _HELIX_AXES = {"Z": ((0, 0, 0), 0), "Y": ((1, 0, 0), -90),
                   "X": ((0, 1, 0), 90)}

    def curve_helix(self, pitch, height, radius, angle=0.0, left=False,
                    axis="Z"):
        """Hélice (ou spirale conique avec ``angle``) autour d'un axe
        d'origine — trajectoire de balayage, ressort, filet."""
        from engine.kernel import KernelError
        App = self._app()
        pitch, height, radius = float(pitch), float(height), float(radius)
        if pitch <= 0 or height <= 0 or radius <= 0:
            raise KernelError("pas, hauteur et rayon doivent être positifs")
        if str(axis) not in self._HELIX_AXES:
            raise KernelError("axe inconnu : {}".format(axis))
        turn_axis, degrees = self._HELIX_AXES[str(axis)]

        def configure(obj):
            obj.Pitch = pitch
            obj.Height = height
            obj.Radius = radius
            obj.Angle = float(angle)
            obj.LocalCoord = "Left-handed" if left else "Right-handed"
            obj.Placement = App.Placement(
                App.Vector(0, 0, 0),
                App.Rotation(App.Vector(*turn_axis), degrees))

        return self._add_part_surface("Part::Helix", "Hélice", configure)

    def _helix_curve_spec(self, obj):
        """Ce que la réédition d'une hélice 3D reprend de sa création : son
        axe d'origine (None s'il a été tourné autrement) et son sens."""
        App = self._app()
        rotation = obj.Placement.Rotation
        axis = None
        for token, (turn_axis, degrees) in self._HELIX_AXES.items():
            wanted = App.Rotation(App.Vector(*turn_axis), degrees)
            if abs((wanted.inverted() * rotation).Angle) < 1e-7:
                axis = token
                break
        return {"kind": "helix", "axis": axis,
                "left": str(obj.LocalCoord) == "Left-handed"}

    @staticmethod
    def _check_helix_curve_values(values):
        """Pas, hauteur et rayon d'une hélice 3D rééditée : positifs, comme
        à la création. Une expression passe (le moteur d'expressions la
        juge)."""
        from engine.kernel import KernelError, parse_user_number
        for key, value in values.items():
            if str(key).lower() not in ("pitch", "height", "radius"):
                continue
            if isinstance(value, bool):
                continue
            number = (float(value) if isinstance(value, (int, float))
                      else parse_user_number(value))
            if number is not None and number <= 0:
                raise KernelError("pas, hauteur et rayon doivent être "
                                  "positifs")

    def _set_helix_curve_params(self, obj, values):
        """``set_params`` d'une hélice 3D : son axe et son sens, comme à la
        création, puis ses cotes par la voie commune — tout ou rien."""
        from engine.kernel import KernelError
        App = self._app()
        axis = values.pop("axis", None)
        left = values.pop("left", None)
        if axis is not None and str(axis) not in self._HELIX_AXES:
            raise KernelError("axe inconnu : {}".format(axis))
        if left is not None and not isinstance(left, bool):
            raise KernelError("{} : booléen attendu".format("left"))
        saved = (obj.Placement.copy(), str(obj.LocalCoord))
        try:
            if axis is not None:
                turn_axis, degrees = self._HELIX_AXES[str(axis)]
                placement = obj.Placement.copy()
                placement.Rotation = App.Rotation(App.Vector(*turn_axis),
                                                  degrees)
                obj.Placement = placement
            if left is not None:
                obj.LocalCoord = "Left-handed" if left else "Right-handed"
            if values:
                return self.set_params(obj.Name, values)
            self._recompute()
        except Exception:
            obj.Placement, obj.LocalCoord = saved
            try:
                self._recompute()
            except KernelError:
                pass  # l'état d'avant était sain : ne pas masquer l'erreur
            raise
        return self.get_tree()

    def curve_composite(self, boundary):
        """Courbe composite : des arêtes et courbes bout à bout réunies en
        une seule trajectoire (lieur de forme paramétrique)."""
        from engine.kernel import (
            KernelError,
            _explain,
        )
        import Part
        import PartDesign  # noqa: F401 — enregistre le lieur de forme
        doc = self._require_doc()
        links = self._boundary_links(boundary)
        groups = {}
        order = []
        for obj, sub in links:
            if obj.Name not in groups:
                groups[obj.Name] = (obj, [])
                order.append(obj.Name)
            groups[obj.Name][1].append(sub)
        binder = doc.addObject("PartDesign::SubShapeBinder", "Surface")
        try:
            binder.addProperty("App::PropertyBool", "FreeSolidComposite",
                               "FreeSolid")
            binder.setEditorMode("FreeSolidComposite", 2)
            binder.FreeSolidComposite = True
            binder.Support = [(groups[n][0], tuple(groups[n][1]))
                              for n in order]
            binder.Label = self._t("Courbe composite")
            self._recompute()
            edges = binder.Shape.Edges
            if not edges:
                raise KernelError("aucune arête retenue")
            # Une seule chaîne connexe, sinon ce n'est pas une trajectoire.
            if len(Part.sortEdges(list(edges))) != 1:
                raise KernelError("les arêtes ne se suivent pas bout à "
                                  "bout")
        except Exception as exc:  # noqa: BLE001
            try:
                doc.removeObject(binder.Name)
            except Exception:
                pass
            if isinstance(exc, KernelError):
                raise
            raise KernelError(_explain(exc))
        return self.get_tree()
