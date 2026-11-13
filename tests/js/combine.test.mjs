import { afterEach, describe, it } from "node:test";
import assert from "node:assert/strict";

import {
  addCombineTools,
  combineConfirm,
  combineFinished,
  combineToolOptions,
  resetCombineTools,
} from "../../app/combine.js";
import { combineEditOptions, combineEditValues } from "../../app/features.js";
import { featureEditor } from "../../app/editkind.js";

afterEach(() => {
  resetCombineTools();
});

const TREE = {
  bodies: [
    { name: "Body", label: "Pièce", active: true },
    { name: "Body001", label: "Outil", active: false },
  ],
  pieces: [{ name: "Piece", label: "Pièce rapportée" }],
};

describe("combineToolOptions", () => {
  it("sans plugin : les corps inactifs seulement", () => {
    assert.deepEqual(combineToolOptions(TREE), [["Body001", "Outil"]]);
    assert.deepEqual(combineToolOptions(null), []);
  });

  it("ajoute les outils des plugins, après les corps", () => {
    addCombineTools({
      options: (tree) => tree.pieces.map((p) => [p.name, p.label]),
    });
    assert.deepEqual(combineToolOptions(TREE), [
      ["Body001", "Outil"],
      ["Piece", "Pièce rapportée"],
    ]);
  });

  it("un plugin cassé ou une entrée mal formée n'empêche rien", () => {
    addCombineTools({ options: () => { throw new Error("boum"); } });
    addCombineTools({ options: () => [["", "vide"], "texte", ["Seul"]] });
    addCombineTools({});
    assert.deepEqual(combineToolOptions(TREE), [
      ["Body001", "Outil"],
      ["Seul", "Seul"],
    ]);
  });
});

describe("combineConfirm", () => {
  it("se tait sans plugin, rend la première question sinon", () => {
    assert.equal(combineConfirm(TREE, "Body001"), null);
    addCombineTools({ options: () => [], confirm: () => null });
    addCombineTools({ options: () => [], confirm: () => { throw new Error(); } });
    addCombineTools({
      options: () => [],
      confirm: (_tree, tool) => (tool === "Piece" ? "Long. Continuer ?" : null),
    });
    assert.equal(combineConfirm(TREE, "Body001"), null);
    assert.equal(combineConfirm(TREE, "Piece"), "Long. Continuer ?");
  });
});

describe("combineFinished", () => {
  it("prévient chaque plugin, avec l'arbre d'avant", () => {
    const seen = [];
    addCombineTools({
      options: () => [],
      finished: () => { throw new Error("boum"); },
    });
    addCombineTools({
      options: () => [],
      finished: (tree, tool, seconds) => seen.push([tree, tool, seconds]),
    });
    combineFinished(TREE, "Piece", 2.5);
    assert.deepEqual(seen, [[TREE, "Piece", 2.5]]);
  });
});

describe("Combiner réédité", () => {
  const spec = { type: "cut", tool: "Body002", tool_label: "Absorbé" };

  it("propose aussi le corps qu'il tient, absorbé", () => {
    assert.deepEqual(combineEditOptions(TREE, spec),
                     [["Body002", "Absorbé"], ["Body001", "Outil"]]);
    assert.deepEqual(combineEditOptions(TREE, { ...spec, tool: "Body001" }),
                     [["Body001", "Outil"]]);
  });

  it("n'envoie que l'opération ou le corps qui changent", () => {
    assert.deepEqual(combineEditValues({ type: "cut", tool: "Body002" }, spec),
                     {});
    assert.deepEqual(combineEditValues({ type: "fuse", tool: "Body001" }, spec),
                     { type: "fuse", tool: "Body001" });
    assert.equal(combineEditValues({ type: "cut", tool: "" }, spec), null);
    // Un corps outil venu d'un module : l'opération seule.
    assert.deepEqual(combineEditValues({ type: "common" },
                                       { type: "cut", tool: null }),
                     { type: "common" });
  });

  it("se rouvre au double-clic", () => {
    assert.equal(featureEditor({ type_key: "boolean", combine: spec }),
                 "combine");
  });
});
