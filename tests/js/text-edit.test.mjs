// Texte qu'on réédite : le panneau de la création, rempli ; seul ce qui a
// changé part au moteur.

import { describe, it } from "node:test";
import assert from "node:assert/strict";

import { dressupPickValues, textEditValues, textRows } from "../../app/features.js";

const text = { text: "AB", size: 6, depth: 1, x: 0, y: 2, face: 5 };

describe("texte réédité", () => {
  it("reprend le panneau de la création, sans le relief", () => {
    const rows = textRows(text);
    assert.deepEqual(rows.map((row) => row.key),
      ["content", "size", "depth", "x", "y"]);
    assert.deepEqual(rows.map((row) => row.value), ["AB", 6, 1, 0, 2]);
    assert.ok(textRows().some((row) => row.key === "emboss"));
  });

  it("n'envoie que ce qui change", () => {
    const same = { content: "AB", size: "6", depth: "1", x: "0", y: "2" };
    assert.deepEqual(textEditValues(same, text), {});
    assert.deepEqual(textEditValues({ ...same, content: " XY ", size: "5,5" },
                                    text), { text: "XY", size: 5.5 });
  });

  it("refuse un texte vide ou une cote invalide", () => {
    const same = { content: "AB", size: "6", depth: "1", x: "0", y: "2" };
    assert.equal(textEditValues({ ...same, content: "  " }, text), null);
    assert.equal(textEditValues({ ...same, depth: "0" }, text), null);
    assert.equal(textEditValues({ ...same, x: "" }, text), null);
  });

  it("sa face d'appui se compare comme celle d'un congé", () => {
    assert.deepEqual(dressupPickValues({ kind: "face", face: 5 },
                                       { face: 5 }), {});
    assert.deepEqual(dressupPickValues({ kind: "face", face: 0 },
                                       { face: 5 }), { face: 0 });
    // Face perdue (la pièce a changé en amont) : la zone se remplit.
    assert.deepEqual(dressupPickValues({ kind: "face", face: 0 },
                                       { face: null }), { face: 0 });
    assert.equal(dressupPickValues(null, { face: null }), null);
  });
});
