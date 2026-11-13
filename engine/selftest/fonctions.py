"""Selftest — fonctions volumiques : extrusions, révolutions, habillage,
répétitions, perçage, références.

Une fonction par étape, dans l'ordre d'exécution ;
``engine/selftest/__init__.py`` fixe l'ordre global.
"""

import math
import os

from engine.kernel import KernelError


def m0_piece_esquisse_bossage(self, mark, report, etat):
    mark("m0: pièce + esquisse contrainte + bossage")
    tree = self.new_part("Pièce de test")
    report["m0_planes"] = [p["label"] for p in tree["planes"]]
    tree = self.add_rect_sketch(100, 60)
    sk_free = next(
        f["name"] for f in tree["features"]
        if f["type"] == "Sketcher::SketchObject")
    mesh = self.tessellate()
    found = next((s for s in mesh.get("sketches") or []
                  if s["name"] == sk_free), None)
    free_ok = bool(found and found.get("positions"))
    tree = self.add_pad(10)
    report["m0_body_solid"] = (
        bool(tree["bodies"])
        and tree["bodies"][0].get("has_solid") is True)
    mesh = self.tessellate()
    report["p3_free_sketch_in_mesh"] = (
        free_ok
        and not any(s["name"] == sk_free
                    for s in mesh.get("sketches") or []))
    report["m0_faces"] = len(mesh["groups"])
    match = getattr(self, "_face_match", None) or {}
    report["p038_face_producers"] = (
        report["m0_faces"] == 6
        and all(g.get("feature") for g in mesh["groups"])
        and match.get("matched") == 6
        and match.get("tip", 1) == 0
    )
    etat.mesh = mesh
    etat.tree = tree


def m0_reparametrage(self, mark, report, etat):
    mesh = etat.mesh  # posé par fonctions.m0_piece_esquisse_bossage
    tree = etat.tree  # posé par fonctions.m0_piece_esquisse_bossage
    mark("m0: reparamétrage 10 → 25")
    pad = next(f["name"] for f in tree["features"]
               if f["type"] == "PartDesign::Pad")
    self.set_param(pad, "Length", 25.0)
    report["m0_reparam_ok"] = self.tessellate() != mesh


def m1_enlevement_et_conge(self, mark, report, etat):
    mark("m1: esquisse sur face + enlèvement à travers tout + congé")
    top = self._top_face_id()
    report["m1_top_face"] = top
    self.add_rect_sketch(40, 20, face=top)
    self.add_pocket(through=True)
    report["m1_pocket_faces"] = len(self.tessellate()["groups"])
    tree = self.add_fillet(3, face=self._top_face_id())
    report["m1_fillet_ok"] = not any(
        f["error"] for f in tree["features"])
    etat.tree = tree


def p2_revolution_tube(self, mark, report, etat):
    mark("p2: révolution (tube) + enlèvement avec révolution")
    self.new_part("Pièce révolution")
    state = self.sketch_start()
    rev_sk = state["sketch"]
    for line in ((10, 0, 30, 0), (30, 0, 30, 20),
                 (30, 20, 10, 20), (10, 20, 10, 0)):
        self.sketch_add_line(rev_sk, *line)
    self.sketch_finish(rev_sk)
    tree = self.add_revolution(360, sketch=rev_sk)
    report["p2_revolution_ok"] = not any(
        f["error"] for f in tree["features"])
    state = self.sketch_start()
    groove_sk = state["sketch"]
    for line in ((15, 8, 25, 8), (25, 8, 25, 12),
                 (25, 12, 15, 12), (15, 12, 15, 8)):
        self.sketch_add_line(groove_sk, *line)
    self.sketch_finish(groove_sk)
    tree = self.add_groove(360, sketch=groove_sk)
    report["p2_groove_ok"] = not any(
        f["error"] for f in tree["features"])


def p2_revolution_autour_ligne_construction(self, mark, report, etat):
    mark("p2: révolution autour d'une ligne de construction")
    import math
    self.new_part("Pièce axe")
    state = self.sketch_start()
    axis_sk = state["sketch"]
    for line in ((10, 0, 20, 0), (20, 0, 20, 10),
                 (20, 10, 10, 10), (10, 10, 10, 0)):
        self.sketch_add_line(axis_sk, *line)
    state = self.sketch_add_line(axis_sk, 5, -2, 5, 12)
    axis_id = state["entities"][-1]["id"]
    self.sketch_toggle_construction(axis_sk, axis_id)
    self.sketch_finish(axis_sk)
    tree = self.add_revolution(
        360, sketch=axis_sk, axis="line:{}".format(axis_id))
    rev = next(f for f in tree["features"]
               if f["type"] == "PartDesign::Revolution")
    sketch_child = rev["children"][0]
    tube = abs(float(self._require_body().Shape.Volume)
               - 2000.0 * math.pi) < 1.0
    report["p2_revolution_axis_ok"] = (
        tube
        and rev.get("revolution", {}).get("axis") == "line:{}".format(axis_id)
        and any(line["id"] == axis_id and line["construction"]
                for line in sketch_child.get("lines") or []))
    tree = self.set_params(rev["name"], {"axis": "vertical"})
    rev = next(f for f in tree["features"]
               if f["type"] == "PartDesign::Revolution")
    report["p2_revolution_axis_edit_ok"] = (
        abs(float(self._require_body().Shape.Volume)
            - 3000.0 * math.pi) < 1.0
        and rev.get("revolution", {}).get("axis") == "vertical")
    kept = float(self._require_body().Shape.Volume)
    refused = False
    try:
        self.set_params(rev["name"], {"axis": "sommet"})
    except KernelError:
        refused = True
    report["p2_revolution_axis_refused"] = (
        refused
        and abs(float(self._require_body().Shape.Volume) - kept) < 0.01)
    tree = self.set_params(rev["name"], {"Midplane": True})
    rev = next(f for f in tree["features"]
               if f["type"] == "PartDesign::Revolution")
    report["p2_revolution_midplane_ok"] = (
        rev.get("revolution", {}).get("midplane") is True
        and not rev.get("error"))


def p2_symetrie_repetition_lineaire(self, mark, report, etat):
    mark("p2: symétrie + répétition linéaire")
    self.new_part("Pièce symétrie")
    state = self.sketch_start()
    sym_sk = state["sketch"]
    for line in ((0, -10, 20, -10), (20, -10, 20, 10),
                 (20, 10, 0, 10), (0, 10, 0, -10)):
        self.sketch_add_line(sym_sk, *line)
    self.sketch_finish(sym_sk)
    self.add_pad(10, sketch=sym_sk)
    tree = self.add_mirror(plane="YZ")
    report["p2_mirror_ok"] = not any(
        f["error"] for f in tree["features"])
    tree = self.add_linear_pattern(length=20, count=2, axis="Y")
    report["p2_linear_pattern_ok"] = not any(
        f["error"] for f in tree["features"])


def p2_repetition_circulaire(self, mark, report, etat):
    mark("p2: répétition circulaire (4 perçages)")
    self.new_part("Pièce répétition")
    self.add_rect_sketch(60, 60)
    self.add_pad(6)
    state = self.sketch_start(face=self._top_face_id())
    pat_sk = state["sketch"]
    self.sketch_add_circle(pat_sk, 20, 0, 4)
    self.sketch_finish(pat_sk)
    self.add_pocket(through=True)
    tree = self.add_polar_pattern(count=4)
    report["p2_polar_pattern_ok"] = not any(
        f["error"] for f in tree["features"])


def p2_depouille_coque(self, mark, report, etat):
    mark("p2: dépouille + coque")
    self.new_part("Pièce coque")
    self.add_rect_sketch(40, 40)
    self.add_pad(20)
    top = self._top_face_id()
    try:
        self.add_draft(face=top, angle=5, neutral="XY")
        report["p2_draft_noop_refuse"] = False
    except KernelError:
        tree = self.get_tree()
        report["p2_draft_noop_refuse"] = not any(
            f["type"] == "PartDesign::Draft" for f in tree["features"])
    vol_before = float(self._require_body().Shape.Volume)
    tree = self.add_draft(face=top, angle=5, neutral="XZ")
    report["p2_draft_neutral_ok"] = (
        not any(f["error"] for f in tree["features"])
        and abs(float(self._require_body().Shape.Volume)
                - vol_before) > 1e-9)
    # La capture du rejeu (répétition variable) relit le plan neutre.
    from engine.replay import capture_group
    draft = next(f["name"] for f in tree["features"]
                 if f["type"] == "PartDesign::Draft")
    captured = capture_group(self, [draft])["features"][0]
    report["p2_draft_neutral_capture"] = captured.get("neutral") == "XZ"
    self.new_part("Pièce coque")
    self.add_rect_sketch(40, 40)
    self.add_pad(20)
    tree = self.add_draft(face=self._side_face_id(), angle=5)
    report["p2_draft_ok"] = not any(
        f["error"] for f in tree["features"])
    tree = self.add_thickness(self._top_face_id(), 2)
    report["p2_thickness_ok"] = not any(
        f["error"] for f in tree["features"])


def p4_apercu_jaune(self, mark, report, etat):
    mark("p4: aperçu jaune (exécuté puis annulé)")
    # Sur sa propre géométrie saine : chanfreiner le bord d'une
    # coque dépouillée segfaultait ChFi3d dans OCCT 7.8 (SIGSEGV
    # vu sur 1.1.3) — un crash C++, ininterceptable en Python.
    self.new_part("Pièce aperçu")
    self.add_rect_sketch(30, 30)
    self.add_pad(10)
    count = len(self.get_tree()["features"])
    faces_now = len(self.tessellate()["groups"])
    ghost = self.preview(
        "add_chamfer", {"face": self._top_face_id(), "size": 2})
    report["p4_preview_changes_mesh"] = (
        len(ghost["groups"]) != faces_now)
    report["p4_preview_leaves_doc_intact"] = (
        len(self.get_tree()["features"]) == count
        and len(self.tessellate()["groups"]) == faces_now)
    vol_before = float(self._require_body().Shape.Volume)
    top_edges = [i for i, e in
                 enumerate(self._require_body().Shape.Edges)
                 if abs(e.CenterOfMass.z - 10) < 1e-6]
    tree = self.add_chamfer(size=2, edges=[top_edges[0]])
    vol_chamfered = float(self._require_body().Shape.Volume)
    report["p4_chamfer_commit_ok"] = (
        not any(f["error"] for f in tree["features"])
        and (vol_chamfered < vol_before - 1e-6
             or len(self.tessellate()["groups"]) > faces_now))
    chamfer_name = next(f["name"] for f in tree["features"]
                        if f["type"] == "PartDesign::Chamfer")
    tree = self.delete_feature(chamfer_name)
    chamfer_gone = (
        not any(f["type"] == "PartDesign::Chamfer"
                for f in tree["features"])
        and not any(f["error"] for f in tree["features"]))
    # delete_feature du Tip laisse Tip=None et Shape invalide
    # (constat P007, hors périmètre). Indicateur faux, l'étape
    # continue — p5 repart sur une pièce neuve.
    try:
        vol_restored = abs(
            float(self._require_body().Shape.Volume)
            - vol_before) < 1e-6
    except RuntimeError:
        vol_restored = False
    report["p4_delete_feature_ok"] = chamfer_gone and vol_restored


def p4b_chanfrein(self, mark, report, etat):
    mark("p4b: chanfrein deux distances, distance-angle, inversion")
    self.new_part("Pièce chanfrein")
    self.add_rect_sketch(40, 30)
    self.add_pad(20)

    def _verts():
        shape = self._require_body().Shape
        solids = list(getattr(shape, "Solids", None) or [])
        solid = solids[0] if solids else shape
        return tuple(sorted(
            (round(float(v.Point.x), 3),
             round(float(v.Point.y), 3),
             round(float(v.Point.z), 3))
            for v in solid.Vertexes))

    def _top_edge():
        return next(
            i for i, item in
            enumerate(self._require_body().Shape.Edges)
            if abs(item.CenterOfMass.z - 20) < 1e-6)

    edge = _top_edge()
    tree = self.add_chamfer(size=2, edges=[edge])
    made = next(f for f in tree["features"]
                if f["type"] == "PartDesign::Chamfer")
    equal_verts = _verts()
    report["p4_chamfer_equal_ok"] = (
        made.get("chamfer", {}).get("type") == "egale"
        and abs(made["chamfer"]["size"] - 2) < 1e-6
        and made["chamfer"]["flip"] is False
        and [p["prop"] for p in made.get("params") or []] == ["Size"]
        and not made.get("error"))
    tree = self.set_params(made["name"], {
        "ChamferType": "deux", "Size2": 5, "FlipDirection": False})
    made = next(f for f in tree["features"] if f["name"] == made["name"])
    two_verts = _verts()
    report["p4_chamfer_two_ok"] = (
        made["chamfer"]["type"] == "deux"
        and abs(made["chamfer"]["size2"] - 5) < 1e-6
        and two_verts != equal_verts
        and [p["prop"] for p in made.get("params") or []]
        == ["Size", "Size2"]
        and not made.get("error"))
    tree = self.set_params(made["name"], {"FlipDirection": True})
    made = next(f for f in tree["features"] if f["name"] == made["name"])
    report["p4_chamfer_flip_ok"] = (
        made["chamfer"]["flip"] is True
        and _verts() != two_verts
        and not made.get("error"))

    self.new_part("Pièce chanfrein angle")
    self.add_rect_sketch(40, 30)
    self.add_pad(20)
    edge = _top_edge()
    tree = self.add_chamfer(
        size=4, angle=30, chamfer_type="angle", flip=True, edges=[edge])
    made = next(f for f in tree["features"]
                if f["type"] == "PartDesign::Chamfer")
    report["p4_chamfer_angle_ok"] = (
        made["chamfer"]["type"] == "angle"
        and abs(made["chamfer"]["angle"] - 30) < 1e-6
        and made["chamfer"]["flip"] is True
        and _verts() != equal_verts
        and [p["prop"] for p in made.get("params") or []]
        == ["Size", "Angle"]
        and not made.get("error"))
    before = len(tree["features"])
    try:
        self.add_chamfer(size=2, edges=[edge], chamfer_type="sommet")
        refused = False
    except KernelError as exc:
        refused = "type de chanfrein" in str(exc)
    report["p4_chamfer_type_refused"] = (
        refused and len(self.get_tree()["features"]) == before)


def p5_conge_aretes(self, mark, report, etat):
    mark("p5: congé sur arêtes")
    self.new_part("Pièce arêtes")
    self.add_rect_sketch(40, 40)
    self.add_pad(10)
    edges_pack = self.tessellate_edges()
    report["p5_edges"] = len(edges_pack["groups"])
    top_edges = [i for i, e in
                 enumerate(self._require_body().Shape.Edges)
                 if abs(e.CenterOfMass.z - 10) < 1e-6]
    report["p5_top_edges"] = len(top_edges)
    faces_before = len(self.tessellate()["groups"])
    tree = self.add_fillet(radius=3, edges=top_edges)
    report["p5_edge_fillet_ok"] = (
        not any(f["error"] for f in tree["features"])
        and len(self.tessellate()["groups"]) > faces_before)


def q1_conge_coque_trop_grands(self, mark, report, etat):
    mark("q1: congé trop grand et coque trop épaisse")
    self.new_part("Pièce refus")
    self.add_rect_sketch(40, 30)
    self.add_pad(12)
    edge = next(
        i for i, item in enumerate(self._require_body().Shape.Edges)
        if abs(item.CenterOfMass.z - 12) < 1e-6)
    try:
        self.add_fillet(100, edges=[edge])
        report["q1_conge_trop_grand"] = False
    except KernelError as exc:
        text = str(exc)
        tree = self.get_tree()
        report["q1_conge_trop_grand"] = (
            "réduisez le rayon" in text
            and "command not done" not in text
            and "SolidWorks" not in text
            and not any(f.get("error") for f in tree["features"]))
    try:
        self.add_thickness(self._top_face_id(), 30)
        report["q1_coque_trop_epaisse"] = False
    except KernelError as exc:
        text = str(exc)
        tree = self.get_tree()
        report["q1_coque_trop_epaisse"] = (
            "épaisseur est trop forte" in text
            and not any(f.get("error") for f in tree["features"]))
    tree = self.add_thickness(self._top_face_id(), 2)
    report["q1_coque_valide_apres_refus"] = (
        not any(f.get("error") for f in tree["features"])
        and abs(float(self._require_body().Shape.Volume) - 5040) < 1e-2)


def _plaque_cylindre_affleurant(self, rayon):
    """Plaque en rainure conique (R12 en (0, 0), R25 en (70, 0), tangentes
    extérieures, 10 mm) et cylindre de rayon ``rayon`` centré en (70, 0),
    posé dessus (22 mm). Rend l'indice de l'arc commun au cylindre et au
    dessus de la plaque, côté plaque."""
    self.new_part("Pièce affleurante")
    sk = self.sketch_start(plane="XY")["sketch"]
    phi = math.acos((12.0 - 25.0) / 70.0)
    haut1 = (12 * math.cos(phi), 12 * math.sin(phi))
    haut2 = (70 + 25 * math.cos(phi), 25 * math.sin(phi))
    self.sketch_add_arc(sk, 70, 0, 25, -phi, phi)
    self.sketch_add_line(sk, haut2[0], haut2[1], haut1[0], haut1[1])
    self.sketch_add_arc(sk, 0, 0, 12, phi, 2 * math.pi - phi)
    self.sketch_add_line(sk, haut1[0], -haut1[1], haut2[0], -haut2[1])
    self.sketch_finish(sk)
    self.add_pad(10)
    sk = self.sketch_start(face=self._top_face_id())["sketch"]
    centre = self._get_sketch(sk).Placement.inverse().multVec(
        self._app().Vector(70, 0, 10))
    self.sketch_add_circle(sk, centre.x, centre.y, rayon)
    self.sketch_finish(sk)
    self.add_pad(22)
    for i, edge in enumerate(self._require_body().Shape.Edges):
        curve = edge.Curve
        milieu = edge.valueAt((edge.FirstParameter + edge.LastParameter) / 2)
        if (curve.TypeId == "Part::GeomCircle"
                and abs(curve.Radius - rayon) < 1e-9
                and abs(curve.Center.x - 70) < 1e-6
                and abs(curve.Center.z - 10) < 1e-6 and milieu.x < 70):
            return i
    raise KernelError("arc commun cylindre / plaque introuvable")


def q2_conge_cylindre_affleurant(self, mark, report, etat):
    mark("q2: congé sur un cylindre qui affleure")
    # Cylindre R25 au ras de l'arrondi R25 : le modeleur rend un congé « à
    # jour » de forme invalide. Il est refusé, avec l'indice.
    arete = _plaque_cylindre_affleurant(self, 25.0)
    body = self._require_body()
    pointe = body.Tip
    avant = [f["name"] for f in self.get_tree()["features"]]

    def refuse(appel):
        try:
            appel()
        except KernelError as exc:
            texte = str(exc)
            tree = self.get_tree()
            return ("pièce invalide" in texte
                    and "affleure exactement" in texte
                    and [f["name"] for f in tree["features"]] == avant
                    and not any(f.get("error") for f in tree["features"])
                    and body.Tip is pointe and body.Shape.isValid())
        return False

    report["q2_conge_affleurant_refuse"] = refuse(
        lambda: self.add_fillet(3, edges=[arete]))
    report["q2_chanfrein_affleurant_refuse"] = refuse(
        lambda: self.add_chamfer(3, edges=[arete]))
    report["q2_apercu_affleurant_refuse"] = refuse(
        lambda: self.preview("add_fillet", {"radius": 3, "edges": [arete]}))
    # Un congé cassé déjà là (fichier d'avant la garde) : la réédition de
    # son rayon est refusée et le rayon reste.
    conge = body.newObject("PartDesign::Fillet", "Fillet")
    conge.Base = (pointe, ["Edge{}".format(arete + 1)])
    conge.Radius = 3.0
    self._require_doc().recompute()
    try:
        self.set_params(conge.Name, {"Radius": 2})
        report["q2_reedition_affleurant_refusee"] = False
    except KernelError as exc:
        texte = str(exc)
        report["q2_reedition_affleurant_refusee"] = (
            "affleure exactement" in texte
            and "la pièce n'a pas été modifiée" in texte
            and abs(self._prop_float(conge, "Radius") - 3.0) < 1e-9)
    # Cylindre élargi de 0,001 mm : le même congé passe, forme valide.
    arete = _plaque_cylindre_affleurant(self, 25.001)
    body = self._require_body()
    volume = float(body.Shape.Volume)
    tree = self.add_fillet(3, edges=[arete])
    report["q2_conge_elargi_valide"] = (
        body.Tip.TypeId == "PartDesign::Fillet"
        and body.Tip.Shape.isValid()
        and float(body.Shape.Volume) > volume
        and not any(f.get("error") for f in tree["features"]))


def p6_assistant_percage(self, mark, report, etat):
    mark("p6: assistant de perçage (2 trous lamés)")
    self.new_part("Pièce perçages")
    self.add_rect_sketch(60, 40)
    self.add_pad(8)
    state = self.sketch_start(face=self._top_face_id())
    hole_sk = state["sketch"]
    self.sketch_add_circle(hole_sk, -15, 0, 3)
    self.sketch_add_circle(hole_sk, 15, 0, 3)
    self.sketch_finish(hole_sk)
    faces_before = len(self.tessellate()["groups"])
    tree = self.add_hole(diameter=6, through=True,
                         cut="lamage", cut_diameter=11, cut_depth=3)
    report["p6_hole_ok"] = (
        not any(f["error"] for f in tree["features"])
        and len(self.tessellate()["groups"]) > faces_before)
    etat.tree = tree


def p8_plan_decale_lissage(self, mark, report, etat):
    mark("p8: plan de référence décalé + lissage")
    self.new_part("Pièce lissage")
    tree = self.add_datum_plane(base="XY", offset=30)
    datum = next(f["name"] for f in tree["features"]
                 if f["type"] == "PartDesign::Plane")
    report["p8_datum_has_placement"] = any(
        "placement" in f for f in tree["features"])
    self.add_rect_sketch(40, 40)
    base_sk = self._latest_sketch().Name
    state = self.sketch_start(datum=datum)
    top_sk = state["sketch"]
    for line in ((-10, -10, 10, -10), (10, -10, 10, 10),
                 (10, 10, -10, 10), (-10, 10, -10, -10)):
        self.sketch_add_line(top_sk, *line)
    self.sketch_finish(top_sk)
    tree = self.add_loft(sketches=[base_sk, top_sk])
    report["p8_loft_ok"] = (
        not any(f["error"] for f in tree["features"])
        and len(self.tessellate()["groups"]) > 0)


def p8_balayage(self, mark, report, etat):
    mark("p8: balayage (profil + trajectoire)")
    self.new_part("Pièce balayage")
    state = self.sketch_start(plane="XZ")
    spine_sk = state["sketch"]
    self.sketch_add_line(spine_sk, 0, 0, 0, 30)
    self.sketch_add_line(spine_sk, 0, 30, 25, 30)
    self.sketch_finish(spine_sk)
    state = self.sketch_start()
    prof_sk = state["sketch"]
    self.sketch_add_circle(prof_sk, 0, 0, 4)
    self.sketch_finish(prof_sk)
    tree = self.add_sweep(profile=prof_sk, spine=spine_sk)
    report["p8_sweep_ok"] = not any(
        f["error"] for f in tree["features"])


def p8_helice_ressort(self, mark, report, etat):
    mark("p8: hélice (ressort)")
    self.new_part("Pièce hélice")
    state = self.sketch_start(plane="XZ")
    hel_sk = state["sketch"]
    self.sketch_add_circle(hel_sk, 15, 0, 2)
    self.sketch_finish(hel_sk)
    tree = self.add_helix(pitch=8, height=40, sketch=hel_sk)
    report["p8_helix_ok"] = not any(
        f["error"] for f in tree["features"])


def p9_multi_corps_combiner(self, mark, report, etat):
    mark("p9: multi-corps + Combiner (soustraction)")
    self.new_part("Pièce multi-corps")
    self.add_rect_sketch(40, 40)
    self.add_pad(10)
    first_body = self._require_body().Name
    tree = self.add_body("Corps outil")
    report["p9_two_bodies"] = (
        len(tree["bodies"]) == 2
        and any(b["active"] and b["label"] == "Corps outil"
                for b in tree["bodies"]))
    state = self.sketch_start()
    tool_sk = state["sketch"]
    self.sketch_add_circle(tool_sk, 0, 0, 8)
    self.sketch_finish(tool_sk)
    self.add_pad(30)
    mesh = self.tessellate()
    report["p9_others_shown"] = "others" in mesh
    # L'autre corps se dessine face par face, numéroté comme quand il
    # sera actif, arêtes comprises : le clic dans la vue l'active. Son nom
    # est celui du dossier, sa dernière fonction.
    other = next((b for b in mesh.get("other_bodies", ())
                  if b["name"] == first_body), {})
    first = self._doc.getObject(first_body)
    report["p9_autres_cliquables"] = (
        other.get("label") == first.Tip.Label
        and sorted(g["faceId"] for g in other.get("groups", ()))
        == list(range(len(first.Shape.Faces)))
        and bool(other.get("edges", {}).get("groups")))
    tool_body = self._require_body().Name
    self.set_active_body(first_body)
    tree = self.set_body_color(first_body, "#cc5533")
    report["p9_color_ok"] = any(
        b["name"] == first_body and b.get("color") == "#cc5533"
        for b in tree["bodies"])
    try:
        self.set_body_color(first_body, "rouge")
        report["p9_color_invalid_ok"] = False
    except KernelError:
        report["p9_color_invalid_ok"] = True
    import tempfile
    color_path = os.path.join(tempfile.gettempdir(),
                              "freesolid-selftest-color.FCStd")
    self.save_part(color_path)
    reopened = self.open_part(color_path)
    report["p9_color_persist_ok"] = any(
        b["name"] == first_body and b.get("color") == "#cc5533"
        for b in reopened["bodies"])
    self.set_active_body(first_body)
    faces_before = len(self.tessellate()["groups"])
    tree = self.add_boolean(tool=tool_body, type="cut")
    report["p9_boolean_ok"] = (
        not any(f["error"] for f in tree["features"])
        and len(self.tessellate()["groups"]) > faces_before)


def p15_gravure_texte(self, mark, report, etat):
    mark("p15: gravure de texte")
    self.new_part("Pièce gravée")
    self.add_rect_sketch(60, 20)
    self.add_pad(5)
    faces_now = len(self.tessellate()["groups"])
    tree = self.add_text("AB", face=self._top_face_id(),
                         size=8, depth=1)
    # Volume et validité, pas seulement le compte de faces : la
    # gravure « AB » rendait un corps invalide de 17 mm³ (faces de
    # glyphes d'aire négative) sans que ce test le voie (P032).
    plate = self._require_body().Shape
    report["p15_text_ok"] = (
        not any(f["error"] for f in tree["features"])
        and len(self.tessellate()["groups"]) > faces_now
        and plate.isValid()
        and 5900.0 < float(plate.Volume) < 5999.9)


def p31_verites_geometriques(self, mark, report, etat):
    _close = etat._close  # posé par document.cycle_de_vie_open_part
    _volume = etat._volume  # posé par document.cycle_de_vie_open_part
    mark("p31: vérités géométriques")
    self.new_part("Pièce volumes P031")
    self.add_rect_sketch(40, 30)
    self.add_pad(10)
    report["p31_volume_pad"] = _close(_volume(), 12000.0)
    report["p31_faces_pad"] = len(self.tessellate()["groups"]) == 6
    self.add_rect_sketch(10, 10, face=self._top_face_id())
    self.add_pocket(through=True)
    report["p31_volume_pocket"] = _close(_volume(), 11000.0)
    producers = self._face_producers()
    report["p038_face_producers_historique"] = (
        "Pad" in producers.values() and "Pocket" in producers.values()
    )

    self.new_part("Pièce miroir P031")
    state = self.sketch_start()
    mir_sk = state["sketch"]
    # 20×20 à cheval sur YZ (x=-5..15) : un Body n'a qu'un solide,
    # les copies disjointes sont jetées — le chevauchement fusionne.
    for line in ((-5, -10, 15, -10), (15, -10, 15, 10),
                 (15, 10, -5, 10), (-5, 10, -5, -10)):
        self.sketch_add_line(mir_sk, *line)
    self.sketch_finish(mir_sk)
    self.add_pad(10, sketch=mir_sk)
    vol_before_mirror = _volume()
    self.add_mirror(plane="YZ")
    report["p31_volume_miroir"] = _close(
        _volume(), vol_before_mirror * 1.5)

    self.new_part("Pièce répétition P031")
    self.add_rect_sketch(20, 20)
    self.add_pad(10)
    vol_before_pattern = _volume()
    self.add_linear_pattern(length=10, count=2, axis="X")
    report["p31_volume_repetition"] = _close(
        _volume(), vol_before_pattern * 1.5)

    self.new_part("Pièce combiner P031")
    self.add_rect_sketch(40, 40)
    self.add_pad(10)
    first_body = self._require_body().Name
    vol_host = _volume()
    self.add_body("Corps outil")
    self.add_rect_sketch(20, 20)
    self.add_pad(10)
    tool_body = self._require_body().Name
    vol_tool = _volume()
    self.set_active_body(first_body)
    self.add_boolean(tool=tool_body, type="cut")
    report["p31_volume_combiner"] = _close(
        _volume(), vol_host - vol_tool)


def p19_paroi_mince(self, mark, report, etat):
    mark("p19: paroi mince — profil fermé, ouvert, réédition")
    self.new_part("Pièce paroi mince")
    self.add_rect_sketch(40, 20)
    tree = self.add_pad(10, thin={"type": "un", "thickness": 2})
    thin_pad = tree["features"][-1]
    volume = self._require_body().Shape.Volume
    closed_ok = (abs(volume - (44 * 24 - 40 * 20) * 10) < 1e-3
                 and len(tree["features"]) == 1
                 and len(thin_pad.get("children") or []) == 1
                 and thin_pad.get("thin", {}).get("thickness") == 2
                 and thin_pad.get("deps") == [
                     thin_pad["children"][0]["name"]])
    self.set_params(thin_pad["name"], {"Thickness": 1})
    volume = self._require_body().Shape.Volume
    edit_ok = abs(volume - (42 * 22 - 40 * 20) * 10) < 1e-3
    state = self.sketch_start()
    self.sketch_add_line(state["sketch"], 0, 50, 30, 50)
    self.sketch_add_line(state["sketch"], 30, 50, 30, 70)
    before = self._require_body().Shape.Volume
    tree = self.add_pad(5, sketch=state["sketch"],
                        thin={"type": "milieu", "thickness": 2})
    open_ok = abs(self._require_body().Shape.Volume - before
                  - 2 * 50 * 5) < 1e-3
    last = tree["features"][-1]["name"]
    self.delete_feature(last)
    helpers = [o for o in self._require_body().Group
               if self._is_thin_helper(o)]
    # Ceux de la première paroi seulement : son profil décalé et l'axe
    # qui suit la normale de l'esquisse.
    own = self._thin_helpers(self._doc.getObject(thin_pad["name"]))
    report["p19_paroi_mince"] = (closed_ok and edit_ok and open_ok
                                 and len(own) == 2 and helpers == own)
    try:
        self.add_pad(5, thin={"type": "deux", "thickness": 1})
        report["p19_paroi_mince_refus"] = False
    except KernelError:
        report["p19_paroi_mince_refus"] = (
            [o for o in self._require_body().Group
             if self._is_thin_helper(o)] == own)


def p38_coque_plusieurs_faces(self, mark, report, etat):
    mark("p38: coque sur plusieurs faces, vers l'extérieur")
    self.new_part("Pièce coque")
    self.add_rect_sketch(40, 20)
    self.add_pad(10)
    body = self._require_body()
    faces = body.Shape.Faces
    top = next(i for i, f in enumerate(faces)
               if abs(f.CenterOfMass.z - 10) < 1e-6)
    side = next(i for i, f in enumerate(faces)
                if abs(f.CenterOfMass.x - 20) < 1e-6)
    tree = self.add_thickness(faces=[top, side], thickness=1)
    inward = body.Shape.Volume
    self.delete_feature(tree["features"][-1]["name"])
    self.add_thickness(faces=[top, side], thickness=1, outward=True)
    bb = body.Shape.BoundBox
    report["p38_coque_multi"] = (
        abs(inward - (8000 - 39 * 18 * 9)) < 1e-3
        and abs(bb.XMin + 21) < 1e-6 and abs(bb.XMax - 20) < 1e-6
        and abs(bb.ZMax - 10) < 1e-6)
    try:
        self.add_thickness(faces=[], thickness=1)
        report["p38_coque_refus"] = False
    except KernelError:
        report["p38_coque_refus"] = True


def p44_trou_place_par_cote(self, mark, report, etat):
    mark("p44: trou placé par cote depuis l'origine et verticale")
    self.new_part("Pièce cercle de perçage")
    name = self.sketch_start()["sketch"]
    self.sketch_add_circle(name, 2, -28, 4)
    # Cercle + origine : la distance de son centre à l'origine.
    self.sketch_dim(name, 0, value=30, geo2=-1, point2=1)
    state = self.sketch_constrain(name, "vertical", 0, point1=3,
                                  geo2=-1, point2=1)
    circle = state["entities"][0]
    report["p44_cote_origine"] = (
        abs(circle["c"][0]) < 1e-6 and abs(circle["c"][1] + 30) < 1e-6
        and state["dof"] == 1)  # reste le rayon
    # Cotes horizontale / verticale d'un point depuis l'origine :
    # un sommet de nervure posé en (20, 12), valeurs positives même
    # tracé de l'autre côté.
    name = self.sketch_start()["sketch"]
    self.sketch_add_line(name, 18, 10, 36, 10)
    self.sketch_dim(name, -1, geo2=0, point=1, point2=1, axis="x")
    state = self.sketch_dim(name, 0, geo2=-1, point=1, point2=1,
                            axis="y")
    dims = state["dims"]
    for dim, target in zip(dims, (20, 12)):
        self.sketch_set_dim(name, dim["id"], value=target)
    line = self.sketch_state(name)["entities"][0]
    # Posée sous le segment : la cote garde ce décalage (sauvé).
    placed = self.sketch_dim(name, 0, at=[27, 3])["dims"][-1]
    moved = self.sketch_place_dim(name, placed["id"], 5)
    moved = next(d for d in moved["dims"] if d["id"] == placed["id"])
    report["p44_cote_posee"] = (
        placed["offset"] is not None
        and abs(placed["offset"] + 9) < 1e-6
        and abs(moved["offset"] - 5) < 1e-6
        and abs(moved["value"] - placed["value"]) < 1e-9)
    # Cotation intelligente : rayon d'un cercle, cercle + ligne,
    # deux cercles, longueur projetée d'une ligne oblique.
    name = self.sketch_start()["sketch"]
    self.sketch_add_circle(name, 0, 0, 5)                   # 0
    self.sketch_add_line(name, 20, -10, 20, 10)             # 1
    self.sketch_add_circle(name, 0, 30, 3)                  # 2
    self.sketch_add_line(name, 40, 0, 50, 6)                # 3
    kinds = []
    for params in ({"geo": 0, "radius": True},
                   {"geo": 0, "geo2": 1},
                   {"geo": 0, "geo2": 2},
                   {"geo": 3, "geo2": 3, "point": 1, "point2": 2,
                    "axis": "x"}):
        last = self.sketch_dim(name, **params)["dims"][-1]
        kinds.append((last["type"], round(last["value"], 6)))
    # Angle posé : l'arc passe là où on a cliqué (rayon retenu).
    self.sketch_add_line(name, 60, 0, 80, 0)                # 4
    self.sketch_add_line(name, 60, 10, 80, 30)              # 5
    # Les lignes 5 puis 4 tournent dans le sens horaire : la cote ne
    # doit pas les faire pivoter.
    before = [e for e in self.sketch_state(name)["entities"]
              if e["id"] in (4, 5)]
    state = self.sketch_dim(name, 5, geo2=4, at=[50, 50])
    angle = state["dims"][-1]
    after = [e for e in state["entities"] if e["id"] in (4, 5)]
    unmoved = all(abs(u - v) < 1e-6
                  for e1, e2 in zip(before, after)
                  for key in ("p1", "p2")
                  for u, v in zip(e1[key], e2[key]))
    corner_ok = (angle["type"] == "Angle" and angle["offset"] is not None
                 and abs(angle["offset"] - 50) < 1e-6)
    report["p44_cotation_intelligente"] = corner_ok and unmoved and kinds == [
        ("Radius", 5.0), ("Distance", 20.0), ("Distance", 30.0),
        ("DistanceX", 10.0)]
    report["p44_cotes_hv"] = (
        [d["type"] for d in dims] == ["DistanceX", "DistanceY"]
        and all(d["value"] > 0 for d in dims)
        and abs(line["p1"][0] - 20) < 1e-6
        and abs(line["p1"][1] - 12) < 1e-6)


def p45_apercu_plan_reference(self, mark, report, etat):
    mark("p45: aperçu du plan de référence, sans le créer")
    self.new_part("Pièce plan")
    before = len(self._require_doc().Objects)
    shown = self.preview("add_datum_plane",
                         {"base": "XY", "offset": 50})
    matrix = shown.get("plane") or []
    report["p45_apercu_plan"] = (
        len(matrix) == 16 and abs(matrix[11] - 50) < 1e-6
        and len(self._require_doc().Objects) == before)


def p41_percage_centres_cliques(self, mark, report, etat):
    mark("p41: perçage par centres cliqués sur une face")
    self.new_part("Pièce perçage")
    self.add_rect_sketch(60, 40)
    self.add_pad(8)
    body = self._require_body()
    top = next(i for i, f in enumerate(body.Shape.Faces)
               if abs(f.CenterOfMass.z - 8) < 1e-6)
    before = body.Shape.Volume
    tree = self.add_hole(6, through=True, face=top,
                         points=[[-15, 0, 8], [15, 5, 8]])
    import math
    removed = before - body.Shape.Volume
    report["p41_percage_points"] = (
        abs(removed - 2 * math.pi * 9 * 8) < 1e-2
        and tree["features"][-1]["type"] == "PartDesign::Hole"
        and len(tree["features"]) == 2)


def p57_chanfrein_sommet(self, mark, report, etat):
    mark("p57: chanfrein de sommet")
    self.new_part("Pièce coin")
    self.add_rect_sketch(40, 30)
    self.add_pad(10)
    body = self._require_body()
    box = body.Shape.Volume
    corner = body.Shape.BoundBox
    self.add_vertex_chamfer([5], point=[corner.XMax, corner.YMax,
                                        corner.ZMax])
    equal = box - body.Shape.Volume
    cham = self.get_tree()["features"][-1]
    self.edit_vertex_chamfer(cham["name"], [2, 3, 4])
    three = box - body.Shape.Volume
    # La pièce grandit : le chanfrein suit la fonction d'avant.
    pad = self.get_tree()["features"][0]["name"]
    self.set_params(pad, {"Length": 20})
    grown = body.Shape.Volume
    report["p57_chanfrein_sommet"] = (
        abs(equal - 125 / 6) < 1e-6
        and abs(three - 24 / 6) < 1e-6
        and cham.get("vertex_chamfer", {}).get("distances")
        == [5.0, 5.0, 5.0]
        and abs(grown - (40 * 30 * 20 - 4)) < 1e-6)


def p58_chaine_tangente_boucle(self, mark, report, etat):
    mark("p58: chaîne tangente, boucle")
    self.new_part("Pièce chaîne")
    self.add_rect_sketch(40, 30)
    self.add_pad(10)
    body = self._require_body()
    upright = [i for i, e in enumerate(body.Shape.Edges)
               if abs(e.BoundBox.ZLength - 10) < 1e-6]
    self.add_fillet(5, edges=upright)
    shape = body.Shape
    # Un bord droit du dessus : sa chaîne tangente fait le tour
    # (4 droites + 4 arcs) ; la boucle prend le dessus (8 arêtes)
    # ou le flanc (4 arêtes).
    line = next(i for i, e in enumerate(shape.Edges)
                if abs(e.BoundBox.ZMin - 10) < 1e-6
                and abs(e.BoundBox.ZMax - 10) < 1e-6
                and e.Curve.TypeId == "Part::GeomLine")
    chain = self.edge_chain(line)["edges"]
    loop = self.edge_chain(line, mode="loop")
    other = self.edge_chain(line, mode="loop", face=1)
    report["p58_chaine"] = (
        len(upright) == 4 and len(chain) == 8
        and loop["faces"] == 2
        and sorted([len(loop["edges"]), len(other["edges"])]) == [4, 8]
        and line in loop["edges"] and line in other["edges"])


def p61_axe_point_repere(self, mark, report, etat):
    mark("p61: axe, point, repère de référence")
    self.new_part("Pièce repères")
    self.add_rect_sketch(20, 10)
    self.add_pad(5)
    body = self._require_body()
    upright = next(i for i, e in enumerate(body.Shape.Edges)
                   if abs(e.BoundBox.ZLength - 5) < 1e-6)
    self.add_datum_axis(axis="X")
    self.add_datum_axis(edge=upright)
    self.add_datum_point(vertex=[10, 5, 5])
    self.add_datum_point(point=[1, 2, 3])
    tree = self.add_datum_cs(vertex=[-10, -5, 0])
    refs = [f for f in tree["features"] if f["type"] in (
        "PartDesign::Line", "PartDesign::Point",
        "PartDesign::CoordinateSystem")]
    doc = self._require_doc()

    def base(item):
        p = doc.getObject(item["name"]).Placement
        return [round(p.Base.x, 6), round(p.Base.y, 6),
                round(p.Base.z, 6)]

    def along(item):
        v = doc.getObject(item["name"]).Placement.Rotation.multVec(
            self._app().Vector(0, 0, 1))
        return [round(abs(v.x), 6), round(abs(v.y), 6),
                round(abs(v.z), 6)]
    report["p61_reference"] = (
        [r["type"].split("::")[1] for r in refs]
        == ["Line", "Line", "Point", "Point", "CoordinateSystem"]
        and all(len(r.get("placement") or []) == 16 for r in refs)
        and along(refs[0]) == [1, 0, 0] and along(refs[1]) == [0, 0, 1]
        and base(refs[2]) == [10, 5, 5] and base(refs[3]) == [1, 2, 3]
        and base(refs[4]) == [-10, -5, 0]
        and refs[0]["kind"] == "Axe de référence")


def p63_repetition_deux_directions(self, mark, report, etat):
    mark("p63: répétition dans deux directions")
    self.new_part("Pièce quadrillée")
    self.add_rect_sketch(100, 100)
    self.add_pad(5)
    body = self._require_body()
    top = next(i for i, f in enumerate(body.Shape.Faces)
               if f.normalAt(0, 0).z > 0.9)
    self.add_rect_sketch(10, 10, face=top)
    self.add_pad(5)
    tree = self.add_linear_pattern(20, 3, axis="X", spacing=True,
                                   length2=25, count2=2, axis2="Y")
    grid = tree["features"][-1]["name"]
    six = body.Shape.Volume
    self.set_params(grid, {"Occurrences2": 3})
    nine = body.Shape.Volume
    props = [p["prop"] for p in self.get_params(grid)["params"]]
    report["p63_deux_directions"] = (
        abs(six - (100 * 100 * 5 + 6 * 500)) < 1e-6
        and abs(nine - (100 * 100 * 5 + 9 * 500)) < 1e-6
        and "Occurrences2" in props)


def p67_tirer_face_bout(self, mark, report, etat):
    mark("p67: tirer la face du bout")
    self.new_part("Pièce tirée")
    self.add_rect_sketch(40, 30)
    self.add_pad(20)
    body = self._require_body()
    top = next(i for i, f in enumerate(body.Shape.Faces)
               if f.normalAt(0, 0).z > 0.9)
    side = next(i for i, f in enumerate(body.Shape.Faces)
                if abs(f.normalAt(0, 0).z) < 0.1)
    cap = self.face_drag_info(top)["drag"]
    wall = self.face_drag_info(side)["drag"]
    self.add_rect_sketch(10, 10, face=top)
    self.add_pocket(5)
    floor = next(i for i, f in enumerate(body.Shape.Faces)
                 if f.normalAt(0, 0).z > 0.9
                 and abs(f.CenterOfMass.z - 15) < 1e-6)
    hole = self.face_drag_info(floor)["drag"]
    report["p67_tirer_face"] = (
        cap is not None and cap["factor"] == 1 and cap["value"] == 20
        and wall is None
        and hole is not None and hole["factor"] == -1
        and abs(hole["value"] - 5) < 1e-9
        and cap["key"] == hole["key"] == "length")

    # Réédition : la flèche au bout de la fonction, comme à la création.
    def near(drag, z, dz, factor):
        return (drag is not None and abs(drag["point"][2] - z) < 1e-6
                and abs(drag["normal"][2] - dz) < 1e-6
                and drag["factor"] == factor and drag["key"] == "length")
    sketch = self._doc.getObject(cap["feature"]).Profile[0].Name
    tip = self.feature_drag_info(cap["feature"])["drag"]
    dig = self.feature_drag_info(hole["feature"])["drag"]
    self.add_rect_sketch(10, 10)
    both = self.add_pad(8, midplane=True)["features"][-1]["name"]
    half = self.feature_drag_info(both)["drag"]
    under = next(i for i, f in enumerate(body.Shape.Faces)
                 if f.normalAt(0, 0).z < -0.9
                 and abs(f.CenterOfMass.z + 4) < 1e-6)
    pulled = self.face_drag_info(under)["drag"]
    report["p67_fleche_reedition"] = (
        near(tip, 20, 1, 1) and tip["value"] == 20
        and near(dig, 15, -1, 1) and near(half, 4, 1, 2)
        and self.feature_drag_info(sketch)["drag"] is None)
    # Plan milieu (SideType depuis FreeCAD 1.1) : sa face se tire aussi.
    report["p67_tirer_face_symetrique"] = (
        pulled is not None and pulled["factor"] == 2
        and pulled["value"] == 8)


def p19b_paroi_mince_extremites_fermees(self, mark, report, etat):
    mark("p19b: paroi mince à extrémités fermées")
    self.new_part("Pièce paroi fermée")
    self.add_rect_sketch(40, 20)
    body = self._require_body()
    tree = self.add_pad(10, thin={"type": "un", "thickness": 2,
                                  "caps": 1})
    capped = tree["features"][-1]["name"]
    def near(expected):
        return abs(body.Shape.Volume - expected) < 1e-3
    ok = (near(44 * 24 * 10 - 40 * 20 * 8)
          and len(body.Shape.Solids) == 1
          and len(tree["features"]) == 1
          and tree["tip"] == capped
          and tree["features"][0]["thin"]["caps"] == 1
          and len(tree["features"][0].get("children") or []) == 1)
    self.set_params(capped, {"Length": 20})
    ok = ok and near(44 * 24 * 20 - 40 * 20 * 18)
    self.set_params(capped, {"CapThickness": 2})
    ok = ok and near(44 * 24 * 20 - 40 * 20 * 16)
    try:
        self.set_params(capped, {"CapThickness": 10})
        ok = False
    except KernelError:
        ok = ok and near(44 * 24 * 20 - 40 * 20 * 16)
    mesh = self.tessellate()
    ok = ok and all(g.get("feature") == capped
                    for g in mesh["groups"])
    tree = self.set_tip(capped)
    ok = (ok and tree["tip"] == capped
          and self._is_thin_helper(body.Tip)
          and near(44 * 24 * 20 - 40 * 20 * 16))
    self.delete_feature(capped)
    ok = ok and not [o for o in body.Group
                     if self._is_thin_helper(o)]
    tree = self.add_pad(20, midplane=True, thin={
        "type": "milieu", "thickness": 2, "caps": 1})
    own = self._thin_helpers(self._doc.getObject(tree["features"][-1]["name"]))
    bb = body.Shape.BoundBox
    ok = (ok and near(42 * 22 * 20 - 38 * 18 * 18)
          and abs(bb.ZMin + 10) < 1e-6 and abs(bb.ZMax - 10) < 1e-6)
    report["p19b_extremites_fermees"] = ok
    refused = 0
    for call_refused in (
            lambda: self.add_pad(cond="suivant", thin={
                "type": "un", "thickness": 1, "caps": 1}),
            lambda: self.add_pocket(5, thin={
                "type": "un", "thickness": 1, "caps": 1})):
        try:
            call_refused()
        except KernelError:
            refused += 1
    # Deux profils décalés, l'axe de la normale, la cavité ; rien de plus.
    report["p19b_extremites_refus"] = (
        refused == 2 and len(own) == 4
        and [o for o in body.Group if self._is_thin_helper(o)] == own)


def p91_conditions_d_extrusion(self, mark, report, etat):
    mark("p91: les conditions d'une extrusion se rééditent")
    from engine.kernel import dispatch
    self.new_part("Conditions rééditées")
    self.add_rect_sketch(40, 20)
    body = self._require_body()
    tree = self.add_pad(10)
    pad = tree["features"][-1]["name"]

    def near(expected):
        return abs(body.Shape.Volume - expected) < 1e-3

    def spans(low, high):
        box = body.Shape.BoundBox
        return abs(box.ZMin - low) < 1e-6 and abs(box.ZMax - high) < 1e-6

    def row(tree, name):
        return next(f for f in tree["features"] if f["name"] == name)

    ok = row(tree, pad).get("extrude", {}).get("cond") == "borgne"
    self.set_params(pad, {"midplane": True})
    ok = ok and near(8000) and spans(-5, 5)
    tree = self.set_params(pad, {"midplane": False, "cond2": "borgne",
                                 "length2": 4})
    ok = (ok and near(40 * 20 * 14) and spans(-4, 10)
          and any(p["key"] == "length2" for p in row(tree, pad)["params"]))
    # Par le protocole : « cond2 » nul referme le côté 2.
    answer = dispatch(self, "set_params", {
        "feature": pad, "values": {"cond2": None, "reversed": True}})
    ok = ok and answer.get("ok") is True and near(8000) and spans(-10, 0)
    self.add_rect_sketch(10, 10)
    tree = self.add_pocket()
    pocket = tree["features"][-1]["name"]
    ok = (ok and near(8000 - 1000)
          and row(tree, pocket).get("extrude", {}).get("cond") == "travers")
    self.set_params(pocket, {"cond": "borgne", "length": 3})
    ok = ok and near(8000 - 300)
    refused = dispatch(self, "set_params", {
        "feature": pocket, "values": {"cond": "face", "length": 5}})
    ok = (ok and refused.get("ok") is False
          and "face d'arrivée" in refused["error"]
          and near(8000 - 300) and self._doc.getObject(pocket).Type == "Length")
    report["p91_conditions_extrusion"] = ok

    # Paroi mince : le côté se change ; fermée, la cavité suit le plan
    # milieu et refuse une condition non borgne.
    self.new_part("Paroi rééditée")
    self.add_rect_sketch(40, 20)
    body = self._require_body()
    thin = self.add_pad(10, thin={"type": "un", "thickness": 2})
    thin = thin["features"][-1]["name"]
    ok = near(44 * 24 * 10 - 8000)
    self.set_params(thin, {"thinReversed": True})
    ok = ok and near(8000 - 36 * 16 * 10)
    self.delete_feature(thin)
    capped = self.add_pad(10, thin={"type": "un", "thickness": 2, "caps": 1})
    capped = capped["features"][-1]["name"]
    closed = 44 * 24 * 10 - 40 * 20 * 8
    ok = ok and near(closed)
    self.set_params(capped, {"midplane": True})
    ok = ok and near(closed) and spans(-5, 5)
    try:
        self.set_params(capped, {"midplane": False, "cond": "suivant"})
        ok = False
    except KernelError as exc:
        ok = ok and "extrémités fermées" in str(exc)
    report["p91_paroi_mince_reeditee"] = (
        ok and near(closed) and spans(-5, 5)
        and not any("Invalid" in (o.State or ())
                    for o in self._doc.Objects))


def p92_coque_et_percage_reedites(self, mark, report, etat):
    mark("p92: le sens de la coque, le type et la fin du perçage se rééditent")
    from engine.kernel import dispatch
    self.new_part("Coque rééditée")
    self.add_rect_sketch(40, 40)
    self.add_pad(20)
    body = self._require_body()

    def top_face():
        return next(i for i, f in enumerate(body.Shape.Faces)
                    if abs(f.CenterOfMass.z - 20) < 1e-6)

    def row(tree, name):
        return next(f for f in tree["features"] if f["name"] == name)

    tree = self.add_thickness(faces=[top_face()], thickness=2)
    shell = body.Tip.Name
    ok = ((row(tree, shell).get("shell") or {}).get("outward") is False
          and abs(body.Shape.Volume - (32000 - 36 * 36 * 18)) < 1e-3)
    self.set_params(shell, {"outward": True})
    box = body.Shape.BoundBox
    ok = (ok and abs(box.XMax - 22) < 1e-6 and abs(box.ZMin + 2) < 1e-6
          and abs(box.ZMax - 20) < 1e-6)
    outward = body.Shape.Volume
    # Vers l'intérieur et trop épaisse : refusée, la coque reste dehors.
    refused = dispatch(self, "set_params", {
        "feature": shell, "values": {"outward": False, "thickness": 30}})
    report["p92_sens_de_la_coque"] = (
        ok and refused.get("ok") is False
        and abs(body.Shape.Volume - outward) < 1e-6
        and self._doc.getObject(shell).Reversed is False)

    self.new_part("Perçage réédité")
    self.add_rect_sketch(40, 40)
    self.add_pad(20)
    body = self._require_body()
    tree = self.add_hole(6, through=True, face=top_face(),
                         points=[[0, 0, 20]])
    hole = body.Tip
    state = row(tree, hole.Name).get("hole") or {}
    ok = (state.get("cut") == "none" and state.get("cond") == "travers"
          and [p["key"] for p in row(tree, hole.Name)["params"]]
          == ["diameter"])
    self.set_params(hole.Name, {"cut": "lamage", "cutDiameter": 10,
                                "cutDepth": 3})
    ok = (ok and hole.HoleCutType == "Counterbore"
          and abs(body.Shape.Volume - (32000 - math.pi * (9 * 17 + 25 * 3)))
          < 1e-3)
    through = body.Shape.Volume
    self.set_params(hole.Name, {"cond": "borgne", "depth": 8})
    ok = ok and hole.DepthType == "Dimension" and body.Shape.Volume > through
    tree = self.set_params(hole.Name, {"cut": "fraisage", "cutDiameter": 12,
                                       "cutAngle": 90})
    ok = (ok and hole.HoleCutType == "Countersink"
          and abs(float(hole.HoleCutDiameter) - 12) < 1e-9
          and [p["key"] for p in row(tree, hole.Name)["params"]]
          == ["diameter", "depth", "cutDiameter", "cutAngle"])
    report["p92_type_du_percage"] = (
        ok and not any("Invalid" in (o.State or ())
                       for o in self._doc.Objects))


def p93_fusionner_ou_non(self, mark, report, etat):
    mark("p93: une extrusion fusionne avec un corps choisi ou en crée un")
    from engine.kernel import dispatch
    self.new_part("Fusionner")
    self.add_rect_sketch(40, 20)
    self.add_pad(10)
    first = self._require_body()

    def top_face(body, z):
        return next(i for i, f in enumerate(body.Shape.Faces)
                    if abs(f.CenterOfMass.z - z) < 1e-6)

    def sketch(x1, y1, x2, y2, **where):
        name = self.sketch_start(**where)["sketch"]
        self.sketch_add_rectangle(name, x1, y1, x2, y2)
        self.sketch_finish(name)
        return name

    # Esquisse sur la face du dessus, extrusion non fusionnée : un corps
    # neuf, le premier ne bouge pas, l'esquisse se range sous sa fonction.
    profile = sketch(0, 0, 10, 10, face=top_face(first, 10))
    answer = dispatch(self, "add_pad", {"length": 5, "merge": False})
    tree = answer.get("result") or {}
    made = self._require_body()
    pad = made.Tip
    box = made.Shape.BoundBox
    rows = tree.get("features") or []
    report["p93_nouveau_corps"] = (
        answer.get("ok") is True and made is not first
        and abs(first.Shape.Volume - 8000) < 1e-6
        and abs(made.Shape.Volume - 500) < 1e-6
        and abs(box.ZMin - 10) < 1e-6 and abs(box.ZMax - 15) < 1e-6
        and len(tree.get("bodies") or []) == 2
        and any(r["name"] == pad.Name
                and [c["name"] for c in r.get("children", [])] == [profile]
                for r in rows)
        and not any(r["name"] == profile
                    for r in rows + (tree.get("other_features") or []))
        and not protocol_dangling(tree))

    # Ctrl+Z : plus de corps neuf, on revient au premier ; Ctrl+Y le rend.
    dispatch(self, "undo", {})
    back = self._require_body()
    undone = (back is first and len(self.get_tree()["bodies"]) == 1)
    dispatch(self, "redo", {})
    made = next(o for o in self._doc.Objects
                if o.TypeId == "PartDesign::Body" and o is not first)
    # Supprimer sa seule fonction emporte le corps.
    dispatch(self, "delete_feature", {"feature": made.Tip.Name})
    gone = (len(self.get_tree()["bodies"]) == 1
            and self._require_body() is first)
    dispatch(self, "undo", {})
    report["p93_annuler_et_supprimer"] = (
        undone and gone and len(self.get_tree()["bodies"]) == 2)

    # Fusionner avec l'autre corps : l'esquisse reste dans le premier.
    made = next(o for o in self._doc.Objects
                if o.TypeId == "PartDesign::Body" and o is not first)
    self._body = first
    before = made.Shape.Volume
    profile = sketch(0, 0, 5, 5, plane="XY")
    self.add_pad(25, body=made.Name)
    report["p93_fusion_avec_un_corps"] = (
        self._require_body() is made
        and abs(first.Shape.Volume - 8000) < 1e-6
        and abs(made.Shape.Volume - before - 500) < 1e-6
        and len(made.Shape.Solids) == 1
        and self._doc.getObject(profile).getParentGeoFeatureGroup() is first)

    # Refus : un « jusqu'à » sans solide, une face d'un autre corps.
    self._body = first
    sketch(60, 0, 70, 5, plane="XY")
    count = len(self._doc.Objects)
    suivant = dispatch(self, "add_pad", {"merge": False, "cond": "suivant"})
    face = dispatch(self, "add_pad", {"body": made.Name, "cond": "face",
                                      "face": 0})
    preview = dispatch(self, "preview", {"op": "add_pad", "params": {
        "length": 3, "merge": False}})
    report["p93_refus"] = (
        suivant.get("ok") is False and face.get("ok") is False
        and preview.get("ok") is True and self._body is first
        and len(self._doc.Objects) == count)

    # Contours choisis, nouveau corps ; plan de face : la normale de
    # l'esquisse, comme une extrusion de l'esquisse elle-même.
    name = sketch(60, 0, 70, 5, plane="XY")
    self.sketch_edit(name)
    self.sketch_add_rectangle(name, 80, 0, 90, 5)
    self.sketch_finish(name)
    self.add_pad(2, sketch=name, merge=False, contours=[1])
    alone = self._require_body()
    box = alone.Shape.BoundBox
    ok = (abs(alone.Shape.Volume - 100) < 1e-6
          and abs(box.XMin - 80) < 1e-6)
    self._body = first
    sketch(100, 0, 110, 5, plane="XZ")
    self.add_pad(4, merge=False)
    box = self._require_body().Shape.BoundBox
    report["p93_contours_et_sens"] = (
        ok and abs(box.YMin + 4) < 1e-6 and abs(box.YMax) < 1e-6)

    # Paroi mince sur le plan de face : du même côté que l'extrusion pleine.
    self.new_part("Paroi de face")
    sketch(2, 3, 12, 8, plane="XZ")
    self.add_pad(5, thin={"type": "un", "thickness": 1})
    box = self._require_body().Shape.BoundBox
    report["p93_paroi_mince_suit_l_esquisse"] = (
        abs(box.YMin + 5) < 1e-6 and abs(box.YMax) < 1e-6
        and not any("Invalid" in (o.State or ()) for o in self._doc.Objects))


def p94_fusionner_les_autres_volumes(self, mark, report, etat):
    mark("p94: révolution, lissage et balayage fusionnent ou non ; "
         "Ctrl+Z rend le corps actif")
    import math
    from engine.kernel import dispatch

    def start():
        self.new_part("Autres volumes")
        self.add_rect_sketch(40, 20)
        self.add_pad(10)
        return self._require_body()

    def rect(x1, y1, x2, y2, **where):
        name = self.sketch_start(**where)["sketch"]
        self.sketch_add_rectangle(name, x1, y1, x2, y2)
        self.sketch_finish(name)
        return name

    def box(feature):
        b = feature.AddSubShape.BoundBox
        return [round(v, 6) for v in (b.XMin, b.YMin, b.ZMin,
                                      b.XMax, b.YMax, b.ZMax)]

    def clean():
        return not any("Invalid" in (o.State or ())
                       for o in self._doc.Objects)

    # Révolution en nouveau corps, d'une esquisse du premier : même
    # volume et même côté que la révolution de l'esquisse elle-même, pour
    # chaque axe d'esquisse ; Ctrl+Z rend le premier corps.
    same = True
    for axis in ("vertical", "horizontal", "line:1"):
        first = start()
        profile = rect(30, 5, 40, 15, plane="XZ")
        dispatch(self, "add_revolution", {"angle": 90, "axis": axis,
                                          "merge": False})
        made = self._require_body()
        linked = (made is not first, box(made.Tip),
                  round(made.Tip.AddSubShape.Volume, 6))
        dispatch(self, "undo", {})
        back = self._require_body() is first
        self.add_revolution(90, sketch=profile, axis=axis)
        direct = (True, box(first.Tip),
                  round(first.Tip.AddSubShape.Volume, 6))
        same = same and back and linked == direct and clean()
    report["p94_revolution_nouveau_corps"] = same

    # Réédition de l'axe depuis un autre corps actif : la ligne cachée
    # resert, l'axe interne d'une ligne va dans le corps de la fonction,
    # le volume suit. Supprimer la révolution emporte son corps.
    first = start()
    rect(30, 5, 40, 15, plane="XZ")
    self.add_revolution(90, merge=False)
    made = self._require_body()
    revolution = made.Tip.Name
    self._body = first
    volumes = []
    homes = []
    for token in ("horizontal", "X", "line:2", "vertical"):
        answer = dispatch(self, "set_params", {
            "feature": revolution, "values": {"axis": token}})
        obj = self._doc.getObject(revolution)
        volumes.append((answer.get("ok"),
                        self._revolution_axis_token(obj),
                        round(obj.AddSubShape.Volume, 2)))
        homes.append(obj.ReferenceAxis[0].getParentGeoFeatureGroup() is made)
    side = round(100 * 5 * math.pi / 2, 2)
    edited = (
        volumes == [(True, "horizontal", round(100 * 10 * math.pi / 2, 2)),
                    (True, "X", round(100 * 10 * math.pi / 2, 2)),
                    (True, "line:2", side),
                    (True, "vertical", round(100 * 35 * math.pi / 2, 2))]
        and all(homes)
        and len(self._thin_helpers(self._doc.getObject(revolution))) == 2
        and self._revolution_state(obj)["profile"] != obj.Profile[0].Name)
    self._body = made
    dispatch(self, "set_params", {"feature": revolution,
                                  "values": {"axis": "line:2"}})
    self.delete_feature(revolution)
    report["p94_reedition_de_l_axe"] = (
        edited and len(self.get_tree()["bodies"]) == 1)

    # Fusion dans un autre corps, puis Ctrl+Z : le corps d'avant redevient
    # actif — extrusion comme révolution.
    first = start()
    rect(50, 0, 70, 10, plane="XY")
    self.add_pad(5, merge=False)
    other = self._require_body()
    self._body = first
    rect(52, 2, 58, 8, plane="XY")
    dispatch(self, "add_pad", {"length": 8, "body": other.Name})
    pad_back = (self._require_body() is other
                and dispatch(self, "undo", {}).get("ok") is True
                and self._require_body() is first)
    self._body = first
    rect(55, 0, 65, 5, plane="XZ")
    before = other.Shape.Volume
    dispatch(self, "add_revolution", {"angle": 90, "body": other.Name})
    grown = other.Shape.Volume - before
    dispatch(self, "undo", {})
    report["p94_ctrl_z_rend_le_corps"] = (
        pad_back and grown > 0 and self._require_body() is first)

    # Ctrl+Y rend le corps d'après : le corps neuf, y compris après deux
    # pas défaits d'un coup ; une esquisse abandonnée entre deux ne
    # dérègle rien, une op neuve vide la pile.
    first = start()
    rect(50, 0, 70, 10, plane="XY")
    dispatch(self, "add_pad", {"length": 5, "merge": False})
    made = self._require_body().Name
    dispatch(self, "undo", {})
    undone = self._require_body() is first
    dispatch(self, "redo", {})
    redone = self._require_body().Name == made
    rect(52, 2, 58, 8, plane="XY")
    dispatch(self, "add_pad", {"length": 8})
    dispatch(self, "undo", {"steps": 2})
    both = self._require_body() is first
    dispatch(self, "redo", {})
    one = self._require_body().Name == made
    dispatch(self, "redo", {})
    two = self._require_body().Name == made
    sketch = dispatch(self, "sketch_start", {"plane": "XY"})["result"]["sketch"]
    dispatch(self, "sketch_add_line", {"sketch": sketch, "x1": 0, "y1": 0,
                                       "x2": 5, "y2": 5})
    dispatch(self, "sketch_cancel", {"sketch": sketch})
    dispatch(self, "undo", {})
    dispatch(self, "redo", {})
    cancelled = self._require_body().Name == made
    dispatch(self, "undo", {})
    self._body = first
    rect(0, 0, 5, 5, plane="XY")
    dispatch(self, "add_pad", {"length": 2})
    dispatch(self, "undo", {})
    dispatch(self, "redo", {})
    report["p94_ctrl_y_rend_le_corps"] = (
        undone and redone and both and one and two and cancelled
        and self._require_body() is first and clean())

    # Lissage en nouveau corps : le même que dans le corps des esquisses.
    first = start()
    self.add_datum_plane(base="XY", offset=20)
    plane = [o.Name for o in self._doc.Objects
             if o.TypeId == "PartDesign::Plane"][-1]
    low = rect(60, 0, 70, 10, plane="XY")
    high = rect(62, 2, 68, 8, datum=plane)
    tree = dispatch(self, "add_loft", {"sketches": [low, high],
                                       "merge": False}).get("result") or {}
    made = self._require_body()
    linked = (box(made.Tip), round(made.Tip.AddSubShape.Volume, 6))
    dispatch(self, "undo", {})
    self.add_loft([low, high])
    report["p94_lissage_nouveau_corps"] = (
        made is not first and self._require_body() is first
        and linked == (box(first.Tip),
                       round(first.Tip.AddSubShape.Volume, 6))
        and not protocol_dangling(tree) and clean())

    # Balayage en nouveau corps ; un profil en deux morceaux est refusé
    # (le liant n'en donnerait qu'un), sans rien laisser.
    first = start()
    circle = self.sketch_start(plane="XZ")["sketch"]
    self.sketch_add_circle(circle, 60, 0, 2)
    self.sketch_finish(circle)
    path = self.sketch_start(plane="XY")["sketch"]
    self.sketch_add_line(path, 60, 0, 60, -30)
    self.sketch_finish(path)
    self.add_sweep(circle, path, merge=False)
    made = self._require_body()
    swept = (made is not first
             and abs(made.Shape.Volume - math.pi * 4 * 30) < 1e-6)
    self.delete_feature(made.Tip.Name)
    gone = len(self.get_tree()["bodies"]) == 1
    self.sketch_edit(circle)
    self.sketch_add_circle(circle, 66, 0, 1)
    self.sketch_finish(circle)
    count = len(self._doc.Objects)
    refused = dispatch(self, "add_sweep", {"profile": circle, "spine": path,
                                           "merge": False})
    refused_ok = (refused.get("ok") is False
                  and "seul tenant" in str(refused.get("error"))
                  and len(self._doc.Objects) == count
                  and self._require_body() is first)
    # Sur une courbe 3D : son liant part aussi avec le balayage.
    curve = self.add_curve3d([[-60, 0, 0], [-60, 0, 30], [-40, 0, 50]],
                             spline=True)["surfaces"][-1]["name"]
    ring = self.sketch_start(plane="XY")["sketch"]
    self.sketch_add_circle(ring, -60, 0, 3)
    self.sketch_finish(ring)
    self.add_sweep(ring, curve, merge=False)
    curved = self._require_body()
    on_curve = curved is not first and curved.Shape.Volume > 0
    # Un balayage ne se colle pas : sa trajectoire resterait la sienne.
    pasted = dispatch(self, "paste_feature", {"feature": curved.Tip.Name,
                                              "plane": "XY"})
    self.delete_feature(curved.Tip.Name)
    report["p94_balayage_nouveau_corps"] = (
        swept and gone and refused_ok and on_curve
        and pasted.get("ok") is False
        and len(self.get_tree()["bodies"]) == 1 and clean())

    # Copier-coller d'une révolution d'un autre corps : l'axe de
    # l'esquisse collée.
    first = start()
    rect(30, 5, 40, 15, plane="XZ")
    self.add_revolution(90, merge=False)
    made = self._require_body()
    source = made.Tip
    pasted = dispatch(self, "paste_feature", {"feature": source.Name,
                                              "plane": "XZ"})
    twin = made.Tip
    report["p94_coller_une_revolution"] = (
        pasted.get("ok") is True and twin is not source
        and twin.ReferenceAxis[0] is twin.Profile[0]
        and abs(twin.AddSubShape.Volume - source.AddSubShape.Volume) < 1e-6
        and clean())


def p95_fusionner_plusieurs_corps(self, mark, report, etat):
    mark("p95: un volume fond plusieurs corps en un seul")
    from engine.kernel import dispatch

    def call(op, **params):
        return dispatch(self, op, params)

    def rect(x1, y1, x2, y2):
        name = self.sketch_start(plane="XY")["sketch"]
        self.sketch_add_rectangle(name, x1, y1, x2, y2)
        self.sketch_finish(name)
        return name

    def folder():
        return [b["name"] for b in self.get_tree()["bodies"]]

    def shown():
        return [o["name"] for o in self.tessellate().get("other_bodies", [])]

    def clean():
        return not any("Invalid" in (o.State or ()) for o in self._doc.Objects)

    self.new_part("Fusionner plusieurs corps")
    rect(0, 0, 20, 20)
    first = self.add_pad(10)["features"][0]["name"]
    a = self._require_body()
    self.add_body()
    rect(30, 0, 50, 20)
    self.add_pad(10)
    b = self._require_body()
    self.add_body()
    rect(60, 0, 80, 20)
    self.add_pad(10)
    c = self._require_body()
    self.set_active_body(a.Name)
    rect(10, 5, 70, 15)
    # Une barre de 60 × 10 × 5 qui touche les trois corps : un solide.
    merged = call("add_pad", length=5, bodies=[b.Name, c.Name])
    pad = a.Tip.FreeSolidThinOwner if self._is_thin_helper(a.Tip) else ""
    rows = [r["name"] for r in (merged.get("result") or {}).get("features", [])
            + (merged.get("result") or {}).get("other_features", [])]
    one = 3 * 4000 + 3000 - 2000
    report["p95_trois_corps_fondus"] = (
        merged.get("ok") is True and bool(pad)
        and a.Tip.TypeId == "PartDesign::Boolean"
        and abs(a.Shape.Volume - one) < 1e-6 and len(a.Shape.Solids) == 1
        and folder() == [a.Name] and shown() == []
        and b.Tip.Name in rows and c.Tip.Name in rows and pad in rows
        and not any(r["name"] == a.Tip.Name
                    for r in merged["result"]["features"]))

    # Un corps fondu n'est plus ni actif, ni outil, ni à fondre ailleurs.
    refused = [call("set_active_body", body=b.Name),
               call("add_boolean", tool=b.Name, type="fuse")]
    rect(0, 30, 10, 40)
    refused.append(call("add_pad", length=5, bodies=[c.Name]))
    report["p95_corps_fondu_refuse"] = (
        all(r.get("ok") is False and "est fondu dans" in str(r.get("error"))
            for r in refused)
        and self._require_body() is a)

    # Désactiver la fonction rend les corps ; la réactiver les refond.
    call("set_suppressed", features=[pad], suppressed=True)
    apart = (folder() == [a.Name, b.Name, c.Name]
             and shown() == [b.Name, c.Name]
             and abs(a.Shape.Volume - 4000) < 1e-6)
    call("set_suppressed", features=[pad], suppressed=False)
    report["p95_desactiver_rend_les_corps"] = (
        apart and folder() == [a.Name]
        and abs(a.Shape.Volume - one) < 1e-6)

    # Barre au-dessus : chaque corps à son rang, même ceux qui ne sont
    # pas encore nés ; redescendue, la fusion revient.
    up = call("set_tip", feature=first)
    above = (up.get("ok") is True and abs(a.Shape.Volume - 4000) < 1e-6
             and folder() == [a.Name, b.Name, c.Name])
    down = call("tip_to_end")
    report["p95_barre_au_dessus"] = (
        above and down.get("ok") is True and folder() == [a.Name]
        and abs(a.Shape.Volume - one) < 1e-6 and clean())

    # Supprimer la fonction rend les corps ; Ctrl+Z les refond.
    call("delete_feature", feature=pad)
    freed = (folder() == [a.Name, b.Name, c.Name]
             and abs(b.Shape.Volume - 4000) < 1e-6
             and not any(o.TypeId == "PartDesign::Boolean"
                         for o in a.Group))
    call("undo")
    report["p95_supprimer_et_annuler"] = (
        freed and folder() == [a.Name]
        and abs(a.Shape.Volume - one) < 1e-6 and clean())

    # « Supprimer des corps » posée après : sa réédition ne propose pas
    # les corps fondus. Le rejeu d'une fonction qui fond est refusé.
    self.add_body()
    rect(0, 40, 10, 50)
    self.add_pad(5)
    d = self._require_body()
    removal = call("add_remove_bodies", targets=[{"name": d.Name}])
    host = next((r["name"] for r in (removal.get("result") or {}).get(
        "features", []) + (removal.get("result") or {}).get(
        "other_features", []) if r.get("role") == "remove"), None)
    if host is None:
        host = self._removal_hosts()[-1].Name
    info = call("remove_bodies_info", feature=host).get("result") or {}
    offered = sorted(c["name"] for c in info.get("candidates", []))
    from engine.replay import capture_group
    try:
        capture_group(self, [pad])
        captured = True
    except KernelError as exc:
        captured = "fond d'autres corps" not in str(exc)
    report["p95_suppression_et_rejeu"] = (
        removal.get("ok") is True and offered == sorted([a.Name, d.Name])
        and not captured)

    # Une révolution fond aussi ; un « Combiner » laisse la barre monter
    # au-dessus de son corps outil.
    self.new_part("Combiner sous la barre")
    rect(0, 0, 20, 20)
    first = self.add_pad(10)["features"][0]["name"]
    a = self._require_body()
    self.add_body()
    rect(10, 0, 40, 20)
    self.add_pad(10)
    b = self._require_body()
    self.set_active_body(a.Name)
    combined = call("add_boolean", tool=b.Name, type="fuse")
    up = call("set_tip", feature=first)
    above = (up.get("ok") is True and abs(a.Shape.Volume - 4000) < 1e-6
             and folder() == [a.Name, b.Name])
    down = call("tip_to_end")
    report["p95_combiner_sous_la_barre"] = (
        combined.get("ok") is True and above and down.get("ok") is True
        and folder() == [a.Name] and abs(a.Shape.Volume - 8000) < 1e-6
        and clean())
    self.new_part("Révolution qui fond")
    rect(0, 0, 20, 20)
    self.add_pad(10)
    a = self._require_body()
    self.add_body()
    rect(30, 0, 50, 20)
    self.add_pad(10)
    b = self._require_body()
    self.set_active_body(a.Name)
    ring = self.sketch_start(plane="XZ")["sketch"]
    self.sketch_add_rectangle(ring, 15, 0, 35, 5)
    self.sketch_finish(ring)
    turned = call("add_revolution", sketch=ring, angle=360, bodies=[b.Name])
    report["p95_revolution_fond"] = (
        turned.get("ok") is True and folder() == [a.Name]
        and len(a.Shape.Solids) == 1 and a.Shape.Volume > 8000 and clean())

    # Une paroi mince fermée désactivée part en entier, sa cavité aussi :
    # tournée vers le bloc, la cavité restée seule le creuserait.
    self.new_part("Paroi désactivée")
    self.add_rect_sketch(40, 20)
    self.add_pad(10)
    a = self._require_body()
    rect_name = self.sketch_start(face=self._top_face_id())["sketch"]
    self.sketch_add_rectangle(rect_name, -10, -5, 10, 5)
    self.sketch_finish(rect_name)
    before = a.Shape.Volume
    capped = self.add_pad(6, reversed=True, thin={
        "type": "un", "thickness": 2, "caps": 1})["features"][-1]["name"]
    hollow = a.Shape.Volume < before - 1
    call("set_suppressed", features=[capped], suppressed=True)
    report["p95_paroi_desactivee"] = (
        hollow and abs(a.Shape.Volume - before) < 1e-6 and clean())


def p96_corps_fondus_reedites(self, mark, report, etat):
    mark("p96: les corps qu'un volume fond se rééditent")
    from engine.kernel import dispatch

    def call(op, **params):
        return dispatch(self, op, params)

    def rect(x1, y1, x2, y2, **where):
        name = self.sketch_start(**(where or {"plane": "XY"}))["sketch"]
        self.sketch_add_rectangle(name, x1, y1, x2, y2)
        self.sketch_finish(name)
        return name

    def folder():
        return [b["name"] for b in self.get_tree()["bodies"]]

    def row(name):
        tree = self.get_tree()
        return next(r for r in tree["features"] + tree["other_features"]
                    if r["name"] == name)

    def clean():
        return not any("Invalid" in (o.State or ()) for o in self._doc.Objects)

    self.new_part("Corps fondus rééditer")
    rect(0, 0, 20, 20)
    self.add_pad(10)
    a = self._require_body()
    self.add_body()
    rect(30, 0, 50, 20)
    self.add_pad(10)
    b = self._require_body()
    self.add_body()
    rect(60, 0, 80, 20)
    self.add_pad(10)
    c = self._require_body()
    self.set_active_body(a.Name)
    rect(10, 5, 70, 15)
    call("add_pad", length=5, bodies=[b.Name])
    pad = self._thin_owner(a.Tip).Name
    first = (folder() == [a.Name, c.Name]
             and [f["name"] for f in row(pad).get("fused", [])] == [b.Name])

    # Ajouter C et changer la profondeur, d'un même OK.
    more = call("set_params", feature=pad, values={"length": 6,
                                                   "bodies": [b.Name, c.Name]})
    three = 3 * 4000 + 3600 - 2400
    added = (more.get("ok") is True and folder() == [a.Name]
             and abs(a.Shape.Volume - three) < 1e-6
             and len(a.Shape.Solids) == 1
             and [f["name"] for f in row(pad)["fused"]] == [b.Name, c.Name])
    call("undo")
    undone = (folder() == [a.Name, c.Name]
              and abs(float(self._doc.getObject(pad).Length) - 5) < 1e-6)
    report["p96_ajouter_un_corps"] = first and added and undone and clean()

    # Plus aucun corps : le combiner caché part, la fonction reste.
    none = call("set_params", feature=pad, values={"bodies": []})
    report["p96_retirer_tous_les_corps"] = (
        none.get("ok") is True and folder() == [a.Name, b.Name, c.Name]
        and not any(o.TypeId == "PartDesign::Boolean" for o in a.Group)
        and abs(a.Shape.Volume - (4000 + 3000 - 500)) < 1e-6
        and "fused" not in row(pad) and clean())

    # Une fonction suivie d'une autre : le combiner se pose juste après
    # elle, la suivante se rebranche dessus, la pointe ne bouge pas.
    rect(0, 30, 10, 40)
    self.add_pad(4)
    after = self._last_body_feature(a)
    back = call("set_params", feature=pad, values={"bodies": [c.Name]})
    fuse = self._fuse_helper(self._doc.getObject(pad))
    report["p96_inserer_au_milieu"] = (
        back.get("ok") is True and fuse is not None
        and fuse.BaseFeature is self._doc.getObject(pad)
        and after.BaseFeature is fuse and a.Tip is after
        and folder() == [a.Name, b.Name]
        and abs(a.Shape.Volume - (4000 + 3000 - 500 + 4000 - 500 + 400))
        < 1e-6 and clean())

    # Refus : une esquisse ne fond rien (un enlèvement creuse, p99) ; un
    # corps fondu ailleurs non plus.
    sketch = rect(2, 2, 4, 4, face=self._top_face_id())
    refused = [call("set_params", feature=sketch,
                    values={"bodies": [b.Name]}),
               call("set_params", feature=after.Name, values={"bodies": [c.Name]})]
    report["p96_refus"] = (
        refused[0].get("ok") is False
        and "volume ajouté" in str(refused[0].get("error"))
        and refused[1].get("ok") is False
        and "est fondu dans" in str(refused[1].get("error")) and clean())

    # Une révolution aussi.
    self.new_part("Révolution rééditée")
    rect(0, 0, 20, 20)
    self.add_pad(10)
    a = self._require_body()
    self.add_body()
    rect(30, 0, 50, 20)
    self.add_pad(10)
    b = self._require_body()
    self.set_active_body(a.Name)
    ring = rect(15, 0, 35, 5, plane="XZ")
    # L'anneau touche B : sans liste, il le fondrait dès la création.
    call("add_revolution", sketch=ring, angle=360, bodies=[])
    turned = self._thin_owner(a.Tip).Name
    alone = folder() == [a.Name, b.Name]
    fused = call("set_params", feature=turned, values={"bodies": [b.Name]})
    report["p96_revolution"] = (
        alone and fused.get("ok") is True and folder() == [a.Name]
        and len(a.Shape.Solids) == 1 and clean())

    # Une fonction désactivée qu'on réédite : son combiner l'est aussi.
    call("set_params", feature=turned, values={"bodies": []})
    call("set_suppressed", features=[turned], suppressed=True)
    off = call("set_params", feature=turned, values={"bodies": [b.Name]})
    stays = folder() == [a.Name, b.Name]
    call("set_suppressed", features=[turned], suppressed=False)
    report["p96_fonction_desactivee"] = (
        off.get("ok") is True and stays and folder() == [a.Name]
        and clean())

    # Barre levée au-dessus du combiner : le corps qu'il tient reparaît,
    # mais ne se fond pas une seconde fois — FreeCAD le lui prendrait.
    self.new_part("Corps tenu sous la barre")
    rect(0, 0, 20, 20)
    self.add_pad(10)
    a = self._require_body()
    self.add_body()
    rect(30, 0, 50, 20)
    self.add_pad(10)
    b = self._require_body()
    b_pad = b.Tip.Name
    self.set_active_body(a.Name)
    rect(10, 5, 40, 15)
    call("add_pad", length=5, bodies=[b.Name])
    call("set_tip", feature=b_pad)
    shown = folder() == [a.Name, b.Name]
    self.set_active_body(a.Name)
    rect(0, 30, 10, 40)
    held = [call("add_pad", length=5, bodies=[b.Name]),
            call("add_boolean", tool=b.Name, type="fuse")]
    call("tip_to_end")
    report["p96_corps_tenu_sous_la_barre"] = (
        shown and all(r.get("ok") is False and "déjà fondu" in str(r.get("error"))
                for r in held)
        and folder() == [a.Name] and clean())


def p97_fusion_des_corps_touches(self, mark, report, etat):
    mark("p97: « Fusionner » fond les corps que le volume touche")
    from engine.kernel import dispatch

    def call(op, **params):
        return dispatch(self, op, params)

    def rect(x1, y1, x2, y2, **where):
        name = self.sketch_start(**(where or {"plane": "XY"}))["sketch"]
        self.sketch_add_rectangle(name, x1, y1, x2, y2)
        self.sketch_finish(name)
        return name

    def folder():
        return [b["name"] for b in self.get_tree()["bodies"]]

    def clean():
        return not any("Invalid" in (o.State or ()) for o in self._doc.Objects)

    def box(x1, y1, x2, y2):
        # Un corps vide, puis son premier volume : un corps à part.
        self.add_body()
        rect(x1, y1, x2, y2)
        call("add_pad", length=10)
        return self._require_body()

    def fused_by(body):
        row = next(r for r in self.get_tree()["features"]
                   if r["name"] == self._thin_owner(body.Tip).Name)
        return [f["name"] for f in row.get("fused", [])]

    self.new_part("Corps touchés")
    rect(0, 0, 20, 20)
    self.add_pad(10)
    a = self._require_body()
    b = box(20, 0, 40, 20)   # contre A par une face
    c = box(60, 0, 80, 20)
    d = box(100, 0, 120, 20)
    report["p97_corps_vide"] = (
        folder() == [a.Name, b.Name, c.Name, d.Name] and clean())

    # Une barre posée contre C par une face : C se fond dans B, rien
    # d'autre. Un cube qui ne touche D que par une arête : pas fondu.
    self.set_active_body(b.Name)
    rect(40, 5, 60, 15)
    face = call("add_pad", length=5)
    one = (face.get("ok") is True and folder() == [a.Name, b.Name, d.Name]
           and fused_by(b) == [c.Name] and len(b.Shape.Solids) == 1
           and abs(b.Shape.Volume - (4000 + 4000 + 1000)) < 1e-6)
    rect(90, 20, 100, 30)
    edge = call("add_pad", length=10)
    report["p97_face_oui_arete_non"] = (
        one and edge.get("ok") is True
        and folder() == [a.Name, b.Name, d.Name]
        and len(b.Shape.Solids) == 2 and clean())

    # Une liste, même vide, ou un corps choisi : rien d'office.
    rect(15, 5, 25, 15)
    empty = call("add_pad", length=5, bodies=[])
    rect(15, 5, 25, 15)
    chosen = call("add_pad", length=5, body=a.Name)
    report["p97_liste_ou_corps_choisi"] = (
        empty.get("ok") is True and chosen.get("ok") is True
        and folder() == [a.Name, b.Name, d.Name]
        and self._require_body() is a and clean())

    # Sans liste, dans B : A s'y fond. L'aperçu ne laisse rien ; Ctrl+Z
    # rend A ; la réédition le rend aussi.
    self.set_active_body(b.Name)
    rect(15, 5, 25, 15)
    count = len(self._doc.Objects)
    preview = dispatch(self, "preview",
                       {"op": "add_pad", "params": {"length": 3}})
    seen = (preview.get("ok") is True and len(self._doc.Objects) == count
            and folder() == [a.Name, b.Name, d.Name])
    call("add_pad", length=3)
    merged = folder() == [b.Name, d.Name] and fused_by(b) == [a.Name]
    call("undo")
    back = folder() == [a.Name, b.Name, d.Name]
    call("redo")
    pad = self._thin_owner(b.Tip).Name
    edit = call("set_params", feature=pad, values={"bodies": []})
    report["p97_apercu_annuler_reediter"] = (
        seen and merged and back and edit.get("ok") is True
        and folder() == [a.Name, b.Name, d.Name] and fused_by(b) == []
        and clean())

    # Une révolution aussi.
    self.set_active_body(d.Name)
    ring = rect(90, 0, 100, 5, plane="XZ")
    turned = call("add_revolution", sketch=ring, angle=360)
    report["p97_revolution"] = (
        turned.get("ok") is True and b.Name not in folder()
        and fused_by(d) == [b.Name] and clean())

    # Barre levée au-dessus d'un « Combiner » : le corps qu'il tient
    # reparaît, mais un volume qui le touche ne le lui prend pas.
    self.new_part("Corps tenu, corps touchés")
    rect(0, 0, 20, 20)
    self.add_pad(10)
    a = self._require_body()
    b = box(30, 0, 50, 20)
    c = box(60, 0, 80, 20)
    c_pad = c.Tip.Name
    self.set_active_body(a.Name)
    call("add_boolean", tool=b.Name, type="fuse")
    combiner = a.Tip
    call("set_tip", feature=c_pad)
    shown = folder() == [a.Name, b.Name, c.Name]
    self.set_active_body(c.Name)
    rect(45, 5, 65, 15)
    taken = call("add_pad", length=5)
    call("tip_to_end")
    report["p97_corps_tenu"] = (
        shown and taken.get("ok") is True
        and b in self._boolean_tools(combiner) and fused_by(c) == []
        and folder() == [a.Name, c.Name] and clean())

    # Une copie de réseau, figée au rang du réseau, se fond dans sa source
    # comme un autre corps : sans boucler le graphe.
    self.new_part("Copie touchée")
    self.add_rect_sketch(10, 10)
    self.add_pad(8)
    source = self._require_body()
    self.add_body_pattern("linear", [source.Name], length=20, count=2,
                          axis="X", spacing=True)
    copies = [n for n in folder() if n != source.Name]
    self.set_active_body(source.Name)
    rect(0, -2, 16, 2)
    reached = call("add_pad", length=4)
    report["p97_copie_de_reseau"] = (
        reached.get("ok") is True and len(copies) == 1
        and folder() == [source.Name] and fused_by(source) == copies
        and len(source.Shape.Solids) == 1
        and abs(source.Shape.Volume - (800 + 800 + 256 - 80 - 16)) < 1e-6
        and clean())

    # Une répétition variable rejoue son groupe dans un corps provisoire,
    # au contact du corps hôte : le second volume ne doit pas l'y fondre,
    # sinon la copie emporterait tout le corps.
    self.new_part("Répétition, corps touchés")
    self.add_rect_sketch(20, 20)
    self.add_pad(10)
    host = self._require_body()
    rect(5, -5, 15, 5)
    self.add_pad(5)
    first = self._thin_owner(host.Tip).Name
    rect(12, -2, 20, 2)
    self.add_pad(8)
    second = self._thin_owner(host.Tip).Name
    alone = abs(host.Shape.Volume - 4446) < 1e-6
    # Deux copies empilées, qui se touchent : 696 mm³ chacune.
    repeated = call("add_repeat_feature", features=[first, second],
                    instances=[{"offset": [0, 0, 10]}, {"offset": [0, 0, 18]}],
                    mode="fuse")
    report["p97_repetition_variable"] = (
        alone and repeated.get("ok") is True
        and abs(host.Shape.Volume - (4446 + 2 * 696)) < 1e-6
        and folder() == [host.Name] and clean())

    # Une esquisse sur XZ : la forme ajoutée est dans le repère tourné de
    # sa fonction. La barre entre dans B, posé à côté.
    self.new_part("Corps touchés sur XZ")
    rect(0, 0, 20, 20, plane="XZ")
    self.add_pad(10)
    a = self._require_body()
    b = box(30, -10, 50, 0)
    self.set_active_body(a.Name)
    rect(15, 5, 35, 10, plane="XZ")
    standing = call("add_pad", length=4)
    report["p97_esquisse_sur_xz"] = (
        standing.get("ok") is True and folder() == [a.Name]
        and fused_by(a) == [b.Name] and len(a.Shape.Solids) == 1
        and clean())

    # Une paroi mince fermée autour d'un corps qui ne la touche pas : la
    # cavité n'est pas de la matière, le corps reste à part.
    self.new_part("Enceinte")
    rect(0, 0, 10, 10)
    self.add_pad(5)
    inner = self._require_body()
    host = box(40, 0, 60, 20)
    rect(-10, -10, 20, 20)
    walls = call("add_pad", length=20, midplane=True,
                 thin={"type": "un", "thickness": 2, "caps": 2})
    report["p97_paroi_fermee_autour"] = (
        walls.get("ok") is True and folder() == [inner.Name, host.Name]
        and fused_by(host) == [] and abs(inner.Shape.Volume - 500) < 1e-6
        and clean())


def p98_enlevement_traversant(self, mark, report, etat):
    mark("p98: un enlèvement creuse tous les corps qu'il traverse")
    from engine.kernel import dispatch
    from engine.replay import capture_group

    def call(op, **params):
        return dispatch(self, op, params)

    def rect(x1, y1, x2, y2, **where):
        name = self.sketch_start(**(where or {"plane": "XY"}))["sketch"]
        self.sketch_add_rectangle(name, x1, y1, x2, y2)
        self.sketch_finish(name)
        return name

    def clean():
        return not any("Invalid" in (o.State or ()) for o in self._doc.Objects)

    def rows():
        tree = self.get_tree()
        return [r["name"] for r in tree["features"]
                + tree.get("other_features", [])]

    def side_by_side(title):
        # A et B côte à côte, 20 × 20 × 10 chacun.
        self.new_part(title)
        rect(0, 0, 20, 20)
        self.add_pad(10)
        a = self._require_body()
        rect(20, 0, 40, 20)
        call("add_pad", length=10, merge=False)
        b = self._require_body()
        self.set_active_body(a.Name)
        return a, b

    def shape_parts():
        return [o.Name for o in self._doc.Objects
                if o.Name.startswith("ScopeShape")]

    # Une rainure à travers tout, de A dans B : les deux sont creusés, une
    # seule ligne dans l'arbre, et elle dit ce qu'elle creuse aussi.
    a, b = side_by_side("Enlèvement traversant")
    b_pad = b.Tip.Name
    before = rows()
    rect(10, 5, 30, 15)
    cut = call("add_pocket", through=True, reversed=True)
    pocket = self._thin_owner(a.Tip).Name
    tree = self.get_tree()
    row = next(r for r in tree["features"] if r["name"] == pocket)
    # Les deux corps portent son nom, numérotés ; la bulle nomme B ainsi.
    label = self._doc.getObject(pocket).Label
    named = [label + "[1]", label + "[2]"]
    report["p98_deux_corps_creuses"] = (
        cut.get("ok") is True and abs(a.Shape.Volume - 3000) < 1e-6
        and abs(b.Shape.Volume - 3000) < 1e-6
        and sorted(rows()) == sorted(before + [pocket])
        and [r["label"] for r in tree["bodies"]] == named
        and row.get("scope") == named[1:]
        and self._is_thin_helper(b.Tip) and clean())

    # La barre au-dessus de l'enlèvement le retire de B aussi ; posée sur
    # lui, B est creusé.
    call("set_tip", feature=b_pad)
    above = abs(b.Shape.Volume - 4000) < 1e-6
    call("set_tip", feature=pocket)
    at = abs(b.Shape.Volume - 3000) < 1e-6
    call("tip_to_end")
    report["p98_barre_de_retour"] = above and at and clean()

    # B suit la cote rééditée, « Désactiver », la suppression et Ctrl+Z.
    call("set_params", feature=pocket, values={"cond": "borgne", "length": 3})
    deep = abs(b.Shape.Volume - 3700) < 1e-6
    call("set_suppressed", features=[pocket], suppressed=True)
    off = abs(b.Shape.Volume - 4000) < 1e-6
    call("set_suppressed", features=[pocket], suppressed=False)
    on = abs(b.Shape.Volume - 3700) < 1e-6
    call("delete_feature", feature=pocket)
    gone = abs(b.Shape.Volume - 4000) < 1e-6 and not shape_parts()
    call("undo")
    report["p98_suit_la_fonction"] = (
        deep and off and on and gone and abs(b.Shape.Volume - 3700) < 1e-6
        and len(shape_parts()) == 1 and clean())

    # Corps actif seulement : une liste vide.
    rect(2, 2, 38, 4)
    alone = call("add_pocket", length=2, reversed=True, bodies=[])
    report["p98_corps_actif_seul"] = (
        alone.get("ok") is True and abs(b.Shape.Volume - 3700) < 1e-6
        and abs(a.Shape.Volume - (3700 - 72)) < 1e-6 and clean())

    # Le rejeu d'une répétition ne capture pas un enlèvement qui creuse
    # d'autres corps : il ne creuserait que le sien.
    try:
        capture_group(self, [pocket])
        captured = True
    except KernelError as exc:
        captured = "creuse d'autres corps" not in str(exc)
    report["p98_rejeu_refuse"] = not captured

    # Celui du corps actif seul se répète, et son rejeu ne laisse aucune
    # étape cachée derrière lui.
    a, b = side_by_side("Répétition d'un enlèvement")
    rect(14, 4, 18, 8)
    self.add_pad(15)
    boss = self._thin_owner(a.Tip).Name
    rect(15, 5, 17, 7)
    call("add_pocket", through=True, reversed=True, bodies=[])
    hole = self._thin_owner(a.Tip).Name
    repeated = call("add_repeat_feature", features=[boss, hole],
                    instances=[{"offset": [0, 0, 0]}, {"offset": [-8, 0, 0]}],
                    mode="fuse")
    report["p98_repetition_d_un_enlevement"] = (
        repeated.get("ok") is True
        and abs(a.Shape.Volume - (4000 + 20 + 60)) < 1e-6
        and abs(b.Shape.Volume - 4000) < 1e-6 and not shape_parts()
        and clean())

    # Une gorge et un perçage à cheval sur les deux corps.
    a, b = side_by_side("Gorge traversante")
    ring = rect(15, 8, 25, 10, plane="XZ")
    groove = call("add_groove", sketch=ring, angle=360)
    grooved = (groove.get("ok") is True and b.Shape.Volume < 4000 - 1e-6
               and a.Shape.Volume < 4000 - 1e-6
               and self._is_thin_helper(b.Tip))
    a, b = side_by_side("Perçage traversant")
    hole = call("add_hole", diameter=4, through=True,
                face=self._top_face_id(), points=[[20, 10, 10]])
    half = math.pi * 4 * 10 / 2
    report["p98_gorge_et_percage"] = (
        grooved and hole.get("ok") is True
        and abs(b.Shape.Volume - (4000 - half)) < 1e-4
        and abs(a.Shape.Volume - (4000 - half)) < 1e-4 and clean())

    # Remonté au-dessus d'une fonction de son corps plus ancienne que celles
    # de B, il creuse encore B : son étape cachée vient après elles.
    a, b = side_by_side("Enlèvement remonté")
    rect(0, 0, 20, 5)
    call("add_pad", length=12, body=a.Name)
    boss = self._thin_owner(a.Tip).Name
    rect(20, 0, 30, 5)
    call("add_pad", length=12, body=b.Name)
    self.set_active_body(a.Name)
    rect(10, 8, 30, 12)
    call("add_pocket", through=True, reversed=True)
    pocket = self._thin_owner(a.Tip).Name
    moved = call("reorder_feature", feature=pocket, target=boss)
    call("tip_to_end")
    at_end = abs(b.Shape.Volume - (4100 - 400)) < 1e-6
    tree = self.get_tree()
    last = max(tree["features"] + tree["other_features"],
               key=lambda row: row["order"])["name"]
    call("set_tip", feature=last)
    report["p98_reordonne"] = (
        moved.get("ok") is True and at_end
        and abs(b.Shape.Volume - 3700) < 1e-6 and clean())

    # Une plaque mince sur un bloc haut : « à travers tout » traverse le
    # bloc entier, pas seulement l'encombrement de la plaque — perçage
    # compris, et quand la plaque change d'épaisseur.
    self.new_part("À travers tout, loin")
    rect(0, 0, 20, 20)
    self.add_pad(2)
    a = self._require_body()
    rect(0, 0, 20, 20)
    call("add_pad", length=100, reversed=True, merge=False)
    b = self._require_body()
    self.set_active_body(a.Name)
    plate = a.Tip.Name
    rect(5, 5, 15, 15, face=self._top_face_id())
    call("add_pocket", through=True)
    drilled = call("add_hole", diameter=4, through=True,
                   face=self._top_face_id(), points=[[2.5, 2.5, 2]])
    bore = math.pi * 4 * 100
    deep = abs(b.Shape.Volume - (40000 - 10000 - bore)) < 1e-4
    call("set_params", feature=plate, values={"length": 3})
    report["p98_a_travers_tout_loin"] = (
        drilled.get("ok") is True and deep
        and abs(b.Shape.Volume - (40000 - 10000 - bore)) < 1e-4 and clean())


def p99_corps_creuses_reedites(self, mark, report, etat):
    mark("p99: rééditer les corps qu'un enlèvement creuse")
    from engine.kernel import dispatch

    def call(op, **params):
        return dispatch(self, op, params)

    def rect(x1, y1, x2, y2, **where):
        name = self.sketch_start(**(where or {"plane": "XY"}))["sketch"]
        self.sketch_add_rectangle(name, x1, y1, x2, y2)
        self.sketch_finish(name)
        return name

    def clean():
        return not any("Invalid" in (o.State or ()) for o in self._doc.Objects)

    def ranks():
        tree = self.get_tree()
        rows = tree["features"] + tree.get("other_features", [])
        return [r["name"] for r in sorted(rows, key=lambda r: r["order"])]

    def volumes(*bodies):
        return [round(b.Shape.Volume, 6) for b in bodies]

    # Trois corps côte à côte ; l'enlèvement ne creuse d'abord que A.
    self.new_part("Corps creusés")
    bodies = []
    for x in (0, 20, 40):
        rect(x, 0, x + 20, 20)
        call("add_pad", length=10, merge=not bodies)
        bodies.append(self._require_body())
    a, b, c = bodies
    self.set_active_body(a.Name)
    rect(10, 5, 50, 15)
    call("add_pocket", through=True, reversed=True, bodies=[])
    pocket = self._thin_owner(a.Tip).Name
    alone = volumes(a, b, c) == [3000, 4000, 4000]
    before = ranks()

    def row():
        return next(r for r in self.get_tree()["features"]
                    if r["name"] == pocket)

    # Cocher B et C : creusés à leur tour ; la ligne les nomme.
    both = call("set_params", feature=pocket,
                values={"bodies": [b.Name, c.Name]})
    cut_both = (both.get("ok") is True
                and volumes(a, b, c) == [3000, 2000, 3000]
                and [x["name"] for x in row().get("cut", [])]
                == [b.Name, c.Name])
    # Décocher B : il revient ; Ctrl+Z le recreuse.
    call("set_params", feature=pocket, values={"bodies": [c.Name]})
    back = volumes(b, c) == [4000, 3000]
    call("undo")
    report["p99_cocher_decocher"] = (
        alone and cut_both and back and volumes(b, c) == [2000, 3000]
        and ranks() == before and clean())

    # Un corps coché à la réédition est creusé au rang de l'enlèvement :
    # le bossage posé ensuite sur B le recouvre sans être entamé (4400 ;
    # creusé en bout de chaîne, 4320 ; pas creusé, 4800). Ni ce bossage ni
    # la fonction de A venue après lui ne changent de rang.
    self.new_part("Corps creusé à son rang")
    rect(0, 0, 20, 20)
    self.add_pad(10)
    a = self._require_body()
    rect(20, 0, 40, 20)
    call("add_pad", length=10, merge=False)
    b = self._require_body()
    self.set_active_body(a.Name)
    rect(10, 8, 30, 12)
    call("add_pocket", through=True, reversed=True, bodies=[])
    pocket = self._thin_owner(a.Tip).Name
    self.set_active_body(b.Name)
    rect(20, 0, 40, 20, face=self._top_face_id())
    call("add_pad", length=2, bodies=[])
    self.set_active_body(a.Name)
    rect(0, 0, 5, 5, face=self._top_face_id())
    call("add_pad", length=2, bodies=[])
    before = ranks()
    call("set_params", feature=pocket, values={"bodies": [b.Name]})
    report["p99_a_son_rang"] = (
        abs(b.Shape.Volume - 4400) < 1e-6 and ranks() == before
        and clean())

    # Refus : un corps né après l'enlèvement, un enlèvement désactivé.
    rect(50, 0, 60, 10)
    call("add_pad", length=5, merge=False)
    late = self._require_body()
    born = call("set_params", feature=pocket,
                values={"bodies": [b.Name, late.Name]})
    call("set_suppressed", features=[pocket], suppressed=True)
    call("set_params", feature=pocket, values={"bodies": []})
    off = call("set_params", feature=pocket, values={"bodies": [b.Name]})
    report["p99_refus"] = (
        born.get("ok") is False
        and "n'existe pas encore" in str(born.get("error"))
        and off.get("ok") is False
        and "désactivé" in str(off.get("error")) and clean())

    # Le perçage aussi : un trou à cheval sur A et B, puis B coché.
    self.new_part("Perçage réédité")
    rect(0, 0, 20, 20)
    self.add_pad(10)
    a = self._require_body()
    rect(20, 0, 40, 20)
    call("add_pad", length=10, merge=False)
    b = self._require_body()
    self.set_active_body(a.Name)
    call("add_hole", diameter=4, through=True, face=self._top_face_id(),
         points=[[20, 10, 10]], bodies=[])
    hole = self._thin_owner(a.Tip).Name
    whole = abs(b.Shape.Volume - 4000) < 1e-6
    call("set_params", feature=hole, values={"bodies": [b.Name]})
    report["p99_percage"] = (
        whole and abs(b.Shape.Volume - (4000 - math.pi * 4 * 10 / 2)) < 1e-4
        and clean())

    # La barre au-dessus de l'enlèvement : B, coché, reste entier tant
    # qu'elle n'est pas redescendue.
    self.new_part("Réédité sous la barre")
    rect(0, 0, 20, 20)
    self.add_pad(10)
    a = self._require_body()
    rect(20, 0, 40, 20)
    call("add_pad", length=10, merge=False)
    b = self._require_body()
    b_pad = b.Tip.Name
    self.set_active_body(a.Name)
    rect(10, 8, 30, 12)
    call("add_pocket", through=True, reversed=True, bodies=[])
    pocket = self._thin_owner(a.Tip).Name
    call("set_tip", feature=b_pad)
    call("set_params", feature=pocket, values={"bodies": [b.Name]})
    above = abs(b.Shape.Volume - 4000) < 1e-6
    call("tip_to_end")
    report["p99_sous_la_barre"] = (
        above and abs(b.Shape.Volume - 3600) < 1e-6 and clean())


def p100_repetition_traversante(self, mark, report, etat):
    mark("p100: une répétition creuse les corps que ses occurrences "
         "traversent")
    from engine.kernel import dispatch

    def call(op, **params):
        return dispatch(self, op, params)

    def rect(x1, y1, x2, y2):
        name = self.sketch_start(plane="XY")["sketch"]
        self.sketch_add_rectangle(name, x1, y1, x2, y2)
        self.sketch_finish(name)
        return name

    def clean():
        return not any("Invalid" in (o.State or ()) for o in self._doc.Objects)

    def rows():
        tree = self.get_tree()
        return tree["features"] + tree.get("other_features", [])

    def volumes():
        return [round(a.Shape.Volume, 6), round(b.Shape.Volume, 6)]

    # A et B côte à côte, 20 × 20 × 10 chacun ; une rainure de A dans B
    # (100 de chaque côté), répétée deux fois le long de Y.
    self.new_part("Répétition traversante")
    rect(0, 0, 20, 20)
    self.add_pad(10)
    a = self._require_body()
    rect(20, 0, 40, 20)
    call("add_pad", length=10, merge=False)
    b = self._require_body()
    self.set_active_body(a.Name)
    rect(15, 2, 25, 4)
    call("add_pocket", through=True, reversed=True)
    pocket = self._thin_owner(a.Tip).Name
    made = call("add_linear_pattern", length=6, count=3, axis="Y",
                spacing=True, features=[pocket])
    pattern = self._doc.getObject(a.Tip.Name)
    steps = [c.Name for c in self._scope_cuts(pattern)]
    row = next(r for r in rows() if r["name"] == pattern.Name)
    # Ses étapes dans B sont cachées : la ligne de la répétition les porte.
    report["p100_creuse_les_traverses"] = (
        made.get("ok") is True and volumes() == [3700, 3700]
        and len(steps) == 1 and self._is_thin_helper(b.Tip)
        and not [r for r in rows()
                 if r["name"] in steps or r.get("edits") == pattern.Name]
        and len(row.get("scope", [])) == 1 and clean())

    # B suit la barre, la cote, « Désactiver » ; ramenée à une occurrence,
    # la répétition ne creuse plus rien.
    call("set_tip", feature=pocket)
    above = volumes() == [3900, 3900]
    call("tip_to_end")
    call("set_params", feature=pattern.Name, values={"count": 2})
    two = volumes() == [3800, 3800]
    call("set_suppressed", features=[pattern.Name], suppressed=True)
    off = volumes() == [3900, 3900]
    call("set_suppressed", features=[pattern.Name], suppressed=False)
    call("set_params", feature=pattern.Name, values={"count": 1})
    one = volumes() == [3900, 3900]
    call("set_params", feature=pattern.Name, values={"count": 3})
    report["p100_suit_la_repetition"] = (
        above and two and off and one and volumes() == [3700, 3700]
        and clean())

    # Les occurrences seules : décocher B dans l'enlèvement rend sa place.
    call("set_params", feature=pocket, values={"bodies": []})
    report["p100_occurrences_seules"] = (
        volumes() == [3700, 3800] and clean())

    # Corps actif seulement : une liste vide.
    alone = call("add_linear_pattern", length=3, count=2, axis="Y",
                 spacing=True, features=[pocket], scope=[])
    report["p100_corps_actif_seul"] = (
        alone.get("ok") is True and volumes() == [3600, 3800] and clean())

    # Une répétition d'un fichier d'avant : toutes ses occurrences
    # creusent, ses booléens restent des lignes de l'arbre.
    pattern.removeProperty(self._SCOPE_INSTANCES)
    for step in self._scope_cuts(pattern):
        step.removeProperty(self._THIN_HELPER)
        step.removeProperty("FreeSolidThinOwner")
    self._recompute()
    report["p100_fichier_d_avant"] = (
        volumes() == [3600, 3700]
        and [r["edits"] for r in rows() if r["name"] in steps]
        == [pattern.Name] and clean())


def p101_repetition_corps_reedites(self, mark, report, etat):
    mark("p101: rééditer les corps qu'une répétition creuse")
    from engine.kernel import dispatch

    def call(op, **params):
        return dispatch(self, op, params)

    def rect(x1, y1, x2, y2, **where):
        name = self.sketch_start(**(where or {"plane": "XY"}))["sketch"]
        self.sketch_add_rectangle(name, x1, y1, x2, y2)
        self.sketch_finish(name)
        return name

    def clean():
        return not any("Invalid" in (o.State or ()) for o in self._doc.Objects)

    def rows():
        tree = self.get_tree()
        return tree["features"] + tree.get("other_features", [])

    def row(name):
        return next(r for r in rows() if r["name"] == name)

    def ranks():
        return [r["name"] for r in sorted(rows(), key=lambda r: r["order"])]

    def volumes():
        return [round(a.Shape.Volume, 6), round(b.Shape.Volume, 6)]

    def refused(answer, words):
        return answer.get("ok") is False and words in str(answer.get("error"))

    # A et B côte à côte, 20 × 20 × 10, symétriques par rapport au plan de
    # face. Une rainure de A dans B, qui ne creuse que A, répétée une fois
    # le long de Y et symétrisée, sans corps concernés ; puis un bossage
    # de 2 sur B.
    self.new_part("Répétition rééditée")
    rect(0, -10, 20, 10)
    self.add_pad(10)
    a = self._require_body()
    rect(20, -10, 40, 10)
    call("add_pad", length=10, merge=False)
    b = self._require_body()
    self.set_active_body(a.Name)
    rect(15, 2, 25, 4)
    call("add_pocket", through=True, reversed=True, bodies=[])
    pocket = self._thin_owner(a.Tip).Name
    call("add_linear_pattern", length=3, count=2, axis="Y", spacing=True,
         features=[pocket], scope=[])
    linear = a.Tip.Name
    call("add_mirror", plane="XZ", features=[pocket], scope=[])
    mirror = a.Tip.Name
    self.set_active_body(b.Name)
    rect(20, -10, 40, 10, face=self._top_face_id())
    call("add_pad", length=2, bodies=[])
    before = ranks()
    offered = (volumes() == [3700, 4800] and row(linear).get("cut") == []
               and row(mirror).get("cut") == []
               and row(mirror).get("has_params") is False)

    # Cocher B : ses occurrences le creusent, à leur rang — le bossage qui
    # le recouvre n'est pas entamé (creusé en bout de chaîne, 4680). La
    # rainure elle-même ne creuse toujours pas B.
    added = call("set_params", feature=linear, values={"bodies": [b.Name]})
    at_rank = volumes() == [3700, 4700]
    call("set_params", feature=mirror, values={"bodies": [b.Name]})
    both = (volumes() == [3700, 4600]
            and [x["name"] for x in row(linear).get("cut", [])] == [b.Name]
            and [x["name"] for x in row(mirror).get("cut", [])] == [b.Name])
    hidden = not [r for r in rows() if r.get("edits") in (linear, mirror)]
    # Décocher B : il revient ; Ctrl+Z le recreuse.
    call("set_params", feature=linear, values={"bodies": []})
    back = volumes() == [3700, 4700]
    call("undo")
    report["p101_cocher_decocher"] = (
        offered and added.get("ok") is True and at_rank and both and hidden
        and back and volumes() == [3700, 4600] and ranks() == before
        and clean())

    # Refus : une répétition ramenée à la fonction répétée, une symétrie
    # désactivée, une répétition d'extrusion. Décocher passe toujours.
    call("set_params", feature=linear, values={"count": 1})
    call("set_params", feature=linear, values={"bodies": []})
    lone = call("set_params", feature=linear, values={"bodies": [b.Name]})
    call("set_params", feature=linear, values={"count": 2})
    call("set_suppressed", features=[mirror], suppressed=True)
    call("set_params", feature=mirror, values={"bodies": []})
    off = call("set_params", feature=mirror, values={"bodies": [b.Name]})
    call("set_suppressed", features=[mirror], suppressed=False)
    self.set_active_body(a.Name)
    rect(0, -10, 2, -8, face=self._top_face_id())
    call("add_pad", length=2, bodies=[])
    boss = a.Tip.Name
    call("add_linear_pattern", length=4, count=2, axis="X", spacing=True,
         features=[boss], scope=[])
    bosses = a.Tip.Name
    no_cut = call("set_params", feature=bosses, values={"bodies": [b.Name]})
    report["p101_refus"] = (
        refused(lone, "pas d'autre occurrence") and refused(off, "désactivé")
        and refused(no_cut, "seuls les enlèvements")
        and "cut" not in row(bosses) and volumes()[1] == 4800 and clean())

    # Fichiers d'avant. Une répétition qui ne creusait rien devient neuve
    # en cochant B ; une qui creusait déjà garde ses lignes.
    mirror_obj = self._doc.getObject(mirror)
    mirror_obj.removeProperty(self._SCOPE_INSTANCES)
    offered = row(mirror).get("cut") == []
    call("set_params", feature=mirror, values={"bodies": [b.Name]})
    renewed = (volumes()[1] == 4700
               and getattr(mirror_obj, self._SCOPE_INSTANCES, False)
               and all(self._is_thin_helper(c)
                       for c in self._scope_cuts(mirror_obj)))
    call("set_params", feature=linear, values={"bodies": [b.Name]})
    linear_obj = self._doc.getObject(linear)
    linear_obj.removeProperty(self._SCOPE_INSTANCES)
    for step in self._scope_cuts(linear_obj):
        step.removeProperty(self._THIN_HELPER)
        step.removeProperty("FreeSolidThinOwner")
    self._recompute()
    kept = call("set_params", feature=linear, values={"bodies": []})
    report["p101_fichier_d_avant"] = (
        offered and renewed and volumes()[1] == 4500
        and "cut" not in row(linear)
        and refused(kept, "fichier d'avant") and clean())


def protocol_dangling(tree):
    from engine import protocol
    return protocol.dangling_deps(tree)


def _volumes(self):
    """Volume de chaque corps de la pièce (outils internes exclus)."""
    return {o.Name: o.Shape.Volume for o in self._doc.Objects
            if o.TypeId == "PartDesign::Body"
            and not self._is_internal_tool(o)}


def _centre_x(self, name):
    bb = self._doc.getObject(name).Shape.BoundBox
    return (bb.XMin + bb.XMax) / 2, (bb.YMin + bb.YMax) / 2


def p82_reseau_de_corps(self, mark, report, etat):
    mark("p82: réseau de corps — chaque occurrence est un corps")
    import tempfile
    self.new_part("Réseau de corps")
    self.add_rect_sketch(10, 10)
    self.add_pad(8)
    source = self._require_body().Name
    pad = self._require_body().Tip.Name
    self.add_body_pattern("linear", [source], length=20, count=3,
                          axis="X", spacing=True)
    host = self._body_pattern_hosts()[0]
    copies = [n for n in _volumes(self) if n != source]
    centres = sorted(round(_centre_x(self, n)[0], 6) for n in copies)
    report["p82_lineaire"] = (
        len(copies) == 2 and centres == [20.0, 40.0]
        and all(abs(v - 800) < 1e-6 for v in _volumes(self).values()))
    # Le réseau est une ligne de l'arbre de sa source ; ses copies
    # s'affichent arêtes comprises, et la source aussi quand une copie
    # est active.
    rows = [f for f in self.get_tree()["features"]
            if f["type_key"] == "body_pattern"]
    shown = {b["name"]: b for b in self.tessellate().get("other_bodies", [])}
    self.set_active_body(copies[0])
    from_copy = {b["name"]: b
                 for b in self.tessellate().get("other_bodies", [])}
    self.set_active_body(source)
    titles = ["{}[{}]".format(host.Label, i) for i in (1, 2)]
    report["p82_ligne_et_vue"] = (
        len(rows) == 1 and rows[0]["name"] == host.Name
        and sorted(rows[0].get("copies") or ()) == titles
        and all(shown.get(n, {}).get("edges", {}).get("indices")
                for n in copies)
        and all(from_copy.get(n, {}).get("groups")
                for n in (source, copies[1])))
    # Le dossier nomme chaque corps d'après sa dernière fonction ; un
    # corps nommé à la main garde son nom.
    named = {b["name"]: b["label"] for b in self.get_tree()["bodies"]}
    self.rename(copies[1], "Bloc")
    renamed = {b["name"]: b["label"] for b in self.get_tree()["bodies"]}
    report["p82_noms_des_corps"] = (
        named[source] == self._doc.getObject(pad).Label
        and sorted(named[n] for n in copies) == titles
        and renamed[copies[1]] == "Bloc")
    # La source change après le réseau : les copies n'en héritent pas ;
    # une cote d'avant le réseau passe. La cote du réseau se réédite.
    self.set_active_body(source)
    top = self._top_face_id()
    self.add_rect_sketch(4, 4, face=top)
    self.add_pocket(2)
    self.set_params(host.Name, {"count": 4})
    after = _volumes(self)
    self.set_params(pad, {"length": 10})
    upstream = _volumes(self)
    self.set_params(pad, {"length": 8})
    report["p82_suit_la_source"] = (
        len(after) == 4 and abs(after[source] - 768) < 1e-6
        and all(abs(v - 800) < 1e-6
                for n, v in after.items() if n != source)
        and abs(upstream[source] - 968) < 1e-6
        and all(abs(v - 1000) < 1e-6
                for n, v in upstream.items() if n != source))
    # Le réseau a son rang : l'enlèvement ajouté ensuite vient dessous.
    # La barre au-dessus de lui, ses copies n'existent pas encore ; posée
    # sur lui, elles reviennent, sans l'enlèvement.
    pocket = self._require_body().Tip.Name
    host_name = host.Name
    ranks = {f["name"]: f["order"] for f in self.get_tree()["features"]}
    grown = list(self._body_pattern_copies(host).values())
    hidden = {f["name"]: f.get("rolled_back")
              for f in self.set_tip(pad)["features"]}
    unborn = all(copy.Tip is None for copy in grown)
    shown = {f["name"]: f.get("rolled_back")
             for f in self.set_tip(host.Name)["features"]}
    back = _volumes(self)
    self.tip_to_end()
    # Une fonction sur une copie vient aussi sous le réseau, et y reste
    # quand on annule sa suppression (FreeCAD rend les objets en fin de
    # document).
    from engine.kernel import dispatch
    grown = [copy.Name for copy in grown]
    self.set_active_body(grown[0])
    self.add_fillet(radius=0.5, face=self._top_face_id())
    fillet = self._require_body().Tip.Name
    for op, params in (("set_tip", {"feature": pad}),
                       ("delete_rolled_back", {})):
        if not dispatch(self, op, params)["ok"]:
            raise KernelError(op)
    gone = all(self._doc.getObject(name) is None
               for name in grown + [fillet, host_name])
    self.undo()
    self.tip_to_end()
    self.set_active_body(source)
    host = self._doc.getObject(host_name)
    tree = self.get_tree()
    restored = {f["name"]: f["order"]
                for f in tree["features"] + tree["other_features"]}
    report["p82_reseau_a_son_rang"] = (
        ranks[pad] < ranks[host.Name] < ranks[pocket]
        and hidden.get(host.Name) is True and unborn
        and shown.get(host.Name) is False and shown.get(pocket) is True
        and len(back) == 4
        and all(abs(v - 800) < 1e-6 for v in back.values())
        and gone and restored[host_name] < restored.get(fillet, -1)
        and len(_volumes(self)) == 4)
    # Une copie supprimée reste sautée ; la source est protégée.
    far = max(copies, key=lambda n: _centre_x(self, n)[0])
    self.delete_feature(far)
    self.set_params(host.Name, {"length": 25})
    shifted = sorted(round(_centre_x(self, n)[0], 6)
                     for n in _volumes(self) if n != source)
    try:
        self.delete_feature(source)
        protected = False
    except KernelError:
        protected = True
    report["p82_copie_sautee"] = shifted == [25.0, 75.0] and protected
    # Symétrie d'une copie, réseau circulaire : d'autres corps encore.
    near = min((n for n in _volumes(self) if n != source),
               key=lambda n: _centre_x(self, n)[0])
    before = set(_volumes(self))
    self.add_body_pattern("mirror", [near], plane="YZ")
    mirrored = (set(_volumes(self)) - before).pop()
    before = set(_volumes(self))
    self.add_body_pattern("polar", [near], count=4, angle=360, axis="Z")
    turned = sorted((round(x, 6), round(y, 6)) for x, y in (
        _centre_x(self, n) for n in set(_volumes(self)) - before))
    report["p82_symetrie_circulaire"] = (
        abs(_centre_x(self, mirrored)[0] + 25) < 1e-6
        and turned == [(-25.0, 0.0), (0.0, -25.0), (0.0, 25.0)])
    # Rouvert : les mêmes volumes, objets FreeCAD standard.
    volumes = _volumes(self)
    path = os.path.join(tempfile.gettempdir(),
                        "freesolid-selftest-reseau-corps.FCStd")
    self.save_part(path)
    self.open_part(path)
    reopened = _volumes(self)
    report["p82_rouvert"] = (
        set(reopened) == set(volumes)
        and all(abs(reopened[n] - volumes[n]) < 1e-6 for n in volumes))
    # La source se combine avec sa propre copie : la copie lit une
    # fonction d'avant le réseau, le graphe ne boucle pas.
    self.set_active_body(source)
    copy = next(c.Name for c in self._body_pattern_copies(
        self._doc.getObject(host_name)).values() if c.Name != near)
    self.add_boolean(tool=copy, type="fuse")
    report["p82_combine_sa_copie"] = abs(
        _volumes(self)[source] - reopened[source] - reopened[copy]) < 1e-6


def p83_corps_concernes(self, mark, report, etat):
    mark("p83: corps concernés — les trous répétés creusent l'autre corps")
    self.new_part("Corps concernés")
    self.add_rect_sketch(60, 20)
    self.add_pad(5)
    top = self._require_body().Name
    self.add_body("Dessous")
    low = self._require_body().Name
    self.add_rect_sketch(60, 20)
    self.add_pad(5, reversed=True)
    self.set_active_body(top)
    sketch = self.sketch_start(face=self._top_face_id())["sketch"]
    self.sketch_add_circle(sketch, -20, 0, 2)
    self.sketch_finish(sketch)
    # Le trou ne creuse que son corps : seules les occurrences répétées
    # creusent l'autre.
    self.add_pocket(through=True, bodies=[])
    hole = math.pi * 4 * 5
    tree = self.add_linear_pattern(20, 3, axis="X", spacing=True,
                                   scope=[low])
    pattern = next(f for f in tree["features"]
                   if f["type"] == "PartDesign::LinearPattern")
    volumes = _volumes(self)
    report["p83_creuse_l_autre"] = (
        abs(volumes[low] - (6000 - 2 * hole)) < 1e-6
        and abs(volumes[top] - (6000 - 3 * hole)) < 1e-6
        and len(pattern.get("scope", [])) == 1)
    self.set_params(pattern["name"], {"count": 2})
    two = _volumes(self)[low]
    self.set_suppressed([pattern["name"]], True)
    off = _volumes(self)[low]
    self.set_suppressed([pattern["name"]], False)
    try:
        self.add_rect_sketch(4, 4, face=self._top_face_id())
        self.add_pad(2)
        self.add_linear_pattern(10, 2, axis="Y", scope=[low])
        refused = False
    except KernelError:
        refused = True
    report["p83_suit_et_refuse"] = (
        abs(two - (6000 - hole)) < 1e-6 and abs(off - 6000) < 1e-6
        and refused)
    # Supprimer la répétition : son étape cachée, au milieu de la chaîne
    # de l'autre corps, part ; la fonction d'après s'y rebranche.
    self.set_active_body(low)
    self.add_rect_sketch(4, 4)
    self.add_pad(3, bodies=[])  # entre dans l'autre corps : sans le fondre
    self.set_active_body(top)
    self.delete_feature(pattern["name"])
    after = _volumes(self)
    report["p83_suppression_au_milieu"] = (
        abs(after[low] - (6000 + 48)) < 1e-6
        and self._doc.getObject(pattern["name"]) is None
        and abs(after[top] - (6000 - hole + 32)) < 1e-6
        and not [o for o in self._doc.Objects
                 if getattr(o, "FreeSolidBodyPatternTool", False)])


def p84_arbre_unique(self, mark, report, etat):
    mark("p84: un seul arbre, une seule barre pour tous les corps")
    from engine import protocol
    self.new_part("Arbre unique")
    self.add_rect_sketch(20, 20)
    self.add_pad(5)
    first = self._require_body().Name
    pad = self._require_body().Tip.Name
    self.add_body()
    second = self._require_body().Name
    state = self.sketch_start()
    self.sketch_add_circle(state["sketch"], 30, 0, 5)
    self.sketch_finish(state["sketch"])
    self.add_pad(10)
    other_pad = self._require_body().Tip.Name
    self.set_active_body(first)
    self.add_rect_sketch(4, 4, face=self._top_face_id())
    self.add_pocket(2)
    pocket = self._require_body().Tip.Name
    # L'arbre du premier corps montre aussi l'histoire du second, à son
    # rang : Extrusion, puis celle du second corps, puis l'enlèvement.
    tree = self.get_tree()
    ranks = {f["name"]: f["order"]
             for f in tree["features"] + tree["other_features"]}
    foreign = {f["name"]: f.get("body") for f in tree["other_features"]}
    report["p84_arbre_unique"] = (
        foreign.get(other_pad) == second
        and ranks[pad] < ranks[other_pad] < ranks[pocket]
        and not protocol.dangling_deps(tree))
    # La barre recule tous les corps : après l'extrusion du premier, le
    # second n'existe pas encore ; un cran plus bas, il revient.
    tree = self.set_tip(pad)
    flags = {f["name"]: f.get("rolled_back")
             for f in tree["features"] + tree["other_features"]}
    born_later = self._doc.getObject(second).Tip is None
    self.set_tip(other_pad)
    volumes = _volumes(self)
    report["p84_barre_commune"] = (
        born_later and flags.get(pocket) and flags.get(other_pad)
        and not flags.get(pad)
        and abs(volumes[first] - 2000) < 1e-6
        and abs(volumes[second] - math.pi * 250) < 1e-6)
    # On réordonne dans un corps, pas d'un corps à l'autre.
    self.tip_to_end()
    try:
        self.reorder_feature(pocket, other_pad)
        crossed = True
    except KernelError:
        crossed = False
    # Sous la barre, tout part — dans chaque corps.
    self.set_tip(pad)
    self.delete_rolled_back()
    report["p84_sous_la_barre"] = (
        not crossed
        and self._doc.getObject(pocket) is None
        and self._doc.getObject(other_pad) is None
        and self._doc.getObject(pad) is not None)
    # Deux contours disjoints extrudés laissent deux solides : deux corps
    # dans le dossier, numérotés ; une extrusion qui les relie n'en
    # laisse qu'un.
    self.new_part("Deux contours")
    state = self.sketch_start(plane="XY")
    self.sketch_add_rectangle(state["sketch"], 0, 0, 10, 10)
    self.sketch_add_rectangle(state["sketch"], 20, 0, 30, 10)
    self.sketch_finish(state["sketch"])
    self.add_pad(5, sketch=state["sketch"])
    body = self._require_body()
    pad = body.Tip
    title = pad.Label
    split = self.get_tree()["bodies"]
    # Chaque solide a sa couleur, son nom, son masquage : ils le suivent
    # quand la cote change et quand un congé change l'ordre des solides.
    right = 0 if body.Shape.Solids[0].CenterOfMass.x > 15 else 1
    self.set_body_color(body.Name, "#cc3333", solid=right)
    self.rename(body.Name, "Bloc", solid=right)
    self.set_hidden([body.Name], True, solid=1 - right)
    shown = self.tessellate()
    pad.Length = 7
    self._recompute()
    top = next(i for i, f in enumerate(body.Shape.Faces)
               if f.CenterOfMass.x > 15 and abs(f.CenterOfMass.z - 7) < 1e-6)
    self.add_fillet(radius=1, face=top)
    rows = {row["label"]: row for row in self.get_tree()["bodies"][0]["solids"]}
    after = self.tessellate()
    report["p84_reglages_par_solide"] = (
        {g.get("color") for g in shown["groups"]} == {"#cc3333"}
        and len(shown["groups"]) == 6
        and set(rows) == {"Bloc", title}
        and rows["Bloc"]["color"] == "#cc3333" and not rows["Bloc"]["hidden"]
        and rows[title]["hidden"] and rows[title]["color"] is None
        and {g.get("color") for g in after["groups"]} == {"#cc3333"})
    # Le congé a pu changer l'ordre des solides : le rang d'à présent.
    east = 0 if body.Shape.Solids[0].CenterOfMass.x > 15 else 1
    self.set_hidden([body.Name], False, solid=1 - east)
    # Chaque face dit son solide : la vue en vise un seul.
    faces = body.Shape.Faces
    both = self.tessellate()["groups"]
    by_face = all(g.get("solid") == (
        east if faces[g["faceId"]].CenterOfMass.x > 15 else 1 - east)
        for g in both)
    state = self.sketch_start(plane="XY")
    self.sketch_add_rectangle(state["sketch"], 5, 0, 25, 3)
    self.sketch_finish(state["sketch"])
    self.add_pad(5, sketch=state["sketch"])
    report["p84_face_solids"] = (
        by_face and {g.get("solid") for g in both} == {0, 1}
        and all("solid" not in g for g in self.tessellate()["groups"]))
    joined = self.get_tree()["bodies"]
    report["p84_solides_du_corps"] = (
        len(split) == 1
        and [row["label"] for row in split[0].get("solids", [])]
        == [title + "[1]", title + "[2]"]
        and len(joined) == 1 and "solids" not in joined[0])


def p85_supprimer_des_corps(self, mark, report, etat):
    mark("p85: supprimer des corps — une fonction d'historique")
    import tempfile
    from engine.kernel import dispatch
    self.new_part("Supprimer des corps")
    state = self.sketch_start(plane="XY")
    self.sketch_add_rectangle(state["sketch"], 0, 0, 10, 10)
    self.sketch_add_rectangle(state["sketch"], 20, 0, 30, 10)
    self.sketch_finish(state["sketch"])
    self.add_pad(5, sketch=state["sketch"])
    first = self._require_body().Name
    pad = self._require_body().Tip.Name
    self.add_body()
    second = self._require_body().Name
    state = self.sketch_start(plane="XY")
    self.sketch_add_circle(state["sketch"], 50, 5, 4)
    self.sketch_finish(state["sketch"])
    self.add_pad(8, sketch=state["sketch"])
    state = self.sketch_start(plane="XZ")
    self.sketch_add_line(state["sketch"], 0, 20, 30, 20)
    self.sketch_finish(state["sketch"])
    surface = self.surface_extrude(10, sketch=state["sketch"])[
        "surfaces"][-1]["name"]
    # Un des deux solides du premier corps : une étape cachée l'ôte de
    # la forme, la cote d'avant passe toujours.
    body = self._doc.getObject(first)
    right = 0 if body.Shape.Solids[0].CenterOfMass.x > 15 else 1
    tree = self.add_remove_bodies([{"name": first, "solid": right}])
    row = next(f for f in tree["features"]
               if f["type_key"] == "remove_bodies")
    self._doc.getObject(pad).Length = 7
    self._recompute()
    report["p85_un_solide"] = (
        len(body.Shape.Solids) == 1 and abs(body.Shape.Volume - 700) < 1e-6
        and body.Shape.Solids[0].CenterOfMass.x < 15
        and row["removes"] == ["Extrusion[{}]".format(right + 1)]
        and row["rolled_back"] is False and not row.get("keep"))
    # Le second corps et la surface : ni dans les dossiers, ni dans la
    # vue, ni actifs ; leur histoire reste.
    tree = self.add_remove_bodies([{"name": second}, {"name": surface}])
    mesh = self.tessellate()
    try:
        self.set_active_body(second)
        refused = False
    except KernelError:
        refused = True
    surfaces = {s["name"]: s for s in tree["surfaces"]}
    report["p85_corps_et_surface"] = (
        [b["name"] for b in tree["bodies"]] == [first]
        and tree["body"] == body.Label and refused
        and surfaces[surface].get("removed") is True
        and not mesh.get("other_bodies") and not mesh.get("surfaces")
        and any(f.get("body") == second for f in tree["other_features"]))
    # La barre au-dessus des deux fonctions : tout revient.
    hosts = [f["name"] for f in tree["features"]
             if f["type_key"] == "remove_bodies"]
    tree = self.set_tip(pad)
    back = (len(body.Shape.Solids) == 2
            and {b["name"] for b in tree["bodies"]} >= {first, second})
    self.tip_to_end()
    # Garder tout ce qui reste, ou tout supprimer : refusés.
    try:
        self.add_remove_bodies([{"name": first}], keep=True)
        nothing = False
    except KernelError:
        nothing = True
    try:
        self.add_remove_bodies([{"name": first}])
        all_gone = False
    except KernelError:
        all_gone = True
    report["p85_barre_et_refus"] = back and nothing and all_gone
    # Supprimer la fonction rend ses corps ; Annuler la remet.
    op = "delete_feature"
    if not dispatch(self, op, {"feature": hosts[1]})["ok"]:
        raise KernelError(op)
    tree = self.get_tree()
    returned = ({b["name"] for b in tree["bodies"]} == {first, second}
                and len(self.tessellate().get("surfaces") or []) == 1)
    self.undo()
    tree = self.get_tree()
    path = os.path.join(tempfile.gettempdir(),
                        "freesolid-selftest-supprimer-corps.FCStd")
    self.save_part(path)
    self.open_part(path)
    reopened = self.get_tree()
    report["p85_supprimer_annuler_rouvrir"] = (
        returned
        and [b["name"] for b in tree["bodies"]] == [first]
        and [b["name"] for b in reopened["bodies"]] == [first]
        and len(self._require_body().Shape.Solids) == 1
        and sum(f["type_key"] == "remove_bodies"
                for f in reopened["features"]) == 2)
    # Garder seulement le premier corps : le second et la surface partent.
    self.new_part("Garder des corps")
    self.add_rect_sketch(10, 10)
    self.add_pad(5)
    kept = self._require_body().Name
    self.add_body()
    state = self.sketch_start(plane="XY")
    self.sketch_add_circle(state["sketch"], 30, 0, 4)
    self.sketch_finish(state["sketch"])
    self.add_pad(5, sketch=state["sketch"])
    tree = self.add_remove_bodies([{"name": kept}], keep=True)
    row = next(f for f in tree["features"]
               if f["type_key"] == "remove_bodies")
    report["p85_garder"] = (
        [b["name"] for b in tree["bodies"]] == [kept] and row["keep"] is True
        and row["kind"] == self._t("Garder des corps"))


def p86_reediter_une_suppression(self, mark, report, etat):
    mark("p86: rééditer une suppression de corps, à son rang")
    import tempfile
    from engine.kernel import dispatch
    self.new_part("Rééditer une suppression")
    state = self.sketch_start(plane="XY")
    for x in (0, 20, 40):
        self.sketch_add_rectangle(state["sketch"], x, 0, x + 10, 10)
    self.sketch_finish(state["sketch"])
    self.add_pad(5, sketch=state["sketch"])
    body = self._require_body()
    first, pad = body.Name, body.Tip.Name
    self.add_body()
    second = self._require_body().Name
    state = self.sketch_start(plane="XY")
    self.sketch_add_circle(state["sketch"], 70, 5, 4)
    self.sketch_finish(state["sketch"])
    self.add_pad(8, sketch=state["sketch"])
    self.set_active_body(first)

    def rank_of(x):
        """Rang, avant la suppression, du solide centré en ``x``."""
        solids = self._doc.getObject(pad).Shape.Solids
        return next(i for i, s in enumerate(solids)
                    if abs(s.CenterOfMass.x - x) < 1)

    def centers():
        solids = self._doc.getObject(first).Shape.Solids  # rouvert : autre objet
        return sorted(round(s.CenterOfMass.x) for s in solids)

    tree = self.add_remove_bodies([{"name": first, "solid": rank_of(25)}])
    host = next(f["name"] for f in tree["features"]
                if f["type_key"] == "remove_bodies")
    # Une extrusion ajoutée ensuite, collée au bloc de gauche.
    state = self.sketch_start(plane="XY")
    self.sketch_add_rectangle(state["sketch"], 0, 10, 10, 20)
    self.sketch_finish(state["sketch"])
    self.add_pad(5, sketch=state["sketch"])
    later = body.Tip.Name
    info = self.remove_bodies_info(host)
    mine = [c for c in info["candidates"] if c["name"] == first]
    report["p86_cases_au_rang"] = (
        len(mine) == 3 and info["keep"] is False
        and [c["checked"] for c in mine] == [
            i == rank_of(25) for i in range(3)]
        and any(c["name"] == second and not c["checked"]
                for c in info["candidates"])
        and centers() == [5, 45])
    # Un autre solide : l'étape cachée change de cible, l'extrusion
    # d'après reste.
    tree = self.edit_remove_bodies(host, [{"name": first,
                                           "solid": rank_of(45)}])
    row = next(f for f in tree["features"] if f["name"] == host)
    report["p86_changer_de_solide"] = (
        centers() == [5, 25] and abs(body.Shape.Volume - 1500) < 1e-6
        and len(self._removal_parts(self._doc.getObject(host))) == 1
        and len(row["removes"]) == 1)
    # Garder seulement le second corps : le premier part en entier, son
    # étape cachée aussi.
    tree = self.edit_remove_bodies(host, [{"name": second}], keep=True)
    obj = self._doc.getObject(host)
    whole = ([b["name"] for b in tree["bodies"]] == [second]
             and not self._removal_parts(obj)
             and obj.Label == self._t("Garder des corps")
             and not any("FreeSolidRemovekeys" in o.PropertiesList
                         for o in self._doc.Objects)
             and self._doc.getObject(later).BaseFeature.Name == pad)
    # Retour à un seul solide, par l'enveloppe annulable : l'étape cachée
    # s'insère entre l'extrusion du début et celle d'après.
    op = "edit_remove_bodies"
    if not dispatch(self, op, {"feature": host, "keep": False,
                               "targets": [{"name": first,
                                            "solid": rank_of(5)}]})["ok"]:
        raise KernelError(op)
    parts = self._removal_parts(obj)
    inserted = (len(parts) == 1 and parts[0].BaseFeature.Name == pad
                and self._doc.getObject(later).BaseFeature is parts[0]
                and body.Tip.Name == later and centers() == [5, 25, 45]
                and abs(body.Shape.Volume - 1500) < 1e-6
                and obj.Label == self._t("Supprimer des corps"))
    report["p86_inserer_au_milieu"] = whole and inserted
    self.undo()
    undone = (not self._removal_parts(obj)
              and [b["name"] for b in self.get_tree()["bodies"]] == [second])
    self.redo()
    redone = len(self._removal_parts(obj)) == 1 and centers() == [5, 25, 45]
    # Un nom choisi ne suit pas le mode.
    self.rename(host, "Mes corps")
    self.edit_remove_bodies(host, [{"name": second}], keep=True)
    self.edit_remove_bodies(host, [{"name": first, "solid": rank_of(5)}])
    named = self._doc.getObject(host).Label == "Mes corps"
    path = os.path.join(tempfile.gettempdir(),
                        "freesolid-selftest-reediter-suppression.FCStd")
    self.save_part(path)
    self.open_part(path)
    info = self.remove_bodies_info(host)
    checked = [c.get("solid") for c in info["candidates"] if c["checked"]]
    report["p86_annuler_nommer_rouvrir"] = (
        undone and redone and named and checked == [rank_of(5)]
        and centers() == [5, 25, 45])


def p87_modifier_suit_le_double_clic(self, mark, report, etat):
    mark("p87: l'arbre dit quelles lignes ont des cotes (« Modifier »)")
    self.new_part("Modifier")
    self.add_rect_sketch(10, 10)
    self.add_pad(5)
    pad = self._require_body().Tip.Name
    self.add_mirror(plane="XZ")
    mirror = self._require_body().Tip.Name
    state = self.sketch_start(plane="XZ")
    self.sketch_add_line(state["sketch"], 0, 20, 30, 20)
    self.sketch_finish(state["sketch"])
    self.surface_extrude(10, sketch=state["sketch"])
    # Plan et axe de référence : leur « Length » est une taille
    # d'affichage, pas une cote.
    self.add_datum_plane(base="XY", offset=5)
    tree = self.add_datum_axis(axis="Z")
    rows = {f["name"]: f for f in tree["features"]}
    surface = tree["surfaces"][-1]
    datums = [f for f in tree["features"]
              if f.get("type_key") in ("datum_plane", "datum_axis")]
    report["p87_cotes_dans_l_arbre"] = (
        rows[pad]["has_params"] is True and rows[mirror]["has_params"] is False
        and surface["has_params"] is True
        and self.get_params(mirror)["params"] == []
        and bool(self.get_params(pad)["params"]))
    try:
        self.set_params(datums[0]["name"], {"Length": 50})
        datum_refused = False
    except KernelError:
        datum_refused = True
    report["p87_reference_sans_cote"] = (
        len(datums) == 2 and datum_refused
        and all(d["has_params"] is False
                and self.get_params(d["name"])["params"] == []
                for d in datums))
    # Corps concernés : la ligne creusée dans l'autre corps rouvre la
    # répétition, et dit si elle a des cotes (une symétrie n'en a pas).
    self.new_part("Modifier — corps concernés")
    self.add_rect_sketch(40, 20)
    self.add_pad(5)
    top = self._require_body().Name
    self.add_body("Dessous")
    low = self._require_body().Name
    self.add_rect_sketch(40, 20)
    self.add_pad(5, reversed=True)
    self.set_active_body(top)
    sketch = self.sketch_start(face=self._top_face_id())["sketch"]
    self.sketch_add_circle(sketch, 10, 0, 2)
    self.sketch_finish(sketch)
    self.add_pocket(through=True)
    self.add_mirror(plane="YZ", scope=[low])
    tree = self.add_linear_pattern(5, 2, axis="Y", scope=[low])
    repeats = {f["name"]: f["has_params"] for f in tree["features"]
               if f.get("type_key") in ("mirror", "linear_pattern")}
    # Les lignes creusées d'un fichier d'avant sont dans l'arbre de
    # l'autre corps (une répétition neuve en fait des étapes cachées).
    for name in repeats:
        repeat = self._doc.getObject(name)
        repeat.removeProperty(self._SCOPE_INSTANCES)
        for step in self._scope_cuts(repeat):
            step.removeProperty(self._THIN_HELPER)
            step.removeProperty("FreeSolidThinOwner")
    self._recompute()
    self.set_active_body(low)
    cuts = [f for f in self.get_tree()["features"]
            if f.get("edits") in repeats]
    report["p87_corps_concernes"] = (
        sorted(repeats.values()) == [False, True]
        and {f["edits"] for f in cuts} == set(repeats)
        and all(f["edits_has_params"] is repeats[f["edits"]]
                and f["suppressible"] is False for f in cuts))


def p88_desactiver_suit_le_moteur(self, mark, report, etat):
    mark("p88: l'arbre dit quelles lignes se désactivent (« Désactiver »)")
    self.new_part("Désactiver")
    self.add_rect_sketch(10, 10)
    self.add_pad(5)
    pad = self._require_body().Tip.Name
    self.add_datum_axis(axis="Z")
    self.add_datum_point(point=[0, 0, 5])
    self.add_datum_cs(point=[0, 0, 5])
    curves = []
    for pts in ([[0, 0, 10], [15, 0, 15], [30, 0, 10]],
                [[30, 0, 10], [32, 15, 14], [30, 30, 10]]):
        curves.append(self.add_curve3d(pts)["surfaces"][-1]["name"])
    tree = self.curve_composite([{"name": c} for c in curves])
    composite = tree["surfaces"][-1]
    datums = [f for f in tree["features"] if f.get("type_key") in (
        "datum_axis", "datum_point", "datum_cs")]
    rows = {f["name"]: f for f in tree["features"]}

    def refused(name):
        try:
            self.set_suppressed([name], True)
        except KernelError:
            return True
        self.set_suppressed([name], False)
        return False

    # Références et courbes se désactivent aussi (drapeau FreeSolid) ; un
    # corps, non.
    body = self._require_body().Name
    report["p88_desactiver_suit_le_moteur"] = (
        rows[pad]["suppressible"] is True
        and len(datums) == 3
        and all(d["suppressible"] is True and not refused(d["name"])
                for d in datums)
        and composite["suppressible"] is True
        and not refused(composite["name"])
        and refused(body)
        and not refused(pad))
    self.set_suppressed([pad], True)
    off = {f["name"]: f for f in self.get_tree()["features"]}
    back = {f["name"]: f for f in self.set_suppressed([pad], False)["features"]}
    report["p88_reactiver"] = (
        off[pad].get("suppressed") is True
        and "suppressed" not in back[pad])


def p89_moities_d_un_solide(self, mark, report, etat):
    mark("p89: régler une moitié d'un solide coupé ne règle pas l'autre")
    self.new_part("Moitiés")
    self.add_rect_sketch(60, 20)
    self.add_pad(5)
    body = self._require_body()
    sketch = self.sketch_start(face=self._top_face_id())["sketch"]
    self.sketch_add_rectangle(sketch, -2, -15, 2, 15)
    self.sketch_finish(sketch)
    self.add_pocket(through=True)
    left = 0 if body.Shape.Solids[0].CenterOfMass.x < 0 else 1
    self.set_body_color(body.Name, "#cc3333", solid=left)
    self.set_hidden([body.Name], True, solid=1 - left)
    rows = self.get_tree()["bodies"][0]["solids"]
    report["p89_moities_d_un_solide"] = (
        len(rows) == 2
        and rows[left]["color"] == "#cc3333" and not rows[left]["hidden"]
        and rows[1 - left]["color"] is None and rows[1 - left]["hidden"])


def p90_copie_repetee(self, mark, report, etat):
    mark("p90: une copie qu'un autre réseau répète ne part pas sans le dire")
    self.new_part("Copie répétée")
    self.add_rect_sketch(10, 10)
    self.add_pad(8)
    source = self._require_body().Name
    self.add_body_pattern("linear", [source], length=20, count=3,
                          axis="X", spacing=True)
    host = self._body_pattern_hosts()[0].Name
    far = max((n for n in _volumes(self) if n != source),
              key=lambda n: _centre_x(self, n)[0])
    self.add_body_pattern("mirror", [far], plane="YZ")
    before = sorted(_volumes(self))
    from engine.kernel import dispatch
    shrunk = dispatch(self, "set_params",
                      {"feature": host, "values": {"count": 2}})
    deleted = dispatch(self, "delete_feature", {"feature": host})
    report["p90_copie_repetee"] = (
        shrunk.get("ok") is False and "est répété par" in shrunk["error"]
        and deleted.get("ok") is False and "est répété par" in deleted["error"]
        and sorted(_volumes(self)) == before
        and not any("Invalid" in (o.State or ())
                    for o in self._doc.Objects))


def p102_corps_vide_ou_cache(self, mark, report, etat):
    mark("p102: corps creusé en entier, corps cachés fondus et creusés")
    from engine.kernel import dispatch

    def call(op, **params):
        return dispatch(self, op, params)

    def rect(x1, y1, x2, y2):
        name = self.sketch_start(plane="XY")["sketch"]
        self.sketch_add_rectangle(name, x1, y1, x2, y2)
        self.sketch_finish(name)
        return name

    def folder():
        return [row["name"] for row in self.get_tree()["bodies"]]

    def shown():
        return {row["name"] for row in self.tessellate().get("other_bodies", [])}

    def clean():
        return not any("Invalid" in (o.State or ()) for o in self._doc.Objects)

    # A (20 de long), B et C (10) en ligne, 20 de large, 10 de haut.
    self.new_part("Corps vide")
    rect(0, 0, 20, 20)
    self.add_pad(10)
    a = self._require_body()
    rect(30, 0, 40, 20)
    self.add_pad(10, merge=False)
    b = self._require_body()
    rect(50, 0, 60, 20)
    self.add_pad(10, merge=False)
    c = self._require_body()
    pad_c = c.Tip.Name
    self.set_active_body(a.Name)

    # Un enlèvement de A qui couvre B tout entier : B n'est plus un corps
    # volumique, comme dans les modeleurs courants — hors du dossier et de
    # la vue, il ne se rend plus actif.
    rect(10, -5, 45, 25)
    call("add_pocket", through=True, reversed=True)
    pocket = a.Tip.Name
    refused = call("set_active_body", body=b.Name)
    titles = {row["name"]: row["label"] for row in self.get_tree()["bodies"]}
    report["p102_corps_vide_quitte_le_dossier"] = (
        clean() and folder() == [a.Name, c.Name]
        # Seul corps restant de l'enlèvement : pas de numéro.
        and titles[a.Name] == self._doc.getObject(pocket).Label
        and shown() == {c.Name}
        and refused.get("ok") is False
        and "creusé en entier" in str(refused.get("error"))
        and round(a.Shape.Volume) == 2000)

    # Il revient quand l'enlèvement cesse d'agir : désactivé, sous la
    # barre, supprimé — et repart avec Ctrl+Z.
    back = []
    call("set_suppressed", features=[pocket], suppressed=True)
    back.append(folder() == [a.Name, b.Name, c.Name])
    call("set_suppressed", features=[pocket], suppressed=False)
    back.append(folder() == [a.Name, c.Name])
    call("set_tip", feature=pad_c)
    back.append(b.Name in folder())
    call("tip_to_end")
    back.append(b.Name not in folder())
    call("delete_feature", feature=pocket)
    back.append(b.Name in folder())
    call("undo")
    back.append(b.Name not in folder() and clean())
    report["p102_corps_vide_revient"] = all(back)

    # Cacher ne change que l'affichage : un corps caché est creusé…
    self.set_active_body(a.Name)
    self.set_hidden([c.Name], True)
    rect(5, 5, 55, 8)
    call("add_pocket", through=True, reversed=True)
    report["p102_cache_creuse"] = (
        clean() and round(c.Shape.Volume) == 1850
        and c.Name in folder())

    # … et fondu par un volume qui le touche.
    rect(45, 0, 50, 20)
    call("add_pad", length=10)
    report["p102_cache_fondu"] = (
        clean() and c.Name in self._absorbed_bodies()
        and folder() == [a.Name])


def p103_fusionner_a_la_reedition(self, mark, report, etat):
    mark("p103: « Fusionner » se change à la réédition")
    from engine.kernel import dispatch

    def call(op, **params):
        return dispatch(self, op, params)

    def rect(x1, y1, x2, y2, plane="XY"):
        name = self.sketch_start(plane=plane)["sketch"]
        self.sketch_add_rectangle(name, x1, y1, x2, y2)
        self.sketch_finish(name)
        return name

    def folder():
        return [row["name"] for row in self.get_tree()["bodies"]]

    def flags():
        tree = self.get_tree()
        return {row["name"]: row["merged"]
                for row in tree["features"] + tree.get("other_features", [])
                if "merged" in row}

    def volume(obj):
        return round(obj.Shape.Volume, 3)

    def added(obj):
        shape = obj.AddSubShape
        box = shape.BoundBox
        return (round(shape.Volume, 3),
                tuple(round(v, 3) for v in (box.XMin, box.YMin, box.ZMin,
                                            box.XMax, box.YMax, box.ZMax)))

    def clean():
        return not any("Invalid" in (o.State or ()) for o in self._doc.Objects)

    def unmerge(feature):
        return call("set_params", feature=feature.Name,
                    values={"merge": False})

    # Une extrusion au milieu de son corps, sur le plan de face : décochée,
    # elle sort dans un corps neuf, dans le même sens ; l'enlèvement
    # d'après reste au corps d'origine. Ctrl+Z la remet, Ctrl+Y la ressort.
    self.new_part("Fusionner rééditer")
    rect(0, 0, 20, 20)
    self.add_pad(10)
    a = self._require_body()
    rect(15, 0, 30, 10, plane="XZ")
    self.add_pad(5)
    pad = a.Tip
    shape = added(pad)
    rect(2, 2, 5, 5)
    call("add_pocket", length=3, reversed=True)
    pocket = a.Tip
    before = (flags(), volume(a))
    answer = unmerge(pad)
    out = pad.getParentGeoFeatureGroup()
    report["p103_sort_de_son_corps"] = (
        before == ({"Pad": False, "Pad001": True}, 4723.0)
        and answer.get("ok") and clean()
        and out is not a and folder() == [a.Name, out.Name]
        and flags() == {"Pad": False, "Pad001": False}
        and added(pad) == shape and volume(out) == 750.0
        and pocket.getParentGeoFeatureGroup() is a and volume(a) == 3973.0
        and pocket.BaseFeature.Name == "Pad")
    call("undo")
    back = pad.getParentGeoFeatureGroup() is a and volume(a) == 4723.0
    call("redo")
    report["p103_ctrl_z_ctrl_y"] = (
        back and pad.getParentGeoFeatureGroup() is out
        and folder() == [a.Name, out.Name] and clean())

    # Cochée : le premier volume d'un corps fond les corps qu'il touche,
    # nés avant lui ; un volume qui ne touche rien est refusé.
    answer = call("set_params", feature=pad.Name, values={"merge": True})
    fused = (answer.get("ok") and clean() and folder() == [out.Name]
             and a.Name in self._absorbed_bodies()
             and flags()["Pad001"] is True)
    rect(40, 0, 50, 10)
    self.add_pad(5, merge=False)
    lone = self._require_body().Tip
    refused = call("set_params", feature=lone.Name, values={"merge": True})
    report["p103_fond_les_corps_touches"] = (
        fused and refused.get("ok") is False
        and "ne touche aucun autre corps" in str(refused.get("error"))
        and not self._is_merged(lone))

    # Une révolution sort de même, pour chaque genre d'axe : même volume,
    # même place.
    same = []
    for axis in ("vertical", "horizontal", "line:1", "X"):
        self.new_part("Révolution rééditée")
        rect(0, 0, 20, 20)
        self.add_pad(10)
        a = self._require_body()
        rect(30, 5, 40, 15, plane="XZ")
        self.add_revolution(90, axis=axis)
        revolution = self._thin_owner(a.Tip)
        shape = added(revolution)
        answer = unmerge(revolution)
        same.append(answer.get("ok") and clean()
                    and revolution.getParentGeoFeatureGroup() is not a
                    and self._revolution_axis_token(revolution) == axis
                    and added(revolution) == shape)
    report["p103_revolution_sort"] = all(same)

    # Paroi mince fermée et contours choisis : ses objets cachés et son
    # profil la suivent.
    self.new_part("Mince rééditée")
    rect(0, 0, 20, 20)
    self.add_pad(10)
    a = self._require_body()
    rect(25, 0, 45, 20)
    self.add_pad(10, thin={"type": "un", "thickness": 2, "caps": 1})
    thin = self._thin_owner(a.Tip)
    total = volume(a)
    thin_ok = unmerge(thin).get("ok") and clean()
    home = thin.getParentGeoFeatureGroup()
    thin_ok = (thin_ok and home is not a
               and abs(volume(a) + volume(home) - total) < 1e-2
               and all(h.getParentGeoFeatureGroup() is home
                       for h in self._thin_helpers(thin)))
    name = self.sketch_start(plane="XY")["sketch"]
    self.sketch_add_rectangle(name, 0, 30, 5, 35)
    self.sketch_add_rectangle(name, 10, 30, 15, 35)
    self.sketch_finish(name)
    self.set_active_body(a.Name)
    self.add_pad(4, sketch=name, contours=[1])
    chosen = a.Tip
    shape = added(chosen)
    used = self._profile_entry(chosen)["used"]
    report["p103_mince_et_contours"] = (
        thin_ok and len(used) == 1 and unmerge(chosen).get("ok") and clean()
        and added(chosen) == shape
        and self._profile_entry(chosen)["used"] == used)

    # Refusé, la pièce comme avant et rien en erreur : « jusqu'au
    # suivant » (rien ne l'arrête dans un corps neuf), sous la barre, un
    # congé sur ses arêtes.
    self.new_part("Fusionner refusé")
    rect(10, 0, 20, 20)
    self.add_pad(10)
    a = self._require_body()
    rect(30, 0, 40, 10)
    self.add_pad(10)
    lone = a.Tip
    rect(5, 2, 10, 5, plane="YZ")
    upto = call("add_pad", length=5, cond="suivant")
    if not upto.get("ok"):
        upto = call("add_pad", length=5, cond="suivant", reversed=True)
    upto_name = a.Tip.Name
    refusals = [upto.get("ok") is True]
    answer = call("set_params", feature=upto_name, values={"merge": False})
    refusals.append("profondeur borgne" in str(answer.get("error")))
    call("set_tip", feature=lone.BaseFeature.Name)
    answer = unmerge(lone)
    refusals.append("sous la barre" in str(answer.get("error")))
    call("tip_to_end")
    edges = [i for i, e in enumerate(a.Shape.Edges)
             if all(v.Point.x >= 30 - 1e-6 for v in e.Vertexes)]
    call("add_fillet", radius=1, edges=edges[:1])
    kept = volume(a)
    answer = unmerge(lone)
    refusals.append(answer.get("ok") is False)
    report["p103_refus"] = (
        all(refusals) and clean() and volume(a) == kept
        and lone.getParentGeoFeatureGroup() is a
        and not any(row.get("error") for row in self.get_tree()["features"]))


def p104_corps_de_la_fonction(self, mark, report, etat):
    mark("p104: le corps de la fonction se change à la réédition")
    from engine.kernel import dispatch

    def call(op, **params):
        return dispatch(self, op, params)

    def rect(x1, y1, x2, y2):
        name = self.sketch_start(plane="XY")["sketch"]
        self.sketch_add_rectangle(name, x1, y1, x2, y2)
        self.sketch_finish(name)

    def folder():
        return [row["name"] for row in self.get_tree()["bodies"]]

    def volume(obj):
        return round(obj.Shape.Volume, 3)

    def clean():
        return not any("Invalid" in (o.State or ()) for o in self._doc.Objects)

    def row(feature):
        tree = self.get_tree()
        return next(r for r in tree["features"] + tree.get("other_features", [])
                    if r["name"] == feature.Name)

    # A et C, puis une extrusion de A qui touche les deux : elle fond C.
    self.new_part("Corps de la fonction")
    rect(0, 0, 20, 20)
    self.add_pad(10)
    a = self._require_body()
    rect(30, 0, 40, 20)
    self.add_pad(10, merge=False)
    c = self._require_body()
    self.set_active_body(a.Name)
    rect(15, 5, 35, 10)
    call("add_pad", length=5)
    pad = self._thin_owner(a.Tip)
    start = (folder() == [a.Name] and volume(a) == 6250.0
             and [b.Name for b in self._fused_bodies_of(pad)] == [c.Name]
             and row(pad)["alone"] is False)

    # Comme la zone d'action des modeleurs courants : le corps de A ôté de
    # la liste, la fonction sort de A pour un corps neuf qui fond C.
    same = call("set_params", feature=pad.Name,
                values={"merge": True, "bodies": [a.Name, c.Name]})
    unchanged = same.get("ok") and pad.getParentGeoFeatureGroup() is a
    answer = call("set_params", feature=pad.Name,
                  values={"merge": True, "bodies": [c.Name]})
    home = pad.getParentGeoFeatureGroup()
    report["p104_sort_vers_les_corps_choisis"] = (
        start and unchanged and answer.get("ok") and clean()
        and home is not a and folder() == [a.Name, home.Name]
        and volume(a) == 4000.0 and volume(home) == 2375.0
        and c.Name in self._absorbed_bodies()
        and row(pad)["alone"] is True and row(pad)["merged"] is True)
    call("undo")
    back = (pad.getParentGeoFeatureGroup() is a and volume(a) == 6250.0
            and folder() == [a.Name] and clean())

    # Liste vide : elle sort de A et ne fond plus rien.
    answer = call("set_params", feature=pad.Name,
                  values={"merge": True, "bodies": []})
    home = pad.getParentGeoFeatureGroup()
    report["p104_liste_vide_et_ctrl_z"] = (
        back and answer.get("ok") and clean()
        and folder() == [a.Name, c.Name, home.Name]
        and volume(home) == 500.0 and row(pad)["merged"] is False)


def p105_corps_du_lissage_et_du_balayage(self, mark, report, etat):
    mark("p105: corps fondus et creusés d'un lissage, d'un balayage, "
         "à la réédition")
    from engine.kernel import dispatch

    def call(op, **params):
        return dispatch(self, op, params)

    def rect(x1, y1, x2, y2, datum=None):
        name = (self.sketch_start(datum=datum) if datum
                else self.sketch_start(plane="XY"))["sketch"]
        self.sketch_add_rectangle(name, x1, y1, x2, y2)
        self.sketch_finish(name)
        return name

    def folder():
        return [row["name"] for row in self.get_tree()["bodies"]]

    def volume(obj):
        return round(obj.Shape.Volume, 3)

    def clean():
        return not any("Invalid" in (o.State or ()) for o in self._doc.Objects)

    def row(feature):
        tree = self.get_tree()
        return next(r for r in tree["features"] + tree.get("other_features", [])
                    if r["name"] == feature.Name)

    def datum(offset):
        self.add_datum_plane(base="XY", offset=offset)
        return [o.Name for o in self._doc.Objects
                if o.TypeId == "PartDesign::Plane"][-1]

    def two_bodies(title):
        self.new_part(title)
        rect(0, 0, 20, 20)
        self.add_pad(10)
        a = self._require_body()
        rect(30, 0, 40, 20)
        self.add_pad(10, merge=False)
        c = self._require_body()
        self.set_active_body(a.Name)
        return a, c

    # Un lissage de A qui touche C, créé sans le fondre : sans cote, il se
    # rouvre sur sa zone « Corps concernés », vide. C choisi, il le fond ;
    # la zone vidée, il le rend.
    a, c = two_bodies("Lissage")
    top = datum(20)
    low, high = rect(15, 5, 35, 10), rect(15, 5, 35, 10, datum=top)
    call("add_loft", sketches=[low, high], bodies=[])
    loft = self._thin_owner(a.Tip)
    offered = (row(loft).get("fused") == [] and folder() == [a.Name, c.Name]
               and volume(a) == 5750.0)
    fused = call("set_params", feature=loft.Name,
                 values={"bodies": [c.Name]})
    fused_ok = (fused.get("ok") and folder() == [a.Name]
                and volume(a) == 7500.0
                and [b["name"] for b in row(loft)["fused"]] == [c.Name]
                and clean())
    freed = call("set_params", feature=loft.Name, values={"bodies": []})
    freed_ok = (freed.get("ok") and folder() == [a.Name, c.Name]
                and volume(a) == 5750.0 and volume(c) == 2000.0
                and row(loft)["fused"] == [] and clean())
    call("undo")
    # Seul corps de la pièce : rien à choisir, pas de zone.
    self.new_part("Lissage seul")
    rect(0, 0, 20, 20)
    self.add_pad(10)
    top = datum(20)
    self.add_loft([rect(5, 5, 15, 15), rect(5, 5, 15, 15, datum=top)])
    alone = "fused" not in row(self._thin_owner(self._require_body().Tip))
    report["p105_lissage_fond_les_corps_choisis"] = (
        offered and fused_ok and freed_ok and alone and clean())

    # Un enlèvement balayé de A qui traverse C, créé sans le creuser : sa
    # zone « Corps creusés » se rouvre vide ; C choisi, il est creusé.
    a, c = two_bodies("Balayage")
    ring = self.sketch_start(plane="YZ")["sketch"]
    self.sketch_add_circle(ring, 10, 5, 2)
    self.sketch_finish(ring)
    path = self.sketch_start(datum=datum(5))["sketch"]
    self.sketch_add_line(path, 0, 10, 40, 10)
    self.sketch_finish(path)
    call("add_sweep", profile=ring, spine=path, subtractive=True, bodies=[])
    sweep = self._thin_owner(a.Tip)
    hole = round(math.pi * 4, 3)
    offered = (row(sweep).get("cut") == [] and volume(c) == 2000.0
               and abs(volume(a) - (4000.0 - hole * 20)) < 1e-2)
    cut = call("set_params", feature=sweep.Name, values={"bodies": [c.Name]})
    cut_ok = (cut.get("ok") and folder() == [a.Name, c.Name]
              and abs(volume(c) - (2000.0 - hole * 10)) < 1e-2
              and [b["name"] for b in row(sweep)["cut"]] == [c.Name]
              and clean())
    call("undo")
    undone = volume(c) == 2000.0 and row(sweep)["cut"] == [] and clean()
    call("redo")
    report["p105_balayage_creuse_les_corps_choisis"] = (
        offered and cut_ok and undone
        and abs(volume(c) - (2000.0 - hole * 10)) < 1e-2 and clean())


def p106_fusionner_lissage_et_balayage(self, mark, report, etat):
    mark("p106: « Fusionner » d'un lissage, d'un balayage, à la réédition")
    from engine.kernel import dispatch

    def call(op, **params):
        return dispatch(self, op, params)

    def rect(x1, y1, x2, y2, datum=None):
        name = (self.sketch_start(datum=datum) if datum
                else self.sketch_start(plane="XY"))["sketch"]
        self.sketch_add_rectangle(name, x1, y1, x2, y2)
        self.sketch_finish(name)
        return name

    def datum(offset):
        self.add_datum_plane(base="XY", offset=offset)
        return [o.Name for o in self._doc.Objects
                if o.TypeId == "PartDesign::Plane"][-1]

    def folder():
        return [row["name"] for row in self.get_tree()["bodies"]]

    def volume(obj):
        return round(obj.Shape.Volume, 3)

    def clean():
        return not any("Invalid" in (o.State or ()) for o in self._doc.Objects)

    def row(feature):
        tree = self.get_tree()
        return next(r for r in tree["features"] + tree.get("other_features", [])
                    if r["name"] == feature.Name)

    def box(shape):
        b = shape.BoundBox
        return tuple(round(v, 3) for v in (b.XMin, b.YMin, b.ZMin,
                                           b.XMax, b.YMax, b.ZMax))

    def home(feature):
        return feature.getParentGeoFeatureGroup()

    def inside(feature):
        """Profils et trajectoire dans le corps de la fonction : des liants
        cachés, comme à la création dans un autre corps (FreeCAD calcule
        aussi un lien qui en sort, avec un simple avertissement)."""
        links = [getattr(feature, "Profile", None),
                 getattr(feature, "Spine", None)]
        links += list(getattr(feature, "Sections", None) or [])
        objects = [self._as_object(link) for link in links if link]
        return bool(objects) and all(
            obj.getParentGeoFeatureGroup() is home(feature)
            and self._thin_owner(obj) is feature for obj in objects)

    def sweep_on_block(circles):
        """Un bloc A, et un balayage le long de son dessus."""
        self.new_part("Balayage")
        rect(0, 0, 40, 20)
        self.add_pad(10)
        a = self._require_body()
        ring = self.sketch_start(plane="YZ")["sketch"]
        for y in circles:
            self.sketch_add_circle(ring, y, 10, 2)
        self.sketch_finish(ring)
        path = self.sketch_start(datum=datum(10))["sketch"]
        self.sketch_add_line(path, 0, 10, 40, 10)
        self.sketch_finish(path)
        self.add_sweep(ring, path)
        return a, self._thin_owner(a.Tip)

    # Un lissage posé sur A : décoché, il sort pour un corps neuf, même
    # volume, même place ; ses esquisses restent dans A. Ctrl+Z le remet,
    # Ctrl+Y le ressort ; recoché, il refond A, qu'il touche.
    self.new_part("Lissage")
    rect(0, 0, 20, 20)
    self.add_pad(10)
    a = self._require_body()
    low = rect(5, 5, 15, 15, datum=datum(10))
    high = rect(7, 7, 13, 13, datum=datum(20))
    self.add_loft([low, high])
    loft = self._thin_owner(a.Tip)
    added, where = round(loft.AddSubShape.Volume, 3), box(loft.AddSubShape)
    flags = (row(loft).get("merged") is True and row(loft)["alone"] is False
             and volume(a) == round(4000.0 + added, 3))
    out = call("set_params", feature=loft.Name, values={"merge": False})
    made = home(loft)
    out_ok = (out.get("ok") and made is not a and folder() == [a.Name, made.Name]
              and volume(a) == 4000.0 and volume(made) == added
              and box(loft.Shape) == where and inside(loft)
              and all(self._doc.getObject(s).getParentGeoFeatureGroup() is a
                      for s in (low, high))
              and row(loft)["merged"] is False and clean())
    call("undo")
    undone = home(loft) is a and folder() == [a.Name] and clean()
    call("redo")
    redone = home(loft) is made and volume(a) == 4000.0 and clean()
    back = call("set_params", feature=loft.Name, values={"merge": True})
    report["p106_lissage_sort_de_son_corps"] = (
        flags and out_ok and undone and redone and back.get("ok")
        and folder() == [made.Name]
        and volume(made) == round(4000.0 + added, 3)
        and a.Name in self._absorbed_bodies() and clean())

    # Un balayage, le long d'une esquisse puis d'une courbe 3D : il sort de
    # même ; le liant de la courbe part avec lui.
    a, pipe = sweep_on_block([10])
    tube = round(pipe.AddSubShape.Volume, 3)
    out = call("set_params", feature=pipe.Name, values={"merge": False})
    on_sketch = (out.get("ok") and home(pipe) is not a
                 and volume(a) == 8000.0 and volume(home(pipe)) == tube
                 and abs(tube - math.pi * 4 * 40) < 1e-2 and inside(pipe)
                 and clean())
    self.new_part("Courbe")
    rect(-70, -10, -50, 10)
    self.add_pad(10)
    a = self._require_body()
    curve = self.add_curve3d([[-60, 0, 10], [-60, 0, 30], [-40, 0, 50]],
                             spline=True)["surfaces"][-1]["name"]
    ring = self.sketch_start(datum=datum(10))["sketch"]
    self.sketch_add_circle(ring, -60, 0, 3)
    self.sketch_finish(ring)
    self.add_sweep(ring, curve)
    pipe = self._thin_owner(a.Tip)
    tube = round(pipe.AddSubShape.Volume, 3)
    out = call("set_params", feature=pipe.Name, values={"merge": False})
    group = home(pipe).Group
    report["p106_balayage_sort_de_son_corps"] = (
        on_sketch and out.get("ok") and home(pipe) is not a
        and volume(a) == 4000.0 and volume(home(pipe)) == tube
        and inside(pipe)
        and any(o.Name.startswith("SpineBinder") for o in group)
        and not any(o.Name.startswith("SpineBinder") for o in a.Group)
        and clean())

    # Zone d'action : un lissage de A qui fond C ; A retiré de la zone, il
    # sort pour un corps neuf qui fond C.
    self.new_part("Zone")
    rect(0, 0, 20, 20)
    self.add_pad(10)
    a = self._require_body()
    rect(30, 0, 40, 20)
    self.add_pad(10, merge=False)
    c = self._require_body()
    self.set_active_body(a.Name)
    self.add_loft([rect(15, 5, 35, 15, datum=datum(10)),
                   rect(15, 5, 35, 15, datum=datum(20))])
    loft = self._thin_owner(a.Tip)
    fused = [b.Name for b in self._fused_bodies_of(loft)] == [c.Name]
    out = call("set_params", feature=loft.Name,
               values={"merge": True, "bodies": [c.Name]})
    made = home(loft)
    report["p106_zone_d_action"] = (
        fused and out.get("ok") and made is not a
        and folder() == [a.Name, made.Name] and volume(a) == 4000.0
        and volume(made) == 4000.0 and c.Name in self._absorbed_bodies()
        and inside(loft) and clean())

    # Refusé, la pièce comme avant : un profil en deux morceaux (d'un
    # liant, FreeCAD ne balaie qu'une face), un lissage sous la barre.
    a, pipe = sweep_on_block([5, 15])
    before, count = volume(a), len(self._doc.Objects)
    two = call("set_params", feature=pipe.Name, values={"merge": False})
    refused = (two.get("ok") is False and "seul tenant" in str(two.get("error"))
               and volume(a) == before and len(self._doc.Objects) == count
               and home(pipe) is a and clean())
    self.new_part("Barre")
    rect(0, 0, 20, 20)
    self.add_pad(10)
    a = self._require_body()
    self.add_loft([rect(5, 5, 15, 15, datum=datum(10)),
                   rect(7, 7, 13, 13, datum=datum(20))])
    loft = self._thin_owner(a.Tip)
    call("set_tip", feature=loft.BaseFeature.Name)
    barred = call("set_params", feature=loft.Name, values={"merge": False})
    call("tip_to_end")
    report["p106_refus"] = (
        refused and barred.get("ok") is False
        and "sous la barre" in str(barred.get("error")) and home(loft) is a
        and folder() == [a.Name] and clean())


def p107_enlevement_remonte(self, mark, report, etat):
    mark("p107: un enlèvement réordonné creuse les autres corps à son rang")
    from engine.kernel import dispatch

    def call(op, **params):
        return dispatch(self, op, params)

    def rect(x1, y1, x2, y2):
        name = self.sketch_start(plane="XY")["sketch"]
        self.sketch_add_rectangle(name, x1, y1, x2, y2)
        self.sketch_finish(name)
        return name

    def clean():
        return not any("Invalid" in (o.State or ()) for o in self._doc.Objects)

    def volume(body):
        return round(body.Shape.Volume)

    def step_after(body):
        """La fonction de ``body`` juste avant l'étape cachée."""
        group = [o for o in body.Group if o.isDerivedFrom("PartDesign::Feature")]
        step = next(o for o in group if self._hidden_cut_source(o))
        return group[group.index(step) - 1]

    # A1, B1, A2, B2, puis un enlèvement de A à travers tout, qui creuse
    # une rainure dans B (B1 : 10 × 10 × 10 ; B2 le rehausse sur la moitié).
    self.new_part("Enlèvement remonté")
    rect(0, 0, 10, 10)
    self.add_pad(10)
    a = self._require_body()
    rect(30, 0, 40, 10)
    self.add_pad(10, merge=False)
    b = self._require_body()
    b1 = b.Tip
    self.set_active_body(a.Name)
    rect(0, 0, 5, 5)
    self.add_pad(20)
    a2 = a.Tip
    self.set_active_body(b.Name)
    rect(30, 0, 35, 10)
    self.add_pad(20)
    b2 = b.Tip
    self.set_active_body(a.Name)
    rect(-5, 4, 45, 6)
    call("add_pocket", through=True, reversed=True)
    cut = a.Tip
    start = volume(b) == 1200 and step_after(b) is b2

    # Remonté au-dessus de B2 : il creuse B avant B2, qui rebouche sa part
    # de la rainure. La barre posée juste sous lui montre B creusé, sans B2.
    up = call("reorder_feature", feature=cut.Name, target=a2.Name)
    raised = (up.get("ok") and volume(b) == 1400 and step_after(b) is b1
              and clean())
    call("set_tip", feature=cut.Name)
    barred = volume(b) == 800 and b2.Name in self._features_after_tips()
    call("tip_to_end")
    report["p107_remonte_creuse_avant"] = (
        start and raised and barred and volume(b) == 1400)

    # Redescendu sous B2, il le creuse de nouveau ; Ctrl+Z le remonte.
    down = call("reorder_feature", feature=cut.Name, target=a2.Name,
                after=True)
    lowered = down.get("ok") and volume(b) == 1200 and step_after(b) is b2
    call("undo")
    report["p107_redescendu"] = (
        lowered and volume(b) == 1400 and step_after(b) is b1 and clean())

    # La barre au milieu reste sous la même ligne : posée sous B2,
    # l'enlèvement qu'on remonte passe au-dessus d'elle, A2 dessous.
    call("reorder_feature", feature=cut.Name, target=a2.Name, after=True)
    call("set_tip", feature=b2.Name)
    mid = call("reorder_feature", feature=cut.Name, target=a2.Name)
    rolled = self._features_after_tips()
    report["p107_barre_au_milieu"] = (
        mid.get("ok") and volume(b) == 1400 and cut.Name not in rolled
        and a2.Name in rolled and b2.Name not in rolled and clean())
    call("tip_to_end")

    # Refusé au-dessus de la naissance de B : rien à creuser à ce rang.
    self.new_part("Avant le corps")
    rect(0, 0, 10, 10)
    self.add_pad(10)
    a = self._require_body()
    rect(0, 0, 5, 5)
    self.add_pad(20)
    a1b = a.Tip
    rect(30, 0, 40, 10)
    self.add_pad(10, merge=False)
    b = self._require_body()
    self.set_active_body(a.Name)
    rect(-5, 4, 45, 6)
    call("add_pocket", through=True, reversed=True)
    cut = a.Tip
    before = volume(b)
    early = call("reorder_feature", feature=cut.Name, target=a1b.Name)
    report["p107_refus_avant_le_corps"] = (
        before == 800 and early.get("ok") is False
        and "n'existe pas encore" in str(early.get("error"))
        and volume(b) == 800 and a.Tip is cut and clean())


def p108_ajout_barre_au_milieu(self, mark, report, etat):
    mark("p108: une fonction ajoutée la barre au milieu y reste")
    import os
    import tempfile
    from engine.kernel import dispatch

    def call(op, **params):
        return dispatch(self, op, params)

    def rect(x1, y1, x2, y2):
        name = self.sketch_start(plane="XY")["sketch"]
        self.sketch_add_rectangle(name, x1, y1, x2, y2)
        self.sketch_finish(name)
        return name

    def clean():
        return not any("Invalid" in (o.State or ()) for o in self._doc.Objects)

    def order():
        """Les fonctions de l'arbre, de haut en bas (sans étapes cachées)."""
        return [row["name"] for row in self._history_rows()
                if row["role"] == "feature"
                and not self._hidden_cut_source(
                    self._doc.getObject(row["name"]))]

    def under_bar(name):
        return name in self._features_after_tips()

    def part():
        """A1, B1, A2, B2 : deux corps qui s'entrelacent ; B1 10 × 10 × 10
        et B2 qui le rehausse sur la moitié."""
        rect(0, 0, 10, 10)
        self.add_pad(10)
        a = self._require_body()
        rect(30, 0, 40, 10)
        self.add_pad(10, merge=False)
        b = self._require_body()
        b1 = b.Tip
        self.set_active_body(a.Name)
        rect(0, 0, 5, 5)
        self.add_pad(20)
        a2 = a.Tip
        self.set_active_body(b.Name)
        rect(30, 0, 35, 10)
        self.add_pad(20)
        b2 = b.Tip
        return a, b, b1, a2, b2

    # La barre sous B1 : X, ajouté dans A, vient à la barre et y reste
    # quand elle redescend, puis remonte. A2 garde son rang avant B2.
    self.new_part("Barre au milieu")
    a, b, b1, a2, b2 = part()
    a1 = a2.BaseFeature
    call("set_tip", feature=b1.Name)
    self.set_active_body(a.Name)
    rect(5, 5, 10, 10)
    call("add_pad", length=15)
    x = a.Tip
    wanted = [a1.Name, b1.Name, x.Name, a2.Name, b2.Name]
    born = (order() == wanted and not under_bar(x.Name)
            and under_bar(a2.Name) and under_bar(b2.Name))
    call("tip_to_end")
    ended = order() == wanted
    call("set_tip", feature=b1.Name)
    raised = order() == wanted and under_bar(x.Name)
    call("tip_to_end")
    report["p108_fonction_reste_a_la_barre"] = (
        born and ended and raised and order() == wanted and clean())

    # Ctrl+Z sur les trois pas de barre : X redevient la fonction neuve
    # sous laquelle passe la barre, au même rang ; encore Ctrl+Z, il part.
    for _ in range(3):
        call("undo")
    back = order() == wanted and not under_bar(x.Name) and under_bar(a2.Name)
    name = x.Name
    call("undo")
    report["p108_annuler"] = (
        back and self._doc.getObject(name) is None
        and order() == [a1.Name, b1.Name, a2.Name, b2.Name] and clean())

    # Un enlèvement ajouté à la barre creuse B à ce rang : avant B2, qui
    # rebouche sa part de la rainure.
    self.set_active_body(a.Name)
    rect(-5, 4, 45, 6)
    call("add_pocket", through=True, reversed=True)
    cut = a.Tip
    call("tip_to_end")
    report["p108_enlevement_a_la_barre"] = (
        order() == [a1.Name, b1.Name, cut.Name, a2.Name, b2.Name]
        and round(b.Shape.Volume) == 1400 and clean())

    # Une fonction collée la barre au milieu y vient aussi, pas au rang de
    # sa source.
    call("set_tip", feature=cut.Name)
    self.set_active_body(a.Name)
    pasted = call("paste_feature", feature=a1.Name, plane="XY")
    twin = a.Tip
    report["p108_collage_a_la_barre"] = (
        pasted.get("ok") and twin is not a1
        # copyObject recopie le rang de la source : la copie le perd.
        and "FreeSolidRank" not in twin.PropertiesList
        and order() == [a1.Name, b1.Name, cut.Name, twin.Name, a2.Name,
                        b2.Name]
        and not under_bar(twin.Name) and under_bar(a2.Name) and clean())
    call("tip_to_end")

    # Un fichier d'avant les rangs enregistrés, la barre au milieu : à la
    # réouverture, ce qu'on ajoute vient à la barre.
    self.new_part("Fichier d'avant")
    a, b, b1, a2, b2 = part()
    names = [a2.BaseFeature.Name, b1.Name, a2.Name, b2.Name]
    body = a.Name
    call("set_tip", feature=b1.Name)
    for obj in self._doc.Objects:
        if "FreeSolidRank" in obj.PropertiesList:
            obj.removeProperty("FreeSolidRank")
    path = os.path.join(tempfile.gettempdir(), "freesolid-barre.FCStd")
    self.save_part(path)
    self.open_part(path)
    self.set_active_body(body)
    rect(5, 5, 10, 10)
    call("add_pad", length=15)
    x = self._doc.getObject(body).Tip.Name
    call("tip_to_end")
    report["p108_fichier_d_avant"] = (
        order() == names[:2] + [x] + names[2:] and clean())


def p109_reedition_au_rang(self, mark, report, etat):
    mark("p109: rééditer une suppression de corps sur la pièce à son rang")
    import os
    import tempfile
    from engine.kernel import dispatch

    def call(op, **params):
        return dispatch(self, op, params)

    def rect(x1, y1, x2, y2):
        name = self.sketch_start(plane="XY")["sketch"]
        self.sketch_add_rectangle(name, x1, y1, x2, y2)
        self.sketch_finish(name)
        return name

    def clean():
        return not any("Invalid" in (o.State or ()) for o in self._doc.Objects)

    def solids(body):
        """Le milieu en x de chaque solide du corps, en mm (arrondi bas)."""
        return sorted(int(s.CenterOfMass.x) for s in body.Shape.Solids)

    def steps():
        return len(self._doc.UndoNames)

    # Un bloc coupé en deux par un enlèvement (moitiés centrées en 4,5 et
    # 15,5) ; la suppression ôte celle de droite, une extrusion vient
    # ensuite à part (centrée en 2,5).
    self.new_part("Réédition au rang")
    rect(0, 0, 20, 10)
    self.add_pad(10)
    a = self._require_body()
    rect(9, -5, 11, 15)
    call("add_pocket", through=True, reversed=True)
    cut = a.Tip
    right = next(i for i, s in enumerate(cut.Shape.Solids)
                 if s.CenterOfMass.x > 10)
    host = call("add_remove_bodies",
                targets=[{"name": a.Name, "solid": right}])["result"]
    host = next(f["name"] for f in host["features"]
                if f["type_key"] == "remove_bodies")
    rect(0, 20, 5, 25)
    call("add_pad", length=5)
    later = a.Tip
    today = solids(a)

    # La vue au rang : la barre juste au-dessus de la suppression, les deux
    # moitiés revenues, dans le corps comme dans le dossier. Pas de pas
    # d'annulation, la pièce n'est pas modifiée.
    count, modified = steps(), self._modified
    tree = call("rank_view", feature=host)["result"]
    rolled = self._rolled_back_objects()
    folder = next(b for b in tree["bodies"] if b["name"] == a.Name)
    report["p109_vue_au_rang"] = (
        today == [2, 4] and solids(a) == [4, 15]
        and len(folder.get("solids") or []) == 2
        and host in {o.Name for o in rolled}
        and later.Name in {o.Name for o in rolled}
        and cut.Name not in {o.Name for o in rolled}
        and steps() == count and self._modified == modified and clean())

    # Fermée sans réédition : la pièce d'aujourd'hui revient.
    call("rank_view_end")
    report["p109_fin_de_la_vue"] = (
        solids(a) == today and not self._rolled_back_objects()
        and steps() == count and clean())

    # Rééditée depuis la vue : le moteur rend d'abord la barre, la
    # réédition s'applique à la pièce d'aujourd'hui et Ctrl+Z ne défait
    # qu'elle.
    call("rank_view", feature=host)
    left = 1 - right
    edited = call("edit_remove_bodies", feature=host,
                  targets=[{"name": a.Name, "solid": left}])
    after = solids(a)
    call("undo")
    report["p109_reedition_depuis_la_vue"] = (
        edited.get("ok") and after == [2, 15]
        and solids(a) == today and not self._rolled_back_objects()
        and self._rank_view is None and clean())

    # La barre au milieu revient où elle était ; enregistrer depuis la vue
    # enregistre la pièce d'aujourd'hui.
    call("set_tip", feature=host)
    call("rank_view", feature=host)
    call("rank_view_end")
    mid = (later.Name in self._features_after_tips()
           and host not in self._features_after_tips())
    call("tip_to_end")
    call("rank_view", feature=host)
    path = os.path.join(tempfile.gettempdir(), "freesolid-au-rang.FCStd")
    call("save_part", path=path)
    saved = solids(a) == today and not self._rolled_back_objects()
    name = a.Name
    call("open_part", path=path)
    a = self._doc.getObject(name)
    report["p109_barre_et_enregistrement"] = (
        mid and saved and solids(a) == today
        and not self._rolled_back_objects() and clean())


def p110_face_du_corps_fondu(self, mark, report, etat):
    mark("p110: une face venue d'un corps fondu désigne la fonction de ce corps")
    from engine.kernel import dispatch

    def call(op, **params):
        return dispatch(self, op, params)

    def rect(x1, y1, x2, y2):
        name = self.sketch_start(plane="XY")["sketch"]
        self.sketch_add_rectangle(name, x1, y1, x2, y2)
        self.sketch_finish(name)
        return name

    def designated():
        """Centre de chaque face du corps actif (mm, arrondi à 0,1) → la
        fonction qu'elle désigne au survol."""
        faces = self._require_body().Shape.Faces
        found = {}
        for group in self.tessellate()["groups"]:
            centre = faces[group["faceId"]].CenterOfMass
            key = tuple(round(v, 1) for v in (centre.x, centre.y, centre.z))
            found[key] = group.get("feature")
        return found

    # Une barre en A fond B et C : les faces de B et de C, même rognées
    # par la barre, désignent leur propre extrusion ; celles de la barre,
    # la barre.
    self.new_part("Face du corps fondu")
    rect(0, 0, 20, 20)
    a_pad = self.add_pad(10)["features"][0]["name"]
    a = self._require_body()
    self.add_body()
    rect(30, 0, 50, 20)
    self.add_pad(10)
    b = self._require_body()
    self.add_body()
    rect(60, 0, 80, 20)
    self.add_pad(10)
    c = self._require_body()
    self.set_active_body(a.Name)
    rect(10, 5, 70, 15)
    call("add_pad", length=5, bodies=[b.Name, c.Name])
    bar = self._thin_owner(a.Tip).Name
    seen = designated()
    match = self._face_match
    report["p110_extrusion_qui_fond"] = (
        seen.get((40.0, 10.0, 10.0)) == b.Tip.Name      # dessus de B
        and seen.get((30.0, 10.0, 5.8)) == b.Tip.Name   # flanc rogné
        and seen.get((70.0, 10.0, 10.0)) == c.Tip.Name  # dessus de C
        and seen.get((25.0, 10.0, 5.0)) == bar          # dessus de la barre
        and seen.get((10.0, 10.0, 10.0)) == a_pad       # dessus de A
        and match.get("matched") == match.get("faces") == len(seen))

    # Tirer le dessus de B change l'extrusion de B.
    top = next(i for i, face in enumerate(a.Shape.Faces)
               if abs(face.CenterOfMass.z - 10) < 1e-6
               and abs(face.CenterOfMass.x - 40) < 1e-6)
    drag = self.face_drag_info(top)["drag"] or {}
    report["p110_tirer_la_face"] = (
        drag.get("feature") == b.Tip.Name and drag.get("value") == 10.0)

    # « Combiner » : la face de B restée entière et celle qu'il rogne.
    self.new_part("Face combinée")
    rect(0, 0, 20, 20)
    a_pad = self.add_pad(10)["features"][0]["name"]
    a = self._require_body()
    self.add_body()
    rect(10, 0, 40, 20)
    self.add_pad(5)
    b = self._require_body()
    self.set_active_body(a.Name)
    call("add_boolean", tool=b.Name, type="fuse")
    seen = designated()
    report["p110_combiner"] = (
        seen.get((40.0, 10.0, 2.5)) == b.Tip.Name
        and seen.get((30.0, 10.0, 5.0)) == b.Tip.Name
        and seen.get((10.0, 10.0, 10.0)) == a_pad)

    # Une copie de réseau de corps : ses faces désignent le réseau, seule
    # ou combinée avec sa source.
    self.new_part("Face d'une copie")
    rect(0, 0, 10, 10)
    self.add_pad(8)
    source = self._require_body()
    self.add_body_pattern("linear", [source.Name], length=8, count=2,
                          axis="X", spacing=True)
    host = self._body_pattern_hosts()[0].Name
    copy = next(bd for bd in self._history_bodies() if bd is not source)
    self.set_active_body(copy.Name)
    alone = set(designated().values())
    self.set_active_body(source.Name)
    call("add_boolean", tool=copy.Name, type="fuse")
    report["p110_copie_de_reseau"] = (
        alone == {host} and designated().get((18.0, 5.0, 4.0)) == host)


def p111_coller_lissage_et_balayage(self, mark, report, etat):
    mark("p111: un lissage ou un balayage collé emporte ses autres esquisses")
    from engine.kernel import dispatch

    def call(op, **params):
        return dispatch(self, op, params)

    def clean():
        return not any("Invalid" in (o.State or ()) for o in self._doc.Objects)

    def square(sketch, x1, y1, x2, y2):
        for line in ((x1, y1, x2, y1), (x2, y1, x2, y2),
                     (x2, y2, x1, y2), (x1, y2, x1, y1)):
            self.sketch_add_line(sketch, *line)
        self.sketch_finish(sketch)

    def top_of(body, x):
        """La face du dessus du bloc dont le milieu est en ``x``."""
        faces = body.Shape.Faces
        best = max((f.CenterOfMass.z, i) for i, f in enumerate(faces)
                   if abs(f.CenterOfMass.x - x) < 1e-6
                   and abs(f.normalAt(0, 0).z - 1) < 1e-6)
        return best[1]

    def owned(twin, link, source_links):
        """L'esquisse de ``link`` : neuve, dans le corps, attachée au
        profil collé."""
        sketch = self._as_object(link)
        support = list(getattr(sketch, "AttachmentSupport", None)
                       or getattr(sketch, "Support", None) or [])
        return (sketch not in source_links
                and sketch.getParentGeoFeatureGroup() is self._require_body()
                and sketch.MapMode == "ObjectXY"
                and support and support[0][0] is self._as_object(twin.Profile))

    # Un lissage à côté du bloc, collé sur le dessus du bloc (l'esquisse
    # garde ses coordonnées : la copie monte de 5) : même volume, sa
    # section le suit quand le bloc grandit.
    self.new_part("Coller un lissage")
    self.add_rect_sketch(20, 20)
    block = self.add_pad(5)["features"][0]["name"]
    body = self._require_body()
    low = self.sketch_start(plane="XY")["sketch"]
    square(low, 40, -10, 60, 10)
    datum = next(f["name"] for f in self.add_datum_plane(
        base="XY", offset=20)["features"] if f["type"] == "PartDesign::Plane")
    high = self.sketch_start(datum=datum)["sketch"]
    square(high, 45, -5, 55, 5)
    self.add_loft([low, high])
    source = body.Tip
    before = body.Shape.Volume
    count = len(self._doc.Objects)
    pasted = call("paste_feature", feature=source.Name, face=top_of(body, 0))
    twin = body.Tip
    section = self._as_object(twin.Sections[0])
    report["p111_lissage_colle"] = (
        pasted.get("ok") is True and twin is not source
        and owned(twin, twin.Sections[0],
                  [self._as_object(s) for s in source.Sections])
        and abs(twin.AddSubShape.Volume - source.AddSubShape.Volume) < 1e-6
        and body.Shape.Volume > before + 1
        and abs(section.getGlobalPlacement().Base.z - 25) < 1e-6
        and clean())
    call("set_params", feature=block, values={"length": 15})
    followed = (abs(section.getGlobalPlacement().Base.z - 35) < 1e-6
                and abs(twin.AddSubShape.Volume
                        - source.AddSubShape.Volume) < 1e-6)
    call("undo")
    call("undo")
    report["p111_suit_la_face_et_s_annule"] = (
        followed and len(self._doc.Objects) == count
        and body.Tip is source and clean())

    # Un balayage : sa trajectoire part avec lui.
    self.new_part("Coller un balayage")
    self.add_rect_sketch(20, 20)
    self.add_pad(5)
    body = self._require_body()
    spine = self.sketch_start(plane="XZ")["sketch"]
    self.sketch_add_line(spine, 40, 0, 40, 30)
    self.sketch_add_line(spine, 40, 30, 60, 30)
    self.sketch_finish(spine)
    ring = self.sketch_start(plane="XY")["sketch"]
    self.sketch_add_circle(ring, 40, 0, 3)
    self.sketch_finish(ring)
    self.add_sweep(ring, spine)
    source = body.Tip
    pasted = call("paste_feature", feature=source.Name, face=top_of(body, 0))
    twin = body.Tip
    report["p111_balayage_colle"] = (
        pasted.get("ok") is True and twin is not source
        and owned(twin, twin.Spine, [self._as_object(source.Spine)])
        and abs(twin.AddSubShape.Volume - source.AddSubShape.Volume) < 1e-6
        and clean())


def p112_reseau_reduit_confirme(self, mark, report, etat):
    mark("p112: réduire un réseau de corps demande confirmation")
    from engine.kernel import dispatch

    def call(name, confirmed=False, **params):
        return dispatch(self, name, params, confirmed=confirmed)

    def clean():
        return not any("Invalid" in (o.State or ()) for o in self._doc.Objects)

    # Quatre occurrences ; une extrusion sur la dernière copie, l'avant-
    # dernière combinée à la source.
    self.new_part("Réseau réduit")
    self.add_rect_sketch(10, 10)
    self.add_pad(8)
    source = self._require_body()
    self.add_body_pattern("linear", [source.Name], length=40, count=4,
                          axis="X", spacing=False)
    host = self._body_pattern_hosts()[0]
    ordered = sorted(self._body_pattern_copies(host).values(),
                     key=lambda body: body.Shape.BoundBox.XMin)
    last, before_last = ordered[-1], ordered[-2]
    self.set_active_body(last.Name)
    top = next(i for i, f in enumerate(last.Shape.Faces)
               if abs(f.CenterOfMass.z - 8) < 1e-6)
    x0 = last.Shape.BoundBox.XMin
    sketch = self.sketch_start(face=top)["sketch"]
    self.sketch_add_rectangle(sketch, x0 + 3, 3, x0 + 7, 7)
    self.sketch_finish(sketch)
    call("add_pad", length=3)
    extra = last.Tip
    extra_name, extra_label = extra.Name, extra.Label
    self.set_active_body(source.Name)
    call("add_boolean", tool=before_last.Name, type="fuse")
    combine = source.Tip
    count = len(self._doc.Objects)

    # Ramené à 2 : refusé avec la question, rien ne change ; l'aperçu
    # montre la réduction sans rien demander.
    asked = call("set_params", feature=host.Name, values={"Occurrences": 2})
    question = str(asked.get("confirm") or "")
    report["p112_question_avant_de_reduire"] = (
        asked.get("ok") is False
        and extra_label in question and combine.Label in question
        and "2 copie(s)" in question
        and len(self._doc.Objects) == count
        and len(self._body_pattern_copies(host)) == 3
        and int(host.Occurrences) == 4 and clean())
    shown = call("preview", op="set_params",
                 params={"feature": host.Name, "values": {"Occurrences": 2}})
    report["p112_apercu_sans_question"] = (
        shown.get("ok") is True and "confirm" not in shown
        and len(self._doc.Objects) == count)

    # Confirmé : réduit, et un seul Ctrl+Z rend tout.
    done = call("set_params", confirmed=True, feature=host.Name,
                values={"Occurrences": 2})
    reduced = (done.get("ok") is True
               and len(self._body_pattern_copies(host)) == 1
               and self._doc.getObject(extra_name) is None
               and not self._confirmed)
    call("undo")
    report["p112_confirme_puis_annule"] = (
        reduced and len(self._doc.Objects) == count
        and self._doc.getObject(extra_name) is not None
        and len(self._body_pattern_copies(host)) == 3 and clean())

    # Des copies qui ne portent rien partent sans question.
    self.new_part("Réseau nu")
    self.add_rect_sketch(10, 10)
    self.add_pad(8)
    bare = self._require_body()
    self.add_body_pattern("linear", [bare.Name], length=40, count=4,
                          axis="X", spacing=False)
    host = self._body_pattern_hosts()[0]
    quiet = call("set_params", feature=host.Name, values={"Occurrences": 2})
    report["p112_copies_vides_sans_question"] = (
        quiet.get("ok") is True and "confirm" not in quiet
        and len(self._body_pattern_copies(host)) == 1 and clean())



def p113_habillage_reedite_ses_aretes(self, mark, report, etat):
    mark("p113: un congé, un chanfrein re-choisissent leurs arêtes au rang")
    from engine.kernel import dispatch

    def call(name, **params):
        return dispatch(self, name, params)

    def clean():
        return not any("Invalid" in (o.State or ()) for o in self._doc.Objects)

    def entry(tree, name):
        return next((f for f in tree.get("features", ())
                     if f.get("name") == name), {})

    # Une extrusion, un congé sur deux arêtes, puis une extrusion qui
    # recouvre le dessus : la pièce d'aujourd'hui n'a plus les arêtes
    # d'avant le congé.
    self.new_part("Habillage réédité")
    self.add_rect_sketch(20, 20)
    self.add_pad(10)
    body = self._require_body()
    pad = body.Tip
    self.add_fillet(2, edges=[0, 2])
    fillet = body.Tip
    self.add_rect_sketch(6, 6)
    self.add_pad(20)
    last = body.Tip
    report["p113_arbre_dit_les_aretes"] = (
        entry(self.get_tree(), fillet.Name).get("dressup")
        == {"edges": [0, 2]})

    # Au rang du congé : la pièce d'avant lui. L'aperçu le montre réédité
    # sans quitter ce rang.
    call("rank_view", feature=fillet.Name)
    base_faces = len(body.Shape.Faces)
    shown = call("preview", op="set_params", params={
        "feature": fillet.Name,
        "values": {"radius": 1.5, "edges": [0, 2, 4, 6]}})
    groups = (shown.get("result") or {}).get("groups") or []
    report["p113_apercu_au_rang"] = (
        shown.get("ok") is True and self._rank_view is not None
        and body.Tip is pad and base_faces == 6 and len(groups) > base_faces
        and list(fillet.Base[1]) == ["Edge1", "Edge3"])

    # OK : la barre revient, les arêtes et le rayon changent ensemble ; un
    # Ctrl+Z rend les arêtes d'avant.
    done = call("set_params", feature=fillet.Name,
                values={"radius": 1.5, "edges": [0, 2, 4, 6]})
    changed = (done.get("ok") is True and self._rank_view is None
               and body.Tip is last
               and list(fillet.Base[1]) == ["Edge1", "Edge3", "Edge5", "Edge7"]
               and abs(float(fillet.Radius) - 1.5) < 1e-9
               and entry(done["result"], fillet.Name).get("dressup")
               == {"edges": [0, 2, 4, 6]} and clean())
    call("undo")
    report["p113_aretes_rechoisies"] = (
        changed and list(fillet.Base[1]) == ["Edge1", "Edge3"] and clean())

    # Un chanfrein après le congé, sur une arête que le congé a faite :
    # re-choisir les arêtes du congé la ferait disparaître — refusé, en
    # nommant le chanfrein. Le chanfrein, lui, passe à une face ; une
    # arête inconnue, des arêtes pour une extrusion : refusées.
    self.new_part("Habillage et sa suite")
    self.add_rect_sketch(20, 20)
    self.add_pad(10)
    body = self._require_body()
    pad = body.Tip
    self.add_fillet(2, edges=[0, 2])
    fillet = body.Tip
    self.add_chamfer(1, edges=[5])
    chamfer = body.Tip
    self.add_rect_sketch(6, 6)
    self.add_pad(20)
    broken = call("set_params", feature=fillet.Name,
                  values={"edges": [0, 2, 4, 6]})
    report["p113_refus_si_la_suite_perd_son_arete"] = (
        entry(self.get_tree(), chamfer.Name).get("dressup") == {"edges": [5]}
        and broken.get("ok") is False
        and chamfer.Label in str(broken.get("error"))
        and list(fillet.Base[1]) == ["Edge1", "Edge3"] and clean())
    top = next(i for i, f in enumerate(chamfer.Base[0].Shape.Faces)
               if abs(f.CenterOfMass.z - 10) < 1e-6)
    faced = call("set_params", feature=chamfer.Name, values={"face": top})
    unknown = call("set_params", feature=fillet.Name, values={"edges": [99]})
    foreign = call("set_params", feature=pad.Name, values={"edges": [1]})
    report["p113_face_et_refus"] = (
        faced.get("ok") is True
        and entry(faced["result"], chamfer.Name).get("dressup")
        == {"face": top}
        and unknown.get("ok") is False
        and "99" in str(unknown.get("error"))
        and list(fillet.Base[1]) == ["Edge1", "Edge3"]
        and foreign.get("ok") is False and clean())


def p114_coque_depouille_rechoisissent(self, mark, report, etat):
    mark("p114: une coque, une dépouille re-choisissent leurs faces au rang")
    from engine.kernel import dispatch

    def call(name, **params):
        return dispatch(self, name, params)

    def clean():
        return not any("Invalid" in (o.State or ()) for o in self._doc.Objects)

    def entry(tree, name):
        return next((f for f in tree.get("features", ())
                     if f.get("name") == name), {})

    def face_at(shape, axis, value):
        return next(i for i, f in enumerate(shape.Faces)
                    if abs((f.CenterOfMass.x, f.CenterOfMass.y,
                            f.CenterOfMass.z)[axis] - value) < 1e-6)

    # Coque ouverte sur le dessus, puis une extrusion par-dessus.
    self.new_part("Coque rééditée")
    self.add_rect_sketch(20, 20)
    self.add_pad(10)
    body = self._require_body()
    pad = body.Tip
    top = face_at(pad.Shape, 2, 10)
    side = face_at(pad.Shape, 0, 10)
    self.add_thickness(faces=[top], thickness=1)
    shell = body.Tip
    self.add_rect_sketch(6, 6)
    self.add_pad(20)
    listed = entry(self.get_tree(), shell.Name).get("shell") or {}
    call("rank_view", feature=shell.Name)
    shown = call("preview", op="set_params", params={
        "feature": shell.Name, "values": {"faces": [top, side]}})
    at_rank = (shown.get("ok") is True and self._rank_view is not None
               and body.Tip is pad)
    done = call("set_params", feature=shell.Name,
                values={"faces": [top, side], "thickness": 1.5})
    changed = (done.get("ok") is True and self._rank_view is None
               and sorted(shell.Base[1]) == sorted(
                   ["Face{}".format(top + 1), "Face{}".format(side + 1)])
               and (entry(done["result"], shell.Name).get("shell") or {})
               .get("faces") == [top, side] and clean())
    call("undo")
    empty = call("set_params", feature=shell.Name, values={"faces": []})
    edges = call("set_params", feature=shell.Name, values={"edges": [1]})
    report["p114_coque_rechoisit_ses_faces"] = (
        listed.get("faces") == [top] and at_rank and changed
        and list(shell.Base[1]) == ["Face{}".format(top + 1)]
        and empty.get("ok") is False and edges.get("ok") is False
        and clean())

    # Dépouille d'un flanc : passe à un autre flanc ; un plan neutre
    # parallèle à la face est refusé, la pièce reste telle quelle.
    self.new_part("Dépouille rééditée")
    self.add_rect_sketch(20, 20)
    self.add_pad(10)
    body = self._require_body()
    pad = body.Tip
    side = face_at(pad.Shape, 0, 10)
    other = face_at(pad.Shape, 1, 10)
    self.add_draft(side, 5, "XY")
    draft = body.Tip
    listed = entry(self.get_tree(), draft.Name).get("draft")
    call("rank_view", feature=draft.Name)
    shown = call("preview", op="set_params", params={
        "feature": draft.Name, "values": {"face": other}})
    at_rank = shown.get("ok") is True and self._rank_view is not None
    done = call("set_params", feature=draft.Name,
                values={"face": other, "angle": 4})
    moved = (done.get("ok") is True
             and list(draft.Base[1]) == ["Face{}".format(other + 1)]
             and entry(done["result"], draft.Name).get("draft")
             == {"face": other, "neutral": "XY"} and clean())
    parallel = call("set_params", feature=draft.Name,
                    values={"neutral": "XZ"})
    unknown = call("set_params", feature=draft.Name, values={"neutral": "AB"})
    foreign = call("set_params", feature=pad.Name, values={"neutral": "XY"})
    report["p114_depouille_rechoisit_face_et_plan"] = (
        listed == {"face": side, "neutral": "XY"} and at_rank and moved
        and parallel.get("ok") is False
        and self._draft_neutral_token(draft) == "XY"
        and unknown.get("ok") is False and foreign.get("ok") is False
        and clean())


def p115_percage_rechoisit_ses_positions(self, mark, report, etat):
    mark("p115: un perçage re-choisit sa face et ses positions au rang")
    from engine.kernel import dispatch

    def call(name, **params):
        return dispatch(self, name, params)

    def clean():
        return not any("Invalid" in (o.State or ()) for o in self._doc.Objects)

    def entry(tree, name):
        return next((f for f in tree.get("features", ())
                     if f.get("name") == name), {})

    def face_at(shape, axis, value):
        return next(i for i, f in enumerate(shape.Faces)
                    if abs((f.CenterOfMass.x, f.CenterOfMass.y,
                            f.CenterOfMass.z)[axis] - value) < 1e-6)

    # Deux trous sur le dessus, puis une extrusion par-dessus : on passe à
    # trois trous, puis à un trou sur un flanc ; annuler revient en arrière.
    self.new_part("Perçage réédité")
    self.add_rect_sketch(40, 40)
    self.add_pad(10)
    body = self._require_body()
    pad = body.Tip
    top = face_at(pad.Shape, 2, 10)
    side = face_at(pad.Shape, 0, 20)
    self.add_hole(4, through=True, face=top,
                  points=[[5, 5, 10], [-5, -5, 10]])
    hole = body.Tip
    self.add_rect_sketch(6, 6)
    self.add_pad(20)
    listed = entry(self.get_tree(), hole.Name).get("positions") or {}
    volume = body.Shape.Volume
    call("rank_view", feature=hole.Name)
    shown = call("preview", op="set_params", params={
        "feature": hole.Name,
        "values": {"positions": {"face": top, "points": [[10, 10, 10]]}}})
    at_rank = (shown.get("ok") is True and self._rank_view is not None
               and body.Tip is pad)
    three = [[10, 10, 10], [-10, 10, 10], [0, -10, 10]]
    done = call("set_params", feature=hole.Name, values={
        "positions": {"face": top, "points": three}})
    after = entry(done.get("result") or {}, hole.Name).get("positions") or {}
    more = (done.get("ok") is True and self._rank_view is None
            and after.get("face") == top
            and sorted(after.get("points") or ()) == sorted(three)
            and body.Shape.Volume < volume - 1e-6 and clean())
    flank = call("set_params", feature=hole.Name, values={
        "positions": {"face": side, "points": [[20, 0, 5]]}})
    moved = (flank.get("ok") is True
             and (entry(flank["result"], hole.Name).get("positions") or {})
             == {"face": side, "points": [[20, 0, 5]]} and clean())
    call("undo")
    back = entry(self.get_tree(), hole.Name).get("positions") or {}
    report["p115_percage_rechoisit_ses_positions"] = (
        listed.get("face") == top
        and sorted(listed.get("points") or ())
        == [[-5, -5, 10], [5, 5, 10]]
        and at_rank and more and moved
        and back.get("face") == top and len(back.get("points") or ()) == 3
        and clean())

    # Refus : aucune position, une face inconnue, des positions sur une
    # fonction qui n'est pas un perçage posé par clics.
    empty = call("set_params", feature=hole.Name, values={
        "positions": {"face": top, "points": []}})
    unknown = call("set_params", feature=hole.Name, values={
        "positions": {"face": 999, "points": [[0, 0, 10]]}})
    foreign = call("set_params", feature=pad.Name, values={
        "positions": {"face": top, "points": [[0, 0, 10]]}})
    report["p115_percage_positions_refusees"] = (
        empty.get("ok") is False and unknown.get("ok") is False
        and foreign.get("ok") is False
        and len((entry(self.get_tree(), hole.Name).get("positions") or {})
                .get("points") or ()) == 3
        and clean())


def p116_texte_rechoisit_sa_face(self, mark, report, etat):
    mark("p116: un texte re-choisit sa face d'appui au rang")
    from engine.kernel import dispatch

    def call(name, **params):
        return dispatch(self, name, params)

    def clean():
        return not any("Invalid" in (o.State or ()) for o in self._doc.Objects)

    def entry(tree, name):
        return next((f for f in tree.get("features", ())
                     if f.get("name") == name), {})

    def face_at(shape, axis, value):
        return next(i for i, f in enumerate(shape.Faces)
                    if abs((f.CenterOfMass.x, f.CenterOfMass.y,
                            f.CenterOfMass.z)[axis] - value) < 1e-6)

    def tool_of(text):
        tool = next(o for o in text.Group if o.TypeId == "PartDesign::Body")
        return tool.BaseFeature.Shape.BoundBox

    # Gravure sur le dessus, puis une extrusion par-dessus : la gravure
    # passe sur le flanc y = -10, plus petite ; annuler la ramène.
    self.new_part("Texte réédité")
    self.add_rect_sketch(60, 20)
    self.add_pad(10)
    body = self._require_body()
    pad = body.Tip
    top = face_at(pad.Shape, 2, 10)
    side = face_at(pad.Shape, 1, -10)
    self.add_text("AB", top, size=6, depth=1)
    text = body.Tip
    self.add_rect_sketch(6, 6)
    self.add_pad(20)
    listed = (entry(self.get_tree(), text.Name).get("text") or {}).get("face")
    call("rank_view", feature=text.Name)
    shown = call("preview", op="set_params", params={
        "feature": text.Name, "values": {"face": side}})
    at_rank = (shown.get("ok") is True and self._rank_view is not None
               and body.Tip is pad)
    done = call("set_params", feature=text.Name,
                values={"face": side, "size": 5})
    after = entry(done.get("result") or {}, text.Name).get("text") or {}
    box = tool_of(text)
    moved = (done.get("ok") is True and self._rank_view is None
             and after.get("face") == side and after.get("size") == 5
             and box.YMax < -8.9 and box.ZMax < 10 and clean())
    call("undo")
    back = entry(self.get_tree(), text.Name).get("text") or {}
    report["p116_texte_rechoisit_sa_face"] = (
        listed == top and at_rank and moved
        and back.get("face") == top and back.get("size") == 6
        and tool_of(text).ZMax > 10 and clean())

    # Refus : une clé de la création qui ne se change pas (le relief), une
    # cote qui n'est pas un nombre, une face inconnue, un texte vide.
    refused = [call("set_params", feature=text.Name, values=values)
               for values in ({"emboss": True}, {"size": "abc"},
                              {"face": 999}, {"text": " "})]
    report["p116_texte_refus"] = (
        all(r.get("ok") is False for r in refused)
        and (entry(self.get_tree(), text.Name).get("text") or {})
        .get("face") == top and clean())


def p117_chanfrein_de_sommet_rechoisit_son_coin(self, mark, report, etat):
    mark("p117: un chanfrein de sommet re-choisit son coin au rang")
    from engine.kernel import dispatch

    def call(name, **params):
        return dispatch(self, name, params)

    def clean():
        return not any("Invalid" in (o.State or ()) for o in self._doc.Objects)

    def entry(tree, name):
        return next((f for f in tree.get("features", ())
                     if f.get("name") == name), {})

    # Coin (10, 10, 10) d'un pavé, puis une extrusion par-dessus : le
    # chanfrein passe au coin opposé du dessus, trois distances ; annuler
    # le ramène.
    self.new_part("Chanfrein de sommet réédité")
    self.add_rect_sketch(20, 20)
    self.add_pad(10)
    body = self._require_body()
    pad = body.Tip
    self.add_vertex_chamfer([2], point=[10, 10, 10])
    cham = body.Tip
    self.add_rect_sketch(4, 4)
    self.add_pad(15)
    volume = body.Shape.Volume
    listed = entry(self.get_tree(), cham.Name).get("vertex_chamfer") or {}
    call("rank_view", feature=cham.Name)
    shown = call("preview", op="set_params", params={
        "feature": cham.Name, "values": {"point": [-10, -10, 10.3]}})
    at_rank = (shown.get("ok") is True and self._rank_view is not None
               and body.Tip is pad)
    done = call("set_params", feature=cham.Name, values={
        "point": [-10, -10, 10.3], "distances": [1, 2, 3]})
    after = (entry(done.get("result") or {}, cham.Name)
             .get("vertex_chamfer") or {})
    # 2·2·2/6 retiré avant, 1·2·3/6 après.
    moved = (done.get("ok") is True and self._rank_view is None
             and after.get("point") == [-10, -10, 10]
             and after.get("distances") == [1, 2, 3]
             and abs(body.Shape.Volume - volume - (8 - 6) / 6) < 1e-6
             and clean())
    call("undo")
    back = entry(self.get_tree(), cham.Name).get("vertex_chamfer") or {}
    report["p117_chanfrein_de_sommet_rechoisit_son_coin"] = (
        listed.get("point") == [10, 10, 10] and at_rank and moved
        and back.get("point") == [10, 10, 10]
        and back.get("distances") == [2, 2, 2] and clean())

    # Refus : un clic loin d'un coin, une clé qui n'est pas la sienne, des
    # distances fausses ; la fonction reste telle quelle.
    refused = [call("set_params", feature=cham.Name, values=values)
               for values in ({"point": [0, 0, 5]}, {"vertex": 3},
                              {"distances": [50]}, {"distances": [1, 2]})]
    report["p117_chanfrein_de_sommet_refus"] = (
        all(r.get("ok") is False for r in refused)
        and (entry(self.get_tree(), cham.Name).get("vertex_chamfer") or {})
        .get("point") == [10, 10, 10] and clean())


def p118_plan_d_esquisse_au_rang(self, mark, report, etat):
    mark("p118: le plan d'une esquisse se re-choisit au rang")
    from engine.kernel import dispatch

    def call(name, **params):
        return dispatch(self, name, params)

    def clean():
        return not any("Invalid" in (o.State or ()) for o in self._doc.Objects)

    def support(tree, name):
        def walk(items):
            for item in items:
                if item.get("name") == name:
                    return item
                found = walk(item.get("children") or ())
                if found:
                    return found
            return None
        return (walk(tree.get("features", ())) or {}).get("support")

    def face_at(shape, axis, value):
        return next(i for i, f in enumerate(shape.Faces)
                    if abs((f.CenterOfMass.x, f.CenterOfMass.y,
                            f.CenterOfMass.z)[axis] - value) < 1e-6)

    # Un bossage posé sur le dessus d'un pavé, puis une extrusion
    # par-dessus : son esquisse passe sur un flanc du pavé (une face de la
    # pièce à son rang), puis sur le plan XZ ; annuler la ramène.
    self.new_part("Plan d'esquisse au rang")
    self.add_rect_sketch(40, 40)
    self.add_pad(10)
    body = self._require_body()
    pad = body.Tip
    top = face_at(pad.Shape, 2, 10)
    side = face_at(pad.Shape, 0, 20)
    first = next(o for o in body.Group
                 if o.TypeId == "Sketcher::SketchObject")
    self.add_rect_sketch(10, 10, face=top)
    sketch = [o for o in body.Group
              if o.TypeId == "Sketcher::SketchObject"][-1]
    self.add_pad(5)
    boss = body.Tip
    self.add_rect_sketch(4, 4)
    self.add_pad(30)
    listed = support(self.get_tree(), sketch.Name)
    ranked = call("rank_view", feature=sketch.Name)
    at_rank = ranked.get("ok") is True and body.Tip is pad
    shown = call("preview", op="set_params", params={
        "feature": sketch.Name, "values": {"face": side}})
    previewed = shown.get("ok") is True and self._rank_view is not None
    flank = call("set_params", feature=sketch.Name, values={"face": side})
    on_flank = (flank.get("ok") is True and self._rank_view is None
                and support(flank["result"], sketch.Name) == {"face": side}
                and abs(boss.Shape.BoundBox.XMax - 25) < 1e-6 and clean())
    upright = call("set_params", feature=sketch.Name, values={"plane": "XZ"})
    on_plane = (upright.get("ok") is True
                and support(upright["result"], sketch.Name)
                == {"plane": "XZ"} and clean())
    call("undo")
    call("undo")
    report["p118_plan_d_esquisse_au_rang"] = (
        listed == {"face": top} and at_rank and previewed and on_flank
        and on_plane and support(self.get_tree(), sketch.Name)
        == {"face": top} and support(self.get_tree(), first.Name)
        == {"plane": "XY"} and clean())

    # Refus : une face inconnue, deux plans à la fois, un plan inconnu, la
    # face d'une pièce vide au rang de la première esquisse.
    refused = [call("set_params", feature=sketch.Name, values=values)
               for values in ({"face": 999}, {"plane": "XY", "face": 1},
                              {"plane": "AB"}, {"datum": "Inconnu"})]
    empty = call("set_params", feature=first.Name, values={"face": 0})
    report["p118_plan_d_esquisse_refus"] = (
        all(r.get("ok") is False for r in refused)
        and empty.get("ok") is False
        and support(self.get_tree(), sketch.Name) == {"face": top}
        and clean())


def p119_repetition_rechoisit_au_rang(self, mark, report, etat):
    mark("p119: une répétition re-choisit ses fonctions et sa direction")
    from engine.kernel import dispatch

    def call(name, **params):
        return dispatch(self, name, params)

    def clean():
        return not any("Invalid" in (o.State or ()) for o in self._doc.Objects)

    def state(tree, name):
        return next((f.get("pattern") for f in tree.get("features", ())
                     if f.get("name") == name), None) or {}

    def top():
        return max((i for i, f in enumerate(body.Tip.Shape.Faces)
                    if abs(f.CenterOfMass.z - 5) < 1e-6),
                   key=lambda i: body.Tip.Shape.Faces[i].Area)

    # Deux enlèvements dans le dessus d'une plaque, un réseau linéaire du
    # premier selon X, puis un bossage par-dessus.
    self.new_part("Répétition rééditée")
    self.add_rect_sketch(60, 60)
    self.add_pad(5)
    body = self._require_body()
    self.add_rect_sketch(4, 4, face=top())
    self.add_pocket(2)
    first = body.Tip
    self.add_rect_sketch(8, 2, face=top())
    self.add_pocket(1)
    second = body.Tip
    self.add_linear_pattern(20, 3, axis="X", spacing=True,
                            features=[first.Name])
    linear = body.Tip
    self.add_rect_sketch(2, 2)
    self.add_pad(20)
    listed = state(self.get_tree(), linear.Name)
    call("rank_view", feature=linear.Name)
    shown = call("preview", op="set_params", params={
        "feature": linear.Name, "values": {"axis": "Y"}})
    at_rank = (shown.get("ok") is True and self._rank_view is not None
               and body.Tip is second)
    done = call("set_params", feature=linear.Name, values={
        "features": [first.Name, second.Name], "axis": "Y",
        "reversed": True})
    after = state(done.get("result") or {}, linear.Name)
    rechosen = (done.get("ok") is True and self._rank_view is None
                and after.get("features") == [first.Name, second.Name]
                and after.get("axis") == "Y" and after.get("reversed") is True
                and clean())
    # Une arête droite de la plaque, parallèle à X.
    edge = next(i for i, e in enumerate(second.Shape.Edges)
                if e.Curve.TypeId == "Part::GeomLine" and e.Length > 50
                and abs(abs(e.Curve.Direction.x) - 1) < 1e-9)
    along = call("set_params", feature=linear.Name, values={"edge": edge})
    on_edge = (along.get("ok") is True
               and state(along["result"], linear.Name).get("edge") == edge)
    call("undo")
    call("undo")
    report["p119_repetition_rechoisit_fonctions_et_direction"] = (
        listed == {"features": [first.Name], "axis": "X", "edge": None,
                   "reversed": False, "mode": "spacing", "dir2": False}
        and at_rank and rechosen and on_edge
        and state(self.get_tree(), linear.Name) == listed and clean())

    # Réseau en pas : la distance rééditée est le pas (FreeCAD ignore la
    # longueur dans ce mode). Pas de 20 : le trou à x = 40 tombe hors de
    # la plaque ; pas de 10, ou longueur totale de 20 : trois trous.
    def distance():
        return next((p for p in self.get_params(linear.Name)["params"]
                     if p["key"] == "length"), {})
    pitch = distance()
    two_holes = body.Shape.Volume
    tighter = call("set_params", feature=linear.Name, values={"length": 10})
    three_holes = body.Shape.Volume
    extent = call("set_params", feature=linear.Name, values={
        "mode": "extent", "length": 20})
    total = distance()
    same = abs(body.Shape.Volume - three_holes) < 1e-6
    call("undo")
    call("undo")
    report["p119_repetition_pas_ou_longueur"] = (
        pitch.get("prop") == "Offset" and pitch.get("value") == 20
        and tighter.get("ok") is True
        and abs(two_holes - three_holes - 4 * 4 * 2) < 1e-6
        and extent.get("ok") is True
        and state(extent["result"], linear.Name).get("mode") == "extent"
        and total.get("prop") == "Length" and total.get("value") == 20
        and same
        and call("set_params", feature=linear.Name,
                 values={"mode": "pas"}).get("ok") is False
        and state(self.get_tree(), linear.Name) == listed and clean())

    # La deuxième direction s'active (pas de 10, réseau en pas), suit son
    # nombre, se retire ; une symétrie change de plan ; refus.
    opened = call("set_params", feature=linear.Name, values={
        "dir2": True, "axis2": "Y", "length2": 10, "count2": 2})
    two = state(opened.get("result") or {}, linear.Name)
    recount = call("set_params", feature=linear.Name, values={"count2": 3})
    stretched = abs(float(linear.Length2) - 20) < 1e-6
    closed = call("set_params", feature=linear.Name, values={"dir2": False})
    self.add_mirror("YZ", features=[first.Name])
    mirror = body.Tip
    flipped = call("set_params", feature=mirror.Name, values={"plane": "XZ"})
    refused = [
        call("set_params", feature=linear.Name, values=values)
        for values in ({"features": []}, {"dir2": True}, {"plane": "XY"},
                       {"edge": 999}, {"length2": 5})]
    report["p119_repetition_direction_2_et_symetrie"] = (
        opened.get("ok") is True and two.get("dir2") is True
        and two.get("axis2") == "Y" and two.get("length2") == 10
        and recount.get("ok") is True and stretched
        and closed.get("ok") is True and int(linear.Occurrences2) == 1
        and flipped.get("ok") is True
        and state(flipped["result"], mirror.Name).get("plane") == "XZ"
        and call("set_params", feature=mirror.Name,
                 values={"axis": "X"}).get("ok") is False
        and all(r.get("ok") is False for r in refused) and clean())


def p120_repetition_de_corps_rechoisit(self, mark, report, etat):
    mark("p120: une répétition de corps re-choisit ses corps et sa direction")
    from engine.kernel import dispatch

    def call(name, **params):
        return dispatch(self, name, params)

    def clean():
        return not any("Invalid" in (o.State or ()) for o in self._doc.Objects)

    def copies(host_name):
        """(volume, centre) des copies d'un réseau, triés."""
        out = []
        for o in self._doc.Objects:
            if str(getattr(o, "FreeSolidPatternCopy", "")).startswith(
                    host_name + "|"):
                bb = o.Shape.BoundBox
                out.append((round(o.Shape.Volume),
                            round((bb.XMin + bb.XMax) / 2, 6),
                            round((bb.YMin + bb.YMax) / 2, 6),
                            round((bb.ZMin + bb.ZMax) / 2, 6)))
        return sorted(out)

    def state(name):
        tree = self.get_tree()
        rows = tree["features"] + tree.get("other_features", [])
        return next((f.get("pattern") for f in rows
                     if f.get("name") == name), None) or {}

    # Un bloc A (10 × 10 × 8) et une tige B (4 × 4 × 20) ; A répété
    # trois fois selon X, au pas de 20.
    self.new_part("Corps répétés rééditée")
    self.add_rect_sketch(10, 10)
    self.add_pad(8)
    a = self._require_body()
    self.add_body()
    self.add_rect_sketch(4, 4)
    self.add_pad(20)
    b = self._require_body()
    self.set_active_body(a.Name)
    self.add_body_pattern("linear", [a.Name], length=20, count=3, axis="X",
                          spacing=True)
    host = self._body_pattern_hosts()[0]

    def edit(**values):
        return call("set_params", feature=host.Name, values=values)

    listed = state(host.Name)
    both = edit(sources=[a.Name, b.Name], axis="Y", reversed=True)
    moved = copies(host.Name) == [(320, 0, -40, 10), (320, 0, -20, 10),
                                  (800, 0, -40, 4), (800, 0, -20, 4)]
    extent = edit(mode="extent", length=60)
    spread = copies(host.Name) == [(320, 0, -60, 10), (320, 0, -30, 10),
                                   (800, 0, -60, 4), (800, 0, -30, 4)]
    call("undo")
    call("undo")
    # Une arête de A, verticale, sur A au rang du réseau.
    tip = self._pattern_source_at(host, a)
    edge = next(i for i, e in enumerate(tip.Shape.Edges)
                if e.Curve.TypeId == "Part::GeomLine"
                and abs(abs(e.Curve.Direction.z) - 1) < 1e-9)
    along = edit(edge=edge)
    lifted = copies(host.Name) == [(800, 0, 0, 24), (800, 0, 0, 44)]
    on_edge = state(host.Name).get("edge") == edge
    call("undo")
    report["p120_corps_et_direction"] = (
        listed == {"sources": [a.Name], "axis": "X", "edge": None,
                   "reversed": False, "mode": "spacing", "dir2": False}
        and both.get("ok") is True and moved
        and extent.get("ok") is True and spread
        and along.get("ok") is True and lifted and on_edge
        and state(host.Name) == listed and clean())

    # Une esquisse sur la première copie : la deuxième direction s'active
    # et se retire sans la faire partir ; retirer A la ferait partir, le
    # moteur le demande d'abord. Refus.
    first = next(o for o in self._doc.Objects
                 if getattr(o, "FreeSolidPatternCopy", "")
                 == "{}|{}|1".format(host.Name, a.Name))
    self.set_active_body(first.Name)
    top = next(i for i, f in enumerate(first.Shape.Faces)
               if abs(f.CenterOfMass.z - 8) < 1e-6)
    self.add_rect_sketch(2, 2, face=top)
    self.set_active_body(a.Name)
    carried = len(first.Group)
    opened = edit(dir2=True, axis2="Y", length2=15, count2=2)
    grid = len(copies(host.Name)) == 5
    kept = (self._doc.getObject(first.Name) is not None
            and len(first.Group) == carried)
    closed = edit(dir2=False)
    back = (len(copies(host.Name)) == 2
            and self._doc.getObject(first.Name) is not None
            and len(first.Group) == carried)
    asked = edit(sources=[b.Name])
    refused = [edit(**values) for values in (
        {"sources": []}, {"sources": [first.Name]}, {"plane": "XY"},
        {"mode": "pas"}, {"axis2": "Z"}, {"edge": 999})]
    report["p120_deuxieme_direction_et_refus"] = (
        opened.get("ok") is True and grid and kept
        and closed.get("ok") is True and back
        and asked.get("ok") is False and bool(asked.get("confirm"))
        and all(r.get("ok") is False for r in refused) and clean())

    # Une symétrie change de plan ; une répétition circulaire, d'axe.
    self.add_body_pattern("mirror", [first.Name], plane="YZ")
    mirror = self._body_pattern_hosts()[-1]
    across = copies(mirror.Name) == [(800, -20, 0, 4)]
    flipped = call("set_params", feature=mirror.Name,
                   values={"plane": "XY"})
    below = copies(mirror.Name) == [(800, 20, 0, -4)]
    self.add_body_pattern("polar", [b.Name], count=2, angle=180, axis="Z")
    polar = self._body_pattern_hosts()[-1]
    turned = call("set_params", feature=polar.Name, values={"axis": "X"})
    report["p120_symetrie_et_circulaire"] = (
        across and flipped.get("ok") is True and below
        and state(mirror.Name).get("plane") == "XY"
        and turned.get("ok") is True
        and state(polar.Name).get("axis") == "X"
        and copies(polar.Name) == [(320, 0, 0, -10)]
        and call("set_params", feature=mirror.Name,
                 values={"axis": "X"}).get("ok") is False
        and call("set_params", feature=polar.Name,
                 values={"mode": "extent"}).get("ok") is False
        and clean())


def p121_surface_rechoisit_sa_source(self, mark, report, etat):
    mark("p121: une surface re-choisit son contour, sa surface, ses bords")
    import Part
    from engine.kernel import dispatch

    def call(name, **params):
        return dispatch(self, name, params)

    def edit(obj, **values):
        return call("set_params", feature=obj.Name, values=values)

    def rect(x, y, w, h):
        name = self.sketch_start(plane="XY")["sketch"]
        self.sketch_add_rectangle(name, x, y, w, h)
        self.sketch_finish(name)
        return name

    def last(tree):
        return self._doc.getObject(tree["surfaces"][-1]["name"])

    def spec(obj):
        return next((s.get("surface") for s in self.get_tree()["surfaces"]
                     if s["name"] == obj.Name), None) or {}

    def clean():
        return not any("Invalid" in (o.State or ()) for o in self._doc.Objects)

    # Deux carrés (40 et 20) et un petit (10 × 10, ailleurs) ; une surface
    # plane du grand, une du petit, puis un décalage, un épaississement et
    # un prolongement d'un bord.
    self.new_part("Sources de surfaces")
    big, small, far = rect(0, 0, 40, 40), rect(0, 0, 20, 20), rect(60, 0, 10, 10)
    plane = last(self.surface_planar(sketch=big))
    other = last(self.surface_planar(sketch=far))
    offset = last(self.surface_offset(plane.Name, 10))
    thick = last(self.surface_thicken(other.Name, 2))
    extended = last(self.surface_extend(plane.Name, 10, edge=0))
    listed = (spec(plane) == {"kind": "planar", "sketch": big}
              and spec(offset).get("source") == plane.Name
              and spec(thick) == {"kind": "thicken", "distance": 2.0,
                                  "source": other.Name})
    contour = edit(plane, sketch=small)
    later = edit(plane, sketch=rect(0, 0, 5, 5))
    moved = edit(offset, source=other.Name)
    report["p121_plane_decalee_epaissie"] = (
        listed and contour.get("ok") is True
        and abs(plane.Shape.Area - 400) < 1e-6
        and later.get("ok") is False and "vient après" in later["error"]
        and moved.get("ok") is True
        and spec(offset).get("source") == other.Name
        and abs(offset.Shape.Area - other.Shape.Area) < 1e-6
        and edit(offset, source=offset.Name).get("ok") is False
        and edit(offset, source=extended.Name).get("ok") is False
        and edit(thick, source=plane.Name, distance=3).get("ok") is True
        and abs(thick.Shape.Volume - 20 * 20 * 3) < 1e-6 and clean())

    # Prolonger : tous les bords, puis un autre bord, puis l'autre carré.
    everywhere = edit(extended, edge=None)
    all_area = extended.Shape.Area
    one = edit(extended, edge=1, distance=5)
    one_area = extended.Shape.Area
    one_edge = spec(extended).get("edge")
    elsewhere = edit(extended, source=other.Name)
    shown = call("preview", op="set_params", params={
        "feature": offset.Name, "values": {"distance": 20}})
    report["p121_prolonger_rechoisit_son_bord"] = (
        everywhere.get("ok") is True and abs(all_area - 40 * 40) < 1
        and one.get("ok") is True and abs(one_area - 20 * 25) < 1
        and one_edge == 1
        and elsewhere.get("ok") is True
        and spec(extended).get("source") == other.Name
        and spec(extended).get("edge") is None
        and edit(extended, edge=99).get("ok") is False
        and shown.get("ok") is True and clean())

    # Congé de surface : son rayon, puis les arêtes d'une autre équerre.
    def corner(x):
        name = self.sketch_start(plane="XY")["sketch"]
        self.sketch_add_line(name, x, 0, x + 20, 0)
        self.sketch_add_line(name, x + 20, 0, x + 20, 20)
        self.sketch_finish(name)
        return last(self.surface_extrude(10, sketch=name))

    def shared(obj):
        return [i for i, e in enumerate(obj.Shape.Edges)
                if len(obj.Shape.ancestorsOfType(e, Part.Face)) == 2]

    first, second = corner(0), corner(50)
    fillet = last(self.surface_fillet(first.Name, shared(first), 3))
    area3 = fillet.Shape.Area
    wider = edit(fillet, radius=5)
    bare = edit(fillet, source=second.Name)
    moved = edit(fillet, source=second.Name, edges=shared(second))
    lone = next(i for i in range(len(second.Shape.Edges))
                if i not in shared(second))
    report["p121_conge_rechoisit_ses_aretes"] = (
        spec(fillet).get("edges") == shared(first)
        and wider.get("ok") is True and fillet.Shape.Area < area3
        and bare.get("ok") is False
        and moved.get("ok") is True
        and spec(fillet).get("source") == second.Name
        and fillet.Shape.BoundBox.XMin > 49
        and edit(fillet, edges=[lone]).get("ok") is False
        and clean())


def p122_outil_rechoisi(self, mark, report, etat):
    mark("p122: coupe, intersection et projection re-choisissent leurs "
         "formes")
    import math

    import FreeCAD as App
    from engine.kernel import dispatch

    def call(name, **params):
        return dispatch(self, name, params)

    def edit(obj, **values):
        return call("set_params", feature=obj.Name, values=values)

    def clean():
        return not any("Invalid" in (o.State or ()) for o in self._doc.Objects)

    def wall(x1, y1, x2, y2):
        name = self.sketch_start(plane="XY")["sketch"]
        self.sketch_add_line(name, x1, y1, x2, y2)
        self.sketch_finish(name)
        self._doc.getObject(name).AttachmentOffset = App.Placement(
            App.Vector(0, 0, -10), App.Rotation())
        self._recompute()
        return self.surface_extrude(40, sketch=name)["surfaces"][-1]["name"]

    def volume():
        return self._require_body().Shape.Volume

    def cut_spec(cut):
        return next(f for f in self.get_tree()["features"]
                    if f["name"] == cut.Name).get("surface_cut")

    # Un bloc 40 × 40 × 20 coupé par sa diagonale ; un mur à x = 10, un
    # autre hors du bloc.
    self.new_part("Coupe re-choisie")
    self.add_rect_sketch(40, 40)
    self.add_pad(20)
    diagonal = wall(-40, -40, 40, 40)
    side = wall(10, -40, 10, 40)
    far = wall(100, -40, 100, 40)
    self.add_surface_cut(diagonal)
    cut = self._require_body().Tip
    moved = edit(cut, surface=side)
    on_side = volume()
    banded = edit(cut, thickness=4, flip=True)
    in_band = volume()
    band_spec = cut_spec(cut)
    whole = edit(cut, thickness=None, flip=False)
    refused = edit(cut, surface=far)
    later = wall(-10, -40, -10, 40)
    report["p122_coupe_rechoisit_sa_surface"] = (
        moved.get("ok") is True and abs(on_side - 8000) < 1e-3
        and banded.get("ok") is True and abs(in_band - 28800) < 1e-3
        and band_spec == {"surface": side, "flip": True, "thickness": 4.0}
        and whole.get("ok") is True and abs(volume() - 8000) < 1e-3
        and refused.get("ok") is False and abs(volume() - 8000) < 1e-3
        and cut_spec(cut) == {"surface": side, "flip": False}
        and "vient après" in (edit(cut, surface=later).get("error") or "")
        and clean())

    # Courbe d'intersection : un plancher à z = 5, coupé par un tube de
    # rayon 5 puis par un de rayon 8, puis le tube et le solide.
    def last(tree):
        return self._doc.getObject(tree["surfaces"][-1]["name"])

    def circle(x, y, r, z):
        name = self.sketch_start(plane="XY")["sketch"]
        self.sketch_add_circle(name, x, y, r)
        self.sketch_finish(name)
        self._doc.getObject(name).AttachmentOffset = App.Placement(
            App.Vector(0, 0, z), App.Rotation())
        self._recompute()
        return name

    def square(z):
        name = self.sketch_start(plane="XY")["sketch"]
        self.sketch_add_rectangle(name, -30, -30, 30, 30)
        self.sketch_finish(name)
        self._doc.getObject(name).AttachmentOffset = App.Placement(
            App.Vector(0, 0, z), App.Rotation())
        self._recompute()
        return last(self.surface_planar(sketch=name))

    def curve_spec(obj):
        return next(s for s in self.get_tree()["surfaces"]
                    if s["name"] == obj.Name).get("surface")

    self.new_part("Courbes re-choisies")
    self.add_rect_sketch(40, 40)
    self.add_pad(10)
    floor, high = square(5), square(20)
    tube = last(self.surface_extrude(30, sketch=circle(0, 0, 5, -5)))
    wide = last(self.surface_extrude(30, sketch=circle(0, 0, 8, -5)))
    section = last(self.curve_intersection(floor.Name, tube.Name))
    listed = curve_spec(section) == {"kind": "intersection",
                                     "first": floor.Name,
                                     "second": tube.Name, "body": False}
    wider = edit(section, second=wide.Name)
    wide_length = section.Shape.Length
    solid = edit(section, first=tube.Name, body=True)
    report["p122_intersection_rechoisit_ses_formes"] = (
        listed and wider.get("ok") is True
        and abs(wide_length - 2 * math.pi * 8) < 1e-3
        and solid.get("ok") is True
        and abs(section.Shape.Length - 4 * math.pi * 5) < 1e-3
        and curve_spec(section)["body"] is True
        and edit(section, body=False).get("ok") is False
        and edit(section, body=False, first=high.Name,
                 second=floor.Name).get("ok") is False
        and abs(section.Shape.Length - 4 * math.pi * 5) < 1e-3
        and clean())

    # Courbe projetée : un cercle projeté sur le plancher, puis un autre
    # cercle, puis sur la surface haute.
    first, other = circle(0, 0, 4, 40), circle(5, 5, 2, 40)
    projected = last(self.curve_project(first, floor.Name))
    listed = curve_spec(projected) == {"kind": "project", "sketch": first,
                                       "surface": floor.Name, "face": 0}
    swapped = edit(projected, sketch=other)
    small = projected.Shape.Length
    raised = edit(projected, surface=high.Name)
    later = circle(0, 0, 1, 40)
    report["p122_projetee_rechoisit_esquisse_et_face"] = (
        listed and swapped.get("ok") is True
        and abs(small - 2 * math.pi * 2) < 1e-3
        and raised.get("ok") is True
        and abs(projected.Shape.BoundBox.ZMin - 20) < 1e-3
        and edit(projected, face=3).get("ok") is False
        and "vient après" in (edit(projected, sketch=later).get("error")
                              or "")
        and clean())


def p123_ajuster_rechoisit(self, mark, report, etat):
    mark("p123: un ajustement re-choisit son outil et sa partie gardée")
    import FreeCAD as App
    from engine.kernel import dispatch

    def edit(obj, **values):
        return dispatch(self, "set_params",
                        {"feature": obj.Name, "values": values})

    def clean():
        return not any("Invalid" in (o.State or ()) for o in self._doc.Objects)

    def last(tree):
        return self._doc.getObject(tree["surfaces"][-1]["name"])

    def square(x1, y1, x2, y2):
        name = self.sketch_start(plane="XY")["sketch"]
        self.sketch_add_rectangle(name, x1, y1, x2, y2)
        self.sketch_finish(name)
        return last(self.surface_planar(sketch=name))

    def wall(x):
        name = self.sketch_start(plane="XY")["sketch"]
        self.sketch_add_line(name, x, -10, x, 100)
        self.sketch_finish(name)
        self._doc.getObject(name).AttachmentOffset = App.Placement(
            App.Vector(0, 0, -10), App.Rotation())
        self._recompute()
        return last(self.surface_extrude(20, sketch=name))

    def span(obj):
        box = obj.Shape.BoundBox
        return (round(box.XMin, 3), round(box.XMax, 3), round(box.YMin, 3))

    # Deux carrés de 40 (y de 0 à 40, et de 50 à 90), coupés par des murs
    # à x = 10 et x = 30.
    self.new_part("Ajuster re-choisi")
    floor, other = square(0, 0, 40, 40), square(0, 50, 40, 90)
    near, far = wall(10), wall(30)
    trim = last(self.surface_trim(floor.Name, near.Name, point=[5, 20, 0]))
    listed = next(s for s in self.get_tree()["surfaces"]
                  if s["name"] == trim.Name)["surface"]
    tool = edit(trim, tool=far.Name)
    same_side = span(trim)
    side = edit(trim, point=[35, 20, 0])
    other_side = span(trim)
    moved = edit(trim, source=other.Name, point=[5, 70, 0])
    report["p123_ajuster_rechoisit_outil_et_partie"] = (
        listed.get("tool") == near.Name and listed.get("point") is not None
        and tool.get("ok") is True and same_side == (0, 30, 0)
        and side.get("ok") is True and other_side == (30, 40, 0)
        and moved.get("ok") is True and span(trim) == (0, 30, 50)
        and edit(trim, tool=other.Name).get("ok") is False
        and span(trim) == (0, 30, 50)
        and clean())


def p124_radiee_rechoisit_son_contour(self, mark, report, etat):
    mark("p124: une surface radiée re-choisit son contour")
    from engine.kernel import dispatch

    def edit(obj, **values):
        return dispatch(self, "set_params",
                        {"feature": obj.Name, "values": values})

    def clean():
        return not any("Invalid" in (o.State or ()) for o in self._doc.Objects)

    def last(tree):
        return self._doc.getObject(tree["surfaces"][-1]["name"])

    def square(x1, y1, x2, y2):
        name = self.sketch_start(plane="XY")["sketch"]
        self.sketch_add_rectangle(name, x1, y1, x2, y2)
        self.sketch_finish(name)
        return name

    def boundary(obj):
        return next(s for s in self.get_tree()["surfaces"]
                    if s["name"] == obj.Name)["surface"]["boundary"]

    # Un bloc 40 × 40 × 10 et un carré de 20 à côté ; une collerette de 5
    # autour du haut du bloc, puis autour du carré.
    self.new_part("Radiée re-choisie")
    self.add_rect_sketch(40, 40)
    self.add_pad(10)
    body = self._require_body()
    top = [i for i, e in enumerate(body.Shape.Edges)
           if abs(e.CenterOfMass.z - 10) < 1e-6]
    plate = last(self.surface_planar(sketch=square(100, 0, 120, 20)))
    collar = last(self.surface_radiate(
        [{"body": True, "edge": i} for i in top], 5))
    listed = boundary(collar) == [{"body": True, "edge": i} for i in top]
    around = abs(collar.Shape.Area - (50 * 50 - 40 * 40)) < 1e-3
    moved = edit(collar, boundary=[{"name": plate.Name}])
    plate_area = collar.Shape.Area
    later = self.surface_planar(sketch=square(200, 0, 220, 20))
    refused = edit(collar, boundary=[{"name": later["surfaces"][-1]["name"]}])
    report["p124_radiee_rechoisit_son_contour"] = (
        listed and around
        and moved.get("ok") is True
        and abs(plate_area - (30 * 30 - 20 * 20)) < 1e-3
        and len(boundary(collar)) == 4
        and all(b.get("name") == plate.Name for b in boundary(collar))
        and refused.get("ok") is False
        and "vient après" in (refused.get("error") or "")
        and abs(collar.Shape.Area - plate_area) < 1e-6
        and clean())


def p125_forme_libre_rechoisit_sa_surface(self, mark, report, etat):
    mark("p125: une forme libre (points ou pôles) re-choisit sa surface")
    from engine.kernel import dispatch

    def edit(obj, **values):
        return dispatch(self, "set_params",
                        {"feature": obj.Name, "values": values})

    def clean():
        return not any("Invalid" in (o.State or ()) for o in self._doc.Objects)

    def last(tree):
        return self._doc.getObject(tree["surfaces"][-1]["name"])

    def square(x1, y1, x2, y2):
        name = self.sketch_start(plane="XY")["sketch"]
        self.sketch_add_rectangle(name, x1, y1, x2, y2)
        self.sketch_finish(name)
        return last(self.surface_planar(sketch=name))

    def spec(obj):
        return next(s for s in self.get_tree()["surfaces"]
                    if s["name"] == obj.Name)["surface"]

    def span(obj):
        box = obj.Shape.BoundBox
        return (round(box.XMin, 3), round(box.YMin, 3), round(box.ZMax, 3))

    # Deux carrés qui se chevauchent : une bosse de 5 au milieu du premier,
    # puis la même forme libre sur le second ; un pôle levé de 7.
    self.new_part("Forme libre re-choisie")
    first, second = square(0, 0, 40, 40), square(-10, -10, 30, 30)
    bump = last(self.surface_freeform(first.Name, radius=10,
                                      pushes=[[20, 20, 0, 5]]))
    moved = edit(bump, source=second.Name)
    pole = last(self.surface_freeform(first.Name, moves=[[1, 1, 0, 0, 7]]))
    pole_moved = edit(pole, source=second.Name)
    later = square(100, 0, 110, 10)
    report["p125_forme_libre_rechoisit_sa_surface"] = (
        spec(bump)["source"] == second.Name and moved.get("ok") is True
        and span(bump) == (-10, -10, 5)
        and edit(bump, radius=6).get("ok") is True
        and spec(bump)["radius"] == 6
        and pole_moved.get("ok") is True
        and spec(pole)["source"] == second.Name and span(pole) == (-10, -10, 7)
        and edit(pole, radius=3).get("ok") is False
        and "vient après" in (edit(bump, source=later.Name).get("error")
                              or "")
        and spec(bump)["source"] == second.Name
        and clean())


def p126_combiner_rechoisit(self, mark, report, etat):
    mark("p126: un « Combiner » re-choisit son opération et son corps outil")
    from engine.kernel import dispatch

    def edit(obj, **values):
        return dispatch(self, "set_params",
                        {"feature": obj.Name, "values": values})

    def clean():
        return not any("Invalid" in (o.State or ()) for o in self._doc.Objects)

    def spec(obj):
        return next(f for f in self.get_tree()["features"]
                    if f["name"] == obj.Name).get("combine")

    def present():
        return {b["name"] for b in self.get_tree()["bodies"]}

    # Une plaque 40 × 40 × 10 ; deux poteaux qui la traversent, 10 × 10
    # et 20 × 20, hauts de 30 (centrés).
    self.new_part("Combiner re-choisi")
    self.add_rect_sketch(40, 40)
    self.add_pad(10)
    plate = self._require_body()
    posts = []
    for side in (10, 20):
        self.add_body()
        self.add_rect_sketch(side, side)
        self.add_pad(30)
        posts.append(self._require_body())
    small, large = posts
    self.set_active_body(plate.Name)
    self.add_boolean(small.Name, "cut")
    combine = plate.Tip
    listed = spec(combine) == {"type": "cut", "tool": small.Name,
                               "tool_label": self._body_title(small)}
    fused = edit(combine, type="fuse")
    fused_volume = plate.Shape.Volume
    swapped = edit(combine, tool=large.Name)
    report["p126_combiner_rechoisit"] = (
        listed and fused.get("ok") is True
        and abs(fused_volume - 18000) < 1e-3
        and swapped.get("ok") is True
        and abs(plate.Shape.Volume - 24000) < 1e-3
        and spec(combine)["tool"] == large.Name
        and small.Name in present() and large.Name not in present()
        and edit(combine, tool=plate.Name).get("ok") is False
        and spec(combine)["tool"] == large.Name
        and clean())


def p127_indices_suivent_leur_cible(self, mark, report, etat):
    mark("p127: les indices de face et d'arête suivent leur cible quand "
         "l'esquisse amont change")
    import FreeCAD as App
    import Part

    def last(tree):
        return self._doc.getObject(tree["surfaces"][-1]["name"])

    def inside(shape, x, y, z):
        return shape.isInside(App.Vector(x, y, z), 1e-6, True)

    def valid(obj):
        return "Invalid" not in (obj.State or ())

    def spec(obj):
        return next(s for s in self.get_tree()["surfaces"]
                    if s["name"] == obj.Name)["surface"]

    def grow(sketch, *segment):
        # Un segment de plus dans l'esquisse amont : l'ordre de ses
        # arêtes — et des faces et arêtes qu'on en tire — change.
        self.sketch_edit(sketch)
        if len(segment) == 4:
            self.sketch_add_line(sketch, *segment)
        else:
            self.sketch_add_rectangle(sketch, *segment[1:])
        self.sketch_finish(sketch)
        self._recompute()

    # Une plaque 40 × 40 × 10, son arête du haut à y = +20 arrondie de 3,
    # celle à y = -20 chanfreinée de 2, puis une surface radiée de 5 sur
    # ses arêtes longues du haut.
    self.new_part("Indices suivis")
    self.add_rect_sketch(40, 40)
    self.add_pad(10)
    body = self._require_body()
    sketch = body.Tip.Profile[0].Name
    edge = next(i for i, e in enumerate(body.Shape.Edges)
                if abs(e.CenterOfMass.z - 10) < 1e-6
                and abs(e.CenterOfMass.y - 20) < 1e-6)
    self.add_fillet(3, edges=[edge])
    edge = next(i for i, e in enumerate(body.Shape.Edges)
                if abs(e.CenterOfMass.z - 10) < 1e-6
                and abs(e.CenterOfMass.y + 20) < 1e-6)
    self.add_chamfer(2, edges=[edge])
    top = [i for i, e in enumerate(body.Shape.Edges)
           if abs(e.CenterOfMass.z - 10) < 1e-6 and e.Length > 30]
    rad = last(self.surface_radiate([{"body": True, "edge": i}
                                     for i in top], 5))
    rad_area = rad.Shape.Area
    # Une équerre ouverte (20 puis 30), extrudée de 10 : son arête commune
    # arrondie de 3, un pôle de sa face de 30 tiré de 5 en x, et le patron
    # à plat de cette même face.
    corner_sketch = self.sketch_start(plane="XY")["sketch"]
    self.sketch_add_line(corner_sketch, 0, 100, 20, 100)
    self.sketch_add_line(corner_sketch, 20, 100, 20, 130)
    self.sketch_finish(corner_sketch)
    corner = last(self.surface_extrude(10, sketch=corner_sketch))
    shared = [i for i, e in enumerate(corner.Shape.Edges)
              if len(corner.Shape.ancestorsOfType(e, Part.Face)) == 2]
    fillet = last(self.surface_fillet(corner.Name, shared, 3))
    fillet_area = fillet.Shape.Area
    tall = next(i for i, f in enumerate(corner.Shape.Faces)
                if abs(f.Area - 300) < 1e-6)
    pole = last(self.surface_freeform(corner.Name,
                                      moves=[[tall, 2, 2, 5, 0, 0]]))
    flat = last(self.surface_flatten(corner.Name, face=tall))
    before = (round(pole.Shape.BoundBox.XMax, 3), round(flat.Shape.Area, 3))
    # Un trou au milieu de la plaque, un segment au début de l'équerre.
    grow(sketch, "rect", -5, -5, 5, 5)
    grow(corner_sketch, -20, 100, 0, 100)
    tall_now = next(i for i, f in enumerate(corner.Shape.Faces)
                    if abs(f.Area - 300) < 1e-6)
    filleted = [int(e[0]) - 1 for e in fillet.Edges]
    report["p127_indices_suivent_leur_cible"] = (
        before == (25, 300) and tall_now != tall
        and valid(body.Tip) and valid(body.Tip.BaseFeature)
        and not inside(body.Shape, 0, 19.9, 9.9)
        and not inside(body.Shape, 0, -19.9, 9.9)
        and inside(body.Shape, 19.9, 0, 9.9)
        and valid(rad) and abs(rad.Shape.Area - rad_area) < 1e-6
        # Le congé rend toute l'équerre : la face ajoutée (20 × 10) en plus.
        and valid(fillet)
        and abs(fillet.Shape.Area - fillet_area - 200) < 1e-6
        and len(filleted) == 1
        and abs(corner.Shape.Edges[filleted[0]].CenterOfMass.x - 20) < 1e-6
        and round(pole.Shape.BoundBox.XMax, 3) == 25
        and spec(pole)["moves"][0][0] == tall_now
        and round(flat.Shape.Area, 3) == 300
        and spec(flat)["face"] == tall_now)


def p128_face_d_arrivee_rechoisie(self, mark, report, etat):
    mark("p128: une extrusion re-choisit sa face d'arrivée, ou y passe")
    from engine.kernel import dispatch

    def edit(obj, **values):
        return dispatch(self, "set_params",
                        {"feature": obj.Name, "values": values})

    def rect(x1, y1, x2, y2):
        name = self.sketch_start(plane="XY")["sketch"]
        self.sketch_add_rectangle(name, x1, y1, x2, y2)
        self.sketch_finish(name)

    def top(z, x):
        return next(i for i, f in enumerate(body.Shape.Faces)
                    if abs(f.CenterOfMass.z - z) < 1e-6
                    and abs(f.CenterOfMass.x - x) < 1e-6)

    def state(obj):
        return next(f for f in self.get_tree()["features"]
                    if f["name"] == obj.Name)["extrude"]

    # Une plaque 40 × 40 × 10, deux tours 10 × 10 hautes de 30 et de 20 ;
    # un plot 10 × 10 à côté, monté jusqu'au dessus de la tour de 30.
    self.new_part("Face d'arrivée re-choisie")
    self.add_rect_sketch(40, 40)
    self.add_pad(10)
    body = self._require_body()
    rect(10, 10, 20, 20)
    self.add_pad(30)
    rect(-20, 10, -10, 20)
    self.add_pad(20)
    before = body.Shape.Volume
    high, low = top(30, 15), top(20, -15)
    rect(-15, -15, -5, -5)
    self.add_pad(cond="face", face=high)
    stud = body.Tip
    made = abs(body.Shape.Volume - before - 2000) < 1e-6
    listed = state(stud)["face"] == high
    # Au rang, comme le panneau : la tour de 20, puis retour au borgne et
    # de nouveau jusqu'à la face.
    dispatch(self, "rank_view", {"feature": stud.Name})
    lowered = edit(stud, face=low)
    lowered_volume = body.Shape.Volume - before
    blind = edit(stud, cond="borgne", length=15)
    blind_volume = body.Shape.Volume - before
    back = edit(stud, cond="face", face=high)
    report["p128_face_d_arrivee_rechoisie"] = (
        made and listed and lowered.get("ok") is True
        and abs(lowered_volume - 1000) < 1e-6
        and getattr(self, "_rank_view", None) is None
        and blind.get("ok") is True
        and abs(blind_volume - 500) < 1e-6
        and back.get("ok") is True
        and abs(body.Shape.Volume - before - 2000) < 1e-6
        and state(stud)["face"] == high
        # Une face inconnue, ou sans « jusqu'à la face » : refusées.
        and edit(stud, face=999).get("ok") is False
        and "n'est pas" in (edit(stud, cond="borgne", length=5, face=low)
                            .get("error") or "")
        and abs(body.Shape.Volume - before - 2000) < 1e-6
        and "Invalid" not in (stud.State or ()))


def p129_lissage_balayage_rechoisissent(self, mark, report, etat):
    mark("p129: un lissage re-choisit ses profils, un balayage son profil "
         "et sa trajectoire")
    import math
    from engine.kernel import dispatch

    def edit(obj, **values):
        return dispatch(self, "set_params",
                        {"feature": obj.Name, "values": values})

    def plane(z):
        self.add_datum_plane(base="XY", offset=z)
        return [o.Name for o in self._doc.Objects
                if o.TypeId == "PartDesign::Plane"][-1]

    def rect(x1, y1, x2, y2, datum=None):
        name = (self.sketch_start(datum=datum) if datum
                else self.sketch_start(plane="XY"))["sketch"]
        self.sketch_add_rectangle(name, x1, y1, x2, y2)
        self.sketch_finish(name)
        return name

    def circle(r, plane="XY"):
        name = self.sketch_start(plane=plane)["sketch"]
        self.sketch_add_circle(name, 0, 0, r)
        self.sketch_finish(name)
        return name

    def line(length):
        name = self.sketch_start(plane="XZ")["sketch"]
        self.sketch_add_line(name, 0, 0, 0, length)
        self.sketch_finish(name)
        return name

    def spec(obj):
        return next(f for f in self.get_tree()["features"]
                    if f["name"] == obj.Name).get("swept")

    def names(obj):
        return [p["name"] for p in spec(obj)["profiles"]]

    def clean():
        return not any("Invalid" in (o.State or ()) for o in self._doc.Objects)

    # Trois carrés : 20 au sol, 10 à z = 20, 20 à z = 40 ; un second corps
    # a son carré de 16 à z = 20.
    self.new_part("Lissage re-choisi")
    body = self._require_body()
    low, high = plane(20), plane(40)
    a = rect(-10, -10, 10, 10)
    b = rect(-5, -5, 5, 5, datum=low)
    c = rect(-10, -10, 10, 10, datum=high)
    self.add_body()
    d = rect(-8, -8, 8, 8, datum=plane(20))
    self.set_active_body(body.Name)
    self.add_loft([a, b, c])
    loft = body.Tip
    waisted = body.Shape.Volume
    listed = names(loft) == [a, b, c]
    straight = edit(loft, profiles=[a, c])
    straight_volume = body.Shape.Volume
    flipped = edit(loft, profiles=[c, b, a])
    flipped_names = names(loft)
    # Le carré de l'autre corps entre par un liant caché, qui part quand
    # le profil est retiré.
    count = len(self._doc.Objects)
    linked = edit(loft, profiles=[a, d, c])
    helpers = len(self._swept_helpers(loft))
    back = edit(loft, profiles=[a, b, c])
    restored = (names(loft) == [a, b, c] and not self._swept_helpers(loft)
                and len(self._doc.Objects) == count
                and abs(body.Shape.Volume - waisted) < 1e-6)
    later = rect(-3, -3, 3, 3, datum=high)
    report["p129_lissage_rechoisit"] = (
        listed and straight.get("ok") is True
        and abs(straight_volume - 20 * 20 * 40) < 1e-6
        and flipped.get("ok") is True and flipped_names == [c, b, a]
        and linked.get("ok") is True and helpers == 1
        and back.get("ok") is True and restored
        and edit(loft, ruled=True).get("ok") is True
        and spec(loft)["ruled"] is True
        # Refus : un seul profil, deux fois le même, une esquisse d'après ;
        # avec un corps inconnu, rien ne change.
        and edit(loft, profiles=[a]).get("ok") is False
        and edit(loft, profiles=[a, a]).get("ok") is False
        and "vient après" in (edit(loft, profiles=[a, later])
                              .get("error") or "")
        and edit(loft, profiles=[a, c], bodies=["Inconnu"]).get("ok")
        is False
        and names(loft) == [a, b, c] and clean())

    # Un cercle de 3 le long d'un trait de 30 ; un trait de 50, un cercle
    # de 2, une courbe 3D.
    self.new_part("Balayage re-choisi")
    body = self._require_body()
    short, long_ = line(30), line(50)
    big, small = circle(3), circle(2)
    curve = self.add_curve3d([[0, 0, 0], [0, 0, 30], [20, 0, 50]],
                             spline=True)["surfaces"][-1]["name"]
    self.add_sweep(big, short)
    pipe = body.Tip
    first = spec(pipe) == {"kind": "sweep",
                           "profile": {"name": big, "label": self._doc
                                       .getObject(big).Label},
                           "spine": {"name": short, "label": self._doc
                                     .getObject(short).Label}}
    longer = edit(pipe, spine=long_)
    longer_volume = body.Shape.Volume
    thinner = edit(pipe, profile=small)
    thinner_volume = body.Shape.Volume
    curved = edit(pipe, spine=curve)
    on_curve = (spec(pipe)["spine"].get("curve") is True
                and len(self._swept_helpers(pipe)) == 1)
    back = edit(pipe, profile=big, spine=short)
    report["p129_balayage_rechoisit"] = (
        first and longer.get("ok") is True
        and abs(longer_volume - math.pi * 9 * 50) < 1e-6
        and thinner.get("ok") is True
        and abs(thinner_volume - math.pi * 4 * 50) < 1e-6
        and curved.get("ok") is True and on_curve
        and back.get("ok") is True and not self._swept_helpers(pipe)
        and abs(body.Shape.Volume - math.pi * 9 * 30) < 1e-6
        and "différents" in (edit(pipe, profile=short).get("error") or "")
        and clean())


def p130_aplatir_rechoisit_sa_face(self, mark, report, etat):
    mark("p130: un patron à plat re-choisit sa surface et sa face")
    import math
    from engine.kernel import dispatch

    def edit(obj, **values):
        return dispatch(self, "set_params",
                        {"feature": obj.Name, "values": values})

    def last(tree):
        return self._doc.getObject(tree["surfaces"][-1]["name"])

    def spec(obj):
        return next(s for s in self.get_tree()["surfaces"]
                    if s["name"] == obj.Name)["surface"]

    # Une équerre ouverte (20 puis 30) extrudée de 10, et un carré plan
    # de 40 : le patron de la face de 20, puis de celle de 30, puis du
    # carré.
    self.new_part("Patron re-choisi")
    name = self.sketch_start(plane="XY")["sketch"]
    self.sketch_add_line(name, 0, 100, 20, 100)
    self.sketch_add_line(name, 20, 100, 20, 130)
    self.sketch_finish(name)
    corner = last(self.surface_extrude(10, sketch=name))
    square = self.sketch_start(plane="XY")["sketch"]
    self.sketch_add_rectangle(square, 200, 0, 240, 40)
    self.sketch_finish(square)
    plate = last(self.surface_planar(sketch=square))
    short = next(i for i, f in enumerate(corner.Shape.Faces)
                 if abs(f.Area - 200) < 1e-6)
    tall = next(i for i, f in enumerate(corner.Shape.Faces)
                if abs(f.Area - 300) < 1e-6)
    flat = last(self.surface_flatten(corner.Name, face=short))
    first = round(flat.Shape.Area, 3) == 200 and spec(flat) == {
        "kind": "flatten", "face": short, "surface": corner.Name,
        "area_error": 0.0, "edge_error": 0.0}
    taller = edit(flat, face=tall)
    taller_area = round(flat.Shape.Area, 3)
    moved = edit(flat, surface=plate.Name)
    report["p130_aplatir_rechoisit_sa_face"] = (
        first and taller.get("ok") is True and taller_area == 300
        and moved.get("ok") is True
        and round(flat.Shape.Area, 3) == 1600
        and spec(flat)["surface"] == plate.Name and spec(flat)["face"] == 0
        # Une face inconnue : refusée, le patron reste.
        and edit(flat, face=9).get("ok") is False
        and round(flat.Shape.Area, 3) == 1600
        and abs(flat.Shape.BoundBox.ZMax) < 1e-6
        and not math.isnan(flat.Shape.Area))


def p131_repetition_variable_rechoisit(self, mark, report, etat):
    mark("p131: une répétition variable re-choisit ses fonctions")
    from engine.kernel import dispatch
    from engine.replay import _temp_bodies_left

    def edit(name, features):
        return dispatch(self, "set_params",
                        {"feature": name, "values": {"features": features}})

    def volume():
        return round(self._require_body().Shape.Volume, 3)

    def repeated(name):
        line = next(f for f in self.get_tree()["features"]
                    if f["name"] == name)
        return (line.get("repeat") or {}).get("features")

    # Un bloc 20×20×10 percé de 8×8, répété trois fois plus haut (10, 20,
    # 30) : 3360 + 336 × 60 = 23520. Sans le perçage, les copies sont
    # pleines : 3360 + 400 × 60 = 27360.
    self.new_part("Répétition variable re-choisie")
    self.add_rect_sketch(20, 20)
    tree = self.add_pad(10)
    pad = next(f["name"] for f in tree["features"]
               if f["type"] == "PartDesign::Pad")
    self.add_rect_sketch(8, 8, face=self._top_face_id())
    tree = self.add_pocket(through=True)
    pocket = next(f["name"] for f in tree["features"]
                  if f["type"] == "PartDesign::Pocket")
    tree = self.add_repeat_feature(
        [pad, pocket],
        [{"offset": [20 * k, 0, 0], "params": {pad: {"Length": 10 * k}}}
         for k in (1, 2, 3)],
        mode="fuse")
    repeat = next(f["name"] for f in tree["features"] if f.get("repeat"))
    holed = volume()
    full = edit(repeat, [pad])
    full_volume = volume()
    full_features = repeated(repeat)
    full_stored = self.get_repeat_feature(repeat)
    back = edit(repeat, [pad, pocket])
    back_volume = volume()
    back_features = repeated(repeat)
    # Des cotes d'instance qui visent une fonction retirée, une zone vide :
    # refusées, la répétition reste.
    orphan = edit(repeat, [pocket])
    empty = edit(repeat, [])
    kept_volume = volume()
    # Une fonction qui vient après la répétition est refusée : elle en
    # dépend, comme toute fonction plus bas dans le corps.
    state = self.sketch_start(plane="XY")
    self.sketch_add_rectangle(state["sketch"], -10, -10, -6, -6)
    self.sketch_finish(state["sketch"])
    self.add_pad(5, sketch=state["sketch"])
    later = self._thin_owner(self._require_body().Tip).Name
    before_later = volume()
    refused = edit(repeat, [pad, pocket, later])
    report["p131_repetition_variable_rechoisit"] = (
        holed == 23520 and full.get("ok") is True
        and full_volume == 27360 and full_features == [pad]
        and full_stored.get("features") == [pad]
        and len(full_stored.get("instances") or []) == 3
        and back.get("ok") is True and back_volume == 23520
        and back_features == [pad, pocket]
        and orphan.get("ok") is False and empty.get("ok") is False
        and kept_volume == 23520 and repeated(repeat) == [pad, pocket]
        and refused.get("ok") is False
        and self._doc.getObject(later).Label in (refused.get("error") or "")
        and volume() == before_later
        and repeated(repeat) == [pad, pocket]
        and sum(1 for f in self.get_tree()["features"]
                if f.get("repeat")) == 1
        and _temp_bodies_left(self) == [])


def p132_surfaces_a_liens_rechoisissent(self, mark, report, etat):
    mark("p132: les surfaces à liens re-choisissent ce qu'elles prennent")
    from engine.kernel import dispatch
    seen = etat.p132 = {}

    def edit(obj, **values):
        return dispatch(self, "set_params",
                        {"feature": obj.Name, "values": values}).get("ok")

    def last(tree):
        return self._doc.getObject(tree["surfaces"][-1]["name"])

    def spec(obj):
        return next(s for s in self.get_tree()["surfaces"]
                    if s["name"] == obj.Name).get("surface")

    def sketch(fill, plane="XY", datum=None):
        name = (self.sketch_start(datum=datum) if datum
                else self.sketch_start(plane=plane))["sketch"]
        fill(name)
        self.sketch_finish(name)
        return name

    def datum(offset):
        tree = self.add_datum_plane(base="XY", offset=offset)
        return [f for f in tree["features"]
                if f["type"] == "PartDesign::Plane"][-1]["name"]

    def zmax(obj):
        return round(obj.Shape.BoundBox.ZMax, 3)

    self.new_part("Surfaces à liens re-choisies")
    mid, high = datum(20), datum(40)

    def ring(r):
        return lambda s: self.sketch_add_circle(s, 0, 0, r)

    # Lissée : deux profils, puis trois, l'ordre gardé ; un seul, ou deux
    # fois le même, refusés.
    a, b, c = sketch(ring(10)), sketch(ring(6), datum=mid), sketch(
        ring(10), datum=high)
    loft = last(self.surface_loft([a, b]))
    seen["loft"] = (spec(loft), zmax(loft),
                    edit(loft, profiles=[a, b, c]), zmax(loft),
                    [p["name"] for p in spec(loft)["profiles"]] == [a, b, c],
                    edit(loft, profiles=[a]), edit(loft, profiles=[a, a]),
                    zmax(loft))
    # Balayée : une autre trajectoire.
    short = sketch(lambda s: self.sketch_add_line(s, 30, 0, 30, 25), "XZ")
    long_ = sketch(lambda s: self.sketch_add_line(s, 30, 0, 30, 45), "XZ")
    disk = sketch(lambda s: self.sketch_add_circle(s, 30, 0, 2))
    sweep = last(self.surface_sweep(disk, short))
    seen["sweep"] = (zmax(sweep), edit(sweep, spine=long_), zmax(sweep),
                     spec(sweep)["spine"]["name"] == long_,
                     edit(sweep, spine=disk), zmax(sweep))
    # Réglée : une autre seconde courbe ; trois courbes refusées.
    low_line = sketch(lambda s: self.sketch_add_line(s, 60, 0, 70, 0))
    mid_line = sketch(lambda s: self.sketch_add_line(s, 60, 0, 70, 0),
                      datum=mid)
    top_line = sketch(lambda s: self.sketch_add_line(s, 60, 0, 70, 0),
                      datum=high)
    ruled = last(self.surface_ruled([{"name": low_line},
                                     {"name": mid_line}]))
    seen["ruled"] = (zmax(ruled),
                     edit(ruled, boundary=[{"name": low_line},
                                           {"name": top_line}]),
                     zmax(ruled), spec(ruled)["boundary"] == [
                         {"name": low_line, "edge": 0},
                         {"name": top_line, "edge": 0}],
                     edit(ruled, boundary=[{"name": low_line},
                                           {"name": mid_line},
                                           {"name": top_line}]),
                     zmax(ruled))
    # Frontière : de deux courbes à deux autres.
    frontier = last(self.surface_boundary([{"name": low_line},
                                           {"name": mid_line}]))
    seen["boundary"] = (zmax(frontier),
                        edit(frontier, boundary=[{"name": mid_line},
                                                 {"name": top_line}]),
                        round(frontier.Shape.BoundBox.ZMin, 3),
                        zmax(frontier))
    # Remplissage : d'un carré à un cercle (une arête fermée : moitiés
    # auxiliaires), puis retour au carré (moitiés défaites).

    def square(x, half):
        return lambda s: self.sketch_add_rectangle(
            s, x - half, -half, x + half, half)

    small = sketch(square(120, 5))
    big = sketch(square(120, 10))
    circle = sketch(lambda s: self.sketch_add_circle(s, 120, 0, 8))
    fill = last(self.surface_fill([{"name": small}]))

    def halves():
        return sum(1 for o in self._doc.Objects
                   if getattr(o, "FreeSolidHalvessource", ""))

    seen["fill"] = (round(fill.Shape.Area, 1),
                    edit(fill, boundary=[{"name": big}]),
                    round(fill.Shape.Area, 1),
                    edit(fill, boundary=[{"name": circle}]), halves(),
                    round(fill.Shape.Area, 1),
                    spec(fill)["boundary"] == [{"name": circle, "edge": 0}],
                    edit(fill, boundary=[{"name": small}]), halves(),
                    round(fill.Shape.Area, 1))
    # Courbe composite : deux arêtes, puis trois ; deux qui ne se suivent
    # pas, refusées.
    chain = sketch(lambda s: (self.sketch_add_line(s, 0, 80, 10, 80),
                              self.sketch_add_line(s, 10, 80, 10, 90),
                              self.sketch_add_line(s, 10, 90, 20, 90)))
    composite = last(self.curve_composite([{"name": chain, "edge": 0},
                                           {"name": chain, "edge": 1}]))
    seen["composite"] = (len(composite.Shape.Edges),
                         edit(composite, boundary=[
                             {"name": chain, "edge": i} for i in range(3)]),
                         len(composite.Shape.Edges),
                         edit(composite, boundary=[
                             {"name": chain, "edge": 0},
                             {"name": chain, "edge": 2}]),
                         len(composite.Shape.Edges))
    # Diviser : un autre trait qui traverse ; un trait à côté, refusé.
    plate = last(self.surface_planar(sketch=sketch(square(200, 20))))
    across = sketch(lambda s: self.sketch_add_line(s, 190, -30, 190, 30))
    other = sketch(lambda s: self.sketch_add_line(s, 210, -30, 210, 30))
    beside = sketch(lambda s: self.sketch_add_line(s, 300, -30, 300, 30))
    split = last(self.surface_split(plate.Name, across))
    seen["split"] = (len(split.Shape.Faces), edit(split, tool=other),
                     sorted(round(f.Area) for f in split.Shape.Faces),
                     spec(split)["tool"] == other,
                     edit(split, tool=beside),
                     sorted(round(f.Area) for f in split.Shape.Faces))
    # Supprimer la face d'une surface : une autre face ; toutes, refusé.
    corner = last(self.surface_extrude(10, sketch=sketch(
        lambda s: (self.sketch_add_line(s, 300, 100, 320, 100),
                   self.sketch_add_line(s, 320, 100, 320, 130)))))
    wide = next(i for i, f in enumerate(corner.Shape.Faces)
                if abs(f.Area - 200) < 1e-6)
    tall = 1 - wide
    removed = last(self.surface_delete_faces(corner.Name, [wide]))
    seen["deleteface"] = (round(removed.Shape.Area),
                          edit(removed, faces=[tall]),
                          round(removed.Shape.Area),
                          spec(removed)["faces"] == [tall],
                          edit(removed, faces=[0, 1]),
                          round(removed.Shape.Area))
    # Annuler l'ajustement : une autre surface.
    untrim = last(self.surface_untrim(plate.Name, 0))
    seen["untrim"] = (round(untrim.Shape.Area),
                      edit(untrim, source=corner.Name, face=tall),
                      round(untrim.Shape.Area),
                      spec(untrim) == {"kind": "untrim",
                                       "source": corner.Name, "face": tall},
                      edit(untrim, face=9), round(untrim.Shape.Area))
    # Bouchon tangent (remplissage figé) : le bout d'un autre tube ; une
    # arête qui ne borde pas de face, refusée.

    def tube(x, r):
        made = last(self.surface_extrude(20, sketch=sketch(
            lambda s: self.sketch_add_circle(s, x, 300, r))))
        top = next(i for i, e in enumerate(made.Shape.Edges)
                   if e.isClosed() and e.BoundBox.ZMin > 19)
        return made, top

    thin, thin_top = tube(0, 5)
    thick, thick_top = tube(40, 8)
    dome = last(self.surface_fill([{"name": thin.Name, "edge": thin_top}],
                                  tangent=True))
    seen["cap"] = (bool(getattr(dome, "FreeSolidCapedges", "")),
                   round(dome.Shape.BoundBox.XMin),
                   edit(dome, boundary=[{"name": thick.Name,
                                         "edge": thick_top}]),
                   round(dome.Shape.BoundBox.XMin),
                   spec(dome)["boundary"] == [{"name": thick.Name,
                                               "edge": thick_top}],
                   edit(dome, boundary=[{"name": circle}]),
                   round(dome.Shape.BoundBox.XMin))
    report["p132_surfaces_a_liens_rechoisissent"] = all((
        seen["cap"] == (True, -5, True, 32, True, False, 32),
        [p["name"] for p in seen["loft"][0]["profiles"]] == [a, b],
        seen["loft"][1] == 20 and seen["loft"][2] is True
        and seen["loft"][3] == 40 and seen["loft"][4]
        and seen["loft"][5] is False and seen["loft"][6] is False
        and seen["loft"][7] == 40,
        seen["sweep"][0] == 25 and seen["sweep"][1] is True
        and seen["sweep"][2] == 45 and seen["sweep"][3]
        and seen["sweep"][4] is False and seen["sweep"][5] == 45,
        seen["ruled"][0] == 20 and seen["ruled"][1] is True
        and seen["ruled"][2] == 40 and seen["ruled"][3]
        and seen["ruled"][4] is False and seen["ruled"][5] == 40,
        seen["boundary"] == (20, True, 20, 40),
        seen["fill"][0] == 100 and seen["fill"][1] is True
        and seen["fill"][2] == 400 and seen["fill"][3] is True
        and seen["fill"][4] == 1 and seen["fill"][6]
        and seen["fill"][7] is True and seen["fill"][8] == 0
        and seen["fill"][9] == 100,
        seen["composite"] == (2, True, 3, False, 3),
        seen["split"][0] == 2 and seen["split"][1] is True
        and seen["split"][2] == [400, 1200] and seen["split"][3]
        and seen["split"][4] is False and seen["split"][5] == [400, 1200],
        seen["deleteface"] == (300, True, 200, True, False, 200),
        seen["untrim"][1] is True and seen["untrim"][2] == 300
        and seen["untrim"][3] and seen["untrim"][4] is False
        and seen["untrim"][5] == 300,
    ))


def p133_formes_figees_rechoisissent(self, mark, report, etat):
    mark("p133: les formes figées re-choisissent ce qu'elles prennent")
    from engine.kernel import dispatch
    seen = etat.p133 = {}

    def edit(name, **values):
        return dispatch(self, "set_params",
                        {"feature": name, "values": values}).get("ok")

    def last(tree):
        return self._doc.getObject(tree["surfaces"][-1]["name"])

    def sketch(fill, plane="XY", datum=None):
        name = (self.sketch_start(datum=datum) if datum
                else self.sketch_start(plane=plane))["sketch"]
        fill(name)
        self.sketch_finish(name)
        return name

    def volume():
        return round(self._require_body().Shape.Volume, 3)

    # Supprimer la face : un bloc 40×40×10, un bossage 10×10×10 dans un
    # coin, un trou 8×8 au centre. Le trou bouché (un ajout), puis le
    # bossage retiré (une intersection), puis les deux (ajout et
    # intersection), puis le trou seul de nouveau.
    self.new_part("Formes figées re-choisies")
    self.add_rect_sketch(40, 40)
    self.add_pad(10)
    boss = sketch(lambda s: self.sketch_add_rectangle(s, 10, 10, 20, 20))
    self.add_pad(20, sketch=boss)
    self.add_rect_sketch(8, 8, face=self._top_face_id())
    self.add_pocket(through=True)
    shape = self._require_body().Shape

    def faces_where(test):
        return [i for i, f in enumerate(shape.Faces) if test(f.BoundBox)]

    hole = faces_where(lambda b: b.XMax < 4.01 and b.XMin > -4.01
                       and b.YMax < 4.01 and b.YMin > -4.01
                       and b.ZLength > 1)
    bump = faces_where(lambda b: b.XMin > 9.99 and b.YMin > 9.99
                       and b.ZMax > 10.01)
    holed = volume()
    tree = self.add_delete_face(hole)
    owner = next(f["name"] for f in tree["features"] if f.get("delete_face"))
    obj = self._doc.getObject(owner)

    def helpers():
        return [o.Name for o in self._require_body().Group
                if getattr(o, "FreeSolidThinOwner", "") == owner]

    seen["delete"] = (holed, volume(), obj.Type, edit(owner, faces=bump),
                      volume(), obj.Type, helpers(),
                      edit(owner, faces=hole + bump), volume(), obj.Type,
                      len(helpers()), edit(owner, faces=hole), volume(),
                      len(helpers()), edit(owner, faces=[]), volume(),
                      next(f for f in self.get_tree()["features"]
                           if f["name"] == owner)["delete_face"]["faces"]
                      == sorted(hole))
    seen["delete_clean"] = not any(f["error"]
                                   for f in self.get_tree()["features"])
    # Remplacer la face : un bloc 20×20×10 dont le dessus monte à une
    # surface plane à 15, puis descend à une autre à 5.
    self.new_part("Face remplacée re-choisie")
    self.add_rect_sketch(20, 20)
    self.add_pad(10)
    top = self._top_face_id()
    planes = []
    for z in (15, 5):
        tree = self.add_datum_plane(base="XY", offset=z)
        datum = [f for f in tree["features"]
                 if f["type"] == "PartDesign::Plane"][-1]["name"]
        square = sketch(lambda s: self.sketch_add_rectangle(
            s, -30, -30, 30, 30), datum=datum)
        planes.append(last(self.surface_planar(sketch=square)).Name)
    face = int(str(top).rsplit("Face", 1)[-1]) - 1 if isinstance(
        top, str) else int(top)
    tree = self.add_replace_face(face, planes[0])
    owner2 = next(f["name"] for f in tree["features"]
                  if f.get("replace_face"))
    seen["replace"] = (volume(), self._doc.getObject(owner2).Type,
                       edit(owner2, surface=planes[1]), volume(),
                       self._doc.getObject(owner2).Type,
                       next(f for f in self.get_tree()["features"]
                            if f["name"] == owner2)["replace_face"]
                       ["surface"] == planes[1])
    # Couture : deux bandes qui se touchent, puis deux autres.

    def band(x1, y1, x2, y2):
        return last(self.surface_extrude(10, sketch=sketch(
            lambda s: self.sketch_add_line(s, x1, y1, x2, y2)))).Name

    a, b, c = (band(100, 0, 110, 0), band(110, 0, 110, 10),
               band(100, 0, 100, 20))
    sewn = last(self.surface_sew([a, b]))
    seen["sew"] = (round(sewn.Shape.Area), edit(sewn.Name, surfaces=[a, c]),
                   round(sewn.Shape.Area), sewn.FreeSolidSources,
                   edit(sewn.Name, surfaces=[a]), round(sewn.Shape.Area))
    # Médiane d'un bloc 40×40×10 (mis à part) : dessus et dessous, puis
    # gauche et droite, puis les parois plus minces que 15.
    self.new_part("Médiane re-choisie")
    self.add_rect_sketch(40, 40)
    self.add_pad(10)
    block = self._require_body().Shape
    tops = [i for i, f in enumerate(block.Faces)
            if f.BoundBox.ZLength < 1e-6]
    sides = [i for i, f in enumerate(block.Faces)
             if f.BoundBox.XLength < 1e-6]
    mid = last(self.surface_mid(faces=tops))
    seen["mid"] = (round(mid.Shape.Area), edit(mid.Name, faces=sides),
                   round(mid.Shape.Area), edit(mid.Name, thickness=15),
                   round(mid.Shape.Area), edit(mid.Name, faces=tops[:1]),
                   round(mid.Shape.Area))
    report["p133_formes_figees_rechoisissent"] = all((
        seen["delete"][:3] == (16360.0, 17000.0, "Fuse"),
        seen["delete"][3:7] == (True, 15360.0, "Common", []),
        seen["delete"][7:11] == (True, 16000.0, "Common", 1),
        seen["delete"][11:14] == (True, 17000.0, 1),
        seen["delete"][14:] == (False, 17000.0, True),
        seen["delete_clean"],
        seen["replace"] == (6000.0, "Fuse", True, 2000.0, "Common", True),
        seen["sew"][0] == 200 and seen["sew"][1] is True
        and seen["sew"][2] == 300 and seen["sew"][3] == ";".join((a, c))
        and seen["sew"][4] is False and seen["sew"][5] == 300,
        seen["mid"] == (1600, True, 400, True, 1600, False, 1600),
    ))


def p134_references_rechoisissent(self, mark, report, etat):
    mark("p134: plan, axe, point et repère re-choisissent ce qui les porte")
    from engine.kernel import dispatch
    seen = etat.p134 = {}

    def edit(name, **values):
        return dispatch(self, "set_params",
                        {"feature": name, "values": values}).get("ok")

    def spec(name):
        return next(f for f in self.get_tree()["features"]
                    if f["name"] == name).get("reference")

    def volume():
        return round(self._require_body().Shape.Volume, 3)

    def newest(tree, type_id):
        return [f["name"] for f in tree["features"]
                if f["type"] == type_id][-1]

    # Un bloc 40×40×10 percé d'un trou de rayon 5 ; un plan sur le dessus,
    # un bossage 10×10×5 esquissé sur ce plan.
    self.new_part("Références re-choisies")
    base = self.sketch_start(plane="XY")["sketch"]
    self.sketch_add_rectangle(base, -20, -20, 20, 20)
    self.sketch_add_circle(base, 0, 0, 5)
    self.sketch_finish(base)
    pad = self.add_pad(10, sketch=base)["features"][-1]["name"]
    block = self._doc.getObject(pad).Shape
    top = next(i for i, f in enumerate(block.Faces)
               if f.BoundBox.ZMin > 9.99 and f.BoundBox.ZLength < 1e-6)
    bottom = next(i for i, f in enumerate(block.Faces)
                  if f.BoundBox.ZMax < 1e-6 and f.BoundBox.ZLength < 1e-6)
    plane = newest(self.add_datum_plane(face=top, offset=0),
                   "PartDesign::Plane")
    boss = self.sketch_start(datum=plane)["sketch"]
    self.sketch_add_rectangle(boss, 10, 10, 20, 20)
    self.sketch_finish(boss)
    self.add_pad(5, sketch=boss)
    boss_pad = self._require_body().Tip
    seen["plane_spec"] = spec(plane) == {"kind": "plane", "face": top,
                                         "offset": 0.0, "angle": 0.0}
    # La vue au rang du plan : la pièce d'avant lui, sans le bossage.
    self.rank_view(plane)
    seen["rank"] = self._require_body().Tip.Name == pad
    self.rank_view_end()
    seen["rank_back"] = self._require_body().Tip.Name == boss_pad.Name
    full = volume()
    # Le plan s'enfonce de 2 : le bossage avec lui. Puis le plan d'origine
    # XY décalé de 10 (le dessus), puis la face de dessous.
    seen["offset"] = (full, edit(plane, offset=-2), volume(),
                      spec(plane)["offset"])
    seen["base"] = (edit(plane, base="XY", offset=10), volume(),
                    spec(plane).get("base"))
    seen["face"] = (edit(plane, face=bottom, offset=0), volume(),
                    round(boss_pad.Shape.BoundBox.ZMin, 6),
                    spec(plane).get("face") == bottom)
    # Aperçu : où le plan se poserait ; la pièce ne change pas.
    undo = self._doc.UndoCount
    preview = dispatch(self, "preview", {"op": "set_params", "params": {
        "feature": plane, "values": {"offset": 3, "angle": 30}}})
    matrix = (preview.get("result") or {}).get("plane") or []
    seen["preview"] = (len(matrix) == 16, self._doc.UndoCount == undo,
                       spec(plane)["offset"] == 0.0)
    # Refusés, la pièce restant telle quelle : une face inconnue, une clé
    # d'ailleurs, un plan d'origine inconnu.
    seen["refused"] = (edit(plane, face=999), edit(plane, Length=5),
                       edit(plane, base="AB", offset=4), volume(),
                       spec(plane).get("face") == bottom
                       and spec(plane)["offset"] == 0.0)
    seen["angle"] = (edit(plane, angle=30), spec(plane)["angle"])
    edit(plane, angle=0)
    # Les arêtes de la pièce au rang des références qui suivent : le
    # bossage, dernière fonction avant elles.
    solid = self._require_body().Tip.Shape
    straight = next(i for i, e in enumerate(solid.Edges)
                    if e.Curve.TypeId == "Part::GeomLine")
    circle = next(i for i, e in enumerate(solid.Edges)
                  if e.Curve.TypeId == "Part::GeomCircle"
                  and e.BoundBox.ZMin > 9.99)
    # Axe : une arête droite, puis le trou (son axe), puis l'axe X.
    axis = newest(self.add_datum_axis(edge=straight), "PartDesign::Line")
    line = self._doc.getObject(axis)
    seen["axis"] = (spec(axis) == {"kind": "axis", "edge": straight},
                    edit(axis, edge=circle), line.MapMode,
                    spec(axis) == {"kind": "axis", "edge": circle},
                    [round(c, 6) for c in line.Placement.Base][:2],
                    edit(axis, axis="X"), spec(axis))
    # Point : un coin, puis le centre du trou, puis des coordonnées ; une
    # arête droite n'a pas de centre.
    point = newest(self.add_datum_point(vertex=[20, 20, 10]),
                   "PartDesign::Point")
    dot = self._doc.getObject(point)
    seen["point"] = (spec(point) == {"kind": "point",
                                     "vertex": [20.0, 20.0, 10.0]},
                     edit(point, edge=circle), dot.MapMode,
                     [round(c, 6) for c in dot.Placement.Base],
                     edit(point, edge=straight), dot.MapMode,
                     edit(point, point=[4, 5, 6]), dot.MapMode,
                     spec(point))
    # Repère : des coordonnées, puis un coin.
    frame = newest(self.add_datum_cs(point=[1, 2, 3]),
                   "PartDesign::CoordinateSystem")
    cs = self._doc.getObject(frame)
    seen["cs"] = (spec(frame), edit(frame, vertex=[-20, -20, 0]), cs.MapMode,
                  [round(c, 6) for c in cs.Placement.Base], spec(frame))
    seen["clean"] = not any(f["error"] for f in self.get_tree()["features"])
    report["p134_references_rechoisissent"] = all((
        seen["plane_spec"], seen["rank"], seen["rank_back"],
        seen["offset"][1:] == (True, round(full - 200, 3), -2.0),
        seen["base"] == (True, full, "XY"),
        seen["face"][:3] == (True, full, -5.0) and seen["face"][3],
        seen["preview"] == (True, True, True),
        seen["refused"] == (False, False, False, full, True),
        seen["angle"] == (True, 30.0),
        seen["axis"] == (True, True, "AxisOfCurvature", True, [0.0, 0.0],
                         True, {"kind": "axis", "axis": "X"}),
        seen["point"][:4] == (True, True, "CenterOfCurvature",
                              [0.0, 0.0, 10.0])
        and seen["point"][4:] == (False, "CenterOfCurvature", True,
                                  "Deactivated",
                                  {"kind": "point", "point": [4.0, 5.0, 6.0]}),
        seen["cs"] == ({"kind": "cs", "point": [1.0, 2.0, 3.0]}, True,
                       "Translate", [-20.0, -20.0, 0.0],
                       {"kind": "cs", "vertex": [-20.0, -20.0, 0.0]}),
        seen["clean"],
    ))


def p135_apercu_des_surfaces_a_la_creation(self, mark, report, etat):
    mark("p135: surfaces, courbes et références ont leur aperçu à la création")
    from engine.kernel import dispatch
    seen = etat.p135 = {}

    def last(tree):
        return tree["surfaces"][-1]["name"]

    def sketch(fill, plane="XY", datum=None):
        name = (self.sketch_start(datum=datum) if datum
                else self.sketch_start(plane=plane))["sketch"]
        fill(name)
        self.sketch_finish(name)
        return name

    def line(x1, y1, x2, y2, **where):
        return sketch(lambda s: self.sketch_add_line(s, x1, y1, x2, y2),
                      **where)

    def circle(cx, cy, r, **where):
        return sketch(lambda s: self.sketch_add_circle(s, cx, cy, r), **where)

    def square(x, half, **where):
        return sketch(lambda s: self.sketch_add_rectangle(
            s, x - half, -half, x + half, half), **where)

    def preview(op, **params):
        """(accepté, quelque chose à montrer, pièce inchangée)."""
        doc = self._doc
        count, undo = len(doc.Objects), doc.UndoCount
        answer = dispatch(self, "preview", {"op": op, "params": params})
        result = answer.get("result") or {}
        shown = (bool(result.get("indices"))
                 or bool((result.get("lines") or {}).get("positions"))
                 or "reference" in result)
        seen[op] = (answer.get("ok"), shown, len(doc.Objects) == count
                    and doc.UndoCount == undo, answer.get("error"))

    self.new_part("Aperçus à la création")
    high = [f for f in self.add_datum_plane(base="XY", offset=20)["features"]
            if f["type"] == "PartDesign::Plane"][-1]["name"]
    low_plane = [f for f in self.add_datum_plane(base="XY", offset=-5)[
        "features"] if f["type"] == "PartDesign::Plane"][-1]["name"]
    plate = last(self.surface_planar(sketch=square(0, 20)))
    band = last(self.surface_extrude(10, sketch=line(
        0, -30, 0, 30, datum=low_plane)))
    preview("surface_extrude", length=10, sketch=line(-20, 30, 20, 30))
    preview("surface_revolve", angle=180, sketch=line(105, 0, 105, 10))
    preview("surface_loft", sketches=[circle(200, 0, 10),
                                      circle(200, 0, 6, datum=high)])
    outline = square(300, 10)
    preview("surface_planar", sketch=outline)
    preview("surface_radiate", boundary=[{"name": outline}], distance=5)
    spine = line(400, 0, 400, 20, plane="XZ")
    preview("surface_sweep", profile=circle(400, 0, 2), spine=spine)
    preview("surface_offset", surface=plate, distance=3)
    preview("surface_thicken", surface=plate, thickness=2)
    preview("surface_fill", boundary=[{"name": circle(500, 0, 8)}])
    lower, upper = line(600, 0, 610, 0), line(600, 0, 610, 0, datum=high)
    preview("surface_ruled", boundary=[{"name": lower}, {"name": upper}])
    preview("surface_boundary", boundary=[{"name": lower}, {"name": upper}])
    chain = sketch(lambda s: (self.sketch_add_line(s, 700, 0, 710, 0),
                              self.sketch_add_line(s, 710, 0, 710, 10)))
    preview("curve_composite", boundary=[{"name": chain, "edge": 0},
                                         {"name": chain, "edge": 1}])
    preview("surface_split", surface=plate, tool=line(0, -30, 0, 30))
    preview("surface_untrim", surface=plate)
    preview("surface_extend", surface=plate, distance=5)
    preview("surface_trim", surface=plate, tool=band, point=[10, 0, 0])
    preview("surface_flatten", surface=plate)
    preview("surface_freeform", surface=plate, radius=15, point=[0, 0, 0],
            height=5)
    preview("curve_intersection", first=plate, second=band)
    preview("curve_project", sketch=circle(0, 0, 5, datum=high),
            surface=plate)
    preview("curve_helix", pitch=5, height=20, radius=10)
    # Couture de deux bandes en équerre, puis son congé et ses faces.
    left = last(self.surface_extrude(10, sketch=line(800, 0, 810, 0)))
    right = last(self.surface_extrude(10, sketch=line(810, 0, 810, 10)))
    preview("surface_sew", surfaces=[left, right])
    sewn = last(self.surface_sew([left, right]))
    shape = self._doc.getObject(sewn).Shape
    shared = [i for i, edge in enumerate(shape.Edges)
              if sum(any(e.isSame(edge) for e in face.Edges)
                     for face in shape.Faces) == 2]
    preview("surface_fillet", surface=sewn, edges=shared[:1], radius=2)
    preview("surface_delete_faces", surface=sewn, faces=[0])
    # Axe, point, repère : où ils se posent.
    preview("add_datum_axis", axis="X")
    preview("add_datum_point", point=[1, 2, 3])
    preview("add_datum_cs", point=[1, 2, 3])
    failed = {op: value for op, value in seen.items()
              if value[:3] != (True, True, True)}
    seen["failed"] = failed
    # La flèche d'une surface extrudée qu'on réédite : au bout de la bande
    # (esquisse à −5, longueur 10), le long de la normale de l'esquisse.
    drag = self.feature_drag_info(band)["drag"] or {}
    seen["drag"] = (drag.get("key"), drag.get("value"),
                    [round(c, 6) for c in drag.get("normal", [])],
                    round(drag.get("point", [0, 0, 0])[2], 6))
    report["p135_apercu_des_surfaces_a_la_creation"] = (
        len(seen) == 29 and not failed
        and seen["drag"] == ("length", 10.0, [0.0, 0.0, 1.0], 5.0))


def p136_fleches_percage_helice(self, mark, report, etat):
    mark("p136: flèches de profondeur du perçage et de l'hélice volume")
    seen = etat.p136 = {}

    def rounded(values):
        return [round(c, 6) for c in values]

    self.new_part("Flèches perçage et hélice")
    self.add_rect_sketch(40, 40)
    self.add_pad(10)
    body = self._require_body()
    top = next(i for i, f in enumerate(body.Shape.Faces)
               if abs(f.CenterOfMass.z - 10) < 1e-6)
    frame = self.face_frame(top)
    seen["face"] = (rounded(frame["normal"]), round(frame["center"][2], 6))
    tree = self.add_hole(6, depth=5, face=top, points=[[5, 5, 10]])
    hole = next(f["name"] for f in tree["features"]
                if f["type"] == "PartDesign::Hole")
    drag = self.feature_drag_info(hole)["drag"] or {}
    seen["hole"] = (drag.get("key"), drag.get("value"),
                    rounded(drag.get("normal", [])),
                    rounded(drag.get("point", [0, 0, 0])), drag.get("factor"))
    # Traversant : pas de flèche.
    through = self.add_hole(3, through=True, face=top, points=[[-5, -5, 10]])
    thru = [f["name"] for f in through["features"]
            if f["type"] == "PartDesign::Hole"][-1]
    seen["through"] = self.feature_drag_info(thru)["drag"]
    # Hélice : l'axe vertical de l'esquisse (XZ → Z).
    self.new_part("Flèche hélice")
    sk = self.sketch_start(plane="XZ")["sketch"]
    self.sketch_add_circle(sk, 15, 0, 2)
    self.sketch_finish(sk)
    seen["frame"] = rounded(self.sketch_frame(sk)["vaxis"])
    tree = self.add_helix(pitch=8, height=40, sketch=sk)
    helix = next(f["name"] for f in tree["features"]
                 if f["type"] == "PartDesign::AdditiveHelix")
    drag = self.feature_drag_info(helix)["drag"] or {}
    top_z = self._doc.getObject(helix).Shape.BoundBox.ZMax
    seen["helix"] = (drag.get("key"), drag.get("value"),
                     rounded(drag.get("normal", [])),
                     round(drag.get("point", [0, 0, 0])[2], 6),
                     top_z > 35)
    report["p136_fleches_percage_helice"] = (
        seen["face"] == ([0.0, 0.0, 1.0], 10.0)
        and seen["hole"] == ("depth", 5.0, [0.0, 0.0, -1.0],
                             [5.0, 5.0, 5.0], 1.0)
        and seen["through"] is None
        and seen["helix"] == ("height", 40.0, [0.0, 0.0, 1.0], 40.0, True))
    # Hélice conique : l'angle se donne à la création, comme à la
    # réédition ; hors de ]-90°, 90°[ il est refusé.
    from engine.kernel import dispatch
    self.new_part("Hélice conique")
    sk = self.sketch_start(plane="XZ")["sketch"]
    self.sketch_add_circle(sk, 15, 0, 2)
    self.sketch_finish(sk)
    refused = dispatch(self, "add_helix", {"pitch": 8, "height": 40,
                                           "angle": 90, "sketch": sk})
    seen["cone_refused"] = not refused.get("ok")
    tree = dispatch(self, "add_helix", {"pitch": 8, "height": 40,
                                        "angle": 15, "sketch": sk}
                    ).get("result") or {"features": []}
    cone = self._doc.getObject(next(
        f["name"] for f in tree["features"]
        if f["type"] == "PartDesign::AdditiveHelix"))
    box = cone.Shape.BoundBox
    seen["cone"] = (round(float(cone.Angle), 6),
                    next((e["value"] for e in self.get_params(cone.Name)
                          ["params"] if e["key"] == "angle"), None),
                    box.XMax > 17 + 30 * 0.2)
    report["p136_helice_conique"] = (
        seen["cone_refused"]
        and seen["cone"][0] == 15.0 and seen["cone"][1] == 15.0
        and seen["cone"][2])


def p137_barre_et_references(self, mark, report, etat):
    mark("p137: plan et axe de référence reculent avec la barre de retour")
    from engine.kernel import dispatch
    seen = etat.p137 = {}

    def call(op, **params):
        return dispatch(self, op, params)

    def rolled(*names):
        rows = {f["name"]: f for f in self.get_tree()["features"]}
        return [bool(rows[n].get("rolled_back")) for n in names]

    def tip():
        return getattr(self._require_body().Tip, "Name", None)

    # Bloc, esquisse libre, plan sur le dessus, axe Z, bossage sur le plan.
    self.new_part("Barre et références")
    base = self.sketch_start(plane="XY")["sketch"]
    self.sketch_add_rectangle(base, -20, -20, 20, 20)
    self.sketch_finish(base)
    pad = self.add_pad(10, sketch=base)["features"][-1]["name"]
    free = self.sketch_start(plane="XZ")["sketch"]
    self.sketch_add_line(free, 0, 0, 10, 10)
    self.sketch_finish(free)
    top = next(i for i, f in enumerate(self._doc.getObject(pad).Shape.Faces)
               if f.BoundBox.ZMin > 9.99 and f.BoundBox.ZLength < 1e-6)
    plane = [f["name"] for f in self.add_datum_plane(face=top)["features"]
             if f["type"] == "PartDesign::Plane"][-1]
    axis = [f["name"] for f in self.add_datum_axis(axis="Z")["features"]
            if f["type"] == "PartDesign::Line"][-1]
    boss = self.sketch_start(datum=plane)["sketch"]
    self.sketch_add_rectangle(boss, 5, 5, 15, 15)
    self.sketch_finish(boss)
    self.add_pad(5, sketch=boss)
    boss_pad = tip()
    # Barre en tête : tout recule, les références aussi, et la vue ne les
    # dessine plus.
    call("set_tip")
    seen["top"] = (rolled(plane, axis),
                   self._doc.getObject(plane).Visibility)
    # Sous le bloc : une esquisse ne se pose pas sur le plan reculé.
    call("set_tip", feature=pad)
    refused = call("sketch_start", datum=plane)
    seen["sketch_refused"] = (rolled(plane, axis), refused.get("ok"),
                              "barre" in str(refused.get("error")))
    # La barre se pose sur une référence : ce qui suit recule.
    seen["on_plane"] = (call("set_tip", feature=plane).get("ok"),
                        rolled(plane, axis), tip() == pad)
    seen["on_axis"] = (call("set_tip", feature=axis).get("ok"),
                       rolled(plane, axis), tip() == pad)
    call("tip_to_end")
    seen["end"] = (rolled(plane, axis), tip() == boss_pad)
    # La vue au rang de l'axe : le plan reste, l'axe recule ; puis retour.
    self.rank_view(axis)
    seen["rank"] = (rolled(plane, axis), tip() == pad)
    self.rank_view_end()
    seen["rank_back"] = (rolled(plane, axis), tip() == boss_pad)
    # L'esquisse libre précède le plan : elle ne s'y pose pas.
    moved = call("sketch_set_plane", sketch=free, datum=plane)
    seen["set_plane_refused"] = (moved.get("ok"),
                                 "après" in str(moved.get("error")))
    # Supprimer ce qui est sous la barre posée sur le plan : l'axe part
    # avec le bossage ; l'annulation les rend.
    call("set_tip", feature=plane)
    call("delete_rolled_back")
    gone = (self._doc.getObject(axis) is None,
            self._doc.getObject(boss_pad) is None,
            self._doc.getObject(plane) is not None)
    call("undo")
    call("tip_to_end")
    seen["deleted"] = (gone, self._doc.getObject(axis) is not None,
                       tip() == boss_pad)
    report["p137_barre_et_references"] = (
        seen["top"] == ([True, True], False)
        and seen["sketch_refused"] == ([True, True], False, True)
        and seen["on_plane"] == (True, [False, True], True)
        and seen["on_axis"] == (True, [False, False], True)
        and seen["end"] == ([False, False], True)
        and seen["rank"] == ([False, True], True)
        and seen["rank_back"] == ([False, False], True)
        and seen["set_plane_refused"] == (False, True)
        and seen["deleted"] == ((True, True, True), True, True))


def p138_formes_figees_et_barre(self, mark, report, etat):
    mark("p138: une fonction glissée sous la barre entre dans les formes "
         "figées d'après")
    from engine.kernel import dispatch
    seen = etat.p138 = {}

    def call(op, **params):
        return dispatch(self, op, params)

    def volume():
        return round(self._require_body().Shape.Volume, 3)

    def block(x1, y1, x2, y2, height, hole=None):
        sk = self.sketch_start(plane="XY")["sketch"]
        self.sketch_add_rectangle(sk, x1, y1, x2, y2)
        if hole:
            self.sketch_add_circle(sk, 0, 0, hole)
        self.sketch_finish(sk)
        self.add_pad(height, sketch=sk)
        return self._require_body().Tip.Name

    # Chanfrein de sommet, puis la barre sous le bloc : un plot de 5×5×5
    # posé alors dépasse au-dessus, il reste quand la barre revient.
    self.new_part("Formes figées et barre")
    pad = block(0, 0, 20, 20, 10)
    self.add_vertex_chamfer([3, 3, 3], point=[20, 20, 10])
    corner = self._require_body().Tip
    chamfered = volume()
    call("set_tip", feature=pad)
    block(0, 0, 5, 5, 15)
    call("tip_to_end")
    seen["vertex"] = (chamfered, volume(),
                      corner.FreeSolidVchamferspec.split(";")[1:])
    # Supprimer la face : le trou rebouché ; une poche posée sous la barre
    # reste creusée, la face suit son nouveau numéro.
    self.new_part("Formes figées et barre, face")
    pad = block(-20, -20, 20, 20, 10, hole=4)
    faces = self._doc.getObject(pad).Shape.Faces
    hole = next(i for i, f in enumerate(faces)
                if f.Surface.TypeId == "Part::GeomCylinder")
    top = next(i for i, f in enumerate(faces)
               if f.BoundBox.ZMin > 9.99 and f.BoundBox.ZLength < 1e-6)
    self.add_delete_face([hole])
    deleted = self._require_body().Tip
    filled = volume()
    call("set_tip", feature=pad)
    sk = self.sketch_start(face=top)["sketch"]
    self.sketch_add_rectangle(sk, 10, 10, 15, 15)
    self.sketch_finish(sk)
    self.add_pocket(sketch=sk, length=5)
    call("tip_to_end")
    # La forme part de la poche ; la face retirée y est encore le trou.
    frozen = self._frozen_steps(deleted)[0][1]
    start = self._doc.getObject(frozen.FreeSolidDefeatbase)
    face = start.Shape.Faces[int(deleted.FreeSolidDeletefaces)]
    seen["face"] = (filled, volume(), start.Name != pad,
                    face.Surface.TypeId == "Part::GeomCylinder")
    # Une couture suit sa surface rééditée sous la barre.
    self.new_part("Formes figées et barre, couture")

    def band(x1, y1, x2, y2):
        sk = self.sketch_start(plane="XY")["sketch"]
        self.sketch_add_line(sk, x1, y1, x2, y2)
        self.sketch_finish(sk)
        return self.surface_extrude(10, sketch=sk)["surfaces"][-1]["name"]

    first, second = band(0, 0, 10, 0), band(10, 0, 10, 10)
    sewn = self.surface_sew([first, second])["surfaces"][-1]["name"]
    call("set_tip", feature=first)
    call("set_params", feature=first, values={"length": 20})
    call("tip_to_end")
    seen["sew"] = round(self._doc.getObject(sewn).Shape.Area, 3)
    report["p138_formes_figees_et_barre"] = (
        seen["vertex"] == (3995.5, 4120.5, ["3", "3", "3"])
        and seen["face"] == (16000.0, 15875.0, True, True)
        and seen["sew"] == 300.0)


def p140_desactiver_emporte_les_enfants(self, mark, report, etat):
    mark("p140: désactiver emporte ce qui s'appuie dessus")
    from engine.kernel import dispatch
    seen = etat.p140 = {}

    def call(op, **params):
        return dispatch(self, op, params)

    def off(*names):
        tree = self.get_tree()
        rows = {}
        stack = list(tree["features"]) + list(tree["surfaces"])
        while stack:
            row = stack.pop()
            rows.setdefault(row["name"], row)
            stack.extend(row.get("children") or ())
        return [bool(rows[n].get("suppressed")) for n in names]

    def volume():
        return round(self._require_body().Shape.Volume, 3)

    # Bloc, plan sur son dessus, esquisse sur le plan, bossage.
    self.new_part("Désactiver et enfants")
    base = self.sketch_start(plane="XY")["sketch"]
    self.sketch_add_rectangle(base, -20, -20, 20, 20)
    self.sketch_finish(base)
    pad = self.add_pad(10, sketch=base)["features"][-1]["name"]
    top = next(i for i, f in enumerate(self._doc.getObject(pad).Shape.Faces)
               if f.BoundBox.ZMin > 9.99 and f.BoundBox.ZLength < 1e-6)
    plane = [f["name"] for f in self.add_datum_plane(face=top)["features"]
             if f["type"] == "PartDesign::Plane"][-1]
    boss_sk = self.sketch_start(datum=plane)["sketch"]
    self.sketch_add_rectangle(boss_sk, 5, 5, 15, 15)
    self.sketch_finish(boss_sk)
    self.add_pad(5, sketch=boss_sk)
    boss = self._require_body().Tip.Name
    full = volume()
    # Le plan : l'esquisse et le bossage partent avec lui.
    call("set_suppressed", features=[plane], suppressed=True)
    seen["plane"] = (off(plane, boss_sk, boss, pad), volume())
    alone = call("set_suppressed", features=[boss], suppressed=False)
    seen["alone"] = (alone.get("ok"), "réactivez" in str(alone.get("error")))
    on_plane = call("sketch_start", datum=plane)
    seen["sketch_on_off"] = on_plane.get("ok")
    call("set_suppressed", features=[plane], suppressed=False)
    seen["back"] = (off(plane, boss_sk, boss), volume() == full)
    # Le bloc : le plan posé sur sa face, puis tout ce qui suit.
    call("set_suppressed", features=[pad], suppressed=True)
    seen["pad"] = off(pad, plane, boss_sk, boss)
    call("set_suppressed", features=[pad], suppressed=False)
    seen["pad_back"] = (off(pad, plane, boss_sk, boss), volume() == full,
                        self.rebuild_errors()["errors"] == [])
    # Un congé sur l'arête d'un trou part avec le trou ; un bossage
    # d'après qui ne prend rien au trou reste.
    self.new_part("Désactiver un trou")
    sk = self.sketch_start(plane="XY")["sketch"]
    self.sketch_add_rectangle(sk, -20, -20, 20, 20)
    self.sketch_finish(sk)
    self.add_pad(10, sketch=sk)
    hole_sk = self.sketch_start(plane="XY")["sketch"]
    self.sketch_add_circle(hole_sk, 0, 0, 4)
    self.sketch_finish(hole_sk)
    # L'esquisse est sous le bloc : l'enlèvement part vers le haut.
    self.add_pocket(through=True, reversed=True, sketch=hole_sk)
    hole = self._require_body().Tip.Name
    rim = next(i for i, e in enumerate(self._require_body().Shape.Edges)
               if e.Curve.TypeId == "Part::GeomCircle"
               and e.BoundBox.ZMin > 9.99)
    self.add_fillet(1, edges=[rim])
    fillet = self._require_body().Tip.Name
    post_sk = self.sketch_start(plane="XY")["sketch"]
    self.sketch_add_rectangle(post_sk, 10, 10, 18, 18)
    self.sketch_finish(post_sk)
    self.add_pad(15, sketch=post_sk)
    post = self._require_body().Tip.Name
    call("set_suppressed", features=[hole], suppressed=True)
    seen["hole"] = (off(hole, fillet, post),
                    self.rebuild_errors()["errors"] == [])
    call("set_suppressed", features=[hole], suppressed=False)
    seen["hole_back"] = (off(hole, fillet, post),
                         self.rebuild_errors()["errors"] == [])
    # Surfaces : la décalée part avec sa source, pas l'inverse ; la vue
    # ne dessine plus une surface désactivée.
    self.new_part("Désactiver une surface")
    square = self.sketch_start(plane="XY")["sketch"]
    self.sketch_add_rectangle(square, 0, 0, 40, 40)
    self.sketch_finish(square)
    flat = self.surface_planar(sketch=square)["surfaces"][-1]["name"]
    offset = self.surface_offset(flat, 10)["surfaces"][-1]["name"]
    call("set_suppressed", features=[offset], suppressed=True)
    seen["offset"] = (off(flat, offset),
                      len(self.tessellate().get("surfaces") or []))
    call("set_suppressed", features=[offset], suppressed=False)
    call("set_suppressed", features=[flat], suppressed=True)
    seen["flat"] = (off(flat, offset),
                    len(self.tessellate().get("surfaces") or []))
    call("set_suppressed", features=[flat], suppressed=False)
    seen["flat_back"] = (off(flat, offset),
                         len(self.tessellate().get("surfaces") or []))
    report["p140_desactiver_emporte_les_enfants"] = (
        seen["plane"][0] == [True, True, True, False]
        and seen["plane"][1] < full
        and seen["alone"] == (False, True)
        and seen["sketch_on_off"] is False
        and seen["back"] == ([False, False, False], True)
        and seen["pad"] == [True, True, True, True]
        and seen["pad_back"] == ([False, False, False, False], True, True)
        and seen["hole"] == ([True, True, False], True)
        and seen["hole_back"] == ([False, False, False], True)
        and seen["offset"] == ([False, True], 1)
        and seen["flat"] == ([True, True], 0)
        and seen["flat_back"] == ([False, False], 2))
