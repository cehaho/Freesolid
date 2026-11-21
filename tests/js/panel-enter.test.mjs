import { describe, it } from "node:test";
import assert from "node:assert/strict";

import { enterAction } from "../../app/panel.js";

describe("Entrée dans le panneau", () => {
  it("une valeur tapée est d'abord appliquée, sans fermer", () => {
    assert.equal(enterAction({ tag: "INPUT", edited: true }), "commit");
  });

  it("un second appui valide la fonction", () => {
    assert.equal(enterAction({ tag: "INPUT", edited: false }), "apply");
    assert.equal(enterAction({ tag: "BUTTON", edited: false }), "apply");
  });

  it("boîte de cote : Entrée applique et ferme d'un coup", () => {
    assert.equal(enterAction({ tag: "INPUT", edited: true,
      enterApplies: true }), "apply");
    assert.equal(enterAction({ tag: "INPUT", edited: true,
      enterApplies: true, noApply: true }), "commit");
  });

  it("liste déroulante et panneau sans validation : rien", () => {
    assert.equal(enterAction({ tag: "SELECT", edited: true }), "none");
    assert.equal(enterAction({ tag: "INPUT", edited: false, noApply: true }),
      "none");
    assert.equal(enterAction({ tag: "INPUT", edited: true, noApply: true }),
      "commit");
  });
});
