// Révolution : l'axe choisi part avec la fonction et se réédite.

import { describe, it } from "node:test";
import assert from "node:assert/strict";

import {
  revolutionAxisOptions, revolutionCreationParams, revolutionEditValues,
  revolutionGroups, revolutionProblem,
  defaultRevolutionAxis, FEATURES,
} from "../../app/features.js";

const sketch = {
  lines: [
    { id: 0, construction: false, x1: 0, y1: 0, x2: 10, y2: 0 },
    { id: 3, construction: true, x1: 5, y1: 0, x2: 5, y2: 10 },
  ],
};

describe("création de la révolution", () => {
  it("prend d'office l'unique ligne de construction comme axe", () => {
    assert.equal(defaultRevolutionAxis(sketch), "line:3");
    assert.equal(defaultRevolutionAxis({ lines: [sketch.lines[0]] }),
      "vertical");
    const two = { lines: [...sketch.lines,
      { id: 4, construction: true, x1: 0, y1: 5, x2: 10, y2: 5 }] };
    assert.equal(defaultRevolutionAxis(two), "vertical");
    assert.equal(defaultRevolutionAxis(null), "vertical");
  });

  it("le panneau part sur cet axe, même si l'esquisse est cliquée dans l'arbre", () => {
    const lastTree = { features: [
      { name: "Sketch", label: "Esquisse1", type_key: "sketch", ...sketch }] };
    for (const button of ["btn-revolution", "btn-groove"]) {
      const spec = FEATURES.find((f) => f.button === button);
      const groups = spec.groups({ lastTree, selection: () => null,
        selectedSketch: { name: "Sketch", label: "Esquisse1" } });
      const row = groups.flatMap((g) => g.rows ?? [])
        .find((r) => r.key === "axis");
      assert.equal(row.value, "line:3", button);
    }
  });

  it("place les lignes de construction avant les lignes réelles", () => {
    const values = revolutionAxisOptions(sketch).map(([value]) => value);
    assert.deepEqual(values.slice(0, 4),
      ["vertical", "horizontal", "line:3", "line:0"]);
    assert.deepEqual(values.slice(-4), ["X", "Y", "Z", "edge"]);
  });

  it("omet l'axe vertical et n'envoie le plan milieu qu'à la place de l'inversion", () => {
    assert.deepEqual(
      revolutionCreationParams({ angle: 360, axis: "vertical", cond: "one" },
        "add_revolution"),
      { op: "add_revolution", params: { angle: 360 } });
    assert.deepEqual(
      revolutionCreationParams({
        angle: 180, axis: "line:3", cond: "milieu", reversed: true,
      }, "add_groove"),
      { op: "add_groove", params: { angle: 180, axis: "line:3", midplane: true } });
  });

  it("refuse un angle nul ou au-delà de 360", () => {
    assert.equal(revolutionCreationParams(
      { angle: 0, axis: "vertical", cond: "one" }, "add_revolution"), null);
    assert.equal(revolutionCreationParams(
      { angle: 361, axis: "X", cond: "one" }, "add_revolution"), null);
    assert.deepEqual(
      revolutionCreationParams(
        { angle: 90, axis: "X", cond: "one", reversed: true }, "add_revolution"),
      { op: "add_revolution", params: { angle: 90, axis: "X", reversed: true } });
  });
});

describe("réédition de la révolution", () => {
  const revolution = {
    axis: "line:3", angle: 360, reversed: false, midplane: false,
  };
  const params = [{ key: "angle", value: 360 }];

  it("ne renvoie rien si les champs n'ont pas changé", () => {
    assert.deepEqual(revolutionEditValues({
      angle: 360, axis: "line:3", cond: "one", reversed: false,
    }, revolution, params), {});
  });

  it("envoie l'axe, l'angle et le plan milieu quand ils changent", () => {
    assert.deepEqual(revolutionEditValues({
      angle: "180", axis: "vertical", cond: "milieu", reversed: true,
    }, revolution, params), {
      angle: 180, axis: "vertical", reversed: false, midplane: true,
    });
  });

  it("conserve une expression d'angle", () => {
    const expressed = [{ key: "angle", value: 360, expr: "2*Tours" }];
    assert.deepEqual(revolutionEditValues({
      angle: "2*Tours", axis: "line:3", cond: "one", reversed: false,
    }, revolution, expressed), {});
    assert.deepEqual(revolutionEditValues({
      angle: "3*Tours", axis: "line:3", cond: "one", reversed: false,
    }, revolution, expressed), { angle: "3*Tours" });
  });
});

describe("révolution : deux directions et arête pour axe", () => {
  it("envoie l'angle de la seconde direction, dans un tour", () => {
    assert.deepEqual(revolutionCreationParams(
      { angle: 30, angle2: 60, cond: "deux", axis: "vertical" },
      "add_groove"),
    { op: "add_groove", params: { angle: 30, angle2: 60 } });
    const over = { angle: 200, angle2: 200, cond: "deux", axis: "vertical" };
    assert.equal(revolutionCreationParams(over, "add_revolution"), null);
    assert.equal(revolutionProblem(over), "Les deux angles dépassent un tour");
  });

  it("prend l'arête cliquée pour axe, et la réclame sinon", () => {
    const clicked = { angle: 90, cond: "one", axis: "edge",
                      axisEdge: { kind: "edges", edges: [7] } };
    assert.deepEqual(revolutionCreationParams(clicked, "add_revolution"),
      { op: "add_revolution", params: { angle: 90, axis: "edge:7" } });
    const missing = { angle: 90, cond: "one", axis: "edge" };
    assert.equal(revolutionCreationParams(missing, "add_revolution"), null);
    assert.equal(revolutionProblem(missing),
      "Cliquez une arête droite pour l'axe");
  });

  it("la zone d'arête se montre d'un clic, sans en garder deux", () => {
    const rows = revolutionGroups(sketch).flatMap((g) => g.rows);
    const zone = rows.find((r) => r.key === "axisEdge");
    assert.deepEqual(zone.reveal, { key: "axis", value: "edge" });
    assert.ok(!zone.edgeSet);
  });

  it("la réédition rouvre sur l'arête et les deux directions", () => {
    const rows = revolutionGroups(sketch,
      { axis: "edge:4", angle: 30, angle2: 60 }).flatMap((g) => g.rows);
    const value = (key) => rows.find((r) => r.key === key).value;
    assert.equal(value("cond"), "deux");
    assert.equal(value("angle2"), 60);
    assert.equal(value("axis"), "edge");
    assert.deepEqual(value("axisEdge"), { kind: "edges", edges: [4] });
  });

  it("la réédition change ou ferme la seconde direction", () => {
    const spec = { axis: "edge:4", angle: 30, angle2: 60 };
    const params = [{ key: "angle", value: 30 }];
    const base = { angle: 30, cond: "deux", axis: "edge",
                   axisEdge: { kind: "edges", edges: [4] } };
    assert.deepEqual(revolutionEditValues({ ...base, angle2: 60 }, spec,
      params), {});
    assert.deepEqual(revolutionEditValues({ ...base, angle2: 90 }, spec,
      params), { angle2: 90 });
    assert.deepEqual(revolutionEditValues({ ...base, cond: "one" }, spec,
      params), { angle2: 0 });
    assert.deepEqual(revolutionEditValues({ ...base, angle2: 60,
      axisEdge: { kind: "edges", edges: [9] } }, spec, params),
    { axis: "edge:9" });
  });
});
