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
