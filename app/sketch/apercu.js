// Esquisse : l'aperçu d'un tracé en cours.

/** Pose `points` dans le trait `line`. Une géométrie neuve à chaque fois :
 *  three (depuis la 0.163) réécrit le tampon en place et ne l'agrandit
 *  pas — un arc, plus long que la ligne d'avant, ne se dessinait plus. */
export function setLinePoints(line, points) {
  const old = line.geometry;
  line.geometry = new old.constructor().setFromPoints(points);
  old.dispose();
}
