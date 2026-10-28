"""Rebuild road carriageways whose deck mesh jogs / stops short of its junction (27-28 Oct: EEH ramp rd_131599713 jogged
8 m; rd_185467270 / rd_185467297 ended short of their junction = deck hanging in the air). Editor bridge job, globals RIDS.
Per centreline point of Data/road_build.json: scan the current deck across the road; where its centre is within ON m of
the json line, keep the measured centre + height (meets the neighbours as today); elsewhere use the json line and the
json's own slope, shifted by the (measured - json) height difference interpolated between the nearest kept points
(ends: the nearest kept difference) - an off-line run of 180 m must keep its slope, not go flat. Writes the new pts into road_build.json
(backup .pre_rebuild_line once) and Data/road_rebuild_line.json for Blender/build_roads.py --split; then run Blender and
Fix_CheckNaka_Import.py with "road_fbx_checknaka" -> "road_fbx_line", "road_checknaka.json" -> "road_rebuild_line.json"."""
import json, math, shutil, os
import unreal
RIDS = globals()["RIDS"]; ON = 200.0; DECK = 12.0
OFF = globals().get("OFF", {})   # {rid: first index to trust} - points before it are treated as off-line (re-run after a bad import)
P = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()) + "Scripts/Neelam/Data/"
J = json.load(open(P + "road_build.json"))
acts = {a.get_actor_label(): a for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()}
if not os.path.exists(P + "road_build.json.pre_rebuild_line"): shutil.copy(P + "road_build.json", P + "road_build.json.pre_rebuild_line")
outj = {}; rep = {}
for rid in RIDS:
    r = J["roads"][rid]; pts = r["pts"]
    lab = next(l for l in acts if l.startswith("Road_") and l.endswith("_" + rid[3:]) and acts[l].get_class().get_name() == "StaticMeshActor")
    c = acts[lab].static_mesh_component; meas = []
    for i in range(len(pts)):
        p, q = pts[max(i - 1, 0)], pts[min(i + 1, len(pts) - 1)]; dx, dy = q[0] - p[0], q[1] - p[1]; l = math.hypot(dx, dy) or 1; nx, ny = -dy / l, dx / l
        hit = []; o = -1600.0
        while o <= 1600:
            h = c.line_trace_component(unreal.Vector(pts[i][0] + nx * o, pts[i][1] + ny * o, 60000), unreal.Vector(pts[i][0] + nx * o, pts[i][1] + ny * o, -60000), True, False, False)
            if h: hit.append((o, h[0].z))
            o += 50
        if hit:
            mid = (hit[0][0] + hit[-1][0]) / 2; zc = sorted(z for o_, z in hit if abs(o_ - mid) <= 150)
            meas.append((mid, zc[len(zc) // 2] if zc else None, nx, ny))
        else: meas.append((None, None, nx, ny))
    good = [i for i, m in enumerate(meas) if m[0] is not None and abs(m[0]) <= ON and m[1] is not None and i >= OFF.get(rid, 0)]
    if not good: rep[rid] = "no deck on line - skipped"; continue
    new = []
    for i, p in enumerate(pts):
        if i in good:
            m, z, nx, ny = meas[i]; new.append([p[0] + nx * m, p[1] + ny * m, z - DECK])
        else:
            a = max([g for g in good if g < i], default=None); b = min([g for g in good if g > i], default=None)
            da = meas[a][1] - DECK - pts[a][2] if a is not None else None; db = meas[b][1] - DECK - pts[b][2] if b is not None else None
            dz = db if a is None else da if b is None else da + (db - da) * (i - a) / (b - a)
            new.append([p[0], p[1], p[2] + dz])
    r["pts"] = [[round(v, 1) for v in p] for p in new]; outj[rid] = r
    rep[rid] = {"points": len(pts), "rebuilt_from_line": [i for i in range(len(pts)) if i not in good]}
json.dump(J, open(P + "road_build.json", "w")); json.dump({"roads": outj}, open(P + "road_rebuild_line.json", "w"))
result = rep
