"""Ground under the railway (PIE, 4 Oct): Data/rail_pts.json (UE xy, 10 m along rails / platforms / station / FOBs, 2.7 km
round the site) -> Data/rail_heights.json {"x,y": [z_top, z_low]} - top = first hit on the Google tiles, low = lowest of
5 samples within 4 m (trains / canopies in the photogrammetry). Camera Neelam_AlignCam 450 m above 500 m cells.
Modes prep -> go/trace (CELL) -> save (same loop as Massing_PIE.py)."""
import json, os, math
import unreal
P = os.path.join(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()), "Scripts", "Neelam")
MODE = globals().get("MODE", "prep"); env = globals()["env"]; CC = 50000.0
gw = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
if MODE == "prep":
    pts = json.load(open(os.path.join(P, "Data", "rail_pts.json"))); cells = {}
    for p in pts: cells.setdefault((math.floor(p[0] / CC), math.floor(p[1] / CC)), []).append(p)
    env["rh_cells"] = sorted(cells.items()); env["rh_res"] = {}
    result = {"points": len(pts), "cells": len(cells)}
elif MODE == "go":
    (cx, cy), _ = env["rh_cells"][CELL]
    pc = unreal.GameplayStatics.get_player_controller(gw, 0)
    cam = next(a for a in unreal.GameplayStatics.get_all_actors_of_class(gw, unreal.CameraActor) if a.get_actor_label() == "Neelam_AlignCam")
    cam.set_actor_location_and_rotation(unreal.Vector((cx + .5) * CC, (cy + .5) * CC, 45000), unreal.Rotator(roll=0.0, pitch=-90.0, yaw=0.0), False, True)
    cam.camera_component.set_editor_property("field_of_view", 90.0); pc.set_view_target_with_blend(cam, 0.0)
    result = CELL
elif MODE == "trace":
    if env.get("rh_world") != gw.get_path_name():
        env["rh_ignore"] = [a for a in unreal.GameplayStatics.get_all_actors_of_class(gw, unreal.Actor) if not isinstance(a, unreal.Cesium3DTileset)]
        env["rh_world"] = gw.get_path_name()
    def z_at(x, y):
        hs = unreal.SystemLibrary.line_trace_multi(gw, unreal.Vector(x, y, 80000), unreal.Vector(x, y, -60000), unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True,
                                                   env["rh_ignore"], unreal.DrawDebugTrace.NONE, True)
        for h in hs or []:
            t = h.to_tuple()
            if t[9] is not None and isinstance(t[9], unreal.Cesium3DTileset): return float(t[4].z)
        return None
    _, plist = env["rh_cells"][CELL]; ok = 0
    for x, y in plist:
        zs = [z_at(x + dx, y + dy) for dx, dy in ((0, 0), (400, 0), (-400, 0), (0, 400), (0, -400))]
        zs = [z for z in zs if z is not None]
        if zs: env["rh_res"]["%d,%d" % (x, y)] = [zs[0], min(zs)]; ok += 1
    result = [CELL, ok, len(plist)]
elif MODE == "save":
    json.dump(env["rh_res"], open(os.path.join(P, "Data", "rail_heights.json"), "w"))
    result = len(env["rh_res"])
