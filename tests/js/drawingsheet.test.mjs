import { describe, it } from "node:test";
import assert from "node:assert/strict";

import { dimText, sheetEntities, sheetSvg } from "../../app/drawingsheet.js";

const DATA = {
  sheet: { width: 297, height: 210, margin: 10 },
  title_block: { width: 120, height: 36 },
  scale: 2, scale_label: "2:1", part: "Bloc <A>", material: null,
  views: [
    { name: "front", label: "Face", width: 40, height: 10, center: [118, 34],
      visible: [[[-20, -5], [20, -5], [20, 5], [-20, 5], [-20, -5]]],
      hidden: [[[-5, 5], [-5, 1]]] },
    { name: "top", label: "Dessus", width: 40, height: 20, center: [118, 78],
      visible: [[[-20, -10], [20, -10]]], hidden: [] },
  ],
  dims: [
    { view: "front", axis: "x", value: 40 },
    { view: "front", axis: "y", value: 10 },
    { view: "top", axis: "y", value: 20.5 },
  ],
};

describe("feuille de mise en plan", () => {
  it("une cote sans zéros inutiles, séparateur régional", () => {
    assert.equal(dimText(40, 2, "fr-FR"), "40");
    assert.equal(dimText(12.5, 2, "fr-FR"), "12,5");
    assert.equal(dimText(12.25, 2, "en-US"), "12.25");
  });

  it("dessine le cadre, les vues à l'échelle, les cotes et le cartouche", () => {
    const svg = sheetSvg(DATA, { locale: "fr-FR", date: "19/11/2026" });
    assert.match(svg, /viewBox="0 0 297 210"/);
    // Échelle 2 : le coin (-20, -5) de la face tombe en (78, 44), y vers le bas.
    assert.match(svg, /points="78\.000,44\.000 158\.000,44\.000/);
    assert.equal((svg.match(/class="cache"/g) || []).length, 1);
    assert.equal((svg.match(/stroke-dasharray/g) || []).length, 1);
    assert.match(svg, />20,5</);
    assert.match(svg, />2:1</);
    // Le nom de la pièce est échappé.
    assert.match(svg, /Bloc &lt;A&gt;/);
  });

  it("l'écran et le DXF partagent les mêmes entités", () => {
    const entities = sheetEntities(DATA, { locale: "fr-FR" });
    const texts = entities.filter((e) => e.k === "text").map((e) => e.text);
    assert.ok(texts.includes("40") && texts.includes("10") && texts.includes("20,5"));
    // Trois cotes : deux pointes de flèche chacune.
    assert.equal(entities.filter((e) => e.k === "fill").length, 6);
    assert.ok(entities.every((e) => ["cadre", "visible", "cache", "cote", "texte"]
      .includes(e.layer)));
  });
});
