"""Fichiers : ouvrir, enregistrer, importer, exporter.

Mixin de ``Kernel``. Pas d'import FreeCAD au niveau du module :
les méthodes importent le noyau à l'appel, pour éviter un cycle.
"""

#: Objets qui rangent ou montrent d'autres objets sans les consommer :
#: un solide qu'ils tiennent reste une pièce à part entière.
_HOLDERS = ("App::DocumentObjectGroup", "App::Part", "App::Origin",
            "App::Link", "App::LinkGroup", "Spreadsheet::Sheet")


def _feeds(user, obj):
    """``user`` prend-il ``obj`` par une propriété de lien (une booléenne
    ses opérandes, une extrusion son profil) ? Une expression qui lit une
    cote de ``obj`` ne compte pas : elle ne consomme pas sa forme."""
    for prop in getattr(user, "PropertiesList", ()):
        try:
            kind = user.getTypeIdOfProperty(prop)
        except Exception:  # noqa: BLE001 - propriété dynamique disparue
            continue
        if not str(kind).startswith("App::PropertyLink"):
            continue
        stack = [getattr(user, prop, None)]
        while stack:
            item = stack.pop()
            if item is obj:
                return True
            if isinstance(item, (list, tuple)):
                stack.extend(item)
    return False


def part_leaves(objects):
    """Les formes d'un document sans corps PartDesign (atelier Part) qui
    font la pièce : celles qu'aucune autre ne consomme, comme le résultat
    d'une booléenne et non ses opérandes. Les solides d'abord ; à défaut,
    les surfaces. Les visibles l'emportent sur les cachées."""
    leaves = []
    for obj in objects:
        kind = str(getattr(obj, "TypeId", ""))
        if kind.startswith(("App::", "PartDesign::", "Sketcher::",
                            "Spreadsheet::", "Mesh::")):
            continue
        shape = getattr(obj, "Shape", None)
        if shape is None or shape.isNull():
            continue
        if any(getattr(user, "TypeId", "") not in _HOLDERS
               and _feeds(user, obj)
               for user in getattr(obj, "InList", ())):
            continue
        leaves.append(obj)
    for keep in (lambda o: o.Shape.Solids, lambda o: o.Shape.Faces):
        found = [o for o in leaves if keep(o)]
        if found:
            visible = [o for o in found if getattr(o, "Visibility", True)]
            return visible or found
    return []


def _baked(shape):
    """La forme avec son placement inscrit dans sa géométrie : la base
    d'un corps (``PartDesign::FeatureBase``) ne garde pas le placement
    de la forme, une pièce rangée dans un App::Part ou un STEP placé à la
    racine reviendraient à l'origine."""
    import FreeCAD
    placement = shape.Placement
    if placement.isIdentity():
        return shape
    moved = shape.copy()
    moved.Placement = FreeCAD.Placement()
    moved.transformShape(placement.toMatrix(), True)
    return moved


class FilesMixin:
    # -- fichiers ---------------------------------------------------------

    def export_part(self, path):
        """Export STL (impression 3D) ou STEP (échange CAO), par extension.

        Exports the body's current shape — what the viewport shows is what
        the printer gets.
        """
        import os
        from engine.kernel import (
            KernelError,
            _explain,
        )
        body = self._require_body()
        shape = getattr(body, "Shape", None)
        if shape is None or not shape.Solids:
            raise KernelError("rien à exporter — la pièce n'a pas de solide")
        path = self._user_path(
            path, (".stl", ".step", ".3mf"), must_exist=False)
        ext = os.path.splitext(path)[1].lower()
        try:
            if ext == ".stl":
                shape.exportStl(path)
            elif ext == ".step":
                shape.exportStep(path)
            elif ext == ".3mf":
                import Mesh
                Mesh.export([body], path)
            else:
                raise KernelError("format inconnu « {} » — utilisez .stl, "
                                  ".step ou .3mf".format(
                                      ext or "aucune extension"))
        except KernelError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise KernelError(_explain(exc))
        return {"path": path, "size": os.path.getsize(path)}

    #: Wire names for the body's origin planes — Dessus/Face/Droite in the
    #: client, following vocab.ORIGIN_PLANES (FreeCAD is Z-up).

    def list_dir(self, path=None):
        """Liste un dossier de la prison de chemins. Lecture seule.

        ``path`` absent : le dossier personnel. Même règles que
        l'ouverture et l'enregistrement (``protocol.list_user_dir``).
        """
        from engine.kernel import KernelError
        from . import protocol
        try:
            return protocol.list_user_dir(path)
        except protocol.ProtocolError as exc:
            raise KernelError(str(exc))

    def open_part(self, path):
        """Open an existing .FCStd — the user's real files, not our demos.

        Every PartDesign body of the file opens. A file without one comes
        from the Part workbench: its final shapes (``part_leaves``) each
        become the base of their own body, like a STEP import — geometry
        only, the Part history is not carried over. A file with neither
        (empty, mesh only) is refused with the reason.
        """
        from engine import foreign
        App = self._app()
        path = self._user_path(
            path, (".FCStd", ".step", ".stp", ".iges", ".igs")
            + foreign.EXTENSIONS, must_exist=True)
        if foreign.is_foreign(path):
            return self._import_foreign(path)
        if path.lower().endswith((".step", ".stp", ".iges", ".igs")):
            return self._import_cad(path)
        self._close_current()
        doc = App.openDocument(path)
        self._setup_doc(doc)
        bodies = [
            o for o in doc.Objects
            if o.TypeId == "PartDesign::Body"
            and not self._is_internal_tool(o)
        ]
        if not bodies:
            bodies = [o for o in doc.Objects
                      if o.TypeId == "PartDesign::Body"]
        if not bodies:
            if self._is_assembly_doc(doc):
                # C'est un assemblage enregistré par nous : on le rouvre
                # dans le mode qui va avec.
                self._doc, self._body = doc, None
                self._assembly = True
                return self.assembly_tree()
            return self._import_part_workbench(doc, path)
        self._doc, self._body = doc, bodies[0]
        if self._bar_line() is not None:
            # Enregistré la barre au milieu : ce qu'on ajoute vient à la
            # barre, même dans un fichier d'avant les rangs enregistrés.
            self._persist_ranks()
        tree = self.get_tree()
        tree["bodies_in_file"] = len(bodies)
        return tree

    @staticmethod
    def _is_assembly_doc(doc):
        """Un assemblage FreeSolid : son Assembly::AssemblyObject, ou
        (ancien format) des liens vers les corps d'autres fichiers. Un
        lien vers une forme du même fichier, courant dans l'atelier Part,
        n'en fait pas un assemblage."""
        for obj in doc.Objects:
            if obj.TypeId == "Assembly::AssemblyObject":
                return True
        for obj in doc.Objects:
            if obj.TypeId != "App::Link":
                continue
            target = getattr(obj, "LinkedObject", None)
            if (getattr(target, "TypeId", "") == "PartDesign::Body"
                    and getattr(target, "Document", doc) is not doc):
                return True
        return False

    def _import_part_workbench(self, doc, path):
        """Un .FCStd de l'atelier Part : ses formes finales deviennent
        chacune la base d'un corps, dans un document neuf. Le fichier
        n'est pas touché ; « Enregistrer » demande où écrire."""
        import os
        from engine.kernel import KernelError
        App = self._app()
        shapes = []
        for obj in part_leaves(doc.Objects):
            shape = obj.Shape.copy()
            try:
                # Placement global : une forme rangée dans un App::Part
                # garde la position que ce conteneur lui donne.
                shape.Placement = obj.getGlobalPlacement()
            except Exception:  # noqa: BLE001 - pas de conteneur à composer
                pass
            shapes.append((obj.Label, shape))
        # Document ouvert ici mais non adopté : le fermer pour ne pas
        # laisser d'orphelin dans App.listDocuments().
        try:
            App.closeDocument(doc.Name)
        except Exception:
            pass
        self._doc = self._body = None
        if not shapes:
            raise KernelError(
                "rien à ouvrir : ni corps PartDesign ni forme dans ce "
                "fichier (vide, ou un maillage seul)")
        label = os.path.splitext(os.path.basename(path))[0]
        self._doc = App.newDocument("FreeSolid")
        self._setup_doc(self._doc)
        solid = any(shape.Solids for _, shape in shapes)
        if solid:
            parts = [(name, piece) for name, shape in shapes
                     for piece in shape.Solids]
        else:
            parts = shapes
        tree = self._bodies_from_shapes(
            parts, label, solid=solid, names=len(parts) == len(shapes))
        tree["imported_solids"] = len(parts) if solid else 0
        tree["from_part_workbench"] = True
        return tree

    def _import_foreign(self, path):
        """.sldprt / .x_t / .x_b : le lecteur d'OpenSW (``engine/foreign.py``)
        en écrit un STEP, importé ensuite comme un STEP. La géométrie
        seule — l'arbre de fonctions du fichier n'est pas rejoué. La pièce
        ouverte reste en place si la lecture échoue."""
        import os
        import shutil
        import tempfile
        from engine import foreign
        from engine.kernel import KernelError
        work = tempfile.mkdtemp(prefix="freesolid-lecture-")
        try:
            self._report_progress("Lecture de la pièce par OpenSW")
            step = os.path.join(work, "piece.step")
            try:
                report = foreign.convert(path, step)
            except foreign.ForeignError as exc:
                raise KernelError(str(exc)) from None
            self._report_progress("Import de la géométrie")
            label = os.path.splitext(os.path.basename(path))[0]
            tree = self._import_cad(step, label=label)
            tree["converted_from"] = os.path.splitext(path)[1].lower()
            # Corps que le lecteur n'a pas su écrire : le dire, pas les taire.
            tree["skipped_bodies"] = int(getattr(report, "skipped_bodies", 0) or 0)
            return tree
        finally:
            shutil.rmtree(work, ignore_errors=True)

    def _import_cad(self, path, label=None):
        """Import STEP/IGES : chaque solide arrive comme base de son propre
        corps — toutes les fonctions s'appliquent ensuite dessus."""
        import os
        from engine.kernel import (
            KernelError,
            _explain,
        )
        import Part
        App = self._app()
        self._close_current()
        self._doc = App.newDocument("FreeSolid")
        self._setup_doc(self._doc)
        shape = Part.Shape()
        try:
            shape.read(path)
            label = label or os.path.splitext(os.path.basename(path))[0]
            solids = shape.Solids
            parts = [(label, part) for part in (solids or [shape])]
            tree = self._bodies_from_shapes(parts, label, solid=bool(solids))
            tree["imported_solids"] = len(solids)
            return tree
        except KernelError:
            self._close_current()
            raise
        except Exception as exc:  # noqa: BLE001
            self._close_current()
            raise KernelError(_explain(exc))

    def _bodies_from_shapes(self, parts, label, solid=True, names=False):
        """Un corps par forme de ``parts`` (``(nom, forme)``), la forme en
        base : toutes les fonctions s'appliquent ensuite dessus. ``names``
        : chaque corps prend le nom de sa forme, sinon celui du fichier,
        numéroté s'il y en a plusieurs. Sans solide, les formes restent
        des surfaces et chaque corps attend une première fonction."""
        for index, (name, part) in enumerate(parts, start=1):
            body = self._doc.addObject("PartDesign::Body", "Body")
            body.Label = (name if names
                          else label if len(parts) == 1
                          else "{} ({})".format(label, index))
            if self._body is None:
                self._body = body
            base = self._doc.addObject("Part::Feature", "Imported")
            base.Shape = _baked(part)
            if not solid:
                # Que des surfaces : elles restent visibles dans la
                # section Surfaces, le corps attend une première fonction.
                base.Label = self._t("Import — {}").format(body.Label)
                continue
            base.Label = self._t("Forme importée — {}").format(body.Label)
            body.BaseFeature = base
            # FreeCAD enveloppe la forme dans un PartDesign::FeatureBase
            # nommé « BaseFeature » : c'est lui que l'arbre montre.
            for wrapper in body.Group:
                if wrapper.TypeId == "PartDesign::FeatureBase":
                    wrapper.Label = self._t("Import — {}").format(body.Label)
        self._doc.recompute()
        return self.get_tree()

    def save_part(self, path):
        """Save as a standard .FCStd — openable in stock FreeCAD.

        The exit door stays open by design: nothing this app produces is
        locked into it.
        """
        doc = self._require_doc()
        path = str(path)
        if not path.endswith(".FCStd"):
            path += ".FCStd"
        path = self._user_path(path, (".FCStd",), must_exist=False)
        doc.saveAs(path)
        return {"path": path}
