import { describe, it } from "node:test";
import assert from "node:assert/strict";

import {
  loftOptionRows, loftOptionValues, loftProfilesPick, loftProfilesValues,
  sweepEditValues, sweptPick,
} from "../../app/features.js";

const sketch = (name) => ({ kind: "sketch", name, label: name });

describe("lissage réédité", () => {
  const swept = { kind: "loft", ruled: false, closed: true,
                  profiles: [{ name: "A", label: "Bas" },
                             { name: "B", label: "Milieu" },
                             { name: "C", label: "Haut" }] };

  it("ses profils reviennent dans l'ordre : rien à envoyer", () => {
    const zone = loftProfilesPick(swept);
    assert.deepEqual(zone.items.map((i) => [i.name, i.label]),
                     [["A", "Bas"], ["B", "Milieu"], ["C", "Haut"]]);
    assert.deepEqual(loftProfilesValues(zone, swept), {});
  });

  it("un profil retiré, ajouté ou déplacé : la liste dans l'ordre", () => {
    const zone = (...names) => ({ kind: "sketch", items: names.map(sketch) });
    assert.deepEqual(loftProfilesValues(zone("A", "C"), swept),
                     { profiles: ["A", "C"] });
    assert.deepEqual(loftProfilesValues(zone("C", "B", "A"), swept),
                     { profiles: ["C", "B", "A"] });
    assert.deepEqual(loftProfilesValues(zone("A", "B", "C", "D"), swept),
                     { profiles: ["A", "B", "C", "D"] });
    // Moins de deux profils : rien ne part.
    assert.equal(loftProfilesValues(zone("A"), swept), null);
    assert.equal(loftProfilesValues(null, swept), null);
  });

  it("lissage droit et boucle fermée : ceux de la fonction", () => {
    const rows = loftOptionRows(swept);
    assert.deepEqual(rows.map((r) => [r.key, r.value]),
                     [["ruled", false], ["closed", true]]);
    assert.deepEqual(loftOptionRows().map((r) => r.value), [false, false]);
    assert.deepEqual(loftOptionValues({ ruled: false, closed: true }, swept),
                     {});
    assert.deepEqual(loftOptionValues({ ruled: true, closed: false }, swept),
                     { ruled: true, closed: false });
  });
});

describe("balayage réédité", () => {
  const swept = { kind: "sweep", profile: { name: "P", label: "Cercle" },
                  spine: { name: "Surface", label: "Spline 3D",
                           curve: true } };

  it("profil et trajectoire reviennent, une courbe 3D comme surface", () => {
    assert.deepEqual(sweptPick(swept.profile),
                     { kind: "sketch", name: "P", label: "Cercle" });
    assert.deepEqual(sweptPick(swept.spine),
                     { kind: "surface", name: "Surface", label: "Spline 3D" });
    assert.equal(sweptPick(null), null);
  });

  it("seulement ce qui change ; il en faut deux, différents", () => {
    const v = { profile: sweptPick(swept.profile),
                spine: sweptPick(swept.spine) };
    assert.deepEqual(sweepEditValues(v, swept), {});
    assert.deepEqual(sweepEditValues({ ...v, spine: sketch("T") }, swept),
                     { spine: "T" });
    assert.deepEqual(sweepEditValues({ ...v, profile: sketch("Q") }, swept),
                     { profile: "Q" });
    assert.equal(sweepEditValues({ ...v, spine: null }, swept), null);
    assert.equal(sweepEditValues({ ...v, spine: sketch("P") }, swept), null);
  });
});
