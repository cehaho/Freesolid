// Registry déclaratif des panneaux de fonctions mécaniques.
// Le branchement (clic → featureCommand → panel.open) vit dans main.js.
//
// Chaque entrée décrit un panneau « ouvrir → éditer → aperçu → OK ».
// build(v, ctx) rend { op, params } ou null (aperçu éteint, OK bloqué).
//
// Les entrées et leurs aides vivent par famille dans features/ : ce
// fichier les rassemble dans le même ordre et ré-exporte les aides
// publiques (des plugins importent dressup et hasSelection d'ici).

import { VOLUMES } from "./features/volumes.js";
import { HABILLAGE } from "./features/habillage.js";
import { REPETITIONS } from "./features/repetitions.js";
import { COMBINER } from "./features/combiner.js";
import { SURFACES } from "./features/surfaces.js";
import { NOEUDS } from "./features/noeuds.js";

export {
  availableSketches,
  bodyZoneRow,
  dressup,
  hasSelection,
  NO_SKETCH_AVAILABLE,
  resolveProfileSketch,
} from "./features/commun.js";
export {
  bodyChoiceGroups,
  bodyChoiceValues,
  checkedContours,
  contourLabel,
  contourRows,
  cutGroups,
  cutParams,
  extrudeBuild,
  extrudeEditInitial,
  extrudeEditProblem,
  extrudeEditValues,
  extrudeGroups,
  extrudeInvalid,
  extrudeMergeProblem,
  holeEditInitial,
  holeEditValues,
  holeGroups,
  holePositionValues,
  holePositions,
  holePositionsPick,
  holePositionsRow,
  holeSamePosition,
  mergeGroups,
  mergeParams,
  mergeProblem,
  revolutionAxisOptions,
  revolutionCreationParams,
  revolutionEditValues,
  revolutionGroups,
  revolutionProblem,
  textEditValues,
  textRows,
} from "./features/volumes.js";
export {
  chamferCreationParams,
  chamferEditValues,
  chamferFieldValue,
  chamferProblem,
  chamferRows,
  draftEditGroups,
  draftEditValues,
  dressupPick,
  dressupPickValues,
  filletEditRows,
  filletEditValues,
  shellBuild,
  shellEditGroups,
  shellEditValues,
  shellFacesPick,
  shellFacesValues,
  vertexChamferDistances,
  vertexChamferEditValues,
  vertexChamferPick,
  vertexChamferPointValues,
  vertexChamferRow,
  vertexChamferRows,
} from "./features/habillage.js";
export {
  BODY_PATTERN_TYPES,
  linearSecondDirection,
  patternDirectionParams,
  patternDirectionRows,
  patternEditGroups,
  patternEditValues,
  patternFeaturesGroup,
  patternFeaturesParams,
  patternFeaturesPick,
  patternFeaturesValues,
  patternSourcesPick,
  patternSourcesValues,
} from "./features/repetitions.js";
export {
  REMOVE_BODIES_NOTE, removalCandidates, removalItem, removalMatch,
  removeBodiesGroups, removeBodiesParams,
  COMBINE_TYPES, combineEditOptions, combineEditValues,
} from "./features/combiner.js";
export {
  boundaryParam,
  cutOptionValues,
  deleteFacesBuild,
  deleteFacesParams,
  extendParams,
  extendPick,
  extendTargetValues,
  filletEdgesPick,
  filletEdgesValues,
  freeformEditValues,
  freeformParams,
  intersectionEditValues,
  midParams,
  ownSketchPick,
  planarEditValues,
  projectEditValues,
  projectTargetPick,
  radiateBoundaryPick,
  radiateBoundaryValues,
  signedEditValues,
  sourceEditValues,
  surfaceCutParams,
  surfaceFilletParams,
  surfacePick,
  trimEditValues,
  trimKeepPick,
  trimParams,
} from "./features/surfaces.js";

export const FEATURES = [
  ...VOLUMES,
  ...HABILLAGE,
  ...REPETITIONS,
  ...COMBINER,
  ...SURFACES,
  ...NOEUDS,
];
