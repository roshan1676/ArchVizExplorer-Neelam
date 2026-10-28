"""Ribbon ground = max(photogrammetry map, our road deck MESH the ribbon runs along) per 3 m sample (27 Oct).
Data/road_build.json z is STALE for many carriageways (mesh deck up to 3.5 m higher than its centreline z), so the deck is
read from the real mesh: Road_<grp>_<id> StaticMeshActor traced (complex) straight down from 6 m above to 6 m below the
ribbon; topmost hit = deck top. Only decks running ALONG the ribbon count (road_build.json centreline xy direction
within 30 deg) - a flyover crossing over a route is an underpass, not the route's ground.
Editor world, read-only. Needs Data/ribbon_surface.json (Ribbon_Surface_PIE.py).
Writes Data/ribbon_ground.json {label: {"g": [cm|None], "deck": [deck label|None]}} (input of Ribbon_Fit.py).
result: per ribbon (min margin cm, max float cm, samples on a deck)."""
import json, math
import unreal
P = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()) + "Scripts/Neelam/Data/"
RS = json.load(open(P + "ribbon_surface.json")); RB = json.load(open(P + "road_build.json"))["roads"]
acts = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
by = {a.get_actor_label(): a for a in acts}
COS = math.cos(math.radians(30))
decks = []
for a in acts:
    l = a.get_actor_label()
    if a.get_class().get_name() == "StaticMeshActor" and l.startswith("Road_") and ("rd_" + l.split("_")[-1]) in RB:
        o, e = a.get_actor_bounds(False)
        decks.append((o.x - e.x, o.y - e.y, o.x + e.x, o.y + e.y, a.static_mesh_component, l, RB["rd_" + l.split("_")[-1]]["pts"]))


def along(pts, x, y, tx, ty):
    """direction of the carriageway centreline nearest to (x, y) parallel to (tx, ty)?"""
    j = min(range(len(pts) - 1), key=lambda k: math.hypot((pts[k][0] + pts[k + 1][0]) / 2 - x, (pts[k][1] + pts[k + 1][1]) / 2 - y))
    dx, dy = pts[j + 1][0] - pts[j][0], pts[j + 1][1] - pts[j][1]; L = math.hypot(dx, dy) or 1.0
    return abs(dx / L * tx + dy / L * ty) >= COS


WS = unreal.SplineCoordinateSpace.WORLD; out = {}; rep = {}
for l, d in RS.items():
    s = by[l].get_component_by_class(unreal.SplineComponent); G = []; D = []; mn = 1e9; mx = -1e9; nd = 0
    for dd, xy, z in zip(d["d"], d["xy"], d["z"]):
        if xy is None: G.append(None); D.append(None); continue
        x, y = xy; rz = s.get_location_at_distance_along_spline(dd, WS).z; t = s.get_direction_at_distance_along_spline(dd, WS)
        top = None
        for x0, y0, x1, y1, c, dl, pts in decks:
            if not (x0 <= x <= x1 and y0 <= y <= y1): continue
            r = c.line_trace_component(unreal.Vector(x, y, rz + 600), unreal.Vector(x, y, rz - 600), True, False, False)
            if r and r[0].z < rz + 598 and (top is None or r[0].z > top[0]) and along(pts, x, y, t.x, t.y): top = (r[0].z, dl)
        g = z if top is None else (top[0] if z is None else max(z, top[0]))
        G.append(None if g is None else round(g, 1)); D.append(top[1] if top else None); nd += top is not None
        if g is not None:
            h = rz - g; mn = min(mn, h); mx = max(mx, h)
    out[l] = {"g": G, "deck": D}; rep[l] = (round(mn), round(mx), nd)
json.dump(out, open(P + "ribbon_ground.json", "w"))
result = rep
