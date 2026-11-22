"""Répétition pilotée par esquisse : les fonctions choisies (la dernière
par défaut) recopiées sur chaque point d'une esquisse — comme dans les
modeleurs courants.

Le point de référence est le centre des fonctions répétées ; chaque copie
s'en déplace jusqu'à un point de l'esquisse, dans le plan de l'esquisse
(une fonction posée sur une face y reste). Un point confondu avec la
référence ne fait pas de copie : l'original y est déjà.

La copie d'une fonction est son outil (``AddSubShape``) : ajouté pour un
bossage, retiré pour un enlèvement. La forme est rangée dans l'historique
comme la nervure (``_commit_frozen``) et recalculée à chaque
reconstruction : elle suit l'esquisse et les fonctions répétées. Les
imports FreeCAD restent dans les méthodes ; ``parse_spec`` et
``format_spec`` sont testées en CI.
"""


def format_spec(sketch, features):
    """« esquisse;fonction1,fonction2 » — rangé sur la forme figée et la
    fonction."""
    return "%s;%s" % (sketch, ",".join(str(name) for name in features))


def parse_spec(spec):
    """(esquisse, [fonctions])."""
    sketch, _, names = str(spec).partition(";")
    return sketch, [name for name in names.split(",") if name]


class SketchPatternMixin:
    """Ops : répétition pilotée par esquisse (création ; la réédition passe
    par ``set_params``)."""

    def _sketch_pattern_points(self, sketch):
        """Les points de l'esquisse, dans le repère de la pièce."""
        from engine.kernel import KernelError
        import FreeCAD
        points = []
        for geo in sketch.Geometry:
            if type(geo).__name__ == "Point":
                points.append(sketch.Placement.multVec(
                    FreeCAD.Vector(geo.X, geo.Y, geo.Z)))
        if not points:
            raise KernelError("l'esquisse n'a aucun point — placez un "
                              "point à chaque copie")
        return points

    def _sketch_pattern_tools(self, names):
        """[(outil, ajout ?)] des fonctions répétées."""
        from engine.bodyscope import is_subtractive_type
        from engine.kernel import KernelError
        doc = self._require_doc()
        tools = []
        for name in names:
            obj = doc.getObject(name)
            if obj is None:
                raise KernelError("fonction inconnue : {}".format(name))
            additive = not is_subtractive_type(obj.TypeId)
            if not obj.isDerivedFrom("PartDesign::FeatureAddSub"):
                raise KernelError(
                    "« {} » n'ajoute ni n'enlève de matière — répétez un "
                    "bossage, un enlèvement ou un perçage".format(obj.Label))
            tool = getattr(obj, "AddSubShape", None)
            if tool is None or tool.isNull() or not tool.Solids:
                raise KernelError("« {} » n'a pas de forme à recopier"
                                  .format(obj.Label))
            tools.append((tool, additive))
        return tools

    def _sketch_patterned(self, base_shape, spec):
        """La pièce ``base_shape`` avec les copies ``spec``."""
        from engine.kernel import KernelError
        import FreeCAD
        name, names = parse_spec(spec)
        sketch = self._require_doc().getObject(name)
        if sketch is None or sketch.TypeId != "Sketcher::SketchObject":
            raise KernelError("esquisse inconnue : {}".format(name))
        if not names:
            raise KernelError("choisissez au moins une fonction à répéter")
        points = self._sketch_pattern_points(sketch)
        tools = self._sketch_pattern_tools(names)
        box = FreeCAD.BoundBox()
        for tool, _ in tools:
            box.add(tool.BoundBox)
        reference = box.Center
        normal = sketch.Placement.Rotation.multVec(FreeCAD.Vector(0, 0, 1))
        added, removed = [], []
        for point in points:
            shift = point - reference
            shift = shift - normal * shift.dot(normal)
            if shift.Length < 1e-6:
                continue
            for tool, additive in tools:
                copy = tool.copy()
                copy.translate(shift)
                (added if additive else removed).append(copy)
        if not added and not removed:
            raise KernelError("tous les points sont sur l'original — "
                              "placez-en ailleurs")
        try:
            result = base_shape
            if added:
                result = result.fuse(added)
            if removed:
                result = result.cut(removed)
            result = result.removeSplitter()
        except Exception:  # noqa: BLE001
            result = None
        if (result is None or result.isNull() or not result.Solids
                or not result.isValid()):
            raise KernelError("le modeleur ne sait pas poser ces copies")
        if abs(result.Volume - base_shape.Volume) < 1e-9:
            raise KernelError("les copies ne changent pas la pièce — "
                              "les points sont-ils sur la pièce ?")
        return result

    def add_sketch_pattern(self, sketch=None, features=None):
        """Recopie ``features`` (sinon la dernière fonction de matière) sur
        chaque point de l'esquisse ``sketch`` (sinon la dernière libre)."""
        tip = self._solid_tip("une répétition demande un solide")
        source = (self._get_sketch(str(sketch)) if sketch
                  else self._latest_sketch())
        originals = self._pattern_originals(features)
        spec = format_spec(source.Name, [obj.Name for obj in originals])
        stamps = {"spatbase": tip.Name, "spat": spec}
        result = self._frozen_result(stamps, tip.Shape)
        tree = self._commit_frozen(tip, result, stamps,
                                   "Répétition pilotée par esquisse",
                                   {"spatspec": spec})
        source.Visibility = False
        return tree

    def _sketch_pattern_frozen(self, owner):
        """La forme figée d'une répétition pilotée par esquisse."""
        from engine.kernel import KernelError
        for obj in getattr(owner, "Group", None) or ():
            base = getattr(obj, "BaseFeature", None)
            if getattr(base, "FreeSolidSpatbase", ""):
                return base
        raise KernelError("répétition incomplète — la forme est absente")

    def _sketch_pattern_state(self, owner):
        """Ligne d'arbre : son esquisse et ses fonctions ; None pour une
        autre fonction."""
        spec = getattr(owner, "FreeSolidSpatspec", "")
        if not spec:
            return None
        sketch, names = parse_spec(spec)
        return {"sketch": sketch, "features": names}

    def _set_sketch_pattern_params(self, owner, values):
        """``set_params`` : ``features``, re-choisies. La forme se
        recalcule sur la fonction d'avant ; un refus la laisse telle
        quelle."""
        from engine.kernel import KernelError
        for key in values:
            if key != "features":
                raise KernelError(
                    "propriété non éditable : {}".format(key))
        doc = self._require_doc()
        frozen = self._sketch_pattern_frozen(owner)
        sketch, names = parse_spec(frozen.FreeSolidSpat)
        if "features" in values:
            names = [obj.Name for obj in
                     self._pattern_originals(values["features"])]
        spec = format_spec(sketch, names)
        base = doc.getObject(frozen.FreeSolidSpatbase)
        if base is None:
            raise KernelError("répétition incomplète — la forme est absente")
        frozen.Shape = self._sketch_patterned(base.Shape, spec)
        frozen.FreeSolidSpat = spec
        owner.FreeSolidSpatspec = spec
        self._recompute()
        return self.get_tree()
