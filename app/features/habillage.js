// Fonctions — habillage : congé, chanfrein (arête, sommet), coque,
// dépouille.

import { t } from "../i18n.js";
import { num, plainNumber } from "../num.js";
import {
  dressup,
  measureRow,
  readMeasure,
  sameMeasure,
  storedMeasure,
} from "./commun.js";

function dressupParams(sel) {
  return sel.kind === "edges"
    ? { edges: sel.edges } : { face: sel.face };
}

/** Coque : faces à ouvrir (une ou plusieurs), épaisseur, sens. */
export function shellBuild(v) {
  const faces = (v.faces?.items ?? []).map((item) => item.face)
    .filter((face) => face != null);
  const thickness = num(v.thickness);
  if (!faces.length || !(thickness > 0)) return null;
  return { op: "add_thickness",
           params: { faces, thickness, outward: !!v.outward } };
}

/** Coque qu'on réédite : son épaisseur et son sens (les faces ouvertes
 *  restent celles de la création). */
export function shellEditGroups(feature) {
  return [{ label: "Paramètres", rows: [
    measureRow("thickness", "Épaisseur",
               chamferFieldValue(feature.params, "thickness", 2), "mm"),
    { type: "check", key: "outward", label: "Coque vers l'extérieur",
      value: !!feature.shell?.outward },
  ] }];
}

/** Valeurs `set_params` d'une coque rééditée : `{}` si rien n'a changé,
 *  null si l'épaisseur est invalide. */
export function shellEditValues(v, feature) {
  const stored = storedMeasure(feature.params, "thickness", 2);
  const thickness = readMeasure(v.thickness, stored,
                                { min: 0, max: Infinity });
  if (thickness == null) return null;
  const values = {};
  if (!sameMeasure(thickness, stored)) values.thickness = thickness;
  if (!!v.outward !== !!feature.shell?.outward) values.outward = !!v.outward;
  return values;
}

function expressionText(raw) {
  const text = String(raw ?? "").trim();
  return text.length > 0 && plainNumber(text) == null;
}

const CHAMFER_KINDS = new Set(["egale", "deux", "angle"]);

/** Champs du panneau : le type décide de ce qui est visible. */
export function chamferRows({
  kind = "egale", size = 2, size2 = 2, angle = 45, flip = false,
} = {}) {
  return [
    { type: "select", key: "kind", value: kind, label: "Type de chanfrein",
      options: [["egale", "Distance égale"], ["deux", "Deux distances"],
                ["angle", "Distance et angle"]] },
    measureRow("size", "Distance", size, "mm"),
    measureRow("size2", "Seconde distance", size2, "mm",
      (v) => v.kind === "deux"),
    measureRow("angle", "Angle", angle, "°",
      (v) => v.kind === "angle"),
    { type: "check", key: "flip", label: "Inverser les côtés",
      value: !!flip, showIf: (v) => v.kind === "deux" || v.kind === "angle" },
  ];
}

/** Valeur affichée : l'expression si la cote `key` en a une, sinon le nombre. */
export function chamferFieldValue(params, key, fallback) {
  const found = (params ?? []).find((item) => item.key === key);
  if (found?.expr) return found.expr;
  if (found && found.value != null) return found.value;
  return fallback;
}

/** Zone d'un congé ou d'un chanfrein qu'on réédite : ce qu'il arrondit
 *  (`dressup` de l'arbre : des arêtes ou une face), comme la zone de la
 *  création ; null si l'arbre ne le dit pas. */
export function dressupPick(dressup) {
  if (Array.isArray(dressup?.edges) && dressup.edges.length) {
    return { kind: "edges", edges: [...dressup.edges] };
  }
  if (Number.isInteger(dressup?.face)) {
    return { kind: "face", face: dressup.face };
  }
  return null;
}

/** Valeurs `set_params` de la zone rééditée : `{}` si elle n'a pas
 *  changé, `{ edges }` ou `{ face }` sinon, null si elle est vide. */
export function dressupPickValues(sel, dressup) {
  if (sel?.kind === "edges" && sel.edges?.length) {
    const chosen = [...new Set(sel.edges)];
    const before = new Set(dressup?.edges ?? []);
    const same = chosen.length === before.size
      && chosen.every((edge) => before.has(edge));
    return same ? {} : { edges: chosen };
  }
  if (sel?.kind === "face" && Number.isInteger(sel.face)) {
    return sel.face === dressup?.face ? {} : { face: sel.face };
  }
  return null;
}

/** Zone des faces ouvertes d'une coque qu'on réédite. */
export function shellFacesPick(faces) {
  return { kind: "face",
           items: (faces ?? []).map((face) => ({ kind: "face", face })) };
}

/** Valeurs `set_params` des faces ouvertes : `{}` si elles n'ont pas
 *  changé, `{ faces }` sinon, null si la zone est vide. */
export function shellFacesValues(zone, before) {
  const chosen = [...new Set((zone?.items ?? []).map((item) => item.face)
    .filter((face) => Number.isInteger(face)))];
  if (!chosen.length) return null;
  const kept = new Set(before ?? []);
  const same = chosen.length === kept.size
    && chosen.every((face) => kept.has(face));
  return same ? {} : { faces: chosen };
}

const NEUTRAL_PLANES = [["XY", "Plan de dessus"], ["XZ", "Plan de face"],
                        ["YZ", "Plan de droite"]];

/** Dépouille qu'on réédite : son angle et son plan neutre. */
export function draftEditGroups(feature) {
  return [{ label: "Angle de dépouille", rows: [
    measureRow("angle", "Angle",
               chamferFieldValue(feature.params, "angle", 3), "°"),
    { type: "select", key: "neutral", label: "Plan neutre",
      value: feature.draft?.neutral ?? "XY", options: NEUTRAL_PLANES },
  ] }];
}

/** Valeurs `set_params` de l'angle et du plan neutre : `{}` si rien n'a
 *  changé, null si l'angle est invalide. */
export function draftEditValues(v, feature) {
  const stored = storedMeasure(feature.params, "angle", 3);
  const angle = readMeasure(v.angle, stored, { min: 0, max: 90 });
  if (angle == null) return null;
  const values = {};
  if (!sameMeasure(angle, stored)) values.angle = angle;
  const neutral = v.neutral ?? feature.draft?.neutral ?? "XY";
  if (neutral !== (feature.draft?.neutral ?? "XY")) values.neutral = neutral;
  return values;
}

/** Congé qu'on réédite : son rayon. */
export function filletEditRows(feature) {
  return [measureRow("radius", "Rayon",
                     chamferFieldValue(feature.params, "radius", 3), "mm")];
}

/** Valeurs `set_params` du rayon : `{}` s'il n'a pas changé, null s'il
 *  est invalide. */
export function filletEditValues(v, feature) {
  const stored = storedMeasure(feature.params, "radius", 3);
  const radius = readMeasure(v.radius, stored, { min: 0, max: Infinity });
  if (radius == null) return null;
  return sameMeasure(radius, stored) ? {} : { radius };
}

/** Chanfrein de sommet : une distance égale, ou une par arête. */
export function vertexChamferRows({ distances = [2, 2, 2] } = {}) {
  const same = distances.every((d) => d === distances[0]);
  return [
    { type: "select", key: "vkind", value: same ? "egale" : "trois",
      options: [["egale", "Distance égale"], ["trois", "Une par arête"]] },
    { type: "number", key: "d1", label: "Distance", value: distances[0],
      unit: "mm", min: 0.01 },
    { type: "number", key: "d2", label: "Distance 2", value: distances[1],
      unit: "mm", min: 0.01, showIf: (v) => v.vkind === "trois" },
    { type: "number", key: "d3", label: "Distance 3", value: distances[2],
      unit: "mm", min: 0.01, showIf: (v) => v.vkind === "trois" },
  ];
}

/** Distances du panneau → [d] ou [d1, d2, d3] ; null si l'une est fausse. */
export function vertexChamferDistances(v) {
  const keys = v.vkind === "trois" ? ["d1", "d2", "d3"] : ["d1"];
  const values = keys.map((key) => num(v[key]));
  return values.every((d) => d > 0) ? values : null;
}

/** Zone du coin d'un chanfrein de sommet, à la création comme à la
 *  réédition (`value` : son coin). */
export function vertexChamferRow(value = null) {
  return { type: "selection", key: "pos", accepts: ["vertex"],
           hint: "Cliquez près d'un coin de la pièce",
           ...(value ? { value } : {}) };
}

/** Zone du coin d'un chanfrein de sommet réédité (`point` de l'arbre :
 *  le sommet sur la pièce à son rang). */
export function vertexChamferPick(point) {
  if (!Array.isArray(point) || point.length !== 3) return null;
  const [x, y, z] = point;
  return { kind: "vertex", x, y, z };
}

/** Le coin re-choisi : `{}` si c'est le même, `{ point }` sinon, null si
 *  la zone est vide. */
export function vertexChamferPointValues(sel, point) {
  if (sel?.kind !== "vertex") return null;
  const at = [sel.x, sel.y, sel.z];
  const same = Array.isArray(point)
    && at.every((c, i) => Math.abs(c - point[i]) < 1e-6);
  return same ? {} : { point: at };
}

/** Distances d'un chanfrein de sommet réédité : `{}` si elles n'ont pas
 *  changé, `{ distances }` sinon, null si l'une est fausse. */
export function vertexChamferEditValues(v, chamfer) {
  const distances = vertexChamferDistances(v);
  if (!distances) return null;
  const before = chamfer?.distances ?? [];
  const same = [0, 1, 2].every((i) => Math.abs(
    distances[distances.length === 1 ? 0 : i] - before[i]) < 1e-9);
  return same ? {} : { distances };
}

/** Params `add_chamfer`, ou null si les champs visibles sont invalides. */
export function chamferCreationParams(v) {
  const kind = v.kind || "egale";
  if (!CHAMFER_KINDS.has(kind)) return null;
  const size = plainNumber(v.size);
  if (!(size > 0)) return null;
  const params = { size, chamfer_type: kind };
  if (kind === "deux") {
    const size2 = plainNumber(v.size2);
    if (!(size2 > 0)) return null;
    params.size2 = size2;
    params.flip = !!v.flip;
  } else if (kind === "angle") {
    const angle = plainNumber(v.angle);
    if (!(angle > 0) || !(angle < 90)) return null;
    params.angle = angle;
    params.flip = !!v.flip;
  }
  return params;
}

/** Message français quand la saisie ne peut pas être appliquée. */
export function chamferProblem(v) {
  const kind = v.kind || "egale";
  const size = plainNumber(v.size);
  if (size == null) {
    if (!expressionText(v.size)) return "Distance de chanfrein invalide";
  } else if (!(size > 0)) {
    return "Distance de chanfrein invalide";
  }
  if (kind === "deux") {
    const size2 = plainNumber(v.size2);
    if (size2 == null) {
      if (!expressionText(v.size2)) return "Seconde distance de chanfrein invalide";
    } else if (!(size2 > 0)) {
      return "Seconde distance de chanfrein invalide";
    }
  }
  if (kind === "angle") {
    const angle = plainNumber(v.angle);
    if (angle == null) {
      if (!expressionText(v.angle)) return "Angle de chanfrein invalide";
    } else if (!(angle > 0) || !(angle < 90)) {
      return "Angle de chanfrein invalide";
    }
  }
  return "Valeurs du chanfrein invalides";
}

/**
 * Valeurs `set_params` pour rééditer un chanfrein.
 * `{}` si rien n'a changé, `null` si la saisie est invalide.
 */
export function chamferEditValues(v, chamfer, params) {
  const kind = v.kind || "egale";
  if (!CHAMFER_KINDS.has(kind)) return null;
  const sizeStored = storedMeasure(params, "size", chamfer.size);
  const size = readMeasure(v.size, sizeStored, { min: 0, max: Infinity });
  if (size == null) return null;
  const values = { kind, size };
  const flip = kind === "egale" ? false : !!v.flip;
  let secondSame = true;
  if (kind === "deux") {
    const stored = storedMeasure(params, "size2", chamfer.size2);
    const size2 = readMeasure(v.size2, stored, { min: 0, max: Infinity });
    if (size2 == null) return null;
    values.size2 = size2;
    values.flip = flip;
    secondSame = sameMeasure(size2, stored);
  } else if (kind === "angle") {
    const stored = storedMeasure(params, "angle", chamfer.angle);
    const angle = readMeasure(v.angle, stored, { min: 0, max: 90 });
    if (angle == null) return null;
    values.angle = angle;
    values.flip = flip;
    secondSame = sameMeasure(angle, stored);
  } else {
    values.flip = false;
  }
  const unchanged = kind === chamfer.type
    && flip === !!chamfer.flip
    && sameMeasure(size, sizeStored)
    && secondSame;
  return unchanged ? {} : values;
}

export const HABILLAGE = [
  dressup({
    button: "btn-fillet",
    op: "add_fillet",
    icon: "fillet", title: "Congé",
    selectionLabel: "Éléments à arrondir",
    accepts: ["edges", "face"],
    hint: "Cliquez des arêtes (Ctrl = ajouter) ou une face",
    group: "Paramètres du congé",
    rows: [{ type: "number", key: "radius", label: "Rayon", value: 3,
             unit: "mm", min: 0.01 }],
    build: (v) => {
      const radius = num(v.radius);
      return radius > 0
        ? { op: "add_fillet",
            params: { ...dressupParams(v.sel), radius } }
        : null;
    },
  }),
  dressup({
    button: "btn-chamfer",
    op: "add_chamfer",
    icon: "chamfer", title: "Chanfrein",
    selectionLabel: "Éléments à chanfreiner",
    accepts: ["edges", "face"],
    hint: "Cliquez des arêtes (Ctrl = ajouter) ou une face",
    group: "Paramètres du chanfrein",
    rows: chamferRows(),
    build: (v) => {
      const params = chamferCreationParams(v);
      return params
        ? { op: "add_chamfer",
            params: { ...dressupParams(v.sel), ...params } }
        : null;
    },
    invalid: (v) => chamferProblem(v),
  }),
  {
    button: "btn-vertex-chamfer",
    op: "add_vertex_chamfer",
    icon: "vertex_chamfer", title: "Chanfrein de sommet",
    groups: () => [
      { label: "Sommet", rows: [vertexChamferRow()] },
      { label: "Distances", rows: vertexChamferRows() },
    ],
    build: (v) => {
      const item = v.pos?.kind === "vertex" ? v.pos : null;
      const distances = vertexChamferDistances(v);
      return item && distances
        ? { op: "add_vertex_chamfer",
            params: { point: [item.x, item.y, item.z], distances } }
        : null;
    },
    invalid: (v) => (v.pos ? "Distance de chanfrein invalide"
      : "Cliquez près d'un coin de la pièce"),
    refresh: "part",
  },
  {
    button: "btn-shell",
    op: "add_thickness",
    icon: "shell", title: "Coque",
    dressup: true,
    groups: (ctx) => {
      const first = ctx.selection(["face"]);
      return [
        { label: "Faces à supprimer",
          rows: [{ type: "selection", key: "faces", accepts: ["face"],
                   multiple: true,
                   hint: "Cliquez les faces à ouvrir — un second clic retire",
                   value: { kind: "face",
                            items: first?.face != null ? [first] : [] } }] },
        { label: "Paramètres",
          rows: [
            { type: "number", key: "thickness", label: "Épaisseur",
              value: 2, unit: "mm", min: 0.01 },
            { type: "check", key: "outward", label: "Coque vers l'extérieur",
              value: false },
          ] },
      ];
    },
    build: (v) => shellBuild(v),
    invalid: (v) => ((v.faces?.items ?? []).length
      ? "Épaisseur invalide"
      : { text: t("Coque : cliquez au moins une face à ouvrir"), tone: "guide" }),
    refresh: "part",
  },
  dressup({
    button: "btn-draft",
    op: "add_draft",
    icon: "draft", title: "Dépouille",
    selectionLabel: "Face à dépouiller",
    group: "Angle de dépouille",
    rows: [
      { type: "number", key: "angle", label: "Angle", value: 3,
        unit: "°", min: 0.01 },
      { type: "select", key: "neutral", value: "XY", label: "Plan neutre",
        options: NEUTRAL_PLANES },
    ],
    build: (v) => {
      const angle = num(v.angle);
      return angle > 0
        ? { op: "add_draft",
            params: { face: v.sel.face, angle, neutral: v.neutral } }
        : null;
    },
  }),
];
