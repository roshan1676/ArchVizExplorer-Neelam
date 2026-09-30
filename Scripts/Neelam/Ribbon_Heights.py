"""Ribbon spline heights from Data/ribbon_surface.json (Ribbon_Surface_PIE.py) - editor (30 Sep).
Per ribbon, the 3 m ground profile is cleaned, then every spline point gets the highest cleaned ground within its half
segments + a small lift, so no segment dips under the map and nothing floats:
  1. inside the site cut-out -> site ground (Neelam_SiteGround top) - the old photogrammetry blocks there still collide;
     landmark routes are trimmed to start at the site boundary (they used to cut through the podium)
  2. upper 7 % cone: anything rising steeper than a road can is cut away (trees, cars, buildings, walls, overpasses)
  3. lower 7 % cone: tile holes filled
  4. on a built carriageway at the same level (+-2.5 m) -> exact deck top; within 3 m of its edge -> at least the deck
  5. 7.5 m mean
Lifts: routes 30 cm + 4 cm per route (stable stacking), key-road glows 35 cm, traffic strips 20 cm."""
import json, os, math
import unreal
P = os.path.join(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()), "Scripts", "Neelam")
RS = json.load(open(os.path.join(P, "Data", "ribbon_surface.json")))
RB = json.load(open(os.path.join(P, "Data", "road_build.json")))["roads"]
CUT = json.load(open(os.path.join(P, "Data", "site_outline.json")))["cut"]
acts = {a.get_actor_label(): a for a in unreal.EditorLevelLibrary.get_all_level_actors()}
SITE_Z = acts["Neelam_SiteGround"].get_actor_bounds(False)[0].z + acts["Neelam_SiteGround"].get_actor_bounds(False)[1].z
WS = unreal.SplineCoordinateSpace.WORLD
DECK = 12.0; STEP = 300.0
def inside(x, y, poly=CUT):
    c = False; n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]; x2, y2 = poly[(i + 1) % n]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / ((y2 - y1) or 1e-9) + x1: c = not c
    return c
grid = {}
for k, r in RB.items():
    for p in r["pts"]: grid.setdefault((int(p[0] // 2000), int(p[1] // 2000)), []).append((p[0], p[1], p[2], r["width_m"] * 50))
def deck(x, y):
    best = None
    for i in (-1, 0, 1):
        for j in (-1, 0, 1):
            for (px, py, pz, hw) in grid.get((int(x // 2000) + i, int(y // 2000) + j), []):
                d = math.hypot(px - x, py - y) - hw           # < 0 inside the carriageway
                if d < 300 and (best is None or d < best[0]): best = (d, pz + DECK)
    return best
def win(a, i, h): return a[max(0, i - h): i + h + 1]
def clean(xy, z):
    n = len(z)
    good = [i for i in range(n) if z[i] is not None]
    if not good: return None
    zz = []
    for i in range(n):
        if z[i] is not None: zz.append(z[i]); continue
        a = max([g for g in good if g < i], default=None); b = min([g for g in good if g > i], default=None)
        zz.append(z[b] if a is None else z[a] if b is None else z[a] + (z[b] - z[a]) * (i - a) / (b - a))
    site = [inside(*xy[i]) for i in range(n)]
    zz = [SITE_Z if site[i] else zz[i] for i in range(n)]
    raw = zz[:]
    # roads never climb or fall faster than ~7 %: an upper 7 % cone removes everything that rises steeper (buildings,
    # walls, trees, buses, overpasses, old photogrammetry blocks at the site edge), a lower one fills tile holes
    G = 0.07 * STEP
    for rng in (range(1, n), range(n - 2, -1, -1)):
        for i in rng:
            j = i - 1 if rng.step == 1 else i + 1
            zz[i] = min(zz[i], zz[j] + G)
    for rng in (range(1, n), range(n - 2, -1, -1)):
        for i in rng:
            j = i - 1 if rng.step == 1 else i + 1
            zz[i] = max(zz[i], zz[j] - G)
    ondeck = 0
    for i in range(n):
        if site[i]: continue
        dk = deck(*xy[i])
        if dk and (abs(dk[1] - zz[i]) < 250 or abs(dk[1] - raw[i]) < 250):      # same level as the traced map (flyover decks too)
            if dk[0] < -50: zz[i] = dk[1]; ondeck += 1
            else: zz[i] = max(zz[i], dk[1])
    zz = [sum(win(zz, i, 1)) / len(win(zz, i, 1)) for i in range(n)]
    return zz, ondeck
rep = {}; routes = sorted(l for l in RS if l.startswith("Route_"))
for l, d in RS.items():
    a = acts.get(l)
    if a is None: continue
    res = clean(d["xy"], d["z"])
    if res is None: rep[l] = "no data"; continue
    g, ondeck = res; D = d["d"]
    lift = (30.0 + 4.0 * routes.index(l)) if l.startswith("Route_") else 35.0 if l.startswith("Road_") else 20.0
    s = a.get_component_by_class(unreal.SplineComponent)
    if l.startswith("Route_"):      # routes start at the site boundary (no ribbon through the building / podium)
        while s.get_number_of_spline_points() > 2 and inside(*[(lambda v: (v.x, v.y))(s.get_location_at_spline_point(1, WS))][0]):
            s.remove_spline_point(0, False)
        if s.get_number_of_spline_points() > 2 and inside(*[(lambda v: (v.x, v.y))(s.get_location_at_spline_point(0, WS))][0]):
            s.remove_spline_point(0, False)
        s.update_spline()
    np_ = s.get_number_of_spline_points()
    XY = d["xy"]; pts = [s.get_location_at_spline_point(i, WS) for i in range(np_)]
    near = []; j0 = 0                       # nearest 3 m sample of every spline point (by position, monotonic search)
    for p in pts:
        best = min(range(j0, len(XY)), key=lambda k: (XY[k][0] - p.x) ** 2 + (XY[k][1] - p.y) ** 2) if j0 < len(XY) else len(XY) - 1
        near.append(best); j0 = max(0, best - 5)
    worst = 0.0
    for i, p in enumerate(pts):
        lo = (near[i - 1] + near[i]) // 2 if i > 0 else near[i]; hi = (near[i] + near[i + 1] + 1) // 2 if i < np_ - 1 else near[i]
        zt = max(g[k] for k in range(min(lo, hi), max(lo, hi) + 1)) + lift
        worst = max(worst, abs(p.z - zt))
        s.set_location_at_spline_point(i, unreal.Vector(p.x, p.y, zt), WS, False)
    s.update_spline()
    for pr in ("spline_has_been_edited", "input_spline_points_to_construction_script"):
        try: s.set_editor_property(pr, True)
        except Exception: pass
    # the construction script only re-runs when a property really CHANGES -> nudge and restore
    if a.get_class().get_name() == "BP_Route_C":
        c = a.get_editor_property("Route_Color")
        a.set_editor_property("Route_Color", unreal.LinearColor(c.r * 0.999 + 0.0005, c.g, c.b, c.a)); a.set_editor_property("Route_Color", c)
    else:
        w = a.get_editor_property("Width_Road")
        a.set_editor_property("Width_Road", w + 0.01); a.set_editor_property("Width_Road", w)
    rep[l] = [np_, ondeck, len(D), round(worst / 100, 1), len(a.get_components_by_class(unreal.SplineMeshComponent))]
unreal.EditorLevelLibrary.save_current_level()
result = {"site_z": SITE_Z, "ribbons": len(rep), "biggest_changes_m": sorted(((v[3], k) for k, v in rep.items() if isinstance(v, list)), reverse=True)[:12]}
