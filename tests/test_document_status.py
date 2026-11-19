"""Document modifié : suivi par l'aiguillage des opérations, sans FreeCAD."""

import os

os.environ.setdefault("FREESOLID_NO_SERVE", "1")

from engine import kernel as kernel_mod  # noqa: E402
from engine.kernel import Kernel          # noqa: E402


def _kernel(monkeypatch, *ops):
    k = Kernel()
    for op in ops:
        monkeypatch.setattr(k, op, lambda **_params: {}, raising=False)
    return k


def _status(k):
    return kernel_mod.dispatch(k, "document_status", {})["result"]


def test_neuf_puis_modifie_puis_enregistre(monkeypatch):
    k = _kernel(monkeypatch, "new_part", "add_pad", "save_part")
    assert _status(k)["modified"] is False
    kernel_mod.dispatch(k, "new_part", {})
    assert _status(k)["modified"] is False
    kernel_mod.dispatch(k, "add_pad", {})
    assert _status(k)["modified"] is True
    kernel_mod.dispatch(k, "save_part", {})
    assert _status(k)["modified"] is False


def test_annuler_et_glisser_modifient(monkeypatch):
    for op in ("undo", "redo", "sketch_move"):
        k = _kernel(monkeypatch, op)
        kernel_mod.dispatch(k, op, {})
        assert _status(k)["modified"] is True, op


def test_lecture_et_echec_ne_modifient_pas(monkeypatch):
    k = _kernel(monkeypatch, "get_tree", "tessellate")
    kernel_mod.dispatch(k, "get_tree", {})
    kernel_mod.dispatch(k, "tessellate", {})
    assert _status(k)["modified"] is False

    def refuse(**_params):
        raise kernel_mod.KernelError("non")
    monkeypatch.setattr(k, "add_pad", refuse, raising=False)
    kernel_mod.dispatch(k, "add_pad", {})
    assert _status(k)["modified"] is False


def test_le_fichier_du_document(monkeypatch):
    # Ctrl+S écrit dans le .FCStd du document ; un document neuf ou
    # importé (STEP) n'en a pas encore.
    import types
    k = Kernel()
    assert _status(k)["path"] is None
    k._doc = types.SimpleNamespace(FileName="")
    assert _status(k)["path"] is None
    k._doc = types.SimpleNamespace(FileName="C:/pieces/bloc.FCStd")
    assert _status(k)["path"] == "C:/pieces/bloc.FCStd"
    k._doc = types.SimpleNamespace(FileName="C:/pieces/cube.step")
    assert _status(k)["path"] is None
