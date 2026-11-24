import { describe, it } from "node:test";
import assert from "node:assert/strict";

import { findFeatureInTree, sketchesPickable } from "../../app/picking.js";

describe("findFeatureInTree", () => {
  const tree = {
    features: [
      { name: "Pad", children: [{ name: "Sketch" }] },
    ],
    surfaces: [{ name: "Surface" }],
  };

  it("trouve une fonction, son enfant, ou une surface", () => {
    assert.equal(findFeatureInTree(tree, "Pad").name, "Pad");
    assert.equal(findFeatureInTree(tree, "Sketch").name, "Sketch");
    assert.equal(findFeatureInTree(tree, "Surface").name, "Surface");
  });

  it("rend null sans nom, sans arbre, ou si rien ne correspond", () => {
    assert.equal(findFeatureInTree(tree, ""), null);
    assert.equal(findFeatureInTree(null, "Pad"), null);
    assert.equal(findFeatureInTree(tree, "Absent"), null);
    assert.equal(findFeatureInTree({}, "Pad"), null);
  });
});

describe("sketchesPickable", () => {
  const panel = (applicable, takes) => ({ applicable,
    accepts: (kind) => takes.includes(kind) });

  it("sans commande ouverte, les esquisses se visent", () => {
    assert.equal(sketchesPickable(null), true);
    assert.equal(sketchesPickable(panel(false, [])), true);
  });

  it("une commande qui ne prend pas d'esquisse les traverse", () => {
    assert.equal(sketchesPickable(panel(true, ["point", "face"])), false);
  });

  it("une commande qui prend une esquisse les vise", () => {
    assert.equal(sketchesPickable(panel(true, ["sketch"])), true);
  });

  it("le filtre de sélection les écarte toujours", () => {
    assert.equal(sketchesPickable(null, { sketches: false }), false);
  });
});
