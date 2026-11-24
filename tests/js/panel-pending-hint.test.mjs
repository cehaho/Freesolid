import { describe, it } from "node:test";
import assert from "node:assert/strict";

import { pendingHint } from "../../app/panel.js";

const groups = [
  { rows: [{ type: "selection", key: "profile" }] },
  { rows: [{ type: "selection", key: "spine" }] },
];
const sketch = (name) => ({ kind: "sketch", name });

describe("pendingHint : un panneau qui attend un clic guide", () => {
  it("à l'ouverture, zones vides : un guide, pas une erreur", () => {
    assert.deepEqual(pendingHint("Balayage : un profil puis une trajectoire",
      groups, {}),
    { text: "Balayage : un profil puis une trajectoire", tone: "guide" });
  });

  it("zones remplies mais saisie refusée : l'erreur reste", () => {
    assert.equal(pendingHint("même esquisse", groups,
      { profile: sketch("A"), spine: sketch("A") }), "même esquisse");
  });

  it("un message déjà typé ou vide passe tel quel", () => {
    const typed = { text: "Cliquez une face", tone: "guide" };
    assert.equal(pendingHint(typed, groups, {}), typed);
    assert.equal(pendingHint(null, groups, {}), null);
  });
});
