import { describe, it } from "node:test";
import assert from "node:assert/strict";

import { relationGlyphs } from "../../app/geom2d.js";

const line = (id, p1, p2) => ({ id, type: "line", p1, p2 });

describe("relationGlyphs", () => {
  it("H sur une ligne horizontale, décalé hors de la ligne", () => {
    const g = relationGlyphs(
      [{ type: "Horizontal", geos: [0, null, null] }],
      [line(0, [0, 0], [10, 0])], 2);
    assert.equal(g.length, 1);
    assert.equal(g[0].text, "H");
    assert.equal(g[0].x, 5);
    assert.equal(g[0].y, 2);
  });

  it("une relation entre deux lignes se marque sur chacune", () => {
    const g = relationGlyphs(
      [{ type: "Parallel", geos: [0, 1, null] }],
      [line(0, [0, 0], [10, 0]), line(1, [0, 5], [10, 5])]);
    assert.deepEqual(g.map((x) => [x.text, x.geo]), [["∥", 0], ["∥", 1]]);
  });

  it("une horizontale entre deux points ne marque aucune courbe", () => {
    assert.deepEqual(relationGlyphs(
      [{ type: "Horizontal", geos: [1, 0, null], pos: [2, 3, 0] }],
      [{ id: 0, type: "circle", c: [0, 0], r: 5 }, line(1, [-9, -9], [5, 0])]),
    []);
  });

  it("les coïncidences ne sont pas marquées", () => {
    assert.deepEqual(relationGlyphs(
      [{ type: "Coincident", geos: [0, 1, null] }],
      [line(0, [0, 0], [1, 0]), line(1, [1, 0], [1, 1])]), []);
  });

  it("deux symboles sur la même entité ne se superposent pas", () => {
    const g = relationGlyphs(
      [{ type: "Horizontal", geos: [0] }, { type: "Equal", geos: [0, 1] }],
      [line(0, [0, 0], [10, 0]), line(1, [0, 5], [10, 5])], 2);
    const onFirst = g.filter((x) => x.geo === 0);
    assert.equal(onFirst.length, 2);
    assert.notEqual(onFirst[0].y, onFirst[1].y);
  });

  it("les axes et la géométrie externe (géo négative) sont ignorés", () => {
    assert.equal(relationGlyphs(
      [{ type: "Parallel", geos: [0, -1, null] }],
      [line(0, [0, 0], [10, 0])]).length, 1);
  });
});

describe("symboles sans chevauchement", () => {
  const overlap = (a, b, size) => Math.abs(a.x - b.x) < size * 0.8
    && Math.abs(a.y - b.y) < size * 0.8;
  it("deux segments proches : leurs symboles ne se couvrent pas", () => {
    const g = relationGlyphs(
      [{ type: "Horizontal", geos: [0] }, { type: "Horizontal", geos: [1] }],
      [line(0, [0, 0], [10, 0]), line(1, [0, 1], [10, 1])], 1,
      { size: 1.5 });
    assert.equal(g.length, 2);
    assert.ok(!overlap(g[0], g[1], 1.5));
  });

  it("une étiquette de cote repousse le symbole de l'autre côté", () => {
    // V de la ligne x = 0 : d'office à droite (x = +2), là où est la cote.
    const g = relationGlyphs([{ type: "Vertical", geos: [0] }],
      [line(0, [0, 10], [0, 0])], 2,
      { size: 2, obstacles: { boxes: [{ x: 2, y: 5, hw: 2, hh: 1 }] } });
    assert.ok(g[0].x < 0);
  });

  it("petite entité : ses symboles restent hors du tracé et séparés", () => {
    const square = [line(0, [0, 0], [1, 0]), line(1, [1, 0], [1, 1]),
                    line(2, [1, 1], [0, 1]), line(3, [0, 1], [0, 0])];
    const g = relationGlyphs(
      [0, 2].map((i) => ({ type: "Horizontal", geos: [i] }))
        .concat([1, 3].map((i) => ({ type: "Vertical", geos: [i] }))),
      square, 1.2, { size: 1.5 });
    assert.equal(g.length, 4);
    for (const a of g) {
      assert.ok(a.x < -0.5 || a.x > 1.5 || a.y < -0.5 || a.y > 1.5);
      for (const b of g) if (a !== b) assert.ok(!overlap(a, b, 1.5));
    }
  });
});

describe("ancres des entités bloquées", () => {
  it("disparaissent quand elles sont trop nombreuses", async () => {
    const { MAX_BLOCK_GLYPHS, relationGlyphs: glyphs } =
      await import("../../app/geom2d.js");
    const lines = Array.from({ length: MAX_BLOCK_GLYPHS + 1 }, (_, i) =>
      ({ id: i, type: "line", p1: [0, i], p2: [5, i] }));
    const blocks = lines.map((l) => ({ type: "Block", geos: [l.id] }));
    assert.equal(glyphs(blocks.slice(0, 2), lines).length, 2);
    assert.equal(glyphs(blocks, lines).length, 0);
  });
});
