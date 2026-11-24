import { describe, it } from "node:test";
import assert from "node:assert/strict";

import { installFeaturePanel } from "../../app/main/featurepanel.js";

describe("perçage : la face présélectionnée donne la première position", () => {
  it("avec la normale de la face (ses champs X / Y s'affichent)", () => {
    const app = {
      selectedEdges: new Set(),
      selectedFaceId: 4,
      lastFaceHit: { face: 4, pick: [-30, 2, -4], normal: [0, 0, -1] },
    };
    const { currentSelection } = installFeaturePanel(app);
    const sel = currentSelection(["point"]);
    assert.deepEqual(sel.items, [{ kind: "point", face: 4, x: -30, y: 2,
                                   z: -4, normal: [0, 0, -1] }]);
  });
});
