"""Réédition de ce qu'une surface prend : l'esquisse du contour d'une
surface plane, la surface d'un décalage ou d'un épaississement, le bord
d'un prolongement, les arêtes d'un congé.

Mixin de ``Kernel``. Pas d'import FreeCAD au niveau du module.
"""


class SurfaceReeditMixin:
    """``set_params`` des surfaces dont la source se re-choisit."""

    #: Clés de ``set_params`` par genre de surface à source re-choisie.
    _SURFACE_PICK_KEYS = {
        "planar": ("sketch",),
        "extend": ("source", "edge", "distance"),
        "fillet": ("source", "edges", "radius"),
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

    def _set_surface_params(self, obj, values):
        """``set_params`` d'une surface à source re-choisie : tout ou rien,
        la surface d'avant revient sur refus."""
        from engine.kernel import KernelError, _explain
        kind = self._surface_pick_kind(obj)
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
            else:
                self._set_surface_fillet_params(obj, values)
            self._recompute()
        except Exception as exc:  # noqa: BLE001
            for prop, value in saved:
                setattr(obj, prop, value)
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
        """Ce qu'il faut remettre sur refus."""
        props = {
            "planar": ("Sources",),
            "extend": ("Face", "ExtendUNeg", "ExtendUPos", "ExtendVNeg",
                       "ExtendVPos", "FreeSolidDistance", "FreeSolidEdge"),
            "fillet": ("Base", "Edges"),
        }[kind]
        return [(prop, getattr(obj, prop)) for prop in props
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
