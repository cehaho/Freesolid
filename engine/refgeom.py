"""Géométrie de référence : axe, point, repère.

Comme le plan de référence, ils vivent dans le corps et suivent ce qui
les porte : un axe d'origine, une arête droite ou circulaire ; un sommet,
le centre d'un cercle ou des coordonnées ; un repère sur un sommet ou à
des coordonnées. Les imports FreeCAD restent dans les méthodes.
"""

_AXIS_ROLES = {"X": "X_Axis", "Y": "Y_Axis", "Z": "Z_Axis"}
_AXIS_OF_ROLE = {role: axis for axis, role in _AXIS_ROLES.items()}
_PLANE_OF_ROLE = {"XY_Plane": "XY", "XZ_Plane": "XZ", "YZ_Plane": "YZ"}

#: Types de la géométrie de référence (l'arbre leur donne un placement).
REFERENCE_TYPES = frozenset({
    "PartDesign::Plane", "PartDesign::Line", "PartDesign::Point",
    "PartDesign::CoordinateSystem",
})


#: Ce qu'une référence re-choisit à sa réédition (``set_params``) : les
#: mots de sa création, dans leur ordre de priorité.
REFERENCE_KEYS = {
    "PartDesign::Plane": ("face", "base", "offset", "angle"),
    "PartDesign::Line": ("edge", "axis"),
    "PartDesign::Point": ("vertex", "edge", "point"),
    "PartDesign::CoordinateSystem": ("vertex", "point"),
}

_REFERENCE_KIND = {
    "PartDesign::Plane": "plane", "PartDesign::Line": "axis",
    "PartDesign::Point": "point", "PartDesign::CoordinateSystem": "cs",
}


class RefGeomMixin:
    """Ops : add_datum_axis, add_datum_point, add_datum_cs ; la réédition
    de toute la géométrie de référence (plan compris)."""

    def _new_datum(self, type_id, name, label, support, mode, at=None):
        """Crée l'objet, l'attache (ou le pose à ``at``), le retire si la
        reconstruction échoue."""
        from engine.kernel import KernelError, _explain
        App = self._app()
        body = self._require_body()
        doc = self._require_doc()
        obj = body.newObject(type_id, name)
        try:
            if support:
                obj.AttachmentSupport = support
                obj.MapMode = mode
            else:
                obj.MapMode = "Deactivated"
                obj.Placement = App.Placement(
                    App.Vector(*[float(c) for c in at]), App.Rotation())
            obj.Label = self._t(label)
            self._recompute()
        except Exception as exc:  # noqa: BLE001
            try:
                doc.removeObject(obj.Name)
            except Exception:  # noqa: BLE001
                pass
            if isinstance(exc, KernelError):
                raise
            raise KernelError(_explain(exc))
        return self.get_tree()

    def _edge_support(self, edge, tip=None):
        """(appui, mode) d'une arête du solide (``tip``, sinon la pointe
        du corps actif) : droite ou circulaire."""
        from engine.kernel import KernelError
        tip = tip or self._solid_tip("un élément de référence sur une "
                                     "arête demande un solide")
        edges = tip.Shape.Edges
        index = int(edge)
        if not 0 <= index < len(edges):
            raise KernelError("arête inconnue : {}".format(index))
        curve = edges[index].Curve.TypeId
        support = [(tip, "Edge{}".format(index + 1))]
        if curve == "Part::GeomLine":
            return support, "straight"
        if curve in ("Part::GeomCircle", "Part::GeomEllipse"):
            return support, "circle"
        raise KernelError("choisissez une arête droite ou circulaire")

    def _vertex_support(self, at, tip=None):
        tip = tip or self._solid_tip("un élément de référence sur un "
                                     "sommet demande un solide")
        index = self._nearest_vertex(tip.Shape, at)
        return [(tip, "Vertex{}".format(index + 1))]

    def add_datum_axis(self, axis=None, edge=None):
        """Axe de référence : sur un axe d'origine (``axis`` X, Y ou Z), le
        long d'une arête droite, ou sur l'axe d'une arête circulaire."""
        from engine.kernel import KernelError
        if edge is not None:
            support, shape = self._edge_support(edge)
            mode = "TwoPointLine" if shape == "straight" else "AxisOfCurvature"
        else:
            role = _AXIS_ROLES.get(str(axis or "Z").upper())
            if role is None:
                raise KernelError("axe inconnu « {} » — attendu X, Y ou Z"
                                  .format(axis))
            support = [(self._origin_feature(role), "")]
            mode = "TwoPointLine"
        return self._new_datum("PartDesign::Line", "DatumLine",
                               "Axe de référence", support, mode)

    def add_datum_point(self, point=None, vertex=None, edge=None):
        """Point de référence : sur le sommet le plus proche de ``vertex``
        (coordonnées cliquées), au centre d'une arête circulaire, ou aux
        coordonnées ``point``."""
        from engine.kernel import KernelError
        if vertex is not None:
            return self._new_datum("PartDesign::Point", "DatumPoint",
                                   "Point de référence",
                                   self._vertex_support(vertex), "Vertex")
        if edge is not None:
            support, shape = self._edge_support(edge)
            if shape != "circle":
                raise KernelError("le centre demande une arête circulaire")
            return self._new_datum("PartDesign::Point", "DatumPoint",
                                   "Point de référence", support,
                                   "CenterOfCurvature")
        if point is None or len(point) != 3:
            raise KernelError("donnez un sommet, un cercle ou trois "
                              "coordonnées")
        return self._new_datum("PartDesign::Point", "DatumPoint",
                               "Point de référence", None, None, at=point)

    def add_datum_cs(self, point=None, vertex=None):
        """Repère : axes parallèles à ceux de l'origine, posé sur le
        sommet le plus proche de ``vertex`` ou aux coordonnées ``point``."""
        from engine.kernel import KernelError
        if vertex is not None:
            return self._new_datum("PartDesign::CoordinateSystem",
                                   "LocalCS", "Repère",
                                   self._vertex_support(vertex), "Translate")
        if point is None or len(point) != 3:
            raise KernelError("donnez un sommet ou trois coordonnées")
        return self._new_datum("PartDesign::CoordinateSystem", "LocalCS",
                               "Repère", None, None, at=point)

    # -- réédition : ce qui porte la référence, re-choisi au rang ---------

    def _is_reference(self, obj):
        """Une référence rangée dans un corps de la pièce."""
        parent = getattr(obj, "getParentGeoFeatureGroup", None)
        if parent is None or obj.TypeId not in REFERENCE_TYPES:
            return False
        body = parent()
        return body is not None and body in self._history_bodies()

    def _reference_rank(self, obj, history):
        """La dernière ligne d'historique avant la référence ``obj`` (une
        référence n'en est pas une) : la barre se pose juste après elle
        pour montrer la pièce à son rang. None si rien ne la précède."""
        order_of = self._tree_order()
        mine = order_of.get(obj.Name, -1)
        before = [line.Name for line in history
                  if order_of.get(line.Name, -1) < mine]
        return before[-1] if before else None

    def _reference_rank_base(self, obj):
        """La pièce au rang d'une référence : la dernière fonction de son
        corps qui la précède dans l'arbre, celle que montre la vue au rang.
        Ses faces, arêtes et sommets sont ceux que la réédition re-choisit.
        None si aucune fonction ne la précède."""
        body = obj.getParentGeoFeatureGroup()
        mine = self._tree_order().get(obj.Name)
        if body is None or mine is None:
            return None
        rows = [row for row in self._history_rows()
                if row["role"] == "feature" and row["body"] == body.Name
                and row["order"] < mine]
        if not rows:
            return None
        last = max(rows, key=lambda row: row["order"])
        return self._require_doc().getObject(last["name"])

    def _reference_base(self, obj, message):
        """``_reference_rank_base``, qui doit être un solide."""
        from engine.kernel import KernelError
        base = self._reference_rank_base(obj)
        shape = getattr(base, "Shape", None)
        if base is None or shape is None or not shape.Solids:
            raise KernelError(message)
        return base

    @staticmethod
    def _element_on(base, target, kind, index):
        """L'indice sur ``base`` de l'élément ``kind`` (``Faces``,
        ``Edges``, ``Vertexes``) numéro ``index`` de ``target`` ; None s'il
        n'y est plus."""
        if base is None:
            return None
        if target is base:
            return index
        try:
            element = getattr(target.Shape, kind)[index]
            return next((i for i, other in enumerate(getattr(base.Shape, kind))
                         if other.isSame(element)), None)
        except Exception:  # noqa: BLE001
            return None

    def _reference_spec(self, obj):
        """Ce qui porte une référence, dans les mots de sa création (et de
        ``set_params``) : ``{"kind": "plane", "base": "XY" | "face": id,
        "offset", "angle"}``, ``{"kind": "axis", "axis": "Z" | "edge": id}``,
        ``{"kind": "point" | "cs", "vertex": [x, y, z] | "edge": id |
        "point": [x, y, z]}``. Les faces et arêtes sont celles de la pièce
        à son rang, None si elles n'y sont plus. None pour une référence
        posée autrement (un fichier d'ailleurs)."""
        kind = _REFERENCE_KIND.get(obj.TypeId)
        if kind is None:
            return None
        mode = str(getattr(obj, "MapMode", ""))
        spec = {"kind": kind}
        if kind == "plane":
            offset = obj.AttachmentOffset
            spec["offset"] = round(float(offset.Base.z), 9)
            spec["angle"] = round(float(offset.Rotation.getYawPitchRoll()[2]),
                                  9)
        if mode == "Deactivated":
            if kind not in ("point", "cs"):
                return None
            spec["point"] = [round(float(c), 9) for c in obj.Placement.Base]
            return spec
        support = (getattr(obj, "AttachmentSupport", None)
                   or getattr(obj, "Support", None) or [])
        try:
            target, subs = list(support)[0]
        except (IndexError, TypeError, ValueError):
            return None
        if target is None:
            return None
        subs = list(subs) if isinstance(subs, (list, tuple)) else [subs]
        name = str(subs[0]) if subs else ""
        role = str(getattr(target, "Role", ""))
        expected = {"plane": ("FlatFace",),
                    "axis": ("TwoPointLine", "AxisOfCurvature"),
                    "point": ("Vertex", "CenterOfCurvature"),
                    "cs": ("Translate",)}[kind]
        if mode not in expected:
            return None
        if kind == "plane" and role in _PLANE_OF_ROLE:
            spec["base"] = _PLANE_OF_ROLE[role]
            return spec
        if kind == "axis" and role in _AXIS_OF_ROLE:
            spec["axis"] = _AXIS_OF_ROLE[role]
            return spec
        for prefix, key, shapes in (("Face", "face", "Faces"),
                                    ("Edge", "edge", "Edges"),
                                    ("Vertex", "vertex", "Vertexes")):
            if not (name.startswith(prefix) and name[len(prefix):].isdigit()):
                continue
            index = int(name[len(prefix):]) - 1
            if key == "vertex":
                try:
                    point = target.Shape.Vertexes[index].Point
                except Exception:  # noqa: BLE001
                    return None
                spec["vertex"] = [round(float(c), 9) for c in point]
            else:
                # Une face, une arête : celles de la pièce à son rang.
                spec[key] = self._element_on(self._reference_rank_base(obj),
                                             target, shapes, index)
            return spec
        return None

    def _set_reference_params(self, obj, values):
        """``set_params`` d'une référence : ce qui la porte, re-choisi —
        une face (``face``), une arête (``edge``) ou un sommet (``vertex``)
        de la pièce à son rang, un élément d'origine (``base``, ``axis``)
        ou des coordonnées (``point``) — et le décalage et l'angle d'un
        plan. Ce qui n'est pas donné reste. Tout ou rien."""
        from engine.kernel import KernelError, parse_user_number
        allowed = REFERENCE_KEYS[obj.TypeId]
        for key in values:
            if key not in allowed:
                raise KernelError("propriété non éditable : {}".format(key))
        App = self._app()
        body = obj.getParentGeoFeatureGroup()
        chosen = next((key for key in allowed
                       if key in values and key not in ("offset", "angle")),
                      None)
        support, mode, at = None, None, None
        if chosen == "face":
            base = self._reference_base(obj, "pas de solide pour porter ce "
                                             "plan")
            face = values["face"]
            if (isinstance(face, bool) or not isinstance(face, int)
                    or not 0 <= face < len(base.Shape.Faces)):
                raise KernelError("face inconnue : {}".format(face))
            support, mode = [(base, ("Face{}".format(face + 1),))], "FlatFace"
        elif chosen == "base":
            role = self._PLANE_ROLES.get(str(values["base"] or "XY").upper())
            if role is None:
                raise KernelError("plan inconnu « {} » — attendu XY, XZ ou "
                                  "YZ".format(values["base"]))
            support = [(self._origin_feature(role, body), ("",))]
            mode = "FlatFace"
        elif chosen == "axis":
            role = _AXIS_ROLES.get(str(values["axis"] or "Z").upper())
            if role is None:
                raise KernelError("axe inconnu « {} » — attendu X, Y ou Z"
                                  .format(values["axis"]))
            support = [(self._origin_feature(role, body), "")]
            mode = "TwoPointLine"
        elif chosen == "edge":
            base = self._reference_base(obj, "un élément de référence sur "
                                             "une arête demande un solide")
            support, shape = self._edge_support(values["edge"], base)
            if obj.TypeId == "PartDesign::Line":
                mode = ("TwoPointLine" if shape == "straight"
                        else "AxisOfCurvature")
            elif shape != "circle":
                raise KernelError("le centre demande une arête circulaire")
            else:
                mode = "CenterOfCurvature"
        elif chosen == "vertex":
            base = self._reference_base(obj, "un élément de référence sur "
                                             "un sommet demande un solide")
            support = self._vertex_support(values["vertex"], base)
            mode = ("Vertex" if obj.TypeId == "PartDesign::Point"
                    else "Translate")
        elif chosen == "point":
            at = values["point"]
            if not isinstance(at, (list, tuple)) or len(at) != 3:
                raise KernelError("donnez un sommet ou trois coordonnées")
            at = [parse_user_number(c) for c in at]
            if None in at:
                raise KernelError("valeur invalide pour {} : {}".format(
                    "point", values["point"]))
        numbers = {}
        for key in ("offset", "angle"):
            if key in values:
                number = parse_user_number(values[key])
                if number is None:
                    raise KernelError("valeur invalide pour {} : {}".format(
                        key, values[key]))
                numbers[key] = number
        if support is not None:
            try:
                obj.AttachmentSupport = support
            except AttributeError:
                obj.Support = support
            obj.MapMode = mode
        elif at is not None:
            obj.MapMode = "Deactivated"
            try:
                obj.AttachmentSupport = []
            except AttributeError:
                obj.Support = []
            obj.Placement = App.Placement(App.Vector(*at), App.Rotation())
        if numbers:
            offset = obj.AttachmentOffset
            obj.AttachmentOffset = App.Placement(
                App.Vector(0, 0, numbers.get("offset", offset.Base.z)),
                App.Rotation(App.Vector(1, 0, 0), numbers.get(
                    "angle", offset.Rotation.getYawPitchRoll()[2])))
        self._recompute()
        return self.get_tree()
