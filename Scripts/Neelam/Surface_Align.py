"""Precise surface alignment for every route ribbon, key-road glow and traffic strip.
Samples the REAL map surface (Google 3D Tiles, traced during PIE while the player camera sweeps the area in 600 m
cells) every 3 m along each polyline, with 3 traces across the width (centre, +-2.5 m) and keeps the highest hit.
Result: Data/surface_dense.json {poly_id: {"s": [cm along polyline], "z": [surface Z]}}.
connectivity_lib.envelope_z() then gives each spline point the max surface over BOTH neighbouring segments, so the
straight segment between two points can never pass under a bump -> strips always stay on top of the map.
Modes: prep (editor) -> pie_go / pie_trace (CELL=i, during PIE) -> fill -> save."""
import json, os, sys, math
import unreal
P = os.path.join(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()), "Scripts", "Neelam")
sys.path.insert(0, P)
MODE = globals().get("MODE", "prep"); env = globals()["env"]
STEP, CELL_CM, HALF_W = 300.0, 60000.0, 250.0
OUT = os.path.join(P, "Data", "surface_dense.json")

if MODE == "prep":
    import importlib, connectivity_lib as C; importlib.reload(C)
    polys = {}
    for ph in ("phase2", "phase3"):
        G = json.load(open(os.path.join(P, "Data", "connectivity_%s.json" % ph), encoding="utf-8"))
        for k, v in G["roads"].items(): polys["road_" + k] = v["pts"]
        for k, v in G["routes"].items(): polys["route_" + k] = v["pts"]
    sa = {}; cells = {}
    for pid, pts in polys.items():
        xy = [(lambda w: (w.x, w.y))(C.to_xy(la, lo)) for la, lo in pts]
        s = [0.0]
        for a, b in zip(xy, xy[1:]): s.append(s[-1] + math.dist(a, b))
        ds, dxy, j = [], [], 0
        n = int(s[-1] // STEP) + 1
        for q in range(n + 1):
            t = min(q * STEP, s[-1])
            while j < len(s) - 2 and s[j + 1] < t: j += 1
            seg = (s[j + 1] - s[j]) or 1.0; f = (t - s[j]) / seg
            x = xy[j][0] + f * (xy[j + 1][0] - xy[j][0]); y = xy[j][1] + f * (xy[j + 1][1] - xy[j][1])
            dx, dy = xy[j + 1][0] - xy[j][0], xy[j + 1][1] - xy[j][1]; L = math.hypot(dx, dy) or 1.0
            ds.append(round(t, 1)); dxy.append((x, y, -dy / L, dx / L))
            cells.setdefault((math.floor(x / CELL_CM), math.floor(y / CELL_CM)), []).append((pid, len(ds) - 1))
        sa[pid] = {"s": ds, "xy": dxy, "z": [None] * len(ds)}
    env["sa"] = sa; env["sa_cells"] = sorted(cells.items()); env["sa_rz"] = C.RZ
    result = {"polylines": len(sa), "samples": sum(len(v["s"]) for v in sa.values()), "cells": len(cells)}

elif MODE == "pie_go":
    gw = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    (cx, cy), _ = env["sa_cells"][CELL]
    pc = unreal.GameplayStatics.get_player_controller(gw, 0); pawn = pc.get_controlled_pawn()
    pawn.set_actor_location(unreal.Vector((cx + .5) * CELL_CM, (cy + .5) * CELL_CM, env["sa_rz"] + env.get("sa_cam_h", 45000)), False, True)   # camera ~450 m up: whole cell streams at high detail
    arm = pawn.get_component_by_class(unreal.SpringArmComponent); arm.set_editor_property("do_collision_test", False); arm.set_editor_property("target_arm_length", 35000.0)
    pc.set_control_rotation(unreal.Rotator(roll=0.0, pitch=-70.0, yaw=0.0))
    result = CELL

elif MODE == "pie_trace":
    gw = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    if env.get("sa_world") != gw.get_path_name():
        env["sa_ignore"] = [a for a in unreal.GameplayStatics.get_all_actors_of_class(gw, unreal.Actor) if not isinstance(a, unreal.Cesium3DTileset)]
        env["sa_world"] = gw.get_path_name()
    rz = env["sa_rz"]; hit = 0; _, plist = env["sa_cells"][CELL]
    for pid, j in plist:
        x, y, px, py = env["sa"][pid]["xy"][j]; best = None
        for o in (0.0, HALF_W, -HALF_W):
            hs = unreal.SystemLibrary.line_trace_multi(gw, unreal.Vector(x + px * o, y + py * o, rz + 60000), unreal.Vector(x + px * o, y + py * o, rz - 60000),
                                                       unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, [], unreal.DrawDebugTrace.NONE, True)
            for h in hs or []:                                   # first hit that belongs to a map tileset
                t = h.to_tuple()
                if t[9] is not None and isinstance(t[9], unreal.Cesium3DTileset):
                    z = float(t[4].z); best = z if best is None else max(best, z); break
        if best is not None:
            old = env["sa"][pid]["z"][j]; env["sa"][pid]["z"][j] = best if old is None else max(old, best); hit += 1
    result = [CELL, hit, len(plist)]

elif MODE == "gaps":
    # second pass: 400 m clusters of samples still missing -> camera straight over each (pie_go/pie_trace use env["sa_cells"])
    g = {}
    for pid, v in env["sa"].items():
        for j, z in enumerate(v["z"]):
            if z is None:
                x, y, _, _ = v["xy"][j]; g.setdefault((math.floor(x / 40000.0), math.floor(y / 40000.0)), []).append((pid, j))
    cl = []
    for (cx, cy), pl in sorted(g.items()):                     # camera over the MEAN of the missing samples, lower
        mx = sum(env["sa"][p]["xy"][j][0] for p, j in pl) / len(pl); my = sum(env["sa"][p]["xy"][j][1] for p, j in pl) / len(pl)
        cl.append(((mx / CELL_CM - .5, my / CELL_CM - .5), pl))
    env["sa_cells"] = cl; env["sa_cam_h"] = 25000
    result = {"gap_clusters": len(env["sa_cells"]), "samples": sum(len(pl) for _, pl in env["sa_cells"])}
elif MODE == "fill":
    miss = 0; total = 0
    for pid, v in env["sa"].items():
        z = v["z"]; good = [i for i, q in enumerate(z) if q is not None]; total += len(z)
        for i in range(len(z)):
            if z[i] is not None: continue
            miss += 1
            if not good: continue
            a = max([g for g in good if g < i], default=None); b = min([g for g in good if g > i], default=None)
            if a is None: z[i] = z[b]
            elif b is None: z[i] = z[a]
            else: t = (i - a) / (b - a); z[i] = z[a] * (1 - t) + z[b] * t
    result = {"samples": total, "interpolated": miss}

elif MODE == "save":
    json.dump({pid: {"s": v["s"], "z": [None if q is None else round(q, 1) for q in v["z"]]} for pid, v in env["sa"].items()}, open(OUT, "w"))
    result = {"saved": OUT, "polylines": len(env["sa"])}
