// Fonctions — répétitions linéaire et circulaire, symétrie.

import { num } from "../num.js";
import { bodyZoneRow, bodyZoneValue, zoneNames } from "./commun.js";

// ---------- répétitions et symétrie ----------
// Répéter des fonctions du corps actif, ou des corps entiers : chaque
// occurrence d'un corps devient un nouveau corps qui suit sa source
// (add_body_pattern).
// Fonctions à répéter : clic dans l'arbre (plusieurs, un second clic
// retire) ; vide = la dernière fonction. Direction : un axe d'origine ou
// une arête droite cliquée dans la zone graphique.
// Corps à répéter, corps concernés : des zones, remplies par un clic dans
// la vue ou sur une ligne du dossier.

const repeatsBodies = (v) => v.target === "bodies";

export function patternTargetGroup() {
  return {
    label: "Répéter",
    rows: [{ type: "select", key: "target", value: "features",
             options: [["features", "Des fonctions"],
                       ["bodies", "Des corps"]] }],
  };
}

/** Les corps à répéter : une zone, remplie du corps actif. Un corps vide
 *  n'y entre pas. */
export function patternBodiesGroup(ctx) {
  const bodies = ctx?.lastTree?.bodies ?? [];
  const active = bodies.filter((body) => body.active && body.has_solid);
  return {
    label: "Corps à répéter",
    showIf: repeatsBodies,
    rows: [bodyZoneRow("sources", {
      value: bodyZoneValue(active),
      allows: (pick) => bodies.some((body) => body.name === pick.name
        && body.has_solid === true) })],
  };
}

/** Les corps de la zone, dans l'ordre des clics. */
export function patternBodiesParams(v) {
  return zoneNames(v.sources);
}

const otherBodies = (ctx) =>
  (ctx?.lastTree?.bodies ?? []).filter((body) => !body.active);

/** Corps concernés : rien tant que la pièce n'a qu'un corps. Comme dans
 *  les modeleurs courants, les occurrences creusent les corps qu'elles
 *  traversent — le moteur les trouve. */
export function patternScopeGroup(ctx) {
  const others = otherBodies(ctx);
  if (!others.length) return null;
  return {
    label: "Corps concernés",
    showIf: (v) => !repeatsBodies(v),
    rows: [
      { type: "select", key: "scopeMode", value: "crossed",
        options: [["crossed", "Corps traversés"],
                  ["active", "Corps actif seulement"],
                  ["all", "Tous les corps"],
                  ["selected", "Corps choisis"]] },
      bodyZoneRow("scopeBodies", {
        allows: (pick) => others.some((body) => body.name === pick.name),
        showIf: (v) => v.scopeMode === "selected" }),
      { type: "note", readonly: true,
        text: "Seuls les enlèvements de matière creusent les autres corps",
        showIf: (v) => v.scopeMode && v.scopeMode !== "active" },
    ],
  };
}

/** Params moteur : rien, et le moteur prend les corps traversés ; sinon
 *  `scope`, les autres corps creusés (vide : le corps actif seul). */
export function patternScopeParams(v, ctx) {
  const others = otherBodies(ctx);
  if (!others.length || (v.scopeMode ?? "crossed") === "crossed") return {};
  const names = others.map((body) => body.name);
  const chosen = v.scopeMode === "all" ? names
    : v.scopeMode === "selected"
      ? zoneNames(v.scopeBodies).filter((name) => names.includes(name)) : [];
  return { scope: chosen };
}

/** Groupes d'une répétition : quoi répéter, puis `own` (direction, plan). */
function patternGroups(ctx, own) {
  return [
    patternTargetGroup(),
    { ...patternFeaturesGroup(ctx), showIf: (v) => !repeatsBodies(v) },
    patternBodiesGroup(ctx),
    ...own,
    patternScopeGroup(ctx),
  ].filter(Boolean);
}

/** Des corps → add_body_pattern (`kind`) ; des fonctions → `op`. */
function patternBuild(v, ctx, op, kind, params) {
  if (repeatsBodies(v)) {
    const bodies = patternBodiesParams(v);
    return bodies.length
      ? { op: "add_body_pattern", params: { kind, bodies, ...params } }
      : null;
  }
  return { op, params: { ...params, ...patternFeaturesParams(v),
                         ...patternScopeParams(v, ctx) } };
}

function patternInvalid(v) {
  return repeatsBodies(v) && !patternBodiesParams(v).length
    ? "Choisissez au moins un corps à répéter" : "Valeurs invalides";
}

export function patternFeaturesGroup(ctx) {
  return {
    label: "Fonctions à répéter",
    rows: [{ type: "selection", key: "features", accepts: ["feature"],
             multiple: true, value: ctx?.selection?.(["feature"]) ?? null,
             hint: "Cliquez les fonctions dans l'arbre — vide : la dernière" }],
  };
}

export function patternFeaturesParams(v) {
  const items = v.features?.items ?? [];
  return items.length ? { features: items.map((i) => i.name) } : {};
}

export function patternDirectionRows(defaultAxis) {
  return [
    { type: "select", key: "dirKind", value: "axis",
      options: [["axis", "Axe d'origine"], ["edge", "Arête"]] },
    { type: "select", key: "axis", value: defaultAxis,
      options: [["X", "Axe X"], ["Y", "Axe Y"], ["Z", "Axe Z"]],
      showIf: (v) => v.dirKind !== "edge" },
    { type: "selection", key: "edge", accepts: ["edges"],
      hint: "Cliquez une arête droite",
      showIf: (v) => v.dirKind === "edge" },
    { type: "check", key: "reversed", label: "Inverser la direction",
      value: false },
  ];
}

/** Deuxième direction d'un réseau linéaire → params, null si invalide. */
export function linearSecondDirection(v) {
  const length2 = num(v.length2);
  const count2 = parseInt(v.count2, 10);
  if (!(length2 > 0) || !(count2 >= 2)) return null;
  return { axis2: v.axis2 || "Y", length2, count2, reversed2: !!v.reversed2 };
}

/** Ce que compte la distance d'un réseau linéaire : le pas entre deux
 *  occurrences, ou la longueur totale. */
function patternModeRow(value) {
  return { type: "select", key: "mode", value,
           options: [["spacing", "Pas entre occurrences"],
                     ["extent", "Longueur totale"]] };
}

export function patternDirectionParams(v) {
  const params = { reversed: !!v.reversed };
  const edge = v.edge?.edges?.[0];
  if (v.dirKind === "edge" && edge != null) params.edge = edge;
  else params.axis = v.axis;
  return params;
}

export const REPETITIONS = [
  {
    button: "btn-linpattern",
    op: ["add_linear_pattern", "add_body_pattern"],
    icon: "linear_pattern",
    title: "Réseau linéaire",
    groups: (ctx) => patternGroups(ctx, [
      {
        label: "Direction 1",
        rows: [
          ...patternDirectionRows("X"),
          patternModeRow("spacing"),
          { type: "number", key: "length", label: "Distance",
            value: 20, unit: "mm", min: 0.01 },
          { type: "number", key: "count", label: "Nombre d'occurrences",
            value: 3, min: 2, step: 1 },
        ],
      },
      {
        label: "Direction 2",
        rows: [
          { type: "check", key: "dir2", label: "Deuxième direction",
            value: false },
          { type: "select", key: "axis2", value: "Y",
            options: [["X", "Axe X"], ["Y", "Axe Y"], ["Z", "Axe Z"]],
            showIf: (v) => v.dir2 },
          { type: "check", key: "reversed2", label: "Inverser la direction",
            value: false, showIf: (v) => v.dir2 },
          { type: "number", key: "length2", label: "Distance",
            value: 20, unit: "mm", min: 0.01, showIf: (v) => v.dir2 },
          { type: "number", key: "count2", label: "Nombre d'occurrences",
            value: 2, min: 2, step: 1, showIf: (v) => v.dir2 },
        ],
      },
    ]),
    build: (v, ctx) => {
      const length = num(v.length);
      const count = parseInt(v.count, 10);
      const second = v.dir2 ? linearSecondDirection(v) : {};
      return length && count >= 2 && second
        ? patternBuild(v, ctx, "add_linear_pattern", "linear",
          { ...patternDirectionParams(v), length, count,
            spacing: v.mode === "spacing", ...second })
        : null;
    },
    invalid: patternInvalid,
    refresh: "part",
  },
  {
    button: "btn-polpattern",
    op: ["add_polar_pattern", "add_body_pattern"],
    icon: "polar_pattern",
    title: "Réseau circulaire",
    groups: (ctx) => patternGroups(ctx, [
      {
        label: "Axe",
        rows: [
          ...patternDirectionRows("Z"),
          { type: "number", key: "angle", label: "Angle total", value: 360,
            unit: "°", min: 0.01 },
          { type: "number", key: "count", label: "Nombre d'occurrences",
            value: 4, min: 2, step: 1 },
        ],
      },
    ]),
    build: (v, ctx) => {
      const angle = num(v.angle);
      const count = parseInt(v.count, 10);
      return angle && count >= 2
        ? patternBuild(v, ctx, "add_polar_pattern", "polar",
          { ...patternDirectionParams(v), count, angle })
        : null;
    },
    invalid: patternInvalid,
    refresh: "part",
  },
  {
    button: "btn-mirror",
    op: ["add_mirror", "add_body_pattern"],
    icon: "mirror",
    title: "Symétrie",
    groups: (ctx) => patternGroups(ctx, [
      {
        label: "Plan de symétrie",
        rows: [
          { type: "select", key: "plane", value: "YZ",
            options: [["YZ", "Plan de droite"], ["XZ", "Plan de face"],
                      ["XY", "Plan de dessus"]] },
        ],
      },
    ]),
    build: (v, ctx) => patternBuild(v, ctx, "add_mirror", "mirror",
                                    { plane: v.plane }),
    invalid: patternInvalid,
    refresh: "part",
  },
];

// ---------- réédition d'une répétition de fonctions ----------
// Le panneau de la création, rempli de ce qu'elle est (`pattern` de
// l'arbre) ; la pièce se montre à son rang. Seul ce qui change part au
// moteur (set_params).

/** Libellé d'une fonction de l'arbre, sinon son nom. */
function featureLabel(tree, name) {
  const find = (items) => {
    for (const item of items ?? []) {
      if (item.name === name) return item.label;
      const inner = find(item.children);
      if (inner) return inner;
    }
    return null;
  };
  return find(tree?.features) ?? name;
}

/** La zone des fonctions répétées, remplie de celles de la répétition. */
export function patternFeaturesPick(pattern, tree) {
  return { kind: "feature", items: (pattern?.features ?? []).map(
    (name) => ({ kind: "feature", name, label: featureLabel(tree, name) })) };
}

/** Les fonctions re-choisies : `{}` si ce sont les mêmes (dans n'importe
 *  quel ordre), `{ features }` sinon, null si la zone est vide. */
export function patternFeaturesValues(sel, pattern) {
  const names = [...new Set((sel?.items ?? []).map((item) => item.name))];
  if (!names.length) return null;
  const before = new Set(pattern?.features ?? []);
  const same = names.length === before.size
    && names.every((name) => before.has(name));
  return same ? {} : { features: names };
}

/** Sa direction n'est ni un axe d'origine ni une arête de la pièce à son
 *  rang : la zone vide la garde telle quelle. */
const lostDirection = (pattern) => !pattern?.axis
  && !Number.isInteger(pattern?.edge);

/** Rangées de la direction d'une répétition rééditée : axe d'origine ou
 *  arête (remplie de la sienne), et son sens. */
function directionEditRows(pattern) {
  const rows = patternDirectionRows(pattern?.axis ?? "X");
  const edge = pattern?.edge;
  return rows.map((row) => {
    if (row.key === "dirKind") {
      // Une arête qui n'est plus sur la pièce : « Arête », zone vide.
      return { ...row,
               value: Number.isInteger(edge) || lostDirection(pattern)
                 ? "edge" : "axis" };
    }
    if (row.key === "edge" && Number.isInteger(edge)) {
      return { ...row, value: { kind: "edges", edges: [edge] } };
    }
    if (row.key === "reversed") return { ...row, value: !!pattern?.reversed };
    return row;
  });
}

/** Groupes d'une répétition rééditée, autour de ses cotes (`dims`, les
 *  rangées de get_params) : direction et sens, plan d'une symétrie ;
 *  pas ou longueur totale et deuxième direction d'un réseau linéaire. */
export function patternEditGroups(pattern, typeKey, dims = []) {
  if (typeKey === "mirror") {
    return [{ label: "Plan de symétrie", rows: [
      { type: "select", key: "plane", value: pattern?.plane ?? "YZ",
        options: [["YZ", "Plan de droite"], ["XZ", "Plan de face"],
                  ["XY", "Plan de dessus"]] },
    ] }, ...(dims.length ? [{ label: "Paramètres", rows: dims }] : [])];
  }
  const polar = typeKey === "polar_pattern";
  const linear = typeKey === "linear_pattern";
  const groups = [{ label: polar ? "Axe" : "Direction 1", rows: [
    ...directionEditRows(pattern),
    ...(linear ? [patternModeRow(pattern?.mode ?? "extent")] : []),
    ...dims] }];
  if (linear) {
    const two = !!pattern?.dir2;
    groups.push({ label: "Direction 2", rows: [
      { type: "check", key: "dir2", label: "Deuxième direction",
        value: two },
      { type: "select", key: "axis2", value: pattern?.axis2 ?? "Y",
        options: [["X", "Axe X"], ["Y", "Axe Y"], ["Z", "Axe Z"]],
        showIf: (v) => v.dir2 },
      { type: "check", key: "reversed2", label: "Inverser la direction",
        value: !!pattern?.reversed2, showIf: (v) => v.dir2 },
      { type: "number", key: "length2", label: "Distance",
        value: pattern?.length2 ?? 20, unit: "mm", min: 0.01,
        showIf: (v) => v.dir2 },
      { type: "number", key: "count2", label: "Nombre d'occurrences",
        value: pattern?.count2 ?? 2, min: 2, step: 1,
        showIf: (v) => v.dir2 },
    ] });
  }
  return groups;
}

/** Ce qui change dans la direction, le plan et la deuxième direction :
 *  un objet de `set_params` ; null si une arête manque ou si la deuxième
 *  direction est incomplète. */
export function patternEditValues(v, pattern, typeKey) {
  if (typeKey === "mirror") {
    return v.plane && v.plane !== (pattern?.plane ?? "YZ")
      ? { plane: v.plane } : {};
  }
  const values = {};
  if (v.dirKind === "edge") {
    const edge = v.edge?.edges?.[0];
    if (!Number.isInteger(edge)) {
      if (!lostDirection(pattern)) return null;
    } else if (edge !== pattern?.edge) values.edge = edge;
  } else if (v.axis !== pattern?.axis || Number.isInteger(pattern?.edge)) {
    values.axis = v.axis;
  }
  if (!!v.reversed !== !!pattern?.reversed) values.reversed = !!v.reversed;
  if (typeKey !== "linear_pattern") return values;
  if (v.mode && v.mode !== (pattern?.mode ?? "extent")) {
    // La distance change de sens avec le mode : elle part avec lui,
    // telle qu'elle est écrite.
    values.mode = v.mode;
    const length = String(v.length ?? "").trim();
    if (length) values.length = length;
  }
  const two = !!pattern?.dir2;
  if (!v.dir2) {
    if (two) values.dir2 = false;
    return values;
  }
  const length2 = num(v.length2);
  const count2 = parseInt(v.count2, 10);
  if (!(length2 > 0) || !(count2 >= 2)) return null;
  if (!two) {
    return { ...values, dir2: true, axis2: v.axis2 || "Y",
             reversed2: !!v.reversed2, length2, count2 };
  }
  // Une deuxième direction posée sur une arête la garde tant que l'axe
  // de la liste ne change pas.
  if ((v.axis2 || "Y") !== (pattern.axis2 ?? "Y")) values.axis2 = v.axis2 || "Y";
  if (!!v.reversed2 !== !!pattern.reversed2) values.reversed2 = !!v.reversed2;
  if (Math.abs(length2 - pattern.length2) > 1e-9) values.length2 = length2;
  if (count2 !== pattern.count2) values.count2 = count2;
  return values;
}
