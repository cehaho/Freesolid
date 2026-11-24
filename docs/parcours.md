# Parcours de pièces réelles

Chaque pièce est construite entièrement à la souris, dans l'interface,
en 1366 × 768. Chaque accroc est noté puis corrigé, ou laissé avec une
raison. Branche `parcours`.

## 1. Équerre percée

Profil en L sur le Plan de face (60 × 40, épaisseur 8), extrusion de
40 mm, deux trous de 6 mm dans l'aile, congé de 5 mm à l'angle intérieur.

| # | Accroc | Suite |
|---|---|---|
| 1 | « Nouvelle pièce » remplace la pièce en cours sans rien demander, modifications perdues. | **Corrigé** : nouveau, ouvrir, nouvel assemblage et récents demandent confirmation si le document a changé depuis son enregistrement (`document_status`). |
| 2 | Le premier clic sur l'origine ne s'y accroche pas : le profil flotte (2 degrés de liberté de trop). | **Corrigé** : l'origine est un point d'accrochage, et le moteur pose une coïncidence avec le point racine (lignes, arcs, centres de cercle). |
| 3 | Panneau Extrusion : le focus va sur la liste « Borgne », pas sur la profondeur. | **Corrigé** : focus sur la première valeur à taper. |
| 4 | Perçage : la face choisie est ignorée ; il faut d'abord une esquisse de cercles. | **Corrigé** : ligne « Positions », chaque clic sur la face pose un centre ; le moteur crée l'esquisse et le perçage d'un coup. |
| 5 | La barre d'icônes contextuelle reste par-dessus quand une commande s'ouvre. | **Corrigé**. |
| 6 | Le message d'un aperçu raté reste après un aperçu réussi. | **Corrigé**. |
| 7 | Le focus sur une valeur ne la sélectionne pas : « 5 » tapé sur « 3 » donne 35. | **Corrigé** : la valeur est sélectionnée. |
| 8 | Une fonction refusée par le moteur ferme le panneau : la saisie est perdue. | **Corrigé** : le panneau revient avec les valeurs saisies. |
| 9 | Barre d'état sur deux lignes avec un message long. | **Corrigé** : une ligne, texte abrégé, entier au survol. |
| 10 | Le message garde « (BRep_API: command not done) ». | **Corrigé** : ce générique du modeleur n'est plus recopié. |
| 11 | Après un refus puis une réussite, l'erreur rouge reste affichée. | **Corrigé** : une opération réussie l'efface. |
| — | Deux onglets sur le même serveur partagent le même document. | Voulu (un document par processus) ; à afficher un jour. |
| — | Les symboles de relations (H, V) se chevauchent sur deux segments proches. | **Corrigé** : comme dans les modeleurs courants, chaque symbole se pose à côté de son entité sans rien couvrir — s'il tombe sur un autre symbole, un trait de l'esquisse, une ligne ou une étiquette de cote, il glisse le long de l'entité, change de côté, puis s'éloigne ; sans place libre, il prend celle qui gêne le moins. |
| — | Entrée applique la valeur puis une seconde Entrée valide. | Voulu : on voit l'aperçu avant de valider. |

## 2. Boîtier

Rectangle par le centre 100 × 60 sur le Plan de dessus, coté ; extrusion
de 40 mm ; congés de 8 mm sur les quatre arêtes verticales ; coque de
2 mm ouverte sur le dessus ; chanfrein de 1 mm sur le bord extérieur.

| # | Accroc | Suite |
|---|---|---|
| 12 | Le rectangle par le centre n'est pas tenu par son centre (4 degrés de liberté au lieu de 2), et il coûte quatre Ctrl+Z (un par côté). | **Corrigé** : `sketch_add_rectangle`, une seule opération ; centré sur l'origine, ses coins y restent symétriques (selftest p42). |
| 13 | La barre d'icônes contextuelle passe par-dessus la boîte d'orientation. | **Corrigé**. |
| 14 | Après une reconstruction, la barre d'état cite encore « sél. 4 arête(s) ». | **Corrigé**. |
| 15 | Pendant l'aperçu de la coque, la face choisie reste orange et cache l'ouverture. | **Corrigé** : la face choisie s'estompe avec la pièce. |
| 16 | Juste après l'ouverture d'un panneau, Entrée ne valide pas : le premier aperçu marquait le champ comme modifié (tous les panneaux). | **Corrigé**. |
| — | La cote verticale recouvre le symbole « V » du côté coté. | **Corrigé** : comme dans les modeleurs courants, chaque symbole se pose à côté de son entité sans rien couvrir — s'il tombe sur un autre symbole, un trait de l'esquisse, une ligne ou une étiquette de cote, il glisse le long de l'entité, change de côté, puis s'éloigne ; sans place libre, il prend celle qui gêne le moins. |
| — | Les flèches gauche/droite tournent autour de l'axe vertical de l'écran : douze appuis montrent la pièce par-dessous. Une rotation autour de l'axe Z de la pièce serait plus naturelle. | À discuter. |
| — | Sélectionner une arête cachée oblige à tourner la vue (pas de vue isométrique arrière dans la boîte d'orientation). | À discuter : vues isométriques des quatre coins. |
| ✓ | Le chanfrein d'une arête suit toute la chaîne tangente (côtés et arrondis). | Bon comportement. |

## 3. Arbre étagé

Demi-profil sur le Plan de face (Ø 24 sur 30 mm, Ø 16 sur 40 mm), révolution
autour de l'axe vertical de l'esquisse ; gorge de circlip par un rectangle
de 2 × 1,5 mm et un enlèvement par révolution ; chanfrein de 1 mm au bout.

| # | Accroc | Suite |
|---|---|---|
| 17 | Esquisse sur un plan qui traverse la pièce : le solide cache les traits (ils étaient « devant », mais la pièce, transparente pour l'aperçu, était dessinée après). | **Corrigé** : les traits, cotes et points d'esquisse passent dans la même passe, devant la pièce. |
| 18 | Un trait vertical traverse chaque cylindre : la couture interne du noyau, tracée comme une arête. | **Corrigé** : les arêtes de couture ne sont plus tracées (selftest p43) ; les ids des autres restent ceux du noyau. |
| 19 | Titre de panneau coupé (« Enlèvement par r… »). | **Corrigé** : il passe sur deux lignes. |
| — | Sur une petite entité, les symboles H/V recouvrent tout le tracé. | **Corrigé** : comme dans les modeleurs courants, chaque symbole se pose à côté de son entité sans rien couvrir — s'il tombe sur un autre symbole, un trait de l'esquisse, une ligne ou une étiquette de cote, il glisse le long de l'entité, change de côté, puis s'éloigne ; sans place libre, il prend celle qui gêne le moins. |
| — | Après la première fonction, la vue n'est pas recadrée sur la pièce (F le fait). | À discuter : cadrer automatiquement après la première fonction. |
| — | Positionner exactement un profil (la gorge) demande de le coter ; pas de cote entre un point et l'origine testée ici. | À vérifier au prochain parcours. |

## 4. Bride

Disque Ø80 × 12 sur le Plan de dessus, moyeu Ø40 jusqu'à 32 mm, alésage
Ø20 débouchant, un trou Ø8 sur un cercle de perçage de 60 répété six fois
autour de l'axe Z, puis une nervure triangulaire (16 × 16, épaisseur 6,
plan milieu) sur le Plan de face et sa symétrique par le Plan de droite.

| # | Accroc | Suite |
|---|---|---|
| 20 | Perçage : un clic au centre du moyeu pose le trou à 2 mm du centre ; rien n'aimante la position. | **Corrigé** : le moteur envoie le centre exact des arêtes circulaires ; un clic de position s'y aimante (et aux sommets) à moins de 12 px, dans le plan de la face (selftest p43). |
| 21 | L'outil Cotation ignore l'origine : cercle puis origine donne un Ø, pas la distance. | **Corrigé** : l'origine se sélectionne et se cote ; un cercle coté contre un point se prend par son centre. |
| 22 | Pas de relation horizontale / verticale entre deux points (centre de trou et origine). | **Corrigé** : proposée dès que deux points sont sélectionnés, origine comprise. |
| 23 | Seules les cotes alignées existent : impossible de placer un sommet à 20 mm en X et 12 mm en Y de l'origine. | **Corrigé** : entre deux points, un 3e clic pose la cote, avec aperçu ; à côté : verticale, dessus ou dessous : horizontale, entre : alignée (selftest p44). |
| 24 | Les cotes s'empilent au même endroit et cachent la pièce ; elles ne restent pas où on les pose. | **Corrigé** : le clic de pose devient le décalage de la ligne de cote, gardé par la pièce et sauvé avec elle. |
| 25 | Répétition ou symétrie après avoir cliqué une fonction dans l'arbre : la case « Fonctions à répéter » reste vide. | **Corrigé** : la fonction présélectionnée remplit la case (répétitions, symétrie, réseau variable) ; à 3 fonctions et plus, la case dit « fonctions », plus « profils ». |
| — | La barre d'icônes de la face restait au milieu d'une esquisse ouverte et prenait les clics. | **Corrigé** sur `qualite` (smoke de la PR #90). |
| — | L'esquisse d'un perçage reste « sous-contrainte » : son rayon, piloté par le diamètre du perçage, n'est pas coté. | **Corrigé** : comme dans les modeleurs courants, l'esquisse d'un perçage ne fixe que les positions ; le rayon de ses cercles, tenu par le diamètre du perçage, ne compte plus comme libre. Centres cotés, elle est totalement contrainte (selftest p41). |
| 26 | Une cote déjà posée ne se déplace pas à la souris. | **Corrigé** : avec l'outil Sélectionner, on glisse son étiquette ; elle reste sous le curseur, la valeur ne change pas, Ctrl+Z annule (`sketch_place_dim`). |
| 27 | Cotation incomplète : pas de rayon d'un cercle, pas de cercle + ligne, et la longueur d'une ligne oblique toujours alignée. | **Corrigé** — l'outil Cotation choisit d'après ce qu'on clique : une ligne → sa longueur (le clic de pose choisit horizontale, verticale ou alignée, avec aperçu) ; un cercle → Ø, un arc → R, un cercle puis son centre → R ; deux points → H/V/alignée ; point + ligne → distance ; deux lignes → distance si parallèles, sinon angle ; cercle + point, ligne ou cercle → depuis son centre (selftest p44). |
| — | Traits d'esquisse définis (clairs) peu contrastés sur une face claire. | **Corrigé** : quand les traits sont plus clairs que la pièce (thème sombre), chacun porte un liseré couleur du fond, comme le halo des étiquettes de cote ; lisible sur la face comme sur le fond. Thème clair inchangé (traits sombres). |
| 28 | Étiquettes de cote en gros pavés gris, flèches en V épaisses. | **Corrigé** : texte seul de 12 px, net, halo du fond ; pointes pleines et fines ; l'étiquette se place à côté de sa ligne. |
| 29 | La cote d'angle faisait pivoter les lignes quand on les cliquait dans le sens horaire, et se dessinait au point de rencontre, parfois loin d'elles. | **Corrigé** : lignes ordonnées dans le sens trigonométrique (selftest p44 : rien ne bouge) ; l'arc passe là où on a cliqué la 2e ligne, attaches si besoin, et se glisse comme les autres cotes. |

## 5. Raccord carré → rond, coudé

Carré 60 × 60 sur le Plan de dessus et cercle Ø40 sur un plan de référence
à 50 mm, lissage ; creux de 2 mm par lissage-enlèvement des profils
projetés et décalés (la coque échoue, voir 33) ; tube coudé par balayage
d'un anneau R20/R18 le long d'un chemin en L de 40 × 50 arrondi à R20.

| # | Accroc | Suite |
|---|---|---|
| 30 | Saisie au clavier pendant le tracé : l'aperçu reste affiché après la pose, et les valeurs tapées ne deviennent pas des cotes (esquisse sous-contrainte). | **Corrigé** : l'aperçu disparaît ; largeur, hauteur, longueur ou rayon tapés deviennent des cotes. |
| 31 | Plan de référence : aucun aperçu avant de valider. | **Corrigé** : le moteur pose le plan dans une transaction annulée et renvoie sa position ; le client l'affiche en translucide (selftest p45). |
| 32 | Sans solide, le plan de référence validé tombe sous la barre de retour, grisé. | **Corrigé** : un plan, un axe ou un point de référence se range comme une esquisse libre. |
| 33 | Coque sur le lissage carré → rond : échec, message brut du modeleur en anglais. | **Limite du noyau** (arête vive qui devient tangente) ; **message clair** qui donne le contournement : enlèvement par lissage des profils décalés. |
| 34 | Décaler des arêtes projetées : les originaux restent dans le profil. | **Corrigé** : option « Originaux en construction », cochée d'office pour des arêtes projetées. |
| 35 | Décaler : le côté dépend de l'ordre des arêtes (cercle vers l'intérieur, carré vers l'extérieur), sans aperçu. | **Corrigé** : contour fermé vers l'extérieur par défaut, « Inverser le côté » vers l'intérieur, aperçu de la copie (selftest p17). |
| 36 | Congé d'esquisse et polygone : boîte système `prompt()` ; dans le navigateur intégré elle se ferme d'office et le congé est perdu sans message. | **Corrigé** : panneau d'outil (Rayon, Nombre de côtés), l'outil reste actif pour plusieurs coins. |
| 37 | Congé d'esquisse : les cotes des deux lignes disparaissent. | **Corrigé** : le coin reste en point de construction, les cotes s'y rattachent, le rayon est coté (selftest p17). |
| 38 | Esquisse rééditée : la vue ne cadre que la pièce, le haut du chemin est hors écran. | **Corrigé** : la vue englobe le contenu de l'esquisse à l'ouverture. |
| 39 | « Esquisse fermée — contour ouvert » : fermée et ouvert dans la même phrase. | **Corrigé** : « Esquisse terminée — profil non fermé… ». |
| — | Rayons de deux cercles concentriques : étiquettes superposées. | **Corrigé** : comme les longueurs, une cote de rayon ou de diamètre se pose là où on clique et se glisse autour du cercle (l'angle est gardé avec la pièce) ; sans pose, les cercles de même centre partent dans des directions décalées (selftest p44). |
| — | L'anneau du haut (2 mm) est difficile à viser ; pas de vue de dessous dans la barre (Ctrl+6 marche). | **Corrigé** : sur une face, une arête ne gagne que si le curseur est presque sur son trait (3 px ; 8 px sur le fond) — l'anneau mince se vise sur presque toute sa largeur. La barre de vue porte « Orientation de la vue », qui ouvre sous elle la boîte des vues standard, dessous compris (comme la touche Espace). |

## 6. Support à nervure

Semelle 80 × 50 × 6 sur le Plan de dessus, paroi 80 × 6 de 40 mm sur
son bord arrière, nervure de 6 mm (une ligne sur le Plan de droite),
deux perçages de 6 mm cotés à ± 25 / − 10 de l'origine, congés R5 sur
les coins avant, puis la paroi passée à 50 mm (tout suit).

| # | Accroc | Suite |
|---|--------|-------|
| 40 | Esquisse sélectionnée dans l'arbre (celle des positions d'un perçage), puis bouton Esquisse : une nouvelle esquisse demande un plan au lieu de rouvrir la sélectionnée. | **Corrigé** : comme dans les modeleurs courants, Esquisse rouvre l'esquisse choisie dans l'arbre (le même geste que « Modifier » de son panneau, qui se ferme). |
| 41 | Réseau linéaire de la nervure : refusé (« pas une fonction additive ou soustractive »). | **Corrigé** : la nervure est maintenant une fonction additive dont le moteur pose la forme et la matière ajoutée ; réseaux linéaire et circulaire, symétrie et répétition pilotée par esquisse la répètent comme un bossage, et les copies suivent sa réédition (selftest p164). Une nervure d'un fichier plus ancien garde l'ancien rangement : la recréer pour la répéter. |

## 7. Capot coqué

Rectangle centré 100 × 60 sur le Plan de dessus, extrudé de 30 mm ;
congés R10 sur les quatre arêtes verticales, coque de 2 mm ouverte
par-dessous ; bossage Ø16 × 10 sur le dessus, sa symétrie par le Plan
de droite, chanfreins de 1 mm en tête des bossages ; une fente de la
paroi avant répétée 5 fois au pas de 8 mm, puis le bloc passé à 40 mm
(tout suit).

| # | Accroc | Suite |
|---|--------|-------|
| 42 | Panneau Coque ouvert, curseur dans l'Épaisseur : Ctrl+6 ne fait rien ; la face cliquée ensuite est celle du dessus, et la coque s'ouvre du mauvais côté. | **Corrigé** : comme dans les modeleurs courants, Ctrl+1…8 (vues standard, normal à) marchent même le curseur dans un champ — une saisie ne s'en sert jamais. |
| 43 | Fonction cliquée dans l'arbre, puis Symétrie : « Fonctions à répéter » reste vide (seul le repli « la dernière » sauvait le résultat). | **Corrigé** : ouvrir une commande efface les cotes affichées mais garde la fonction choisie, que le panneau prend d'emblée (répétitions, symétrie). |

## 8. Flasque tournée

Profil en L sur le Plan de face — moyeu Ø20…40 de 25 mm, flasque
Ø100 de 8 mm — tourné autour de l'axe vertical ; un perçage Ø6 sur la
flasque répété 6 fois autour de l'axe, congé R3 au pied du moyeu, puis
le moyeu coté à 35 mm dans l'esquisse rééditée (tout suit).

| # | Accroc | Suite |
|---|--------|-------|
| 44 | Congé au pied du moyeu : l'arête ne se clique que sur ses côtés ; de face, c'est l'arête voisine (le haut de la flasque, à quelques pixels) qui prend la sélection, ou la face entière. | **Corrigé** : sur une face, l'arête retenue est la première de cette face sous le curseur, plus seulement la première trouvée. |
| 45 | Face de la flasque cliquée, puis Perçage : le panneau redemande les centres des trous. | **Corrigé** : comme dans les modeleurs courants, le point cliqué sur la face présélectionnée devient la première position (aimanté comme un clic dans le panneau). |

## 9. Bielle

Deux cercles (R20 à l'origine, R12 à 80 mm) reliés par deux lignes
tangentes, arcs intérieurs ajustés, esquisse totalement contrainte ;
extrusion de 10 mm plan milieu, perçages Ø16 et Ø8 aux centres des
bossages (face cliquée puis Perçage), allègement en rainure de 5 mm de
profondeur, puis l'entraxe passé à 90 mm.

Vérifié dans SolidWorks (par son API) : un point accroché au quadrant
d'un cercle y garde « Coïncidente » et « Verticale » avec le centre — la
tangence ajoutée ensuite ne le fait pas glisser. FreeSolid fait de même :
pas d'accroc.

| # | Accroc | Suite |
|---|--------|-------|
| 46 | Petit arc glissé dans l'esquisse : l'ancien tracé (ligne, bout d'arc) reste dessiné sous le nouveau, même après un rechargement. | **Corrigé** : la forme 3D de l'esquisse ouverte, recalculée à la fermeture seulement, ne se dessine plus pendant son édition. |
| 47 | Face cliquée puis Esquisse : un gros point bleu au milieu de l'esquisse — la flèche pour tirer la face, vue de face. | **Corrigé** : la flèche part avec la sélection de la face. |
| 48 | Esquisse neuve quittée par ✗ : elle reste, vide, dans l'arbre. | **Corrigé** : la pile d'annulation de FreeCAD est bornée (20 pas) ; pleine, le compte ne bougeait plus et rien n'était défait. Les pas défaits sont ceux de la session d'esquisse, puis sa création (selftest p79). |
| 49 | Entraxe passé de 80 à 90 : le perçage du petit bossage reste à 80. | **Corrigé** : comme dans les modeleurs courants, un centre aimanté au centre d'un bossage y reste lié et le suit (selftest p168). |

## 10. Plaque de base

Rectangle par le centre 120 × 80 sur le Plan de dessus, coins arrondis
(congé d'esquisse R10), extrusion de 12 mm ; perçage lamé Ø9 / Ø15
prof. 6 au centre d'un arrondi (le clic s'y aimante), répétition linéaire
2 × 2 (100 × 60) ; rainure par le centre 50 × 16 sur l'origine, enlevée
sur 6 mm ; chanfrein de 1 sur le contour du dessus (arêtes tangentes
prises d'un clic). Puis la largeur passée à 140 : le lamage suit
l'arrondi (#285), les copies gardent leur pas de 100 — comme dans les
modeleurs courants.

| # | Accroc | Suite |
|---|--------|-------|
| 50 | Congé d'esquisse : un clic sur le sommet du coin est pris pour une première ligne ; il faut cliquer les deux lignes. | **Corrigé** : un clic sur le sommet où deux lignes se joignent arrondit (ou chanfreine) le coin ; les deux lignes restent possibles. |
| 51 | Rainure par le centre posée sur l'origine, à l'horizontale : aucune relation, 5 degrés de liberté au lieu de 2, pas d'axe. | **Corrigé** : les deux outils de rainure gardent leurs accrochages (centres des bouts, milieu, axe horizontal ou vertical) et tracent une ligne d'axe entre les centres (selftest p169). |
| 52 | Congé, chanfrein : une face cliquée est remplacée par l'arête cliquée ensuite, et un second clic sur la face ne la retire pas. | **Corrigé** : comme dans les modeleurs courants, arêtes et faces se mélangent dans la zone ; un second clic retire l'une ou l'autre. Création, réédition et rejeu les prennent ensemble (selftest p170). |
| 53 | Répétition linéaire : la direction 2 n'a pas de flèche dans la vue. | Laissé : la vue n'a qu'une poignée de glisser à la fois ; le pas se règle dans le panneau. |
| — | Esquisse de la rainure nommée Esquisse3 (Esquisse2 est celle des positions du perçage). | Voulu : comme dans les modeleurs courants. |

## 11. Palier à semelle

Semelle 100 × 15 sur le Plan de face, milieu du bas sur l'origine,
extrudée en plan milieu sur 50 ; arche (deux lignes, arc tangent R22,
centre à 45 au-dessus de l'origine) extrudée en plan milieu sur 30 ;
alésage Ø25 à travers tout, le clic s'aimante au centre de l'arc ; trou
de fixation Ø9 sur la semelle, placé à X = −40 dans son esquisse de
positions, puis symétrie par le Plan de droite ; congé R3 sur le raccord
de l'arche. Puis la semelle passée à 60 de profondeur : trous, symétrie
et congé suivent — comme dans les modeleurs courants.

| # | Accroc | Suite |
|---|--------|-------|
| 54 | Perçage : la position cliquée ne se cote pas pendant la fonction ; il faut valider, puis éditer l'esquisse de positions pour la coter. | **Corrigé** (#292) : comme dans les modeleurs courants, chaque position montre ses deux coordonnées dans le plan de la face ; une valeur tapée devient une cote de l'esquisse de positions (selftest p171). |

## 12. Poignée

Trajectoire en U sur le Plan de face — deux lignes de 40, arc tangent
R30, pieds symétriques par une ligne d'axe et à hauteur de l'origine ;
profil Ø10 sur le Plan de dessus, au pied gauche ; balayage ; deux
embases Ø16 de 4 mm sous les pieds (le centre s'aimante au bord du
tube) ; perçage Ø5 borgne de 10 dans une embase, coordonnées tapées,
puis symétrie par le Plan de droite. Puis les jambes passées à 50 :
balayage, embases, trous et symétrie suivent — comme dans les
modeleurs courants.

| # | Accroc | Suite |
|---|--------|-------|
| 55 | Outil Ligne : la touche A ne passe pas en arc tangent depuis le dernier point ; elle quitte la polyligne et ouvre l'Arc 3 points. | **Corrigé** (#301) : comme dans les modeleurs courants, A passe en arc tangent depuis le bout de la polyligne ; l'arc posé, la ligne reprend ; A de nouveau revient à la ligne. |
| 56 | Arc tangent : pas d'aperçu pendant le tracé ; la console répète « Buffer size too small for points data ». | **Corrigé** (#296) : three (0.163 et après) n'agrandit pas un tampon réécrit en place ; l'aperçu reçoit une géométrie neuve à chaque mouvement. |
| 57 | Profil sur le Plan de dessus : le centre ne s'accroche pas à l'extrémité de la trajectoire (une autre esquisse) ; il faut une relation et une cote. | **Corrigé** (#300) : les sommets des esquisses visibles faites avant, posés dans le plan, accrochent ; le point y est lié par une référence (selftest p173). |
| 58 | Balayage : le panneau s'ouvre avec un message d'erreur rouge avant tout choix. | **Corrigé** (#299) : tant qu'une zone de sélection est vide, le message guide au lieu d'être une erreur — pour toutes les commandes. |
| 59 | Après le balayage, la trajectoire reste à la racine de l'arbre, visible, « Utilisée par : libre » ; seul le profil se range sous Balayage1. Visible, sa ligne prend les clics sur les embases. | **Corrigé** (#295) : comme dans les modeleurs courants, toutes les esquisses d'un balayage ou d'un lissage se rangent sous lui (selftest p172). |
| 60 | Outil Diamètre : la cote se pose au clic sans demander sa valeur (l'outil Cotation la demande) ; le chiffre tapé ensuite est perdu. | **Corrigé** (#297) : Diamètre, Longueur d'arc et Angle à l'axe ouvrent la saisie de valeur, comme Cotation. |
| 61 | Perçage en cours : un clic sur une ligne d'esquisse visible ferme le panneau et ouvre les propriétés de l'esquisse ; la saisie est perdue. | **Corrigé** (#294) : une commande qui ne prend pas d'esquisse les traverse ; le clic va à la face derrière, le panneau reste. |
| 62 | Face cliquée puis Perçage : la position venue de la face n'a pas ses champs X / Y (#292) ; un clic dans le panneau les a. | **Corrigé** (#298) : la position porte la normale de la face ; ses champs X / Y s'affichent. |
| 63 | Perçage : un clic sur la seconde embase (autre face, même plan) remplace la position au lieu de l'ajouter ; il faut une symétrie. | **Corrigé** (#302) : les faces au même plan reçoivent les trous d'un même perçage ; chaque centre aimanté reste lié à son embase (selftest p174). |
| — | Les relations se posent sur une sélection faite avant (Ctrl+clic pour ajouter), et les axes de l'origine ne se cliquent pas : une ligne d'axe sert de symétrie. | Voulu : comme dans les modeleurs courants. |
