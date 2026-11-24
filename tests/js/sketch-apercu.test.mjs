import { describe, it } from "node:test";
import assert from "node:assert/strict";

import { setLinePoints } from "../../app/sketch/apercu.js";

class FakeGeometry {
  constructor() { this.points = null; this.disposed = false; }
  setFromPoints(points) { this.points = points; return this; }
  dispose() { this.disposed = true; }
}

describe("aperçu d'esquisse : setLinePoints", () => {
  it("donne une géométrie neuve, assez grande, et libère l'ancienne", () => {
    const first = new FakeGeometry().setFromPoints([1, 2]);
    const line = { geometry: first };
    const arc = Array.from({ length: 40 }, (_, i) => i);
    setLinePoints(line, arc);
    assert.notEqual(line.geometry, first);
    assert.ok(line.geometry instanceof FakeGeometry);
    assert.deepEqual(line.geometry.points, arc);
    assert.equal(first.disposed, true);
  });
});
