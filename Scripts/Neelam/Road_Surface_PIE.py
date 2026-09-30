"""Real road-surface height under every built carriageway, traced in PIE at full tile detail (29 Sep).
The first pass (Sample_Roads.py) fell into holes of not-yet-refined tiles -> 10-19 m pits in the decks. Here the player
camera hovers 380 m above each 500 m cell for 20 s (full detail, cf. Verify_Ribbons.py) and every 2nd centreline point
(6 m) is traced at 5 points across (0, +-quarter, +-(half width - 1.2 m)); the median of the tileset hits is kept.
Modes: prep (editor or PIE) -> go / trace (CELL=i, PIE) -> save  => Data/road_surface_pie.json {rd_key: [z|None per pt]}.
Flatten_Roads.py uses it before anything else."""
import json, os, math
import unreal
P = os.path.join(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()), "Scripts", "Neelam")
MODE = globals().get("MODE", "prep"); env = globals()["env"]; CC = 50000.0
SRC = globals().get("SRC", "road_build_aligned_raw.json" if os.path.exists(os.path.join(P, "Data", "road_build_aligned_raw.json")) else "road_build_raw.json")
OUT = os.path.join(P, "Data", "road_surface_pie.json")
gw = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
if MODE == "prep":
    R = json.load(open(os.path.join(P, "Data", SRC)))["roads"]
    pts, cells = [], {}
    for k, r in R.items():
        p = r["pts"]
        for i in range(0, len(p), 2):
            a, b = p[max(i - 1, 0)], p[min(i + 1, len(p) - 1)]
            dx, dy = b[0] - a[0], b[1] - a[1]; l = math.hypot(dx, dy) or 1.0
            pts.append([k, i, p[i][0], p[i][1], -dy / l, dx / l, max(0.0, r["width_m"] * 50 - 120), None])
            cells.setdefault((math.floor(p[i][0] / CC), math.floor(p[i][1] / CC)), []).append(len(pts) - 1)
    env["rs"] = pts; env["rs_cells"] = sorted(cells.items())
    result = {"points": len(pts), "cells": len(cells)}
elif MODE == "go":
    (cx, cy), _ = env["rs_cells"][CELL]
    pc = unreal.GameplayStatics.get_player_controller(gw, 0)
    cam = next((a for a in unreal.GameplayStatics.get_all_actors_of_class(gw, unreal.CameraActor) if a.get_actor_label() == "Neelam_AlignCam"), None)
    if cam:      # view target camera (Road_Align_PIE.py) -> tiles stream around it
        cam.set_actor_location_and_rotation(unreal.Vector((cx + .5) * CC, (cy + .5) * CC, 60000), unreal.Rotator(roll=0.0, pitch=-90.0, yaw=0.0), False, True)
        pc.set_view_target_with_blend(cam, 0.0)
    else:
        pawn = pc.get_controlled_pawn()
        arm = pawn.get_component_by_class(unreal.SpringArmComponent); arm.set_editor_property("do_collision_test", False); arm.set_editor_property("target_arm_length", 1.0)
        pawn.set_actor_location(unreal.Vector((cx + .5) * CC, (cy + .5) * CC, 38000), False, True); pc.set_control_rotation(unreal.Rotator(roll=0.0, pitch=-89.0, yaw=0.0))
    result = CELL
elif MODE == "trace":
    _, idx = env["rs_cells"][CELL]; hit = 0
    if env.get("rs_world") != gw.get_path_name():      # ribbons / poles / trees have collision -> ignore everything but the map
        env["rs_ignore"] = [a for a in unreal.GameplayStatics.get_all_actors_of_class(gw, unreal.Actor) if not isinstance(a, unreal.Cesium3DTileset)]
        env["rs_world"] = gw.get_path_name()
    for i in idx:
        k, j, x, y, nx, ny, o, _ = env["rs"][i]; zs = []
        for off in (0.0, o / 2, -o / 2, o, -o):
            hs = unreal.SystemLibrary.line_trace_multi(gw, unreal.Vector(x + nx * off, y + ny * off, 60000), unreal.Vector(x + nx * off, y + ny * off, -60000),
                                                       unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, env["rs_ignore"], unreal.DrawDebugTrace.NONE, True)
            for h in hs or []:
                t = h.to_tuple()
                if t[9] is not None and isinstance(t[9], unreal.Cesium3DTileset): zs.append(float(t[4].z)); break
        if zs:
            zs.sort(); env["rs"][i][7] = zs[len(zs) // 2]; hit += 1
    result = [CELL, hit, len(idx)]
elif MODE == "save":
    out = {}
    R = json.load(open(os.path.join(P, "Data", SRC)))["roads"]
    for k, r in R.items(): out[k] = [None] * len(r["pts"])
    for k, j, x, y, nx, ny, o, z in env["rs"]:
        if z is not None: out[k][j] = round(z, 1)
    json.dump(out, open(OUT, "w"))
    result = {"traced": sum(1 for v in out.values() for z in v if z is not None), "total": len(env["rs"])}
