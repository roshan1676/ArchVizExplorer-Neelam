"""Merge carriageways that continue into each other into ONE road (28 Oct, client: kerb notches at the EEH ramp junction).
Separate meshes meet with square-cut ends -> V-notches in the kerb that overlapping could not hide. Editor bridge job,
globals CHAINS = [["rd_A", "rd_B"], ...] (A's end continues into B's start).
Every point of A and B is re-measured from the CURRENT deck meshes (they are the truth: road_build.json xy is the un-
aligned OSM line and its width_m is not the built width): scan across the road at the json point -> deck centre (xy),
deck height (median at the centre, minus the 12 cm deck) and width (hit span minus the two 35 cm kerbs). The chain becomes
road A in road_build.json (pts / widths / ground; lanes of A; no "ext"); B is removed from road_build.json and its Road_*
actor + RoadCut_* are deleted after the merged mesh is imported (MODE "delete_old").
MODE "build" -> road_build.json (backup .pre_merge once) + Data/road_merge.json, then: Blender build_roads.py --split ->
Saved/NeelamBridge/road_fbx_merge, Fix_CheckNaka_Import.py with the paths swapped, MODE "delete_old", Fix_RoadCuts.py fix."""
import json, math, os, shutil, time
import unreal
MODE = globals().get("MODE", "build"); CHAINS = globals().get("CHAINS", [])
P = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()) + "Scripts/Neelam/Data/"
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
acts = {a.get_actor_label(): a for a in EAS.get_all_level_actors()}
DECK, KW = 12.0, 35.0


def save(path, data):
    for k in range(20):
        try:
            with open(path + ".tmp", "w") as f: json.dump(data, f)
            os.replace(path + ".tmp", path); return
        except OSError: time.sleep(0.5)
    raise OSError("could not write " + path)


def deck(rid):
    return next(acts[l] for l in acts if l.startswith("Road_") and l.endswith("_" + rid[3:]) and acts[l].get_class().get_name() == "StaticMeshActor")


def measure(rid, pts):
    c = deck(rid).static_mesh_component; out = []
    for i in range(len(pts)):
        p, q = pts[max(i - 1, 0)], pts[min(i + 1, len(pts) - 1)]; dx, dy = q[0] - p[0], q[1] - p[1]; l = math.hypot(dx, dy) or 1; nx, ny = -dy / l, dx / l
        hit = []
        for o in range(-1600, 1601, 25):
            h = c.line_trace_component(unreal.Vector(pts[i][0] + nx * o, pts[i][1] + ny * o, 60000), unreal.Vector(pts[i][0] + nx * o, pts[i][1] + ny * o, -60000), True, False, False)
            if h: hit.append((o, h[0].z))
        if not hit: out.append(None); continue
        lo, hi = hit[0][0], hit[-1][0]; m = (lo + hi) / 2
        zc = sorted(z for o, z in hit if abs(o - m) <= 100) or sorted(z for o, z in hit)
        out.append([pts[i][0] + nx * m, pts[i][1] + ny * m, zc[len(zc) // 2] - DECK, max(3.0, (hi - lo - 2 * KW) / 100)])
    return out


J = json.load(open(P + "road_build.json")); R = J["roads"]
if MODE == "build":
    if not os.path.exists(P + "road_build.json.pre_merge"): shutil.copy(P + "road_build.json", P + "road_build.json.pre_merge")
    out = {}; rep = {}
    for a_id, b_id in CHAINS:
        A, B = R[a_id], R[b_id]
        ma, mb = measure(a_id, A["pts"]), measure(b_id, B["pts"])
        rows = [(m, g) for m, g in zip(ma, A.get("ground", [None] * len(ma)))] + [(m, g) for m, g in list(zip(mb, B.get("ground", [None] * len(mb))))[1:]]
        rows = [(m, g) for m, g in rows if m is not None]
        # drop points closer than 1 m to the previous one (the joint)
        keep = [rows[0]]
        for m, g in rows[1:]:
            if math.hypot(m[0] - keep[-1][0][0], m[1] - keep[-1][0][1]) >= 100: keep.append((m, g))
        new = dict(A); new.pop("ext", None)
        new["pts"] = [[round(m[0], 1), round(m[1], 1), round(m[2], 1)] for m, g in keep]
        new["widths"] = [round(m[3], 2) for m, g in keep]; new["ground"] = [g for m, g in keep]
        new["merged_from"] = [a_id, b_id]; R[a_id] = new; del R[b_id]; out[a_id] = new
        ws = new["widths"]; rep[a_id] = {"points": len(new["pts"]), "width_m_min_max": [min(ws), max(ws)], "dropped": len(ma) + len(mb) - 1 - len(new["pts"])}
    save(P + "road_build.json", J); save(P + "road_merge.json", {"roads": out}); save(P + "road_merge_chains.json", CHAINS)
    result = rep
elif MODE == "delete_old":
    gone = []
    for a_id, b_id in json.load(open(P + "road_merge_chains.json")):
        for l in list(acts):
            if (l.startswith("Road_") and l.endswith("_" + b_id[3:]) and acts[l].get_class().get_name() == "StaticMeshActor") or l == "RoadCut_" + b_id[3:]:
                EAS.destroy_actor(acts[l]); gone.append(l)
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    result = {"deleted": gone}
