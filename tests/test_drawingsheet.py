"""Feuille de mise en plan : échelle normalisée et place des vues."""

from engine import drawingsheet as ds


def _sizes(x, y, z):
    iso = (0.9 * (x + y), 0.8 * (x + y + z))
    return {"front": (x, z), "top": (x, y), "right": (y, z), "iso": iso}


def test_echelle_la_plus_grande_qui_tient():
    assert ds.layout(_sizes(40, 20, 10))["scale"] == 2.0
    assert ds.layout(_sizes(100, 60, 40))["scale"] == 0.5
    assert ds.layout(_sizes(4000, 2000, 1000))["scale"] == 0.02


def test_echelle_imposee():
    assert ds.layout(_sizes(40, 20, 10), scale=1)["scale"] == 1.0


def test_premier_diedre():
    # Le dessus sous la face, la droite à gauche, l'iso à droite.
    centers = ds.layout(_sizes(40, 20, 10))["centers"]
    fx, fy = centers["front"]
    assert centers["top"][0] == fx and centers["top"][1] > fy
    assert centers["right"][0] < fx and centers["right"][1] == fy
    assert centers["iso"][0] > fx


def test_rien_ne_deborde_ni_ne_couvre_le_cartouche():
    for size in ((40, 20, 10), (300, 20, 10), (20, 20, 200), (100, 100, 100)):
        out = ds.layout(_sizes(*size))
        assert ds._fits(_sizes(*size), out["scale"]), size


def test_libelle_d_echelle():
    assert ds.scale_label(1.0) == "1:1"
    assert ds.scale_label(0.5) == "1:2"
    assert ds.scale_label(2.0) == "2:1"
    assert ds.scale_label(0.02) == "1:50"


def test_groupe_centre_sur_la_feuille():
    # Le bloc 40 × 20 × 10 (iso mesurée 42,4 × 32,7) : le groupe de vues
    # n'est plus calé en haut à gauche, et tient toujours.
    sizes = {"front": (40, 10), "top": (40, 20), "right": (20, 10),
             "iso": (42.4, 32.7)}
    out = ds.layout(sizes)
    plain = ds._centers(sizes, out["scale"])
    assert out["centers"]["right"][0] > plain["right"][0]
    assert out["centers"]["right"][1] > plain["right"][1]
    assert ds._fits(sizes, out["scale"], ds._centring(sizes, out["scale"]))
