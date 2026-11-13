import { describe, it } from "node:test";
import assert from "node:assert/strict";

import {
  datumPlaneBuild,
  datumPlaneEditValues,
  datumPlaneGroups,
  datumPlaneSpecValues,
  referenceBuild,
  referenceEditValues,
  referenceGroups,
  referenceItems,
  referenceSpecValues,
} from "../../app/refgeom.js";

describe("géométrie de référence", () => {
  it("garde les axes, points et repères placés, hors barre de retour", () => {
    const m = Array(16).fill(0);
    const items = referenceItems({ features: [
      { name: "A", type_key: "datum_axis", placement: m },
      { name: "D", type_key: "datum_axis", placement: m, suppressed: true },
      { name: "B", type_key: "datum_point", placement: m, rolled_back: true },
      { name: "P", type_key: "datum_plane", placement: m },
      { name: "Pad", type_key: "pad",
        children: [{ name: "C", type_key: "datum_cs", placement: m }] },
    ] });
    assert.deepEqual(items.map((i) => [i.name, i.shape]), [["A", "axis"], ["C", "cs"]]);
  });

  it("traduit le panneau en paramètres de l'op", () => {
    assert.deepEqual(referenceBuild("axis", { by: "Y" }),
      { op: "add_datum_axis", params: { axis: "Y" } });
    assert.deepEqual(referenceBuild("axis", { by: "edge", edge: { edges: [4] } }),
      { op: "add_datum_axis", params: { edge: 4 } });
    assert.equal(referenceBuild("axis", { by: "edge" }), null);
    assert.deepEqual(referenceBuild("point",
      { by: "vertex", vertex: { kind: "vertex", x: 1, y: 2, z: 3 } }),
      { op: "add_datum_point", params: { vertex: [1, 2, 3] } });
    assert.deepEqual(referenceBuild("cs", { by: "xyz", x: "1", y: 0, z: -2 }),
      { op: "add_datum_cs", params: { point: [1, 0, -2] } });
    assert.equal(referenceBuild("cs", { by: "xyz", x: "a", y: 0, z: 0 }), null);
  });

  it("pose un plan sur sa face, sinon sur le plan d'origine choisi", () => {
    assert.deepEqual(datumPlaneBuild({ sel: { kind: "face", face: 3 },
      base: "XY", offset: "5", angle: 0 }),
    { op: "add_datum_plane", params: { offset: 5, angle: 0, face: 3 } });
    assert.deepEqual(datumPlaneBuild({ sel: null, base: "YZ", offset: "",
      angle: "30" }),
    { op: "add_datum_plane", params: { offset: 0, angle: 30, base: "YZ" } });
    const [support, position] = datumPlaneGroups({ base: "XZ", offset: 4 });
    assert.deepEqual(support.rows.map((r) => [r.key, r.value ?? null]),
      [["sel", null], ["base", "XZ"]]);
    assert.deepEqual(position.rows.map((r) => [r.key, r.value]),
      [["offset", 4], ["angle", 0]]);
  });

  it("rouvre un plan rempli de ce qui le porte", () => {
    assert.deepEqual(datumPlaneSpecValues(
      { kind: "plane", face: 2, offset: 3, angle: 15 }),
    { face: { kind: "face", face: 2 }, base: "", offset: 3, angle: 15 });
    assert.deepEqual(datumPlaneSpecValues(
      { kind: "plane", base: "YZ", offset: 0, angle: 0 }),
    { face: null, base: "YZ", offset: 0, angle: 0 });
    // Une face perdue au rang : la zone vient vide, la liste sans choix.
    const lost = datumPlaneSpecValues({ kind: "plane", face: null });
    assert.equal(lost.face, null);
    assert.equal(lost.base, "");
  });

  it("n'envoie d'un plan réédité que ce qui change", () => {
    const onFace = { kind: "plane", face: 2, offset: 3, angle: 0 };
    const same = { sel: { kind: "face", face: 2 }, base: "", offset: "3",
                   angle: 0 };
    assert.deepEqual(datumPlaneEditValues(same, onFace), {});
    assert.deepEqual(datumPlaneEditValues({ ...same, offset: "7,5" }, onFace),
      { offset: 7.5 });
    assert.deepEqual(datumPlaneEditValues(
      { ...same, sel: { kind: "face", face: 5 } }, onFace), { face: 5 });
    // La zone vidée par la liste : le plan d'origine choisi.
    assert.deepEqual(datumPlaneEditValues({ ...same, sel: null, base: "XZ" },
      onFace), { base: "XZ" });
    // La face disparue au rang, rien de choisi : le plan reste où il est.
    const lost = { kind: "plane", face: null, offset: 3, angle: 0 };
    assert.deepEqual(datumPlaneEditValues({ ...same, sel: null }, lost), {});
    assert.deepEqual(datumPlaneEditValues(
      { ...same, sel: null, offset: "4" }, lost), { offset: 4 });
    const onBase = { kind: "plane", base: "XZ", offset: 0, angle: 0 };
    assert.deepEqual(datumPlaneEditValues(
      { sel: null, base: "XZ", offset: 0, angle: "45" }, onBase), { angle: 45 });
    assert.equal(datumPlaneEditValues({ ...same, angle: "x" }, onFace), null);
  });

  it("rouvre un axe, un point, un repère sur ce qui les porte", () => {
    assert.deepEqual(referenceSpecValues({ kind: "axis", axis: "Y" }),
      { by: "Y", edge: null });
    assert.deepEqual(referenceSpecValues({ kind: "axis", edge: 4 }),
      { by: "edge", edge: { kind: "edges", edges: [4] } });
    assert.deepEqual(referenceSpecValues({ kind: "point", vertex: [1, 2, 3] }),
      { by: "vertex", vertex: { kind: "vertex", x: 1, y: 2, z: 3 } });
    assert.deepEqual(referenceSpecValues({ kind: "point", edge: 7 }),
      { by: "center", edge: { kind: "edges", edges: [7] } });
    // L'arête perdue au rang : la zone vient vide, toujours au centre.
    assert.deepEqual(referenceSpecValues({ kind: "point", edge: null }),
      { by: "center", edge: null });
    assert.deepEqual(referenceSpecValues({ kind: "cs", point: [4, 5, 6] }),
      { by: "xyz", point: [4, 5, 6] });
    const [group] = referenceGroups("cs", { by: "xyz", point: [4, 5, 6] });
    assert.deepEqual(group.rows.map((r) => [r.key, r.value ?? null]),
      [["by", "xyz"], ["edge", null], ["vertex", null], ["x", 4], ["y", 5],
       ["z", 6]]);
    assert.equal(referenceGroups("axis")[0].rows[0].value, "Z");
    assert.equal(referenceGroups("axis", { edge: { edges: [1] } })[0].rows[0]
      .value, "edge");
  });

  it("n'envoie d'un axe, d'un point, d'un repère que l'appui qui change", () => {
    const axis = { kind: "axis", edge: 4 };
    assert.deepEqual(referenceEditValues("axis",
      { by: "edge", edge: { edges: [4] } }, axis), {});
    assert.deepEqual(referenceEditValues("axis", { by: "X" }, axis),
      { axis: "X" });
    assert.equal(referenceEditValues("axis", { by: "edge", edge: null }, axis),
      null);
    const point = { kind: "point", vertex: [1, 2, 3] };
    assert.deepEqual(referenceEditValues("point", { by: "vertex",
      vertex: { kind: "vertex", x: 1, y: 2, z: 3 } }, point), {});
    assert.deepEqual(referenceEditValues("point", { by: "xyz", x: 1, y: 2,
      z: 3 }, point), { point: [1, 2, 3] });
    assert.deepEqual(referenceEditValues("cs", { by: "xyz", x: "4", y: 5,
      z: 6 }, { kind: "cs", point: [4, 5, 6] }), {});
    assert.deepEqual(referenceEditValues("point",
      { by: "center", edge: { edges: [9] } }, point), { edge: 9 });
  });
});
