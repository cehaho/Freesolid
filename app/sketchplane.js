// Plan d'une esquisse (menu « Changer de plan… ») : un plan d'origine, un
// plan de référence ou une face de la pièce à son rang. Fonctions pures,
// testées en CI ; le panneau est dans tree.js (editSketchPlane).

/** La liste des plans : ceux de l'origine, les plans de référence, puis
 *  « Face du solide » (la zone de la face apparaît). Pour `sketch`, les
 *  plans de référence qui viennent après elle dans l'arbre n'y sont pas :
 *  une esquisse ne s'appuie pas sur ce qui la suit (son plan actuel
 *  reste). */
export function sketchPlaneOptions(tree, sketch = null) {
  const before = (d) => !sketch || d.name === sketch.support?.datum
    || typeof d.order !== "number" || typeof sketch.order !== "number"
    || d.order < sketch.order;
  const datums = (tree?.features ?? [])
    .filter((f) => f.type_key === "datum_plane" && before(f));
  return [
    ...(tree?.planes ?? []).map((p) => [p.id, p.label]),
    ...datums.map((d) => [`datum:${d.name}`, d.label]),
    ["face", "Face du solide"],
  ];
}

/** Le choix de la liste pour le plan actuel (`support` de l'arbre). */
export function sketchPlaneChoice(support) {
  if (support?.plane) return support.plane;
  if (support?.datum) return `datum:${support.datum}`;
  if (support && "face" in support) return "face";
  return "XY";
}

/** Le plan choisi dans la liste : `{}` s'il n'a pas changé, ou si c'est
 *  une face (la zone la donne) ; `{ plane }` ou `{ datum }` sinon. */
export function sketchPlaneValues(v, support) {
  const choice = String(v.support ?? "");
  if (choice === "face" || choice === sketchPlaneChoice(support)) return {};
  if (choice.startsWith("datum:")) return { datum: choice.slice(6) };
  return { plane: choice };
}

/** La face d'accueil : `{}` hors « Face du solide » ou si c'est la sienne,
 *  `{ face }` sinon, null si la zone est vide. */
export function sketchFaceValues(v, support) {
  if (v.support !== "face") return {};
  const face = v.face?.face;
  if (!Number.isInteger(face)) return null;
  return face === support?.face ? {} : { face };
}
