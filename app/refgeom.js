// Géométrie de référence : axes, points et repères — les panneaux de
// création et leur dessin dans la vue (les plans de référence, eux, se
// montrent au survol de l'arbre).

import { t } from "./i18n.js";
import { num } from "./num.js";

const KINDS = {
  datum_axis: "axis",
  datum_point: "point",
  datum_cs: "cs",
};

/** Icône de chaque genre, à la création comme à la réédition. */
export const REFERENCE_ICONS = { plane: "PartDesign_Plane",
  axis: "datum_axis", point: "datum_point", cs: "datum_cs" };

/** Axes, points et repères à dessiner : placés, pas derrière la barre de
 *  retour. */
export function referenceItems(tree) {
  const out = [];
  const visit = (items) => {
    for (const item of items ?? []) {
      if (KINDS[item.type_key] && item.placement && !item.rolled_back) {
        out.push({ ...item, shape: KINDS[item.type_key] });
      }
      visit(item.children);
    }
  };
  visit(tree?.features);
  return out;
}

/** Groupes du panneau d'un plan de référence, à la création comme à la
 *  réédition : sa face (zone vide : un plan d'origine), son décalage, son
 *  angle. `face` : la valeur de la zone. */
export function datumPlaneGroups({ face = null, base = "XY", offset = 20,
  angle = 0 } = {}) {
  return [
    { label: "Référence", rows: [
      { type: "selection", key: "sel", accepts: ["face"],
        hint: "Cliquez une face — ou choisissez un plan ci-dessous",
        value: face },
      // Choisir un plan d'origine vide la zone : la face ne l'emporte plus.
      { type: "select", key: "base", value: base, label: "Plan",
        clears: "sel",
        options: [["XZ", "Plan de face"], ["XY", "Plan de dessus"],
                  ["YZ", "Plan de droite"]] },
    ] },
    { label: "Position", rows: [
      { type: "number", key: "offset", label: "Décalage", value: offset,
        unit: "mm" },
      { type: "number", key: "angle", label: "Angle", value: angle,
        unit: "°" },
    ] },
  ];
}

/** Panneau d'un plan de référence → { op, params } de sa création. */
export function datumPlaneBuild(v) {
  const params = {
    offset: num(v.offset) ?? 0,
    angle: num(v.angle) ?? 0,
  };
  if (v.sel && v.sel.face != null) params.face = v.sel.face;
  else params.base = v.base;
  return { op: "add_datum_plane", params };
}

/** Valeurs du panneau d'un plan réédité (`spec` : sa ligne `reference`
 *  de l'arbre) : ce qui le porte, son décalage, son angle. Posé sur une
 *  face, la liste des plans d'origine vient vide : rien n'y est choisi.
 *  ⚠ Moteur : `_set_reference_params` (engine/refgeom.py). */
export function datumPlaneSpecValues(spec) {
  return {
    face: Number.isInteger(spec?.face) ? { kind: "face", face: spec.face } : null,
    base: spec?.base ?? "",
    offset: spec?.offset ?? 0,
    angle: spec?.angle ?? 0,
  };
}

/** Ce qui change à la réédition d'un plan : `{}` si rien, les clés qui
 *  changent sinon ; null si une cote n'est pas un nombre. Un plan
 *  d'origine choisi dans la liste (qui vide la zone) le pose dessus ; une
 *  face disparue au rang laisse la zone vide et la liste sans choix : le
 *  plan reste où il est. */
export function datumPlaneEditValues(v, spec) {
  const offset = num(v.offset);
  const angle = num(v.angle);
  if (offset === null || angle === null) return null;
  const out = {};
  if (v.sel?.face != null) {
    if (v.sel.face !== spec.face) out.face = v.sel.face;
  } else if (v.base && v.base !== spec.base) {
    out.base = v.base;
  }
  if (offset !== spec.offset) out.offset = offset;
  if (angle !== spec.angle) out.angle = angle;
  return out;
}

/** Groupe du panneau d'un axe, d'un point ou d'un repère, à la création
 *  comme à la réédition : ce qui le porte (`by`), l'arête, le sommet ou
 *  les coordonnées. */
export function referenceGroups(kind, { by, edge = null, vertex = null,
  point = [0, 0, 0] } = {}) {
  const isAxis = kind === "axis";
  const byOptions = isAxis
    ? [["X", "Axe X de l'origine"], ["Y", "Axe Y de l'origine"],
       ["Z", "Axe Z de l'origine"], ["edge", "Arête du solide"]]
    : [["vertex", "Sommet cliqué"],
       ...(kind === "point" ? [["center", "Centre d'une arête circulaire"]] : []),
       ["xyz", "Coordonnées"]];
  return [{ label: "Référence", rows: [
    { type: "select", key: "by", options: byOptions,
      value: by ?? (isAxis ? (edge ? "edge" : "Z") : "vertex") },
    { type: "selection", key: "edge", accepts: ["edges"], value: edge,
      hint: isAxis ? "Cliquez une arête droite ou circulaire"
        : "Cliquez une arête circulaire",
      showIf: (v) => v.by === "edge" || v.by === "center" },
    { type: "selection", key: "vertex", accepts: ["vertex"], value: vertex,
      hint: "Cliquez près d'un coin de la pièce",
      showIf: (v) => v.by === "vertex" },
    ...["x", "y", "z"].map((axis, i) => ({
      type: "number", key: axis, label: axis.toUpperCase(), value: point[i],
      unit: "mm", showIf: (v) => v.by === "xyz" })),
  ] }];
}

/** Valeurs du panneau d'un axe, d'un point ou d'un repère réédité
 *  (`spec` : sa ligne `reference` de l'arbre). */
export function referenceSpecValues(spec) {
  const edge = Number.isInteger(spec?.edge)
    ? { kind: "edges", edges: [spec.edge] } : null;
  if (spec?.kind === "axis") {
    return { by: spec.axis ?? "edge", edge };
  }
  if (Array.isArray(spec?.vertex)) {
    const [x, y, z] = spec.vertex;
    return { by: "vertex", vertex: { kind: "vertex", x, y, z } };
  }
  if ("edge" in (spec ?? {})) return { by: "center", edge };
  return { by: "xyz", point: spec?.point ?? [0, 0, 0] };
}

/** Ce qui change à la réédition d'un axe, d'un point ou d'un repère : `{}`
 *  si c'est le même appui, `{ clé: valeur }` sinon, null s'il manque le
 *  choix. */
export function referenceEditValues(kind, v, spec) {
  const built = referenceBuild(kind, v);
  if (!built) return null;
  const [[key, value]] = Object.entries(built.params);
  const was = spec?.[key];
  const same = Array.isArray(value)
    ? Array.isArray(was) && value.every((c, i) => Math.abs(c - was[i]) < 1e-9)
    : value === was;
  return same ? {} : { [key]: value };
}

/** Paramètres d'un panneau → { op, params }, ou null s'il manque le choix. */
export function referenceBuild(kind, v) {
  if (kind === "axis") {
    if (v.by !== "edge") return { op: "add_datum_axis", params: { axis: v.by } };
    const edge = v.edge?.edges?.[0];
    return edge == null ? null : { op: "add_datum_axis", params: { edge } };
  }
  const op = kind === "point" ? "add_datum_point" : "add_datum_cs";
  if (v.by === "vertex") {
    return v.vertex?.kind === "vertex"
      ? { op, params: { vertex: [v.vertex.x, v.vertex.y, v.vertex.z] } } : null;
  }
  if (v.by === "center") {
    const edge = v.edge?.edges?.[0];
    return edge == null ? null : { op, params: { edge } };
  }
  const point = [num(v.x), num(v.y), num(v.z)];
  return point.every(Number.isFinite) ? { op, params: { point } } : null;
}

export function installRefGeometry(ctx) {
  const { THREE, scene, sceneTheme } = ctx;
  let group = null;

  function clear() {
    if (!group) return;
    group.traverse((obj) => {
      obj.geometry?.dispose();
      obj.material?.dispose();
    });
    scene.remove(group);
    group = null;
  }

  function line(points, color, dashed = false) {
    const geometry = new THREE.BufferGeometry().setFromPoints(
      points.map((p) => new THREE.Vector3(...p)));
    const material = dashed
      ? new THREE.LineDashedMaterial({ color, dashSize: 3, gapSize: 2 })
      : new THREE.LineBasicMaterial({ color });
    const segment = new THREE.Line(geometry, material);
    if (dashed) segment.computeLineDistances();
    return segment;
  }

  /** Redessine les axes, points et repères de l'arbre. */
  function draw(tree) {
    clear();
    const items = referenceItems(tree);
    // Créés par l'utilisateur : toujours visibles (la case « Plans de
    // référence » ne vise que les trois plans d'origine).
    if (!items.length) return;
    const { radius } = ctx.partCenterRadius();
    const reach = Math.max(radius * 1.2, 40);
    group = new THREE.Group();
    group.name = "reference-geometry";
    for (const item of items) {
      const holder = new THREE.Group();
      holder.matrixAutoUpdate = false;
      holder.matrix.set(...item.placement);
      if (item.shape === "axis") {
        // Un axe court le long de son Z local.
        holder.add(line([[0, 0, -reach], [0, 0, reach]], sceneTheme.accent, true));
      } else if (item.shape === "point") {
        const geometry = new THREE.BufferGeometry().setFromPoints(
          [new THREE.Vector3()]);
        holder.add(new THREE.Points(geometry, new THREE.PointsMaterial(
          { color: sceneTheme.accent, size: 9, sizeAttenuation: false })));
      } else {
        const size = reach / 3;
        holder.add(line([[0, 0, 0], [size, 0, 0]], 0xd9534f),
          line([[0, 0, 0], [0, size, 0]], 0x5cb85c),
          line([[0, 0, 0], [0, 0, size]], 0x4a90d9));
      }
      group.add(holder);
    }
    scene.add(group);
  }

  function open(kind) {
    const edges = ctx.currentSelection(["edges"]);
    const titles = { axis: "Axe de référence", point: "Point de référence",
                     cs: "Repère" };
    ctx.featureCommand(() => ctx.panel.open({
      icon: REFERENCE_ICONS[kind],
      title: t(titles[kind]),
      groups: referenceGroups(kind, { edge: edges }),
      onApply: (v) => {
        const built = referenceBuild(kind, v);
        if (!built) {
          ctx.say(t("Choisissez d'abord ce qui porte l'élément"), true);
          return;
        }
        ctx.refresh(ctx.call(built.op, built.params));
      },
    }));
  }

  for (const [id, kind] of [["btn-datum-axis", "axis"],
    ["btn-datum-point", "point"], ["btn-datum-cs", "cs"]]) {
    document.getElementById(id)?.addEventListener("click", () => open(kind));
  }

  return { draw };
}
