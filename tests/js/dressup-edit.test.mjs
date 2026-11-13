// Congé et chanfrein qu'on réédite : la zone revient remplie de ce qu'ils
// arrondissent, et seul ce qui a changé part au moteur.

import { describe, it } from "node:test";
import assert from "node:assert/strict";

import {
  dressupPick, dressupPickValues, filletEditRows, filletEditValues,
} from "../../app/features.js";

describe("zone d'un habillage réédité", () => {
  it("se remplit de ses arêtes, ou de sa face", () => {
    assert.deepEqual(dressupPick({ edges: [0, 2] }),
      { kind: "edges", edges: [0, 2] });
    assert.deepEqual(dressupPick({ face: 5 }), { kind: "face", face: 5 });
    assert.equal(dressupPick(undefined), null);
    assert.equal(dressupPick({ edges: [] }), null);
  });

  it("n'envoie rien si elle est inchangée, quel que soit l'ordre", () => {
    const dressup = { edges: [0, 2] };
    assert.deepEqual(
      dressupPickValues({ kind: "edges", edges: [2, 0] }, dressup), {});
    assert.deepEqual(
      dressupPickValues({ kind: "face", face: 5 }, { face: 5 }), {});
  });

  it("envoie les arêtes re-choisies, ou la face", () => {
    const dressup = { edges: [0, 2] };
    assert.deepEqual(
      dressupPickValues({ kind: "edges", edges: [0, 2, 4, 4] }, dressup),
      { edges: [0, 2, 4] });
    assert.deepEqual(
      dressupPickValues({ kind: "face", face: 3 }, dressup), { face: 3 });
    assert.deepEqual(
      dressupPickValues({ kind: "edges", edges: [1] }, { face: 3 }),
      { edges: [1] });
  });

  it("vide : rien à appliquer", () => {
    assert.equal(dressupPickValues({ kind: "edges", edges: [] },
                                   { edges: [0] }), null);
    assert.equal(dressupPickValues(null, { edges: [0] }), null);
  });
});

describe("rayon d'un congé réédité", () => {
  const feature = { params: [{ key: "radius", value: 2 }] };

  it("reprend le rayon de la fonction", () => {
    assert.equal(filletEditRows(feature)[0].value, 2);
  });

  it("n'envoie que ce qui change", () => {
    assert.deepEqual(filletEditValues({ radius: "2" }, feature), {});
    assert.deepEqual(filletEditValues({ radius: "3,5" }, feature),
      { radius: 3.5 });
    assert.equal(filletEditValues({ radius: "0" }, feature), null);
  });

  it("garde une expression", () => {
    const driven = { params: [{ key: "radius", value: 2, expr: "Rayon" }] };
    assert.deepEqual(filletEditValues({ radius: "Rayon" }, driven), {});
    assert.deepEqual(filletEditValues({ radius: "2*Rayon" }, driven),
      { radius: "2*Rayon" });
  });
});
