"""Heights of the grey context blocks from the photogrammetry (PIE, 30 Sep). For every building in Data/massing_sel.json:
roof = median of 5 traces inside the footprint (centroid + 4 points 40 % towards the corners), ground = lowest of
16 traces 8 / 18 m outside the corners (streets). Camera Neelam_AlignCam 450 m above 500 m cells (>= 35 s each; from 1100 m the tiles are too coarse - roofs flattened).
Modes: prep -> go / trace (CELL) -> save => Data/massing_heights.json {id: [ground, roof]}."""
import json, os, math
import unreal
P = os.path.join(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()), "Scripts", "Neelam")
MODE = globals().get("MODE", "prep"); env = globals()["env"]; CC = 50000.0
gw = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
if MODE == "prep":
    S = json.load(open(os.path.join(P, "Data", "massing_sel.json"))); cells = {}
    for i, b in enumerate(S):
        cells.setdefault((math.floor(b["c"][0] / CC), math.floor(b["c"][1] / CC)), []).append(i)
    env["ms"] = S; env["ms_cells"] = sorted(cells.items()); env["ms_res"] = {}
    result = {"buildings": len(S), "cells": len(cells)}
elif MODE == "go":
    (cx, cy), _ = env["ms_cells"][CELL]
    pc = unreal.GameplayStatics.get_player_controller(gw, 0)
    cam = next(a for a in unreal.GameplayStatics.get_all_actors_of_class(gw, unreal.CameraActor) if a.get_actor_label() == "Neelam_AlignCam")
    cam.set_actor_location_and_rotation(unreal.Vector((cx + .5) * CC, (cy + .5) * CC, 45000), unreal.Rotator(roll=0.0, pitch=-90.0, yaw=0.0), False, True)
    cam.camera_component.set_editor_property("field_of_view", 90.0); pc.set_view_target_with_blend(cam, 0.0)
    result = CELL
elif MODE == "trace":
    if env.get("ms_world") != gw.get_path_name():
        env["ms_ignore"] = [a for a in unreal.GameplayStatics.get_all_actors_of_class(gw, unreal.Actor) if not isinstance(a, unreal.Cesium3DTileset)]
        env["ms_world"] = gw.get_path_name()
    def z_at(x, y):
        hs = unreal.SystemLibrary.line_trace_multi(gw, unreal.Vector(x, y, 80000), unreal.Vector(x, y, -60000), unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True,
                                                   env["ms_ignore"], unreal.DrawDebugTrace.NONE, True)
        for h in hs or []:
            t = h.to_tuple()
            if t[9] is not None and isinstance(t[9], unreal.Cesium3DTileset): return float(t[4].z)
        return None
    _, idx = env["ms_cells"][CELL]; ok = 0
    for i in idx:
        b = env["ms"][i]; cx, cy = b["c"]; pts = b["pts"]; n = len(pts)
        corners = [pts[int(k * n / 4) % n] for k in range(4)]
        roof = [z_at(cx, cy)] + [z_at(cx + 0.4 * (x - cx), cy + 0.4 * (y - cy)) for x, y in corners]
        grd = []                                   # dense city: 4 m outside is often the next roof -> lowest of 16 ring samples
        for x, y in [pts[int(k * n / 8) % n] for k in range(8)]:
            dx, dy = x - cx, y - cy; L = math.hypot(dx, dy) or 1.0
            for off in (800, 1800): grd.append(z_at(x + dx / L * off, y + dy / L * off))
        roof = sorted(z for z in roof if z is not None); grd = sorted(z for z in grd if z is not None)
        if roof and grd:
            env["ms_res"][b["id"]] = [grd[0], roof[len(roof) // 2]]; ok += 1
    result = [CELL, ok, len(idx)]
elif MODE == "save":
    json.dump(env["ms_res"], open(os.path.join(P, "Data", "massing_heights.json"), "w"))
    result = len(env["ms_res"])
