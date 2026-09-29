"""Real surface under every carriageway of the 3 PDF roads + ground ring around each landmark footprint,
traced in PIE BEFORE the map is cut (Cesium only streams near the player camera).
Roads: every OSM way (both one-way carriageways) densified to 3 m, 5 traces across the carriageway -> all kept
(min = road surface between the photogrammetry cars). Landmarks: ring 3 m outside the footprint box, every 3 m.
Modes: prep (editor) -> pie_go / pie_trace CELL -> gaps -> (pie_go/pie_trace) -> save  => Data/road_surface.json"""
import json, os, sys, math
import unreal
P = os.path.join(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()), "Scripts", "Neelam")
sys.path.insert(0, P)
MODE = globals().get("MODE", "prep"); env = globals()["env"]
STEP, CELL_CM = 300.0, 60000.0
OUT = os.path.join(P, "Data", "road_surface.json")
DEFAULT_LANES = {"vb": 2, "mar": 3, "eeh": 3}

def group(n):
    return "vb" if "Phadke" in n else "mar" if "Airoli" in n else "eeh"

if MODE == "prep":
    import importlib, connectivity_lib as C; importlib.reload(C)
    import poi_highlight as H; importlib.reload(H)
    ways = json.load(open(os.path.join(P, "Data", "osm", "roads_ways.json")))["elements"]
    items = {}
    for w in ways:
        t = w["tags"]; g = group(t.get("name", ""))
        lanes = int(str(t.get("lanes", DEFAULT_LANES[g])).split(";")[0])
        width = float(t.get("width", lanes * 3.5))
        xy = [(lambda v: (v.x, v.y))(C.to_xy(n["lat"], n["lon"])) for n in w["geometry"]]
        items["rd_%d" % w["id"]] = {"kind": "road", "group": g, "lanes": lanes, "width_m": width, "bridge": t.get("bridge") == "yes",
                                   "name": t.get("name", ""), "poly": xy, "offs": [f * width * 100 for f in (-0.4, -0.2, 0.0, 0.2, 0.4)]}
    for ph in ("phase2", "phase3"):
        for lm in json.load(open(os.path.join(P, "Data", "landmarks_%s.json" % ph), encoding="utf-8"))["landmarks"]:
            f = H.FP.get(lm["id"]);  c = C.to_xy(lm["lat"], lm["lon"])
            if not f: continue
            cx, cy = c.x + f["cx_m"] * 100, c.y - f["cy_m"] * 100; a = math.radians(-f["yaw_deg"])
            hw, hd = f["w_m"] * 50 + 300, f["d_m"] * 50 + 300
            ux, uy = math.cos(a), math.sin(a); vx, vy = -uy, ux
            corners = [(cx + sx * hw * ux + sy * hd * vx, cy + sx * hw * uy + sy * hd * vy) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1), (-1, -1))]
            items["lm_" + lm["id"]] = {"kind": "ring", "poly": corners, "offs": [0.0], "center": (cx, cy), "yaw_deg": f["yaw_deg"],
                                       "w_m": f["w_m"], "d_m": f["d_m"]}
    cells = {}
    for k, it in items.items():
        xy = it["poly"]; s = [0.0]
        for a, b in zip(xy, xy[1:]): s.append(s[-1] + math.dist(a, b))
        dense = []; j = 0
        for q in range(int(s[-1] // STEP) + 2):
            t = min(q * STEP, s[-1])
            while j < len(s) - 2 and s[j + 1] < t: j += 1
            f = (t - s[j]) / ((s[j + 1] - s[j]) or 1.0)
            x = xy[j][0] + f * (xy[j + 1][0] - xy[j][0]); y = xy[j][1] + f * (xy[j + 1][1] - xy[j][1])
            dx, dy = xy[j + 1][0] - xy[j][0], xy[j + 1][1] - xy[j][1]; L = math.hypot(dx, dy) or 1.0
            dense.append([round(t, 1), x, y, -dy / L, dx / L])
            cells.setdefault((math.floor(x / CELL_CM), math.floor(y / CELL_CM)), []).append((k, len(dense) - 1))
            if t >= s[-1]: break
        it["dense"] = dense; it["z"] = [None] * len(dense)
    env["rs"] = items; env["rs_cells"] = sorted(cells.items()); env["rs_rz"] = C.RZ; env["rs_cam_h"] = 45000
    result = {"roads": sum(1 for v in items.values() if v["kind"] == "road"), "rings": sum(1 for v in items.values() if v["kind"] == "ring"),
              "samples": sum(len(v["dense"]) for v in items.values()), "cells": len(cells)}

elif MODE == "pie_go":
    gw = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    (cx, cy), _ = env["rs_cells"][CELL]
    pc = unreal.GameplayStatics.get_player_controller(gw, 0); pawn = pc.get_controlled_pawn()
    pawn.set_actor_location(unreal.Vector((cx + .5) * CELL_CM, (cy + .5) * CELL_CM, env["rs_rz"] + env["rs_cam_h"]), False, True)
    arm = pawn.get_component_by_class(unreal.SpringArmComponent); arm.set_editor_property("do_collision_test", False); arm.set_editor_property("target_arm_length", 1.0)
    pc.set_control_rotation(unreal.Rotator(roll=0.0, pitch=-89.0, yaw=0.0))
    result = CELL

elif MODE == "pie_trace":
    gw = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    rz = env["rs_rz"]; hit = 0; _, plist = env["rs_cells"][CELL]
    for k, j in plist:
        it = env["rs"][k]
        if it["z"][j] is not None and None not in it["z"][j]: hit += 1; continue
        _, x, y, px, py = it["dense"][j]; zs = list(it["z"][j] or [None] * len(it["offs"]))
        for oi, o in enumerate(it["offs"]):
            if zs[oi] is not None: continue
            hs = unreal.SystemLibrary.line_trace_multi(gw, unreal.Vector(x + px * o, y + py * o, rz + 60000), unreal.Vector(x + px * o, y + py * o, rz - 60000),
                                                       unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, [], unreal.DrawDebugTrace.NONE, True)
            for h in hs or []:
                tt = h.to_tuple()
                if tt[9] is not None and isinstance(tt[9], unreal.Cesium3DTileset):
                    zs[oi] = round(float(tt[4].z), 1); break
        it["z"][j] = zs; hit += (None not in zs)
    result = [CELL, hit, len(plist)]

elif MODE == "gaps":
    g = {}
    for k, it in env["rs"].items():
        for j, zs in enumerate(it["z"]):
            if zs is None or None in zs:
                _, x, y, _, _ = it["dense"][j]; g.setdefault((math.floor(x / 40000.0), math.floor(y / 40000.0)), []).append((k, j))
    cl = []
    for _, pl in sorted(g.items()):
        mx = sum(env["rs"][k]["dense"][j][1] for k, j in pl) / len(pl); my = sum(env["rs"][k]["dense"][j][2] for k, j in pl) / len(pl)
        cl.append(((mx / CELL_CM - .5, my / CELL_CM - .5), pl))
    env["rs_cells"] = cl; env["rs_cam_h"] = 25000
    result = {"gap_clusters": len(cl), "samples": sum(len(pl) for _, pl in cl)}

elif MODE == "save":
    out = {}
    for k, it in env["rs"].items():
        d = {kk: vv for kk, vv in it.items() if kk not in ("z",)}
        d["z"] = it["z"]; out[k] = d
    json.dump(out, open(OUT, "w"))
    miss = sum(1 for it in env["rs"].values() for zs in it["z"] if zs is None or None in zs)
    result = {"saved": OUT, "items": len(out), "incomplete_samples": miss}
