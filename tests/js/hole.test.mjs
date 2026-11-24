import { describe, it } from "node:test";
import assert from "node:assert/strict";

import {
  FEATURES, hasFreeSketch, holePositionValues, holePositions, holePositionsPick, holePositionsRow,
  holeSamePlane, holeSamePosition,
} from "../../app/features.js";
import { movePosition, planeAxes, zoneToggle } from "../../app/panel.js";

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

  it("le point de la face présélectionnée est la première position", () => {
    const hole = FEATURES.find((e) => e.button === "btn-hole");
    const picked = { kind: "point", items: [at(5, 1, 2, 10)] };
    const asked = [];
    const groups = hole.groups({ lastTree: { bodies: [] },
      selection: (accepts) => { asked.push(accepts); return picked; } });
    assert.deepEqual(asked[0], ["point"]);
    assert.equal(groups[0].rows[0].value, picked);
    // Rien de présélectionné : la zone attend les clics.
    const empty = FEATURES.find((e) => e.button === "btn-hole")
      .groups({ lastTree: { bodies: [] }, selection: () => null });
    assert.equal("value" in empty[0].rows[0], false);
  });

  it("deux positions de faces différentes ne se confondent pas", () => {
    assert.equal(holeSamePosition(at(5, 0, 0, 10), at(1, 0, 0, 10),
                                  { diameter: 4 }), false);
  });
});

describe("perçage : rien à percer tant qu'on n'a pas cliqué", () => {
  const hole = FEATURES.find((e) => e.button === "btn-hole");
  const values = { diameter: 6, cond: "travers", cut: "none" };
  const at = { items: [{ kind: "point", face: 0, x: 1, y: 2, z: 3 }] };

  it("ni position ni esquisse libre : pas d'aperçu, le panneau le dit",
     () => {
    const ctx = { lastTree: { bodies: [], features: [
      { name: "Revolution", type_key: "revolution" }] } };
    assert.equal(hasFreeSketch(ctx.lastTree), false);
    assert.equal(hole.build(values, ctx), null);
    assert.equal(hole.invalid(values, ctx),
                 "Cliquez les centres des trous sur une face");
    assert.deepEqual(hole.build({ ...values, pos: at }, ctx).params.points,
                     [[1, 2, 3]]);
  });

  it("une esquisse libre sert sans position ; une désactivée non", () => {
    const free = { lastTree: { bodies: [], features: [
      { name: "Sketch", type_key: "sketch" }] } };
    assert.equal(hole.build(values, free).op, "add_hole");
    const off = { lastTree: { bodies: [], features: [
      { name: "Sketch", type_key: "sketch", suppressed: true }] } };
    assert.equal(hole.build(values, off), null);
  });
});

describe("perçage : positions tapées", () => {
  it("les axes du plan d'une face perpendiculaire à un axe", () => {
    assert.deepEqual(planeAxes([0, 0, 1]), [0, 1]);
    assert.deepEqual(planeAxes([0, -1, 0]), [0, 2]);
    assert.deepEqual(planeAxes({ x: 1, y: 0, z: 0 }), [1, 2]);
    assert.equal(planeAxes([0, 0.6, 0.8]), null);
    assert.equal(planeAxes(null), null);
  });

  it("une coordonnée retapée devient une cote", () => {
    const items = [{ kind: "point", face: 5, x: -32.5, y: -18, z: 15 },
                   { kind: "point", face: 5, x: 30, y: 10, z: 15 }];
    const moved = movePosition(items, 0, 0, -40);
    assert.deepEqual(moved[0],
      { kind: "point", face: 5, x: -40, y: -18, z: 15, typed: true });
    assert.equal(moved[1], items[1]);
    assert.deepEqual(holePositions({ items: moved }), { face: 5,
      points: [[-40, -18, 15], [30, 10, 15]], dims: [true, false] });
  });

  it("rééditées, elles gardent leurs cotes", () => {
    const positions = { face: 5, points: [[-40, 0, 15], [30, 10, 15]],
                        normal: [0, 0, 1], dims: [true, false] };
    const zone = holePositionsPick(positions);
    assert.equal(zone.items[0].typed, true);
    assert.equal(zone.items[1].typed, undefined);
    assert.deepEqual(zone.items[0].normal, [0, 0, 1]);
    assert.deepEqual(holePositionValues(zone, positions), {});
    const retyped = { items: movePosition(zone.items, 1, 1, 10) };
    assert.deepEqual(holePositionValues(retyped, positions).positions.dims,
      [true, true]);
  });

  it("la zone des positions montre leurs coordonnées", () => {
    assert.equal(holePositionsRow().coords, true);
  });
});

describe("perçage : positions sur des faces au même plan", () => {
  const up = [0, 0, 1];
  const a = { kind: "point", face: 7, x: -30, y: 0, z: 9, normal: up };
  const b = { kind: "point", face: 9, x: 30, y: 0, z: 9, normal: up };
  const low = { kind: "point", face: 2, x: 0, y: 10, z: 5, normal: up };

  it("deux faces au même plan vont ensemble, pas une plus basse", () => {
    assert.equal(holeSamePlane(a, b), true);
    assert.equal(holeSamePlane(a, low), false);
    assert.equal(holeSamePlane(a, { ...b, normal: [0, 0, -1] }), false);
    assert.equal(holeSamePlane(a, { ...b, normal: undefined }), false);
  });

  it("le clic sur l'autre embase ajoute une position", () => {
    const row = holePositionsRow(null);
    assert.deepEqual(zoneToggle(row, [a], b, {}), [a, b]);
    assert.deepEqual(zoneToggle(row, [a], low, {}), [low]);
  });

  it("le moteur reçoit la face de la première et tous les centres", () => {
    assert.deepEqual(holePositions({ items: [a, b] }),
      { face: 7, points: [[-30, 0, 9], [30, 0, 9]] });
    assert.ok(holePositions({ items: [a, low] }).error);
  });
});
