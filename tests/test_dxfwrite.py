"""DXF de la feuille de mise en plan : les entités de l'écran."""

import pytest

from engine.dxfwrite import DxfError, drawing_dxf

SHEET = [
    {"k": "poly", "pts": [[10, 10], [287, 10], [287, 200]], "layer": "cadre"},
    {"k": "line", "a": [50, 40], "b": [90, 40], "layer": "visible"},
    {"k": "poly", "pts": [[60, 45], [60, 50]], "layer": "cache"},
    {"k": "fill", "pts": [[50, 30], [52, 29], [52, 31]], "layer": "cote"},
    {"k": "text", "at": [70, 29], "text": "Échelle 2:1", "size": 3.5,
     "anchor": "middle", "angle": 90, "layer": "texte"},
]


def test_feuille_r12_calques_et_y_retourne():
    text = drawing_dxf(297, 210, SHEET)
    assert text.startswith("0\nSECTION\n2\nHEADER\n9\n$ACADVER\n1\nAC1009\n")
    assert text.endswith("0\nENDSEC\n0\nEOF\n")
    # Une polyligne de trois points : deux LINE ; plus la ligne et la cache.
    assert text.count("0\nLINE\n") == 4
    assert "0\nSOLID\n" in text and "0\nTEXT\n" in text
    assert "2\nDASHED\n" in text and "8\ncache\n" in text
    # y vers le bas à l'écran, vers le haut en DXF : 40 → 170.
    assert "20\n170.0000\n" in text
    assert "1\nÉchelle 2:1\n" in text and "50\n90.0000\n" in text


@pytest.mark.parametrize("bad", [
    [{"k": "line", "a": [0, 0]}],
    [{"k": "fill", "pts": [[0, 0], [1, 1]]}],
    [{"k": "circle"}],
    [{"k": "line", "a": [0, 0], "b": [float("nan"), 1]}],
    "pas une liste",
])
def test_entites_mal_formees(bad):
    with pytest.raises((DxfError, TypeError, ValueError)):
        drawing_dxf(297, 210, bad)
