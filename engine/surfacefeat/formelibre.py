"""Mise à plat et forme libre : points de contrôle, déplacements,
poussées.

Sous-mixin de ``SurfaceMixin`` (voir ``__init__.py``). Pas d'import
FreeCAD au niveau du module : les méthodes importent le noyau à l'appel.
"""


class SurfaceFreeformMixin:
    def surface_flatten(self, surface, face=0):
        """Aplatir une face de surface : son patron à plat (déroulé par
        moindres carrés conformes), posé sur le plan de dessus à côté de la
        pièce — gabarit de découpe, développé de tôle mince."""
        src = self._get_surface(surface)
        shape = self._flat_shape(src.Shape, int(face))
        anchor = self._face_anchor(self._source_face(src.Shape, int(face)))
        stamps = {"flatsource": src.Name, "flatface": int(face),
                  "flatanchor": "%.9g,%.9g,%.9g" % (anchor.x, anchor.y,
                                                    anchor.z)}
        return self._add_frozen_surface(shape, "Surface aplatie", stamps)

    def surface_freeform(self, surface, radius=None, pushes=None,
                         point=None, height=None, face=0, keep_edges=False,
                         moves=None, grid=6):
        """Forme libre : la surface est poussée en un ou plusieurs points
        ``pushes`` = [[x, y, z, hauteur], …] (ou ``point`` + ``height``),
        selon sa normale, chaque effet s'éteignant en douceur à
        ``radius`` mm ; ``keep_edges`` garde les bords en place.
        Rééditable, et suit la surface d'origine."""
        from engine.kernel import KernelError
        src = self._get_surface(surface)
        if moves:
            # Points de contrôle déplacés un à un : [[i, j, dx, dy, dz], …]
            # sur une grille de ``grid`` × ``grid`` pôles.
            stamps = {"freesource": src.Name, "freeface": int(face),
                      "freemoves": self._moves_text(moves, int(face)),
                      "freegrid": int(grid), "freeradius": 0.0}
            shape = self._free_shape(src.Shape, stamps)
            stamps["freeanchors"] = self._anchors_text(
                src.Shape, [m[0] for m in self._free_moves(stamps)])
            return self._add_frozen_surface(shape, "Forme libre", stamps)
        if radius is None:
            raise KernelError("le rayon d'influence doit être positif")
        if not pushes:
            if point is None or height is None:
                raise KernelError("cliquez au moins un point à pousser")
            pushes = [list(point) + [height]]
        stamps = {"freesource": src.Name, "freeface": int(face),
                  "freepushes": self._pushes_text(pushes),
                  "freeradius": float(radius),
                  "freeedges": int(bool(keep_edges))}
        shape = self._free_shape(src.Shape, stamps)
        return self._add_frozen_surface(shape, "Forme libre", stamps)

    def edit_surface_freeform(self, surface, radius=None, pushes=None,
                              height=None, keep_edges=None, moves=None,
                              grid=None):
        """Rééditer une forme libre : points poussés et leurs hauteurs (ou
        une hauteur commune), rayon d'influence, bords fixes."""
        from engine.kernel import KernelError
        obj = self._require_doc().getObject(str(surface))
        if obj is None or not getattr(obj, "FreeSolidFreesource", ""):
            raise KernelError("forme libre inconnue : {}".format(surface))
        self._apply_freeform_edit(obj, radius=radius, pushes=pushes,
                                  height=height, keep_edges=keep_edges,
                                  moves=moves, grid=grid)
        self._recompute()
        return self.get_tree()

    def _apply_freeform_edit(self, obj, radius=None, pushes=None,
                             height=None, keep_edges=None, moves=None,
                             grid=None):
        """La forme libre ``obj`` refaite sur sa surface source (rangée
        sur l'objet), sans recalcul : ``edit_surface_freeform`` et
        ``set_params``."""
        from engine.kernel import KernelError
        stamps = self._frozen_stamps(obj)
        if stamps.get("freemoves"):
            src = self._get_surface(stamps["freesource"])
            old_grid = int(stamps.get("freegrid", 6))
            new_grid = int(grid) if grid is not None else old_grid
            if moves is not None:
                # Indices donnés pour la grille demandée, sur les faces
                # telles que l'arbre les montre.
                stamps["freemoves"] = self._moves_text(
                    moves, int(stamps["freeface"]))
            elif new_grid != old_grid:
                # Seule la grille change : chaque pôle réglé suit sa place.
                stamps["freemoves"] = self._moves_text(self._remap_moves(
                    src.Shape, self._followed_moves(src.Shape, stamps),
                    old_grid, new_grid))
            else:
                stamps["freemoves"] = self._moves_text(
                    self._followed_moves(src.Shape, stamps))
            stamps["freeanchors"] = self._anchors_text(
                src.Shape, [m[0] for m in self._free_moves(stamps)])
            stamps["freegrid"] = new_grid
            obj.Shape = self._free_shape(src.Shape, stamps)
            self._stamp(obj, freemoves=stamps["freemoves"],
                        freeanchors=stamps["freeanchors"],
                        freegrid=new_grid)
            return
        if radius is None:
            raise KernelError("le rayon d'influence doit être positif")
        current = self._free_pushes(stamps)
        if pushes is None:
            pushes = [p[:3] + [float(height) if height is not None else p[3]]
                      for p in current]
        stamps["freepushes"] = self._pushes_text(pushes)
        stamps["freeradius"] = float(radius)
        if keep_edges is not None:
            stamps["freeedges"] = int(bool(keep_edges))
        src = self._get_surface(stamps["freesource"])
        obj.Shape = self._free_shape(src.Shape, stamps)
        self._stamp(obj, freepushes=stamps["freepushes"],
                    freeradius=float(radius),
                    freeedges=int(stamps.get("freeedges", 0)))

    @staticmethod
    def _moves_text(moves, face=0):
        """``[[face, i, j, dx, dy, dz]…]`` — ou ``[i, j, dx, dy, dz]`` sur
        la face ``face`` — en texte rangé sur l'objet."""
        from engine.kernel import KernelError
        rows = []
        for move in moves:
            try:
                move = list(move)
                if len(move) == 5:
                    move = [face] + move
                if len(move) != 6:
                    raise ValueError
                f, i, j = int(move[0]), int(move[1]), int(move[2])
                dx, dy, dz = (float(v) for v in move[3:6])
            except Exception:
                raise KernelError("point de contrôle invalide : {}".format(
                    move))
            rows.append("%d,%d,%d,%.9g,%.9g,%.9g" % (f, i, j, dx, dy, dz))
        if not rows:
            raise KernelError("choisissez au moins un point de contrôle")
        return ";".join(rows)

    @staticmethod
    def _control_surface(face, grid):
        """B-spline de la face, montée au degré 3 et affinée jusqu'à
        ``grid`` × ``grid`` pôles (au moins) — la grille de contrôle."""
        surface = face.toNurbs().Faces[0].Surface
        surface.increaseDegree(max(3, surface.UDegree),
                               max(3, surface.VDegree))
        u0, u1, v0, v1 = surface.bounds()
        grid = max(4, min(int(grid), 16))
        for direction in ("U", "V"):
            count = getattr(surface, "Nb%sPoles" % direction)
            lo, hi = (u0, u1) if direction == "U" else (v0, v1)
            missing = grid - count
            insert = getattr(surface, "insert%sKnot" % direction)
            for k in range(1, missing + 1):
                insert(lo + (hi - lo) * k / (missing + 1.0), 1, 1e-9)
        return surface

    def surface_control_points(self, surface, face=None, grid=6):
        """Grilles de contrôle d'une surface (lecture seule) : les pôles
        que la forme libre peut déplacer un par un. ``faces`` : une grille
        par face ; ``grid``/``poles`` : celle de ``face`` (0 par défaut)."""
        src = self._get_surface(surface)
        grids = []
        for k, target in enumerate(src.Shape.Faces):
            control = self._control_surface(target, grid)
            grids.append({
                "face": k, "grid": [control.NbUPoles, control.NbVPoles],
                "poles": [[[p.x, p.y, p.z]
                           for p in [control.getPole(i, j) for j in
                                     range(1, control.NbVPoles + 1)]]
                          for i in range(1, control.NbUPoles + 1)]})
        self._source_face(src.Shape, int(face or 0))
        chosen = grids[int(face or 0)]
        return {"grid": chosen["grid"], "poles": chosen["poles"],
                "faces": grids}

    @staticmethod
    def _free_moves(stamps):
        """Déplacements rangés : ``[[face, i, j, dx, dy, dz]…]`` (l'ancien
        format à 5 valeurs vise la face de la fonction)."""
        default = int(stamps.get("freeface", 0) or 0)
        moves = []
        for row in str(stamps.get("freemoves", "")).split(";"):
            if not row:
                continue
            parts = row.split(",")
            if len(parts) == 5:
                parts = [default] + parts
            moves.append([int(parts[0]), int(parts[1]), int(parts[2])]
                         + [float(v) for v in parts[3:6]])
        return moves

    def _remap_moves(self, shape, moves, old_grid, new_grid):
        """Indices des pôles réglés reportés sur une grille plus fine ou
        plus grossière : même place relative sur la face."""
        import math
        counts = {}
        out = []
        for f, i, j, dx, dy, dz in moves:
            if f not in counts:
                face = self._source_face(shape, f)
                old = self._control_surface(face, old_grid)
                new = self._control_surface(face, new_grid)
                counts[f] = (old.NbUPoles, old.NbVPoles,
                             new.NbUPoles, new.NbVPoles)
            ou, ov, nu, nv = counts[f]
            # Arrondi au plus proche, moitiés vers le haut (comme l'aperçu).
            ni = 1 + int(math.floor((i - 1) * (nu - 1)
                                    / float(max(ou - 1, 1)) + 0.5))
            nj = 1 + int(math.floor((j - 1) * (nv - 1)
                                    / float(max(ov - 1, 1)) + 0.5))
            if any(m[:3] == [f, ni, nj] for m in out):
                continue
            out.append([f, ni, nj, dx, dy, dz])
        return out

    @staticmethod
    def _face_anchor(face):
        """Un point bien à l'intérieur de ``face`` — le centre du plus
        grand triangle de son maillage, ramené sur elle : il désigne la
        face quand l'ordre des faces change."""
        import Part
        size = max(face.BoundBox.DiagonalLength / 20.0, 1e-3)
        try:
            # Sur une copie : mailler la face même casse ensuite sa
            # conversion en NURBS (« undefined surface type »).
            points, triangles = face.copy().tessellate(size)
        except Exception:  # noqa: BLE001
            points, triangles = [], []
        if triangles:
            a, b, c = max(triangles, key=lambda t: (
                (points[t[1]] - points[t[0]])
                .cross(points[t[2]] - points[t[0]]).Length))
            middle = (points[a] + points[b] + points[c]) * (1.0 / 3.0)
        else:
            middle = face.CenterOfMass
        return face.distToShape(Part.Vertex(middle))[1][0][0]

    def _anchors_text(self, shape, faces):
        """``face,x,y,z;…`` : un point de repère par face réglée."""
        rows = []
        for f in sorted(set(faces)):
            if 0 <= f < len(shape.Faces):
                p = self._face_anchor(shape.Faces[f])
                rows.append("%d,%.9g,%.9g,%.9g" % (f, p.x, p.y, p.z))
        return ";".join(rows)

    @staticmethod
    def _followed_faces(shape, text):
        """Indice rangé → indice actuel : chaque face réglée retrouvée au
        plus près de son point de repère (un segment ajouté au début de
        l'esquisse amont décale l'ordre des faces). Sans repère, ou sur une
        surface d'une seule face, les indices restent."""
        import FreeCAD as App
        import Part
        out = {}
        if len(shape.Faces) < 2:
            return out
        for row in str(text or "").split(";"):
            try:
                f, x, y, z = row.split(",")
                f = int(f)
                point = Part.Vertex(App.Vector(float(x), float(y), float(z)))
            except Exception:  # noqa: BLE001
                continue
            # À égalité (repère sur une arête commune), la face d'avant.
            out[f] = min(range(len(shape.Faces)), key=lambda k: (
                round(shape.Faces[k].distToShape(point)[0], 7), k != f))
        return out

    def _followed_moves(self, shape, stamps):
        """Les pôles déplacés, chacun sur sa face actuelle."""
        follow = self._followed_faces(shape, stamps.get("freeanchors", ""))
        return [[follow.get(m[0], m[0])] + m[1:]
                for m in self._free_moves(stamps)]

    def _followed_flat_face(self, shape, stamps):
        """La face actuelle d'un patron à plat."""
        face = int(stamps.get("flatface", 0) or 0)
        anchor = stamps.get("flatanchor", "")
        text = "%d,%s" % (face, anchor) if anchor else ""
        return self._followed_faces(shape, text).get(face, face)

    def _follow_free_faces(self, obj, shape):
        """Après un rafraîchissement : les indices et les repères rangés
        rejoignent la surface source telle qu'elle est."""
        stamps = self._frozen_stamps(obj)
        if stamps.get("freemoves"):
            moves = self._followed_moves(shape, stamps)
            self._stamp(obj, freemoves=self._moves_text(moves),
                        freeanchors=self._anchors_text(
                            shape, [m[0] for m in moves]))
        elif stamps.get("flatsource"):
            face = self._followed_flat_face(shape, stamps)
            if 0 <= face < len(shape.Faces):
                p = self._face_anchor(shape.Faces[face])
                self._stamp(obj, flatface=face,
                            flatanchor="%.9g,%.9g,%.9g" % (p.x, p.y, p.z))

    @staticmethod
    def _pushes_text(pushes):
        from engine.kernel import KernelError
        rows = []
        for push in pushes:
            try:
                x, y, z, h = (float(v) for v in push)
            except Exception:
                raise KernelError("point à pousser invalide : {}".format(push))
            rows.append("%.9g,%.9g,%.9g,%.9g" % (x, y, z, h))
        if not rows:
            raise KernelError("cliquez au moins un point à pousser")
        return ";".join(rows)

    @staticmethod
    def _free_pushes(stamps):
        """[[x, y, z, h], …] — format multi-points, ou l'ancien point seul."""
        text = str(stamps.get("freepushes", "") or "")
        if text:
            return [[float(v) for v in row.split(",")]
                    for row in text.split(";") if row]
        x, y, z = (float(v) for v in str(stamps["freepoint"]).split(";"))
        return [[x, y, z, float(stamps["freeheight"])]]

    def _add_frozen_surface(self, shape, label, stamps):
        doc = self._require_doc()
        feature = doc.addObject("Part::Feature", "Surface")
        feature.Label = self._t(label)
        feature.Shape = shape
        self._stamp(feature, **stamps)
        doc.recompute()
        return self.get_tree()

    @staticmethod
    def _frozen_stamps(obj):
        prefix = "FreeSolid"
        return {name[len(prefix):].lower(): getattr(obj, name)
                for name in obj.PropertiesList
                if name.startswith(prefix + "Free")
                or name.startswith(prefix + "Flat")}

    @staticmethod
    def _source_face(shape, face):
        from engine.kernel import KernelError
        if face < 0 or face >= len(shape.Faces):
            raise KernelError("face inconnue : {}".format(face))
        return shape.Faces[face]

    def _flat_shape(self, shape, face_index):
        from engine.kernel import KernelError
        import FreeCAD as App
        import Part
        face = self._source_face(shape, face_index).copy()
        try:
            import flatmesh
            face.tessellate(0.05)
            unwrapper = flatmesh.FaceUnwrapper(face)
            unwrapper.findFlatNodes(5, 0.95)
            loops = unwrapper.getFlatBoundaryNodes()
            wires = []
            for loop in loops:
                points = []
                for node in loop:
                    vec = App.Vector(float(node[0]), float(node[1]), 0)
                    if not points or (vec - points[-1]).Length > 1e-7:
                        points.append(vec)
                if (points[0] - points[-1]).Length > 1e-7:
                    points.append(points[0])
                wires.append(Part.makePolygon(points))
            wires.sort(key=lambda w: Part.Face(w).Area, reverse=True)
            flat = Part.Face(wires)
        except Exception:  # noqa: BLE001
            raise KernelError("aplatir : le modeleur ne sait pas dérouler "
                              "cette face")
        if flat.isNull() or not flat.isValid():
            raise KernelError("aplatir : le modeleur ne sait pas dérouler "
                              "cette face")
        # Posé à droite de toute la scène (pièce et surfaces), sur le plan
        # de dessus : il ne chevauche rien.
        box = self._scene_box(shape)
        flat.translate(App.Vector(box.XMax + 10 - flat.BoundBox.XMin,
                                  box.YMin - flat.BoundBox.YMin,
                                  -flat.BoundBox.ZMin))
        return flat

    def _flat_distortion(self, obj):
        """Déformation du patron, en % : écart d'aire et écart de longueur
        du contour entre la face d'origine et son patron à plat (0 pour
        une face développable)."""
        src = self._require_doc().getObject(str(obj.FreeSolidFlatsource))
        shape = getattr(obj, "Shape", None)
        try:
            face = self._source_face(src.Shape, self._followed_flat_face(
                src.Shape, self._frozen_stamps(obj)))
        except Exception:  # noqa: BLE001
            return {}
        if shape is None or shape.isNull() or face.Area <= 0:
            return {}
        outer = sum(e.Length for e in face.OuterWire.Edges)
        flat_outer = (sum(e.Length for e in shape.Faces[0].OuterWire.Edges)
                      if shape.Faces else 0.0)
        return {"area_error": round(100.0 * abs(shape.Area - face.Area)
                                    / face.Area, 2),
                "edge_error": round(100.0 * abs(flat_outer - outer)
                                    / max(outer, 1e-12), 2)}

    def _scene_box(self, fallback):
        """Encombrement du corps actif et des surfaces affichées, hors
        patrons à plat."""
        box = fallback.BoundBox
        shapes = []
        body = self._body
        shape = getattr(body, "Shape", None) if body is not None else None
        if shape is not None and not shape.isNull():
            shapes.append(shape)
        consumed = self._consumed_surfaces()
        for obj in self._require_doc().Objects:
            if (not self._is_surface_obj(obj) or obj.Name in consumed
                    or self._is_internal_tool(obj)
                    or getattr(obj, "FreeSolidFlatsource", "")):
                continue
            shape = getattr(obj, "Shape", None)
            if shape is not None and not shape.isNull():
                shapes.append(shape)
        for shape in shapes:
            try:
                box.add(shape.BoundBox)
            except Exception:  # noqa: BLE001
                pass
        return box

    def _free_shape(self, shape, stamps):
        """Les faces déformées — pôles déplacés face par face, ou points
        poussés rangés sur la face la plus proche — et les autres faces
        telles quelles, recousues quand elles se touchent encore."""
        import Part
        default = int(stamps["freeface"])
        changed = {}
        if stamps.get("freemoves"):
            groups = {}
            for f, i, j, dx, dy, dz in self._followed_moves(shape, stamps):
                groups.setdefault(f, []).append((i, j, dx, dy, dz))
            for f, rows in sorted(groups.items()):
                changed[f] = self._moved_shape(
                    self._source_face(shape, f), rows,
                    int(stamps.get("freegrid", 6)))
        else:
            groups = {}
            for push in self._free_pushes(stamps):
                f = default
                if len(shape.Faces) > 1:
                    point = Part.Vertex(*push[:3])
                    f = min(range(len(shape.Faces)), key=lambda k: shape
                            .Faces[k].distToShape(point)[0])
                groups.setdefault(f, []).append(push)
            for f, pushes in sorted(groups.items()):
                changed[f] = self._free_face_shape(
                    self._source_face(shape, f), pushes, stamps)
        faces = []
        for k, face in enumerate(shape.Faces):
            faces.extend(changed[k].Faces if k in changed else [face.copy()])
        if len(faces) == 1:
            return faces[0]
        try:
            shell = Part.makeShell(faces)
            shell.sewShape()
            if shell.isValid() and len(shell.Faces) == len(faces):
                return shell
        except Exception:  # noqa: BLE001
            pass
        return Part.makeCompound(faces)

    def _free_face_shape(self, face, pushes, stamps):
        """Pôles de la face déplacés selon la normale, avec une cloche
        qui s'éteint au rayon d'influence (mesuré sur la surface)."""
        from engine.kernel import KernelError
        import math
        import FreeCAD as App
        keep_edges = bool(int(stamps.get("freeedges", 0) or 0))
        radius = float(stamps["freeradius"])
        if radius <= 0:
            raise KernelError("le rayon d'influence doit être positif")
        u0, u1, v0, v1 = face.ParameterRange
        surface = face.toNurbs().Faces[0].Surface
        nu0, nu1, nv0, nv1 = surface.bounds()
        # De la finesse pour que la bosse soit ronde : des nœuds en plus.
        for _ in range(3):
            if surface.NbUPoles >= 16:
                break
            for k in range(1, 4):
                surface.insertUKnot(nu0 + (nu1 - nu0) * k / 4.0, 1, 1e-9)
        for _ in range(3):
            if surface.NbVPoles >= 16:
                break
            for k in range(1, 4):
                surface.insertVKnot(nv0 + (nv1 - nv0) * k / 4.0, 1, 1e-9)
        centers = []
        for x, y, z, height in pushes:
            center = App.Vector(x, y, z)
            cu, cv = surface.parameter(center)
            centers.append((center, surface.normal(cu, cv), height))
        poles = {(i, j): surface.getPole(i, j)
                 for i in range(1, surface.NbUPoles + 1)
                 for j in range(1, surface.NbVPoles + 1)}
        moved = False
        for (i, j), pole in poles.items():
            if keep_edges and (i in (1, surface.NbUPoles)
                               or j in (1, surface.NbVPoles)):
                continue
            shift = App.Vector(0, 0, 0)
            for center, normal, height in centers:
                gap = (pole - center).Length
                if gap >= radius:
                    continue
                weight = 0.5 * (1 + math.cos(math.pi * gap / radius))
                shift = shift + normal * (height * weight)
            if shift.Length > 0:
                surface.setPole(i, j, pole + shift)
                moved = True
        if not moved:
            raise KernelError("forme libre : aucun point de contrôle dans le "
                              "rayon — agrandissez-le")
        # Bornes de la face d'origine, sinon celles de la surface entière.
        try:
            result = surface.toShape(u0, u1, v0, v1)
        except Exception:  # noqa: BLE001
            result = surface.toShape(nu0, nu1, nv0, nv1)
        if result.isNull() or not result.isValid():
            raise KernelError("forme libre : la surface poussée est invalide "
                              "— réduisez la hauteur")
        return result

    def _moved_shape(self, face, rows, grid):
        """Pôles de la grille de contrôle déplacés de leur vecteur."""
        from engine.kernel import KernelError
        import FreeCAD as App
        control = self._control_surface(face, grid)
        for i, j, dx, dy, dz in rows:
            if not (1 <= i <= control.NbUPoles and 1 <= j <= control.NbVPoles):
                raise KernelError("point de contrôle hors de la grille : "
                                  "{} {}".format(i, j))
            control.setPole(i, j, control.getPole(i, j)
                            + App.Vector(float(dx), float(dy), float(dz)))
        result = control.toShape()
        if result.isNull() or not result.isValid():
            raise KernelError("forme libre : la surface déformée est "
                              "invalide")
        return result
