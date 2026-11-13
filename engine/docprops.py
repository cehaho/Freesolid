"""Commentaires des fonctions, propriétés du fichier, historique
d'annulation, corps et surfaces masqués, fonctions désactivées, liste
des erreurs de reconstruction.

Les propriétés du document (``docoptions`` : décimales, grille, qualité
d'image) partent aussi avec le fichier.

Un commentaire est une note libre posée sur une fonction (propriété
cachée ``FreeSolidComment``) : l'arbre la montre en infobulle. Les
propriétés du fichier reprennent celles du document FreeCAD (auteur,
société, description) et ses propriétés libres (``Meta``) ; elles
partent avec le .FCStd. Les imports FreeCAD restent dans les méthodes ;
``undo_steps``, ``session_steps``, ``transaction_name``, ``body_before``
et ``clean_meta`` sont testées en CI.
"""

#: Drapeau « désactivé » d'une ligne sans ``Suppressed`` (surface,
#: référence, esquisse emportée).
_DISABLED_PROP = "FreeSolidSuppressed"
#: La ligne désactivée par l'utilisateur qui a emporté celle-ci.
_DISABLED_BY_PROP = "FreeSolidSuppressedBy"

#: Préfixe des transactions ouvertes par ``dispatch`` (kernel.py).
_PREFIX = "freesolid-"
#: Marque, après le nom de l'op, de la session d'esquisse en cours.
_SESSION = "@"
#: Marque, entre l'op et la session, du corps actif avant l'op.
_BODY = "#"


def transaction_name(op, session=None, body=None):
    """Le nom de la transaction d'une op : « freesolid-<op> », suivi de
    « #<corps> », le corps actif avant l'op, que Ctrl+Z rend
    (``body_before``), puis de « @<n> » pendant la session d'esquisse
    numéro ``n`` — Ctrl+Z, dans l'esquisse, ne défait que les pas qui la
    portent (session_steps)."""
    return (_PREFIX + op + ("{}{}".format(_BODY, body) if body else "")
            + ("{}{}".format(_SESSION, session) if session else ""))


def undo_steps(names):
    """Noms de transactions → noms d'ops, du plus récent au plus ancien
    (l'ordre de FreeCAD). Une transaction étrangère garde son nom."""
    return [name[len(_PREFIX):].split(_SESSION)[0].split(_BODY)[0]
            if name.startswith(_PREFIX) else name
            for name in names or ()]


def body_before(name):
    """Le corps actif avant l'op de la transaction ``name``, ou None."""
    name = str(name or "")
    if not name.startswith(_PREFIX):
        return None
    head = name[len(_PREFIX):].split(_SESSION)[0]
    return head.partition(_BODY)[2] or None


def session_steps(names, session):
    """Combien des pas ``names`` (du plus récent au plus ancien) sont ceux
    de la session d'esquisse ``session`` : ceux de tête qui la portent."""
    mark = "{}{}".format(_SESSION, session)
    count = 0
    for name in names or ():
        if not (name.startswith(_PREFIX) and name.endswith(mark)):
            break
        count += 1
    return count


def clean_meta(meta):
    """Propriétés libres valides : noms non vides, sans doublon ; une
    valeur vide retire la propriété."""
    out = {}
    for key, value in (meta or {}).items():
        key = str(key).strip()
        value = str(value if value is not None else "").strip()
        if key and value:
            out[key] = value
    return out


#: Champs fixes du panneau → propriété du document FreeCAD.
_DOC_FIELDS = {"author": "CreatedBy", "company": "Company",
               "description": "Comment"}


class DocPropsMixin:
    """Ops : commentaires, propriétés du fichier, historique."""

    def set_comment(self, feature, text=""):
        """Pose (ou retire, texte vide) le commentaire d'une fonction."""
        from engine.kernel import KernelError
        doc = self._require_doc()
        obj = doc.getObject(feature)
        if obj is None:
            raise KernelError("fonction inconnue : {}".format(feature))
        text = str(text or "").strip()
        if "FreeSolidComment" not in obj.PropertiesList:
            if not text:
                return self._current_tree()
            obj.addProperty("App::PropertyString", "FreeSolidComment",
                            "FreeSolid")
            obj.setEditorMode("FreeSolidComment", 2)
        obj.FreeSolidComment = text
        return self._current_tree()

    def _annotate_comments(self, items):
        """Ajoute ``comment`` aux lignes d'arbre (et à leurs enfants)."""
        for item in items or ():
            obj = self._doc.getObject(item.get("name", ""))
            text = getattr(obj, "FreeSolidComment", "") if obj else ""
            if text:
                item["comment"] = text
            self._annotate_comments(item.get("children"))

    def document_properties(self):
        """Propriétés du fichier : champs fixes et propriétés libres."""
        doc = self._require_doc()
        out = {key: str(getattr(doc, prop, "") or "")
               for key, prop in _DOC_FIELDS.items()}
        out["custom"] = dict(getattr(doc, "Meta", {}) or {})
        return out

    def set_document_properties(self, values):
        """Remplace les propriétés du fichier : ``values`` porte les
        champs fixes (absents : inchangés) et ``custom`` (toutes les
        propriétés libres)."""
        doc = self._require_doc()
        for key, prop in _DOC_FIELDS.items():
            if key in values:
                setattr(doc, prop, str(values[key] or "").strip())
        if "custom" in values:
            doc.Meta = clean_meta(values["custom"])
        return self.document_properties()

    def document_options(self):
        """Propriétés du document (``docoptions``) : décimales, grille,
        qualité d'image — gardées dans le fichier."""
        from engine import docoptions
        doc = self._require_doc()
        return docoptions.normalize(getattr(doc, "FreeSolidOptions", ""))

    def set_document_options(self, values):
        """Change les propriétés du document données dans ``values`` (les
        autres restent). Une clé inconnue ou une valeur hors bornes est
        refusée, rien n'est changé. Hors de l'historique d'annulation,
        comme les propriétés du fichier."""
        import json
        from engine import docoptions
        doc = self._require_doc()
        options = docoptions.merge(getattr(doc, "FreeSolidOptions", ""), values)
        if "FreeSolidOptions" not in doc.PropertiesList:
            doc.addProperty("App::PropertyString", "FreeSolidOptions", "FreeSolid",
                            "Propriétés du document FreeSolid (JSON)")
        doc.FreeSolidOptions = json.dumps(options, sort_keys=True)
        return options

    def _display_mesh(self):
        """La qualité d'image du document : (écart des faces, angle ou
        None, écart des arêtes) — ``docoptions.mesh_settings``."""
        from engine import docoptions
        return docoptions.mesh_settings(
            getattr(self._require_doc(), "FreeSolidOptions", ""))

    @staticmethod
    def _is_hidden(obj):
        return bool(getattr(obj, "FreeSolidHidden", False))

    def set_hidden(self, objects, hidden=True, solid=None):
        """Masque (ou affiche) des corps ou des surfaces : ils restent dans
        la pièce et dans l'arbre, la vue ne les dessine plus. Enregistré
        dans le fichier. ``solid`` : un seul des solides d'un corps qui en
        garde plusieurs (``objects`` ne nomme alors que ce corps)."""
        from engine.kernel import KernelError
        doc = self._require_doc()
        targets = []
        for name in objects or ():
            obj = doc.getObject(str(name))
            if obj is None or not (obj.TypeId == "PartDesign::Body"
                                   or self._is_surface_obj(obj)):
                raise KernelError("corps ou surface inconnu : {}".format(name))
            targets.append(obj)
        if not targets:
            raise KernelError("choisissez un corps ou une surface")
        if solid is not None:
            if len(targets) != 1 or targets[0].TypeId != "PartDesign::Body":
                raise KernelError("un solide se règle dans un seul corps")
            body = targets[0]
            if self._is_hidden(body):
                # Masqué en entier : chaque solide le devient, puis
                # celui-ci change seul.
                for other in range(len(body.Shape.Solids)):
                    self._set_solid(body, other, hidden=True)
                body.FreeSolidHidden = False
            self._set_solid(body, solid, hidden=bool(hidden))
            return self._current_tree()
        for obj in targets:
            if "FreeSolidHidden" not in obj.PropertiesList:
                if not hidden:
                    continue
                obj.addProperty("App::PropertyBool", "FreeSolidHidden",
                                "FreeSolid")
                obj.setEditorMode("FreeSolidHidden", 2)
            obj.FreeSolidHidden = bool(hidden)
        return self._current_tree()

    def _is_suppressible(self, obj):
        """Ce que « Désactiver » accepte : une fonction de corps PartDesign
        (``Suppressed``), une surface ou une courbe, une référence (plan,
        axe, point, repère). Les deux dernières n'ont pas ``Suppressed``
        dans FreeCAD : elles portent ``FreeSolidSuppressed``. L'arbre le
        dit (``suppressible``), le menu le suit."""
        if obj is None:
            return False
        if "Suppressed" in getattr(obj, "PropertiesList", ()):
            return True
        if self._is_internal_tool(obj):
            return False
        if not (self._is_surface_obj(obj) or self._is_reference(obj)):
            return False
        # Réseau de corps, suppression de corps : leurs étapes cachées
        # sont des fonctions de corps, pas encore désactivées avec eux.
        return not any(obj is host for host in self._removal_hosts()) \
            and not any(obj is host for host in self._body_pattern_hosts())

    def _is_disabled(self, obj):
        """Désactivée : ``Suppressed`` d'une fonction de corps, ou le
        drapeau d'une surface, d'une référence, d'une esquisse."""
        if obj is None:
            return False
        if "Suppressed" in getattr(obj, "PropertiesList", ()):
            return bool(obj.Suppressed)
        return bool(getattr(obj, _DISABLED_PROP, False))

    def _emptied_by_suppression(self, obj):
        """Un corps vide parce que toutes ses fonctions sont désactivées :
        FreeCAD le dit en erreur (« Tip shape is empty »), ce n'en est pas
        une — comme dans les modeleurs courants, la pièce est vide."""
        if getattr(obj, "TypeId", "") != "PartDesign::Body":
            return False
        if getattr(obj, "BaseFeature", None) is not None:
            return False
        features = [o for o in obj.Group
                    if o.isDerivedFrom("PartDesign::Feature")]
        return bool(features) and all(
            bool(getattr(o, "Suppressed", False)) for o in features)

    def _disabled_root(self, obj):
        """La ligne dont la désactivation a emporté ``obj``, ou None."""
        name = getattr(obj, _DISABLED_BY_PROP, "") or ""
        root = self._require_doc().getObject(name) if name else None
        return root if root is not None and self._is_disabled(root) else None

    def _can_carry_disabled(self, obj):
        """Ce qu'une cascade désactive : les lignes qui se désactivent et
        les esquisses (une esquisse posée sur une face ou un plan qui
        disparaît). Les objets cachés (liants) se traversent seulement."""
        return (self._is_suppressible(obj)
                or getattr(obj, "TypeId", "") == "Sketcher::SketchObject")

    def _set_disabled(self, obj, disabled, root=None):
        """Pose l'état désactivé et sa racine (``root`` : la ligne que
        l'utilisateur a désactivée, si ce n'est pas ``obj``)."""
        disabled = bool(disabled)
        if "Suppressed" in obj.PropertiesList:
            obj.Suppressed = disabled
        else:
            if _DISABLED_PROP not in obj.PropertiesList:
                if not disabled:
                    return
                obj.addProperty("App::PropertyBool", _DISABLED_PROP,
                                "FreeSolid", "Désactivé")
                obj.setEditorMode(_DISABLED_PROP, 2)
            setattr(obj, _DISABLED_PROP, disabled)
            if hasattr(obj, "Visibility"):
                obj.Visibility = not (disabled or self._is_rolled_back(obj))
        by = root.Name if (disabled and root is not None
                           and root is not obj) else ""
        if _DISABLED_BY_PROP not in obj.PropertiesList:
            if not by:
                return
            obj.addProperty("App::PropertyString", _DISABLED_BY_PROP,
                            "FreeSolid", "Désactivé avec")
            obj.setEditorMode(_DISABLED_BY_PROP, 2)
        setattr(obj, _DISABLED_BY_PROP, by)

    def _parent_links(self, obj):
        """Ce que ``obj`` prend, au sens de « Parents et enfants » : ses
        liens hors chaîne du corps. Un habillage (congé, chanfrein,
        dépouille, coque) ne compte pas sa base, la fonction d'avant : il
        n'en est l'enfant que si ses arêtes ou ses faces disparaissent
        avec elle (``set_suppressed`` le voit à l'erreur)."""
        links = self._links_of(obj)
        if obj.isDerivedFrom("PartDesign::DressUp"):
            base = getattr(obj, "Base", None)
            base = base[0] if isinstance(base, (list, tuple)) and base else base
            links = [o for o in links if o is not base]
        return links

    def _children_of(self, obj):
        return [o for o in getattr(obj, "InList", ())
                if o is not obj and obj in self._parent_links(o)]

    def _disable_closure(self, targets):
        """{nom: (objet, racine)} : les cibles et tout ce qui s'appuie
        sur elles, de proche en proche. Les objets cachés se traversent ;
        ce qui est déjà désactivé garde sa propre racine."""
        out = {}
        stack = [(obj, obj) for obj in targets]
        seen = set()
        while stack:
            obj, root = stack.pop()
            if obj.Name in seen:
                continue
            seen.add(obj.Name)
            if obj is root or (self._can_carry_disabled(obj)
                               and not self._is_disabled(obj)):
                out[obj.Name] = (obj, root)
            elif self._is_disabled(obj):
                continue
            for helper in self._thin_helpers(obj) if (
                    obj.isDerivedFrom("PartDesign::Feature")) else ():
                stack.append((helper, root))
            for child in self._children_of(obj):
                if child.TypeId != "PartDesign::Body":
                    stack.append((child, root))
        return out

    def set_suppressed(self, features, suppressed=True):
        """Désactive (ou réactive) des lignes : elles restent dans l'arbre
        avec leurs réglages, la pièce se calcule sans elles. Comme dans
        les modeleurs courants, ce qui s'appuie sur une ligne désactivée
        l'est avec elle : ce qui la prend par un lien (profil, appui,
        référence), et ce qui perd ses arêtes ou ses faces. La réactiver
        les rend ; une ligne emportée ne se réactive pas seule."""
        from engine.kernel import KernelError
        doc = self._require_doc()
        targets = []
        for name in features or ():
            obj = doc.getObject(str(name))
            if obj is None or not self._is_suppressible(obj):
                raise KernelError(
                    "cette ligne ne se désactive pas : {}".format(
                        getattr(obj, "Label", name)))
            targets.append(obj)
        if not targets:
            raise KernelError("choisissez une fonction")
        if suppressed:
            self._disable(doc, targets)
        else:
            self._enable(doc, targets)
        return self._current_tree()

    def _broken_names(self, doc):
        return {o.Name for o in doc.Objects
                if "Invalid" in (o.State or ())}

    def _recompute_quiet(self):
        from engine.kernel import KernelError
        try:
            self._recompute()
        except KernelError:
            pass  # l'état des objets dit ce qui casse

    def _disable(self, doc, targets):
        broken_before = self._broken_names(doc)
        for obj, root in self._disable_closure(targets).values():
            self._set_disabled(obj, True, root)
            # Ses objets cachés la suivent : la cavité d'une paroi mince,
            # le combiner qui fond d'autres corps (les corps reviennent).
            if obj.isDerivedFrom("PartDesign::Feature"):
                for helper in self._thin_helpers(obj):
                    if "Suppressed" in helper.PropertiesList:
                        helper.Suppressed = True
        roots = list(targets)
        for _ in range(10):
            self._recompute_quiet()
            # Ce qui casse maintenant a perdu ses arêtes ou ses faces avec
            # une ligne désactivée : il l'est avec elle.
            fresh = [doc.getObject(n) for n in
                     self._broken_names(doc) - broken_before]
            fresh = [o for o in fresh if o is not None
                     and self._can_carry_disabled(o)
                     and not self._is_disabled(o)]
            if not fresh:
                break
            for obj in fresh:
                root = self._broken_root(obj, roots)
                for item, by in self._disable_closure([obj]).values():
                    self._set_disabled(item, True,
                                       root if by is obj else by)

    def _broken_root(self, obj, roots):
        """La racine à laquelle rattacher ``obj`` qui casse : la ligne
        désactivée la plus proche avant lui dans l'arbre."""
        order_of = self._tree_order()
        at = order_of.get(obj.Name, -1)
        before = [r for r in roots if order_of.get(r.Name, -1) < at]
        return max(before, key=lambda r: order_of.get(r.Name, -1),
                   default=roots[0])

    def _enable(self, doc, targets):
        from engine.kernel import KernelError
        for obj in targets:
            root = self._disabled_root(obj)
            if root is not None and root not in targets:
                raise KernelError(
                    "« {} » a été désactivée avec « {} » : réactivez "
                    "« {} »".format(obj.Label, root.Label, root.Label))
        names = {o.Name for o in targets}
        coming = list(targets) + [
            o for o in doc.Objects
            if getattr(o, _DISABLED_BY_PROP, "") in names
            and o.Name not in names]
        back = {o.Name for o in coming}
        for obj in coming:
            self._set_disabled(obj, False)
            if obj.isDerivedFrom("PartDesign::Feature"):
                for helper in self._thin_helpers(obj):
                    if "Suppressed" in helper.PropertiesList:
                        helper.Suppressed = False
        # Ce qui s'appuie aussi sur une autre ligne encore désactivée
        # reste désactivé, avec elle.
        for obj in coming:
            if obj in targets:
                continue
            held = next((p for p in self._parent_links(obj)
                         if self._is_disabled(p) and p.Name not in back),
                        None)
            if held is not None:
                self._set_disabled(obj, True,
                                   self._disabled_root(held) or held)
        for _ in range(2):
            try:
                self._recompute()
                break
            except KernelError:
                # Les fonctions qui ont seulement perdu leurs arêtes ou
                # faces le temps de la désactivation : on les leur rend.
                if not self._heal_missing_links(doc):
                    break

    @staticmethod
    def _heal_missing_links(doc):
        """Sous-éléments marqués manquants (« ?Edge1 ») pendant qu'une
        fonction d'appui était désactivée : rendus à leur nom (« Edge1 »).
        Vrai si un lien a été réparé."""
        healed = False
        for obj in doc.Objects:
            for prop in obj.PropertiesList:
                kind = obj.getTypeIdOfProperty(prop)
                if kind == "App::PropertyLinkSub":
                    value = getattr(obj, prop)
                    if value and any(str(s).startswith("?") for s in value[1]):
                        setattr(obj, prop, (value[0], [str(s).lstrip("?")
                                                       for s in value[1]]))
                        healed = True
                elif kind == "App::PropertyLinkSubList":
                    value = getattr(obj, prop) or []
                    if any(str(s).startswith("?") for _, subs in value
                           for s in (subs if isinstance(subs, (list, tuple))
                                     else [subs])):
                        setattr(obj, prop, [
                            (o, [str(s).lstrip("?") for s in (
                                subs if isinstance(subs, (list, tuple))
                                else [subs])])
                            for o, subs in value])
                        healed = True
        return healed

    def rebuild_errors(self):
        """Fonctions en erreur après la reconstruction, dans l'ordre du
        document, avec le message du modeleur (traduit quand il est
        connu)."""
        doc = self._require_doc()
        out = []
        for obj in doc.Objects:
            state = obj.State or ()
            if "Invalid" not in state and "Error" not in state:
                continue
            if (self._is_internal_tool(obj)
                    or self._emptied_by_suppression(obj)):
                continue
            # « Fonction : ce qui ne va pas », traduit comme à la
            # reconstruction.
            message = self._broken_message(obj)
            out.append({"name": obj.Name, "label": obj.Label,
                        "kind": self._t_kind(obj), "message": message})
        return {"errors": out}

    def _t_kind(self, obj):
        from engine.vocab import label_for_type
        return label_for_type(obj.TypeId, self.lang)

    def undo_history(self, sketch=None):
        """Ce que Ctrl+Z et Ctrl+Y défont, du plus proche au plus loin ;
        avec ``sketch``, l'esquisse ouverte : ses pas seulement."""
        doc = self._require_doc()
        undo, redo = list(doc.UndoNames), list(doc.RedoNames)
        if sketch is not None:
            undo = undo[:self._undo_room(undo, sketch)]
            redo = redo[:self._undo_room(redo, sketch)]
        return {"undo": undo_steps(undo), "redo": undo_steps(redo)}
