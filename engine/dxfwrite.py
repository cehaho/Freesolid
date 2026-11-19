"""DXF de la feuille de mise en plan — celle qu'on voit à l'écran.

Pur (aucun import FreeCAD) : les entités viennent de
``app/drawingsheet.js`` (``sheetEntities``), en mm, y vers le bas ; le
DXF a l'y vers le haut. Format R12 (AC1009), lu partout ; texte en
Windows-1252 (``$DWGCODEPAGE``).
"""

#: Calques de la feuille : (nom, couleur ACI, type de ligne).
LAYERS = (
    ("cadre", 7, "CONTINUOUS"),
    ("visible", 7, "CONTINUOUS"),
    ("cache", 8, "DASHED"),
    ("cote", 3, "CONTINUOUS"),
    ("texte", 7, "CONTINUOUS"),
)

#: Bornes d'une feuille : un client ne fait pas écrire n'importe quoi.
MAX_ENTITIES = 200000
MAX_POINTS = 2000000


class DxfError(ValueError):
    """Entités mal formées."""


def _num(value):
    number = float(value)
    if number != number or number in (float("inf"), float("-inf")):
        raise DxfError("nombre invalide")
    return number


def _point(value):
    if not isinstance(value, (list, tuple)) or len(value) != 2:
        raise DxfError("point attendu [x, y]")
    return _num(value[0]), _num(value[1])


def _pairs(code_values):
    return "".join("{}\n{}\n".format(code, value)
                   for code, value in code_values)


def _fmt(number):
    return "{:.4f}".format(number)


def drawing_dxf(width, height, entities):
    """Le texte DXF de la feuille ``width`` × ``height`` (mm)."""
    width, height = _num(width), _num(height)
    if not isinstance(entities, list) or len(entities) > MAX_ENTITIES:
        raise DxfError("liste d'entités attendue")
    layers = {name for name, _, _ in LAYERS}
    flip = lambda y: height - y  # noqa: E731
    body = []
    points = 0
    for entity in entities:
        if not isinstance(entity, dict):
            raise DxfError("entité attendue")
        kind = entity.get("k")
        layer = entity.get("layer") if entity.get("layer") in layers \
            else "visible"
        if kind == "line":
            (x1, y1), (x2, y2) = _point(entity.get("a")), \
                _point(entity.get("b"))
            body.append(_pairs((
                (0, "LINE"), (8, layer),
                (10, _fmt(x1)), (20, _fmt(flip(y1))), (30, "0.0"),
                (11, _fmt(x2)), (21, _fmt(flip(y2))), (31, "0.0"))))
            points += 2
        elif kind in ("poly", "fill"):
            pts = [_point(p) for p in entity.get("pts") or ()]
            points += len(pts)
            if kind == "fill":
                if len(pts) != 3:
                    raise DxfError("pointe de flèche : trois points")
                (ax, ay), (bx, by), (cx, cy) = pts
                body.append(_pairs((
                    (0, "SOLID"), (8, layer),
                    (10, _fmt(ax)), (20, _fmt(flip(ay))), (30, "0.0"),
                    (11, _fmt(bx)), (21, _fmt(flip(by))), (31, "0.0"),
                    (12, _fmt(cx)), (22, _fmt(flip(cy))), (32, "0.0"),
                    (13, _fmt(cx)), (23, _fmt(flip(cy))), (33, "0.0"))))
                continue
            for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
                body.append(_pairs((
                    (0, "LINE"), (8, layer),
                    (10, _fmt(x1)), (20, _fmt(flip(y1))), (30, "0.0"),
                    (11, _fmt(x2)), (21, _fmt(flip(y2))), (31, "0.0"))))
        elif kind == "text":
            x, y = _point(entity.get("at"))
            text = str(entity.get("text", "")).replace("\n", " ")[:250]
            size = _num(entity.get("size", 3.5))
            angle = _num(entity.get("angle", 0) or 0)
            centred = entity.get("anchor") == "middle"
            codes = [(0, "TEXT"), (8, layer),
                     (10, _fmt(x)), (20, _fmt(flip(y))), (30, "0.0"),
                     (40, _fmt(size)), (1, text), (50, _fmt(angle))]
            if centred:
                codes += [(72, 1), (11, _fmt(x)), (21, _fmt(flip(y))),
                          (31, "0.0")]
            body.append(_pairs(codes))
            points += 1
        else:
            raise DxfError("entité inconnue : {}".format(kind))
        if points > MAX_POINTS:
            raise DxfError("feuille trop lourde")
    return "".join((
        _pairs(((0, "SECTION"), (2, "HEADER"),
                (9, "$ACADVER"), (1, "AC1009"),
                (9, "$DWGCODEPAGE"), (3, "ANSI_1252"),
                (9, "$INSBASE"), (10, "0.0"), (20, "0.0"), (30, "0.0"),
                (9, "$EXTMIN"), (10, "0.0"), (20, "0.0"), (30, "0.0"),
                (9, "$EXTMAX"), (10, _fmt(width)), (20, _fmt(height)),
                (30, "0.0"),
                (9, "$LIMMIN"), (10, "0.0"), (20, "0.0"),
                (9, "$LIMMAX"), (10, _fmt(width)), (20, _fmt(height)),
                (0, "ENDSEC"))),
        _tables(),
        _pairs(((0, "SECTION"), (2, "ENTITIES"))),
        "".join(body),
        _pairs(((0, "ENDSEC"), (0, "EOF"))),
    ))


def _tables():
    ltypes = _pairs((
        (0, "TABLE"), (2, "LTYPE"), (70, 2),
        (0, "LTYPE"), (2, "CONTINUOUS"), (70, 0), (3, "Solid line"),
        (72, 65), (73, 0), (40, "0.0"),
        (0, "LTYPE"), (2, "DASHED"), (70, 0), (3, "__ __ __"),
        (72, 65), (73, 2), (40, "2.4"), (49, "1.6"), (49, "-0.8"),
        (0, "ENDTAB")))
    layers = [(0, "TABLE"), (2, "LAYER"), (70, len(LAYERS))]
    for name, color, ltype in LAYERS:
        layers += [(0, "LAYER"), (2, name), (70, 0), (62, color),
                   (6, ltype)]
    layers.append((0, "ENDTAB"))
    return (_pairs(((0, "SECTION"), (2, "TABLES"))) + ltypes
            + _pairs(layers) + _pairs(((0, "ENDSEC"),)))
