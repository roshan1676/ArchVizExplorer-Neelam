"""After Fix_CheckNaka_Road.py raised the plaza deck up to 2 m, the road glow / routes / traffic ribbons on it ended up
under the asphalt (glow looked broken). Bridge job: every BP_Route / BP_RoadTool spline point over the 3 Check Naka
carriageways is raised to deck top + its normal lift (Ribbon_Clearance.py values), then the construction script is
nudged (only re-runs on a real property change)."""
import os, json, math
import unreal
PROJ = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
B = json.load(open(os.path.join(PROJ, "Scripts", "Neelam", "Data", "road_checknaka.json")))["roads"]
WS = unreal.SplineCoordinateSpace.WORLD
DECK = 12.0   # build_roads.py deck top above the centreline (cm)
SEGS = [(r["pts"][i], r["pts"][i + 1], r["width_m"] * 50 + 300) for r in B.values() for i in range(len(r["pts"]) - 1)]


def deck_z(x, y, extra=0.0):
    """deck top under (x, y); extra widens the corridor (the EEH glow runs on the median between the carriageways,
    there the higher of the two decks counts so the glow is not hidden behind the raised kerbs)"""
    best = None; hi = None
    for a, b, half in SEGS:
        dx, dy = b[0] - a[0], b[1] - a[1]; L2 = dx * dx + dy * dy or 1.0
        t = max(0.0, min(1.0, ((x - a[0]) * dx + (y - a[1]) * dy) / L2))
        d = math.hypot(a[0] + t * dx - x, a[1] + t * dy - y)
        z = a[2] + t * (b[2] - a[2]) + DECK
        if d <= half and (best is None or d < best[0]): best = (d, z)
        if extra and d <= half + extra: hi = z if hi is None else max(hi, z)
    return hi if extra else (best[1] if best else None)


def lift(label, routes):
    if label.startswith("Poles_"): return -30.0   # Place_RoadPoles.py: pole base 30 cm into the deck
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


acts = [a for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors() if a.get_class().get_name() in ("BP_Route_C", "BP_RoadTool_C")]
routes = sorted(a.get_actor_label() for a in acts if a.get_actor_label().startswith("Route_"))
rep = {}
for a in acts:
    s = a.get_component_by_class(unreal.SplineComponent)
    if s is None: continue
    clr = lift(a.get_actor_label(), routes); n = 0; mx = 0.0
    for k in range(s.get_number_of_spline_points()):
        p = s.get_location_at_spline_point(k, WS)
        glow = a.get_actor_label().startswith("Road_")
        z = deck_z(p.x, p.y, 1500.0 if glow else 0.0)
        if z is None: continue
        if (p.z < z + clr - 2) or (a.get_actor_label().startswith("Poles_") and abs(p.z - (z + clr)) > 2):
            mx = max(mx, z + clr - p.z)
            if n == 0: a.modify(); s.modify()
            s.set_location_at_spline_point(k, unreal.Vector(p.x, p.y, z + clr), WS, False); n += 1
    if n:
        rebuild(a); rep[a.get_actor_label()] = (n, round(mx))
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
result = rep
