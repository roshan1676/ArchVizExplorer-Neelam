"""Rebuild every RoadCut_<id> map cut-out from the REAL deck footprint (27 Oct, client: EEH "pits"). Several Road_* meshes
sit up to ~7 m sideways off their Data/road_build.json centreline (meshes came from an older alignment), while the cut
polygons follow road_build.json -> part of the cut is not covered by the deck (base terrain shows through = brown pits)
and part of the deck lies over uncut photogrammetry (map pokes through).
Per every 4th centreline point: scan across the road (-SCAN..+SCAN, 50 cm) with complex traces on the deck mesh -> deck
edges [lo, hi]; cut ring = edges +- PAD. Points without deck are skipped (gaps stay uncut = the map shows, as before).
Editor world. MODE "audit" (per road: deck centre offset vs json, max/median m) / "fix" (rewrite rings, refresh tiles, save)."""
import json, math
import unreal
MODE = globals().get("MODE", "audit"); SCAN, STEPW, PAD = 1600.0, 50.0, 20.0
P = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()) + "Scripts/Neelam/Data/"
RB = json.load(open(P + "road_build.json"))["roads"]
acts = {a.get_actor_label(): a for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()}


def footprint(c, pts, i):
    """deck edges across the road at centreline point i: (lo, hi) offsets in cm along the left normal, or None"""
    p, q = pts[max(i - 1, 0)], pts[min(i + 1, len(pts) - 1)]
    dx, dy = q[0] - p[0], q[1] - p[1]; l = math.hypot(dx, dy) or 1.0; nx, ny = -dy / l, dx / l
    x0, y0 = pts[i][0], pts[i][1]; hit = []
    o = -SCAN
    while o <= SCAN:
        x, y = x0 + nx * o, y0 + ny * o
        if c.line_trace_component(unreal.Vector(x, y, 60000), unreal.Vector(x, y, -60000), True, False, False): hit.append(o)
        o += STEPW
    if not hit: return None, (nx, ny)
    # the run of hits nearest the centreline (a parallel carriageway's deck is a different actor, so runs are rare)
    return (min(hit), max(hit)), (nx, ny)


rep = {}; cuts = 0
for rid, r in RB.items():
    lab = next((l for l in acts if l.startswith("Road_") and l.endswith("_" + rid[3:]) and acts[l].get_class().get_name() == "StaticMeshActor"), None)
    cut = acts.get("RoadCut_" + rid[3:])
    if lab is None or cut is None: continue
    c = acts[lab].static_mesh_component; pts = r["pts"]
    idx = list(range(0, len(pts), 4)) + ([len(pts) - 1] if (len(pts) - 1) % 4 else [])
    L, R, offs, miss = [], [], [], 0
    for i in idx:
        fp, (nx, ny) = footprint(c, pts, i)
        if fp is None: miss += 1; continue
        lo, hi = fp; offs.append(abs((lo + hi) / 2) / 100)
        L.append(unreal.Vector(pts[i][0] + nx * (hi + PAD), pts[i][1] + ny * (hi + PAD), pts[i][2]))
        R.append(unreal.Vector(pts[i][0] + nx * (lo - PAD), pts[i][1] + ny * (lo - PAD), pts[i][2]))
    if not offs: rep[rid] = "no deck found"; continue
    so = sorted(offs); rep[rid] = {"max_off_m": round(so[-1], 1), "median_off_m": round(so[len(so) // 2], 1), "no_deck_pts": miss, "of": len(idx)}
    if MODE == "fix" and len(L) >= 2:
        cut.modify(); spl = cut.get_component_by_class(unreal.SplineComponent); spl.clear_spline_points(False)
        for v in L + R[::-1]: spl.add_spline_point(v, unreal.SplineCoordinateSpace.WORLD, False)
        for q in range(spl.get_number_of_spline_points()): spl.set_spline_point_type(q, unreal.SplinePointType.LINEAR, False)
        spl.set_closed_loop(True, True); cuts += 1
if MODE == "fix":
    for t in unreal.GameplayStatics.get_all_actors_of_class(unreal.EditorLevelLibrary.get_editor_world(), unreal.Cesium3DTileset):
        try: t.refresh_tileset()
        except Exception: pass
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
result = {"mode": MODE, "cuts_rebuilt": cuts, "roads": rep}
