"""Nervure : une esquisse ouverte (une ligne, ou plusieurs bout à bout)
épaissie, dont la matière s'étend jusqu'à la pièce — comme dans les
modeleurs courants.

Deux directions :

- ``parallel`` (parallèle à l'esquisse) : l'épaisseur est de part et
  d'autre du plan de l'esquisse ; la matière part de la ligne, dans le
  plan, jusqu'à la pièce. Les bouts de la ligne se prolongent jusqu'à
  elle (un gousset d'équerre) ;
- ``normal`` (normale à l'esquisse) : l'épaisseur est de part et d'autre
  de la ligne, dans le plan ; la matière descend hors du plan jusqu'à la
  pièce (des raidisseurs sous un plateau).

Le côté où va la matière est celui où elle rencontre la pièce ; ``flip``
prend l'autre quand les deux la rencontrent. La forme est rangée dans
l'historique comme le chanfrein de sommet (``_commit_frozen``) et
recalculée à chaque reconstruction depuis la fonction d'avant et
l'esquisse. Les imports FreeCAD restent dans les méthodes ; ``parse_spec``
et ``format_spec`` sont testées en CI.
"""

DIRECTIONS = ("parallel", "normal")


def format_spec(sketch, thickness, direction="parallel", flip=False):
    """« esquisse;épaisseur;direction;inversé » — rangé sur la forme figée
    et la fonction."""
    return "%s;%.9g;%s;%d" % (sketch, float(thickness), direction,
                              1 if flip else 0)


def parse_spec(spec):
    """(esquisse, épaisseur, direction, inversé)."""
    parts = str(spec).split(";")
    sketch = parts[0]
    thickness = float(parts[1])
    direction = parts[2] if len(parts) > 2 and parts[2] else "parallel"
    flip = len(parts) > 3 and parts[3] == "1"
    return sketch, thickness, direction, flip


def check_params(thickness, direction):
    """Une épaisseur positive, une direction connue ; sinon un message."""
    try:
        value = float(thickness)
    except (TypeError, ValueError):
        return "épaisseur de nervure invalide"
    if not value > 0:
        return "épaisseur de nervure invalide"
    if direction not in DIRECTIONS:
        return "direction de nervure inconnue : {}".format(direction)
    return None


class RibMixin:
    """Ops : nervure (création ; la réédition passe par ``set_params``)."""

    def _rib_shape(self, base_shape, spec):
        """La pièce ``base_shape`` avec la nervure ``spec``."""
        from engine.kernel import KernelError
        import FreeCAD
        import Part
        name, thickness, direction, flip = parse_spec(spec)
        problem = check_params(thickness, direction)
        if problem:
            raise KernelError(problem)
        sketch = self._require_doc().getObject(name)
        if sketch is None or sketch.TypeId != "Sketcher::SketchObject":
            raise KernelError("esquisse inconnue : {}".format(name))
        wire = self._rib_wire(sketch)
        normal = sketch.Placement.Rotation.multVec(FreeCAD.Vector(0, 0, 1))
        normal.normalize()
        box = base_shape.BoundBox
        reach = 4 * (box.DiagonalLength + wire.BoundBox.DiagonalLength)
        limit = FreeCAD.BoundBox(box)
        limit.add(wire.BoundBox)
        limit.enlarge(thickness + 1e-6)
        if direction == "parallel":
            sides, slab = self._rib_parallel(wire, normal, thickness, reach)
        else:
            sides, slab = self._rib_normal(wire, normal, thickness, reach)
        found = []
        for side in sides:
            try:
                pieces = slab(side).cut(base_shape).Solids
            except Exception:  # noqa: BLE001
                continue
            keep = [piece for piece in pieces
                    if piece.distToShape(wire)[0] < 1e-6]
            if keep and all(limit.isInside(piece.BoundBox)
                            for piece in keep):
                found.append(keep)
        if not found:
            raise KernelError("la nervure ne rencontre pas la pièce — "
                              "la ligne doit faire face à de la matière")
        keep = found[-1] if flip and len(found) > 1 else found[0]
        try:
            result = base_shape.fuse(keep).removeSplitter()
        except Exception:  # noqa: BLE001
            result = None
        if (result is None or result.isNull() or not result.Solids
                or not result.isValid()):
            raise KernelError("le modeleur ne sait pas poser cette nervure")
        if len(result.Solids) > 1:
            raise KernelError("la nervure ne touche pas la pièce")
        return result

    @staticmethod
    def _rib_wire(sketch):
        """Le trait ouvert de l'esquisse, d'un seul tenant."""
        from engine.kernel import KernelError
        import Part
        edges = list(getattr(sketch.Shape, "Edges", None) or ())
        if not edges:
            raise KernelError("la nervure demande une esquisse ouverte — "
                              "dessinez une ligne")
        try:
            wires = Part.sortEdges(edges)
        except Exception:  # noqa: BLE001
            wires = [edges]
        if len(wires) != 1:
            raise KernelError("la nervure demande un seul trait, d'un "
                              "seul tenant")
        wire = Part.Wire(wires[0])
        if wire.isClosed():
            raise KernelError("la nervure demande une esquisse ouverte — "
                              "pas un contour fermé")
        return wire

    @staticmethod
    def _rib_parallel(wire, normal, thickness, reach):
        """Parallèle à l'esquisse : le trait, prolongé par ses deux bouts,
        balaie le plan perpendiculairement à sa corde ; la bande s'épaissit
        de part et d'autre du plan."""
        from engine.kernel import KernelError
        import Part
        points = [v.Point for v in wire.OrderedVertexes]
        start, end = points[0], points[-1]
        chord = end - start
        if chord.Length < 1e-9:
            raise KernelError("la nervure demande une esquisse ouverte — "
                              "pas un contour fermé")
        chord.normalize()
        ordered = wire.OrderedEdges
        # Les bouts se prolongent dans le sens de leur segment.
        head = start - points[1]
        tail = end - points[-2]
        head.normalize()
        tail.normalize()
        extended = Part.Wire(
            [Part.LineSegment(start + head * reach, start).toShape()]
            + list(ordered)
            + [Part.LineSegment(end, end + tail * reach).toShape()])
        side = normal.cross(chord)
        side.normalize()

        def slab(way):
            band = extended.extrude(way * reach)
            solid = band.extrude(normal * thickness)
            solid.translate(normal * (-thickness / 2))
            return solid

        return [side, side * -1], slab

    @staticmethod
    def _rib_normal(wire, normal, thickness, reach):
        """Normale à l'esquisse : chaque segment s'épaissit de part et
        d'autre dans le plan (prolongé d'une demi-épaisseur aux jonctions),
        puis descend hors du plan."""
        from engine.kernel import KernelError
        import Part
        half = thickness / 2
        if any(type(edge.Curve).__name__ not in ("Line", "LineSegment")
               for edge in wire.Edges):
            raise KernelError("une nervure normale à l'esquisse demande "
                              "des segments droits")
        points = [v.Point for v in wire.OrderedVertexes]
        count = len(points) - 1
        faces = []
        for index in range(count):
            a = points[index]
            b = points[index + 1]
            along = b - a
            along.normalize()
            if index > 0:
                a = a - along * half
            if index < count - 1:
                b = b + along * half
            off = normal.cross(along)
            off.normalize()
            off = off * half
            faces.append(Part.Face(Part.makePolygon(
                [a + off, b + off, b - off, a - off, a + off])))

        def slab(way):
            solids = [face.extrude(way * reach) for face in faces]
            if len(solids) == 1:
                return solids[0]
            return solids[0].fuse(solids[1:]).removeSplitter()

        return [normal, normal * -1], slab

    def add_rib(self, thickness, sketch=None, direction="parallel",
                flip=False):
        """Nervure de l'esquisse ouverte ``sketch`` (sinon la dernière
        esquisse libre) : épaisseur, direction, côté."""
        from engine.kernel import KernelError
        problem = check_params(thickness, direction)
        if problem:
            raise KernelError(problem)
        tip = self._solid_tip("une nervure demande un solide")
        source = (self._get_sketch(str(sketch)) if sketch
                  else self._latest_sketch())
        spec = format_spec(source.Name, thickness, direction, flip)
        stamps = {"ribbase": tip.Name, "rib": spec}
        result = self._frozen_result(stamps, tip.Shape)
        tree = self._commit_frozen(tip, result, stamps, "Nervure",
                                   {"ribspec": spec})
        source.Visibility = False
        return tree

    def _rib_frozen(self, owner):
        """La forme figée d'une nervure."""
        from engine.kernel import KernelError
        for obj in getattr(owner, "Group", None) or ():
            base = getattr(obj, "BaseFeature", None)
            if getattr(base, "FreeSolidRibbase", ""):
                return base
        raise KernelError("nervure incomplète — la forme est absente")

    def _rib_state(self, owner):
        """Ligne d'arbre d'une nervure : son esquisse, épaisseur,
        direction, côté ; None pour une autre fonction."""
        spec = getattr(owner, "FreeSolidRibspec", "")
        if not spec:
            return None
        sketch, thickness, direction, flip = parse_spec(spec)
        return {"sketch": sketch, "thickness": thickness,
                "direction": direction, "flip": flip}

    def _set_rib_params(self, owner, values):
        """``set_params`` d'une nervure : ``thickness``, ``direction``,
        ``flip``. La forme se recalcule sur la fonction d'avant ; un refus
        laisse la nervure telle quelle."""
        from engine.kernel import KernelError
        for key in values:
            if key not in ("thickness", "direction", "flip"):
                raise KernelError(
                    "propriété non éditable : {}".format(key))
        doc = self._require_doc()
        frozen = self._rib_frozen(owner)
        sketch, thickness, direction, flip = parse_spec(frozen.FreeSolidRib)
        thickness = values.get("thickness", thickness)
        direction = values.get("direction", direction)
        flip = bool(values.get("flip", flip))
        problem = check_params(thickness, direction)
        if problem:
            raise KernelError(problem)
        spec = format_spec(sketch, thickness, direction, flip)
        base = doc.getObject(frozen.FreeSolidRibbase)
        if base is None:
            raise KernelError("nervure incomplète — la forme est absente")
        frozen.Shape = self._rib_shape(base.Shape, spec)
        frozen.FreeSolidRib = spec
        owner.FreeSolidRibspec = spec
        self._recompute()
        return self.get_tree()
