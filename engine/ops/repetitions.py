"""Répétitions : symétrie, répétitions linéaire et circulaire, réseau de
corps, répétition pilotée par esquisse.

Méthodes : solids.py, bodypattern.py, sketchpattern.py.
"""

from engine.ops._base import Op, Req


OPS = (
    # Répétition pilotée par esquisse : les fonctions (sinon la dernière)
    # recopiées sur chaque point de l'esquisse (sinon la dernière libre).
    Op("add_sketch_pattern", Req(optional={"sketch": str, "features": list}),
       undo=True, preview=True,
       no_replay="forme figée (FrozenShape), pas get_params"),
    Op("add_mirror", Req(optional={"features": list, "scope": list,
                                   "face": int}),
       undo=True, preview=True,
       no_replay="Originals n'est pas une cote"),
                                       # optional: plane (XY|XZ|YZ), features
    Op("add_linear_pattern", Req(("length", float), ("count", int),
                                 optional={"features": list, "axis": str,
                                           "edge": int, "spacing": bool,
                                           "reversed": bool,
                                           "length2": float, "count2": int,
                                           "axis2": str, "edge2": int,
                                           "reversed2": bool,
                                           "scope": list}),
       undo=True, preview=True,
       no_replay="Originals n'est pas une cote"),
                                       # optional: axis (X|Y|Z), features
    Op("add_polar_pattern", Req(("count", int),
                                optional={"features": list, "axis": str,
                                          "edge": int, "angle": float,
                                          "reversed": bool, "scope": list}),
       undo=True, preview=True,
       no_replay="Originals n'est pas une cote"),
                                       # optional: angle (°), axis, features
    Op("add_body_pattern", Req(("kind", str), ("bodies", list),
                               optional={"length": float, "count": int,
                                         "axis": str, "edge": int,
                                         "spacing": bool, "reversed": bool,
                                         "length2": float, "count2": int,
                                         "axis2": str, "edge2": int,
                                         "reversed2": bool, "angle": float,
                                         "plane": str}),
       undo=True, preview=True, creates="App::DocumentObjectGroup",
       no_replay="des corps entiers, pas des cotes"),
                                       # kind: linear | polar | mirror
)
