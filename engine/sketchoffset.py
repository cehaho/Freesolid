"""Décalage d'entités paramétrique, comme dans les modeleurs courants.

La copie décalée reste liée à ses originaux : une seule cote — la
distance de décalage — la pilote, et elle suit les originaux quand ils
bougent. Sketcher n'a pas de relation « décalage » : on la compose.

- une ligne copiée : parallèle à son original, à la distance du
  décalage (de son premier point à la ligne d'origine) ;
- un cercle ou un arc : concentrique, à la distance du décalage (cercle
  à cercle) ;
- les copies qui se touchent restent jointes (coïncidence) ;
- un bout libre de la copie (chaîne ouverte) glisse sur sa ligne : le
  lier au bout d'origine (distance point à point) dégénère avec la
  distance ligne à ligne — deux cercles tangents, le solveur le refuse.

Chaque distance va de la copie (``First``) à l'original (``Second``).

Une seule de ces distances se montre et se cote : la **pilote**. Les
autres, ses **suiveuses**, sont rangées hors de la vue (espace virtuel
de Sketcher) et prennent sa valeur — ou son expression — chaque fois
qu'elle change (``sync_followers``). Pas d'expression qui la désigne :
supprimer une contrainte ne casse rien. Le lien passe par les noms : la
pilote s'appelle ``_decalage3`` (nom interne, que l'écran ne montre
pas), ses suiveuses ``_decalage3__1``, ``_decalage3__2``… Nommée par
l'utilisateur (``ep``), ses suiveuses deviennent ``ep__1``…

Module pur à l'import : FreeCAD n'est chargé que dans les fonctions.
"""

import re

PREFIX = "_decalage"
_TOL = 1e-6
_LINE = "Part::GeomLineSegment"
_ROUND = ("Part::GeomCircle", "Part::GeomArcOfCircle")


def is_internal_name(name):
    """Le nom que le décalage donne à sa cote pilote : l'écran le tait."""
    return bool(re.fullmatch(re.escape(PREFIX) + r"\d+", name or ""))


def follower_name(driver, k):
    return "{}__{}".format(driver, k)


def followers(sk, driver):
    """Indices des suiveuses de la cote nommée ``driver``."""
    if not driver:
        return []
    pattern = re.compile(re.escape(driver) + r"__\d+")
    return [i for i, c in enumerate(sk.Constraints)
            if c.Name and pattern.fullmatch(c.Name)]


def is_hidden(sk, index):
    """Rangée hors de la vue (une suiveuse de décalage)."""
    try:
        return bool(sk.getVirtualSpace(index))
    except Exception:  # noqa: BLE001
        return False


def _line_distance(p, a, b):
    d = b - a
    if d.Length < 1e-12:
        return float("inf")
    return abs((p.x - a.x) * d.y - (p.y - a.y) * d.x) / d.Length


def _parallel(g1, g2):
    d1 = g1.EndPoint - g1.StartPoint
    d2 = g2.EndPoint - g2.StartPoint
    if d1.Length < 1e-12 or d2.Length < 1e-12:
        return False
    return abs(d1.x * d2.y - d1.y * d2.x) <= 1e-7 * d1.Length * d2.Length


def _ends(geo):
    """Les bouts d'une ligne ou d'un arc : ``[(pos, point)]``."""
    if geo.TypeId in (_LINE, "Part::GeomArcOfCircle"):
        return [(1, geo.StartPoint), (2, geo.EndPoint)]
    return []


def _original_of(sk, copy, originals, distance):
    """L'original dont ``copy`` est le décalé, ou None."""
    g = sk.Geometry[copy]
    best, best_gap = None, None
    for o in originals:
        h = sk.Geometry[o]
        if g.TypeId == _LINE and h.TypeId == _LINE:
            if not _parallel(g, h):
                continue
            if abs(_line_distance(g.StartPoint, h.StartPoint, h.EndPoint)
                   - distance) > 1e-5:
                continue
            mid_g = (g.StartPoint + g.EndPoint) * 0.5
            mid_h = (h.StartPoint + h.EndPoint) * 0.5
            gap = (mid_g - mid_h).Length
        elif g.TypeId in _ROUND and h.TypeId in _ROUND:
            if (g.Center - h.Center).Length > 1e-5:
                continue
            if abs(abs(g.Radius - h.Radius) - distance) > 1e-5:
                continue
            gap = 0.0
        else:
            continue
        if best_gap is None or gap < best_gap:
            best, best_gap = o, gap
    return best


def link_offset(sk, originals, copies, distance):
    """Lie les copies ``copies`` à leurs ``originals`` (voir le module).

    Rend l'indice de la cote pilote, ou None si rien n'a pu se lier ou
    si le solveur refuse l'ensemble — les contraintes ajoutées sont
    alors retirées et les copies restent libres, comme avant.
    """
    import Sketcher
    C = Sketcher.Constraint
    d = float(distance)
    pairs = {c: _original_of(sk, c, originals, d) for c in copies}
    relations, distances = [], []
    for c, o in pairs.items():
        if o is None:
            continue
        g = sk.Geometry[c]
        if g.TypeId == _LINE:
            relations.append(C("Parallel", o, c))
            distances.append(C("Distance", c, 1, o, d))
        else:
            relations.append(C("Coincident", c, 3, o, 3))
            distances.append(C("Distance", c, o, d))
    if not distances:
        return None
    # Les copies qui se touchent restent jointes.
    ends = [(c, pos, p) for c in copies for pos, p in _ends(sk.Geometry[c])]
    for i, (c1, pos1, p1) in enumerate(ends):
        for c2, pos2, p2 in ends[i + 1:]:
            if c1 != c2 and (p1 - p2).Length < _TOL:
                relations.append(C("Coincident", c1, pos1, c2, pos2))

    added = []
    try:
        for constraint in relations:
            added.append(sk.addConstraint(constraint))
        driver = None
        taken = {c.Name for c in sk.Constraints if c.Name}
        n = 1
        while "{}{}".format(PREFIX, n) in taken:
            n += 1
        name = "{}{}".format(PREFIX, n)
        for k, constraint in enumerate(distances):
            index = sk.addConstraint(constraint)
            added.append(index)
            if driver is None:
                driver = index
                sk.renameConstraint(index, name)
            else:
                sk.renameConstraint(index, follower_name(name, k))
                sk.setVirtualSpace(index, True)
        sk.solve()
        trouble = (list(getattr(sk, "ConflictingConstraints", []))
                   + list(getattr(sk, "RedundantConstraints", []))
                   + list(getattr(sk, "PartiallyRedundantConstraints", [])))
        if any(i + 1 in trouble for i in added):
            raise ValueError("décalage : relations refusées")
        return driver
    except Exception:  # noqa: BLE001
        for index in sorted(added, reverse=True):
            try:
                sk.delConstraint(index)
            except Exception:  # noqa: BLE001
                pass
        sk.solve()
        return None


def sync_followers(sk, index, expression=None):
    """Les suiveuses de la cote ``index`` prennent sa valeur (ou son
    expression)."""
    driver = sk.Constraints[index]
    for f in followers(sk, driver.Name):
        path = "Constraints[{}]".format(f)
        if expression:
            sk.setExpression(path, expression)
        else:
            try:
                sk.setExpression(path, None)
            except Exception:  # noqa: BLE001
                pass
            sk.setDatum(f, abs(float(driver.Value)))


def rename_followers(sk, old, new):
    """La pilote renommée : ses suiveuses suivent le nom."""
    pattern = re.compile(re.escape(old) + r"__(\d+)")
    for i, c in enumerate(sk.Constraints):
        match = c.Name and pattern.fullmatch(c.Name)
        if match:
            sk.renameConstraint(i, follower_name(new, match.group(1)))


def heal(sk):
    """Une copie supprimée a emporté la pilote : la première suiveuse
    restante prend sa place (visible, cotable), les autres la suivent."""
    names = {c.Name for c in sk.Constraints if c.Name}
    orphans = {}
    for i, c in enumerate(sk.Constraints):
        match = c.Name and re.fullmatch(r"(.+)__\d+", c.Name)
        if match and match.group(1) not in names:
            orphans.setdefault(match.group(1), []).append(i)
    for driver, indices in orphans.items():
        first = min(indices)
        sk.renameConstraint(first, driver)
        sk.setVirtualSpace(first, False)
    return bool(orphans)


def originals(sk, index):
    """Les originaux d'un décalage, d'après sa cote ``index``."""
    driver = sk.Constraints[index]
    group = [index] + followers(sk, driver.Name)
    return sorted({sk.Constraints[i].Second for i in group
                   if sk.Constraints[i].Second is not None
                   and sk.Constraints[i].Second >= 0})


class pinned:
    """Le temps d'éditer une cote de décalage, les originaux sont bloqués :
    c'est la copie qui bouge, pas l'original sous-contraint. Si le blocage
    gêne le solveur (originaux déjà cotés), il est levé aussitôt."""

    def __init__(self, sk, index):
        self.sk = sk
        name = sk.Constraints[index].Name
        self.geos = (originals(sk, index)
                     if is_internal_name(name) or followers(sk, name)
                     else [])
        self.blocks = []

    def __enter__(self):
        import Sketcher
        for g in self.geos:
            self.blocks.append(
                self.sk.addConstraint(Sketcher.Constraint("Block", g)))
        if self.blocks:
            self.sk.solve()
            trouble = (list(getattr(self.sk, "ConflictingConstraints", []))
                       + list(getattr(self.sk, "RedundantConstraints", [])))
            if trouble:
                self._release()
        return self

    def _release(self):
        for b in sorted(self.blocks, reverse=True):
            self.sk.delConstraint(b)
        self.blocks = []

    def __exit__(self, *exc):
        if self.blocks:
            self.sk.solve()
            self._release()
        return False
