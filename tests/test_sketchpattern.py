"""Répétition pilotée par esquisse : la description rangée sur la forme
figée et la fonction."""

from engine.sketchpattern import format_spec, parse_spec


def test_spec_round_trip():
    spec = format_spec("Sketch002", ["Pocket", "Pad001"])
    assert spec == "Sketch002;Pocket,Pad001"
    assert parse_spec(spec) == ("Sketch002", ["Pocket", "Pad001"])


def test_spec_without_features():
    assert parse_spec("Sketch") == ("Sketch", [])


def test_offsets_round_trip():
    from engine.sketchpattern import format_offsets, parse_offsets
    source = format_offsets([[20, 0, 0], [12.5, -6, 0]])
    assert source == "@20,0,0/12.5,-6,0"
    assert parse_offsets(source) == [[20.0, 0.0, 0.0], [12.5, -6.0, 0.0]]
    assert parse_offsets("Sketch") is None


def test_offsets_checked():
    from engine.sketchpattern import check_offsets
    assert check_offsets([[1, 2]]) == ([[1.0, 2.0, 0.0]], None)
    assert check_offsets([])[1]
    assert check_offsets([["a", 1, 2]])[1]
    assert check_offsets([[1, 2, 3, 4]])[1]
