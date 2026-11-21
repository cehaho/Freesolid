// Zones d'arêtes : celles du congé et du chanfrein en prennent plusieurs
// (`edgeSet` : le clic simple ajoute, un second retire) ; la direction
// d'une répétition n'en tient qu'une (le clic la remplace).

import { describe, it } from "node:test";
import assert from "node:assert/strict";

import { FEATURES } from "../../app/features.js";

const ctx = { selection: () => null, lastTree: null };

function edgeZones(button) {
  const spec = FEATURES.find((f) => f.button === button);
  assert.ok(spec, button);
  const groups = typeof spec.groups === "function" ? spec.groups(ctx) : spec.groups;
  return groups.flatMap((g) => g.rows ?? [])
    .filter((row) => row.type === "selection"
      && (row.accepts ?? []).includes("edges"));
}

describe("zones d'arêtes", () => {
  it("congé et chanfrein prennent plusieurs arêtes", () => {
    for (const button of ["btn-fillet", "btn-chamfer"]) {
      const zones = edgeZones(button);
      assert.equal(zones.length, 1, button);
      assert.equal(zones[0].edgeSet, true, button);
    }
  });

  it("la direction d'une répétition n'en tient qu'une", () => {
    for (const button of ["btn-linpattern", "btn-polpattern"]) {
      const zones = edgeZones(button);
      assert.ok(zones.length, button);
      assert.ok(zones.every((row) => !row.edgeSet), button);
    }
  });
});
