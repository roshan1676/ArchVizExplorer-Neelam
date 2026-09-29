"""PIE verification of every route / road-glow ribbon against the FULL-detail map (camera 250 m over each 500 m cell).
prep: collect spline points of Route_*/Road_* actors in the PIE world -> cells. go/trace per cell: 3 traces across
(+-3 m) per spline point -> highest map hit. save: raise Data/surface_dense.json wherever the map is higher than what
we had (nearest dense samples within 6 m), so the next Build_Surroundings keeps every ribbon above the real surface."""
import json, os, math
import unreal
P = os.path.join(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()), "Scripts", "Neelam")
MODE = globals().get("MODE", "prep"); env = globals()["env"]; CELL = globals().get("CELL", 0); CC = 50000.0
gw = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
if MODE == "prep":
    pts = []; cells = {}
    for a in unreal.ObjectIterator(unreal.Actor):
        try:
            if a.get_world() != gw: continue
            lab = a.get_actor_label()
        except Exception: continue
        if not (lab.startswith("Route_") or lab.startswith("Road_") and not lab.startswith("Road_vb_") and not lab.startswith("Road_eeh_") and not lab.startswith("Road_mar_")): continue
        pid = ("route_" + lab[6:]) if lab.startswith("Route_") else ("road_" + lab[5:])
        s = a.get_component_by_class(unreal.SplineComponent); L = s.get_spline_length(); d = 0.0
        while d <= L:
            p = s.get_location_at_distance_along_spline(d, unreal.SplineCoordinateSpace.WORLD)
            t = s.get_right_vector_at_distance_along_spline(d, unreal.SplineCoordinateSpace.WORLD)
            pts.append([pid, p.x, p.y, p.z, t.x, t.y, None]); cells.setdefault((math.floor(p.x / CC), math.floor(p.y / CC)), []).append(len(pts) - 1)
            d += 300.0
    env["vr"] = pts; env["vr_cells"] = sorted(cells.items())
    result = {"points": len(pts), "cells": len(cells)}
elif MODE == "go":
    (cx, cy), _ = env["vr_cells"][CELL]
    pc = unreal.GameplayStatics.get_player_controller(gw, 0); pawn = pc.get_controlled_pawn()
    arm = pawn.get_component_by_class(unreal.SpringArmComponent); arm.set_editor_property("do_collision_test", False); arm.set_editor_property("target_arm_length", 1.0)
    pawn.set_actor_location(unreal.Vector((cx + .5) * CC, (cy + .5) * CC, env.get("vr_h", 38000)), False, True); pc.set_control_rotation(unreal.Rotator(roll=0.0, pitch=-89.0, yaw=0.0))
    result = CELL
elif MODE == "trace":
    _, idx = env["vr_cells"][CELL]; hit = 0; low = 0
    for i in idx:
        pid, x, y, z, rx, ry, _ = env["vr"][i]; best = None
        for o in (0.0, 300.0, -300.0):
            hs = unreal.SystemLibrary.line_trace_multi(gw, unreal.Vector(x + rx * o, y + ry * o, z + 40000), unreal.Vector(x + rx * o, y + ry * o, z - 40000),
                                                       unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, [], unreal.DrawDebugTrace.NONE, True)
            for h in hs or []:
                t = h.to_tuple()
                if t[9] is not None and isinstance(t[9], unreal.Cesium3DTileset):
                    best = t[4].z if best is None else max(best, t[4].z); break
        if best is not None:
            old = env["vr"][i][6]; env["vr"][i][6] = best if old is None else max(old, best); hit += 1
            low += (z < best + 50)
    result = [CELL, hit, len(idx), "below_or_touching:", low]
elif MODE == "save":
    SP = os.path.join(P, "Data", "surface_dense.json"); S = json.load(open(SP))
    import importlib, sys; sys.path.insert(0, P)
    raised = 0; bad = 0
    for pid, x, y, z, rx, ry, hz in env["vr"]:
        if hz is None or pid not in S: continue
        if z < hz + 50: bad += 1
        env.setdefault("vr_fix", []).append((pid, x, y, hz))
    json.dump(env["vr_fix"], open(os.path.join(P, "Data", "surface_fix.json"), "w"))
    result = {"points_checked": sum(1 for q in env["vr"] if q[6] is not None), "below_or_within_50cm": bad}
