"""Ribbon snap to the built carriageways (30 Sep, client: "splines go out of the route / cut across / hide under the road").
The landmark routes (Route_*) and their traffic strips (Traffic_route_*) come from OSRM/OSM centre lines, but the grey
carriageway meshes (EEH, V B Phadke, Mulund-Airoli; Data/road_build.json) were re-aligned to the imagery -> on those roads
the ribbons ran beside / under the deck and cut diagonally across junctions.
Per spline point: nearest carriageway segment in the SAME travel direction (heading within 40 deg; OSM carriageways are
ordered in the driving direction), within half width + 10 m and within 6 m in height -> the point moves onto that
carriageway centre, z = deck top + 12 cm + the ribbon lift (routes 30 cm + 4 cm/route, traffic 20 cm). Only runs of
>= 3 matched points are snapped (run ends that would jump > 3 m sideways are left alone - that is where the route leaves the road) (no single points pulled sideways at crossings); isolated 1-point gaps inside a run are
snapped too. Points on local streets are not touched. Point type -> CurveClamped (no overshoot at corners).
Road_* glows (median lines, Fix_Highway_Glow.py) and Traffic_lane_* (built from the carriageways) are not changed.
MODE audit / fix. Order: Ribbon_Heights -> Ribbon_Snap -> Ribbon_Clearance."""
import json, os, math
import unreal
P = os.path.join(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()), "Scripts", "Neelam")
MODE = globals().get("MODE", "audit")
RB = json.load(open(os.path.join(P, "Data", "road_build.json")))["roads"]
WS = unreal.SplineCoordinateSpace.WORLD
DECK = 12.0; HD = math.radians(40); ZT = 600.0
segs = []                      # (ax, ay, az, bx, by, bz, heading, halfwidth_cm, key)
grid = {}
for k, r in RB.items():
    pts = r["pts"]; hw = r["width_m"] * 50
    for i in range(len(pts) - 1):
        a, b = pts[i], pts[i + 1]
        if math.hypot(b[0] - a[0], b[1] - a[1]) < 1: continue
        segs.append((a[0], a[1], a[2], b[0], b[1], b[2], math.atan2(b[1] - a[1], b[0] - a[0]), hw, k))
        si = len(segs) - 1
        for gx in range(int(min(a[0], b[0]) // 3000) - 1, int(max(a[0], b[0]) // 3000) + 2):
            for gy in range(int(min(a[1], b[1]) // 3000) - 1, int(max(a[1], b[1]) // 3000) + 2):
                grid.setdefault((gx, gy), set()).add(si)


def nearest(x, y, z, head):
    best = None
    for si in grid.get((int(x // 3000), int(y // 3000)), ()):
        ax, ay, az, bx, by, bz, h, hw, k = segs[si]
        dh = abs((head - h + math.pi) % (2 * math.pi) - math.pi)
        if dh > HD: continue
        dx, dy = bx - ax, by - ay; L2 = dx * dx + dy * dy
        t = max(0.0, min(1.0, ((x - ax) * dx + (y - ay) * dy) / L2))
        px, py, pz = ax + t * dx, ay + t * dy, az + t * (bz - az)
        d = math.hypot(x - px, y - py)
        if d > hw + 1000 or abs(z - pz) > ZT: continue
        if best is None or d < best[0]: best = (d, px, py, pz, k)
    return best


def lift(l, routes):
    return 30.0 + 4.0 * routes.index(l) if l.startswith("Route_") else 20.0


def rebuild(a):
    s = a.get_component_by_class(unreal.SplineComponent)
    s.update_spline()
    for pr in ("spline_has_been_edited", "input_spline_points_to_construction_script"):
        try: s.set_editor_property(pr, True)
        except Exception: pass
    if a.get_class().get_name() == "BP_Route_C":
        c = a.get_editor_property("Route_Color")
        a.set_editor_property("Route_Color", unreal.LinearColor(c.r * 0.999 + 0.0005, c.g, c.b, c.a)); a.set_editor_property("Route_Color", c)
    else:
        w = a.get_editor_property("Width_Road")
        a.set_editor_property("Width_Road", w + 0.01); a.set_editor_property("Width_Road", w)


def run():
    acts = {a.get_actor_label(): a for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()}
    routes = sorted(l for l in acts if l.startswith("Route_") and acts[l].get_class().get_name() == "BP_Route_C")
    rep = {}
    for l, a in sorted(acts.items()):
        if not ((l.startswith("Route_") and a.get_class().get_name() == "BP_Route_C") or (l.startswith("Traffic_route_") and a.get_class().get_name() == "BP_RoadTool_C")):
            continue
        s = a.get_component_by_class(unreal.SplineComponent); n = s.get_number_of_spline_points()
        P = [s.get_location_at_spline_point(i, WS) for i in range(n)]
        m = []
        for i in range(n):
            j0, j1 = max(0, i - 1), min(n - 1, i + 1)
            head = math.atan2(P[j1].y - P[j0].y, P[j1].x - P[j0].x)
            m.append(nearest(P[i].x, P[i].y, P[i].z, head))
        ok = [x is not None for x in m]
        for i in range(1, n - 1):                       # fill 1-point holes inside a run
            if not ok[i] and ok[i - 1] and ok[i + 1]:
                q = nearest(P[i].x, P[i].y, P[i].z, math.atan2(P[i + 1].y - P[i - 1].y, P[i + 1].x - P[i - 1].x))
                if q is None:
                    hd = math.atan2(P[i + 1].y - P[i - 1].y, P[i + 1].x - P[i - 1].x)
                    HDs = globals()["HD"]; globals()["HD"] = math.radians(70); q = nearest(P[i].x, P[i].y, P[i].z, hd); globals()["HD"] = HDs
                if q: m[i] = q; ok[i] = True
        runs = []; i = 0
        while i < n:
            if ok[i]:
                j = i
                while j + 1 < n and ok[j + 1]: j += 1
                a0, a1 = i, j                             # run ends that jump sideways are where the route leaves the road
                while a0 <= a1 and m[a0][0] > 300: a0 += 1
                while a1 >= a0 and m[a1][0] > 300: a1 -= 1
                if a1 - a0 + 1 >= 3: runs.append((a0, a1))
                i = j + 1
            else: i += 1
        moved = [i for r0, r1 in runs for i in range(r0, r1 + 1)]
        if not moved:
            continue
        lat = [m[i][0] for i in moved]
        prof = [(r0, r1, [round(m[i][0] / 100, 1) for i in range(r0, r1 + 1)]) for r0, r1 in runs]
        rep[l] = {"prof": prof, "points": n, "snapped": len(moved), "runs": len(runs), "max_shift_m": round(max(lat) / 100, 1), "mean_shift_m": round(sum(lat) / len(lat) / 100, 1),
                  "roads": sorted(set(m[i][4] for i in moved))[:6]}
        if MODE != "fix": continue
        lf = lift(l, routes)
        for i in moved:
            d, px, py, pz, k = m[i]
            s.set_location_at_spline_point(i, unreal.Vector(px, py, pz + DECK + lf), WS, False)
        for i in range(n):
            s.set_spline_point_type(i, unreal.SplinePointType.CURVE_CLAMPED, False)
        rebuild(a)
    if MODE == "fix":
        unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    return {"mode": MODE, "ribbons": len(rep), "detail": rep}


result = run()
