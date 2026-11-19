"""Feuille de mise en plan : format, échelle normalisée, place des vues.

Pur (aucun import FreeCAD) : la projection est dans ``engine/drawing.py``,
le dessin de la feuille dans ``app/drawingsheet.js``.

Comme dans les modeleurs courants en norme ISO : A4 paysage, projection
au premier dièdre — la vue de dessus sous la vue de face, la vue de
droite à gauche de la face —, une isométrique en haut à droite au-dessus
du cartouche, et la plus grande échelle normalisée qui fait tout tenir.
"""

#: A4 paysage, en mm ; cadre à 10 mm du bord.
SHEET = {"width": 297.0, "height": 210.0, "margin": 10.0}

#: Cartouche, dans le coin bas droit du cadre.
TITLE_BLOCK = {"width": 120.0, "height": 36.0}

#: Jeu entre deux vues, et entre une vue et le cadre (mm sur la feuille).
GAP = 14.0

#: Échelles normalisées, de la plus grande à la plus petite.
STANDARD_SCALES = (10.0, 5.0, 2.0, 1.0, 0.5, 0.2, 0.1, 0.05, 0.02, 0.01,
                   0.005, 0.002, 0.001)

#: Les vues standard, dans l'ordre de la feuille, et leur direction :
#: (droite de la vue, haut de la vue, vers l'observateur), repère pièce
#: Z en haut (le plan de face est XZ).
VIEWS = (
    ("front", "Face", (1, 0, 0), (0, 0, 1), (0, -1, 0)),
    ("top", "Dessus", (1, 0, 0), (0, 1, 0), (0, 0, 1)),
    ("right", "Droite", (0, 1, 0), (0, 0, 1), (1, 0, 0)),
    ("iso", "Isométrique", None, None, (1, -1, 1)),
)


def scale_label(scale):
    """« 1:2 », « 1:1 », « 2:1 »."""
    if scale >= 1:
        return "{}:1".format(_plain(scale))
    return "1:{}".format(_plain(1.0 / scale))


def _plain(value):
    rounded = round(value, 6)
    return str(int(rounded)) if rounded == int(rounded) else str(rounded)


def layout(sizes, scale=None):
    """Échelle et centre de chaque vue sur la feuille (mm, y vers le bas).

    ``sizes`` : ``{nom: (largeur, hauteur)}`` des vues en mm réels
    (``front``, ``top``, ``right``, ``iso``). ``scale`` imposée, sinon la
    plus grande normalisée qui tient (la plus petite si rien ne tient).
    Retourne ``{"scale": s, "centers": {nom: (x, y)}}``.
    """
    candidates = [float(scale)] if scale else list(STANDARD_SCALES)
    chosen = candidates[-1]
    for candidate in candidates:
        if _fits(sizes, candidate):
            chosen = candidate
            break
    shift = _centring(sizes, chosen)
    return {"scale": chosen, "centers": _centers(sizes, chosen, shift)}


def _size(sizes, name):
    width, height = sizes.get(name, (0.0, 0.0))
    return max(float(width), 0.0), max(float(height), 0.0)


def _frame():
    margin = SHEET["margin"]
    return (margin, margin, SHEET["width"] - margin,
            SHEET["height"] - margin)


def _centring(sizes, scale):
    """Décalage qui centre le groupe de vues dans le cadre, sans toucher
    le cartouche : d'abord dans les deux sens, sinon en largeur seule."""
    left, top, right, bottom = _frame()
    boxes = _boxes(sizes, scale).values()
    x0 = min(b[0] for b in boxes) - GAP
    x1 = max(b[2] for b in boxes) + GAP
    y0 = min(b[1] for b in boxes) - GAP
    y1 = max(b[3] for b in boxes) + GAP
    dx = max(0.0, ((right - left) - (x1 - x0)) / 2 - (x0 - left))
    dy = max(0.0, ((bottom - top) - (y1 - y0)) / 2 - (y0 - top))
    for shift in ((dx, dy), (dx, 0.0), (0.0, 0.0)):
        if _fits(sizes, scale, shift):
            return shift
    return (0.0, 0.0)


def _boxes(sizes, scale, shift=(0.0, 0.0)):
    """Cadres (x0, y0, x1, y1) des vues, groupe calé en haut à gauche."""
    left, top, _, _ = _frame()
    left += shift[0]
    top += shift[1]
    fw, fh = _size(sizes, "front")
    tw, th = _size(sizes, "top")
    rw, rh = _size(sizes, "right")
    iw, ih = _size(sizes, "iso")
    s = scale
    x_right = left + GAP
    x_front = x_right + s * rw + GAP
    x_iso = x_front + s * max(fw, tw) + GAP
    row = top + GAP
    front_h = s * max(fh, rh)
    boxes = {
        "right": (x_right, row + (front_h - s * rh) / 2,
                  x_right + s * rw, row + (front_h + s * rh) / 2),
        "front": (x_front, row + (front_h - s * fh) / 2,
                  x_front + s * fw, row + (front_h + s * fh) / 2),
        "top": (x_front, row + front_h + GAP,
                x_front + s * tw, row + front_h + GAP + s * th),
        "iso": (x_iso, row, x_iso + s * iw, row + s * ih),
    }
    return boxes


def _fits(sizes, scale, shift=(0.0, 0.0)):
    _, _, right, bottom = _frame()
    boxes = _boxes(sizes, scale, shift)
    block_left = right - TITLE_BLOCK["width"]
    block_top = bottom - TITLE_BLOCK["height"]
    for x0, y0, x1, y1 in boxes.values():
        if x1 > right - GAP / 2 or y1 > bottom - GAP / 2:
            return False
        # Rien sous le cartouche.
        if x1 > block_left - GAP / 2 and y1 > block_top - GAP / 2:
            return False
    return True


def _centers(sizes, scale, shift=(0.0, 0.0)):
    return {name: ((x0 + x1) / 2, (y0 + y1) / 2)
            for name, (x0, y0, x1, y1)
            in _boxes(sizes, scale, shift).items()}
