// Glisser une fonction dans l'arbre de création : où elle se pose.
//
// Comme dans les modeleurs courants, la ligne survolée passe en
// surbrillance et la fonction se pose juste en dessous. La ligne
// survolée est la dernière ligne d'historique du corps qui commence
// au-dessus du pointeur : une esquisse dépliée sous sa fonction, ou la
// ligne d'un autre corps, compte pour la ligne du corps qui la précède.
// Au-dessus de la première ligne, la fonction passe en tête.

/**
 * @param {number[]} tops haut de chaque ligne d'historique du corps, dans
 *   l'ordre de l'arbre
 * @param {number} own indice de la ligne glissée
 * @param {number} y ordonnée du pointeur
 * @returns {{ hover: number, move: null | { index: number, after: boolean } }}
 *   `hover` : la ligne survolée (-1 : au-dessus de la première) ; `move` :
 *   la ligne d'ancrage et le côté, ou null quand la fonction ne bouge pas.
 */
export function featureDrop(tops, own, y) {
  let hover = -1;
  tops.forEach((top, i) => {
    if (top <= y) hover = i;
  });
  const slot = hover + 1;
  if (!tops.length || slot === own || slot === own + 1) {
    return { hover, move: null };
  }
  return slot < tops.length
    ? { hover, move: { index: slot, after: false } }
    : { hover, move: { index: tops.length - 1, after: true } };
}
