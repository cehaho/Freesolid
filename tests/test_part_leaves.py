"""Les formes qu'on reprend d'un fichier de l'atelier Part (sans FreeCAD).

``part_leaves`` garde les formes qu'aucune autre ne consomme par un lien :
le résultat d'une booléenne, pas ses opérandes. Une expression qui lit une
cote, un groupe ou un App::Part qui range une forme ne la consomment pas.
"""

from engine.files import part_leaves


class Shape:
    def __init__(self, solids=1, faces=None, null=False):
        self.Solids = [object()] * solids
        self.Faces = [object()] * (faces if faces is not None else 6 * solids)
        self._null = null

    def isNull(self):
        return self._null


class Obj:
    def __init__(self, name, type_id="Part::Feature", shape=None,
                 visible=True, links=None):
        self.Name = name
        self.TypeId = type_id
        self.Shape = shape if shape is not None else Shape()
        self.Visibility = visible
        self.InList = []
        self._links = dict(links or {})
        self.PropertiesList = list(self._links) + ["ExpressionEngine"]
        for prop, value in self._links.items():
            setattr(self, prop, value)
            for item in value if isinstance(value, (list, tuple)) else [value]:
                item.InList.append(self)

    def getTypeIdOfProperty(self, prop):
        if prop in self._links:
            value = self._links[prop]
            return ("App::PropertyLinkList" if isinstance(value, list)
                    else "App::PropertyLink")
        return "App::PropertyExpressionEngine"


def names(objects):
    return [o.Name for o in part_leaves(objects)]


def test_une_booleenne_garde_son_resultat_pas_ses_operandes():
    box, cyl = Obj("Box", "Part::Box"), Obj("Cylinder", "Part::Cylinder")
    cut = Obj("Cut", "Part::Cut", links={"Base": box, "Tool": cyl})
    assert names([box, cyl, cut]) == ["Cut"]


def test_une_fusion_par_liste_de_liens():
    a, b = Obj("A", "Part::Box"), Obj("B", "Part::Sphere")
    fusion = Obj("Fusion", "Part::MultiFuse", links={"Shapes": [a, b]})
    assert names([a, b, fusion]) == ["Fusion"]


def test_une_expression_ne_consomme_pas():
    cyl = Obj("Cylinder", "Part::Cylinder")
    box = Obj("Box", "Part::Box")
    cyl.InList.append(box)  # Box.Length = Cylinder.Radius * 2
    assert names([cyl, box]) == ["Cylinder", "Box"]


def test_un_conteneur_ne_consomme_pas():
    box = Obj("Box", "Part::Box")
    part = Obj("Part", "App::Part", links={"Group": [box]})
    group = Obj("Group", "App::DocumentObjectGroup", links={"Group": [box]})
    assert names([part, group, box]) == ["Box"]


def test_esquisses_et_corps_ne_sont_pas_des_pieces():
    sketch = Obj("Sketch", "Sketcher::SketchObject", shape=Shape(0, 0))
    body = Obj("Body", "PartDesign::Body")
    assert names([sketch, body]) == []


def test_les_solides_avant_les_surfaces():
    face = Obj("Face", "Part::Plane", shape=Shape(0, 1))
    box = Obj("Box", "Part::Box")
    assert names([face, box]) == ["Box"]
    assert names([face]) == ["Face"]


def test_les_visibles_avant_les_cachees():
    shown = Obj("Shown", "Part::Box")
    hidden = Obj("Hidden", "Part::Box", visible=False)
    assert names([hidden, shown]) == ["Shown"]
    assert names([hidden]) == ["Hidden"]


def test_forme_nulle_ignoree():
    assert names([Obj("Empty", shape=Shape(0, 0, null=True))]) == []
