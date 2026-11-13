// Répétition de fonctions qu'on réédite : le panneau de la création,
// rempli de ce qu'elle est ; seul ce qui change part au moteur.

import { describe, it } from "node:test";
import assert from "node:assert/strict";

import {
  BODY_PATTERN_TYPES, patternEditGroups, patternEditValues,
  patternFeaturesPick, patternFeaturesValues, patternSourcesPick,
  patternSourcesValues,
} from "../../app/features.js";
import { featureEditor } from "../../app/editkind.js";

const tree = { features: [
  { name: "Pocket", label: "Enlèvement" },
  { name: "Pad001", label: "Extrusion", children: [
    { name: "Pocket001", label: "Enlèvement2" }] },
] };

/** Les valeurs initiales des rangées, comme le panneau les lit. */
function initial(groups) {
  return Object.fromEntries(groups.flatMap((g) => g.rows)
    .filter((row) => row.key).map((row) => [row.key, row.value]));
}

describe("fonctions répétées", () => {
  it("reviennent dans la zone, sous leur nom de l'arbre", () => {
    assert.deepEqual(patternFeaturesPick({ features: ["Pocket", "Pocket001"] },
                                         tree).items.map((i) => i.label),
                     ["Enlèvement", "Enlèvement2"]);
  });

  it("n'envoient que ce qui change, quel que soit l'ordre", () => {
    const pattern = { features: ["Pocket", "Pocket001"] };
    const zone = (names) => ({ items: names.map((name) => ({ name })) });
    assert.deepEqual(patternFeaturesValues(zone(["Pocket001", "Pocket"]),
                                           pattern), {});
    assert.deepEqual(patternFeaturesValues(zone(["Pocket"]), pattern),
                     { features: ["Pocket"] });
    assert.equal(patternFeaturesValues(zone([]), pattern), null);
  });

  it("une répétition se rouvre sur son panneau", () => {
    assert.equal(featureEditor({ type_key: "mirror", has_params: false,
                                 pattern: { features: ["Pocket"] } }),
                 "pattern");
  });
});

describe("direction d'une répétition rééditée", () => {
  const axis = { features: ["Pocket"], axis: "X", edge: null,
                 reversed: false, dir2: false };

  it("revient sur son axe, ou sur son arête", () => {
    const groups = patternEditGroups(axis, "linear_pattern");
    assert.equal(initial(groups).dirKind, "axis");
    assert.equal(initial(groups).axis, "X");
    const onEdge = patternEditGroups({ ...axis, axis: null, edge: 4 },
                                     "linear_pattern");
    assert.equal(initial(onEdge).dirKind, "edge");
    assert.deepEqual(initial(onEdge).edge, { kind: "edges", edges: [4] });
  });

  it("n'envoie que ce qui change", () => {
    const v = initial(patternEditGroups(axis, "linear_pattern"));
    assert.deepEqual(patternEditValues(v, axis, "linear_pattern"), {});
    assert.deepEqual(patternEditValues({ ...v, axis: "Y", reversed: true },
                                       axis, "linear_pattern"),
                     { axis: "Y", reversed: true });
    assert.deepEqual(patternEditValues(
      { ...v, dirKind: "edge", edge: { kind: "edges", edges: [2] } },
      axis, "linear_pattern"), { edge: 2 });
    // « Arête » sans arête : rien à appliquer.
    assert.equal(patternEditValues({ ...v, dirKind: "edge", edge: null },
                                   axis, "linear_pattern"), null);
  });

  it("une arête perdue reste telle quelle tant qu'on n'en clique pas", () => {
    const lost = { ...axis, axis: null, edge: null };
    const v = initial(patternEditGroups(lost, "polar_pattern"));
    assert.equal(v.dirKind, "edge");
    assert.deepEqual(patternEditValues(v, lost, "polar_pattern"), {});
  });
});

describe("pas ou longueur totale d'un réseau linéaire", () => {
  const pattern = { features: ["Pocket"], axis: "X", edge: null,
                    reversed: false, mode: "spacing", dir2: false };
  const dims = [{ type: "text", key: "length", label: "Distance",
                  value: "20" },
                { type: "text", key: "count", label: "Nombre", value: "3" }];

  it("revient sur son mode, juste avant la distance", () => {
    const [first] = patternEditGroups(pattern, "linear_pattern", dims);
    const keys = first.rows.map((row) => row.key);
    assert.equal(initial([first]).mode, "spacing");
    assert.equal(keys.indexOf("mode") + 1, keys.indexOf("length"));
    // Une répétition circulaire n'a pas de mode.
    assert.ok(!patternEditGroups(pattern, "polar_pattern", dims)
      .flatMap((g) => g.rows).some((row) => row.key === "mode"));
  });

  it("un mode changé emporte la distance telle qu'elle est écrite", () => {
    const v = initial(patternEditGroups(pattern, "linear_pattern", dims));
    assert.deepEqual(patternEditValues(v, pattern, "linear_pattern"), {});
    assert.deepEqual(patternEditValues({ ...v, mode: "extent" }, pattern,
                                       "linear_pattern"),
                     { mode: "extent", length: "20" });
  });
});

describe("deuxième direction d'un réseau linéaire", () => {
  const one = { features: ["Pocket"], axis: "X", edge: null,
                reversed: false, dir2: false };
  const two = { ...one, dir2: true, axis2: "Y", edge2: null,
                reversed2: false, count2: 3, length2: 10 };

  it("s'active, complète", () => {
    const v = initial(patternEditGroups(one, "linear_pattern"));
    assert.deepEqual(patternEditValues(
      { ...v, dir2: true, length2: "12", count2: "2" }, one, "linear_pattern"),
    { dir2: true, axis2: "Y", reversed2: false, length2: 12, count2: 2 });
    assert.equal(patternEditValues({ ...v, dir2: true, length2: "0" }, one,
                                   "linear_pattern"), null);
  });

  it("se règle, puis se retire", () => {
    const v = initial(patternEditGroups(two, "linear_pattern"));
    assert.deepEqual(patternEditValues(v, two, "linear_pattern"), {});
    assert.deepEqual(patternEditValues({ ...v, count2: "4", axis2: "Z" }, two,
                                       "linear_pattern"),
                     { axis2: "Z", count2: 4 });
    assert.deepEqual(patternEditValues({ ...v, dir2: false }, two,
                                       "linear_pattern"), { dir2: false });
  });
});

describe("symétrie rééditée", () => {
  it("revient sur son plan, n'envoie que le plan changé", () => {
    const pattern = { features: ["Pocket"], plane: "XZ" };
    const v = initial(patternEditGroups(pattern, "mirror"));
    assert.equal(v.plane, "XZ");
    assert.deepEqual(patternEditValues(v, pattern, "mirror"), {});
    assert.deepEqual(patternEditValues({ plane: "XY" }, pattern, "mirror"),
                     { plane: "XY" });
  });
});

describe("répétition de corps rééditée", () => {
  const tree = { bodies: [{ name: "Body", label: "Plaque" },
                          { name: "Body001", label: "Tige" }] };
  const pattern = { sources: ["Body"], axis: "X", edge: null,
                    reversed: false, mode: "spacing", dir2: false };

  it("revient avec ses corps, sous leur nom du dossier", () => {
    const zone = patternSourcesPick(pattern, tree);
    assert.equal(zone.kind, "body");
    assert.deepEqual(zone.items.map((i) => [i.name, i.label]),
                     [["Body", "Plaque"]]);
  });

  it("n'envoie que les corps changés", () => {
    const zone = (names) => ({ items: names.map((name) => ({ name })) });
    assert.deepEqual(patternSourcesValues(zone(["Body"]), pattern), {});
    assert.deepEqual(patternSourcesValues(zone(["Body001", "Body"]),
                                          pattern),
                     { sources: ["Body001", "Body"] });
    assert.equal(patternSourcesValues(zone([]), pattern), null);
  });

  it("rouvre le panneau de son genre", () => {
    assert.equal(BODY_PATTERN_TYPES.polar, "polar_pattern");
    assert.equal(featureEditor({ type_key: "body_pattern",
                                 body_pattern: "mirror", has_params: false,
                                 pattern: { sources: ["Body"] } }),
                 "pattern");
    // Une ligne qui renvoie à une symétrie, sans cote : elle se rouvre
    // pour ce que la symétrie re-choisit.
    assert.equal(featureEditor({ type_key: "pocket", edits: "Mirrored",
                                 edits_has_params: false,
                                 edits_pattern: { features: ["Pocket"] } }),
                 "edits");
    assert.equal(featureEditor({ type_key: "pocket", edits: "Mirrored",
                                 edits_has_params: false }), null);
  });
});
