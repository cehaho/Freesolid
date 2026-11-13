// Plan d'une esquisse (« Changer de plan… ») : la liste revient sur son
// plan actuel, et seul ce qui change part au moteur.

import { describe, it } from "node:test";
import assert from "node:assert/strict";

import {
  sketchFaceValues, sketchPlaneChoice, sketchPlaneOptions, sketchPlaneValues,
} from "../../app/sketchplane.js";

describe("plan d'une esquisse", () => {
  const tree = {
    planes: [{ id: "XY", label: "Plan de dessus" },
             { id: "XZ", label: "Plan de face" }],
    features: [{ type_key: "datum_plane", name: "DatumPlane", label: "Plan1" },
               { type_key: "pad", name: "Pad", label: "Extrusion" }],
  };

  it("propose l'origine, les plans de référence, puis une face", () => {
    assert.deepEqual(sketchPlaneOptions(tree).map(([id]) => id),
      ["XY", "XZ", "datum:DatumPlane", "face"]);
    assert.deepEqual(sketchPlaneOptions(undefined), [["face", "Face du solide"]]);
  });

  it("ne propose pas un plan de référence qui vient après l'esquisse", () => {
    const later = {
      planes: tree.planes,
      features: [{ type_key: "datum_plane", name: "Avant", label: "P1", order: 2 },
                 { type_key: "datum_plane", name: "Apres", label: "P2", order: 9 }],
    };
    const sketch = { name: "Sketch", order: 5, support: { plane: "XY" } };
    assert.deepEqual(sketchPlaneOptions(later, sketch).map(([id]) => id),
      ["XY", "XZ", "datum:Avant", "face"]);
    // Son plan actuel reste, même venu après (un fichier d'avant).
    const onLater = { ...sketch, support: { datum: "Apres" } };
    assert.deepEqual(sketchPlaneOptions(later, onLater).map(([id]) => id),
      ["XY", "XZ", "datum:Avant", "datum:Apres", "face"]);
  });

  it("revient sur son plan actuel", () => {
    assert.equal(sketchPlaneChoice({ plane: "XZ" }), "XZ");
    assert.equal(sketchPlaneChoice({ datum: "DatumPlane" }), "datum:DatumPlane");
    assert.equal(sketchPlaneChoice({ face: 5 }), "face");
    // Face perdue : toujours « Face du solide », la zone vide.
    assert.equal(sketchPlaneChoice({ face: null }), "face");
    assert.equal(sketchPlaneChoice(null), "XY");
  });

  it("n'envoie que le plan qui change", () => {
    assert.deepEqual(sketchPlaneValues({ support: "XZ" }, { plane: "XZ" }), {});
    assert.deepEqual(sketchPlaneValues({ support: "XY" }, { plane: "XZ" }),
      { plane: "XY" });
    assert.deepEqual(sketchPlaneValues({ support: "datum:DatumPlane" },
                                       { face: 5 }), { datum: "DatumPlane" });
    assert.deepEqual(sketchPlaneValues({ support: "face" }, { plane: "XY" }), {});
  });

  it("la face d'accueil : seulement si elle change, et pas vide", () => {
    assert.deepEqual(sketchFaceValues({ support: "XY" }, { face: 5 }), {});
    assert.deepEqual(sketchFaceValues(
      { support: "face", face: { kind: "face", face: 5 } }, { face: 5 }), {});
    assert.deepEqual(sketchFaceValues(
      { support: "face", face: { kind: "face", face: 1 } }, { face: 5 }),
      { face: 1 });
    assert.deepEqual(sketchFaceValues(
      { support: "face", face: { kind: "face", face: 1 } }, { plane: "XY" }),
      { face: 1 });
    assert.equal(sketchFaceValues({ support: "face", face: null },
                                  { plane: "XY" }), null);
  });
});
