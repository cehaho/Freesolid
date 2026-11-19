// La feuille de mise en plan à l'écran : un A4 paysage, ses vues
// projetées par le moteur (`drawing_views`), les cotes d'encombrement et
// le cartouche — comme la mise en plan des modeleurs courants. On la
// règle (échelle, arêtes cachées), on l'imprime (PDF) ou on l'exporte en
// DXF (`make_drawing`).

import { t } from "./i18n.js";
import { fmtLocal } from "./num.js";

const SCALES = [
  ["", "Auto"], ["5", "5:1"], ["2", "2:1"], ["1", "1:1"], ["0.5", "1:2"],
  ["0.2", "1:5"], ["0.1", "1:10"], ["0.05", "1:20"], ["0.02", "1:50"],
  ["0.01", "1:100"],
];

const ESCAPES = { "&": "&amp;", "<": "&lt;", ">": "&gt;", "\"": "&quot;" };

function esc(text) {
  return String(text ?? "").replace(/[&<>"]/g, (c) => ESCAPES[c]);
}

/** Une cote lue sur la feuille : séparateur régional, sans zéros inutiles
 *  (« 40 », « 12,5 »). */
export function dimText(value, decimals = 2, locale = undefined) {
  const text = fmtLocal(value, decimals, locale);
  return text.includes(",") || text.includes(".")
    ? text.replace(/([,.]\d*?)0+$/, "$1").replace(/[,.]$/, "")
    : text;
}

// Les entités de la feuille, en mm, y vers le bas : l'écran en fait un
// SVG (`sheetSvg`), le moteur un DXF (`write_drawing_dxf`) — une seule
// mise en page. Calques : cadre, visible, cache, cote, texte.
//   { k: "line", a: [x, y], b: [x, y], layer }
//   { k: "poly", pts: [[x, y], …], layer }
//   { k: "fill", pts: [[x, y], …], layer }        (pointe de flèche)
//   { k: "text", at: [x, y], text, size, anchor: "start"|"middle", angle, layer, cls }

function dimension(out, { axis, a, b, at, from, text }) {
  const arrow = 2.2;
  const half = 0.7;
  const layer = "cote";
  const tip = at + Math.sign(at - from) * 1.5;
  if (axis === "x") {
    out.push({ k: "line", a: [a, from], b: [a, tip], layer });
    out.push({ k: "line", a: [b, from], b: [b, tip], layer });
    out.push({ k: "line", a: [a, at], b: [b, at], layer });
    out.push({ k: "fill", pts: [[a, at], [a + arrow, at - half], [a + arrow, at + half]], layer });
    out.push({ k: "fill", pts: [[b, at], [b - arrow, at - half], [b - arrow, at + half]], layer });
    out.push({ k: "text", at: [(a + b) / 2, at - 1], text, size: 3.5,
               anchor: "middle", angle: 0, layer });
  } else {
    out.push({ k: "line", a: [from, a], b: [tip, a], layer });
    out.push({ k: "line", a: [from, b], b: [tip, b], layer });
    out.push({ k: "line", a: [at, a], b: [at, b], layer });
    out.push({ k: "fill", pts: [[at, a], [at - half, a + arrow], [at + half, a + arrow]], layer });
    out.push({ k: "fill", pts: [[at, b], [at - half, b - arrow], [at + half, b - arrow]], layer });
    out.push({ k: "text", at: [at - 1, (a + b) / 2], text, size: 3.5,
               anchor: "middle", angle: 90, layer });
  }
}

/** Les entités de la feuille, à partir de `drawing_views`. */
export function sheetEntities(data, { decimals = 2, date = "", locale } = {}) {
  const { width, height, margin } = data.sheet;
  const block = data.title_block;
  const s = data.scale;
  const out = [];
  const rect = (x, y, w, h, layer) => out.push({ k: "poly", layer,
    pts: [[x, y], [x + w, y], [x + w, y + h], [x, y + h], [x, y]] });
  rect(margin, margin, width - 2 * margin, height - 2 * margin, "cadre");

  const boxes = {};
  for (const view of data.views) {
    const [cx, cy] = view.center;
    const w = s * view.width;
    const h = s * view.height;
    boxes[view.name] = { x0: cx - w / 2, x1: cx + w / 2, y0: cy - h / 2, y1: cy + h / 2 };
    const place = (line) => line.map(([x, y]) => [cx + s * x, cy - s * y]);
    for (const line of view.hidden ?? []) {
      out.push({ k: "poly", pts: place(line), layer: "cache" });
    }
    for (const line of view.visible) {
      out.push({ k: "poly", pts: place(line), layer: "visible" });
    }
    out.push({ k: "text", at: [cx, cy + h / 2 + 9], text: view.label, size: 3.2,
               anchor: "middle", angle: 0, layer: "texte" });
  }

  // Cotes d'encombrement : la largeur au-dessus de la face, la hauteur à
  // sa droite, la profondeur à droite du dessus.
  for (const dim of data.dims ?? []) {
    const box = boxes[dim.view];
    if (!box) continue;
    const text = dimText(dim.value, decimals, locale);
    if (dim.axis === "x") {
      dimension(out, { axis: "x", a: box.x0, b: box.x1, at: box.y0 - 6,
                       from: box.y0 - 1, text });
    } else {
      dimension(out, { axis: "y", a: box.y0, b: box.y1, at: box.x1 + 7,
                       from: box.x1 + 1, text });
    }
  }

  // Cartouche.
  const bx = width - margin - block.width;
  const by = height - margin - block.height;
  const bw = block.width;
  const bh = block.height;
  const row = bh / 3;
  const col = bw / 3;
  rect(bx, by, bw, bh, "cadre");
  out.push({ k: "line", a: [bx, by + row], b: [bx + bw, by + row], layer: "cadre" });
  out.push({ k: "line", a: [bx, by + 2 * row], b: [bx + bw, by + 2 * row], layer: "cadre" });
  out.push({ k: "line", a: [bx + col, by + row], b: [bx + col, by + bh], layer: "cadre" });
  out.push({ k: "line", a: [bx + 2 * col, by + row], b: [bx + 2 * col, by + bh], layer: "cadre" });
  const cell = (x, y, key, value, size = 3.5) => {
    out.push({ k: "text", at: [x + 1.5, y + 3], text: key, size: 2.4, anchor: "start",
               angle: 0, layer: "texte", cls: "k" });
    out.push({ k: "text", at: [x + 1.5, y + row - 2.5], text: value, size,
               anchor: "start", angle: 0, layer: "texte" });
  };
  cell(bx, by, t("Pièce"), data.part ?? "", 5);
  cell(bx, by + row, t("Matière"), data.material ?? "—");
  cell(bx + col, by + row, t("Échelle"), data.scale_label);
  cell(bx + 2 * col, by + row, t("Unité"), "mm");
  cell(bx, by + 2 * row, t("Date"), date);
  cell(bx + col, by + 2 * row, t("Projection"), t("1er dièdre"));
  cell(bx + 2 * col, by + 2 * row, t("Feuille"), "A4 — 1/1");
  return out;
}

const STROKES = { cadre: 0.5, visible: 0.35, cache: 0.18, cote: 0.18 };

const pts = (list) => list.map(([x, y]) => `${x.toFixed(3)},${y.toFixed(3)}`).join(" ");

/** Le SVG de la feuille (unités : mm), à partir de `drawing_views`. */
export function sheetSvg(data, options = {}) {
  const { width, height } = data.sheet;
  const out = [
    `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${width} ${height}" `
      + `width="${width}mm" height="${height}mm" class="ds-svg" `
      + `font-family="Arial, Helvetica, sans-serif">`,
    `<rect x="0" y="0" width="${width}" height="${height}" fill="#fff"/>`,
  ];
  for (const e of sheetEntities(data, options)) {
    const stroke = `stroke="#000" stroke-width="${STROKES[e.layer] ?? 0.25}"`;
    if (e.k === "line") {
      out.push(`<line class="${e.layer}" x1="${e.a[0]}" y1="${e.a[1]}" `
        + `x2="${e.b[0]}" y2="${e.b[1]}" ${stroke}/>`);
    } else if (e.k === "poly") {
      const dash = e.layer === "cache" ? ' stroke-dasharray="1.6 0.8"' : "";
      out.push(`<polyline class="${e.layer}" points="${pts(e.pts)}" fill="none" `
        + `${stroke}${dash} stroke-linejoin="round" stroke-linecap="round"/>`);
    } else if (e.k === "fill") {
      out.push(`<polygon class="${e.layer}" points="${pts(e.pts)}" fill="#000"/>`);
    } else if (e.k === "text") {
      const [x, y] = e.at;
      const turn = e.angle ? ` transform="rotate(${-e.angle} ${x} ${y})"` : "";
      const fill = e.cls === "k" ? "#444" : "#000";
      const weight = e.size >= 5 ? ' font-weight="bold"' : "";
      out.push(`<text x="${x}" y="${y}" font-size="${e.size}" text-anchor="${e.anchor}" `
        + `fill="${fill}"${weight}${turn}>${esc(e.text)}</text>`);
    }
  }
  out.push("</svg>");
  return out.join("");
}

/** Le mode Mise en plan : la feuille par-dessus la vue 3D. */
export function installDrawingSheet({ viewport, call, say, pickFile, decimals }) {
  const doc = viewport.ownerDocument;
  const host = doc.createElement("div");
  host.id = "drawing-sheet";
  host.hidden = true;
  host.innerHTML = `
    <div class="ds-bar">
      <strong class="ds-title"></strong>
      <label>${esc(t("Échelle"))} <select class="ds-scale"></select></label>
      <label><input type="checkbox" class="ds-hidden" checked> ${esc(t("Arêtes cachées"))}</label>
      <span class="ds-grow"></span>
      <button class="ds-dxf">${esc(t("Exporter en DXF…"))}</button>
      <button class="ds-print">${esc(t("Imprimer / PDF…"))}</button>
      <button class="ds-close" title="${esc(t("Fermer (Échap)"))}">${esc(t("Fermer"))}</button>
    </div>
    <div class="ds-paper"></div>`;
  viewport.appendChild(host);
  const scaleEl = host.querySelector(".ds-scale");
  for (const [value, label] of SCALES) {
    const option = doc.createElement("option");
    option.value = value;
    option.textContent = value ? label : t(label);
    scaleEl.appendChild(option);
  }
  const hiddenEl = host.querySelector(".ds-hidden");
  const paper = host.querySelector(".ds-paper");
  const title = host.querySelector(".ds-title");
  let current = null;
  const sheetOptions = () => ({
    decimals: decimals?.() ?? 2,
    date: new Date().toLocaleDateString(),
  });

  async function render() {
    const params = { hidden: hiddenEl.checked };
    if (scaleEl.value) params.scale = Number(scaleEl.value);
    let data;
    try {
      data = await call("drawing_views", params);
    } catch (error) {
      say(error.message, true);
      if (!current) close();
      return;
    }
    current = data;
    title.textContent = t("Mise en plan — {s}", { s: data.scale_label });
    paper.innerHTML = sheetSvg(data, sheetOptions());
  }

  async function open() {
    host.hidden = false;
    doc.body.classList.add("drawing-open");
    paper.innerHTML = "";
    current = null;
    await render();
  }

  function close() {
    host.hidden = true;
    doc.body.classList.remove("drawing-open");
  }

  scaleEl.addEventListener("change", render);
  hiddenEl.addEventListener("change", render);
  host.querySelector(".ds-close").addEventListener("click", close);
  host.querySelector(".ds-print").addEventListener("click", () => doc.defaultView.print());
  host.querySelector(".ds-dxf").addEventListener("click", async () => {
    if (!current) return;
    const path = await pickFile("drawing");
    if (!path) return;
    // La feuille telle qu'elle est à l'écran : mêmes entités.
    const params = {
      path, width: current.sheet.width, height: current.sheet.height,
      entities: sheetEntities(current, sheetOptions()),
    };
    try {
      const out = await call("write_drawing_dxf", params);
      say(t("Mise en plan exportée : {path} ({size} Ko)",
        { path: out.path, size: (out.size / 1024).toFixed(1) }), false, { fade: true });
    } catch (error) {
      say(error.message, true);
    }
  });
  doc.addEventListener("keydown", (event) => {
    if (host.hidden || event.key !== "Escape") return;
    if (!doc.getElementById("file-dialog")?.hidden) return;
    event.preventDefault();
    close();
  });

  return { open, close, isOpen: () => !host.hidden };
}
