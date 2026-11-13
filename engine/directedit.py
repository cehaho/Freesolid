"""Édition directe : tirer la face du bout d'une extrusion ou d'un
enlèvement pour en changer la profondeur.

``face_drag_info`` dit si une face cliquée se tire, et comment : la
fonction et sa cote, le point et la normale de la poignée, et le facteur
entre le déplacement de la face et la cote (−1 pour le fond d'un
enlèvement, 2 pour une extrusion symétrique). ``feature_drag_info`` donne
la même poignée pour une fonction rééditée, posée au bout de l'extrusion.
Les imports FreeCAD restent dans les méthodes ; ``drag_factor`` et
``extrude_arrow`` sont testées en CI.
"""

_EXTRUDES = ("PartDesign::Pad", "PartDesign::Pocket")
_HELICES = ("PartDesign::AdditiveHelix", "PartDesign::SubtractiveHelix")


def drag_factor(face_normal_dot_sketch, cap_offset, kind, midplane=False):
    """Facteur cote / déplacement le long de la normale extérieure de la
    face. ``face_normal_dot_sketch`` : produit scalaire normale de face ·
    normale de l'esquisse ; ``cap_offset`` : distance signée de la face au
    plan de l'esquisse. Une face qui s'éloigne de l'esquisse en suivant sa
    normale allonge la cote."""
    away = face_normal_dot_sketch * (1 if cap_offset >= 0 else -1) > 0
    factor = 1.0 if away else -1.0
    return factor * (2.0 if midplane else 1.0)


def extrude_arrow(center, normal, length, pocket=False, reversed=False,
                  symmetric=False):
    """Bout d'une extrusion borgne vu du centre de son esquisse :
    ``(point, sens, facteur)``. Un enlèvement creuse à l'opposé de la
    normale de l'esquisse et ``reversed`` inverse le sens, sauf en plan
    milieu : la flèche s'y pose à mi-profondeur et la cote suit au double
    du déplacement."""
    sign = (-1 if pocket else 1) * (-1 if reversed and not symmetric else 1)
    direction = [c * sign for c in normal]
    reach = length / 2 if symmetric else length
    point = [c + d * reach for c, d in zip(center, direction)]
    return point, direction, 2.0 if symmetric else 1.0


def _depth_editable(obj):
    """Extrusion borgne dont la profondeur n'est pas pilotée par une
    équation."""
    return (obj.TypeId in _EXTRUDES
            and str(getattr(obj, "Type", "")) == "Length"
            and "Length" not in dict(obj.ExpressionEngine or []))


def _symmetric(obj):
    """Plan milieu : ``SideType`` depuis FreeCAD 1.1, où ``Midplane``
    reste faux ; ``Midplane`` avant."""
    return (str(getattr(obj, "SideType", "")) == "Symmetric"
            or bool(getattr(obj, "Midplane", False)))


class DirectEditMixin:
    """Ops : sketch_frame, face_frame, face_drag_info, feature_drag_info."""

    def sketch_frame(self, sketch):
        """Centre (milieu de l'encombrement) et normale d'une esquisse :
        où poser la poignée de profondeur d'une extrusion."""
        sk = self._get_sketch(sketch)
        App = self._app()
        normal = sk.Placement.Rotation.multVec(App.Vector(0, 0, 1))
        shape = getattr(sk, "Shape", None)
        center = (shape.BoundBox.Center if shape is not None
                  and not shape.isNull() and shape.Edges
                  else sk.Placement.Base)
        vaxis = sk.Placement.Rotation.multVec(App.Vector(0, 1, 0))
        return {"center": [center.x, center.y, center.z],
                "normal": [normal.x, normal.y, normal.z],
                "vaxis": [vaxis.x, vaxis.y, vaxis.z]}

    def face_frame(self, face):
        """Centre et normale extérieure d'une face plane du corps actif :
        d'où part la flèche de profondeur d'un perçage qu'on crée."""
        from engine.kernel import KernelError
        body = self._require_body()
        shape = getattr(body, "Shape", None)
        index = int(face)
        if shape is None or not 0 <= index < len(shape.Faces):
            raise KernelError("face inconnue : {}".format(face))
        target = shape.Faces[index]
        if target.Surface.TypeId != "Part::GeomPlane":
            return {"center": None, "normal": None}
        u0, u1, v0, v1 = target.ParameterRange
        normal = target.normalAt((u0 + u1) / 2, (v0 + v1) / 2)
        center = target.CenterOfMass
        return {"center": [center.x, center.y, center.z],
                "normal": [normal.x, normal.y, normal.z]}

    def face_drag_info(self, face):
        """Comment tirer la face ``face`` du corps actif, ou
        ``{"drag": None}`` si elle ne pilote aucune cote simple."""
        from engine.vocab import param_key_for, type_key_for
        body = self._require_body()
        shape = getattr(body, "Shape", None)
        index = int(face)
        if shape is None or not 0 <= index < len(shape.Faces):
            return {"drag": None}
        target = shape.Faces[index]
        name = self._face_producers().get(index)
        obj = self._doc.getObject(name) if name else None
        obj = self._thin_owner(obj) if obj is not None else None
        if (obj is None or not _depth_editable(obj)
                or target.Surface.TypeId != "Part::GeomPlane"):
            return {"drag": None}
        # L'esquisse, pas le liant d'un profil d'un autre corps ou d'une
        # paroi mince : c'est elle qui porte le plan et la normale.
        sketch = self._profile_sketch(obj)
        if sketch is None:
            return {"drag": None}
        App = self._app()
        axis = sketch.Placement.Rotation.multVec(App.Vector(0, 0, 1))
        u0, u1, v0, v1 = target.ParameterRange
        normal = target.normalAt((u0 + u1) / 2, (v0 + v1) / 2)
        dot = normal.dot(axis)
        if abs(abs(dot) - 1) > 1e-6:
            return {"drag": None}
        center = target.CenterOfMass
        offset = (center - sketch.Placement.Base).dot(axis)
        length = float(obj.Length.Value)
        midplane = _symmetric(obj)
        expected = length / 2 if midplane else length
        if abs(abs(offset) - expected) > 1e-6 * max(1.0, expected):
            return {"drag": None}  # pas la face du bout
        return {"drag": {
            "feature": obj.Name, "label": obj.Label,
            "key": param_key_for(type_key_for(obj.TypeId), "Length"),
            "prop": "Length",  # transition : l'interface lit ``key``
            "value": length,
            "point": [center.x, center.y, center.z],
            "normal": [normal.x, normal.y, normal.z],
            "factor": drag_factor(dot, offset, obj.TypeId, midplane),
        }}

    def feature_drag_info(self, feature):
        """La poignée de profondeur d'une extrusion ou d'un enlèvement
        qu'on réédite, au bout de la fonction — mêmes champs que
        ``face_drag_info``. ``{"drag": None}`` pour une autre fonction,
        une autre condition que borgne ou plan milieu, une profondeur
        pilotée par une équation ou une direction choisie."""
        from engine.kernel import KernelError
        from engine.vocab import param_key_for, type_key_for
        obj = self._require_doc().getObject(str(feature))
        if obj is None:
            raise KernelError("fonction inconnue : {}".format(feature))
        if obj.TypeId == "Part::Extrusion":
            return {"drag": self._surface_extrude_drag(obj)}
        if obj.TypeId == "PartDesign::Hole":
            return {"drag": self._hole_drag(obj)}
        if obj.TypeId in _HELICES:
            return {"drag": self._helix_drag(obj)}
        # L'axe caché qui suit la normale de l'esquisse (profil par un
        # liant) ne change pas la direction : la flèche reste juste.
        axis = getattr(obj, "ReferenceAxis", None)
        if (not _depth_editable(obj)
                or str(getattr(obj, "SideType", "One side"))
                not in ("One side", "Symmetric")
                or getattr(obj, "UseCustomVector", False)
                or (axis is not None and not self._is_thin_helper(axis[0]))):
            return {"drag": None}
        sketch = self._profile_sketch(obj)
        if sketch is None:
            return {"drag": None}
        frame = self.sketch_frame(sketch.Name)
        length = float(obj.Length.Value)
        point, direction, factor = extrude_arrow(
            frame["center"], frame["normal"], length,
            pocket=obj.TypeId == "PartDesign::Pocket",
            reversed=bool(getattr(obj, "Reversed", False)),
            symmetric=_symmetric(obj))
        return {"drag": {
            "feature": obj.Name, "label": obj.Label,
            "key": param_key_for(type_key_for(obj.TypeId), "Length"),
            "value": length, "point": point, "normal": direction,
            "factor": factor,
        }}

    def _surface_extrude_drag(self, obj):
        """La flèche d'une surface extrudée : au bout de son esquisse, le
        long de sa direction, comme à la création. None si elle n'est pas
        d'un seul côté, si sa longueur suit une équation ou si son profil
        n'est pas une esquisse."""
        from engine.vocab import param_key_for

        def number(value):
            return float(getattr(value, "Value", value))

        base = getattr(obj, "Base", None)
        direction = getattr(obj, "Dir", None)
        if (base is None or base.TypeId != "Sketcher::SketchObject"
                or direction is None or direction.Length < 1e-9
                or bool(getattr(obj, "Symmetric", False))
                or bool(getattr(obj, "Reversed", False))
                or abs(number(getattr(obj, "LengthRev", 0))) > 1e-9
                or abs(number(getattr(obj, "TaperAngle", 0))) > 1e-9
                or "LengthFwd" in dict(obj.ExpressionEngine or [])):
            return None
        frame = self.sketch_frame(base.Name)
        unit = direction.normalize()
        length = number(obj.LengthFwd)
        normal = [unit.x, unit.y, unit.z]
        return {
            "feature": obj.Name, "label": obj.Label,
            "key": param_key_for("surface_extrude", "LengthFwd"),
            "value": length,
            "point": [c + d * length for c, d in zip(frame["center"], normal)],
            "normal": normal, "factor": 1.0,
        }

    def _hole_drag(self, obj):
        """La flèche d'un perçage borgne : au fond du premier trou, dans
        le sens du perçage (contre la normale de l'esquisse, sauf
        ``Reversed``). None pour un perçage traversant ou dont la
        profondeur suit une équation."""
        from engine.vocab import param_key_for, type_key_for
        profile = getattr(obj, "Profile", None)
        sketch = profile[0] if profile else None
        if (sketch is None or sketch.TypeId != "Sketcher::SketchObject"
                or str(getattr(obj, "DepthType", "")) != "Dimension"
                or "Depth" in dict(obj.ExpressionEngine or [])):
            return None
        place = sketch.getGlobalPlacement()
        center = next((g.Center for i, g in enumerate(sketch.Geometry)
                       if g.TypeId == "Part::GeomCircle"
                       and not sketch.getConstruction(i)), None)
        if center is None:
            return None
        origin = place.multVec(center)
        normal = place.Rotation.multVec(self._app().Vector(0, 0, 1))
        sign = 1 if getattr(obj, "Reversed", False) else -1
        direction = [c * sign for c in (normal.x, normal.y, normal.z)]
        depth = float(obj.Depth.Value)
        return {
            "feature": obj.Name, "label": obj.Label,
            "key": param_key_for(type_key_for(obj.TypeId), "Depth"),
            "value": depth,
            "point": [o + d * depth for o, d in
                      zip((origin.x, origin.y, origin.z), direction)],
            "normal": direction, "factor": 1.0,
        }

    def _helix_drag(self, obj):
        """La flèche d'une hélice volume : au bout de sa hauteur, le long
        de l'axe vertical de son esquisse (``Reversed`` l'inverse). None
        si le mode ne règle pas la hauteur, si elle suit une équation ou
        si l'axe n'est pas celui de l'esquisse."""
        from engine.vocab import param_key_for, type_key_for
        profile = getattr(obj, "Profile", None)
        sketch = profile[0] if profile else None
        axis = getattr(obj, "ReferenceAxis", None)
        mode = str(getattr(obj, "Mode", "")).lower()
        if (sketch is None or sketch.TypeId != "Sketcher::SketchObject"
                or axis is None or axis[0] is not sketch
                or list(axis[1]) != ["V_Axis"]
                or "height" not in mode
                or "Height" in dict(obj.ExpressionEngine or [])):
            return None
        frame = self.sketch_frame(sketch.Name)
        sign = -1 if getattr(obj, "Reversed", False) else 1
        direction = [c * sign for c in frame["vaxis"]]
        height = float(obj.Height.Value)
        return {
            "feature": obj.Name, "label": obj.Label,
            "key": param_key_for(type_key_for(obj.TypeId), "Height"),
            "value": height,
            "point": [c + d * height for c, d in
                      zip(frame["center"], direction)],
            "normal": direction, "factor": 1.0,
        }
