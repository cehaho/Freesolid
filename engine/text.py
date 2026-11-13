"""Gravure de texte : police, solide des glyphes, réédition.

Mixin de ``Kernel``. Pas d'import FreeCAD au niveau du module :
les méthodes importent le noyau à l'appel, pour éviter un cycle.
"""

class TextMixin:
    # -- gravure de texte -------------------------------------------------

    _TEXT_PROPS = (
        ("FreeSolidTextString", "App::PropertyString"),
        ("FreeSolidTextSize", "App::PropertyFloat"),
        ("FreeSolidTextDepth", "App::PropertyFloat"),
        ("FreeSolidTextX", "App::PropertyFloat"),
        ("FreeSolidTextY", "App::PropertyFloat"),
        ("FreeSolidTextEmboss", "App::PropertyBool"),
        ("FreeSolidTextFont", "App::PropertyString"),
        ("FreeSolidTextPlacement", "App::PropertyPlacement"),
    )

    def _find_font(self, font=None):
        from engine.kernel import (
            KernelError,
            fonts,
        )
        if font:
            # Police fournie par le client : jail. Les polices système
            # (engine/fonts.py) ne passent pas par resolve_user_path.
            return self._user_path(font, (".ttf", ".otf"), must_exist=True)
        dirs = fonts.font_dirs()
        found = fonts.find_font(dirs)
        if found:
            return found
        raise KernelError(
            "aucune police .ttf sur ce système (cherché dans {}) — "
            "passez font=/chemin/vers/police.ttf".format(", ".join(dirs)))

    def _build_text_solid(self, text, base, size, depth, emboss, x, y,
                          font=None):
        """Solide des glyphes, posé par ``base`` (placement sur la face).

        Géométrie pure — ne touche pas au document, donc un échec (police,
        texte vide) ne laisse aucune trace.
        """
        from engine.kernel import KernelError
        import Part
        App = self._app()
        text = str(text)
        if not text.strip():
            raise KernelError("texte vide")
        normal = base.Rotation.multVec(App.Vector(0, 0, 1))
        chars = Part.makeWireString(text, self._find_font(font),
                                    float(size), 0)
        glyph_faces = []
        for char_wires in chars:
            if not char_wires:
                continue
            # FaceMakerBullseye : contours + trous de police correctement
            # orientés. Part.Face(wires) sortait des faces d'aire NÉGATIVE
            # (solides retournés, booléens invalides — la gravure « AB »
            # sur plaque 60×20 rendait un corps de 17 mm³, vu P032).
            try:
                glyph_faces.append(
                    Part.makeFace(char_wires, "Part::FaceMakerBullseye"))
            except Exception:
                for wire in char_wires:
                    glyph_faces.append(Part.Face(wire))
        if not glyph_faces:
            raise KernelError("la police n'a rien produit pour ce texte")
        compound = Part.makeCompound(glyph_faces)
        box = compound.BoundBox
        compound.translate(App.Vector(
            -(box.XMin + box.XMax) / 2 + float(x),
            -(box.YMin + box.YMax) / 2 + float(y), 0))
        compound.Placement = base.multiply(compound.Placement)
        margin = 0.2
        if emboss:
            vector = normal * float(depth)
        else:
            # dépasse légèrement la surface pour une coupe franche
            compound.translate(normal * margin)
            vector = normal * (-(float(depth) + margin))
        solids = [f.extrude(vector) for f in compound.Faces]
        text_solid = solids[0]
        for solid in solids[1:]:
            text_solid = text_solid.fuse(solid)
        return text_solid

    def _text_placement(self, face):
        """Le repère du texte sur une face : son centre, sa normale."""
        App = self._app()
        u0, u1, v0, v1 = face.ParameterRange
        normal = face.normalAt((u0 + u1) / 2, (v0 + v1) / 2).normalize()
        return App.Placement(face.CenterOfMass,
                             App.Rotation(App.Vector(0, 0, 1), normal))

    def _text_face(self, obj):
        """La face d'appui d'un texte, en id sur sa base (la pièce à son
        rang) : celle dont le plan porte son repère, face à face, la plus
        proche de son centre. None si aucune ne le porte plus."""
        App = self._app()
        shape = getattr(getattr(obj, "BaseFeature", None), "Shape", None)
        if shape is None or shape.isNull():
            return None
        place = obj.FreeSolidTextPlacement
        normal = place.Rotation.multVec(App.Vector(0, 0, 1))
        tolerance = 1e-6 * max(1.0, shape.BoundBox.DiagonalLength)
        best = None
        for index, face in enumerate(shape.Faces):
            try:
                u0, u1, v0, v1 = face.ParameterRange
                along = face.normalAt((u0 + u1) / 2, (v0 + v1) / 2)
                center = face.CenterOfMass
            except Exception:  # noqa: BLE001
                continue
            if along.dot(normal) < 1 - 1e-6:
                continue
            if abs((place.Base - center).dot(normal)) > tolerance:
                continue
            gap = (place.Base - center).Length
            if best is None or gap < best[0]:
                best = (gap, index)
        return best[1] if best else None

    def _mark_text_tool(self, obj):
        """Artefact interne d'une gravure : caché de l'arbre et du viewport."""
        if "FreeSolidTextTool" not in obj.PropertiesList:
            obj.addProperty("App::PropertyBool", "FreeSolidTextTool",
                            "FreeSolid", "Outil interne d'une gravure")
        obj.FreeSolidTextTool = True

    def add_text(self, text, face, size=8.0, depth=1.0, x=0.0, y=0.0,
                 emboss=False, font=None):
        """Gravure (ou bossage) de texte sur une face plane — marquage de
        pièces. Le texte devient un corps outil combiné dans l'historique
        (soustraction pour graver, ajout pour embosser). Les paramètres
        sont persistés sur la ligne « Gravure » : rééditables (edit_text)."""
        from engine.kernel import KernelError
        App = self._app()
        body = self._require_body()
        doc = self._require_doc()
        text = str(text)
        faces = body.Shape.Faces
        index = int(face)
        if index < 0 or index >= len(faces):
            raise KernelError("face inconnue : {}".format(face))
        base = self._text_placement(faces[index])
        text_solid = self._build_text_solid(text, base, size, depth,
                                            emboss, x, y, font)
        shape_feature = doc.addObject("Part::Feature", "TextShape")
        shape_feature.Shape = text_solid
        shape_feature.Label = self._t("Forme du texte")
        self._mark_text_tool(shape_feature)
        tool_body = doc.addObject("PartDesign::Body", "TextBody")
        tool_body.Label = self._t("Corps texte")
        tool_body.BaseFeature = shape_feature
        self._mark_text_tool(tool_body)
        doc.recompute()
        try:
            self.add_boolean(tool=tool_body.Name,
                             type="fuse" if emboss else "cut")
        except KernelError:
            for name in (tool_body.Name, shape_feature.Name):
                try:
                    doc.removeObject(name)
                except Exception:
                    pass
            doc.recompute()
            raise
        tip = getattr(body, "Tip", None)
        if tip is not None:
            tip.Label = self._t("{} « {} »").format(
                "Texte en relief" if emboss else "Gravure", text[:15])
            for prop, prop_type in self._TEXT_PROPS:
                if prop not in tip.PropertiesList:
                    tip.addProperty(prop_type, prop, "FreeSolid",
                                    "Paramètre de la gravure")
            tip.FreeSolidTextString = text
            tip.FreeSolidTextSize = float(size)
            tip.FreeSolidTextDepth = float(depth)
            tip.FreeSolidTextX = float(x)
            tip.FreeSolidTextY = float(y)
            tip.FreeSolidTextEmboss = bool(emboss)
            tip.FreeSolidTextFont = str(font or "")
            tip.FreeSolidTextPlacement = base
        return self.get_tree()

    #: Ce que ``set_params`` change d'un texte : les mots de sa création.
    _TEXT_KEYS = ("text", "size", "depth", "x", "y", "face")

    def _set_text_params(self, obj, values):
        """``set_params`` d'un texte : ses cotes, et sa face d'appui
        re-choisie sur la pièce à son rang (``face``, id sur sa base)."""
        from engine.kernel import KernelError, parse_user_number
        for key in values:
            if key not in self._TEXT_KEYS:
                raise KernelError(
                    "propriété non éditable : {}".format(key))
        numbers = {}
        for key in ("size", "depth", "x", "y"):
            if key not in values:
                continue
            value = values[key]
            number = (None if isinstance(value, bool)
                      else parse_user_number(value))
            if number is None:
                raise KernelError("valeur invalide pour {} : {}".format(
                    key, value))
            numbers[key] = number
        return self.edit_text(
            obj.Name, text=values.get("text"), face=values.get("face"),
            **numbers)

    def edit_text(self, feature, text=None, size=None, depth=None,
                  x=None, y=None, face=None):
        """Rééditer une gravure : texte, taille, profondeur, position, et
        sa face d'appui (``face``, id sur sa base : la pièce à son rang).

        La forme des glyphes est reconstruite d'abord (géométrie pure) —
        si elle échoue, la pièce n'est pas modifiée. Les gravures créées
        avant P032 n'ont pas leurs paramètres persistés : refus explicite.
        """
        from engine.kernel import KernelError
        doc = self._require_doc()
        obj = doc.getObject(str(feature))
        if obj is None:
            raise KernelError("fonction inconnue : {}".format(feature))
        if "FreeSolidTextString" not in obj.PropertiesList:
            raise KernelError(
                "cette gravure date d'une version antérieure — "
                "supprimez-la puis recréez le texte")
        tool_body = next(
            (o for o in (getattr(obj, "Group", None) or [])
             if o.TypeId == "PartDesign::Body"), None)
        shape_feature = getattr(tool_body, "BaseFeature", None)
        if tool_body is None or shape_feature is None:
            raise KernelError(
                "gravure incomplète — le corps outil du texte est absent")
        new_text = obj.FreeSolidTextString if text is None else str(text)
        new_size = (obj.FreeSolidTextSize if size is None
                    else float(size))
        new_depth = (obj.FreeSolidTextDepth if depth is None
                     else float(depth))
        new_x = obj.FreeSolidTextX if x is None else float(x)
        new_y = obj.FreeSolidTextY if y is None else float(y)
        if new_size <= 0 or new_depth <= 0:
            raise KernelError(
                "taille et profondeur doivent être positives")
        emboss = bool(obj.FreeSolidTextEmboss)
        base = obj.FreeSolidTextPlacement
        if face is not None:
            shape = getattr(getattr(obj, "BaseFeature", None), "Shape", None)
            faces = shape.Faces if shape is not None else []
            if type(face) is not int or not 0 <= face < len(faces):
                raise KernelError("face inconnue : {}".format(face))
            base = self._text_placement(faces[face])
        text_solid = self._build_text_solid(
            new_text, base, new_size, new_depth, emboss, new_x, new_y,
            obj.FreeSolidTextFont or None)
        old_shape = shape_feature.Shape
        shape_feature.Shape = text_solid
        try:
            self._recompute()
        except KernelError as exc:
            shape_feature.Shape = old_shape
            try:
                self._recompute()
            except KernelError:
                pass
            raise KernelError(
                "{} — la gravure n'a pas été modifiée".format(exc))
        obj.FreeSolidTextString = new_text
        obj.FreeSolidTextSize = new_size
        obj.FreeSolidTextDepth = new_depth
        obj.FreeSolidTextX = new_x
        obj.FreeSolidTextY = new_y
        obj.FreeSolidTextPlacement = base
        obj.Label = self._t("{} « {} »").format(
            "Texte en relief" if emboss else "Gravure", new_text[:15])
        return self.get_tree()
