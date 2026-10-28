"""Rebuild every ribbon's spline heights from the measured ground in ONE deterministic pass (27 Oct). Replaces the
incremental raise / lower / valley-fill passes, which fought each other (V-dips into deck gaps, then 7 m hovering over
real terrain dips). Inputs: Data/ribbon_surface.json (3 m samples), Data/ribbon_ground.json (Ribbon_Deck_Check.py:
ground = max(map, the road deck MESH the ribbon runs along), plus which deck).
  1. deck gaps: a run of samples without a deck, <= GAP long, between two deck samples (MAR creek bridge: no deck mesh
     for ~65 m, map = creek 7 m lower) -> ground bridged linearly between the two rims. Natural dips are NOT filled.
  2. each spline point z = max(bridged ground from halfway to the previous point to halfway to the next one, at least
     +-NEAR - so every sample belongs to a point and no hump between two points pokes through) + lift (routes 30 cm + 4 cm per route, glows 35, traffic 20)
     - raised or lowered.
Editor world. MODE "audit" / "fix" (rebuilds the ribbons, saves the level) / "selftest"."""
import json, bisect
import unreal
MODE = globals().get("MODE", "audit")
GAP, NEAR = 12000.0, 450.0
WS = unreal.SplineCoordinateSpace.WORLD


def bridge(D, G, deck):
    """ground with deck gaps (<= GAP, deck on both sides) filled linearly between the rims"""
    G = list(G); n = len(G); i = 0
    while i < n:
        if deck[i] is None and i > 0 and deck[i - 1] is not None and G[i - 1] is not None:
            j = i
            while j < n and deck[j] is None: j += 1
            if j < n and G[j] is not None and D[j] - D[i - 1] <= GAP:
                a, b = G[i - 1], G[j]
                for k in range(i, j):
                    t = (D[k] - D[i - 1]) / (D[j] - D[i - 1]); line = a + (b - a) * t
                    G[k] = line if G[k] is None else max(G[k], line)
            i = j
        else: i += 1
    return G


def lift(label, routes):
    if label.startswith("Route_"): return 30.0 + 4.0 * routes.index(label)
    if label.startswith("Road_"): return 35.0
    return 20.0


def rebuild(a):
    s = a.get_component_by_class(unreal.SplineComponent); s.update_spline()
    if a.get_class().get_name() == "BP_Route_C":
        c = a.get_editor_property("Route_Color")
        a.set_editor_property("Route_Color", unreal.LinearColor(c.r * 0.999 + 0.0005, c.g, c.b, c.a)); a.set_editor_property("Route_Color", c)
    else:
        w = a.get_editor_property("Width_Road")
        a.set_editor_property("Width_Road", w + 0.01); a.set_editor_property("Width_Road", w)


def selftest():
    D = [i * 300.0 for i in range(60)]; G = [700.0] * 60; deck = ["d"] * 60
    for k in range(20, 40): G[k] = 0.0; deck[k] = None                       # 60 m deck gap over a creek -> bridged
    assert all(abs(v - 700) < 1e-6 for v in bridge(D, G, deck))
    G2 = [700.0] * 60; deck2 = [None] * 60
    for k in range(20, 40): G2[k] = 0.0                                       # natural dip, no decks -> followed
    assert bridge(D, G2, deck2)[30] == 0.0
    return "ok"


if MODE == "selftest": result = selftest()
else:
    P = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()) + "Scripts/Neelam/Data/"
    RS = json.load(open(P + "ribbon_surface.json")); RG = json.load(open(P + "ribbon_ground.json"))
    by = {a.get_actor_label(): a for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()}
    routes = sorted(l for l in RS if l.startswith("Route_")); rep = {}
    for l in RS:
        a = by[l]; s = a.get_component_by_class(unreal.SplineComponent); clr = lift(l, routes)
        D = RS[l]["d"]; G = bridge(D, RG[l]["g"], RG[l]["deck"]); moves = []
        n = s.get_number_of_spline_points(); DK = [s.get_distance_along_spline_at_spline_point(k) for k in range(n)]
        for k in range(n):
            dk = DK[k]
            lo = dk - max(NEAR, (dk - DK[k - 1]) / 2 + 1) if k else dk - NEAR
            hi = dk + max(NEAR, (DK[k + 1] - dk) / 2 + 1) if k < n - 1 else dk + NEAR
            v = [g for g in G[bisect.bisect_left(D, lo):bisect.bisect_right(D, hi)] if g is not None]
            if not v: continue
            p = s.get_location_at_spline_point(k, WS); dz = max(v) + clr - p.z
            if abs(dz) > 2: moves.append((k, dz))
        if not moves: continue
        rep[l] = {"points": len(moves), "max_up_m": round(max([m[1] for m in moves] + [0]) / 100, 2), "max_down_m": round(-min([m[1] for m in moves] + [0]) / 100, 2)}
        if MODE == "fix":
            a.modify(); s.modify()
            for k, dz in moves:
                p = s.get_location_at_spline_point(k, WS); s.set_location_at_spline_point(k, unreal.Vector(p.x, p.y, p.z + dz), WS, False)
            rebuild(a)
    if MODE == "fix": unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    result = {"mode": MODE, "ribbons": len(rep), "detail": rep}
