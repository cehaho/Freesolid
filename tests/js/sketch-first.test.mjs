// Fonction à profil sans esquisse libre : la garde rend exactement
// NO_SKETCH_AVAILABLE — c'est ce message que le panneau reconnaît pour
// faire choisir un plan, ouvrir l'esquisse et reprendre la fonction.

import { describe, it } from "node:test";
import assert from "node:assert/strict";

import { FEATURES, NO_SKETCH_AVAILABLE } from "../../app/features.js";

const empty = { lastTree: { features: [] }, selectedSketch: null,
                selection: () => null };

describe("fonction lancée sans esquisse", () => {
  const profiled = FEATURES.filter((f) => f.sketchProfile);

  it("extrusion et révolution sont des fonctions à profil", () => {
    const buttons = profiled.map((f) => f.button);
    for (const button of ["btn-pad", "btn-pocket", "btn-revolution"]) {
      assert.ok(buttons.includes(button), button);
    }
  });

  it("la garde rend le message reconnu, pour chacune", () => {
    for (const entry of profiled) {
      assert.equal(entry.guard(empty), NO_SKETCH_AVAILABLE, entry.button);
      assert.ok(entry.button, entry.title);
    }
  });
});
