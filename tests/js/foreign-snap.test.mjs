import { describe, it } from "node:test";
import assert from "node:assert/strict";

import {
  engineSnaps, foreignSnapPoints, foreignVertexId, foreignVertexOf,
} from "../../app/sketchsnap.js";

describe("accrochage aux sommets des autres esquisses", () => {
  const foreign = [{ sketch: "Sketch", label: "Esquisse1", vertex: 2,
                     x: -30, y: 0 }];

  it("chaque sommet devient un point d'accrochage", () => {
    assert.deepEqual(foreignSnapPoints(foreign), [
      { geo: foreignVertexId("Sketch", 2), point: 1, x: -30, y: 0 }]);
  });

  it("un sommet déjà repris dans l'esquisse n'est pas offert deux fois", () => {
    const externals = [{ id: -3, type: "point", p1: [-30, 0], external: true }];
    assert.deepEqual(foreignSnapPoints(foreign, { externals }), []);
  });

  it("l'id se relit, et part au moteur en { sketch, vertex }", () => {
    const id = foreignVertexId("Sketch001", 4);
    assert.deepEqual(foreignVertexOf(id), { sketch: "Sketch001", vertex: 4 });
    assert.equal(foreignVertexOf("edge:3"), null);
    assert.equal(foreignVertexOf(5), null);
    assert.deepEqual(engineSnaps({ center: { geo: id, point: 1 } }),
      { center: { geo: { sketch: "Sketch001", vertex: 4 }, point: 1 } });
  });
});
