"""Validation du plan neutre de dépouille — pur Python, sans FreeCAD."""

import pytest

from engine.kernel import KernelError, parse_neutral_plane


def test_parse_neutral_plane_defaults_and_aliases():
    assert parse_neutral_plane() == "XY"
    assert parse_neutral_plane("XY") == "XY"
    assert parse_neutral_plane("xz") == "XZ"
    assert parse_neutral_plane("Yz") == "YZ"


def test_parse_neutral_plane_rejects_unknown():
    with pytest.raises(KernelError) as excinfo:
        parse_neutral_plane("UV")
    assert "plan neutre inconnu" in str(excinfo.value)
    assert "UV" in str(excinfo.value)


def test_draft_replay_keeps_its_neutral_plane():
    """Le rejeu (répétition variable) rappelait add_draft sans plan
    neutre : une dépouille XZ ou YZ revenait en XY."""
    from engine.ops.habillage import _rejouer_depouille
    calls = []

    class Noyau:
        def add_draft(self, **params):
            calls.append(params)

    feat = {"name": "Draft", "faces": [4], "neutral": "XZ"}
    _rejouer_depouille(Noyau(), feat, None, lambda prop: 5.0)
    assert calls == [{"face": 4, "angle": 5.0, "neutral": "XZ"}]


def test_draft_replay_keeps_faces_neutral_face_and_sense():
    """Plusieurs faces, une face pour plan neutre, sens inversé : le
    rejeu les rend tels quels."""
    from engine.ops.habillage import _rejouer_depouille
    calls = []

    class Noyau:
        def add_draft(self, **params):
            calls.append(params)

    feat = {"name": "Draft", "faces": [0, 1, 2, 3], "neutral": "XY",
            "neutral_face": 4, "reversed": True}
    _rejouer_depouille(Noyau(), feat, None, lambda prop: 5.0)
    assert calls == [{"faces": [0, 1, 2, 3], "angle": 5.0, "neutral": "XY",
                      "neutral_face": 4, "reversed": True}]
