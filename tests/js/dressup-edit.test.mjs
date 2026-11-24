// Habillages qu'on réédite (congé, chanfrein, coque, dépouille) : la zone
// revient remplie de ce qu'ils visent, et seul ce qui a changé part au
// moteur.

import { describe, it } from "node:test";
import assert from "node:assert/strict";

import {
  draftBuild, draftEditGroups, draftEditValues, draftGroups, dressupPick, dressupPickValues,
  filletEditRows, filletEditValues, shellFacesPick, shellFacesValues,
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

  it("arêtes et faces mélangées, comme dans les modeleurs courants", () => {
    assert.deepEqual(dressupPick({ edges: [1], faces: [4, 6] }),
      { kind: "edges", edges: [1], faces: [4, 6] });
    const dressup = { edges: [1], faces: [4] };
    assert.deepEqual(dressupPickValues(
      { kind: "edges", edges: [1], faces: [4] }, dressup), {});
    assert.deepEqual(dressupPickValues(
      { kind: "edges", edges: [1], faces: [4, 6] }, dressup),
    { edges: [1], faces: [4, 6] });
    assert.deepEqual(dressupPickValues(
      { kind: "edges", edges: [], faces: [4] }, dressup), { face: 4 });
    assert.deepEqual(dressupPickValues(
      { kind: "edges", edges: [1], faces: [] }, dressup), { edges: [1] });
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

describe("faces ouvertes d'une coque rééditée", () => {
  it("reviennent dans la zone, une par ligne", () => {
    assert.deepEqual(shellFacesPick([5, 1]), { kind: "face", items: [
      { kind: "face", face: 5 }, { kind: "face", face: 1 }] });
  });

  it("n'envoient que ce qui change", () => {
    const zone = (faces) => shellFacesPick(faces);
    assert.deepEqual(shellFacesValues(zone([1, 5]), [5, 1]), {});
    assert.deepEqual(shellFacesValues(zone([5, 1, 3]), [5, 1]),
      { faces: [5, 1, 3] });
    assert.equal(shellFacesValues(zone([]), [5]), null);
  });
});

describe("dépouille rééditée", () => {
  const feature = { params: [{ key: "angle", value: 5 }],
                    draft: { face: 1, neutral: "XZ" } };

  it("reprend son angle et son plan neutre", () => {
    const [plane, sizes] = draftEditGroups(feature);
    assert.equal(plane.rows[0].value, "XZ");
    assert.equal(sizes.rows[0].value, 5);
    assert.equal(sizes.rows[1].value, false);
  });

  it("n'envoie que ce qui change", () => {
    assert.deepEqual(draftEditValues({ angle: "5", neutral: "XZ" }, feature),
      {});
    assert.deepEqual(draftEditValues({ angle: "4", neutral: "XY" }, feature),
      { angle: 4, neutral: "XY" });
    assert.equal(draftEditValues({ angle: "95", neutral: "XZ" }, feature),
      null);
  });

  it("garde sa face neutre, la change, inverse le sens", () => {
    const own = { params: [{ key: "angle", value: 5 }],
                  draft: { faces: [0, 1], neutral: "XY", neutral_face: 4,
                           reversed: false } };
    const [plane] = draftEditGroups(own);
    assert.equal(plane.rows[0].value, "face");
    assert.deepEqual(plane.rows[1].value, { kind: "face", face: 4 });
    assert.deepEqual(draftEditValues({ angle: "5", neutral: "face" }, own),
      {});
    assert.deepEqual(draftEditValues({ angle: "5", neutral: "face",
                                       nface: { kind: "face", face: 5 },
                                       reversed: true }, own),
      { neutral_face: 5, reversed: true });
    assert.deepEqual(draftEditValues({ angle: "5", neutral: "XZ" }, own),
      { neutral: "XZ" });
    assert.equal(draftEditValues({ angle: "5", neutral: "face",
                                   nface: null }, own), null);
  });
});

describe("dépouille créée", () => {
  it("part de la face cliquée, plan neutre sur une face", () => {
    const groups = draftGroups(null, { first: { kind: "face", face: 2 } });
    assert.deepEqual(groups[0].rows[0].value.items, [{ kind: "face", face: 2 }]);
    assert.equal(groups[1].rows[0].value, "face");
    assert.equal(groups[1].rows[1].showIf({ neutral: "face" }), true);
    assert.equal(groups[1].rows[1].showIf({ neutral: "XY" }), false);
  });

  it("plusieurs faces et une face neutre", () => {
    const faces = { items: [{ face: 0 }, { face: 1 }, { face: 1 }] };
    assert.deepEqual(draftBuild({ faces, angle: 5, neutral: "face",
                                  nface: { face: 4 }, reversed: true }),
      { op: "add_draft",
        params: { angle: 5, faces: [0, 1], neutral_face: 4,
                  reversed: true } });
    assert.deepEqual(draftBuild({ faces: { items: [{ face: 3 }] }, angle: 3,
                                  neutral: "XZ" }),
      { op: "add_draft", params: { angle: 3, face: 3, neutral: "XZ" } });
    assert.equal(draftBuild({ faces, angle: 5, neutral: "face" }), null);
    assert.equal(draftBuild({ faces: { items: [] }, angle: 5,
                              neutral: "XY" }), null);
  });

  it("sa face se compare comme celle d'un congé", () => {
    assert.deepEqual(dressupPickValues({ kind: "face", face: 1 }, { face: 1 }),
      {});
    assert.deepEqual(dressupPickValues({ kind: "face", face: 2 }, { face: 1 }),
      { face: 2 });
  });
});
