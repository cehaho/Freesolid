import { describe, it } from "node:test";
import assert from "node:assert/strict";

import { eventToNdc, nearCursor, ndcToScreen, onLabel } from "../../app/screen.js";

const rect = { left: 10, top: 20, width: 200, height: 100 };

describe("projection écran", () => {
  it("le centre NDC tombe au centre du canevas", () => {
    assert.deepEqual(ndcToScreen(0, 0, rect), { x: 110, y: 70 });
  });

  it("le coin NDC haut-droit est le coin haut-droit du canevas", () => {
    assert.deepEqual(ndcToScreen(1, 1, rect), { x: 210, y: 20 });
    assert.deepEqual(ndcToScreen(-1, -1, rect), { x: 10, y: 120 });
  });

  it("un clic au centre du canevas est l'origine NDC", () => {
    assert.deepEqual(eventToNdc(110, 70, rect), { x: 0, y: 0 });
    assert.deepEqual(eventToNdc(10, 20, rect), { x: -1, y: 1 });
  });

  it("l'aller-retour pixel → NDC → pixel retrouve le point", () => {
    const ndc = eventToNdc(80, 90, rect);
    assert.deepEqual(ndcToScreen(ndc.x, ndc.y, rect), { x: 80, y: 90 });
  });
});

describe("barre près du curseur", () => {
  const host = { left: 100, top: 50, width: 400, height: 300 };
  const size = { width: 80, height: 30 };

  it("au-dessus à droite du curseur, en pixels du conteneur", () => {
    assert.deepEqual(nearCursor(300, 250, host, size), { left: 214, top: 156 });
  });

  it("à gauche du curseur au bord droit, dessous au bord du haut", () => {
    assert.deepEqual(nearCursor(480, 250, host, size), { left: 286, top: 156 });
    assert.deepEqual(nearCursor(300, 70, host, size), { left: 214, top: 34 });
  });

  it("jamais hors du conteneur, même plus grande que la place", () => {
    const wide = { width: 500, height: 30 };
    assert.deepEqual(nearCursor(110, 340, host, wide), { left: 4, top: 246 });
  });
});

describe("étiquette de cote cliquable", () => {
  // « Profondeur = 10.00 » : 16,8 px de haut, environ six fois plus large.
  const height = 16.8;
  const aspect = 6;

  it("tout le texte se clique, pas seulement le milieu", () => {
    assert.equal(onLabel(0, 0, aspect, height), true);
    assert.equal(onLabel(45, 0, aspect, height), true);   // sur « 10.00 »
    assert.equal(onLabel(-48, 5, aspect, height), true);
  });

  it("à côté du texte, la face derrière reste cliquable", () => {
    assert.equal(onLabel(60, 0, aspect, height), false);
    assert.equal(onLabel(0, 14, aspect, height), false);
  });
});
