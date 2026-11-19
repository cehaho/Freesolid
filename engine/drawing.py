"""Mise en plan : vues, cotes d'encombrement, coupe, export.

Mixin de ``Kernel``. Pas d'import FreeCAD au niveau du module :
les méthodes importent le noyau à l'appel, pour éviter un cycle.
"""

class DrawingMixin:
    # -- mise en plan ----------------------------------------------------

    @staticmethod
    def _drawing_visible_edges(view):
        try:
            return list(view.getVisibleEdges() or [])
        except Exception:  # noqa: BLE001
            return []

    @staticmethod
    def _drawing_apply_scale(view, scale):
        if scale:
            view.ScaleType = "Custom"
            view.Scale = float(scale)

    @staticmethod
    def _drawing_extreme_edge_ids(edges):
        """Indices gauche / droite / bas / haut (centres des BoundBox 2D)."""
        if len(edges) < 2:
            return None
        indexed = list(enumerate(edges))

        def cx(item):
            box = item[1].BoundBox
            return (box.XMin + box.XMax) / 2.0

        def cy(item):
            box = item[1].BoundBox
            return (box.YMin + box.YMax) / 2.0

        left = min(indexed, key=cx)[0]
        right = max(indexed, key=cx)[0]
        bottom = min(indexed, key=cy)[0]
        top = max(indexed, key=cy)[0]
        if left == right or bottom == top:
            return None
        return left, right, bottom, top

    def _drawing_add_extent_dims(self, doc, page, view, created):
        """Cotes d'encombrement DistanceX/DistanceY sur la vue de face.

        Les arêtes 2D doivent déjà être peuplées (CoarseView posé à la
        création de la vue — trop tard ensuite). Retourne False plutôt
        que d'échouer : le DXF muet reste meilleur que pas de DXF.
        """
        edges = self._drawing_visible_edges(view)
        ids = self._drawing_extreme_edge_ids(edges)
        if ids is None:
            return False
        left, right, bottom, top = ids
        dims = []
        for name, dtype, a, b in (
                ("DimLargeur", "DistanceX", left, right),
                ("DimHauteur", "DistanceY", bottom, top)):
            dim = doc.addObject("TechDraw::DrawViewDimension", name)
            created.append(dim)
            dims.append(dim)
            page.addView(dim)
            dim.Type = dtype
            dim.References2D = [
                (view, "Edge{}".format(a)),
                (view, "Edge{}".format(b)),
            ]
        doc.recompute()
        for dim in dims:
            if "Up-to-date" not in getattr(dim, "State", []):
                return False
            if hasattr(dim, "getRawValue"):
                try:
                    if not (dim.getRawValue() > 0):
                        return False
                except Exception:  # noqa: BLE001
                    return False
        return True

    def _drawing_add_section(self, doc, page, body, views, axis, scale,
                             created):
        """Vue en coupe (DrawViewSection) — normale selon X/Y/Z.

        La vue de base doit avoir une Direction non parallèle à la
        normale, sinon TechDraw n'arrive pas à construire le CS
        (getSectionCS) et le cut async peut SIGSEGV. Origine = (0,0,0).
        Hachures : défaut SvgHatch (CutSurfaceDisplay=Hide SIGSEGV en
        1.0.0 headless). La géométrie 2D de la coupe reste souvent vide
        headless (même thread HLR) — l'objet est quand même exporté.
        """
        App = self._app()
        normals = {"X": (1.0, 0.0, 0.0),
                   "Y": (0.0, 1.0, 0.0),
                   "Z": (0.0, 0.0, 1.0)}
        nx, ny, nz = normals[axis]
        nlen = (nx * nx + ny * ny + nz * nz) ** 0.5
        base = views[0]
        for view in views:
            direction = view.Direction
            length = direction.Length or 1.0
            aligned = abs(direction.x * nx + direction.y * ny
                          + direction.z * nz) / (length * nlen)
            if aligned < 0.95:
                base = view
                break
        section = doc.addObject("TechDraw::DrawViewSection", "Coupe" + axis)
        created.append(section)
        page.addView(section)
        section.Source = [body]
        section.BaseView = base
        section.SectionNormal = App.Vector(nx, ny, nz)
        section.SectionOrigin = App.Vector(0, 0, 0)
        section.Direction = App.Vector(nx, ny, nz)
        self._drawing_apply_scale(section, scale)
        section.X = float(base.X) + 80
        section.Y = float(base.Y)
        doc.recompute()
        return "Up-to-date" in getattr(section, "State", [])

    def make_drawing(self, path, scale=None, dims=True, section=None):
        """Mise en plan : Face / Dessus / Isométrique sur une page
        TechDraw, exportée en DXF (le seul export fiable headless).

        ``dims`` (défaut True) : cotes d'encombrement sur la vue de
        face. ``section`` : ``"X"|"Y"|"Z"`` pour une vue en coupe
        optionnelle. La page est retirée du document après l'export.
        """
        import os
        from engine.kernel import (
            KernelError,
            _explain,
        )
        doc = self._require_doc()
        body = self._require_body()
        App = self._app()
        path = str(path)
        if not path.lower().endswith(".dxf"):
            path += ".dxf"
        path = self._user_path(path, (".dxf",), must_exist=False)
        want_dims = True if dims is None else bool(dims)
        axis = None
        if section not in (None, "", False):
            axis = str(section).strip().upper()
            if axis not in ("X", "Y", "Z"):
                raise KernelError("coupe : axe X, Y ou Z attendu")
        created = []
        cleanup_errors = []
        original = None
        dims_ok = None
        section_ok = None
        try:
            page = doc.addObject("TechDraw::DrawPage", "Page")
            created.append(page)
            template = doc.addObject("TechDraw::DrawSVGTemplate",
                                     "Template")
            created.append(template)
            template_path = os.path.join(
                App.getResourceDir(), "Mod", "TechDraw", "Templates",
                "A4_LandscapeTD.svg")
            if os.path.exists(template_path):
                template.Template = template_path
            page.Template = template
            placements = (("Face", (0, -1, 0), 70, 60),
                          ("Dessus", (0, 0, 1), 70, 150),
                          ("Iso", (1, -1, 1), 210, 105))
            views = []
            for name, direction, x, y in placements:
                view = doc.addObject("TechDraw::DrawViewPart",
                                     "View" + name)
                created.append(view)
                view.Source = [body]
                view.Direction = App.Vector(*direction)
                # Headless 1.0.x : le HLR Qt ne peuple pas les arêtes 2D.
                # CoarseView doit être posé AVANT le premier recompute.
                if want_dims:
                    view.CoarseView = True
                self._drawing_apply_scale(view, scale)
                page.addView(view)
                view.X = x
                view.Y = y
                views.append(view)
            doc.recompute()
            if want_dims:
                try:
                    dims_ok = self._drawing_add_extent_dims(
                        doc, page, views[0], created)
                except Exception:  # noqa: BLE001
                    dims_ok = False
            if axis is not None:
                try:
                    section_ok = self._drawing_add_section(
                        doc, page, body, views, axis, scale, created)
                except Exception:  # noqa: BLE001
                    section_ok = False
            import TechDraw
            TechDraw.writeDXFPage(page, path)
        except KernelError as exc:
            original = exc
            raise
        except Exception as exc:  # noqa: BLE001
            original = KernelError(_explain(exc))
            raise original
        finally:
            for obj in reversed(created):
                try:
                    doc.removeObject(obj.Name)
                except Exception as exc:  # noqa: BLE001
                    cleanup_errors.append("{} ({})".format(
                        getattr(obj, "Name", "?"), _explain(exc)))
            try:
                doc.recompute()
            except Exception:
                pass
            if cleanup_errors:
                note = "mise en plan : nettoyage incomplet — {}".format(
                    " ; ".join(cleanup_errors))
                if original is None:
                    raise KernelError(note)
                original.args = (original.args[0] + " — " + note,)
        if not os.path.exists(path):
            raise KernelError("l'export DXF n'a rien produit")
        result = {"path": path, "size": os.path.getsize(path)}
        if dims_ok is not None:
            result["dims_ok"] = bool(dims_ok)
        if section_ok is not None:
            result["section_ok"] = bool(section_ok)
        return result

    # -- feuille à l'écran -------------------------------------------------

    @staticmethod
    def _view_matrix(App, right, up, toward):
        """Repère pièce → repère de la vue (x à droite, y en haut, z vers
        l'observateur) ; l'isométrique déduit droite et haut de Z."""
        t = App.Vector(*toward)
        t.normalize()
        if right is None:
            z = App.Vector(0, 0, 1)
            u = z - t * z.dot(t)
            u.normalize()
            r = u.cross(t)
        else:
            r, u = App.Vector(*right), App.Vector(*up)
        return App.Matrix(r.x, r.y, r.z, 0,
                          u.x, u.y, u.z, 0,
                          t.x, t.y, t.z, 0,
                          0, 0, 0, 1)

    @staticmethod
    def _polylines(shape, deflection):
        lines = []
        if shape is None or shape.isNull():
            return lines
        for edge in shape.Edges:
            try:
                points = edge.discretize(Deflection=deflection)
            except Exception:  # noqa: BLE001 — arête dégénérée
                continue
            if len(points) >= 2:
                lines.append([[round(p.x, 3), round(p.y, 3)]
                              for p in points])
        return lines

    def _drawing_part_name(self, body):
        import os
        path = getattr(self._doc, "FileName", "") or ""
        if path.lower().endswith(".fcstd"):
            return os.path.splitext(os.path.basename(path))[0]
        return body.Label

    def drawing_views(self, scale=None, hidden=True):
        """La feuille de mise en plan à l'écran : les quatre vues projetées
        (face, dessus, droite, isométrique), leurs arêtes vues et cachées
        en mm réels, centrées, l'échelle normalisée, la place de chaque
        vue sur l'A4 et les cotes d'encombrement. Rien n'entre dans le
        document ; ``make_drawing`` reste l'export DXF."""
        from engine.kernel import KernelError
        from engine import drawingsheet
        import TechDraw
        App = self._app()
        body = self._require_body()
        shape = getattr(body, "Shape", None)
        if shape is None or shape.isNull() or not shape.Solids:
            raise KernelError("mise en plan : la pièce n'a pas de volume")
        extent = max(shape.BoundBox.XLength, shape.BoundBox.YLength,
                     shape.BoundBox.ZLength, 1e-3)
        deflection = extent * 0.002
        views = []
        sizes = {}
        for name, label, right, up, toward in drawingsheet.VIEWS:
            placed = shape.copy()
            placed.transformShape(
                self._view_matrix(App, right, up, toward))
            parts = TechDraw.projectEx(placed, App.Vector(0, 0, 1))
            seen = [parts[i] for i in (0, 1, 3) if i < len(parts)]
            unseen = [parts[i] for i in (5, 6, 8) if i < len(parts)]
            boxes = [s.BoundBox for s in seen if not s.isNull()
                     and s.Edges]
            if not boxes:
                continue
            x0 = min(b.XMin for b in boxes)
            x1 = max(b.XMax for b in boxes)
            y0 = min(b.YMin for b in boxes)
            y1 = max(b.YMax for b in boxes)
            cx, cy = (x0 + x1) / 2, (y0 + y1) / 2

            def centred(lines, cx=cx, cy=cy):
                return [[[round(x - cx, 3), round(y - cy, 3)]
                         for x, y in line] for line in lines]

            visible = []
            for part in seen:
                visible += self._polylines(part, deflection)
            hidden_lines = []
            # Les vues de base montrent leurs arêtes cachées en traits
            # interrompus ; l'isométrique, non.
            if hidden and name != "iso":
                for part in unseen:
                    hidden_lines += self._polylines(part, deflection)
            sizes[name] = (x1 - x0, y1 - y0)
            views.append({"name": name, "label": self._t(label),
                          "width": round(x1 - x0, 3),
                          "height": round(y1 - y0, 3),
                          "visible": centred(visible),
                          "hidden": centred(hidden_lines)})
        placed = drawingsheet.layout(sizes, scale)
        for view in views:
            view["center"] = [round(c, 3)
                              for c in placed["centers"][view["name"]]]
        box = shape.BoundBox
        material = (self._material_of(body) or {}).get("name")
        return {
            "sheet": dict(drawingsheet.SHEET),
            "title_block": dict(drawingsheet.TITLE_BLOCK),
            "scale": placed["scale"],
            "scale_label": drawingsheet.scale_label(placed["scale"]),
            "views": views,
            # Cotes d'encombrement : largeur et hauteur sur la face,
            # profondeur sur le dessus (mm réels).
            "dims": [
                {"view": "front", "axis": "x",
                 "value": round(box.XLength, 3)},
                {"view": "front", "axis": "y",
                 "value": round(box.ZLength, 3)},
                {"view": "top", "axis": "y",
                 "value": round(box.YLength, 3)},
            ],
            # Le nom du fichier, comme le cartouche des modeleurs courants ;
            # le corps tant que la pièce n'est pas enregistrée.
            "part": self._drawing_part_name(body),
            "material": material,
        }

    def write_drawing_dxf(self, path, width, height, entities):
        """Enregistre la feuille vue à l'écran en DXF : les entités de
        ``sheetEntities`` (client), mêmes vues, cotes et cartouche."""
        import os
        from engine.kernel import KernelError
        from engine.dxfwrite import DxfError, drawing_dxf
        path = str(path)
        if not path.lower().endswith(".dxf"):
            path += ".dxf"
        path = self._user_path(path, (".dxf",), must_exist=False)
        try:
            text = drawing_dxf(width, height, entities)
        except (DxfError, TypeError, ValueError) as exc:
            raise KernelError("mise en plan : feuille illisible ({})".format(
                exc))
        with open(path, "w", encoding="cp1252", errors="replace",
                  newline="\r\n") as handle:
            handle.write(text)
        return {"path": path, "size": os.path.getsize(path)}
