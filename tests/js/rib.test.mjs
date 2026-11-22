import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { FEATURES, ribBuild, ribEditValues, ribGroups } from "../../app/features.js";

describe("nervure", () => {
  it("a son bouton, à profil d'esquisse", () => {
    const rib = FEATURES.find((entry) => entry.button === "btn-rib");
    assert.equal(rib?.op, "add_rib");
    assert.equal(rib?.sketchProfile, true);
  });

  it("part de 3 mm, parallèle à l'esquisse", () => {
    const [group] = ribGroups();
    const [thickness, direction, flip] = group.rows;
    assert.equal(thickness.value, 3);
    assert.equal(direction.value, "parallel");
    assert.equal(flip.value, false);
  });

  it("envoie épaisseur, direction et côté", () => {
    assert.deepEqual(ribBuild({ thickness: 4, direction: "normal", flip: true }),
      { op: "add_rib",
        params: { thickness: 4, direction: "normal", flip: true } });
    assert.deepEqual(ribBuild({ thickness: "2.5", direction: "parallel" }),
      { op: "add_rib", params: { thickness: 2.5, direction: "parallel" } });
    assert.equal(ribBuild({ thickness: 0 }), null);
  });

  it("rééditée : n'envoie que ce qui change", () => {
    const rib = { sketch: "Sketch001", thickness: 3, direction: "parallel",
                  flip: false };
    assert.deepEqual(ribGroups(rib)[0].rows[0].value, 3);
    assert.deepEqual(ribEditValues({ thickness: 3, direction: "parallel",
                                     flip: false }, rib), {});
    assert.deepEqual(ribEditValues({ thickness: 5, direction: "normal",
                                     flip: true }, rib),
      { thickness: 5, direction: "normal", flip: true });
    assert.equal(ribEditValues({ thickness: -1 }, rib), null);
  });
});
