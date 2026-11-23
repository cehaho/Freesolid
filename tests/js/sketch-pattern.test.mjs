import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { FEATURES, sketchPatternBuild } from "../../app/features.js";

describe("répétition pilotée par esquisse", () => {
  it("a son bouton, à profil d'esquisse", () => {
    const entry = FEATURES.find((e) => e.button === "btn-sketch-pattern");
    assert.equal(entry?.op, "add_sketch_pattern");
    assert.equal(entry?.sketchProfile, true);
  });

  it("envoie les fonctions choisies, sinon rien (la dernière)", () => {
    assert.deepEqual(sketchPatternBuild({ features: { items: [
      { kind: "feature", name: "Pocket" }, { kind: "feature", name: "Pad001" },
    ] } }), { op: "add_sketch_pattern",
              params: { features: ["Pocket", "Pad001"] } });
    assert.deepEqual(sketchPatternBuild({}),
      { op: "add_sketch_pattern", params: {} });
  });
});

import { tablePatternBuild, tableOffsetsValues } from "../../app/features.js";

describe("répétition pilotée par table", () => {
  it("envoie les décalages, rien sans ligne", () => {
    assert.deepEqual(tablePatternBuild({ offsets: [[20, 0, 0], [5, 5, 0]] }),
      { op: "add_table_pattern",
        params: { offsets: [[20, 0, 0], [5, 5, 0]] } });
    assert.equal(tablePatternBuild({ offsets: [] }), null);
  });

  it("réédition : seulement une table changée", () => {
    const before = [[20, 0, 0]];
    assert.deepEqual(tableOffsetsValues({ offsets: [[20, 0, 0]] }, before), {});
    assert.deepEqual(tableOffsetsValues({ offsets: [[20, 5, 0]] }, before),
      { offsets: [[20, 5, 0]] });
    assert.equal(tableOffsetsValues({ offsets: [] }, before), null);
  });
});
