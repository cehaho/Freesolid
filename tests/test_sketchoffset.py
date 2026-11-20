"""Décalage paramétrique : les noms qui tiennent le lien (sans FreeCAD)."""
from types import SimpleNamespace

from engine import sketchoffset as so


class _Sketch:
    def __init__(self, names):
        self.Constraints = [SimpleNamespace(Name=n, Second=i)
                            for i, n in enumerate(names)]
        self.virtual = set()

    def renameConstraint(self, i, name):
        self.Constraints[i].Name = name

    def setVirtualSpace(self, i, flag):
        (self.virtual.add if flag else self.virtual.discard)(i)


def test_nom_interne_tu_a_l_ecran():
    assert so.is_internal_name("_decalage3")
    assert not so.is_internal_name("_decalage3__1")
    assert not so.is_internal_name("ep")
    assert not so.is_internal_name(None)


def test_suiveuses_par_le_nom():
    sk = _Sketch(["", "ep", "ep__1", "ep__2", "ep2__1", "x"])
    assert so.followers(sk, "ep") == [2, 3]
    assert so.followers(sk, "") == []


def test_renommer_la_pilote_renomme_les_suiveuses():
    sk = _Sketch(["_decalage1", "_decalage1__1", "_decalage1__2"])
    sk.renameConstraint(0, "ep")
    so.rename_followers(sk, "_decalage1", "ep")
    assert [c.Name for c in sk.Constraints] == ["ep", "ep__1", "ep__2"]


def test_pilote_perdue_la_premiere_suiveuse_la_remplace():
    sk = _Sketch(["", "ep__2", "ep__3"])
    sk.virtual = {1, 2}
    assert so.heal(sk)
    assert sk.Constraints[1].Name == "ep" and 1 not in sk.virtual
    assert so.followers(sk, "ep") == [2]
    assert not so.heal(sk)
