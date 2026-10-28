"""Road + railway vs the real map (27 Oct, client: "is any road broken or railway track inside the ground?"). PIE job.
Samples every 3 m along each carriageway centreline (Data/road_build.json xy - its z is stale) and every railway point
(Data/rail_pts.json). Per sample:
  top  = road: our Road_<grp>_<id> deck mesh traced (complex) at the centre; rail: Railway_* meshes traced from 2.5 m
         above the built track height (Data/rail_heights.json) so the platform roofs are not taken for the track.
         Road + railway meshes run with NO collision in PIE -> trace() switches the PIE copies to QUERY_ONLY (transient).
  map  = photogrammetry z at both sides just OUTSIDE the road/track (RoadCut polygons cut the map out under our roads, so the
         centre would hit the base terrain); only Cesium tilesets are hit
Modes (globals MODE, CELL): prep -> go / trace (CELL, after tiles load_progress == 100) -> save => Data/infra_ground.json
Analysis: py infra_ground_report.py"""
import json, math, os
import unreal
P = os.path.join(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()), "Scripts", "Neelam", "Data")
MODE = globals().get("MODE", "prep"); env = globals()["env"]; CC = 60000.0; STEP = 300.0
gw = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()


def actors():
    return {a.get_actor_label(): a for a in unreal.GameplayStatics.get_all_actors_of_class(gw, unreal.StaticMeshActor)}


if MODE == "prep":
    RB = json.load(open(os.path.join(P, "road_build.json")))["roads"]; acts = actors()
    deck = {"rd_" + l.split("_")[-1]: l for l in acts if l.startswith("Road_") and ("rd_" + l.split("_")[-1]) in RB}
    S = []   # [kind, id, d_m, x, y, nx, ny, side_cm, top, mapL, mapR]
    for rid, r in RB.items():
        if rid not in deck: continue
        pts = r["pts"]; side = r["width_m"] * 50 + 350; d0 = 0.0
        for i in range(len(pts) - 1):
            a, b = pts[i], pts[i + 1]; L = math.hypot(b[0] - a[0], b[1] - a[1])
            if L < 1: continue
            nx, ny = -(b[1] - a[1]) / L, (b[0] - a[0]) / L; t = 0.0
            while t < L:
                S.append(["road", rid, round((d0 + t) / 100, 1), a[0] + (b[0] - a[0]) * t / L, a[1] + (b[1] - a[1]) * t / L, nx, ny, side, None, None, None]); t += STEP
            d0 += L
    rp = json.load(open(os.path.join(P, "rail_pts.json"))); RH = json.load(open(os.path.join(P, "rail_heights.json")))
    for i, (x, y) in enumerate(rp):
        j = i + 1 if i + 1 < len(rp) and math.hypot(rp[i + 1][0] - x, rp[i + 1][1] - y) < 3000 else i - 1
        dx, dy = rp[j][0] - x, rp[j][1] - y; L = math.hypot(dx, dy) or 1.0
        h = RH.get("%d,%d" % (round(x), round(y)))
        S.append(["rail", "rail", i, x, y, -dy / L, dx / L, 600.0, max(h) if h else None, None, None])   # [8] = built height until traced
    cells = {}
    for i, s in enumerate(S): cells.setdefault((math.floor(s[3] / CC), math.floor(s[4] / CC)), []).append(i)
    env["ig"] = S; env["ig_cells"] = sorted(cells.items()); env["ig_deck"] = deck
    result = {"road_samples": sum(1 for s in S if s[0] == "road"), "rail_samples": len(rp), "rail_with_height": sum(1 for s in S if s[0] == "rail" and s[8] is not None),
              "cells": len(cells), "decks": len(deck), "rail_actors": sum(1 for l in acts if l.startswith("Railway_"))}
elif MODE == "go":
    (cx, cy), _ = env["ig_cells"][CELL]
    cam = next(a for a in unreal.GameplayStatics.get_all_actors_of_class(gw, unreal.CameraActor) if a.get_actor_label() == "Neelam_AlignCam")
    cam.set_actor_location_and_rotation(unreal.Vector((cx + .5) * CC, (cy + .5) * CC, 70000), unreal.Rotator(roll=0.0, pitch=-90.0, yaw=0.0), False, True)
    cam.camera_component.set_editor_property("field_of_view", 90.0)
    unreal.GameplayStatics.get_player_controller(gw, 0).set_view_target_with_blend(cam, 0.0)
    result = CELL
elif MODE == "trace":
    if env.get("ig_world") != gw.get_path_name():
        env["ig_ignore"] = [a for a in unreal.GameplayStatics.get_all_actors_of_class(gw, unreal.Actor) if not isinstance(a, unreal.Cesium3DTileset)]
        acts = actors(); env["ig_comp"] = {rid: acts[l].static_mesh_component for rid, l in env["ig_deck"].items() if l in acts}
        env["ig_rail"] = []
        for l, a in acts.items():
            if l.startswith("Railway_"):
                o, e = a.get_actor_bounds(False); env["ig_rail"].append((o.x - e.x, o.y - e.y, o.x + e.x, o.y + e.y, a.static_mesh_component))
        for c in list(env["ig_comp"].values()) + [r[4] for r in env["ig_rail"]]:
            c.set_collision_enabled(unreal.CollisionEnabled.QUERY_ONLY)   # PIE copy only
        env["ig_world"] = gw.get_path_name()

    def mapz(x, y):
        hs = unreal.SystemLibrary.line_trace_multi(gw, unreal.Vector(x, y, 60000), unreal.Vector(x, y, -60000), unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,
                                                   True, env["ig_ignore"], unreal.DrawDebugTrace.NONE, True)
        for h in hs or []:
            t = h.to_tuple()
            if t[9] is not None and isinstance(t[9], unreal.Cesium3DTileset): return float(t[4].z)
        return None
    _, idx = env["ig_cells"][CELL]
    for i in idx:
        s = env["ig"][i]; kind, rid, d, x, y, nx, ny, side = s[:8]
        if kind == "road":
            # the deck can sit metres off the road_build.json line (photo alignment): scan across it, use the real edges
            c = env["ig_comp"].get(rid); hit = []
            for o in range(-1600, 1601, 50) if c else []:
                r = c.line_trace_component(unreal.Vector(x + nx * o, y + ny * o, 60000), unreal.Vector(x + nx * o, y + ny * o, -60000), True, False, False)
                if r: hit.append((o, float(r[0].z)))
            if hit:
                lo, hi = hit[0][0], hit[-1][0]; m = (lo + hi) / 2
                zc = sorted(z for o, z in hit if abs(o - m) <= 100) or sorted(z for o, z in hit)
                s[8] = zc[len(zc) // 2]
                s[9] = mapz(x + nx * (hi + 350), y + ny * (hi + 350)); s[10] = mapz(x + nx * (lo - 350), y + ny * (lo - 350))
            else: s[8] = None; s[9] = mapz(x + nx * side, y + ny * side); s[10] = mapz(x - nx * side, y - ny * side)
            continue
        elif s[8] is not None and s[8] < 1e8:   # rail: built height -> traced track top (marked +1e9 once traced, see save)
            h0 = s[8]; best = None
            for x0, y0, x1, y1, c in env["ig_rail"]:
                if x0 - 300 <= x <= x1 + 300 and y0 - 300 <= y <= y1 + 300:
                    r = c.line_trace_component(unreal.Vector(x, y, h0 + 250), unreal.Vector(x, y, h0 - 3000), True, False, False)
                    if r and (best is None or r[0].z > best): best = float(r[0].z)
            s[8] = None if best is None else best + 1e9
        s[9] = mapz(x + nx * side, y + ny * side); s[10] = mapz(x - nx * side, y - ny * side)
    result = [CELL, len(idx)]
elif MODE == "save":
    for s_ in env["ig"]:
        if s_[0] == "rail": s_[8] = s_[8] - 1e9 if s_[8] is not None and s_[8] > 1e8 else None   # untraced = no track
    json.dump(env["ig"], open(os.path.join(P, "infra_ground.json"), "w"))
    result = {"saved": len(env["ig"])}
