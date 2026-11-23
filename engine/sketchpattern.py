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

La répétition pilotée par table suit le même chemin : à la place de
l'esquisse, une table de décalages (X, Y, Z de chaque copie depuis
l'original, dans les axes de la pièce), rangée « @x,y,z/x,y,z ».
"""

#: Préfixe d'une table de décalages à la place d'une esquisse.
TABLE = "@"


def format_spec(sketch, features):
    """« esquisse;fonction1,fonction2 » — rangé sur la forme figée et la
    fonction."""
    return "%s;%s" % (sketch, ",".join(str(name) for name in features))


def parse_spec(spec):
    """(esquisse, [fonctions])."""
    sketch, _, names = str(spec).partition(";")
    return sketch, [name for name in names.split(",") if name]


def _coord(value):
    return ("%.6f" % float(value)).rstrip("0").rstrip(".") or "0"


def format_offsets(offsets):
    """« @x,y,z/x,y,z » — la source d'une répétition pilotée par table."""
    return TABLE + "/".join(
        ",".join(_coord(c) for c in (list(row) + [0, 0, 0])[:3])
        for row in offsets)


def parse_offsets(source):
    """[[x, y, z]…] d'une source de table ; None pour une esquisse."""
    if not str(source).startswith(TABLE):
        return None
    rows = []
    for part in str(source)[len(TABLE):].split("/"):
        if part:
            rows.append([float(c) for c in part.split(",")])
    return rows


def check_offsets(offsets):
    """Les lignes d'une table, en [x, y, z] ; message d'erreur sinon."""
    if not isinstance(offsets, (list, tuple)) or not offsets:
        return None, "la table est vide — ajoutez une ligne par copie"
    rows = []
    for row in offsets:
        if not isinstance(row, (list, tuple)) or not 1 <= len(row) <= 3:
            return None, "ligne de table invalide — X, Y, Z attendus"
        try:
            values = [float(c) for c in row]
        except (TypeError, ValueError):
            return None, "ligne de table invalide — X, Y, Z attendus"
        rows.append((values + [0.0, 0.0, 0.0])[:3])
    return rows, None


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
        if not names:
            raise KernelError("choisissez au moins une fonction à répéter")
        tools = self._sketch_pattern_tools(names)
        offsets = parse_offsets(name)
        if offsets is not None:
            shifts = [FreeCAD.Vector(*row) for row in offsets]
        else:
            sketch = self._require_doc().getObject(name)
            if sketch is None or sketch.TypeId != "Sketcher::SketchObject":
                raise KernelError("esquisse inconnue : {}".format(name))
            points = self._sketch_pattern_points(sketch)
            box = FreeCAD.BoundBox()
            for tool, _ in tools:
                box.add(tool.BoundBox)
            reference = box.Center
            normal = sketch.Placement.Rotation.multVec(
                FreeCAD.Vector(0, 0, 1))
            shifts = []
            for point in points:
                shift = point - reference
                shifts.append(shift - normal * shift.dot(normal))
        added, removed = [], []
        for shift in shifts:
            if shift.Length < 1e-6:
                continue
            for tool, additive in tools:
                copy = tool.copy()
                copy.translate(shift)
                (added if additive else removed).append(copy)
        if not added and not removed:
            raise KernelError(
                "toutes les copies tombent sur l'original — décalez-les"
                if offsets is not None else
                "tous les points sont sur l'original — placez-en ailleurs")
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

    def add_table_pattern(self, offsets, features=None):
        """Recopie ``features`` (sinon la dernière fonction de matière) à
        chaque décalage ``offsets`` ([[x, y, z]…] depuis l'original)."""
        from engine.kernel import KernelError
        rows, error = check_offsets(offsets)
        if error:
            raise KernelError(error)
        tip = self._solid_tip("une répétition demande un solide")
        originals = self._pattern_originals(features)
        spec = format_spec(format_offsets(rows),
                           [obj.Name for obj in originals])
        stamps = {"spatbase": tip.Name, "spat": spec}
        result = self._frozen_result(stamps, tip.Shape)
        return self._commit_frozen(tip, result, stamps,
                                   "Répétition pilotée par table",
                                   {"spatspec": spec})

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
        if parse_offsets(sketch) is not None:
            return None
        return {"sketch": sketch, "features": names}

    def _table_pattern_state(self, owner):
        """Ligne d'arbre : ses décalages et ses fonctions ; None pour une
        autre fonction."""
        spec = getattr(owner, "FreeSolidSpatspec", "")
        source, names = parse_spec(spec)
        offsets = parse_offsets(source) if spec else None
        if offsets is None:
            return None
        return {"offsets": offsets, "features": names}

    def _set_sketch_pattern_params(self, owner, values):
        """``set_params`` : ``features``, re-choisies ; ``offsets`` pour
        une table. La forme se recalcule sur la fonction d'avant ; un
        refus la laisse telle quelle."""
        from engine.kernel import KernelError
        doc = self._require_doc()
        frozen = self._sketch_pattern_frozen(owner)
        sketch, names = parse_spec(frozen.FreeSolidSpat)
        table = parse_offsets(sketch) is not None
        for key in values:
            if key != "features" and not (table and key == "offsets"):
                raise KernelError(
                    "propriété non éditable : {}".format(key))
        if "offsets" in values:
            rows, error = check_offsets(values["offsets"])
            if error:
                raise KernelError(error)
            sketch = format_offsets(rows)
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
