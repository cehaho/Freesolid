// Coin d'esquisse cliqué par son sommet (congé, chanfrein d'esquisse).
import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { cornerAt } from "../../app/geom2d.js";

const L = (id, p1, p2) => ({ id, type: "line", p1, p2 });

describe("cornerAt", () => {
  it("deux lignes qui se joignent au sommet : le coin, un point près du coin sur chacune", () => {
    const entities = [L(0, [-60, 40], [60, 40]), L(1, [-60, -40], [-60, 40])];
    assert.deepEqual(cornerAt(entities, { x: -60, y: 40 }), {
      geo1: 0, geo2: 1, p1: { x: -30, y: 40 }, p2: { x: -60, y: 20 } });
  });

  it("un bout seul, trois lignes, un cercle : pas de coin", () => {
    const two = [L(0, [0, 0], [10, 0]), L(1, [0, 0], [0, 10])];
    assert.equal(cornerAt(two, { x: 10, y: 0 }), null);
    assert.equal(cornerAt([...two, L(2, [0, 0], [-5, -5])], { x: 0, y: 0 }), null);
    assert.equal(cornerAt([{ id: 0, type: "circle", c: [0, 0], r: 5 }],
                          { x: 0, y: 0 }), null);
  });
});
