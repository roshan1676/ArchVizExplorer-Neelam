"""Fit every ribbon's spline heights to its REAL ground (27 Oct, client: "no route part inside the map, none broken").
Ground per 3 m sample = Data/ribbon_ground.json (ribbon_ground_check.py: our road deck where the ribbon runs along that
carriageway, else the traced map). Per spline point:
  LOW  (under ground + lift within +-4.5 m)  -> raised to it (traffic strips were 4-7 m INSIDE their flyover decks)
  (no lowering: a "hovering" ribbon over a bridge whose deck was not detected got pulled down into the creek -> V-dip.
   Hovering is left alone; Ribbon_Valleys.py fills short dips.)
Lift = Ribbon_Clearance.py's: routes 30 cm + 4 cm per route (stacking), road glows 35, traffic 20.
Editor world (not PIE). MODE "audit" / "fix" (fix rebuilds the ribbons and saves the level)."""
import json, bisect
import unreal
P = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()) + "Scripts/Neelam/Data/"
MODE = globals().get("MODE", "audit")
RS = json.load(open(P + "ribbon_surface.json")); RG = json.load(open(P + "ribbon_ground.json"))
WS = unreal.SplineCoordinateSpace.WORLD
NEAR, ENV, FLOAT = 450.0, 1200.0, 150.0


def lift(label, routes):
    if label.startswith("Route_"): return 30.0 + 4.0 * routes.index(label)
    if label.startswith("Road_"): return 35.0
    return 20.0


def rebuild(a):
    s = a.get_component_by_class(unreal.SplineComponent); s.update_spline()
    if a.get_class().get_name() == "BP_Route_C":
        c = a.get_editor_property("Route_Color")
        a.set_editor_property("Route_Color", unreal.LinearColor(c.r * 0.999 + 0.0005, c.g, c.b, c.a)); a.set_editor_property("Route_Color", c)
    else:
        w = a.get_editor_property("Width_Road")
        a.set_editor_property("Width_Road", w + 0.01); a.set_editor_property("Width_Road", w)


def window_max(D, G, lo, hi):
    i, j = bisect.bisect_left(D, lo), bisect.bisect_right(D, hi)
    v = [g for g in G[i:j] if g is not None]
    return max(v) if v else None


by = {a.get_actor_label(): a for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()}
routes = sorted(l for l in RS if l.startswith("Route_"))
rep = {}
for l in RS:
    a = by[l]; s = a.get_component_by_class(unreal.SplineComponent); clr = lift(l, routes)
    D = RS[l]["d"]; G = RG[l]["g"]; up = []; down = []
    for k in range(s.get_number_of_spline_points()):
        dk = s.get_distance_along_spline_at_spline_point(k); p = s.get_location_at_spline_point(k, WS)
        near = window_max(D, G, dk - NEAR, dk + NEAR); env = window_max(D, G, dk - ENV, dk + ENV)
        if near is None: continue
        if p.z < near + clr - 2: up.append((k, near + clr - p.z))
    if not up and not down: continue
    rep[l] = {"raise": len(up), "max_raise_m": round(max([u[1] for u in up] or [0]) / 100, 2),
              "lower": len(down), "max_lower_m": round(max([d[1] for d in down] or [0]) / 100, 2)}
    if MODE == "fix":
        a.modify(); s.modify()
        for k, dz in up:
            p = s.get_location_at_spline_point(k, WS); s.set_location_at_spline_point(k, unreal.Vector(p.x, p.y, p.z + dz), WS, False)
        for k, dz in down:
            p = s.get_location_at_spline_point(k, WS); s.set_location_at_spline_point(k, unreal.Vector(p.x, p.y, p.z - dz), WS, False)
        rebuild(a)
if MODE == "fix":
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
result = {"mode": MODE, "ribbons": len(rep), "detail": rep}
