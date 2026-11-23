import { describe, it } from "node:test";
import assert from "node:assert/strict";

import { luminance, parseColor, readScene, sceneColor, sketchNeedsHalo }
  from "../../app/theme.js";

describe("thème de la scène", () => {
  it("rend la couleur de repli sans DOM", () => {
    assert.equal(sceneColor("selection", null), 0xd9924a);
    assert.equal(sceneColor("bg"), 0x17191c);
    assert.equal(readScene(null).accent, 0x4f8fdb);
  });

  it("lit une variable CSS en hex ou en rgb", () => {
    const style = {
      getPropertyValue(name) {
        if (name === "--selection") return " #ff8800 ";
        if (name === "--bg") return "rgb(10, 20, 30)";
        return "";
      },
    };
    assert.equal(sceneColor("selection", style), 0xff8800);
    assert.equal(sceneColor("bg", style), 0x0a141e);
    assert.equal(sceneColor("accent", style), 0x4f8fdb);
  });

  it("accepte un hex court", () => {
    assert.equal(parseColor("#abc"), 0xaabbcc);
    assert.equal(parseColor("pas une couleur"), null);
  });

  it("liseré des traits d'esquisse en thème sombre seulement", () => {
    assert.equal(luminance(0x000000), 0);
    assert.equal(luminance(0xffffff), 1);
    // Sombre : traits #e8edf2 plus clairs que la pièce #aebccb.
    assert.equal(sketchNeedsHalo(readScene(null)), true);
    // Clair : traits #1d2733 sur une pièce #a9bbcd.
    assert.equal(sketchNeedsHalo({ defined: 0x1d2733, part: 0xa9bbcd }),
                 false);
  });
});
