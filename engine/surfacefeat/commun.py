"""Surfaces — ce que partagent les autres sous-mixins : objets de la
section Surfaces de l'arbre, ajout d'une surface, tampons de réédition
(``_stamp``, ``_surface_spec``), surfaces consommées, recalcul des
formes figées.

Sous-mixin de ``SurfaceMixin`` (voir ``__init__.py``). Pas d'import
FreeCAD au niveau du module : les méthodes importent le noyau à l'appel.
"""


class SurfaceCommonMixin:
    # -- surfaces et courbes ----------------------------------------------

    #: Objets document-level exposés dans la section Surfaces de l'arbre.
    #: Les PartDesign::* dérivent aussi de Part::Feature — filtre exact.
    _SURFACE_TYPE_IDS = frozenset({
        "Part::Feature", "Part::Extrusion", "Part::Revolution",
        "Part::Loft", "Part::Offset", "Part::Face", "Part::Sweep",
        "Surface::Filling", "Surface::Extend", "Surface::GeomFillSurface",
        "Part::RuledSurface", "Part::Fillet", "Part::Section",
        "Part::ProjectOnSurface", "Part::Helix", "Part::Offset2D",
        # Ajuster : la découpe (BOPTools) puis la pièce gardée
        # (CompoundTools) — fonctions Python livrées avec FreeCAD.
        "Part::FeaturePython",
    })

    def _is_surface_obj(self, obj):
        """Surface ou courbe FreeSolid (section Surfaces de l'arbre). Un
        lieur de forme n'en est une que s'il est une courbe composite ou
        une suppression de faces —
        ceux des balayages vivent dans le corps."""
        type_id = getattr(obj, "TypeId", "")
        if type_id == "PartDesign::SubShapeBinder":
            return bool(getattr(obj, "FreeSolidComposite", False)
                        or getattr(obj, "FreeSolidKind", "") == "deleteface")
        if type_id == "Part::Feature" and any(
                getattr(user, "BaseFeature", None) is obj
                for user in getattr(obj, "InList", None) or ()):
            # Forme importée posée en base d'un corps : elle vit dans le
            # corps, pas dans la section Surfaces — sinon elle s'y listait
            # et se dessinait une seconde fois sur le solide.
            return False
        return type_id in self._SURFACE_TYPE_IDS

    #: Propriétés FreeSolid d'une spline 3D (points, interpolée, fermée).
    _CURVE_POINTS = "FreeSolidPoints"

    def _add_surface(self, shape, label):
        """Surface figée (Part::Feature) — couture, courbe 3D, legacy."""
        doc = self._require_doc()
        feature = doc.addObject("Part::Feature", "Surface")
        feature.Shape = shape
        feature.Label = self._t(label)
        doc.recompute()
        return self.get_tree()

    def _add_part_surface(self, type_id, label, configure):
        """Crée un objet Part paramétrique natif ; purge si le recompute
        échoue — pas d'entrée cassée dans l'arbre."""
        from engine.kernel import (
            KernelError,
            _explain,
        )
        doc = self._require_doc()
        obj = doc.addObject(type_id, "Surface")
        obj.Label = self._t(label)
        try:
            configure(obj)
            self._recompute()
        except Exception as exc:  # noqa: BLE001
            try:
                doc.removeObject(obj.Name)
            except Exception:
                pass
            if isinstance(exc, KernelError):
                raise
            raise KernelError(_explain(exc))
        return self.get_tree()

    def _surface_source(self, sketch):
        from engine.kernel import KernelError
        sk = (self._get_sketch(sketch) if sketch is not None
              else self._latest_sketch())
        if not sk.Shape.Edges:
            raise KernelError("l'esquisse est vide")
        return sk

    def _surface_sketch_objects(self, obj):
        """Esquisses sources d'une surface paramétrique Part."""
        sketches = []
        if obj.TypeId == "Part::Extrusion":
            base = getattr(obj, "Base", None)
            if base is not None and base.TypeId == "Sketcher::SketchObject":
                sketches.append(base)
        elif obj.TypeId == "Part::Revolution":
            source = getattr(obj, "Source", None)
            if (source is not None
                    and source.TypeId == "Sketcher::SketchObject"):
                sketches.append(source)
        elif obj.TypeId in ("Part::Loft", "Part::Sweep"):
            for section in getattr(obj, "Sections", None) or []:
                if (section is not None
                        and section.TypeId == "Sketcher::SketchObject"):
                    sketches.append(section)
            spine = None
            if obj.TypeId == "Part::Sweep":
                spine = getattr(obj, "Spine", None)
            if isinstance(spine, tuple):
                spine = spine[0]
            if (spine is not None
                    and spine.TypeId == "Sketcher::SketchObject"):
                sketches.append(spine)
        elif obj.TypeId == "Part::ProjectOnSurface":
            for source in getattr(obj, "Projection", None) or []:
                if isinstance(source, tuple):  # lien (objet, éléments)
                    source = source[0]
                if (source is not None
                        and source.TypeId == "Sketcher::SketchObject"):
                    sketches.append(source)
        elif obj.TypeId == "Part::Face":
            for source in getattr(obj, "Sources", None) or []:
                if (source is not None
                        and source.TypeId == "Sketcher::SketchObject"):
                    sketches.append(source)
        return sketches

    def _surface_tree_entry(self, obj, order_of=None, known_names=None,
                            consumed=None):
        """Entrée d'arbre d'une surface.

        ``known_names`` : noms des nœuds dessinables du payload, pour
        filtrer les arêtes comme le fait ``entry()`` côté fonctions. Passé
        par l'appelant — ne pas le recalculer par surface.
        """
        from engine.kernel import label_for_type
        from engine.vocab import type_key_for
        sketches = self._surface_sketch_objects(obj)
        order_of = order_of if order_of is not None else {}
        known_names = known_names if known_names is not None else set()

        def wire(item, source):
            return self._annotate_tree_links(item, source, known_names)

        entry = {
            "name": obj.Name,
            "label": obj.Label,
            "type": obj.TypeId,
            "type_key": type_key_for(obj.TypeId),
            "sketches": [sk.Name for sk in sketches],
            "order": order_of.get(obj.Name, -1),
            "has_params": self._has_params(obj),
            "suppressible": self._is_suppressible(obj),
        }
        wire(entry, obj)
        # Couture / courbe / fichiers legacy : pas d'objet paramétrique.
        if obj.TypeId == "Part::Feature":
            entry["static"] = True
        curve = self._curve_spec(obj)
        if curve is not None:
            # Spline 3D : figée pour set_params, rééditable par ses points.
            entry["curve"] = curve
        sketch3d = self._sketch3d_spec(obj)
        if sketch3d is not None:
            entry["sketch3d"] = sketch3d
        spec = self._surface_spec(obj)
        if spec is not None:
            entry["surface"] = spec
        if consumed is not None and obj.Name in consumed:
            entry["consumed"] = True
        graph = self._tree_graph_payload(obj)
        if graph is not None:
            entry["graph"] = graph
        if sketches:
            entry["children"] = [wire({
                "name": sk.Name,
                "label": sk.Label,
                "kind": label_for_type(sk.TypeId, self.lang),
                "type": sk.TypeId,
                "type_key": type_key_for(sk.TypeId),
                "error": "Invalid" in (sk.State or ()),
                "order": order_of.get(sk.Name, -1),
                "definition": self._sketch_definition(sk),
            }, sk) for sk in sketches]
        entry["rolled_back"] = self._is_rolled_back(obj)
        return entry

    def _stamp(self, obj, **values):
        """Paramètres FreeSolid rangés sur l'objet (relecture, réédition)."""
        for key, value in values.items():
            prop = "FreeSolid" + key.capitalize()
            if prop not in obj.PropertiesList:
                kind = ("App::PropertyFloat" if isinstance(value, float)
                        else "App::PropertyInteger" if isinstance(value, int)
                        else "App::PropertyString")
                obj.addProperty(kind, prop, "FreeSolid")
                obj.setEditorMode(prop, 2)
            setattr(obj, prop, value)

    @staticmethod
    def _mark_internal(obj):
        """Objet de service (découpe d'un ajustement, demi-espace d'une
        coupe par surface) : hors arbre."""
        obj.addProperty("App::PropertyBool", "FreeSolidSurfaceTool",
                        "FreeSolid")
        obj.setEditorMode("FreeSolidSurfaceTool", 2)
        obj.FreeSolidSurfaceTool = True

    def _surface_spec(self, obj):
        """Paramètres rééditables des surfaces FreeSolid à panneau dédié."""
        if obj.TypeId == "Surface::Extend" and getattr(
                obj, "FreeSolidUntrim", 0):
            face = getattr(obj, "Face", None)
            subs = face[1] if face else ()
            # Ce que la réédition re-choisit : la surface et sa face.
            return {"kind": "untrim",
                    "source": face[0].Name if face else None,
                    "face": int(subs[0][4:]) - 1 if subs else 0}
        if obj.TypeId == "Part::Fillet":
            edges = list(getattr(obj, "Edges", ()) or ())
            base = getattr(obj, "Base", None)
            return {"kind": "fillet",
                    "radius": float(edges[0][1]) if edges else 0.0,
                    # Ce que la réédition re-choisit : la surface, ses
                    # arêtes (base 0, comme les arêtes de la vue).
                    "source": base.Name if base is not None else None,
                    "edges": [int(edge[0]) - 1 for edge in edges]}
        if obj.TypeId == "Surface::Extend":
            face = getattr(obj, "Face", None)
            return {"kind": "extend",
                    "source": face[0].Name if face else None,
                    "distance": float(getattr(obj, "FreeSolidDistance", 0)),
                    "edge": (int(getattr(obj, "FreeSolidEdge", 0)) - 1
                             if getattr(obj, "FreeSolidEdge", 0) else None)}
        if getattr(obj, "FreeSolidKind", "") == "split":
            base = getattr(obj, "Base", None)
            tools = list(getattr(obj, "Tools", None) or ())
            return {"kind": "split",
                    "source": base.Name if base is not None else None,
                    "tool": tools[0].Name if tools else None}
        if getattr(obj, "FreeSolidKind", "") == "deleteface":
            support = list(getattr(obj, "Support", None) or ())
            src, subs = support[0] if support else (None, ())
            kept = {int(sub[4:]) - 1 for sub in subs or ()
                    if str(sub).startswith("Face")}
            count = len(src.Shape.Faces) if src is not None else 0
            # Les faces supprimées (base 0) : le lieur garde les autres.
            return {"kind": "deleteface",
                    "source": src.Name if src is not None else None,
                    "faces": [i for i in range(count) if i not in kept]}
        if getattr(obj, "FreeSolidKind", "") == "trim":
            base = getattr(obj, "Base", None)
            point = self._trim_point(obj)
            return {"kind": "trim",
                    "source": base.Base.Name if base is not None else None,
                    "tool": (base.Tools[0].Name
                             if base is not None and base.Tools else None),
                    # Un point de la partie gardée : la zone le montre.
                    "point": ([round(v, 6) for v in point]
                              if point is not None else None)}
        if getattr(obj, "FreeSolidSources", ""):
            # Couture : ses surfaces, que la réédition re-choisit.
            return {"kind": "sew", "surfaces": [
                n for n in str(obj.FreeSolidSources).split(";") if n]}
        if getattr(obj, "FreeSolidMidbase", ""):
            # Médiane : ses deux faces (base 0, sur la fonction d'avant),
            # ou toutes les parois plus minces qu'une épaisseur.
            spec = str(getattr(obj, "FreeSolidMidfaces", ""))
            if spec.startswith("auto:"):
                return {"kind": "mid", "auto": True,
                        "thickness": float(spec[5:])}
            return {"kind": "mid",
                    "faces": [int(f) for f in spec.split(";") if f]}
        if getattr(obj, "FreeSolidCapedges", ""):
            doc = self._require_doc()
            links = []
            for item in str(obj.FreeSolidCapedges).split(";"):
                name, edge, _ = (item.split(":") + ["", ""])[:3]
                links.append((doc.getObject(name), edge))
            return {"kind": "fill", "cap": True,
                    "boundary": self._link_items(links)}
        if getattr(obj, "FreeSolidFreemoves", ""):
            src = self._require_doc().getObject(
                str(getattr(obj, "FreeSolidFreesource", "")))
            stamps = self._frozen_stamps(obj)
            moves = (self._followed_moves(src.Shape, stamps)
                     if src is not None and getattr(src, "Shape", None)
                     else self._free_moves(stamps))
            return {"kind": "freeform", "moves": moves,
                    "grid": int(getattr(obj, "FreeSolidFreegrid", 6)),
                    "source": str(getattr(obj, "FreeSolidFreesource", "")),
                    "face": int(getattr(obj, "FreeSolidFreeface", 0))}
        if getattr(obj, "FreeSolidFreesource", ""):
            pushes = self._free_pushes(self._frozen_stamps(obj))
            return {"kind": "freeform", "pushes": pushes,
                    "height": pushes[0][3],
                    "radius": float(obj.FreeSolidFreeradius),
                    "keep_edges": bool(getattr(obj, "FreeSolidFreeedges", 0)),
                    "source": str(obj.FreeSolidFreesource)}
        if getattr(obj, "FreeSolidFlatsource", ""):
            src = self._require_doc().getObject(str(obj.FreeSolidFlatsource))
            face = int(getattr(obj, "FreeSolidFlatface", 0))
            if src is not None and getattr(src, "Shape", None):
                face = self._followed_flat_face(src.Shape,
                                                self._frozen_stamps(obj))
            spec = {"kind": "flatten", "face": face,
                    "surface": str(obj.FreeSolidFlatsource)}
            spec.update(self._flat_distortion(obj))
            return spec
        if (obj.TypeId == "Part::Offset"
                and not getattr(obj, "FreeSolidSurfaceTool", False)):
            value = getattr(obj, "Value", 0.0)
            source = getattr(obj, "Source", None)
            # Décalage (une peau) ou épaississement (un solide) : sa
            # distance signée et sa surface.
            return {"kind": "thicken" if getattr(obj, "Fill", False)
                    else "offset",
                    "distance": float(getattr(value, "Value", value)),
                    "source": source.Name if source is not None else None}
        if obj.TypeId == "Part::Face":
            sources = list(getattr(obj, "Sources", None) or ())
            return {"kind": "planar",
                    "sketch": sources[0].Name if sources else None}
        if obj.TypeId == "Part::Section":
            base, tool = obj.Base, obj.Tool
            solid = tool is not None and tool.TypeId == "PartDesign::Body"
            return {"kind": "intersection",
                    "first": base.Name if base is not None else None,
                    "second": (tool.Name if tool is not None and not solid
                               else None),
                    "body": solid}
        if obj.TypeId == "Part::ProjectOnSurface":
            support = obj.SupportFace
            sketches = self._surface_sketch_objects(obj)
            subs = support[1] if support else ()
            return {"kind": "project",
                    "sketch": sketches[0].Name if sketches else None,
                    "surface": support[0].Name if support else None,
                    "face": int(subs[0][4:]) - 1 if subs else 0}
        binder = self._radiate_binder(obj)
        if binder is not None:
            # Surface radiée : sa distance signée et son contour, arête par
            # arête (base 0 ; ``body`` : une arête du solide).
            value = getattr(obj, "Value", 0.0)
            return {"kind": "radiate",
                    "distance": float(getattr(value, "Value", value)),
                    "boundary": self._link_items(binder.Support)}
        if obj.TypeId == "Surface::Filling":
            edges = list(getattr(obj, "BoundaryEdges", None) or ())
            return {"kind": "fill", "edges": len(edges),
                    "boundary": self._link_items(edges)}
        # Ce que prennent les surfaces lissée, balayée, réglée, frontière et
        # la courbe composite : la réédition le re-choisit.
        # Profils et trajectoire : comme ceux d'un lissage ou d'un balayage
        # de volume (``swept`` de l'arbre), nom et libellé.
        if obj.TypeId == "Part::Loft":
            return {"kind": "loft", "profiles": [
                self._swept_entry(sk)
                for sk in getattr(obj, "Sections", None) or ()]}
        if obj.TypeId == "Part::Sweep":
            sections = list(getattr(obj, "Sections", None) or ())
            spine = getattr(obj, "Spine", None)
            return {"kind": "sweep",
                    "profile": (self._swept_entry(sections[0])
                                if sections else None),
                    "spine": self._swept_entry(spine[0]) if spine else None}
        if obj.TypeId == "Part::RuledSurface":
            return {"kind": "ruled", "boundary": self._link_items(
                [getattr(obj, "Curve1", None), getattr(obj, "Curve2", None)])}
        if obj.TypeId == "Surface::GeomFillSurface":
            return {"kind": "boundary", "boundary": self._link_items(
                getattr(obj, "BoundaryList", None))}
        if getattr(obj, "FreeSolidComposite", False):
            return {"kind": "composite", "boundary": self._link_items(
                getattr(obj, "Support", None))}
        return None

    @staticmethod
    def _swept_entry(obj):
        """Un profil ou une trajectoire : son nom, son libellé ; ``curve``
        pour une courbe 3D (pas une esquisse)."""
        entry = {"name": obj.Name, "label": obj.Label}
        if obj.TypeId != "Sketcher::SketchObject":
            entry["curve"] = True
        return entry

    def _link_items(self, links):
        """Les arêtes d'une liste de liens ``(objet, sous-éléments)``, comme
        la zone d'un contour les montre : ``{name, edge}`` (base 0), ou
        ``{body: True, edge}`` pour une arête du solide. Une moitié d'arête
        fermée (l'objet auxiliaire d'un remplissage) revient à son arête."""
        doc = self._require_doc()
        items = []
        for link in links or ():
            if not link or link[0] is None:
                continue
            linked, subs = link[0], link[1] if len(link) > 1 else ()
            if isinstance(subs, str):
                subs = [subs]
            source = getattr(linked, "FreeSolidHalvessource", "")
            for sub in subs or ():
                owner = linked
                if source:
                    owner = doc.getObject(source)
                    sub = linked.FreeSolidHalvesedge
                if owner is None or not str(sub).startswith("Edge"):
                    continue
                edge = int(sub[4:]) - 1
                item = ({"body": True, "edge": edge}
                        if owner.TypeId == "PartDesign::Body"
                        else {"name": owner.Name, "edge": edge})
                if item not in items:
                    items.append(item)
        return items

    @staticmethod
    def _radiate_binder(obj):
        """Le lieur caché qui porte le contour d'une surface radiée, ou
        None."""
        binder = (getattr(obj, "Source", None)
                  if obj.TypeId == "Part::Offset2D" else None)
        if (binder is None or binder.TypeId != "PartDesign::SubShapeBinder"
                or not getattr(binder, "FreeSolidSurfaceTool", False)):
            return None
        return binder

    def _refresh_frozen_shapes(self):
        """Recalcule les formes figées qui dépendent d'une fonction du
        corps (supprimer, remplacer une face) ; vrai si l'une a changé."""
        doc = self._require_doc()
        changed = False
        for obj in doc.Objects:
            if self._sketch3d_spec(obj) is not None:
                changed = self._refresh_sketch3d(obj) or changed
                continue
            curve = self._curve_spec(obj)
            if curve is not None and any(curve.get("links") or ()):
                try:
                    points, links = self._resolve_links(curve["points"],
                                                        curve["links"])
                    points = self.solve_curve_rules(
                        points, curve.get("rules"),
                        [i for i, l in enumerate(links) if l])
                except Exception:  # noqa: BLE001
                    continue
                if any(abs(a - b) > 1e-9 for p, q in zip(points,
                                                           curve["points"])
                       for a, b in zip(p, q)):
                    vectors, shape = self._curve_shape(
                        points, curve["spline"], curve["closed"],
                        curve.get("tangents"))
                    self._store_curve(obj, vectors, curve["spline"],
                                      curve["closed"])
                    obj.Shape = shape
                    changed = True
                continue
            sew_sources = getattr(obj, "FreeSolidSources", "")
            if sew_sources:
                sources = [doc.getObject(n) for n in
                           str(sew_sources).split(";") if n]
                if any(s is None or not getattr(s, "Shape", None)
                       for s in sources):
                    continue
                try:
                    result = self._sew_shape([s.Shape for s in sources])
                except Exception:  # noqa: BLE001
                    continue
                old = obj.Shape
                if (old.isNull() or abs(old.Area - result.Area) > 1e-9
                        or (old.BoundBox.Center - result.BoundBox.Center)
                        .Length > 1e-9):
                    obj.Shape = result
                    changed = True
                continue
            cap_spec = getattr(obj, "FreeSolidCapedges", "")
            if cap_spec:
                try:
                    result = self._cap_shape(cap_spec)
                except Exception:  # noqa: BLE001
                    continue
                old = obj.Shape
                if (old.isNull() or abs(old.Area - result.Area) > 1e-9
                        or (old.BoundBox.Center - result.BoundBox.Center)
                        .Length > 1e-9):
                    obj.Shape = result
                    changed = True
                continue
            halves = getattr(obj, "FreeSolidHalvessource", "")
            if halves:
                src = doc.getObject(halves)
                if src is None or not getattr(src, "Shape", None):
                    continue
                try:
                    result = self._halves_shape(src.Shape,
                                                obj.FreeSolidHalvesedge,
                                                obj.FreeSolidHalvesface)
                except Exception:  # noqa: BLE001
                    continue
                old = obj.Shape
                if (old.isNull() or abs(old.Length - result.Length) > 1e-9
                        or (old.BoundBox.Center - result.BoundBox.Center)
                        .Length > 1e-9):
                    obj.Shape = result
                    changed = True
                continue
            free_src = (getattr(obj, "FreeSolidFlatsource", "")
                        or getattr(obj, "FreeSolidFreesource", ""))
            if free_src:
                src = doc.getObject(free_src)
                if src is None or not getattr(src, "Shape", None):
                    continue
                try:
                    if getattr(obj, "FreeSolidFlatsource", ""):
                        result = self._flat_shape(
                            src.Shape, self._followed_flat_face(
                                src.Shape, self._frozen_stamps(obj)))
                    else:
                        result = self._free_shape(src.Shape,
                                                  self._frozen_stamps(obj))
                except Exception:  # noqa: BLE001
                    continue
                old = obj.Shape
                if (old.isNull() or abs(old.Area - result.Area) > 1e-6
                        or (old.BoundBox.Center - result.BoundBox.Center)
                        .Length > 1e-6):
                    obj.Shape = result
                    self._follow_free_faces(obj, src.Shape)
                    changed = True
                continue
            mid_base = getattr(obj, "FreeSolidMidbase", "")
            if mid_base:
                base = doc.getObject(mid_base)
                if base is None or not getattr(base, "Shape", None):
                    continue
                try:
                    result = self._mid_from_spec(base.Shape,
                                                 obj.FreeSolidMidfaces)
                except Exception:  # noqa: BLE001
                    continue
                old = obj.Shape
                if (old.isNull() or abs(old.Area - result.Area) > 1e-9
                        or (old.BoundBox.Center - result.BoundBox.Center)
                        .Length > 1e-9):
                    obj.Shape = result
                    changed = True
                continue
            base_name = (getattr(obj, "FreeSolidDefeatbase", "")
                         or getattr(obj, "FreeSolidReplacebase", "")
                         or getattr(obj, "FreeSolidVchamferbase", ""))
            if not base_name:
                continue
            base = doc.getObject(base_name)
            # La forme part de la fonction juste avant la sienne : une
            # fonction glissée avant elle (sous la barre reculée) y entre.
            chain = self._frozen_chain_base(obj)
            if chain is not None and chain is not base:
                stamps = self._rebase_frozen(obj, base, chain)
                base = chain
                changed = True
            elif getattr(obj, "FreeSolidVchamferbase", ""):
                stamps = {"vchamfer": obj.FreeSolidVchamfer}
            elif getattr(obj, "FreeSolidDefeatbase", ""):
                stamps = {"defeatfaces": obj.FreeSolidDefeatfaces}
            else:
                stamps = {"replaceface": obj.FreeSolidReplaceface,
                          "replacesurface": obj.FreeSolidReplacesurface}
            if base is None or not getattr(base, "Shape", None):
                continue
            try:
                result = self._frozen_result(stamps, base.Shape)
            except Exception:  # noqa: BLE001
                continue  # l'ancienne forme reste ; l'erreur se verra
            old = obj.Shape
            if (old.isNull() or len(old.Faces) != len(result.Faces)
                    or abs(old.Volume - result.Volume) > 1e-9
                    or abs(old.Area - result.Area) > 1e-9):
                obj.Shape = result
                changed = True
        return changed

    def _consumed_surfaces(self, counts=None):
        """Noms des surfaces remplacées par une autre : source d'un
        ajustement, d'un prolongement, d'un épaississement ou d'une
        couture. Elles restent dans l'historique, plus dans la vue.
        ``counts(objet)`` : les remplaçantes qui comptent — par défaut,
        celles au-dessus de la barre."""
        consumed = set()
        for obj in self._require_doc().Objects:
            if (not counts(obj) if counts is not None
                    else self._is_rolled_back(obj)):
                continue
            if obj.TypeId == "Surface::Extend":
                face = getattr(obj, "Face", None)
                if face:
                    consumed.add(face[0].Name)
            elif obj.TypeId == "Part::Fillet":
                base = getattr(obj, "Base", None)
                if base is not None:
                    consumed.add(base.Name)
            elif getattr(obj, "FreeSolidKind", "") == "deleteface":
                for link in getattr(obj, "Support", None) or []:
                    consumed.add(link[0].Name)
            elif getattr(obj, "FreeSolidKind", "") == "trim":
                base = getattr(obj, "Base", None)
                if base is not None and getattr(base, "Base", None):
                    consumed.add(base.Base.Name)
            elif getattr(obj, "FreeSolidKind", "") == "split":
                base = getattr(obj, "Base", None)
                if base is not None:
                    consumed.add(base.Name)
            elif (obj.TypeId == "Part::Offset" and getattr(obj, "Fill", False)
                  and not getattr(obj, "FreeSolidSurfaceTool", False)):
                source = getattr(obj, "Source", None)
                if source is not None:
                    consumed.add(source.Name)
            if (obj.TypeId == "Part::Extrusion"
                    and getattr(obj, "FreeSolidSurfaceTool", False)):
                # Demi-espace d'une coupe par surface : la surface a servi.
                base = getattr(obj, "Base", None)
                if base is not None:
                    consumed.add(base.Name)
            pushed = getattr(obj, "FreeSolidFreesource", "")
            if pushed:
                consumed.add(pushed)
            replacing = getattr(obj, "FreeSolidReplacesurface", "")
            if replacing:
                # Surface d'un remplacement de face : la pièce la porte.
                consumed.add(replacing)
            for name in str(getattr(obj, "FreeSolidSources", "")).split(";"):
                if name:
                    consumed.add(name)
        return consumed

    def _get_surface(self, name):
        from engine.kernel import KernelError
        obj = self._require_doc().getObject(str(name))
        if obj is None or not self._is_surface_obj(obj):
            raise KernelError("surface inconnue : {}".format(name))
        return obj
