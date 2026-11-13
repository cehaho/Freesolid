// Fonctions — nœuds : fonction graphe, réseau variable.

import { minimalGraphCurve, minimalGraphFeature, minimalRepeatGraph } from "../graph.js";

export const NOEUDS = [
  {
    button: "btn-graph-feature",
    op: "add_graph_feature",
    icon: "graph_feature",
    title: "Fonction graphe",
    preview: false,
    groups: () => [{
      label: "Opération",
      rows: [
        { type: "select", key: "mode", value: "fuse",
          options: [
            ["fuse", "Solide — Ajouter"],
            ["cut", "Solide — Soustraire"],
            ["curve", "Courbe ou surface"],
          ] },
      ],
    }],
    note: "La géométrie produite est figée : changer une variable globale "
      + "ne recalcule pas la fonction — il faut la rouvrir et appliquer. "
      + "Le résultat est une forme combinée par un booléen, pas une "
      + "chaîne de fonctions.",
    build: (v) => {
      if (v.mode === "curve") {
        return {
          op: "add_graph_feature",
          params: { graph: minimalGraphCurve() },
        };
      }
      return {
        op: "add_graph_feature",
        params: { graph: minimalGraphFeature(), mode: v.mode },
      };
    },
    refresh: "part",
    openGraphEditor: true,
  },
  {
    button: "btn-repeat-variable",
    op: "add_repeat_feature",
    icon: "variable_pattern",
    title: "Réseau variable",
    preview: false,
    groups: (ctx) => [
      { label: "Fonctions",
        rows: [repeatFeaturesRow(ctx?.selection?.(["feature"]) ?? null)] },
      { label: "Opération",
        rows: [
          { type: "select", key: "mode", value: "fuse",
            options: [["fuse", "Ajouter"], ["cut", "Soustraire"]] },
        ] },
    ],
    note: "Rejoue un groupe de fonctions avec des cotes différentes. "
      + "Si la topologie d'une instance ne correspond plus, la "
      + "répétition s'arrête plutôt que de produire.",
    build: (v) => {
      const items = v.features?.items ?? [];
      if (!items.length) return null;
      return {
        op: "add_repeat_feature",
        params: {
          features: items.map((item) => item.name),
          graph: minimalRepeatGraph(),
          mode: v.mode,
        },
      };
    },
    invalid: "Réseau variable : cliquez au moins une fonction dans l'arbre",
    refresh: "part",
    openGraphEditor: true,
  },
];

/** La zone des fonctions d'une répétition variable : à la création, et à
 *  la réédition, remplie de celles qu'elle répète. */
export function repeatFeaturesRow(value) {
  return { type: "selection", key: "features", accepts: ["feature"],
           multiple: true, value,
           hint: "Cliquez les fonctions dans l'arbre, dans l'ordre du groupe" };
}

/** Les fonctions re-choisies d'une répétition variable : `{}` si ce sont
 *  les mêmes dans le même ordre (le groupe se rejoue dans cet ordre),
 *  `{ features }` sinon, null si la zone est vide. */
export function repeatFeaturesValues(sel, repeat) {
  const names = [...new Set((sel?.items ?? []).map((item) => item.name))];
  if (!names.length) return null;
  const before = repeat?.features ?? [];
  const same = names.length === before.length
    && names.every((name, index) => name === before[index]);
  return same ? {} : { features: names };
}
