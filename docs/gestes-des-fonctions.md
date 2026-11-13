# Gestes des fonctions

Cette grille sert à repérer où les fonctions ne se comportent pas pareil. Pour chacune, elle dit si l'on peut rééditer après coup ce qu'on a choisi à la création, et si les gestes (aperçu, double-clic, menu « Modifier », barre de retour) sont les mêmes d'une fonction à l'autre.

État décrit : 2026-11-13. La grille a été dressée le 2026-11-02, après #151 (« Modifier » au menu suit le double-clic), #153 (« Désactiver » suit le moteur) et la réédition des options de création (Extrusion, Enlèvement, Coque, Perçage, surfaces décalée et radiée). Elle a été tenue à jour depuis : toutes les fonctions se rééditent (thème 3, #203 à #205), leurs sélections se re-choisissent au rang (thème 4, #189 à #202), l'aperçu est partout sauf là où son absence est voulue (thème 6, #206), et les références et les formes figées entrent dans la barre de retour comme les autres lignes (thème 8, #207). Restent les thèmes 2, 5, 7, 9 et 10. La grille vient de la lecture du code et des selftests, contrôlée par un relevé : ce que l'arbre dit de chaque ligne fabriquée par le selftest (`has_params`, 51 genres), et quelques gestes rejoués dans le navigateur. Ce qui n'a pas été tranché est marqué « à vérifier ».

Tenir la grille à jour : une fonction ajoutée ou corrigée met sa ligne à jour dans le même changement (et, si un écart disparaît ou apparaît, la section « Écarts, par thème »). Les références vont au fichier et à la fonction, jamais à une ligne. « Écart n° N » renvoie au tableau de `docs/ecarts-solidworks.md`.

## Légende des colonnes

- **Aperçu à la création** : le fantôme jaune pendant que le panneau est ouvert. « oui + flèche » : la flèche de profondeur dans la vue en plus.
- **Réédition : ce qui revient** : ce que le double-clic (ou « Modifier ») permet de changer.
- **Ne revient pas** : ce qui a été choisi à la création et qu'on ne peut plus changer sans supprimer et refaire.
- **Aperçu à la réédition** : le fantôme jaune pendant la réédition. « — » : rien à rééditer.
- **Barre de retour** : la fonction se pose sur la barre et recule avec elle. « oui (drapeau) » : surface, esquisse libre ou référence, qui se masque par drapeau au lieu de passer par le Tip du corps.
- **Selftest de réédition** : un test de bout en bout de `engine/selftest/` réédite la fonction. « non » : aucun trouvé.

« Modifier » au menu n'est pas une colonne : depuis #151, il est proposé exactement quand le double-clic rouvre quelque chose (`app/editkind.js`), donc quand la colonne « Réédition » dit autre chose que « rien ». « Désactiver » et « Masquer » non plus : leurs écarts sont dans la section des écarts, car ils tiennent à des règles du menu et non à la fonction.

## Volumes

| Fonction | Aperçu à la création | Réédition : ce qui revient | Ne revient pas | Aperçu à la réédition | Barre de retour | Selftest de réédition |
|---|---|---|---|---|---|---|
| Extrusion | oui + flèche | le panneau de la création, sur la pièce au rang quand un « jusqu'à » peut l'arrêter : condition de fin (borgne seulement pour le premier volume d'un corps), face d'arrivée (cliquée sur la pièce au rang), décalage, inverser, dépouille, direction 2 (condition, profondeur, dépouille), épaisseurs et côté de la paroi mince, contours, « Fusionner », corps fondus et corps de la fonction (une zone : clic ou cadre dans la vue, clic dans le dossier, croix pour retirer) | activer la paroi mince ou en changer le genre (le plan de l'esquisse se re-choisit au rang : clic droit, « Changer de plan… ») | oui + flèche (la flèche s'efface quand le sens ou la condition change) | oui | oui (conditions, face d'arrivée, direction 2, paroi mince, extrémités fermées, « Fusionner », corps fondus, corps de la fonction) |
| Enlèvement extrudé | oui + flèche | comme l'Extrusion, les corps creusés au lieu des corps fondus (une zone : clic ou cadre dans la vue, clic dans le dossier, croix pour retirer) | comme l'Extrusion | oui + flèche | oui | oui (à travers tout, borgne, refus de « jusqu'à la face », corps creusés qui suivent la cote, corps creusés ajoutés ou retirés) |
| Révolution | oui | angle, axe, inverser, plan médian, contours, « Fusionner », corps fondus et corps de la fonction ; plan de l'esquisse (« Changer de plan… ») | — | oui | oui | oui (axe, plan médian, « Fusionner », corps fondus) |
| Enlèvement de révolution | oui | comme la Révolution, les corps creusés au lieu des corps fondus | comme la Révolution | oui | oui | non (seule la Révolution est testée) |
| Perçage | oui + flèche (borgne, dès le premier trou cliqué) | le panneau de la création : positions et face (posé par des clics), type (simple, lamage, fraisage), cotes du type, angle du fraisage, à travers ou borgne, profondeur, corps creusés (une zone : clic ou cadre dans la vue, clic dans le dossier, croix pour retirer) | — | oui + flèche | oui | oui (type, condition de fin, corps creusés, positions) |
| Lissage | oui | le panneau de la création, au rang : profils et leur ordre (un clic dans l'arbre retire une esquisse de la zone ou l'ajoute au bout ; celle d'un autre corps entre par un liant caché), lissage droit, boucle fermée ; « Fusionner » (décochée, il sort de son corps ; ses profils y entrent par des liants) ; quand la pièce a d'autres corps, les corps fondus, ou creusés pour l'enlèvement lissé (une zone : clic ou cadre dans la vue, clic dans le dossier, croix pour retirer) | soustractif | oui | oui | oui (profils retirés, réordonnés, d'un autre corps, lissage droit, « Fusionner » décochée puis recochée, zone d'action, corps fondus ajoutés puis retirés) |
| Balayage | oui | le panneau de la création, au rang : profil et trajectoire (une esquisse ou une courbe 3D), et comme le Lissage : « Fusionner » (profil d'un seul tenant pour sortir de son corps), les corps fondus, ou creusés pour l'enlèvement balayé | soustractif | oui | oui | oui (profil, trajectoire sur une esquisse ou une courbe 3D, « Fusionner » décochée sur une esquisse et sur une courbe 3D, profil en deux morceaux refusé, corps creusés ajoutés, Ctrl+Z et Ctrl+Y) |
| Hélice | oui + flèche | pas, hauteur, angle ; plan de l'esquisse (« Changer de plan… ») | — | oui + flèche | oui | non (la flèche seule : p136) |
| Texte | oui | le panneau de la création : texte, hauteur, profondeur, décalage, face d'appui | relief ou gravure, police | oui | oui | oui |

## Habillage, Combiner et références

| Fonction | Aperçu à la création | Réédition : ce qui revient | Ne revient pas | Aperçu à la réédition | Barre de retour | Selftest de réédition |
|---|---|---|---|---|---|---|
| Congé | oui + bulle de rayon | rayon ; arêtes ou face, re-choisies sur la pièce à son rang | — | oui + bulle de rayon | oui | oui (rayon, arêtes) |
| Chanfrein | oui | type, taille, taille 2, angle, sens ; arêtes ou face, re-choisies sur la pièce à son rang | — | oui | oui | oui |
| Chanfrein de sommet | oui | le panneau de la création : sommet, distances | — | oui | oui (une ligne ; une fonction posée sous la barre avant lui entre dans sa forme) | oui |
| Coque | oui | épaisseur, « vers l'extérieur » ; faces à ouvrir, re-choisies sur la pièce à son rang | — | oui | oui | oui (sens, refus d'une coque trop épaisse, faces) |
| Dépouille | oui | angle, plan neutre ; face, re-choisie sur la pièce à son rang | — | oui | oui | oui (face, plan neutre) |
| Combiner | non, voulu | le panneau de la création, au rang (le corps outil y reparaît) : opération, corps outil (venu d'un module : l'opération seule) | — | non, voulu | oui | oui (opération, corps outil, refus) |
| Supprimer des corps | non, voulu | complète : corps, solides ou surfaces choisis (une zone : clic ou cadre dans la vue, clic dans le dossier, croix pour retirer), ôter ou garder | rien | non, voulu | oui (drapeau) | oui |
| Plan de référence | oui + fantôme | le panneau de la création, sur la pièce à son rang : face ou plan d'origine, décalage, angle | — | oui + fantôme | oui (drapeau) | oui |
| Axe de référence | oui | le panneau de la création, sur la pièce à son rang : axe d'origine ou arête droite ou circulaire | — | oui | oui (drapeau) | oui |
| Point de référence | oui | le panneau de la création, sur la pièce à son rang : sommet, centre d'une arête circulaire ou coordonnées | — | oui | oui (drapeau) | oui |
| Repère | oui | le panneau de la création, sur la pièce à son rang : sommet ou coordonnées | — | oui | oui (drapeau) | oui |

## Répétitions et graphe

| Fonction | Aperçu à la création | Réédition : ce qui revient | Ne revient pas | Aperçu à la réédition | Barre de retour | Selftest de réédition |
|---|---|---|---|---|---|---|
| Répétition linéaire, des fonctions | oui | le panneau de la création : fonctions répétées, direction (axe ou arête), inverser, pas ou longueur totale, distance, nombre, direction 2 (l'activer, la retirer, son axe, son sens, sa distance, son nombre) ; corps creusés, quand elle répète un enlèvement | — | oui, sans la flèche | oui | oui (nombre, corps creusés, fonctions, direction, pas ou longueur totale, direction 2) |
| Répétition linéaire, des corps | oui | le panneau de la création, au rang : corps répétés (une zone : clic dans la vue ou le dossier, croix pour retirer), direction (axe ou arête), inverser, pas ou longueur totale, distance, nombre, direction 2 (l'activer, la retirer, son axe, son sens, sa distance, son nombre) | copies sautées | oui (les copies) | oui | oui (nombre, distance, corps, direction, mode, direction 2) |
| Répétition circulaire, des fonctions | oui | le panneau de la création : fonctions répétées, axe (d'origine ou arête), inverser, angle total, nombre ; corps creusés, quand elle répète un enlèvement | — | oui | oui | non |
| Répétition circulaire, des corps | oui | le panneau de la création, au rang : corps répétés, axe (d'origine ou arête), inverser, angle total, nombre | copies sautées | oui (les copies) | oui | oui (axe) |
| Symétrie, des fonctions | oui | fonctions, plan ; corps creusés, quand elle répète un enlèvement | — | oui | oui | oui (corps creusés, plan) |
| Symétrie, des corps | oui | le panneau de la création, au rang : corps répétés, plan | copie sautée | oui (la copie) | oui | oui (plan) |
| Fonction graphe, solide (ajout, enlèvement) | non, voulu | le graphe, dans l'éditeur de graphe | ajout ou enlèvement, nature solide ou courbe | non, voulu | oui | oui |
| Fonction graphe, courbe ou surface | non, voulu | le graphe, dans l'éditeur de graphe | nature courbe ou surface | non, voulu | oui (drapeau) | oui |
| Répétition variable | non, voulu | nombre d'instances et graphe, dans l'éditeur de graphe ; fonctions répétées, au rang (bouton « Fonctions » de l'éditeur) | ajout ou enlèvement | non, voulu | oui | oui (instances, fonctions) |

## Surfaces

| Fonction | Aperçu à la création | Réédition : ce qui revient | Ne revient pas | Aperçu à la réédition | Barre de retour | Selftest de réédition |
|---|---|---|---|---|---|---|
| Surface extrudée | oui + flèche | longueur ; plan de l'esquisse (« Changer de plan… ») | sens | oui + flèche | oui (drapeau) | oui |
| Surface de révolution | oui | angle ; plan de l'esquisse (« Changer de plan… ») | axe, sens | oui | oui (drapeau) | non |
| Surface lissée | oui | le panneau de la création, au rang : profils, dans l'ordre (un clic dans l'arbre en retire un ou l'ajoute au bout) | — | oui | oui (drapeau) | oui (profils, refus d'un seul ou d'un doublon) |
| Surface cousue | oui | le panneau de la création, au rang : surfaces (forme figée, recalculée sur elles) | — | oui | oui (drapeau) | oui (surfaces, refus d'une seule) |
| Épaissir | oui | le panneau de la création, au rang : surface (clic dans l'arbre), épaisseur (signée) | — | oui | oui (drapeau) | oui (surface, épaisseur) |
| Couper avec une surface | oui | le panneau de la création, au rang : surface outil (clic dans l'arbre), inverser le côté, tout un côté ou une bande épaisse, épaisseur | — | oui | oui | oui (surface outil, bande, retour à tout un côté, refus) |
| Surface plane | oui | le panneau de la création, au rang : esquisse du contour | — | oui | oui (drapeau) | oui (esquisse, refus d'une esquisse d'après) |
| Surface balayée | oui | le panneau de la création, au rang : profil, trajectoire (esquisse ou courbe 3D) | — | oui | oui (drapeau) | oui (trajectoire, refus du profil comme trajectoire) |
| Surface décalée | oui | le panneau de la création, au rang : surface (clic dans l'arbre), distance et « inverser le côté » | — | oui | oui (drapeau) | oui (surface, refus d'elle-même et d'une surface d'après) |
| Surface de remplissage | oui | le panneau de la création, au rang : contour (un bouchon tangent se refait sur les faces que bordent les nouvelles arêtes) | case « tangent » | oui | oui (drapeau) | oui (contour, arête fermée, bouchon tangent) |
| Surface frontière | oui | le panneau de la création, au rang : 2 à 4 courbes | — | oui | oui (drapeau) | oui (courbes) |
| Surface radiée | oui | le panneau de la création, au rang : contour plan, distance et « vers l'intérieur » (pilotée par une équation : la distance signée, dans le panneau des cotes) | — | oui | oui (drapeau) | oui (contour, refus d'une forme d'après) |
| Surface médiane | non, voulu | le panneau de la création, au rang : les deux faces, ou toutes les parois et l'épaisseur (forme figée) | — | non, voulu | oui (drapeau) | oui (faces, toutes les parois, refus d'une face) |
| Surface réglée | oui | le panneau de la création, au rang : les deux courbes | — | oui | oui (drapeau) | oui (courbes, refus de trois) |

## Opérations sur surfaces et courbes

| Fonction | Aperçu à la création | Réédition : ce qui revient | Ne revient pas | Aperçu à la réédition | Barre de retour | Selftest de réédition |
|---|---|---|---|---|---|---|
| Diviser | oui | le panneau de la création, au rang : surface, courbe outil | — | oui | oui (drapeau) | oui (courbe, refus d'une courbe qui ne scinde pas) |
| Remplacer la face (solide) | oui | le panneau de la création, au rang : face, surface de remplacement | — | oui | oui (Tip du corps) | oui (surface : d'un ajout à une intersection) |
| Supprimer la face (solide) | oui | le panneau de la création, au rang : faces | — | oui | oui (Tip du corps) | oui (faces : ajout, intersection, les deux ; refus d'une zone vide) |
| Supprimer la face (surface) | oui | le panneau de la création, au rang : faces d'une même surface (une autre surface la change) | — | oui | oui (drapeau) | oui (faces, refus de toutes) |
| Annuler l'ajustement | oui | le panneau de la création, au rang : face de surface (une autre surface aussi) | — | oui | oui (drapeau) | oui (autre surface, refus d'une face inconnue) |
| Congé de surfaces | oui | le panneau de la création, au rang : arêtes (d'une même surface, qui peut changer), rayon (un pour toutes, comme à la création) | — | oui | oui (drapeau) | oui (rayon, arêtes, autre surface) |
| Aplatir | oui | le panneau de la création, au rang : face de surface (un clic sur une autre la remplace, sur une autre surface aussi) ; la déformation mesurée | — | oui | oui (drapeau) | oui (surface, face) |
| Forme libre | oui | le panneau de la création, au rang : surface (clic dans l'arbre ; les points poussés s'y reprojettent), points poussés, hauteurs, rayon, bords fixes | — | oui | oui (drapeau) | oui (surface, rayon) |
| Pôles | oui, avec sa surcouche dans la vue | surface (clic dans l'arbre ; les pôles déplacés gardent leurs indices), déplacements, pas de grille ; une autre face, en cliquant ses pôles | — | oui | oui (drapeau) | oui (surface) |
| Prolonger | oui | le panneau de la création, au rang : bord (ou la surface entière, pour tous ses bords ; un bord d'une autre surface la change), distance | — | oui | oui (drapeau) | oui (tous les bords, un bord, autre surface) |
| Ajuster | oui | le panneau de la création, au rang : outil, surface ajustée et partie gardée (un clic dessus) | ajustement mutuel (deux lignes : chacune se réédite seule) | oui | oui (drapeau) | oui (outil, partie gardée, autre surface, refus) |
| Courbe d'intersection | oui (ses traits) | le panneau de la création, au rang : les deux surfaces, ou une surface et le solide (« avec le solide ») | — | oui (ses traits) | oui (drapeau) | oui (seconde surface, solide, refus) |
| Projeter une courbe | oui (ses traits) | le panneau de la création, au rang : esquisse, face cible (la direction suit la normale de l'esquisse) | — | oui (ses traits) | oui (drapeau) | oui (esquisse, surface, refus) |
| Hélice 3D | oui (ses traits) | pas, hauteur, rayon, angle | axe, sens | oui (ses traits) | oui (drapeau) | oui (pas) |
| Courbe composite | oui (ses traits) | le panneau de la création, au rang : courbes et arêtes, bout à bout | — | oui (ses traits) | oui (drapeau) | oui (arêtes, refus d'arêtes qui ne se suivent pas) |
| Spline 3D | tracée dans la vue | complète : points, type, fermée, liens, tangentes | rien | tracée dans la vue | oui (drapeau) | oui |
| Esquisse 3D | tracée dans la vue | complète | rien | tracée dans la vue | oui (drapeau) | oui |

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

Un choix de création était définitif : il fallait supprimer et refaire.

Corrigé pour toutes : les surfaces lissée, balayée, frontière, réglée, de remplissage (le bouchon tangent compris), cousue et médiane, Diviser, Annuler l'ajustement, Supprimer la face d'une surface, la Courbe composite, Remplacer et Supprimer la face du solide, et les références (Plan, Axe, Point, Repère) : leur double-clic rouvre le panneau de la création (thème 4).

Une même fonction change de comportement selon un choix : le Remplissage est paramétrique sans tangence, figé avec. Les deux re-choisissent leur contour ; la case « tangent », elle, ne revient pas (thème 5).

Où ça se décide : `app/tree.js`, `editSurface` (aiguille par genre de surface) et `editFeature` (branches dédiées : Révolution et son enlèvement, Chanfrein, Chanfrein de sommet, Texte, Couper avec une surface, Supprimer des corps ; le reste tombe sur `get_params`) ; `engine/equations.py` (`_EDITABLE_PROPS`, liste blanche des cotes) ; `engine/vocab.py` (`PARAM_KEYS`) ; `engine/surfacefeat/commun.py` (ce qui est « figé »).

Contre-exemple à suivre : Supprimer des corps vient d'être rendu rééditable (panneau de la création rouvert, sa zone remplie de ce qu'elle vise, réécrit sur place sans changer de rang).

### 4. Les sélections qui ne reviennent pas

Arêtes, faces, profils, corps, directions, outils : presque aucun ne se re-choisissait.

Fait : chaque fonction qui se réédite re-choisit maintenant ce qu'elle a pris à la création, dans le panneau de sa création, sur la pièce à son rang. Ce qui ne revient toujours pas tient à des options (thème 5). Le détail, fonction par fonction :

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

Surfaces cousue et médiane, Remplacer et Supprimer la face du solide : des formes figées, recalculées sur leurs sources, sans réédition jusqu'ici (thème 3). Leur double-clic rouvre le panneau de la création, au rang : les surfaces d'une couture (un nom par défaut suit la peau, solide si elle se ferme) ; les deux faces d'une médiane, ou toutes les parois plus minces qu'une épaisseur, sans aperçu comme à la création ; les faces supprimées du solide ; la face remplacée et sa surface. La forme se recalcule sur la fonction d'avant. Le booléen qui la range suit : un ajout quand la matière ne fait que croître, une intersection quand elle ne fait que diminuer, les deux à la suite quand elle fait les deux (l'ajout se pose alors, caché, juste avant la fonction). Une surface qui vient après est refusée ; une forme que le modeleur ne sait pas faire aussi, la pièce restant telle quelle. `set_params` prend `surfaces` ; `faces` ou `thickness` ; `faces` ; `face` et `surface`. Selftest p133.

Plan, Axe, Point et Repère de référence : ils n'avaient aucune réédition (thème 3). Leur double-clic rouvre le panneau de la création, sur la pièce à leur rang. Comme toute ligne, la vue montre la pièce telle qu'elle les précède, la barre juste au-dessus d'elles (depuis #207, ce sont des lignes d'historique : thème 8). Le plan revient sur sa face, surlignée, ou sur son plan d'origine, avec son décalage et son angle et l'aperçu de son fantôme ; choisir un plan d'origine dans la liste vide la zone de face (à la création aussi), sinon la face l'emporte. L'axe revient sur son axe d'origine ou son arête ; le point, sur son sommet, le centre de son arête circulaire ou ses coordonnées ; le repère, sur son sommet ou ses coordonnées. Les quatre montrent leur fantôme, à la réédition comme à la création (thème 6). Une face, une arête ou un sommet se cliquent sur la fonction qui précède la référence ; un élément disparu de ce rang laisse la zone vide. Un plan dont la face a disparu reste alors où il est, tant qu'on ne clique pas une face ou ne choisit pas un plan d'origine ; un axe ou un point doit retrouver son appui. Les refus de la création valent aussi (un centre demande une arête circulaire). `set_params` prend `face` ou `base`, `offset` et `angle` ; `edge` ou `axis` ; `vertex`, `edge` ou `point` ; `vertex` ou `point`. Selftest p134.

Répétition variable : son graphe se réédite dans l'éditeur de graphe, dont le bouton « Fonctions » ferme l'éditeur (la question vient d'abord si le graphe n'a pas été appliqué) et rouvre la zone de la création, au rang, remplie des fonctions répétées. Un clic dans l'arbre en retire une ou l'ajoute au bout : l'ordre compte, le groupe se rejoue dans l'ordre de la zone. Le graphe ou les instances enregistrés restent ; des cotes d'instance qui visent une fonction retirée font refuser la réédition, comme une fonction qui vient après la répétition (elle en dépend). `set_params` prend `features`. Selftest p131.

Indices de face ou d'arête, vérifiés quand l'esquisse amont change de topologie (un trou, un segment ajouté au début, qui décalent l'ordre des faces et des arêtes). Le Congé et le Chanfrein, la Surface radiée sur des arêtes de la pièce, le Congé de surfaces suivent leurs arêtes : le nommage topologique de FreeCAD 1.x remet les indices. Le Prolongement range son bord comme un côté de la surface, l'Ajuster sa partie gardée comme un morceau de la découpe : rien ne se décale. Les pôles d'une forme libre et la face d'un patron à plat gardaient l'indice de leur face : quand l'ordre changeait, les déplacements passaient en silence sur une autre face. Chaque face réglée garde maintenant un point de repère pris à l'intérieur, et ses réglages retrouvent la face la plus proche ; repères et indices se remettent à jour quand la surface source change. Selftest p127.

Où ça se décide : `app/tree.js`, `editAtRank`, rouvre le panneau de la création sur la pièce au rang de la fonction (`rank_view`), ses zones remplies de ce que l'arbre décrit (`app/features/*.js`, les fonctions `…Pick` et `…EditValues`), et n'envoie que ce qui change. Le moteur remplace les sélections dans `set_params` (`engine/equations.py` aiguille selon la fonction : `engine/surfacefeat/reedition.py` pour les surfaces et les courbes, `_set_surface_cut_params`, `_set_combine_params`, `_set_swept_params`, `_set_pattern_picks`, `_set_body_pattern_picks`, `edit_repeat_feature`, `_set_reference_params` dans `engine/refgeom.py`…), tout ou rien, et refuse en la nommant une forme qui vient après ou qui dépend de la fonction.

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

Depuis le 2026-11-13, toute fonction qui fabrique une forme nouvelle a son fantôme jaune à la création et à la réédition.

- **À la création** : les surfaces, les opérations sur surfaces et courbes, l'Axe, le Point et le Repère ont maintenant leur aperçu (`preview=True` côté moteur). Une surface montre ses faces ; une courbe (intersection, projection, hélice 3D, composite) montre ses traits ; une référence montre son fantôme, comme le plan. Le moteur crée la fonction dans une transaction qu'il annule aussitôt : le document ne change pas (p135, 27 créations).
- **Spline 3D et Esquisse 3D** : un mode d'édition dans la vue, à la création comme à la réédition ; le tracé en cours tient lieu d'aperçu.
- **Absences voulues** : Combiner (booléen lent sur des corps entiers), la Surface médiane (sa forme figée se calcule sur toutes les parois), Supprimer des corps (aucune forme nouvelle : ce qu'elle retire est sa sélection, déjà surlignée), les fonctions graphe et la Répétition variable (un graphe peut contenir du Python, qui ne s'exécute qu'après autorisation, à l'application ; un aperçu le lancerait à chaque saisie ; à la création, le graphe minimal ne montre rien).
- **À la réédition** : les Pôles prévisualisent leurs déplacements ; la Répétition de corps montre ses copies (branche `FreeSolidBodyPattern` de l'aperçu) ; une surface rééditée par `set_params` montre la surface elle-même ; une référence rééditée montre son fantôme.
- **Bulle de rayon du Congé** : présente à la création et à la réédition.
- **Flèche de profondeur** : Extrusion, Enlèvement, Surface extrudée, Perçage borgne (au fond du premier trou) et Hélice (au bout de sa hauteur, le long de l'axe de son esquisse), à la création comme à la réédition (p136). La Révolution n'en a pas, voulu : sa cote est un angle, pas une profondeur.
- **Entrées du menu de la vue** : entrées dédiées pour l'Extrusion, l'Enlèvement et la Révolution seulement. C'est un écart d'accès, pas d'aperçu.

Où ça se décide : `app/main/featurepanel.js` (branche l'aperçu sauf `preview:false`, et la flèche : `extrudeDepthHandle`, `holeDepthHandle`, `helixDepthHandle` à la création, `editDepthHandle` à la réédition) ; `app/features/*.js` (le drapeau `preview:false` de chaque entrée) ; `engine/ops/*.py` (`preview=True` de chaque opération, relevé dans `tests/ops_instantane.json`) ; `engine/kernel.py` (`preview` : corps, surfaces, courbes et références) ; `app/tree.js` (un `onChange` par panneau de réédition) ; `app/main.js` (`showGhost`, `ghostLines`, `showReferenceGhost`) ; `engine/directedit.py` (`feature_drag_info`, `face_frame`, `sketch_frame`, `_depth_editable`).

### 7. Le sens dit de plusieurs façons

- **Surface décalée, Surface radiée, Épaissir** : la décalée et la radiée ont maintenant la même case à la création et à la réédition (« Inverser le côté », « Vers l'intérieur »), et la radiée est libellée « Distance ». Épaissir n'a pas de case : le signe de l'épaisseur, aux deux moments. Une radiée dont la distance est pilotée par une équation garde le panneau des cotes, où le sens reste le signe.
- **Texte** : « Hauteur », « Décalage X/Y » à la création, « Taille », « X », « Y » à la réédition.
- **Hélice** : l'angle n'existe qu'à la réédition.
- **Dépouille** : libellé « Faces à dépouiller » au pluriel pour une seule face, alors que la Coque en accepte plusieurs.

Où ça se décide : `app/features/surfaces.js`, `habillage.js`, `volumes.js` (panneaux de création) ; `app/tree.js` (libellés de réédition, `PARAM_LABELS_BY_KIND` et le panneau Gravure) ; `engine/vocab.py` (`PARAM_KEYS`).

### 8. Barre de retour : des lignes qui n'y entrent pas comme les autres

- **Références** (Plan, Axe, Point, Repère) : depuis le 2026-11-13, ce sont des lignes comme les autres. La barre se pose sous elles et elles reculent avec elle, par drapeau comme une esquisse libre. Reculées, la vue ne les dessine plus et une esquisse neuve ne se pose pas sur un plan reculé. « Changer de plan… » ne propose que les plans qui précèdent l'esquisse. Supprimer ce qui est sous la barre les emporte (p137).
- **Chanfrein de sommet, Supprimer et Remplacer la face du solide** : une seule ligne chacun, qui recule comme une fonction. Leur forme figée partait de la fonction qui les précédait *à leur création*. Une fonction posée sous la barre reculée au-dessus d'elles n'y entrait donc pas : un bossage disparaissait, une poche se rebouchait. Depuis le 2026-11-13, la forme part de la fonction juste avant elles, et leurs faces ou leur sommet sont retrouvés sur cette forme par leur géométrie (p138).
- **Épaissir** : classée avec les surfaces (barre par drapeau) alors que son résultat est un solide ; Couper avec une surface est une fonction de corps (barre par le Tip). Pas d'écart de comportement constaté.
- **Cousue et Médiane** : vérifié à l'exécution (2026-11-13). Rééditées sous la barre, leurs sources les entraînent et rien n'est sauté (p138 pour la couture). Un écart reste, sans lien avec la barre : quand le recalcul échoue (une face qui n'existe plus), la surface garde son ancienne forme sans le dire.
- **Remplacer et Supprimer la face du solide** : seules opérations de leur famille dans la chaîne du corps ; elles ne se masquent pas.
- **Ajustement mutuel** : deux lignes indépendantes, rééditer l'une ne touche pas l'autre.

Où ça se décide : `engine/tree.py` (`_history_role`, `set_tip`, `_rolled_back_objects`) ; `engine/kernel.py` (`_ROLLBACK_ROLES`, `rollback_plan`) ; `engine/sketch.py` (`_datum_support`) ; `app/sketchplane.js` (`sketchPlaneOptions`) ; `engine/surfacefeat/commun.py` (`_refresh_frozen_shapes`) ; `engine/surfacefeat/solide.py` (`_frozen_chain_base`, `_rebase_frozen`) ; `engine/surfacefeat/prolonger.py`.

### 9. Le rejeu et la documentation

- **Rejeu** : `no_replay` est périmé pour l'Hélice. La raison dit « Pitch/Height hors whitelist », or ces deux cotes sont dans la liste de `get_params`. `engine/replay.py` la classe encore comme rejouable sous condition. Lissage, Balayage, Texte, Combiner, les trois répétitions de fonctions et de corps, les fonctions graphe, le Chanfrein de sommet, les références et la Spline 3D sont non rejouables, pour des raisons de fond. Ce que fait le rejeu d'une opération de surface (sans `replay` ni `no_replay`) : à vérifier.
- **Documentation** : corrigé le 2026-11-13. Les sections détaillées de `docs/ecarts-solidworks.md` (où Extrusion, Enlèvement et Révolution paraissent sans conditions de fin ni axe) sont marquées comme le relevé de la v0.1.3 ; ce qui a été fait depuis est dans son tableau de suivi. L'écart n° 70 de ce tableau renvoie ici pour les surfaces et l'habillage.

Où ça se décide : `engine/ops/volumes.py`, `habillage.py`, `references.py`, `surfaces.py`, `noeuds.py`, `repetitions.py` ; `engine/replay.py` ; `tests/` (le test de cohérence ne couvre que les opérations `add_*`).

### 10. La couverture du selftest

Aucune étape de réédition dans `engine/selftest/` pour : Enlèvement extrudé, Enlèvement de révolution, Hélice (volume), Répétition circulaire (fonctions et corps), Symétrie, Surface de révolution. Les références (p134), Diviser, Annuler l'ajustement, la Courbe composite (p132), Remplacer et Supprimer la face (p133) en ont maintenant une. Les clés de quatre surfaces ne sont vérifiées que par un test unitaire (`tests/test_param_keys.py`). Ce qui n'a pas de réédition n'a pas de test de bout en bout ; que l'arbre et `get_params` disent la même chose est vérifié par l'étape p87, et le choix de l'éditeur par `tests/js/editkind.test.mjs`.

L'aperçu à la création des surfaces, courbes et références est vérifié par p135 (chaque création montre quelque chose et laisse le document intact) ; les flèches du perçage et de l'hélice, par p136.

La barre de retour est testée sur les références (p137), sur les formes figées du corps et sur une couture (p138). Aucun selftest ne vise encore la barre sur les autres surfaces et courbes, ni Masquer (testé seulement sur des corps). Désactiver n'est pas testé fonction par fonction.

Où ça se décide : `engine/selftest/fonctions.py`, `document.py`, `surfaces.py`, `noeuds.py`, `esquisse.py` ; `tests/test_param_keys.py` ; `tests/js/` pour le côté interface.
