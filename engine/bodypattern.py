"""Réseau de corps : répéter des corps entiers.

Chaque occurrence (``add_body_pattern``) est un nouveau corps qui suit sa
source telle qu'elle est à la place du réseau dans l'arbre :

- un lieur de forme placé (``SubShapeBinder``) lit la dernière fonction
  de la source avant le réseau ; ce qui vient après ne passe pas dans les
  copies ;
- un second lieur fige ce placement dans la géométrie, car la base d'un
  corps ignore la position de l'objet qu'elle reçoit ;
- la symétrie passe par ``Part::Mirroring``.

L'hôte, un ``App::DocumentObjectGroup`` qui range ces lieurs, porte les
cotes rééditables (``Length``, ``Occurrences``…). Après chaque
reconstruction, le moteur aligne les copies sur ces cotes
(``_refresh_repetitions``) : il en ajoute, en retire, les déplace, et
rebranche leurs lieurs quand la fonction lue change (supprimée, ou une
autre amenée avant le réseau). Une copie supprimée à la main est sautée
ensuite.

Les pas et les angles d'une répétition (``linear_steps``,
``polar_angles``) servent aussi aux corps concernés
(``engine/bodyscope.py``).

Tout est en objets FreeCAD standard : le fichier s'ouvre dans FreeCAD.
Les calculs de pas et d'angles sont purs, testés en CI ; les imports
FreeCAD restent dans les méthodes.
"""

import json

#: Genres de réseau de corps, et le libellé de l'hôte.
BODY_PATTERN_LABELS = {
    "linear": "Réseau linéaire de corps",
    "polar": "Réseau circulaire de corps",
    "mirror": "Symétrie de corps",
}

#: Écart sous lequel deux placements sont les mêmes.
_SAME = 1e-9


def linear_steps(mode, occurrences, length, offset,
                 spacings=(), pattern=()):
    """Distances des occurrences le long d'une direction, la première à 0.

    Comme ``LinearPattern::calculateSteps`` de FreeCAD 1.1 : en mode
    « Extent », ``length`` est la longueur totale ; en « Spacing »,
    chaque écart est celui de ``spacings`` s'il n'y vaut pas -1, sinon
    celui du motif ``pattern`` (plus d'une valeur), sinon ``offset``.
    """
    count = int(occurrences)
    steps = [0.0]
    if count <= 1:
        return steps
    if str(mode) == "Spacing":
        spacings = list(spacings)
        pattern = list(pattern)
        total = 0.0
        for i in range(1, count):
            if i - 1 < len(spacings) and spacings[i - 1] != -1.0:
                gap = float(spacings[i - 1])
            elif len(pattern) > 1:
                gap = float(pattern[(i - 1) % len(pattern)])
            else:
                gap = float(offset)
            total += gap
            steps.append(total)
        return steps
    gap = float(length) / (count - 1)
    return [gap * i for i in range(count)]


def polar_angles(mode, occurrences, angle, offset=0.0,
                 spacings=(), pattern=()):
    """Angles (degrés) des occurrences autour de l'axe, le premier à 0.

    Comme ``PolarPattern::getTransformations`` : en « Extent », un tour
    complet se partage en ``occurrences`` parts égales, un autre angle en
    ``occurrences - 1`` ; en « Spacing », les écarts suivent la même
    priorité que ``linear_steps``.
    """
    count = int(occurrences)
    if count <= 1:
        return [0.0]
    if str(mode) == "Spacing":
        return linear_steps("Spacing", count, 0.0, offset, spacings, pattern)
    total = float(angle)
    gap = total / count if abs(total - 360.0) < 1e-7 else total / (count - 1)
    return [gap * i for i in range(count)]


def copy_key(host, source, index):
    """Repère d'une copie : son réseau, son corps source, son occurrence."""
    return "{}|{}|{}".format(host, source, index)


def parse_copy_key(text):
    """(réseau, source, occurrence) d'une copie, ou None."""
    parts = str(text or "").split("|")
    return tuple(parts) if len(parts) == 3 and all(parts) else None


def body_pattern_offsets(kind, count, length, spacing,
                         count2=1, length2=0.0, angle=360.0):
    """Occurrences d'un réseau de corps, sans la source : ``[(repère,
    numéro, a, b)]``.

    Linéaire : ``a`` et ``b`` sont les distances sur les deux directions ;
    ``length`` est le pas avec ``spacing``, la longueur totale sinon.
    Circulaire : ``a`` est l'angle, ``b`` vaut 0. Symétrie : une seule
    copie. Le numéro est celui du libellé, « Corps (2) » pour la première
    copie.
    """
    if kind == "mirror":
        return [("1", 2, 0.0, 0.0)]
    mode = "Spacing" if spacing else "Extent"
    if kind == "polar":
        angles = polar_angles("Extent", count, angle)
        return [(str(i), i + 1, a, 0.0) for i, a in enumerate(angles) if i]
    first = linear_steps(mode, count, length, length)
    second = (linear_steps(mode, count2, length2, length2)
              if int(count2 or 1) > 1 else [0.0])
    out = []
    for i, a in enumerate(first):
        for j, b in enumerate(second):
            if i == 0 and j == 0:
                continue
            key = str(i) if len(second) == 1 else "{},{}".format(i, j)
            out.append((key, i * len(second) + j + 1, a, b))
    return out


def _direction_words(suffix, axis, edge, reversed):
    """Une direction dans les mots de la création, pour la réédition :
    l'axe d'origine ou le numéro d'arête, et le sens."""
    return {"axis" + suffix: None if edge is not None else str(axis).upper(),
            "edge" + suffix: int(edge) if edge is not None else None,
            "reversed" + suffix: bool(reversed)}


def rekey_copy(key, two):
    """Repère d'occurrence quand la deuxième direction apparaît (``two``)
    ou disparaît : « 2 » devient « 2,0 », et l'inverse. None si le repère
    est déjà au bon format, ou n'a pas d'équivalent."""
    if two and "," not in key:
        return key + ",0"
    if not two and key.endswith(",0"):
        return key[:-2]
    return None


def _number(obj, prop, default=0.0):
    """Valeur d'une cote FreeCAD (quantité ou nombre), ``default`` sans
    elle."""
    value = getattr(obj, prop, None)
    if value is None:
        return float(default)
    return float(getattr(value, "Value", value))


class BodyPatternMixin:
    """Ops : réseau de corps ; corps concernés d'une répétition."""

    # ---------- réseau de corps ----------

    def add_body_pattern(self, kind, bodies, length=None, count=None,
                         axis=None, edge=None, spacing=False, reversed=False,
                         length2=None, count2=None, axis2=None, edge2=None,
                         reversed2=False, angle=360.0, plane="YZ"):
        """Répète des corps entiers : chaque occurrence devient un corps.

        ``kind`` : ``linear`` (``length``, ``count``, ``spacing`` comme
        ``add_linear_pattern``, deuxième direction comprise), ``polar``
        (``count``, ``angle`` total) ou ``mirror`` (``plane``). Direction :
        axe d'origine ou arête droite du corps actif, comme pour une
        répétition de fonctions. ``bodies`` : noms des corps à répéter.
        """
        from engine.kernel import KernelError
        kind = str(kind)
        if kind not in BODY_PATTERN_LABELS:
            raise KernelError(
                "réseau de corps : type inconnu « {} » — attendu linear, "
                "polar ou mirror".format(kind))
        sources = self._pattern_source_bodies(bodies)
        spec = {"kind": kind, "sources": [b.Name for b in sources],
                "skip": []}
        numbers = {}
        if kind == "mirror":
            base, normal = self._global_plane(plane)
            spec.update(base=base, normal=normal, plane=str(plane).upper())
        elif kind == "polar":
            occurrences = int(count or 0)
            if occurrences < 2:
                raise KernelError("au moins 2 occurrences")
            if not float(angle or 0):
                raise KernelError("réseau : angle invalide")
            base, direction = self._global_line(axis or "Z", edge, reversed)
            spec.update(base=base, dir=direction,
                        **_direction_words("", axis or "Z", edge, reversed))
            numbers = {"Occurrences": occurrences, "Angle": float(angle)}
        else:
            occurrences = int(count or 0)
            if occurrences < 2:
                raise KernelError("au moins 2 occurrences")
            if length is None or float(length) <= 0:
                raise KernelError("réseau : distance invalide")
            _, direction = self._global_line(axis or "X", edge, reversed)
            spec.update(dir=direction, spacing=bool(spacing),
                        **_direction_words("", axis or "X", edge, reversed))
            numbers = {"Length": float(length), "Occurrences": occurrences}
            if count2 is not None and int(count2) > 1:
                if length2 is None or float(length2) <= 0:
                    raise KernelError("indiquez la distance de la direction 2")
                _, second = self._global_line(axis2 or "Y", edge2, reversed2)
                spec["dir2"] = second
                spec.update(_direction_words("2", axis2 or "Y", edge2,
                                             reversed2))
                numbers.update(Length2=float(length2),
                               Occurrences2=int(count2))
        doc = self._require_doc()
        host = doc.addObject("App::DocumentObjectGroup", "BodyPattern")
        host.Label = self._t(BODY_PATTERN_LABELS[kind])
        self._mark_body_pattern_tool(host)
        host.addProperty("App::PropertyString", "FreeSolidBodyPattern",
                         "FreeSolid", "Réseau de corps (JSON)")
        host.FreeSolidBodyPattern = json.dumps(spec)
        kinds = {"Length": "App::PropertyDistance",
                 "Length2": "App::PropertyDistance",
                 "Angle": "App::PropertyAngle",
                 "Occurrences": "App::PropertyInteger",
                 "Occurrences2": "App::PropertyInteger"}
        for prop, value in numbers.items():
            host.addProperty(kinds[prop], prop, "FreeSolid",
                             "Cote du réseau de corps")
            setattr(host, prop, value)
        try:
            self._sync_body_pattern(host)
            self._recompute()
        except KernelError:
            self._remove_body_pattern(host)
            raise
        return self.get_tree()

    def _pattern_source_bodies(self, bodies):
        from engine.kernel import KernelError
        if not isinstance(bodies, (list, tuple)):
            raise KernelError("bodies doit être une liste de noms")
        doc = self._require_doc()
        found = []
        for name in bodies:
            obj = doc.getObject(str(name))
            if (obj is None or obj.TypeId != "PartDesign::Body"
                    or self._is_internal_tool(obj)):
                raise KernelError("corps inconnu : {}".format(name))
            if obj not in found:
                found.append(obj)
        if not found:
            raise KernelError(
                "réseau de corps : cochez au moins un corps à répéter")
        return found

    def _mark_body_pattern_tool(self, obj):
        """Mécanique d'un réseau de corps : hors de l'arbre."""
        if "FreeSolidBodyPatternTool" not in obj.PropertiesList:
            obj.addProperty("App::PropertyBool", "FreeSolidBodyPatternTool",
                            "FreeSolid", "Outil interne d'un réseau de corps")
        obj.FreeSolidBodyPatternTool = True

    @staticmethod
    def _stamp_text(obj, prop, value, doc="FreeSolid"):
        if prop not in obj.PropertiesList:
            obj.addProperty("App::PropertyString", prop, "FreeSolid", doc)
        setattr(obj, prop, value)

    def _global_line(self, axis, edge, reversed=False):
        """(point, direction) dans le repère de la pièce : un axe
        d'origine du corps actif ou une arête droite de sa pièce."""
        body = self._require_body()
        obj, subs = self._pattern_direction(axis, edge)
        base, direction = self._link_line(obj, subs[0] if subs else "")
        outer = body.getGlobalPlacement()
        base = outer.multVec(base)
        direction = outer.Rotation.multVec(direction)
        if reversed:
            direction = direction * -1
        return list(base), list(direction)

    def _global_plane(self, plane):
        from engine.kernel import KernelError
        role = self._PLANE_ROLES.get(str(plane).upper())
        if role is None:
            raise KernelError(
                "plan inconnu « {} » — attendu XY, XZ ou YZ".format(plane))
        base, normal = self._link_plane(self._origin_feature(role), "")
        outer = self._require_body().getGlobalPlacement()
        return list(outer.multVec(base)), list(outer.Rotation.multVec(normal))

    def _local_placement(self, obj):
        """Placement de ``obj`` dans le repère de son corps."""
        body = obj.getParentGeoFeatureGroup()
        placement = obj.getGlobalPlacement()
        if body is None:
            return placement
        return body.getGlobalPlacement().inverse().multiply(placement)

    def _link_line(self, obj, sub):
        """(point, direction unitaire) d'un axe d'origine ou d'une arête
        droite, dans le repère du corps qui les porte."""
        import FreeCAD as App
        from engine.kernel import KernelError
        if obj.TypeId == "App::Line":
            placement = self._local_placement(obj)
            return (placement.Base,
                    placement.Rotation.multVec(App.Vector(1, 0, 0)))
        if sub.startswith("Edge") and getattr(obj, "Shape", None) is not None:
            edge = obj.Shape.getElement(sub)
            if type(edge.Curve).__name__ != "Line":
                raise KernelError("choisissez une arête droite")
            start = edge.Vertexes[0].Point
            direction = edge.Vertexes[-1].Point - start
            if direction.Length < 1e-12:
                raise KernelError("choisissez une arête droite")
            return start, direction.normalize()
        raise KernelError("corps concernés : direction non prise en charge")

    def _link_plane(self, obj, sub):
        """(point, normale) d'un plan d'origine, dans le repère du corps."""
        import FreeCAD as App
        from engine.kernel import KernelError
        if obj.TypeId == "App::Plane":
            placement = self._local_placement(obj)
            return (placement.Base,
                    placement.Rotation.multVec(App.Vector(0, 0, 1)))
        raise KernelError("corps concernés : direction non prise en charge")

    def _body_pattern_spec(self, host):
        try:
            spec = json.loads(host.FreeSolidBodyPattern or "")
        except (TypeError, ValueError):
            return None
        return spec if isinstance(spec, dict) else None

    #: Ce qu'une répétition de corps re-choisit (``set_params``) : ses
    #: corps (``sources`` : ``bodies`` y désigne les corps concernés), sa
    #: direction, son sens, son plan, son mode, sa deuxième direction.
    _BODY_PATTERN_PICKS = ("sources", "axis", "edge", "reversed", "plane",
                           "mode", "dir2", "axis2", "edge2", "reversed2")

    def _body_pattern_state(self, host):
        """Ce qu'une répétition de corps re-choisit, dans les mots de sa
        création : ses corps, sa direction (axe d'origine ou arête du corps
        actif) et son sens, ou son plan ; le mode et la deuxième direction
        d'un réseau linéaire."""
        spec = self._body_pattern_spec(host)
        if spec is None:
            return None
        kind = spec.get("kind", "linear")
        state = {"sources": list(spec.get("sources") or ())}
        if kind == "mirror":
            state["plane"] = spec.get("plane")
            return state
        state.update(self._body_direction_state(spec, "", kind == "polar"))
        if kind != "linear":
            return state
        state["mode"] = "spacing" if spec.get("spacing") else "extent"
        count2 = int(_number(host, "Occurrences2", 1))
        state["dir2"] = count2 > 1
        if count2 > 1:
            second = self._body_direction_state(spec, "2", False)
            state.update(axis2=second["axis"], edge2=second["edge"],
                         reversed2=second["reversed"], count2=count2,
                         length2=_number(host, "Length2"))
        return state

    def _body_direction_state(self, spec, suffix, through_origin):
        """Axe ou arête, et sens, d'une direction de ``spec`` (``dir`` ou
        ``dir2``). Une spec d'avant n'a que le vecteur : il se lit sur les
        axes d'origine du corps actif ; une arête ne s'y retrouve pas."""
        import FreeCAD as App
        if "axis" + suffix in spec or "edge" + suffix in spec:
            edge = spec.get("edge" + suffix)
            return {"axis": None if edge is not None
                    else spec.get("axis" + suffix),
                    "edge": edge,
                    "reversed": bool(spec.get("reversed" + suffix))}
        direction = App.Vector(*(spec.get("dir" + suffix)
                                 or ((0, 1, 0) if suffix else (1, 0, 0))))
        outer = self._require_body().getGlobalPlacement()
        base = App.Vector(*(spec.get("base") or (0, 0, 0)))
        for name, unit in (("X", (1, 0, 0)), ("Y", (0, 1, 0)),
                           ("Z", (0, 0, 1))):
            axis = outer.Rotation.multVec(App.Vector(*unit))
            if direction.cross(axis).Length > 1e-7:
                continue
            if through_origin and (base - outer.Base).cross(
                    axis).Length > 1e-7:
                continue
            return {"axis": name, "edge": None,
                    "reversed": direction.dot(axis) < 0}
        return {"axis": None, "edge": None, "reversed": False}

    def _body_line_at(self, host, axis, edge):
        """(point, direction) d'une direction re-choisie, dans le repère
        de la pièce : un axe d'origine du corps actif, ou une arête droite
        du corps actif tel qu'il est au rang de la répétition."""
        from engine.kernel import KernelError
        body = self._require_body()
        if edge is not None:
            tip = self._pattern_source_at(host, body)
            edges = tip.Shape.Edges if tip is not body else []
            if type(edge) is not int or not 0 <= edge < len(edges):
                raise KernelError("arête inconnue : {}".format(edge))
            obj, sub = tip, "Edge{}".format(edge + 1)
        else:
            obj, sub = self._origin_axis(axis, body), ""
        base, direction = self._link_line(obj, sub)
        outer = body.getGlobalPlacement()
        return (list(outer.multVec(base)),
                list(outer.Rotation.multVec(direction)))

    def _set_body_pattern_picks(self, host, picks, values, previous):
        """Ce qu'une répétition de corps re-choisit
        (``_BODY_PATTERN_PICKS``). La spec et les cotes changées entrent
        dans ``previous``, pour le refus ; les copies suivent à la
        reconstruction (``_sync_body_pattern``)."""
        from engine.kernel import KernelError
        spec = self._body_pattern_spec(host) or {}
        kind = spec.get("kind", "linear")
        state = self._body_pattern_state(host) or {}

        def flag(key):
            value = picks[key]
            if not isinstance(value, bool):
                raise KernelError("{} : booléen attendu".format(key))
            return value

        def refuse(keys):
            wrong = [key for key in keys if key in picks]
            if wrong:
                raise KernelError(
                    "propriété non éditable : {}".format(wrong[0]))

        if "sources" in picks:
            sources = self._pattern_source_bodies(picks["sources"])
            for body in sources:
                key = parse_copy_key(getattr(body, "FreeSolidPatternCopy",
                                             ""))
                if key and key[0] == host.Name:
                    raise KernelError("{} est une copie de {}".format(
                        body.Label, host.Label))
                if self._pattern_source_at(host, body) is body:
                    raise KernelError(
                        "{} vient après la répétition".format(body.Label))
            names = [body.Name for body in sources]
            spec["sources"] = names
            # Une copie sautée d'un corps retiré n'a plus de sens.
            spec["skip"] = [entry for entry in spec.get("skip") or ()
                            if entry.rpartition("#")[0] in names]
        if kind == "mirror":
            refuse(("axis", "edge", "reversed", "mode", "dir2", "axis2",
                    "edge2", "reversed2"))
            if "plane" in picks:
                base, normal = self._global_plane(picks["plane"])
                spec.update(base=base, normal=normal,
                            plane=str(picks["plane"]).upper())
        else:
            refuse(("plane",))
            self._set_body_direction(host, spec, picks, state, "", flag)
        if kind != "linear":
            refuse(("mode", "dir2", "axis2", "edge2", "reversed2"))
        else:
            if "mode" in picks:
                if picks["mode"] not in ("spacing", "extent"):
                    raise KernelError(
                        "mode inconnu « {} » — attendu : {}".format(
                            picks["mode"], "spacing, extent"))
                spec["spacing"] = picks["mode"] == "spacing"
            self._set_body_second(host, spec, picks, values, state, flag,
                                  previous)
        previous.append(("FreeSolidBodyPattern", None,
                         host.FreeSolidBodyPattern))
        host.FreeSolidBodyPattern = json.dumps(spec)

    def _set_body_direction(self, host, spec, picks, state, suffix, flag):
        """Direction ``suffix`` (« » ou « 2 ») re-choisie : un axe ou une
        arête, et le sens. Le sens seul retourne le vecteur gardé."""
        axis_key, edge_key = "axis" + suffix, "edge" + suffix
        reversed_key = "reversed" + suffix
        before = bool(state.get(reversed_key))
        flipped = flag(reversed_key) if reversed_key in picks else before
        if axis_key in picks or edge_key in picks:
            base, direction = self._body_line_at(
                host, picks.get(axis_key) or ("Y" if suffix else "X"),
                picks.get(edge_key))
            if flipped:
                direction = [-c for c in direction]
            spec["dir" + suffix] = direction
            if not suffix and spec.get("kind") == "polar":
                spec["base"] = base
            spec.update(_direction_words(
                suffix, picks.get(axis_key) or ("Y" if suffix else "X"),
                picks.get(edge_key), flipped))
        elif flipped != before:
            spec["dir" + suffix] = [-c for c in (
                spec.get("dir" + suffix)
                or ((0, 1, 0) if suffix else (1, 0, 0)))]
            spec[reversed_key] = flipped

    def _set_body_second(self, host, spec, picks, values, state, flag,
                         previous):
        """Deuxième direction d'un réseau de corps : l'activer (``dir2``,
        avec ``count2`` et ``length2`` dans ``values``), la retirer, changer
        son axe ou son sens. Ses cotes sont celles de l'hôte."""
        from engine.kernel import KernelError
        two = bool(state.get("dir2"))
        want = flag("dir2") if "dir2" in picks else two
        if not want:
            if two:
                previous.append(("Occurrences2", None, host.Occurrences2))
                host.Occurrences2 = 1
                return
            # Sans deuxième direction, ni activée : rien de la sienne.
            for key in ("axis2", "edge2", "reversed2"):
                if key in picks:
                    raise KernelError(
                        "propriété non éditable : {}".format(key))
            return
        opening = not two
        if opening:
            try:
                count = int(float(values.get("Occurrences2", 0)))
            except (TypeError, ValueError):
                count = 0
            if count < 2:
                raise KernelError("au moins 2 occurrences")
            try:
                extent = float(values.get("Length2", 0))
            except (TypeError, ValueError):
                extent = 0
            if extent <= 0:
                raise KernelError("indiquez la distance de la direction 2")
            for prop, kind, neutral in (
                    ("Length2", "App::PropertyDistance", 0.0),
                    ("Occurrences2", "App::PropertyInteger", 1)):
                if prop not in host.PropertiesList:
                    host.addProperty(kind, prop, "FreeSolid",
                                     "Cote du réseau de corps")
                    setattr(host, prop, neutral)
            if not any(key in picks for key in ("axis2", "edge2")):
                picks = {**picks, "axis2": "Y"}
        self._set_body_direction(host, spec, picks, state, "2", flag)

    def _body_pattern_hosts(self):
        return [o for o in self._require_doc().Objects
                if "FreeSolidBodyPattern" in o.PropertiesList]

    def _body_pattern_copies(self, host):
        """{(source, occurrence): corps copie} d'un réseau de corps."""
        copies = {}
        for obj in self._require_doc().Objects:
            key = parse_copy_key(getattr(obj, "FreeSolidPatternCopy", ""))
            if key and key[0] == host.Name:
                copies[(key[1], key[2])] = obj
        return copies

    def _body_pattern_rolled_back(self, host):
        """Sous la barre de retour : ses copies n'existent pas encore."""
        copies = list(self._body_pattern_copies(host).values())
        return bool(copies) and all(
            getattr(copy, "Tip", None) is None for copy in copies)

    def _pattern_source_at(self, host, source):
        """Ce que ``host`` répète de ``source`` : sa dernière fonction
        avant le réseau dans l'arbre, cavité de paroi mince comprise."""
        order_of = self._tree_order()
        at = order_of.get(host.Name, -1)
        before = [o for o in source.Group
                  if o.isDerivedFrom("PartDesign::Feature")
                  and order_of.get(o.Name, -1) < at]
        return self._tip_with_helpers(before[-1]) if before else source

    def _body_pattern_wanted(self, host, spec):
        """{(source, occurrence): (numéro, placement ou None)} attendus.

        Une symétrie n'a pas de placement : ``Part::Mirroring`` la porte.
        """
        import FreeCAD as App
        from engine.kernel import KernelError
        kind = spec.get("kind")
        count = int(_number(host, "Occurrences", 2))
        if kind != "mirror" and count < 2:
            raise KernelError("au moins 2 occurrences")
        length = _number(host, "Length")
        if kind == "linear" and length <= 0:
            raise KernelError("réseau : distance invalide")
        angle = _number(host, "Angle")
        if kind == "polar" and not angle:
            raise KernelError("réseau : angle invalide")
        count2 = int(_number(host, "Occurrences2", 1))
        length2 = _number(host, "Length2")
        if count2 > 1 and length2 <= 0:
            raise KernelError("indiquez la distance de la direction 2")
        offsets = body_pattern_offsets(
            kind, count, length, spec.get("spacing"), count2, length2, angle)
        direction = App.Vector(*(spec.get("dir") or (1, 0, 0)))
        second = App.Vector(*(spec.get("dir2") or (0, 1, 0)))
        base = App.Vector(*(spec.get("base") or (0, 0, 0)))
        skip = set(spec.get("skip") or ())
        wanted = {}
        for source in spec.get("sources") or ():
            for key, number, a, b in offsets:
                if "{}#{}".format(source, key) in skip:
                    continue
                if kind == "polar":
                    placement = App.Placement(
                        App.Vector(), App.Rotation(direction, a), base)
                elif kind == "linear":
                    placement = App.Placement(direction * a + second * b,
                                              App.Rotation())
                else:
                    placement = None
                wanted[(source, key)] = (number, placement)
        return wanted

    def _sync_body_pattern(self, host):
        """Aligne les copies sur les cotes de l'hôte ; vrai si l'une a
        bougé, est apparue ou est partie."""
        import FreeCAD as App
        spec = self._body_pattern_spec(host)
        if spec is None:
            return False
        doc = self._require_doc()
        if any(doc.getObject(n) is None for n in spec.get("sources") or ()):
            return False  # source disparue : on ne touche à rien
        self._rekey_copies(host, spec)
        wanted = self._body_pattern_wanted(host, spec)
        existing = self._body_pattern_copies(host)
        changed = False
        doomed = [body for key, body in existing.items() if key not in wanted]
        self._confirm_dropped_copies(host, doomed)
        for body in doomed:
            self._remove_body_copy(body)
            changed = True
        for (source, key), (number, placement) in wanted.items():
            body = existing.get((source, key))
            if body is None:
                self._make_body_copy(host, spec, doc.getObject(source), key,
                                     number, placement)
                changed = True
                continue
            read = self._pattern_source_at(host, doc.getObject(source))
            if spec.get("kind") == "mirror":
                mirror = doc.getObject(getattr(body, "FreeSolidPatternInner",
                                               ""))
                normal = App.Vector(*spec.get("normal"))
                origin = App.Vector(*spec.get("base"))
                if mirror is not None and (
                        (mirror.Normal - normal).Length > _SAME
                        or (mirror.Base - origin).Length > _SAME):
                    mirror.Normal = normal
                    mirror.Base = origin
                    changed = True
                if mirror is not None and mirror.Source is not read:
                    mirror.Source = read
                    changed = True
                continue
            inner = doc.getObject(getattr(body, "FreeSolidPatternInner", ""))
            if inner is None:
                continue
            if not inner.Placement.isSame(placement, _SAME):
                inner.Placement = placement
                changed = True
            if [link[0] for link in inner.Support] != [read]:
                inner.Support = [(read, ("",))]
                changed = True
        return changed

    def _rekey_copies(self, host, spec):
        """La deuxième direction apparaît ou part : les copies de la
        première rangée changent de repère (« 2 » ↔ « 2,0 ») au lieu de
        partir et de revenir, et gardent ce qu'elles portent. Les copies
        sautées suivent."""
        if spec.get("kind") != "linear":
            return
        two = int(_number(host, "Occurrences2", 1)) > 1
        for (source, key), body in self._body_pattern_copies(host).items():
            new = rekey_copy(key, two)
            if new is not None:
                body.FreeSolidPatternCopy = copy_key(host.Name, source, new)
        skip = list(spec.get("skip") or ())
        moved = []
        for entry in skip:
            source, _, key = entry.rpartition("#")
            new = rekey_copy(key, two)
            moved.append(entry if new is None
                         else "{}#{}".format(source, new))
        if moved != skip:
            spec["skip"] = moved
            host.FreeSolidBodyPattern = json.dumps(spec)

    def _confirm_dropped_copies(self, host, doomed):
        """Moins de copies : celles qui portent quelque chose ne partent
        qu'après confirmation — leurs fonctions partent avec elles, un
        combiner qui en prend une perd son outil. L'aperçu, toujours
        défait, ne demande rien."""
        from engine.kernel import NeedsConfirm
        if (not doomed or getattr(self, "_confirmed", False)
                or getattr(self, "_previewing", False)):
            return
        touched = self._copies_contents(doomed)
        if not touched:
            return
        names = ", ".join("« {} »".format(label) for label in touched)
        raise NeedsConfirm(
            "réseau non réduit : cela toucherait {}".format(names),
            "Réduire « {} » supprime {} copie(s) ; cela touche aussi {}. "
            "Continuer ?".format(host.Label, len(doomed), names))

    def _copies_contents(self, copies):
        """Libellés de ce que portent les copies ``copies`` : leurs
        esquisses et fonctions, et les combiners d'autres corps qui en
        prennent une pour outil."""
        doc = self._require_doc()
        names = {body.Name for body in copies}
        labels = []
        for body in copies:
            inner = getattr(body, "FreeSolidPatternInner", "")
            for obj in body.Group:
                if (obj.Name == inner or self._is_pattern_base(obj)
                        or self._is_internal_tool(obj)
                        or self._is_thin_helper(obj)):
                    continue
                if (obj.isDerivedFrom("PartDesign::Feature")
                        or obj.TypeId == "Sketcher::SketchObject"):
                    labels.append(obj.Label)
        for obj in doc.Objects:
            if (obj.TypeId != "PartDesign::Boolean"
                    or obj.getParentGeoFeatureGroup() in copies):
                continue
            if any(tool.Name in names for tool in self._boolean_tools(obj)):
                labels.append(self._thin_owner(obj).Label)
        return list(dict.fromkeys(labels))

    def _make_body_copy(self, host, spec, source, key, number, placement):
        """Un corps qui suit ``source`` à la place du réseau, placé par
        ``placement`` (ou par la symétrie de l'hôte)."""
        import FreeCAD as App
        doc = self._require_doc()
        read = self._pattern_source_at(host, source)
        parts = []
        if spec.get("kind") == "mirror":
            mirror = doc.addObject("Part::Mirroring", "BodyMirror")
            mirror.Source = read
            mirror.Normal = App.Vector(*spec.get("normal"))
            mirror.Base = App.Vector(*spec.get("base"))
            parts = [mirror]
            inner = base = mirror
        else:
            inner = doc.addObject("PartDesign::SubShapeBinder", "BodyCopy")
            inner.Support = [(read, ("",))]
            inner.Placement = placement
            # La base d'un corps ignore le placement de ce qu'elle reçoit :
            # un second lieur le fige dans la géométrie.
            base = doc.addObject("PartDesign::SubShapeBinder", "BodyCopy")
            base.Support = [(inner, ("",))]
            parts = [inner, base]
        for part in parts:
            self._mark_body_pattern_tool(part)
            host.addObject(part)
        body = doc.addObject("PartDesign::Body", "Body")
        body.Label = "{} ({})".format(source.Label, number)
        body.BaseFeature = base
        self._stamp_text(body, "FreeSolidPatternCopy",
                         copy_key(host.Name, source.Name, key))
        self._stamp_text(body, "FreeSolidPatternInner", inner.Name)
        self._stamp_text(body, "FreeSolidPatternParts",
                         ";".join(p.Name for p in parts))
        color = getattr(source, "FreeSolidColor", "")
        if color:
            self._stamp_text(body, "FreeSolidColor", color)
        for child in body.Group:
            if child.TypeId == "PartDesign::FeatureBase":
                # Numéroté comme le corps : FreeCAD veut des libellés uniques.
                child.Label = "{} ({})".format(host.Label, number)
                self._stamp_text(child, "FreeSolidPatternOf", host.Name)
        return body

    def _refuse_repeated(self, body):
        """Un corps qu'un réseau de corps répète ne part pas sous lui —
        ni supprimé, ni retiré par le réseau qui l'a créé."""
        from engine.kernel import KernelError
        for other in self._body_pattern_hosts():
            spec = self._body_pattern_spec(other) or {}
            if body.Name in (spec.get("sources") or ()):
                raise KernelError(
                    "{} est répété par {} — supprimez d'abord ce réseau "
                    "de corps".format(body.Label, other.Label))

    def _remove_body_copy(self, body):
        """Une copie, ses fonctions et ses lieurs. Si elle était le corps
        actif, sa source le devient. Refusé quand un autre réseau la
        répète : il perdrait sa source sans le dire."""
        self._refuse_repeated(body)
        doc = self._require_doc()
        parts = [n for n in str(getattr(body, "FreeSolidPatternParts", "")
                                ).split(";") if n]
        key = parse_copy_key(getattr(body, "FreeSolidPatternCopy", ""))
        active = self._body is body
        later = self._scope_before_delete(body)
        for child in list(body.Group):
            if doc.getObject(child.Name) is not None:
                doc.removeObject(child.Name)
        doc.removeObject(body.Name)
        self._remove_named_parts(later + list(reversed(parts)))
        if active:
            self._body = (doc.getObject(key[1]) if key else None) \
                or self._first_body()

    def _first_body(self):
        return next((o for o in self._require_doc().Objects
                     if o.TypeId == "PartDesign::Body"
                     and not self._is_internal_tool(o)), None)

    def _remove_body_pattern(self, host):
        """Le réseau entier : copies, lieurs, hôte."""
        doc = self._require_doc()
        for body in self._body_pattern_copies(host).values():
            self._remove_body_copy(body)
        for part in list(getattr(host, "Group", ()) or ()):
            if doc.getObject(part.Name) is not None:
                doc.removeObject(part.Name)
        doc.removeObject(host.Name)

    def _body_pattern_host_of(self, obj):
        """L'hôte que désigne ``obj`` : l'hôte, ou la base d'une copie."""
        doc = self._require_doc()
        if "FreeSolidBodyPattern" in getattr(obj, "PropertiesList", ()):
            return obj
        name = getattr(obj, "FreeSolidPatternOf", "")
        return doc.getObject(name) if name else None

    def _remove_named_parts(self, names):
        """Retire des objets internes par leur nom ; un corps avec ses
        fonctions."""
        doc = self._require_doc()
        for name in names:
            obj = doc.getObject(name)
            if obj is None:
                continue
            if obj.TypeId == "PartDesign::Body":
                for child in list(obj.Group):
                    doc.removeObject(child.Name)
            doc.removeObject(name)

    # ---------- reconstruction, arbre, suppression ----------

    def _bodies_mesh(self, bodies):
        """Maillage de ``bodies`` réunis : le fantôme d'un réseau de
        corps, d'une surface. Une courbe (sans face) y entre par ses
        traits, ``lines`` (segments comme ``pack_edges``)."""
        from engine import protocol
        deviation, angle, _edges = self._display_mesh()
        faces = []
        lines = []
        for body in bodies:
            shape = getattr(body, "Shape", None)
            if shape is None:
                continue
            if not shape.Faces:
                for edge in shape.Edges:
                    try:
                        points = edge.discretize(
                            QuasiDeflection=float(deviation))
                    except Exception:  # noqa: BLE001
                        try:
                            points = edge.discretize(Number=24)
                        except Exception:  # noqa: BLE001
                            continue
                    lines.append((len(lines),
                                  [(p.x, p.y, p.z) for p in points]))
                continue
            for face in self._meshed(shape, deviation, angle).Faces:
                vertices, triangles = face.tessellate(float(deviation))
                faces.append((len(faces),
                              [(v.x, v.y, v.z) for v in vertices], triangles))
        mesh = protocol.pack_mesh(faces)
        if lines:
            mesh["lines"] = protocol.pack_edges(lines)
        return mesh

    def _refresh_repetitions(self):
        """Après une reconstruction : copies et outils à jour ; vrai si
        quelque chose a changé (une passe de plus)."""
        changed = False
        for host in self._body_pattern_hosts():
            if self._is_disabled(host):
                continue  # ses copies attendent sa réactivation
            changed = self._sync_body_pattern(host) or changed
        return self._refresh_scopes() or changed

    def _repetition_tree_fields(self, obj, item):
        """Champs d'arbre : ``edits`` (l'objet que le double-clic rouvre),
        ``edits_type``, ``edits_has_params``, ``body_pattern`` et
        ``scope``."""
        from engine.bodyscope import scope_names
        from engine.vocab import type_key_for
        doc = self._require_doc()
        host = self._body_pattern_host_of(obj)
        if host is not None and host is not obj:
            spec = self._body_pattern_spec(host) or {}
            item["edits"] = host.Name
            item["edits_type"] = type_key_for(host.TypeId)
            item["body_pattern"] = spec.get("kind", "linear")
            # Ce que la répétition re-choisit : le double-clic d'une copie
            # rouvre son panneau.
            state = self._body_pattern_state(host)
            if state is not None:
                item["edits_pattern"] = state
        pattern = doc.getObject(getattr(obj, "FreeSolidScopeOf", "") or "")
        if pattern is not None:
            item["edits"] = pattern.Name
            item["edits_type"] = type_key_for(pattern.TypeId)
            state = self._pattern_state(pattern)
            if state is not None:
                item["edits_pattern"] = state
        if "edits" in item:
            # Une symétrie n'a pas de cote : « Modifier » se tait sur ses
            # copies comme sur elle. Une ligne dérivée se désactive par sa
            # répétition : désactivée seule, la répétition la referait.
            item["edits_has_params"] = self._has_params(
                doc.getObject(item["edits"]))
            item["suppressible"] = False
        names = scope_names(getattr(obj, "FreeSolidScope", ""))
        labels = [self._body_title(doc.getObject(n)) for n in names
                  if doc.getObject(n) is not None]
        if labels:
            item["scope"] = labels

    def _body_pattern_rows(self, body, entry):
        """Lignes d'arbre de ``body`` : chaque réseau de corps qui le
        répète, avec son genre et les corps qu'il crée (``copies``).
        ``entry`` : la ligne ordinaire de ``get_tree``."""
        rows = []
        for host in self._body_pattern_hosts():
            spec = self._body_pattern_spec(host) or {}
            if body.Name not in (spec.get("sources") or ()):
                continue
            kind = spec.get("kind", "linear")
            copies = list(self._body_pattern_copies(host).values())
            item = entry(host)
            item["kind"] = self._t(BODY_PATTERN_LABELS.get(
                kind, BODY_PATTERN_LABELS["linear"]))
            item["body_pattern"] = kind
            # Ce qu'elle re-choisit au rang : ses corps, sa direction…
            item["pattern"] = self._body_pattern_state(host)
            item["copies"] = [self._body_title(copy) for copy in copies]
            item["rolled_back"] = self._body_pattern_rolled_back(host)
            if any("Invalid" in (copy.State or ()) for copy in copies):
                item["error"] = True
            rows.append(item)
        return rows

    def _repetition_delete(self, obj):
        """Suppressions propres aux répétitions : l'arbre, ou None quand la
        suppression ordinaire suit (après ``_scope_before_delete``)."""
        from engine.kernel import KernelError
        doc = self._require_doc()
        if obj.TypeId == "PartDesign::Body":
            self._refuse_repeated(obj)
        host = self._body_pattern_host_of(obj)
        if host is not None:
            self._remove_body_pattern(host)
            self._recompute()
            return self._current_tree()
        key = parse_copy_key(getattr(obj, "FreeSolidPatternCopy", ""))
        if key is not None and doc.getObject(key[0]) is not None:
            host = doc.getObject(key[0])
            spec = self._body_pattern_spec(host) or {}
            skip = list(spec.get("skip") or ())
            skip.append("{}#{}".format(key[1], key[2]))
            spec["skip"] = skip
            host.FreeSolidBodyPattern = json.dumps(spec)
            self._remove_body_copy(obj)
            if not self._body_pattern_copies(host):
                self._remove_body_pattern(host)
            self._recompute()
            return self._current_tree()
        return None
