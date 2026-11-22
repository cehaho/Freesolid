// Symétrie : une face cliquée avant la commande devient le plan de
// symétrie, comme dans les modeleurs courants.

import { describe, it } from "node:test";
import assert from "node:assert/strict";

import { FEATURES } from "../../app/features.js";

const mirror = FEATURES.find((f) => f.button === "btn-mirror");
const planeRows = (ctx) =>
  mirror.groups(ctx).find((g) => g.label === "Plan de symétrie").rows;

describe("symétrie et présélection", () => {
  it("une face présélectionnée devient le plan de symétrie", () => {
    const ctx = { selection: (accepts) =>
      accepts.includes("face") ? { kind: "face", face: 1 } : null };
    const [plane, face] = planeRows(ctx);
    assert.equal(plane.value, "face");
    assert.deepEqual(face.value, { kind: "face", face: 1 });
  });

  it("sans face présélectionnée : le plan de droite", () => {
    const [plane, face] = planeRows({ selection: () => null });
    assert.equal(plane.value, "YZ");
    assert.equal(face.value, null);
  });
});
