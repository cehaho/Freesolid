"""Répétition pilotée par esquisse : la description rangée sur la forme
figée et la fonction."""

from engine.sketchpattern import format_spec, parse_spec


def test_spec_round_trip():
    spec = format_spec("Sketch002", ["Pocket", "Pad001"])
    assert spec == "Sketch002;Pocket,Pad001"
    assert parse_spec(spec) == ("Sketch002", ["Pocket", "Pad001"])


def test_spec_without_features():
    assert parse_spec("Sketch") == ("Sketch", [])
