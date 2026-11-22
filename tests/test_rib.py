"""Nervure : la description rangée sur la forme figée et la fonction."""

from engine.rib import check_params, format_spec, parse_spec


def test_spec_round_trip():
    spec = format_spec("Sketch001", 3, "normal", True)
    assert spec == "Sketch001;3;normal;1"
    assert parse_spec(spec) == ("Sketch001", 3.0, "normal", True)


def test_spec_defaults():
    assert parse_spec("Sketch;2.5") == ("Sketch", 2.5, "parallel", False)


def test_check_params():
    assert check_params(3, "parallel") is None
    assert check_params(0, "parallel") == "épaisseur de nervure invalide"
    assert check_params("x", "normal") == "épaisseur de nervure invalide"
    assert "inconnue" in check_params(2, "oblique")
