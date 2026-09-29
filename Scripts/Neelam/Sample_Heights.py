"""Fill Data/height_cache.json with real ground heights for every point the surroundings layer uses.
Cesium only streams (and gives collision for) tiles near the editor camera, and fog culling hides far tiles,
so the camera is swept over the area in 1 km cells: MODE="prep" -> cells; MODE="go" (CELL=i) moves the camera;
MODE="trace" (CELL=i) traces the points of that cell; MODE="save" writes the cache. Driven by a shell loop."""
import json, os, sys, importlib, math
import unreal
P = os.path.join(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()), "Scripts", "Neelam")
sys.path.insert(0, P)
MODE = globals().get("MODE", "prep"); env = globals()["env"]
import connectivity_lib as C
if not MODE.startswith("pie"): importlib.reload(C)   # during PIE the editor actor list is unavailable: reuse the loaded module
CELL_CM = 100000.0
if MODE == "prep":
    pts = set()
    for ph in globals().get("PHASES", ["phase2", "phase3"]):
        L = json.load(open(os.path.join(P, "Data", "landmarks_%s.json" % ph), encoding="utf-8"))
        G = json.load(open(os.path.join(P, "Data", "connectivity_%s.json" % ph), encoding="utf-8"))
        for lm in L["landmarks"]: pts.add((lm["lat"], lm["lon"]))
        for r in list(G["routes"].values()) + list(G["roads"].values()):
            for la, lo in r["pts"]: pts.add((la, lo))
            if "pts" in r and r is not None:
                mid = r["pts"][len(r["pts"]) // 2]; pts.add((mid[0], mid[1]))
    cells = {}
    for la, lo in pts:
        v = C.to_xy(la, lo)
        cells.setdefault((math.floor(v.x / CELL_CM), math.floor(v.y / CELL_CM)), []).append((la, lo, v.x, v.y))
    env["hs_cells"] = sorted(cells.items()); env["hs_z"] = dict(C.HCACHE)
    result = {"points": len(pts), "cells": len(cells)}
elif MODE == "go":
    (cx, cy), _ = env["hs_cells"][CELL]
    ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    ues.set_level_viewport_camera_info(unreal.Vector((cx + .5) * CELL_CM, (cy + .5) * CELL_CM, C.RZ + 70000), unreal.Rotator(0, -89.9, 0))
    result = CELL
elif MODE == "trace":
    _, plist = env["hs_cells"][CELL]; hit = 0
    for la, lo, x, y in plist:
        k = C.hkey(la, lo)
        if k in env["hs_z"]: hit += 1; continue
        h = unreal.SystemLibrary.line_trace_single(C.WORLD, unreal.Vector(x, y, C.RZ + 60000), unreal.Vector(x, y, C.RZ - 20000),
                                                   unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, C.IGNORE, unreal.DrawDebugTrace.NONE, True)
        if h is not None and h.to_tuple()[0]:
            env["hs_z"][k] = round(float(h.to_tuple()[4].z), 1); hit += 1
    result = [CELL, hit, len(plist)]
elif MODE == "dem":
    # Fallback when Cesium can't stream (editor in background): Copernicus DEM (Open-Meteo API, ~90 m) calibrated
    # against the points that DO trace onto the loaded Google tiles: z = dem_m*100 + median(trace - dem_m*100).
    import urllib.request, statistics, time
    allp = [(la, lo, x, y) for (c, pl) in env["hs_cells"] for (la, lo, x, y) in pl]
    g = sorted({(round(q[0], 3), round(q[1], 3)) for q in allp})      # DEM is ~90 m: sample a 0.001 deg (~110 m) grid
    gz = {}
    for i in range(0, len(g), 100):
        b = g[i:i + 100]
        u = "https://api.open-meteo.com/v1/elevation?latitude=%s&longitude=%s" % (",".join("%.3f" % q[0] for q in b), ",".join("%.3f" % q[1] for q in b))
        for attempt in range(6):
            try:
                e = json.loads(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "neelam-archviz"}), timeout=30).read())["elevation"]; break
            except Exception:
                time.sleep(3 + attempt * 4)
        else:
            raise RuntimeError("elevation API keeps failing")
        for q, z in zip(b, e): gz[q] = z
        time.sleep(1.5)
    def dz(la, lo):                                   # bilinear on the 0.001 grid where corners exist, else nearest
        a0, o0 = math.floor(la * 1000) / 1000, math.floor(lo * 1000) / 1000
        cs = [(round(a0 + da, 3), round(o0 + do, 3)) for da in (0, .001) for do in (0, .001)]
        if all(c in gz for c in cs):
            ta, to = (la - a0) * 1000, (lo - o0) * 1000
            z0 = gz[cs[0]] * (1 - to) + gz[cs[1]] * to; z1 = gz[cs[2]] * (1 - to) + gz[cs[3]] * to
            return z0 * (1 - ta) + z1 * ta
        return gz[(round(la, 3), round(lo, 3))]
    dem = {C.hkey(la, lo): dz(la, lo) for la, lo, x, y in allp}
    pairs = []
    for la, lo, x, y in allp:
        h = unreal.SystemLibrary.line_trace_single(C.WORLD, unreal.Vector(x, y, C.RZ + 60000), unreal.Vector(x, y, C.RZ - 20000),
                                                   unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, C.IGNORE, unreal.DrawDebugTrace.NONE, True)
        if h is not None and h.to_tuple()[0]:
            z = float(h.to_tuple()[4].z); env["hs_z"][C.hkey(la, lo)] = round(z, 1); pairs.append(z - dem[C.hkey(la, lo)] * 100)
    off = statistics.median(pairs) if pairs else C.RZ - 300.0
    nd = 0
    for la, lo, x, y in allp:
        k = C.hkey(la, lo)
        if k not in env["hs_z"]: env["hs_z"][k] = round(dem[k] * 100 + off, 1); nd += 1
    q = sorted(pairs)
    result = {"traced": len(pairs), "dem_filled": nd, "offset_cm": round(off), "calib_p10_p90": [round(q[len(q)//10]), round(q[9*len(q)//10])] if q else None}
elif MODE == "pie_go":
    # Best source: during PIE Cesium streams tiles around the player camera -> move the pawn over each cell.
    gw = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    (cx, cy), _ = env["hs_cells"][CELL]
    pawn = unreal.GameplayStatics.get_player_controller(gw, 0).get_controlled_pawn()
    pawn.set_actor_location(unreal.Vector((cx + .5) * CELL_CM, (cy + .5) * CELL_CM, C.RZ + 2000), False, True)
    result = CELL
elif MODE == "pie_trace":
    gw = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    if "pie_ignore" not in env or env.get("pie_world") != gw.get_path_name():
        acts = unreal.GameplayStatics.get_all_actors_of_class(gw, unreal.Actor)
        env["pie_ignore"] = [a for a in acts if not isinstance(a, unreal.Cesium3DTileset)]; env["pie_world"] = gw.get_path_name()
        env.setdefault("hs_pie", set())
    _, plist = env["hs_cells"][CELL]; hit = 0
    for la, lo, x, y in plist:
        k = C.hkey(la, lo)
        if k in env["hs_pie"]: hit += 1; continue
        h = unreal.SystemLibrary.line_trace_single(gw, unreal.Vector(x, y, C.RZ + 60000), unreal.Vector(x, y, C.RZ - 20000),
                                                   unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, env["pie_ignore"], unreal.DrawDebugTrace.NONE, True)
        if h is not None and h.to_tuple()[0]:
            env["hs_z"][k] = round(float(h.to_tuple()[4].z), 1); env["hs_pie"].add(k); hit += 1
    result = [CELL, hit, len(plist)]
elif MODE == "fill":
    # Points PIE could not trace (tile gaps, site cut-out): interpolate along each route/road from traced neighbours.
    pie = env.get("hs_pie", set()); filled = 0
    for ph in globals().get("PHASES", ["phase2", "phase3"]):
        G = json.load(open(os.path.join(P, "Data", "connectivity_%s.json" % ph), encoding="utf-8"))
        for r in list(G["routes"].values()) + list(G["roads"].values()):
            ks = [C.hkey(la, lo) for la, lo in r["pts"]]; good = [i for i, k in enumerate(ks) if k in pie]
            if not good: continue
            for i, k in enumerate(ks):
                if k in pie: continue
                a = max([g for g in good if g < i], default=None); b = min([g for g in good if g > i], default=None)
                if a is None: z = env["hs_z"][ks[b]]
                elif b is None: z = env["hs_z"][ks[a]]
                else: t = (i - a) / (b - a); z = env["hs_z"][ks[a]] * (1 - t) + env["hs_z"][ks[b]] * t
                env["hs_z"][k] = round(z, 1); filled += 1
    result = {"pie_traced": len(pie), "interpolated": filled}
elif MODE == "save":
    json.dump(env["hs_z"], open(C.HCACHE_PATH, "w"))
    missing = [k for (c, pl) in env["hs_cells"] for (la, lo, x, y) in pl if C.hkey(la, lo) not in env["hs_z"]]
    result = {"cached": len(env["hs_z"]), "missing": len(missing)}
