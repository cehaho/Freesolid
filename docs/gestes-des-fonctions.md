# Gestes des fonctions

Cette grille sert à repérer où les fonctions ne se comportent pas pareil. Pour chacune, elle dit si l'on peut rééditer après coup ce qu'on a choisi à la création, et si les gestes (aperçu, double-clic, menu « Modifier », barre de retour) sont les mêmes d'une fonction à l'autre.

État décrit : 2026-11-02, après #151 (« Modifier » au menu suit le double-clic), #153 (« Désactiver » suit le moteur) et la réédition des options de création (Extrusion, Enlèvement, Coque, Perçage, surfaces décalée et radiée). La grille vient de la lecture du code et des selftests, contrôlée par un relevé : ce que l'arbre dit de chaque ligne fabriquée par le selftest (`has_params`, 51 genres), et quelques gestes rejoués dans le navigateur. Ce qui n'a pas été tranché est marqué « à vérifier ».

Tenir la grille à jour : une fonction ajoutée ou corrigée met sa ligne à jour dans le même changement (et, si un écart disparaît ou apparaît, la section « Écarts, par thème »). Les références vont au fichier et à la fonction, jamais à une ligne. « Écart n° N » renvoie au tableau de `docs/ecarts-solidworks.md`.

## Légende des colonnes

- **Aperçu à la création** : le fantôme jaune pendant que le panneau est ouvert. « oui + flèche » : la flèche de profondeur dans la vue en plus.
- **Réédition : ce qui revient** : ce que le double-clic (ou « Modifier ») permet de changer.
- **Ne revient pas** : ce qui a été choisi à la création et qu'on ne peut plus changer sans supprimer et refaire.
- **Aperçu à la réédition** : le fantôme jaune pendant la réédition. « — » : rien à rééditer.
- **Barre de retour** : la fonction se pose sur la barre et recule avec elle. « oui (drapeau) » : surface ou esquisse libre, qui se masque par drapeau au lieu de passer par le Tip du corps.
- **Selftest de réédition** : un test de bout en bout de `engine/selftest/` réédite la fonction. « non » : aucun trouvé.

« Modifier » au menu n'est pas une colonne : depuis #151, il est proposé exactement quand le double-clic rouvre quelque chose (`app/editkind.js`), donc quand la colonne « Réédition » dit autre chose que « rien ». « Désactiver » et « Masquer » non plus : leurs écarts sont dans la section des écarts, car ils tiennent à des règles du menu et non à la fonction.

## Volumes

| Fonction | Aperçu à la création | Réédition : ce qui revient | Ne revient pas | Aperçu à la réédition | Barre de retour | Selftest de réédition |
|---|---|---|---|---|---|---|
| Extrusion | oui + flèche | le panneau de la création, sur la pièce au rang quand un « jusqu'à » peut l'arrêter : condition de fin (borgne seulement pour le premier volume d'un corps), face d'arrivée (cliquée sur la pièce au rang), décalage, inverser, dépouille, direction 2 (condition, profondeur, dépouille), épaisseurs et côté de la paroi mince, contours, « Fusionner », corps fondus et corps de la fonction (une zone : clic ou cadre dans la vue, clic dans le dossier, croix pour retirer) | activer la paroi mince ou en changer le genre (le plan de l'esquisse se re-choisit au rang : clic droit, « Changer de plan… ») | oui + flèche (la flèche s'efface quand le sens ou la condition change) | oui | oui (conditions, face d'arrivée, direction 2, paroi mince, extrémités fermées, « Fusionner », corps fondus, corps de la fonction) |
| Enlèvement extrudé | oui + flèche | comme l'Extrusion, les corps creusés au lieu des corps fondus (une zone : clic ou cadre dans la vue, clic dans le dossier, croix pour retirer) | comme l'Extrusion | oui + flèche | oui | oui (à travers tout, borgne, refus de « jusqu'à la face », corps creusés qui suivent la cote, corps creusés ajoutés ou retirés) |
| Révolution | oui | angle, axe, inverser, plan médian, contours, « Fusionner », corps fondus et corps de la fonction ; plan de l'esquisse (« Changer de plan… ») | — | oui | oui | oui (axe, plan médian, « Fusionner », corps fondus) |
| Enlèvement de révolution | oui | comme la Révolution, les corps creusés au lieu des corps fondus | comme la Révolution | oui | oui | non (seule la Révolution est testée) |
| Perçage | oui | le panneau de la création : positions et face (posé par des clics), type (simple, lamage, fraisage), cotes du type, angle du fraisage, à travers ou borgne, profondeur, corps creusés (une zone : clic ou cadre dans la vue, clic dans le dossier, croix pour retirer) | — | oui | oui | oui (type, condition de fin, corps creusés, positions) |
| Lissage | oui | le panneau de la création, au rang : profils et leur ordre (un clic dans l'arbre retire une esquisse de la zone ou l'ajoute au bout ; celle d'un autre corps entre par un liant caché), lissage droit, boucle fermée ; « Fusionner » (décochée, il sort de son corps ; ses profils y entrent par des liants) ; quand la pièce a d'autres corps, les corps fondus, ou creusés pour l'enlèvement lissé (une zone : clic ou cadre dans la vue, clic dans le dossier, croix pour retirer) | soustractif | oui | oui | oui (profils retirés, réordonnés, d'un autre corps, lissage droit, « Fusionner » décochée puis recochée, zone d'action, corps fondus ajoutés puis retirés) |
| Balayage | oui | le panneau de la création, au rang : profil et trajectoire (une esquisse ou une courbe 3D), et comme le Lissage : « Fusionner » (profil d'un seul tenant pour sortir de son corps), les corps fondus, ou creusés pour l'enlèvement balayé | soustractif | oui | oui | oui (profil, trajectoire sur une esquisse ou une courbe 3D, « Fusionner » décochée sur une esquisse et sur une courbe 3D, profil en deux morceaux refusé, corps creusés ajoutés, Ctrl+Z et Ctrl+Y) |
| Hélice | oui | pas, hauteur, angle ; plan de l'esquisse (« Changer de plan… ») | — | oui | oui | non |
| Texte | oui | le panneau de la création : texte, hauteur, profondeur, décalage, face d'appui | relief ou gravure, police | oui | oui | oui |

## Habillage, Combiner et références

| Fonction | Aperçu à la création | Réédition : ce qui revient | Ne revient pas | Aperçu à la réédition | Barre de retour | Selftest de réédition |
|---|---|---|---|---|---|---|
| Congé | oui + bulle de rayon | rayon ; arêtes ou face, re-choisies sur la pièce à son rang | — | oui, sans la bulle | oui | oui (rayon, arêtes) |
| Chanfrein | oui | type, taille, taille 2, angle, sens ; arêtes ou face, re-choisies sur la pièce à son rang | — | oui | oui | oui |
| Chanfrein de sommet | oui | le panneau de la création : sommet, distances | — | oui | à vérifier (booléen, jusqu'à deux lignes) | oui |
| Coque | oui | épaisseur, « vers l'extérieur » ; faces à ouvrir, re-choisies sur la pièce à son rang | — | oui | oui | oui (sens, refus d'une coque trop épaisse, faces) |
| Dépouille | oui | angle, plan neutre ; face, re-choisie sur la pièce à son rang | — | oui | oui | oui (face, plan neutre) |
| Combiner | non, voulu | le panneau de la création, au rang (le corps outil y reparaît) : opération, corps outil (venu d'un module : l'opération seule) | — | non, voulu | oui | oui (opération, corps outil, refus) |
| Supprimer des corps | non | complète : corps, solides ou surfaces choisis (une zone : clic ou cadre dans la vue, clic dans le dossier, croix pour retirer), ôter ou garder | rien | non | oui (drapeau) | oui |
| Plan de référence | oui + fantôme | rien | appui, décalage, angle | — | non (d'après le code, à vérifier) | non |
| Axe de référence | non | rien | tout | — | non (d'après le code, à vérifier) | non |
| Point de référence | non | rien | tout | — | non (d'après le code, à vérifier) | non |
| Repère | non | rien | tout | — | non (d'après le code, à vérifier) | non |

## Répétitions et graphe

| Fonction | Aperçu à la création | Réédition : ce qui revient | Ne revient pas | Aperçu à la réédition | Barre de retour | Selftest de réédition |
|---|---|---|---|---|---|---|
| Répétition linéaire, des fonctions | oui | le panneau de la création : fonctions répétées, direction (axe ou arête), inverser, pas ou longueur totale, distance, nombre, direction 2 (l'activer, la retirer, son axe, son sens, sa distance, son nombre) ; corps creusés, quand elle répète un enlèvement | — | oui, sans la flèche | oui | oui (nombre, corps creusés, fonctions, direction, pas ou longueur totale, direction 2) |
| Répétition linéaire, des corps | oui | le panneau de la création, au rang : corps répétés (une zone : clic dans la vue ou le dossier, croix pour retirer), direction (axe ou arête), inverser, pas ou longueur totale, distance, nombre, direction 2 (l'activer, la retirer, son axe, son sens, sa distance, son nombre) | copies sautées | oui (les copies) | oui | oui (nombre, distance, corps, direction, mode, direction 2) |
| Répétition circulaire, des fonctions | oui | le panneau de la création : fonctions répétées, axe (d'origine ou arête), inverser, angle total, nombre ; corps creusés, quand elle répète un enlèvement | — | oui | oui | non |
| Répétition circulaire, des corps | oui | le panneau de la création, au rang : corps répétés, axe (d'origine ou arête), inverser, angle total, nombre | copies sautées | oui (les copies) | oui | oui (axe) |
| Symétrie, des fonctions | oui | fonctions, plan ; corps creusés, quand elle répète un enlèvement | — | oui | oui | oui (corps creusés, plan) |
| Symétrie, des corps | oui | le panneau de la création, au rang : corps répétés, plan | copie sautée | oui (la copie) | oui | oui (plan) |
| Fonction graphe, solide (ajout, enlèvement) | non | le graphe, dans l'éditeur de graphe | ajout ou enlèvement, nature solide ou courbe | non | oui | oui |
| Fonction graphe, courbe ou surface | non | le graphe, dans l'éditeur de graphe | nature courbe ou surface | non | oui (drapeau) | oui |
| Répétition variable | non | nombre d'instances et graphe, dans l'éditeur de graphe ; fonctions répétées, au rang (bouton « Fonctions » de l'éditeur) | ajout ou enlèvement | non | oui | oui (instances, fonctions) |

## Surfaces

| Fonction | Aperçu à la création | Réédition : ce qui revient | Ne revient pas | Aperçu à la réédition | Barre de retour | Selftest de réédition |
|---|---|---|---|---|---|---|
| Surface extrudée | non | longueur ; plan de l'esquisse (« Changer de plan… ») | sens | à vérifier | oui (drapeau) | oui |
| Surface de révolution | non | angle ; plan de l'esquisse (« Changer de plan… ») | axe, sens | à vérifier | oui (drapeau) | non |
| Surface lissée | non | le panneau de la création, au rang : profils, dans l'ordre (un clic dans l'arbre en retire un ou l'ajoute au bout) | — | oui | oui (drapeau) | oui (profils, refus d'un seul ou d'un doublon) |
| Surface cousue | non | rien (forme figée) | tout : liste des surfaces | — | oui (drapeau) | non |
| Épaissir | non | le panneau de la création, au rang : surface (clic dans l'arbre), épaisseur (signée) | — | oui | oui (drapeau) | oui (surface, épaisseur) |
| Couper avec une surface | oui | le panneau de la création, au rang : surface outil (clic dans l'arbre), inverser le côté, tout un côté ou une bande épaisse, épaisseur | — | oui | oui | oui (surface outil, bande, retour à tout un côté, refus) |
| Surface plane | non | le panneau de la création, au rang : esquisse du contour | — | oui | oui (drapeau) | oui (esquisse, refus d'une esquisse d'après) |
| Surface balayée | non | le panneau de la création, au rang : profil, trajectoire (esquisse ou courbe 3D) | — | oui | oui (drapeau) | oui (trajectoire, refus du profil comme trajectoire) |
| Surface décalée | non | le panneau de la création, au rang : surface (clic dans l'arbre), distance et « inverser le côté » | — | oui | oui (drapeau) | oui (surface, refus d'elle-même et d'une surface d'après) |
| Surface de remplissage | non | le panneau de la création, au rang : contour (un bouchon tangent se refait sur les faces que bordent les nouvelles arêtes) | case « tangent » | oui | oui (drapeau) | oui (contour, arête fermée, bouchon tangent) |
| Surface frontière | non | le panneau de la création, au rang : 2 à 4 courbes | — | oui | oui (drapeau) | oui (courbes) |
| Surface radiée | non | le panneau de la création, au rang : contour plan, distance et « vers l'intérieur » (pilotée par une équation : la distance signée, dans le panneau des cotes) | — | oui | oui (drapeau) | oui (contour, refus d'une forme d'après) |
| Surface médiane | non, voulu | rien (forme figée) | tout : les deux faces ou toutes les parois, épaisseur | — | oui (drapeau) | non |
| Surface réglée | non | le panneau de la création, au rang : les deux courbes | — | oui | oui (drapeau) | oui (courbes, refus de trois) |

## Opérations sur surfaces et courbes

| Fonction | Aperçu à la création | Réédition : ce qui revient | Ne revient pas | Aperçu à la réédition | Barre de retour | Selftest de réédition |
|---|---|---|---|---|---|---|
| Diviser | non | le panneau de la création, au rang : surface, courbe outil | — | oui | oui (drapeau) | oui (courbe, refus d'une courbe qui ne scinde pas) |
| Remplacer la face (solide) | oui | rien | face, surface de remplacement | — | oui (Tip du corps) | non |
| Supprimer la face (solide) | oui | rien | liste de faces | — | oui (Tip du corps) | non |
| Supprimer la face (surface) | oui | le panneau de la création, au rang : faces d'une même surface (une autre surface la change) | — | oui | oui (drapeau) | oui (faces, refus de toutes) |
| Annuler l'ajustement | non | le panneau de la création, au rang : face de surface (une autre surface aussi) | — | oui | oui (drapeau) | oui (autre surface, refus d'une face inconnue) |
| Congé de surfaces | non | le panneau de la création, au rang : arêtes (d'une même surface, qui peut changer), rayon (un pour toutes, comme à la création) | — | oui | oui (drapeau) | oui (rayon, arêtes, autre surface) |
| Aplatir | non | le panneau de la création, au rang : face de surface (un clic sur une autre la remplace, sur une autre surface aussi) ; la déformation mesurée | — | oui | oui (drapeau) | oui (surface, face) |
| Forme libre | non | le panneau de la création, au rang : surface (clic dans l'arbre ; les points poussés s'y reprojettent), points poussés, hauteurs, rayon, bords fixes | — | oui | oui (drapeau) | oui (surface, rayon) |
| Pôles | surcouche dans la vue | surface (clic dans l'arbre ; les pôles déplacés gardent leurs indices), déplacements, pas de grille ; une autre face, en cliquant ses pôles | — | non | oui (drapeau) | oui (surface) |
| Prolonger | non | le panneau de la création, au rang : bord (ou la surface entière, pour tous ses bords ; un bord d'une autre surface la change), distance | — | oui | oui (drapeau) | oui (tous les bords, un bord, autre surface) |
| Ajuster | non | le panneau de la création, au rang : outil, surface ajustée et partie gardée (un clic dessus) | ajustement mutuel (deux lignes : chacune se réédite seule) | oui | oui (drapeau) | oui (outil, partie gardée, autre surface, refus) |
| Courbe d'intersection | non | le panneau de la création, au rang : les deux surfaces, ou une surface et le solide (« avec le solide ») | — | non (une courbe n'a pas de fantôme) | oui (drapeau) | oui (seconde surface, solide, refus) |
| Projeter une courbe | non | le panneau de la création, au rang : esquisse, face cible (la direction suit la normale de l'esquisse) | — | non (une courbe n'a pas de fantôme) | oui (drapeau) | oui (esquisse, surface, refus) |
| Hélice 3D | non | pas, hauteur, rayon, angle | axe, sens | non | oui (drapeau) | oui (pas) |
| Courbe composite | non | le panneau de la création, au rang : courbes et arêtes, bout à bout | — | non (une courbe n'a pas de fantôme) | oui (drapeau) | oui (arêtes, refus d'arêtes qui ne se suivent pas) |
| Spline 3D | surcouche dans la vue | complète : points, type, fermée, liens, tangentes | rien | non | oui (drapeau) | oui |
| Esquisse 3D | à vérifier | complète | rien | non | oui (drapeau) | oui |

## Écarts, par thème

Du plus visible pour un utilisateur au moins visible.

### 1. Le menu « Modifier » et le double-clic se contredisaient

Corrigé par #151. Le menu proposait « Modifier » sur une vingtaine de fonctions sans réédition (Lissage, Balayage, Combiner, Symétrie, références, surfaces lissée, plane, balayée…), où le geste ne menait qu'au message « aucun paramètre numérique éditable ». Il le cachait sur des surfaces que le double-clic réédite (Forme libre, Pôles, Spline 3D, Esquisse 3D, Aplatir). Le menu de la vue 3D le proposait pour toute surface, figée ou non.

Maintenant le moteur dit dans l'arbre si une fonction a des cotes (`has_params`), et `app/editkind.js` répond, pour une ligne, quel éditeur le double-clic rouvre, ou aucun. Le double-clic, le menu de l'arbre et celui de la vue lisent cette même réponse.

Le relevé a trouvé en chemin trois fausses cotes : la `Length` du plan et de l'axe de référence (une taille d'affichage) et la `Height` de la projection (sans effet en mode « Edges »). Le double-clic ouvrait pour elles un panneau sans effet. Elles ne sont plus des cotes (`engine/equations.py`, `_NO_DIMENSIONS`).

Et une ligne qu'une répétition à corps concernés creuse dans un autre corps rouvre cette répétition : creusée par une symétrie, elle proposait « Modifier » pour rien. L'arbre dit maintenant si la répétition rouverte a des cotes (`edits_has_params`). Une répétition neuve creuse les autres corps par des étapes cachées : ces lignes ne restent que dans les fichiers d'avant. Elle-même rouvre sa zone « Corps concernés » (`cut` dans l'arbre, même vide) : une symétrie d'enlèvements, sans cote, se réédite pour eux.

Reste : le menu de la vue 3D n'a ni Masquer ni Supprimer, que le menu de l'arbre a.

Où ça se décide : `app/editkind.js` ; `engine/equations.py` (`_has_params`, `_editable_props`) ; `app/contextmenu.js` (`canModifyMenuTarget`) ; `app/viewmenu.js`.

### 2. Désactiver et Masquer : les règles ne suivaient pas les fonctions

- **Désactiver proposé, refusé par le moteur** : Axe, Point et Repère de référence, Courbe composite et Supprimer la face d'une surface. Le menu n'excluait que le Plan, alors que le moteur ne désactive que les objets qui portent la propriété `Suppressed` (message « seule une fonction de volume se désactive »), et qu'aucun de ces genres (`PartDesign::Line`, `Point`, `CoordinateSystem`, `SubShapeBinder`) ne la porte dans FreeCAD 1.1.3. Corrigé par #153 : l'arbre dit si une ligne se désactive (`suppressible`), le menu le suit. Une ligne qu'une répétition creuse dans un autre corps ne se désactive pas seule : on désactive la répétition.
- **Objets cachés d'une fonction** : ils se désactivent avec elle. La cavité d'une paroi mince fermée restait active et creusait le corps (une paroi tournée vers la matière y laissait son vide) ; le combiner caché d'un volume qui fond plusieurs corps les rend quand on le désactive. Corrigé par la fusion de plusieurs corps (`set_suppressed`).
- **Ce qui ne se désactive pas** : tout ce qui n'est pas une fonction de corps PartDesign. Les surfaces (y compris Épaissir, dont le résultat est un solide), les références, le réseau de corps, la Suppression de corps. Les modeleurs courants désactivent tout : il faudrait un mécanisme à FreeSolid, comme le drapeau qui fait reculer les surfaces avec la barre de retour.
- **Fonctions graphe, Répétition variable, Texte** : le menu propose « Désactiver » quand le moteur l'accepte ; l'effet sur la pièce reste à vérifier (le corps outil caché du Texte, par exemple).
- **Masquer** : il manquait à la Courbe composite et à Supprimer la face d'une surface, dont le genre (`binder`) n'était pas dans la liste des surfaces. Corrigé par #151 : toute ligne du dossier des surfaces se masque. Les fonctions de corps ne se masquent pas (seuls les corps et les surfaces du premier niveau).

Où ça se décide :

- `engine/tree.py` (`entry`) et `engine/surfacefeat/commun.py` (`_surface_tree_entry`) : le champ `suppressible` ;
- `engine/docprops.py`, `_is_suppressible` (la règle), `set_suppressed` et `set_hidden` ;
- `app/contextmenu.js`, `isSuppressibleTarget`, `isHideableTarget` et `openMenu` ;
- `app/typekeys.js` : la liste des genres, pour une ligne de plugin sans l'avis du moteur.

### 3. Fonctions sans aucune réédition

Un choix de création est définitif : il faut supprimer et refaire.

- **Références** : Axe, Point, Repère, Plan de référence.
- **Surfaces figées sans réédition** : cousue, médiane. Le moteur les recalcule déjà avec leurs sources (il garde ce qu'il faut sur chaque forme) : un panneau de réédition est possible, comme pour la Forme libre.
- **Opérations** : Remplacer et Supprimer la face du solide.

Corrigé pour les surfaces lissée, balayée, frontière, réglée, de remplissage (le bouchon tangent compris), Diviser, Annuler l'ajustement, Supprimer la face d'une surface et la Courbe composite : leur double-clic rouvre le panneau de la création (thème 4).

Une même fonction change de comportement selon un choix : le Remplissage est paramétrique sans tangence, figé avec. Le choix « tangent » change la rééditabilité sans le dire.

Où ça se décide : `app/tree.js`, `editSurface` (aiguille par genre de surface) et `editFeature` (branches dédiées : Révolution et son enlèvement, Chanfrein, Chanfrein de sommet, Texte, Couper avec une surface, Supprimer des corps ; le reste tombe sur `get_params`) ; `engine/equations.py` (`_EDITABLE_PROPS`, liste blanche des cotes) ; `engine/vocab.py` (`PARAM_KEYS`) ; `engine/surfacefeat/commun.py` (ce qui est « figé »).

Contre-exemple à suivre : Supprimer des corps vient d'être rendu rééditable (panneau de la création rouvert, sa zone remplie de ce qu'elle vise, réécrit sur place sans changer de rang).

### 4. Les sélections qui ne reviennent pas

Arêtes, faces, profils, corps, directions, outils : presque aucun ne se re-choisissait.

Fait : chaque fonction qui se réédite re-choisit maintenant ce qu'elle a pris à la création, dans le panneau de sa création, sur la pièce à son rang. Ce qui ne revient toujours pas tient aux fonctions encore sans aucune réédition (références, surfaces cousue et médiane, Supprimer ou Remplacer la face du solide : thème 3), qui re-choisiront leurs sélections avec leur panneau, ou à des options (thème 5). Le détail, fonction par fonction :

Corrigé pour le Congé, le Chanfrein, la Coque et la Dépouille. Leur double-clic rouvre le panneau de la création, sa zone remplie de leurs arêtes ou de leurs faces. Comme dans les modeleurs courants, la pièce se montre à leur rang, comme pour Supprimer des corps (`rank_view`) : les arêtes qu'ils ont arrondies y existent encore, se surlignent, et Ctrl+clic en ajoute ou en retire. L'aperçu les montre rééditées sans quitter ce rang. `set_params` prend `edges` ou `face` (congé, chanfrein), `faces` (coque), `face` et `neutral` (dépouille, dont le plan neutre se repose sur la nouvelle face) ; une fonction plus bas qui perdrait une arête qu'elle utilise fait refuser la réédition, en la nommant. Toutes les faces d'une zone se surlignent, pas seulement la dernière cliquée (à la création aussi).
Corrigé aussi pour le Perçage posé par des clics sur une face. Sa zone « Positions » revient remplie de ses centres, sur la pièce à son rang : un clic pose un centre, un clic dans un trou le retire, un clic sur une autre face fait repartir la zone de cette face (à la création aussi). `set_params` prend `positions` (`{face, points}`) : l'esquisse du perçage se repose sur la face et n'y garde qu'un cercle par centre. Un perçage posé sur une esquisse dessinée à part garde la réédition de son esquisse.

Corrigé aussi pour le Texte : son double-clic rouvre le panneau de la création (sans le relief, voir thème 5), sa zone « Face d'appui » remplie de sa face sur la pièce à son rang, avec l'aperçu. `set_params` prend les mots de la création (`text`, `size`, `depth`, `x`, `y`) et `face` : le texte se repose au centre de la nouvelle face. Si la pièce a changé en amont et qu'aucune face ne porte plus le texte, la zone revient vide : le texte reste où il est, ou se repose sur la face cliquée.

Corrigé aussi pour le Chanfrein de sommet : sa zone « Sommet » revient remplie de son coin, sur la pièce à son rang, avec l'aperçu ; un clic près d'un autre coin le remplace. `set_params` prend `distances` et `point` (le clic, aimanté au sommet le plus proche, comme à la création).

Profils et esquisses : comme dans les modeleurs courants, une fonction garde son esquisse ; c'est le plan de l'esquisse qui se re-choisit. Le clic droit d'une esquisse, « Changer de plan… », rouvre la pièce au rang de la fonction qui la prend, la liste sur son plan actuel (plan d'origine, plan de référence ou « Face du solide » avec sa face), avec l'aperçu. Une face se clique sur la pièce à ce rang, celle d'une fonction antérieure : avant, seule la face de la pièce d'aujourd'hui se proposait, refusée dès que la fonction était au milieu de l'historique. `set_params` d'une esquisse prend `plane`, `datum` ou `face` ; `rank_view` d'une esquisse prise par une fonction montre le rang de cette fonction. Cela vaut pour toutes les fonctions qui prennent une esquisse : Extrusion, Enlèvement, Révolution, Hélice, surfaces. La Surface extrudée et la Surface de révolution ont maintenant une zone « Profil » à la création, préremplie comme celles des autres surfaces (la sélection de l'arbre, sinon la dernière esquisse libre).

Répétitions de fonctions (linéaire, circulaire, symétrie) : le double-clic rouvre le panneau de la création, au rang. La zone « Fonctions à répéter » revient remplie ; un clic dans l'arbre en ajoute ou en retire une, qui doit venir avant la répétition. La direction revient sur son axe d'origine ou son arête (une arête droite de la pièce à son rang), avec son sens ; la symétrie, sur son plan. La deuxième direction d'un réseau linéaire s'active, se règle (axe, sens, distance, nombre) et se retire ; sa distance est le pas si le réseau compte en pas, comme à la création. Le réseau linéaire revient aussi sur son mode, pas entre occurrences ou longueur totale, et la distance est celle de ce mode : en pas, FreeCAD ignore la longueur totale, et le panneau la montrait, si bien qu'une distance rééditée ne changeait rien ; elle vise maintenant le pas. Changer de mode emporte la distance telle qu'elle est écrite. `set_params` prend `features`, `axis` ou `edge`, `reversed`, `plane`, `mode`, `dir2`, `axis2`, `edge2`, `reversed2`, `length2` et `count2`. Selftest p113 à p119.

Répétitions de corps (linéaire, circulaire, symétrie) : le même panneau, au rang. La zone « Corps à répéter » revient remplie ; un clic dans la vue ou dans le dossier ajoute un corps, la croix le retire. Un corps qui vient après la répétition, ou une de ses propres copies, est refusé. Retirer un corps fait partir ses copies : si l'une porte une esquisse ou une fonction, la question vient d'abord, comme quand on réduit le nombre. La direction revient sur son axe d'origine ou son arête, prise sur le corps actif tel qu'il est au rang ; une répétition d'avant ne gardait que le vecteur : il se relit sur les axes d'origine, sinon la zone d'arête reste vide et la direction telle quelle. La deuxième direction s'active et se retire sans refaire les copies de la première rangée : elles changent de repère et gardent ce qu'elles portent. L'aperçu montre les copies telles qu'elles deviennent. `set_params` prend `sources` (`bodies` y désigne déjà les corps concernés), `axis` ou `edge`, `reversed`, `plane`, `mode`, `dir2`, `axis2`, `edge2`, `reversed2`, et les cotes de l'hôte. Selftest p120.

Surfaces qui prennent une surface, une esquisse, un bord ou des arêtes (Surface plane, Surface décalée, Épaissir, Prolonger, Congé de surfaces) : le double-clic rouvre le panneau de la création, au rang, sa zone remplie de ce que la surface prend, avec l'aperçu de la surface rééditée. La Surface plane re-choisit l'esquisse de son contour ; la décalée et l'épaississement, leur surface, d'un clic dans l'arbre ; le prolongement, son bord, ou la surface entière pour tous ses bords (un bord d'une autre surface fait changer de surface) ; le congé, ses arêtes, qui peuvent être celles d'une autre surface, toutes de la même. Une surface ou une esquisse qui vient après, ou qui dépend de la surface rééditée, est refusée en la nommant ; sur refus, la pièce reste telle quelle. `set_params` prend `sketch` (plane), `source` (décalée, épaississement, prolongement, congé), `edge` (None : tous les bords), `edges` et les cotes. Selftest p121.

Outils de surface (Couper avec une surface, Courbe d'intersection, Projeter une courbe) : le même panneau, au rang. La coupe re-choisit sa surface outil d'un clic dans l'arbre, son côté, et passe de tout un côté à une bande épaisse, et retour : l'outil caché se refait, comme à la création. Une coupe qui n'enlèverait rien, ou tout, est refusée. La courbe d'intersection re-choisit ses deux surfaces, ou passe à une surface et le solide ; la courbe projetée, son esquisse, sa surface et sa face, la direction suivant la normale de l'esquisse. Une forme qui vient après, ou qui dépend de la courbe, est refusée ; deux formes qui ne se coupent plus aussi. `set_params` prend `surface`, `flip` et `thickness` (None : tout un côté) pour la coupe ; `first`, `second` et `body` pour l'intersection ; `sketch`, `surface` et `face` pour la projection. Selftest p122.

Ajuster : le même panneau, au rang, où la surface ajustée se montre entière. La zone « Outil de coupe » revient remplie, la zone « Partie à garder » aussi, sur un point de la partie gardée ; un clic sur une autre partie, ou sur une autre surface, la change. Un outil changé sans nouveau clic garde la partie du même côté. Un ajustement mutuel reste deux lignes, chacune rééditée seule. `set_params` prend `source`, `tool` et `point`. Le panneau ne propose plus « Garder l'autre partie » : comme à la création, on clique la partie. Selftest p123.

Surface radiée : le même panneau, au rang. La zone « Contour plan » revient remplie, arête par arête (une esquisse prise entière revient en ses arêtes) ; un clic en ajoute, la croix en retire. Une forme qui vient après la surface est refusée. Une radiée dont la distance est pilotée par une équation garde le panneau des cotes. `set_params` prend `boundary`, comme à la création, avec `distance`. Selftest p124.

Forme libre et Pôles : la surface déformée revient dans sa zone et se re-choisit d'un clic dans l'arbre, la Forme libre au rang avec l'aperçu. Les points poussés se reprojettent sur la nouvelle surface ; les pôles déplacés gardent leurs indices, et la grille se redessine sur elle. Une surface qui vient après, ou qui dépend de la forme libre, est refusée. `set_params` prend `source` avec, selon le genre, `pushes`, `radius` et `keep_edges`, ou `moves` et `grid`. Selftest p125.

Combiner : le panneau de la création, au rang, où le corps outil reparaît dans le dossier. L'opération et le corps outil reviennent dans leurs listes ; un autre corps outil rend le premier, qui revient au dossier. Un nom donné à la fonction reste ; le nom par défaut suit l'opération. Un corps outil venu d'un module (dérivé par lui) ne se re-choisit pas : l'opération seule. Comme à la création, pas d'aperçu : un booléen peut durer. `set_params` prend `type` et `tool`. Selftest p126.

Extrusion et Enlèvement : la face d'arrivée se re-choisit, et une autre condition passe à « jusqu'à la face ». Quand un « jusqu'à » peut arrêter la fonction (elle n'est pas le premier volume de son corps), le panneau s'ouvre sur la pièce à son rang. La zone « Face d'arrivée » revient remplie et surlignée ; un clic sur une face de la fonction d'avant la remplace, avec l'aperçu. Une face plane qui ne couvre pas le profil est prolongée par FreeCAD. `set_params` prend `face` avec les conditions de fin ; une face sans « jusqu'à la face » est refusée. Selftest p128.

Lissage et Balayage : le panneau de la création, au rang. Les profils d'un lissage reviennent dans leur zone, dans l'ordre : un clic dans l'arbre retire une esquisse de la zone ou l'ajoute au bout, ce qui change aussi l'ordre. Le profil et la trajectoire d'un balayage reviennent dans les leurs ; la trajectoire peut être une esquisse ou une courbe 3D. Comme à la création, une esquisse d'un autre corps entre par un liant caché ; celui d'un profil retiré part. Le lissage droit et la boucle fermée reviennent aussi ; le genre (ajout ou enlèvement) reste. Une esquisse qui vient après la fonction est refusée, comme un profil pris deux fois ou un profil égal à la trajectoire. `set_params` prend `profiles` (dans l'ordre), `ruled`, `closed`, ou `profile` et `spine`, avec les corps concernés et « Fusionner », tout ou rien. Selftest p129.

Aplatir : le panneau de la création, au rang, avec la déformation mesurée. La zone « Face » revient remplie de la surface et de sa face ; un clic sur une autre face la remplace, sur une autre surface aussi. Une surface qui vient après le patron est refusée. `set_params` prend `surface` et `face`. Selftest p130.

Surfaces lissée, balayée, réglée, frontière, de remplissage, Diviser, Annuler l'ajustement, Supprimer la face d'une surface, Courbe composite : elles n'avaient aucune réédition (thème 3). Leur double-clic rouvre maintenant le panneau de la création, au rang, avec l'aperçu, ses zones remplies de ce qu'elles prennent : les profils d'une lissée dans l'ordre, le profil et la trajectoire d'une balayée, les courbes ou le contour, arête par arête (une esquisse prise entière revient en ses arêtes), la surface et la courbe d'une division, la face d'un désajustement, les faces supprimées. Une forme qui vient après, ou qui en dépend, est refusée en la nommant ; les refus de la création valent aussi (deux courbes pour une réglée, deux à quatre pour une frontière, une courbe qui ne scinde pas la surface, des arêtes qui ne se suivent pas, toutes les faces supprimées). Le remplissage garde sa tangence : une arête fermée y prend ses moitiés auxiliaires, défaites quand elle part ; un bouchon tangent se refait sur les faces que bordent les nouvelles arêtes. `set_params` prend `profiles`, `profile` et `spine`, `boundary`, `source` et `tool`, `source` et `face`, `source` et `faces`. Selftest p132.

Répétition variable : son graphe se réédite dans l'éditeur de graphe, dont le bouton « Fonctions » ferme l'éditeur (la question vient d'abord si le graphe n'a pas été appliqué) et rouvre la zone de la création, au rang, remplie des fonctions répétées. Un clic dans l'arbre en retire une ou l'ajoute au bout : l'ordre compte, le groupe se rejoue dans l'ordre de la zone. Le graphe ou les instances enregistrés restent ; des cotes d'instance qui visent une fonction retirée font refuser la réédition, comme une fonction qui vient après la répétition (elle en dépend). `set_params` prend `features`. Selftest p131.

Indices de face ou d'arête, vérifiés quand l'esquisse amont change de topologie (un trou, un segment ajouté au début, qui décalent l'ordre des faces et des arêtes). Le Congé et le Chanfrein, la Surface radiée sur des arêtes de la pièce, le Congé de surfaces suivent leurs arêtes : le nommage topologique de FreeCAD 1.x remet les indices. Le Prolongement range son bord comme un côté de la surface, l'Ajuster sa partie gardée comme un morceau de la découpe : rien ne se décale. Les pôles d'une forme libre et la face d'un patron à plat gardaient l'indice de leur face : quand l'ordre changeait, les déplacements passaient en silence sur une autre face. Chaque face réglée garde maintenant un point de repère pris à l'intérieur, et ses réglages retrouvent la face la plus proche ; repères et indices se remettent à jour quand la surface source change. Selftest p127.

Où ça se décide : `app/tree.js`, `editAtRank`, rouvre le panneau de la création sur la pièce au rang de la fonction (`rank_view`), ses zones remplies de ce que l'arbre décrit (`app/features/*.js`, les fonctions `…Pick` et `…EditValues`), et n'envoie que ce qui change. Le moteur remplace les sélections dans `set_params` (`engine/equations.py` aiguille selon la fonction : `engine/surfacefeat/reedition.py` pour les surfaces et les courbes, `_set_surface_cut_params`, `_set_combine_params`, `_set_swept_params`, `_set_pattern_picks`, `_set_body_pattern_picks`, `edit_repeat_feature`…), tout ou rien, et refuse en la nommant une forme qui vient après ou qui dépend de la fonction.

### 5. Les options de création qui ne reviennent pas

Des réglages simples, parfois un seul booléen, présents à la création et absents à la réédition.

Corrigé pour quatre fonctions : leur double-clic rouvre le panneau de la création, rempli de ce que la fonction est.

- **Extrusion et Enlèvement** : condition de fin, décalage, inverser, dépouille, direction 2 et paroi mince (épaisseurs, côté). Le moteur envoie les conditions dans l'arbre (`extrude`, dans les mots de la création) et `set_params` les pose ensemble, sous les clés du formulaire. La cavité d'une paroi à extrémités fermées suit le plan milieu et refuse, comme à la création, une condition non borgne ou une dépouille.
- **Coque** : la case « vers l'extérieur » (clé `outward`). La garde de la création vaut aussi à la réédition : une coque vers l'intérieur qui n'évide rien est refusée.
- **Perçage** : type, condition de fin, angle du fraisage. Les cotes suivent le type : la profondeur seulement en borgne, le Ø de tête sans « Perçage » simple, la profondeur du lamage pour le lamage, l'angle pour le fraisage. FreeCAD remet les cotes de tête à ses valeurs quand le type change : le panneau les renvoie alors toutes.
- **Surface décalée et Surface radiée** : la case de sens de la création, au lieu du signe de la distance (voir thème 7).
- **Dépouille** : le plan neutre (clé `neutral`), reposé sur la face choisie ; un plan parallèle à la face est refusé, la pièce reste telle quelle.

Reste :

- **Extrusion et Enlèvement** : activer la paroi mince ou changer son genre (un, plan milieu, deux côtés), ce qui ajoute ou retire des profils cachés. « Fusionner » et les corps qu'elle fusionne se rééditent pour l'Extrusion, la Révolution, le Lissage et le Balayage. Décochée, la fonction sort de son corps pour un corps neuf ; cochée sur le premier volume d'un corps, elle fond les corps qu'elle touche, ou ceux de la zone. La zone est remplie des corps fondus et, si la fonction part d'une fonction d'avant, de son corps : retiré, elle en sort pour un corps neuf qui fond les autres ; un clic dans la vue ou le dossier en ajoute ou en retire un, la croix d'une ligne le retire (un corps fondu ne se voit plus à part dans la vue). Le Lissage et le Balayage, sans cote, se rouvrent sur leurs profils (thème 4), avec cette zone quand la pièce a d'autres corps. Un corps ajouté est fondu, ou creusé par l'enlèvement, à leur rang ; retiré, il revient. Cette zone s'appelle « Corps concernés » partout : ajout ou enlèvement, création ou réédition. Une fonction ne fait que l'un ou l'autre, comme la liste unique « Corps volumiques affectés » des modeleurs courants. Leur « Fusionner » se change aussi : décochée, la fonction sort de son corps, et chaque profil et la trajectoire y entrent par un liant caché, comme à la création dans un autre corps (une courbe 3D garde le sien). Un balayage dont le profil n'est pas d'un seul tenant ne sort pas : d'un liant, FreeCAD ne balaie qu'une face.
- **Texte** : relief ou gravure, police. Le relief est dans la forme des lettres et dans le genre du booléen : il faut reconstruire.
- **Fonctions graphe et Répétition variable** : ajout ou enlèvement, nature de la fonction. Les fonctions répétées se re-choisissent (thème 4).
- **Réédition partielle qui laisse croire à une réédition complète** : Hélice 3D (ni axe ni sens).

Où ça se décide : `engine/equations.py` (`set_params`, `_editable_props`) ; `engine/solids.py` (`_extrude_state`, `_set_extrude_options`, `_hole_state`) ; `engine/extrude.py` (`extrude_state`, `extrude_options`) ; `engine/vocab.py` (`PARAM_KEYS`) ; `app/features/volumes.js` et `habillage.js` (panneaux partagés entre création et réédition) ; `app/tree.js` (`editFeature`) ; `app/editkind.js`.

### 6. L'aperçu absent ou inégal

- **À la création** : absent pour toutes les surfaces (sauf Couper avec une surface) et toutes les opérations sur surfaces et courbes (sauf Remplacer et Supprimer la face du solide, et Supprimer la face d'une surface), pour l'Axe, le Point et le Repère, pour les fonctions graphe et la Répétition variable. Les surfaces dont le résultat est le plus incertain (Ajuster, Diviser) sont celles sans aperçu. Deux absences sont voulues : Combiner (booléen lent) et la Surface médiane.
- **À la réédition** : absent pour les Pôles, Supprimer des corps, les fonctions graphe. La Répétition de corps passe par le même aperçu que les fonctions, sans le fantôme des seuls corps nouveaux de la création (à vérifier).
- **Surfaces** : l'aperçu d'une surface rééditée par `set_params` montre la surface elle-même (vérifié pour la Surface plane, la décalée, Épaissir, Prolonger et le Congé de surfaces ; les autres surfaces rééditées par leurs cotes passent par la même voie, à vérifier).
- **Bulle de rayon du Congé** : présente à la création, absente à la réédition.
- **Flèche de profondeur** : seulement pour l'Extrusion et l'Enlèvement. Ni Révolution, ni Perçage, ni Hélice, ni Surface extrudée.
- **Entrées du menu de la vue** : entrées dédiées pour l'Extrusion, l'Enlèvement et la Révolution seulement (écart d'accès, pas de réédition).

Où ça se décide : `app/main/featurepanel.js` (branche l'aperçu sauf `preview:false`, et la flèche) ; `app/features/*.js` (le drapeau `preview:false` de chaque entrée) ; `engine/ops/*.py` (`preview=True` de chaque opération) ; `app/tree.js` (un `onChange` par panneau de réédition) ; `app/main.js` (`showGhost`, qui ne dessine que le maillage du corps) ; `engine/directedit.py` (`_depth_editable`).

### 7. Le sens dit de plusieurs façons

- **Surface décalée, Surface radiée, Épaissir** : la décalée et la radiée ont maintenant la même case à la création et à la réédition (« Inverser le côté », « Vers l'intérieur »), et la radiée est libellée « Distance ». Épaissir n'a pas de case : le signe de l'épaisseur, aux deux moments. Une radiée dont la distance est pilotée par une équation garde le panneau des cotes, où le sens reste le signe.
- **Texte** : « Hauteur », « Décalage X/Y » à la création, « Taille », « X », « Y » à la réédition.
- **Hélice** : l'angle n'existe qu'à la réédition.
- **Dépouille** : libellé « Faces à dépouiller » au pluriel pour une seule face, alors que la Coque en accepte plusieurs.

Où ça se décide : `app/features/surfaces.js`, `habillage.js`, `volumes.js` (panneaux de création) ; `app/tree.js` (libellés de réédition, `PARAM_LABELS_BY_KIND` et le panneau Gravure) ; `engine/vocab.py` (`PARAM_KEYS`).

### 8. Barre de retour : des lignes qui n'y entrent pas comme les autres

- **Références** (Plan, Axe, Point, Repère) : ce ne sont pas des fonctions de l'historique. D'après le code, la barre ne les pose pas et « poser la barre ici » est refusé (« n'est pas une ligne d'historique »). À vérifier à l'exécution.
- **Chanfrein de sommet** : rangé comme un booléen (jusqu'à deux lignes, ajout puis intersection). Effet sur la barre : à vérifier.
- **Épaissir** : classée avec les surfaces (barre par drapeau) alors que son résultat est un solide ; Couper avec une surface est une fonction de corps (barre par le Tip). Pas d'écart de comportement constaté.
- **Cousue et Médiane** : si la barre recule au-dessus de leur base, le moteur saute la mise à jour sans le dire.
- **Remplacer et Supprimer la face du solide** : seules opérations de leur famille dans la chaîne du corps ; elles ne se masquent pas.
- **Ajustement mutuel** : deux lignes indépendantes, rééditer l'une ne touche pas l'autre.

Où ça se décide : `engine/tree.py` (`_history_role`, `set_tip`) ; `engine/kernel.py` (`_ROLLBACK_ROLES`) ; `engine/surfacefeat/commun.py` (`_refresh_frozen_shapes`) ; `engine/surfacefeat/solide.py` ; `engine/surfacefeat/prolonger.py`.

### 9. Le rejeu et la documentation

- **Rejeu** : `no_replay` est périmé pour l'Hélice. La raison dit « Pitch/Height hors whitelist », or ces deux cotes sont dans la liste de `get_params`. `engine/replay.py` la classe encore comme rejouable sous condition. Lissage, Balayage, Texte, Combiner, les trois répétitions de fonctions et de corps, les fonctions graphe, le Chanfrein de sommet, les références et la Spline 3D sont non rejouables, pour des raisons de fond. Ce que fait le rejeu d'une opération de surface (sans `replay` ni `no_replay`) : à vérifier.
- **Documentation** : `docs/ecarts-solidworks.md` décrit encore Extrusion, Enlèvement et Révolution comme sans conditions de fin ni axe, alors que d'autres lignes du même tableau disent « fait » ; il ne consigne aucun écart propre aux surfaces ni à l'habillage.

Où ça se décide : `engine/ops/volumes.py`, `habillage.py`, `references.py`, `surfaces.py`, `noeuds.py`, `repetitions.py` ; `engine/replay.py` ; `tests/` (le test de cohérence ne couvre que les opérations `add_*`).

### 10. La couverture du selftest

Aucune étape de réédition dans `engine/selftest/` pour : Enlèvement extrudé, Enlèvement de révolution, Hélice (volume), Plan, Axe, Point, Repère, Répétition circulaire (fonctions et corps), Symétrie, Surface de révolution, et les opérations Diviser, Annuler l'ajustement, Courbe composite, Remplacer et Supprimer la face. Les clés de quatre surfaces ne sont vérifiées que par un test unitaire (`tests/test_param_keys.py`). Ce qui n'a pas de réédition n'a pas de test de bout en bout ; que l'arbre et `get_params` disent la même chose est vérifié par l'étape p87, et le choix de l'éditeur par `tests/js/editkind.test.mjs`.

Aucun selftest ne vise la barre de retour ni Masquer sur les surfaces et courbes (la barre n'est testée que sur une surface générique, Masquer que sur des corps). Désactiver n'est pas testé fonction par fonction.

Où ça se décide : `engine/selftest/fonctions.py`, `document.py`, `surfaces.py`, `noeuds.py`, `esquisse.py` ; `tests/test_param_keys.py` ; `tests/js/` pour le côté interface.
