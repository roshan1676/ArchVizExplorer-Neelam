"""Night traffic: moving head/tail-light streams (template M_Road_Lighting via BP_RoadTool, no poles) along the key roads
and every landmark drive route. Routes share roads, so the network is de-duplicated: a route only gets a strip where
no earlier strip already runs within 25 m. Outliner folder Neelam/Surroundings/traffic (re-running replaces it)."""
import json, os, sys, importlib, math
import unreal
P = os.path.join(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()), "Scripts", "Neelam")
sys.path.insert(0, P)
import connectivity_lib as C; importlib.reload(C)
ROAD = unreal.EditorAssetLibrary.load_blueprint_class("/Game/ArchVizExplorer/Blueprints/BP_RoadTool")
FOLDER = "Neelam/Surroundings/traffic"
LIFT = globals().get("TRAFFIC_LIFT", 120.0)
WIDTH = {"eeh": 24.0, "mar": 16.0, "vb": 12.0}          # metres; routes default 9 m
for a in [a for a in C.EAS.get_all_level_actors() if str(a.get_folder_path()).startswith(FOLDER)]:
    C.EAS.destroy_actor(a)
lines = []
RB = json.load(open(os.path.join(P, "Data", "road_build.json")))["roads"]
for ph in ("phase2", "phase3"):
    G = json.load(open(os.path.join(P, "Data", "connectivity_%s.json" % ph), encoding="utf-8"))
    lines += [("route_" + k, v["pts"], 9.0) for k, v in sorted(G["routes"].items(), key=lambda kv: len(kv[1]["pts"]))]
lines.sort(key=lambda l: 0 if l[0].startswith("road_") else 1)
cov = set()
def cell(p): return (int(p[0] * 110540 // 25), int(p[1] * 104900 // 25))
def near(p):
    c = cell(p); return any((c[0] + i, c[1] + j) in cov for i in (-1, 0, 1) for j in (-1, 0, 1))
# no cars through the Neelam building: drop points inside the site boundary (+4 m)
SITE = json.load(open(os.path.join(P, "Data", "site_outline.json")))["cut"]
XF = C.ROOT.get_actor_transform()
POLY = [(lambda w: (w.x, w.y))(XF.transform_location(unreal.Vector(x, y, 0))) for x, y in SITE]
def inside(x, y):
    c = False; j = len(POLY) - 1
    for i in range(len(POLY)):
        (xi, yi), (xj, yj) = POLY[i], POLY[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi: c = not c
        j = i
    return c
def seg_d(x, y):
    best = 1e18
    for (ax, ay), (bx, by) in zip(POLY, POLY[1:] + POLY[:1]):
        L2 = (bx - ax) ** 2 + (by - ay) ** 2 or 1.0; t = max(0, min(1, ((x - ax) * (bx - ax) + (y - ay) * (by - ay)) / L2))
        best = min(best, math.hypot(x - ax - t * (bx - ax), y - ay - t * (by - ay)))
    return best
def in_site(p):
    w = C.to_xy(*p); return inside(w.x, w.y) or seg_d(w.x, w.y) < 400.0
report = []; trimmed = 0
for name, pts, width in lines:
    segs, cur = [], []
    for i, p in enumerate(pts):
        w_ = C.to_xy(*p)
        bad = near(p) or in_site(p) or C.road_deck(w_.x, w_.y, 400.0) is not None     # built roads get their own lanes
        trimmed += in_site(p)
        if bad:
            if len(cur) >= 4: segs.append(cur)
            cur = []
        else:
            cur.append(i)
    if len(cur) >= 4: segs.append(cur)
    for p in pts: cov.add(cell(p))
    for i, idx in enumerate(segs):
        vs, precise = C.envelope_z(name, pts, idx, 0.0)
        seg = [pts[k] for k in idx]
        t = C.EAS.spawn_actor_from_class(ROAD, vs[0])
        t.set_actor_label("Traffic_%s_%d" % (name, i)); t.set_folder_path(FOLDER)
        spl = t.get_component_by_class(unreal.SplineComponent); spl.clear_spline_points(False)
        for v in vs: spl.add_spline_point(unreal.Vector(v.x, v.y, v.z + LIFT), unreal.SplineCoordinateSpace.WORLD, False)
        for q in range(spl.get_number_of_spline_points()):   # clamped: no overshoot/dip between points
            spl.set_spline_point_type(q, unreal.SplinePointType.CURVE_CLAMPED, False)
        spl.update_spline()
        for pr in ("spline_has_been_edited", "input_spline_points_to_construction_script"):
            try: spl.set_editor_property(pr, True)
            except Exception: pass
        for k, val in (("DrawSplinePointNumbers?", False), ("Build_LightPoles?", False), ("Collision_Road?", False),
                       ("Traffic_Speed_01", 0.06), ("Traffic_Speed_02", 0.04), ("Width_Road", width)):
            t.set_editor_property(k, val)
        t.set_editor_property("Spacing_Road", 3000.0)            # last: re-runs construction with the edited spline
        report.append([t.get_actor_label(), len(seg), len(t.get_components_by_class(unreal.SplineMeshComponent))])
# ---- one-way traffic on every built carriageway (OSM way direction = driving direction)
for k, r in RB.items():
    pts = r["pts"]
    if len(pts) < 6: continue
    t = C.EAS.spawn_actor_from_class(ROAD, unreal.Vector(*pts[0]))
    t.set_actor_label("Traffic_lane_%s" % k[3:]); t.set_folder_path(FOLDER)
    spl = t.get_component_by_class(unreal.SplineComponent); spl.clear_spline_points(False)
    for x, y, z in pts[::2] + ([pts[-1]] if len(pts) % 2 == 0 else []):
        spl.add_spline_point(unreal.Vector(x, y, z + C.DECK_TOP + 5.0), unreal.SplineCoordinateSpace.WORLD, False)
    for q in range(spl.get_number_of_spline_points()): spl.set_spline_point_type(q, unreal.SplinePointType.CURVE_CLAMPED, False)
    spl.update_spline()
    for pr in ("spline_has_been_edited", "input_spline_points_to_construction_script"):
        try: spl.set_editor_property(pr, True)
        except Exception: pass
    for kk, val in (("DrawSplinePointNumbers?", False), ("Build_LightPoles?", False), ("Collision_Road?", False), ("OneWay_Traffic?", True),
                    ("Traffic_Speed_01", 0.06), ("Traffic_Speed_02", 0.05), ("Width_Road", r["width_m"] - 0.6)):
        t.set_editor_property(kk, val)
    t.set_editor_property("Spacing_Road", 1500.0)
    report.append([t.get_actor_label(), len(pts), 0])
result = {"strips": len(report), "trimmed_in_site": trimmed, "detail": report}
