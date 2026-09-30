"""Ground under every ribbon spline (landmark routes Route_*, key-road glows Road_* (BP_Route), traffic strips Traffic_*),
traced in PIE at full tile detail (30 Sep). Replaces the max-of-3 Surface_Align samples that picked up trees, cars,
overpasses and the old photogrammetry buildings still COLLIDING inside the site cut-out (ribbon at 3rd-floor height).
Every 3 m along each spline, 5 traces across the ribbon width, MEDIAN kept; only the map tilesets are hit.
Camera: CameraActor 'Neelam_AlignCam' (view target) 700 m above each 600 m cell, wait >= 40 s (two tilesets stream).
Modes: prep -> go / trace (CELL) -> save => Data/ribbon_surface.json {label: {"d": [cm], "z": [cm|None]}}.
Then Ribbon_Heights.py (editor) turns it into spline heights."""
import json, os, math
import unreal
P = os.path.join(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()), "Scripts", "Neelam")
MODE = globals().get("MODE", "prep"); env = globals()["env"]; CC = 60000.0; STEP = 300.0
OUT = os.path.join(P, "Data", "ribbon_surface.json")
gw = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
WS = unreal.SplineCoordinateSpace.WORLD
def ribbon_actors(world):
    out = []
    for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor):
        l = a.get_actor_label(); cn = a.get_class().get_name()
        if (l.startswith("Route_") or l.startswith("Road_")) and cn == "BP_Route_C": out.append((l, a, 1.2))
        elif l.startswith("Traffic_") and cn == "BP_RoadTool_C":
            try: w = float(a.get_editor_property("Width_Road")) / 2.2
            except Exception: w = 3.0
            out.append((l, a, min(4.0, max(1.0, w))))
    return out
if MODE == "prep":
    samp = []; cells = {}; meta = {}
    for l, a, hw in ribbon_actors(gw):
        s = a.get_component_by_class(unreal.SplineComponent); L = s.get_spline_length(); n = int(L // STEP) + 1
        meta[l] = n + 1
        for q in range(n + 1):
            d = min(L, q * STEP); p = s.get_location_at_distance_along_spline(d, WS); r = s.get_right_vector_at_distance_along_spline(d, WS)
            samp.append([l, q, d, p.x, p.y, r.x, r.y, hw * 100, None])
            cells.setdefault((math.floor(p.x / CC), math.floor(p.y / CC)), []).append(len(samp) - 1)
    env["rb"] = samp; env["rb_cells"] = sorted(cells.items()); env["rb_meta"] = meta
    result = {"samples": len(samp), "cells": len(cells), "actors": len(meta)}
elif MODE == "go":
    (cx, cy), _ = env["rb_cells"][CELL]
    pc = unreal.GameplayStatics.get_player_controller(gw, 0)
    cam = next(a for a in unreal.GameplayStatics.get_all_actors_of_class(gw, unreal.CameraActor) if a.get_actor_label() == "Neelam_AlignCam")
    cam.set_actor_location_and_rotation(unreal.Vector((cx + .5) * CC, (cy + .5) * CC, 70000), unreal.Rotator(roll=0.0, pitch=-90.0, yaw=0.0), False, True)
    cam.camera_component.set_editor_property("field_of_view", 90.0)
    pc.set_view_target_with_blend(cam, 0.0)
    result = CELL
elif MODE == "trace":
    if env.get("rb_world") != gw.get_path_name():
        env["rb_ignore"] = [a for a in unreal.GameplayStatics.get_all_actors_of_class(gw, unreal.Actor) if not isinstance(a, unreal.Cesium3DTileset)]
        env["rb_world"] = gw.get_path_name()
    _, idx = env["rb_cells"][CELL]; hit = 0
    for i in idx:
        l, q, d, x, y, rx, ry, hw, _ = env["rb"][i]; zs = []
        for o in (0.0, hw / 2, -hw / 2, hw, -hw):
            hs = unreal.SystemLibrary.line_trace_multi(gw, unreal.Vector(x + rx * o, y + ry * o, 60000), unreal.Vector(x + rx * o, y + ry * o, -60000),
                                                       unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, env["rb_ignore"], unreal.DrawDebugTrace.NONE, True)
            for h in hs or []:
                t = h.to_tuple()
                if t[9] is not None and isinstance(t[9], unreal.Cesium3DTileset): zs.append(float(t[4].z)); break
        if zs:
            zs.sort(); env["rb"][i][8] = zs[len(zs) // 2]; hit += 1
    result = [CELL, hit, len(idx)]
elif MODE == "save":
    out = {l: {"d": [None] * n, "z": [None] * n, "xy": [None] * n} for l, n in env["rb_meta"].items()}
    for l, q, d, x, y, rx, ry, hw, z in env["rb"]:
        out[l]["d"][q] = round(d, 1); out[l]["xy"][q] = [round(x, 1), round(y, 1)]
        if z is not None: out[l]["z"][q] = round(z, 1)
    json.dump(out, open(OUT, "w"))
    result = {"traced": sum(1 for s in env["rb"] if s[8] is not None), "total": len(env["rb"])}
