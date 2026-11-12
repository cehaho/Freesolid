import { describe, it } from "node:test";
import assert from "node:assert/strict";

import {
  holePositionValues, holePositions, holePositionsPick, holePositionsRow,
  holeSamePosition,
} from "../../app/features.js";
import { zoneToggle } from "../../app/panel.js";

describe("perçage : positions cliquées", () => {
  it("aucune position : la dernière esquisse sert", () => {
    assert.equal(holePositions(null), null);
    assert.equal(holePositions({ items: [] }), null);
  });

  it("des centres sur une face → face et points monde", () => {
    const sel = { items: [
      { kind: "point", face: 4, x: 10, y: 20, z: 8 },
      { kind: "point", face: 4, x: 40, y: 20, z: 8 },
    ] };
    assert.deepEqual(holePositions(sel),
      { face: 4, points: [[10, 20, 8], [40, 20, 8]] });
  });

  it("des centres sur deux faces sont refusés", () => {
    const sel = { items: [
      { kind: "point", face: 4, x: 0, y: 0, z: 0 },
      { kind: "point", face: 6, x: 1, y: 1, z: 1 },
    ] };
    assert.ok(holePositions(sel).error);
  });
});

describe("perçage réédité : ses positions", () => {
  const positions = { face: 5, points: [[5, 5, 10], [-5, -5, 10]] };

  it("reviennent dans la zone, comme les clics de la création", () => {
    assert.deepEqual(holePositionsPick(positions), { kind: "point", items: [
      { kind: "point", face: 5, x: 5, y: 5, z: 10 },
      { kind: "point", face: 5, x: -5, y: -5, z: 10 }] });
  });

  it("n'envoient que ce qui change, quel que soit l'ordre", () => {
    const zone = holePositionsPick(positions);
    assert.deepEqual(holePositionValues(
      { items: [...zone.items].reverse() }, positions), {});
    const moved = { items: [...zone.items,
      { kind: "point", face: 5, x: 0, y: 0, z: 10 }] };
    assert.deepEqual(holePositionValues(moved, positions), { positions: {
      face: 5, points: [[5, 5, 10], [-5, -5, 10], [0, 0, 10]] } });
  });

  it("vides ou sur deux faces : rien à appliquer", () => {
    assert.equal(holePositionValues({ items: [] }, positions), null);
    assert.equal(holePositionValues({ items: [
      { kind: "point", face: 5, x: 0, y: 0, z: 10 },
      { kind: "point", face: 1, x: 20, y: 0, z: 5 }] }, positions), null);
  });
});

describe("perçage : la zone des positions", () => {
  const row = holePositionsRow();
  const at = (face, x, y, z) => ({ kind: "point", face, x, y, z });
  const two = [at(5, 5, 5, 10), at(5, -5, -5, 10)];

  it("un clic pose un centre", () => {
    assert.deepEqual(zoneToggle(row, two, at(5, 0, 0, 10), { diameter: "4" }),
      [...two, at(5, 0, 0, 10)]);
  });

  it("un clic dans un trou le retire", () => {
    assert.deepEqual(zoneToggle(row, two, at(5, 6, 5.5, 10), { diameter: "4" }),
      [two[1]]);
    // Hors du trou (rayon 2) : un centre de plus.
    assert.equal(zoneToggle(row, two, at(5, 8, 5, 10), { diameter: "4" })
      .length, 3);
  });

  it("un clic sur une autre face repart de cette face", () => {
    assert.deepEqual(zoneToggle(row, two, at(1, 20, 0, 5), { diameter: "4" }),
      [at(1, 20, 0, 5)]);
  });

  it("deux positions de faces différentes ne se confondent pas", () => {
    assert.equal(holeSamePosition(at(5, 0, 0, 10), at(1, 0, 0, 10),
                                  { diameter: 4 }), false);
  });
});
