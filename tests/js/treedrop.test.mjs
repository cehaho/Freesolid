// Glisser une fonction dans l'arbre : la ligne survolée et la place.

import { describe, it } from "node:test";
import assert from "node:assert/strict";

import { featureDrop } from "../../app/treedrop.js";

// Quatre lignes de 20 px ; on glisse la deuxième (indice 1).
const TOPS = [0, 20, 40, 60];

describe("featureDrop", () => {
  it("se pose sous la ligne survolée", () => {
    assert.deepEqual(featureDrop(TOPS, 1, 45),
      { hover: 2, move: { index: 3, after: false } });
  });

  it("sous la dernière ligne : après elle", () => {
    assert.deepEqual(featureDrop(TOPS, 1, 70),
      { hover: 3, move: { index: 3, after: true } });
  });

  it("au-dessus de la première ligne : en tête", () => {
    assert.deepEqual(featureDrop(TOPS, 1, -5),
      { hover: -1, move: { index: 0, after: false } });
  });

  it("sur elle-même ou sous la ligne d'avant : ne bouge pas", () => {
    assert.deepEqual(featureDrop(TOPS, 1, 25), { hover: 1, move: null });
    assert.deepEqual(featureDrop(TOPS, 1, 5), { hover: 0, move: null });
  });

  it("une ligne dépliée sous une fonction compte pour elle", () => {
    // Le pointeur entre le haut de la ligne 2 et celui de la ligne 3 (une
    // esquisse dépliée, une ligne d'un autre corps) : sous la ligne 2.
    assert.deepEqual(featureDrop([0, 20, 40, 100], 0, 80),
      { hover: 2, move: { index: 3, after: false } });
  });

  it("sans ligne : rien", () => {
    assert.deepEqual(featureDrop([], 0, 10), { hover: -1, move: null });
  });
});
