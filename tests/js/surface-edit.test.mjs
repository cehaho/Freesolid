// Surface qu'on réédite : ce qu'elle prend revient dans sa zone (esquisse,
// surface, bord, arêtes) ; seul ce qui change part au moteur.

import { describe, it } from "node:test";
import assert from "node:assert/strict";

import {
  freeformEditValues, radiateBoundaryPick, radiateBoundaryValues, trimEditValues, trimKeepPick, cutOptionValues, intersectionEditValues, projectEditValues,
  projectTargetPick, extendPick, extendTargetValues, filletEdgesPick, filletEdgesValues,
  planarEditValues, ownSketchPick, signedEditValues, sourceEditValues,
  surfacePick,
} from "../../app/features.js";
import { surfaceEditor } from "../../app/editkind.js";
import { polesEditValues } from "../../app/poles.js";

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
    assert.deepEqual(ownSketchPick(surface),
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

describe("coupe par surface rééditée", () => {
  const side = { surface: "Surface", flip: false };
  const band = { surface: "Surface", flip: true, thickness: 3 };

  it("envoie sa surface outil sous la clé de la création", () => {
    assert.deepEqual(sourceEditValues({ name: "Surface001" }, "Surface",
                                      "surface"), { surface: "Surface001" });
  });

  it("n'envoie que le côté ou la bande qui changent", () => {
    assert.deepEqual(cutOptionValues({ flip: false, thick: false }, side), {});
    assert.deepEqual(cutOptionValues({ flip: true, thick: false }, side),
                     { flip: true });
    assert.deepEqual(cutOptionValues({ flip: true, thick: true,
                                       thickness: "3" }, band), {});
    assert.deepEqual(cutOptionValues({ flip: true, thick: true,
                                       thickness: "5" }, band),
                     { thickness: 5 });
  });

  it("passe d'un côté entier à une bande, et retour", () => {
    assert.deepEqual(cutOptionValues({ flip: false, thick: true,
                                       thickness: "2" }, side),
                     { thickness: 2 });
    assert.deepEqual(cutOptionValues({ flip: true, thick: false }, band),
                     { thickness: null });
    assert.equal(cutOptionValues({ flip: false, thick: true,
                                   thickness: "0" }, side), null);
  });
});

describe("courbe d'intersection rééditée", () => {
  const spec = { kind: "intersection", first: "Surface", second: "Surface001",
                 body: false };
  const pick = (name) => ({ kind: "surface", name });

  it("n'envoie que la surface ou le solide qui changent", () => {
    assert.deepEqual(intersectionEditValues(
      { first: pick("Surface"), second: pick("Surface001") }, spec), {});
    assert.deepEqual(intersectionEditValues(
      { first: pick("Surface"), second: pick("Surface002") }, spec),
    { second: "Surface002" });
    assert.deepEqual(intersectionEditValues(
      { first: pick("Surface002"), body: true }, spec),
    { first: "Surface002", body: true });
  });

  it("refuse une seule surface, ou deux fois la même", () => {
    assert.equal(intersectionEditValues({ first: pick("Surface") }, spec),
                 null);
    assert.equal(intersectionEditValues(
      { first: pick("Surface"), second: pick("Surface") }, spec), null);
  });

  it("se rouvre, comme la courbe projetée", () => {
    assert.equal(surfaceEditor({ surface: spec }), "intersection");
    assert.equal(surfaceEditor({ surface: { kind: "project" } }), "project");
  });
});

describe("courbe projetée rééditée", () => {
  const spec = { kind: "project", sketch: "Sketch", surface: "Surface",
                 face: 0 };
  const sketch = (name) => ({ kind: "sketch", name });
  const face = (name, n) => ({ kind: "surfface", name, face: n });

  it("revient sur sa face", () => {
    assert.deepEqual(projectTargetPick(tree, spec),
                     { kind: "surfface", name: "Surface", label: "Plane",
                       face: 0 });
  });

  it("n'envoie que l'esquisse, la surface ou la face qui changent", () => {
    assert.deepEqual(projectEditValues(
      { sketch: sketch("Sketch"), target: face("Surface", 0) }, spec), {});
    assert.deepEqual(projectEditValues(
      { sketch: sketch("Sketch001"), target: face("Surface", 2) }, spec),
    { sketch: "Sketch001", face: 2 });
    assert.deepEqual(projectEditValues(
      { sketch: sketch("Sketch"), target: pick("Surface001") }, spec),
    { surface: "Surface001", face: 0 });
    assert.equal(projectEditValues({ sketch: sketch("Sketch") }, spec), null);
  });

  function pick(name) {
    return { kind: "surface", name };
  }
});

describe("ajustement réédité", () => {
  const spec = { kind: "trim", source: "Surface", tool: "Surface001",
                 point: [5, 20, 0] };
  const keep = (name, x) => ({ kind: "surfpoint", name, x, y: 20, z: 0 });
  const tool = (name) => ({ kind: "surface", name });

  it("revient sur la partie gardée", () => {
    assert.deepEqual(trimKeepPick(tree, spec), {
      kind: "surfpoint", name: "Surface", label: "Plane", x: 5, y: 20, z: 0 });
  });

  it("n'envoie que l'outil, la surface ou le point qui changent", () => {
    assert.deepEqual(trimEditValues(
      { tool: tool("Surface001"), keep: keep("Surface", 5) }, spec), {});
    assert.deepEqual(trimEditValues(
      { tool: tool("Surface002"), keep: keep("Surface", 5) }, spec),
    { tool: "Surface002" });
    assert.deepEqual(trimEditValues(
      { tool: tool("Surface001"), keep: keep("Surface", 35) }, spec),
    { point: [35, 20, 0] });
    assert.deepEqual(trimEditValues(
      { tool: tool("Surface001"), keep: keep("Surface003", 5) }, spec),
    { source: "Surface003" });
  });

  it("refuse une partie gardée sur l'outil, ou sans outil", () => {
    assert.equal(trimEditValues(
      { tool: tool("Surface001"), keep: keep("Surface001", 5) }, spec), null);
    assert.equal(trimEditValues({ keep: keep("Surface", 5) }, spec), null);
  });
});

describe("surface radiée rééditée", () => {
  const spec = { kind: "radiate", distance: 5,
                 boundary: [{ body: true, edge: 3 }, { name: "Surface", edge: 1 }] };

  it("revient avec son contour, arête par arête", () => {
    const items = radiateBoundaryPick(tree, spec).items;
    assert.deepEqual(items.map((i) => [i.name, i.edge, !!i.body]),
                     [["body", 3, true], ["Surface", 1, false]]);
    assert.equal(items[1].label, "Plane");
  });

  it("n'envoie le contour que s'il change", () => {
    const zone = radiateBoundaryPick(tree, spec);
    assert.deepEqual(radiateBoundaryValues(zone, spec), {});
    assert.deepEqual(radiateBoundaryValues({ items: zone.items.slice(1) }, spec),
                     { boundary: [{ name: "Surface", edge: 1 }] });
    assert.deepEqual(radiateBoundaryValues(
      { items: [{ kind: "sketch", name: "Sketch" }] }, spec),
    { boundary: [{ name: "Sketch" }] });
    assert.equal(radiateBoundaryValues({ items: [] }, spec), null);
  });
});

describe("forme libre rééditée", () => {
  const spec = { kind: "freeform", source: "Surface", radius: 10,
                 keep_edges: false, pushes: [[20, 20, 0, 5]] };

  it("n'envoie que ce qui change", () => {
    const same = { radius: "10", pushes: [[20, 20, 0, 5]], keepEdges: false };
    assert.deepEqual(freeformEditValues(same, spec), {});
    assert.deepEqual(freeformEditValues({ ...same, radius: "6" }, spec),
                     { radius: 6 });
    assert.deepEqual(freeformEditValues(
      { ...same, pushes: [[10, 10, 0, -4]], keepEdges: true }, spec),
    { pushes: [[10, 10, 0, -4]], keep_edges: true });
  });

  it("refuse sans point ni rayon", () => {
    assert.equal(freeformEditValues({ radius: "10", pushes: [] }, spec), null);
    assert.equal(freeformEditValues(
      { radius: "0", pushes: [[20, 20, 0, 5]] }, spec), null);
  });

  it("pôles : la surface ne part que si elle change", () => {
    const params = { surface: "Surface", grid: 6, moves: [[0, 1, 1, 0, 0, 7]] };
    assert.deepEqual(polesEditValues(params, { source: "Surface" }),
                     { moves: params.moves, grid: 6 });
    assert.deepEqual(polesEditValues({ ...params, surface: "Surface001" },
                                     { source: "Surface" }),
                     { moves: params.moves, grid: 6, source: "Surface001" });
  });
});
