// Chanfrein de sommet qu'on réédite : son coin revient dans la zone, et
// seul ce qui a changé part au moteur.

import { describe, it } from "node:test";
import assert from "node:assert/strict";

import {
  vertexChamferDistances, vertexChamferEditValues, vertexChamferPick,
  vertexChamferPointValues, vertexChamferRow, vertexChamferRows,
} from "../../app/features.js";

const chamfer = { vertex: 5, distances: [2, 2, 2], point: [10, 10, 10] };

describe("coin d'un chanfrein de sommet réédité", () => {
  it("revient dans la zone, comme le clic de la création", () => {
    assert.deepEqual(vertexChamferPick(chamfer.point),
      { kind: "vertex", x: 10, y: 10, z: 10 });
    assert.equal(vertexChamferPick(null), null);
    const row = vertexChamferRow(vertexChamferPick(chamfer.point));
    assert.deepEqual(row.accepts, ["vertex"]);
    assert.deepEqual(row.value, { kind: "vertex", x: 10, y: 10, z: 10 });
    assert.equal("value" in vertexChamferRow(), false);
  });

  it("n'envoie le coin que s'il change", () => {
    assert.deepEqual(vertexChamferPointValues(
      { kind: "vertex", x: 10, y: 10, z: 10 }, chamfer.point), {});
    assert.deepEqual(vertexChamferPointValues(
      { kind: "vertex", x: -10, y: -10, z: 10 }, chamfer.point),
      { point: [-10, -10, 10] });
    assert.equal(vertexChamferPointValues(null, chamfer.point), null);
  });
});

describe("distances d'un chanfrein de sommet réédité", () => {
  const values = (distances) => {
    const rows = vertexChamferRows({ distances });
    return Object.fromEntries(rows.map((row) => [row.key, row.value]));
  };

  it("reviennent dans le panneau de la création", () => {
    assert.deepEqual(vertexChamferDistances(values([2, 2, 2])), [2]);
    assert.deepEqual(vertexChamferDistances(values([1, 2, 3])), [1, 2, 3]);
  });

  it("n'envoient que ce qui change", () => {
    assert.deepEqual(vertexChamferEditValues(values([2, 2, 2]), chamfer), {});
    assert.deepEqual(vertexChamferEditValues(values([1, 2, 3]), chamfer),
      { distances: [1, 2, 3] });
    assert.deepEqual(vertexChamferEditValues(
      { vkind: "egale", d1: "3" }, chamfer), { distances: [3] });
    assert.equal(vertexChamferEditValues(
      { vkind: "egale", d1: "0" }, chamfer), null);
  });
});
