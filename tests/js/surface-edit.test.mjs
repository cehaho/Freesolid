// Surface qu'on réédite : ce qu'elle prend revient dans sa zone (esquisse,
// surface, bord, arêtes) ; seul ce qui change part au moteur.

import { describe, it } from "node:test";
import assert from "node:assert/strict";

import {
  extendPick, extendTargetValues, filletEdgesPick, filletEdgesValues,
  planarEditValues, planarSketchPick, signedEditValues, sourceEditValues,
  surfacePick,
} from "../../app/features.js";
import { surfaceEditor } from "../../app/editkind.js";

const tree = { surfaces: [{ name: "Surface", label: "Plane" },
                          { name: "Surface001", label: "Petite" }] };

describe("surface source", () => {
  it("revient sous son nom de l'arbre", () => {
    assert.deepEqual(surfacePick(tree, "Surface001"),
                     { kind: "surface", name: "Surface001", label: "Petite" });
    assert.equal(surfacePick(tree, null), null);
  });

  it("n'est envoyée que si elle change", () => {
    assert.deepEqual(sourceEditValues({ name: "Surface" }, "Surface"), {});
    assert.deepEqual(sourceEditValues({ name: "Surface001" }, "Surface"),
                     { source: "Surface001" });
    assert.equal(sourceEditValues(null, "Surface"), null);
  });

  it("garde sa distance signée et son côté", () => {
    assert.deepEqual(signedEditValues({ distance: "10", flip: false }, 10), {});
    assert.deepEqual(signedEditValues({ distance: "10", flip: true }, 10),
                     { distance: -10 });
    // Distance 0 : une copie de la surface.
    assert.deepEqual(signedEditValues({ distance: "0" }, 10), { distance: 0 });
    assert.equal(signedEditValues({ distance: "" }, 10), null);
  });
});

describe("surface plane rééditée", () => {
  const surface = { surface: { kind: "planar", sketch: "Sketch" },
                    children: [{ name: "Sketch", label: "Contour" }] };

  it("revient avec son esquisse", () => {
    assert.deepEqual(planarSketchPick(surface),
                     { kind: "sketch", name: "Sketch", label: "Contour" });
  });

  it("n'envoie que l'esquisse changée", () => {
    assert.deepEqual(planarEditValues({ name: "Sketch" }, surface.surface), {});
    assert.deepEqual(planarEditValues({ name: "Sketch001" }, surface.surface),
                     { sketch: "Sketch001" });
    assert.equal(planarEditValues(null, surface.surface), null);
  });

  it("se rouvre, comme l'épaississement", () => {
    assert.equal(surfaceEditor(surface), "planar");
    assert.equal(surfaceEditor({ surface: { kind: "thicken" } }), "thicken");
  });
});

describe("prolongement réédité", () => {
  const spec = { kind: "extend", source: "Surface", distance: 10, edge: 2 };

  it("revient sur son bord, ou sur la surface entière", () => {
    assert.deepEqual(extendPick(tree, spec), {
      kind: "boundary", name: "Surface", label: "Plane", edge: 2 });
    assert.equal(extendPick(tree, { ...spec, edge: null }).kind, "surface");
  });

  it("envoie le bord, ou tous les bords, ou une autre surface", () => {
    const edge = (n) => ({ kind: "boundary", name: "Surface", edge: n });
    assert.deepEqual(extendTargetValues(edge(2), spec), {});
    assert.deepEqual(extendTargetValues(edge(3), spec), { edge: 3 });
    assert.deepEqual(extendTargetValues({ kind: "surface", name: "Surface" },
                                        spec), { edge: null });
    assert.deepEqual(extendTargetValues(
      { kind: "boundary", name: "Surface001", edge: 0 }, spec),
    { source: "Surface001", edge: 0 });
    // Un bord de courbe ne se prolonge pas.
    assert.equal(extendTargetValues({ ...edge(1), curve: true }, spec), null);
  });
});

describe("congé de surface réédité", () => {
  const spec = { kind: "fillet", source: "Surface", radius: 3, edges: [1, 4] };

  it("revient avec ses arêtes", () => {
    assert.deepEqual(filletEdgesPick(tree, spec).items.map((i) => i.edge),
                     [1, 4]);
  });

  it("n'envoie que les arêtes changées, d'une même surface", () => {
    const zone = (name, edges) => ({ items: edges.map((edge) => ({
      kind: "boundary", name, edge })) });
    assert.deepEqual(filletEdgesValues(zone("Surface", [4, 1]), spec), {});
    assert.deepEqual(filletEdgesValues(zone("Surface", [1]), spec),
                     { edges: [1] });
    assert.deepEqual(filletEdgesValues(zone("Surface001", [0]), spec),
                     { source: "Surface001", edges: [0] });
    assert.equal(filletEdgesValues({ items: [
      ...zone("Surface", [1]).items, ...zone("Surface001", [0]).items] },
    spec), null);
    assert.equal(filletEdgesValues(zone("Surface", []), spec), null);
  });
});
