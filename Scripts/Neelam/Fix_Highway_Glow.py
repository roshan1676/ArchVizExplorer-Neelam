"""Key-road glow lines + route ribbons vs the 3D road decks (29 Sep).
Problem: Road_eeh/vb/mar were 12 m ribbons following ONE carriageway of the OSM line -> a bright band lying on the
asphalt (white by day, glow off-centre at night) and the 7 m landmark routes stacked on the same deck z-fought.
Fix: key-road glows = slim 1.2 m line re-sampled every 8 m and snapped to the MEDIAN of a dual carriageway
(centre of a single one), 30 cm above the higher deck; routes 2.2 m wide; on a deck each category gets its own lane (Healthcare -3 m, Retail 0, Education +3 m, Transport -1.5,\nImmediate +1.5 from the carriageway centre) at the exact deck height + 5 cm per route. (BP_Route width = Scale_X + 1 m).
Re-run safe: always rebuilds from the stored original points (Saved in env / Data/key_road_src.json)."""
import json, os, math
import unreal
P = os.path.join(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()), "Scripts", "Neelam")
B = json.load(open(os.path.join(P, "Data", "road_build.json")))["roads"]
SRC = os.path.join(P, "Data", "key_road_src.json")
DECK, LIFT, STEP, KEY_W, ROUTE_W = 12.0, 30.0, 800.0, 0.8, 1.2
acts = {a.get_actor_label(): a for a in unreal.EditorLevelLibrary.get_all_level_actors()}
WS = unreal.SplineCoordinateSpace.WORLD

# centreline grid per group
G = {}
for k, r in B.items():
    pts = r["pts"]
    for i, p in enumerate(pts):
        q0, q1 = pts[max(i - 1, 0)], pts[min(i + 1, len(pts) - 1)]
        tx, ty = q1[0] - q0[0], q1[1] - q0[1]; tl = math.hypot(tx, ty) or 1
        G.setdefault(r["group"], {}).setdefault((int(p[0] // 2000), int(p[1] // 2000)), []).append(
            (p[0], p[1], p[2], tx / tl, ty / tl, k, r["width_m"]))

def nearest_per_road(grp, x, y, tdir, rad=2600.0):
    best = {}
    gx, gy = int(x // 2000), int(y // 2000)
    for i in (-1, 0, 1, 2, -2):
        for j in (-1, 0, 1, 2, -2):
            for (px, py, pz, tx, ty, k, w) in G.get(grp, {}).get((gx + i, gy + j), []):
                if w < 6.9 or abs(tx * tdir[0] + ty * tdir[1]) < 0.85: continue      # skip ramps / crossings
                d = math.hypot(px - x, py - y)
                if d < rad and (k not in best or d < best[k][0]): best[k] = (d, px, py, pz)
    return sorted(best.values())

LANE = {"Healthcare": 0.0, "Retail": 0.0, "Education": 0.0, "Transport": 0.0, "Immediate": 0.0}   # m, per category (all on the centreline: one clean stripe, not split lanes)

def deck_at(x, y):
    """(deck z, centreline x, y, tangent, half width m) of the carriageway under (x, y), else None"""
    best = None
    gx, gy = int(x // 2000), int(y // 2000)
    for grp in G.values():
        for i in (-1, 0, 1):
            for j in (-1, 0, 1):
                for (px, py, pz, tx, ty, k, w) in grp.get((gx + i, gy + j), []):
                    d = math.hypot(px - x, py - y)
                    if d < w * 50 - 50 and (best is None or d < best[0]): best = (d, pz, px, py, tx, ty, w / 2)
    return None if best is None else best[1:]

def get_pts(a):
    s = a.get_component_by_class(unreal.SplineComponent)
    return s, [s.get_location_at_spline_point(i, WS) for i in range(s.get_number_of_spline_points())]

def set_pts(a, s, vs):
    s.clear_spline_points(False)
    for v in vs: s.add_spline_point(v, WS, False)
    s.update_spline()
    for p in ("spline_has_been_edited", "input_spline_points_to_construction_script"):
        try: s.set_editor_property(p, True)
        except Exception: pass

src = json.load(open(SRC)) if os.path.exists(SRC) else {}
report = {}
# ---- key roads
for rid in ("eeh", "vb", "mar"):
    a = acts.get("Road_" + rid)
    if not a: continue
    s, cur = get_pts(a)
    if rid not in src: src[rid] = [[v.x, v.y, v.z] for v in cur]
    orig = [unreal.Vector(*p) for p in src[rid]]
    set_pts(a, s, orig)                                   # sample the ORIGINAL line
    L = s.get_spline_length(); n = max(2, int(L // STEP) + 1)
    samp = []
    for i in range(n + 1):
        d = min(L, i * L / n)
        p = s.get_location_at_distance_along_spline(d, WS); t = s.get_direction_at_distance_along_spline(d, WS)
        near = nearest_per_road(rid, p.x, p.y, (t.x, t.y))
        if len(near) >= 2 and near[1][0] < 2600:
            (d1, x1, y1, z1), (d2, x2, y2, z2) = near[0], near[1]
            sep = math.hypot(x1 - x2, y1 - y2)
            if 900 < sep < 3500:                          # a real dual carriageway -> median
                samp.append([(x1 + x2) / 2, (y1 + y2) / 2, max(z1, z2) + DECK + LIFT + 10, 2]); continue
        if near and near[0][0] < 1200:
            d1, x1, y1, z1 = near[0]; samp.append([x1, y1, z1 + DECK + LIFT, 1]); continue
        samp.append([p.x, p.y, p.z, 0])
    # smooth x/y/z of snapped samples (window 5) so the line doesn't wobble between centreline vertices
    sm = []
    for i, q in enumerate(samp):
        if q[3] == 0: sm.append(q); continue
        w = [samp[j] for j in range(max(0, i - 2), min(len(samp), i + 3)) if samp[j][3] == q[3]]
        sm.append([sum(v[0] for v in w) / len(w), sum(v[1] for v in w) / len(w), max(q[2], sum(v[2] for v in w) / len(w)), q[3]])
    set_pts(a, s, [unreal.Vector(q[0], q[1], q[2]) for q in sm])
    a.set_editor_property("Scale_X", KEY_W)
    c = a.get_editor_property("Route_Color"); a.set_editor_property("Route_Color", unreal.LinearColor(c.r * 0.999 + 0.0005, c.g, c.b, c.a)); a.set_editor_property("Route_Color", c)   # only a real change re-runs construction
    report["Road_" + rid] = dict(samples=len(sm), median=sum(1 for q in sm if q[3] == 2), centre=sum(1 for q in sm if q[3] == 1),
                                 meshes=len(a.get_components_by_class(unreal.SplineMeshComponent)))
# ---- landmark routes: thinner + height step per route (no z-fight where several share the highway)
routes = sorted(l for l in acts if l.startswith("Route_") and acts[l].get_class().get_name() == "BP_Route_C")
for idx, l in enumerate(routes):
    a = acts[l]; s, cur = get_pts(a)
    if l not in src: src[l] = [[v.x, v.y, v.z] for v in cur]
    dz = 5.0 * (idx + 1)
    cat = next((str(t)[7:] for t in a.tags if str(t).startswith("Neelam_") and str(t)[7:] in LANE), "Retail")
    vs = []; on = 0
    for p in src[l]:
        dk = deck_at(p[0], p[1])
        if dk is None: vs.append(unreal.Vector(p[0], p[1], p[2] + dz)); continue
        # on a built carriageway: its own lane per category (transit-map style, no colour patchwork), exact deck height
        z, cx, cy, tx, ty, hw = dk; on += 1
        off = max(-(hw - 1.3), min(hw - 1.3, LANE[cat])) * 100
        vs.append(unreal.Vector(cx - ty * off, cy + tx * off, z + DECK + LIFT + dz))
    set_pts(a, s, vs)
    a.set_editor_property("Scale_X", ROUTE_W)
    c = a.get_editor_property("Route_Color"); a.set_editor_property("Route_Color", unreal.LinearColor(c.r * 0.999 + 0.0005, c.g, c.b, c.a)); a.set_editor_property("Route_Color", c)
    report[l] = [dz, on, len(vs)]
json.dump(src, open(SRC, "w"))
unreal.EditorLevelLibrary.save_current_level()
result = report   # NOTE: run Ribbon_Heights.py after this (heights + site trim)
