"""Remove U-turn detour loops from the landmark routes (30 Sep, client: "splines curved / going out of the route").
OSRM routes turn around where the destination / the site gate is on the other side of a divided road -> the ribbon
runs out and comes back on the other side (a 250 m - 1.2 km loop: site west gate, Check Naka toll plaza, route ends).
A loop = the route comes back within LOOP_M of a point it passed 250 m or more earlier. The spline points strictly
inside the loop are deleted, so the ribbon goes straight from the loop entry to the loop exit (<= LOOP_M apart).
Traffic strips of the same route (Traffic_route_<id>_*): points along the removed loop (within 20 m of it and more
than 20 m from the kept route) are removed; a strip cut in the middle keeps its longer side; a strip with < 3 points
left is deleted. MODE audit / fix. Run before Ribbon_Heights? No - after it: Ribbon_Heights -> Ribbon_Snap ->
Route_Loops -> Ribbon_Clearance."""
import math
import unreal
MODE = globals().get("MODE", "audit")
LOOP_M = 45.0; MIN_DETOUR_M = 250.0
WS = unreal.SplineCoordinateSpace.WORLD
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def rebuild(a):
    s = a.get_component_by_class(unreal.SplineComponent); s.update_spline()
    for pr in ("spline_has_been_edited", "input_spline_points_to_construction_script"):
        try: s.set_editor_property(pr, True)
        except Exception: pass
    if a.get_class().get_name() == "BP_Route_C":
        c = a.get_editor_property("Route_Color")
        a.set_editor_property("Route_Color", unreal.LinearColor(c.r * 0.999 + 0.0005, c.g, c.b, c.a)); a.set_editor_property("Route_Color", c)
    else:
        w = a.get_editor_property("Width_Road")
        a.set_editor_property("Width_Road", w + 0.01); a.set_editor_property("Width_Road", w)


def find_loops(P, D):
    loops = []; i = 0; n = len(P)
    while i < n:
        best = None
        for j in range(i + 2, n):
            if D[j] - D[i] > 2500 * 100: break
            if D[j] - D[i] >= MIN_DETOUR_M * 100 and math.hypot(P[j][0] - P[i][0], P[j][1] - P[i][1]) < LOOP_M * 100:
                best = j
        if best is not None:
            loops.append((i, best)); i = best
        else:
            i += 1
    return loops


def segd(p, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]; L = dx * dx + dy * dy or 1e-9
    t = max(0, min(1, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L)); return math.hypot(p[0] - a[0] - t * dx, p[1] - a[1] - t * dy)


def pdist(p, poly):
    return min(segd(p, poly[k], poly[k + 1]) for k in range(len(poly) - 1)) if len(poly) > 1 else 1e9


def run():
    acts = {a.get_actor_label(): a for a in EAS.get_all_level_actors()}
    rep = {}
    for l, a in sorted(acts.items()):
        if not l.startswith("Route_") or a.get_class().get_name() != "BP_Route_C": continue
        s = a.get_component_by_class(unreal.SplineComponent); n = s.get_number_of_spline_points()
        P = [(lambda v: (v.x, v.y))(s.get_location_at_spline_point(i, WS)) for i in range(n)]
        D = [s.get_distance_along_spline_at_spline_point(i) for i in range(n)]
        loops = find_loops(P, D)
        if not loops: continue
        removed_polys = [P[i:j + 1] for i, j in loops]
        drop = sorted({k for i, j in loops for k in range(i + 1, j)}, reverse=True)
        kept = [P[k] for k in range(n) if k not in set(drop)]
        rep[l] = {"loops": [(round(D[i] / 100), round((D[j] - D[i]) / 100)) for i, j in loops], "points_removed": len(drop), "traffic": {}}
        if MODE == "fix":
            for k in drop: s.remove_spline_point(k, False)
            rebuild(a)
        # traffic strips of this route
        rid = l[len("Route_"):]
        for tl, ta in sorted(acts.items()):
            if not tl.startswith("Traffic_route_%s_" % rid): continue
            ts = ta.get_component_by_class(unreal.SplineComponent); tn = ts.get_number_of_spline_points()
            TP = [(lambda v: (v.x, v.y))(ts.get_location_at_spline_point(i, WS)) for i in range(tn)]
            bad = [any(pdist(p, rp) < 2000 for rp in removed_polys) and pdist(p, kept) > 2000 for p in TP]
            if not any(bad): continue
            good_runs = []; i = 0
            while i < tn:
                if not bad[i]:
                    j = i
                    while j + 1 < tn and not bad[j + 1]: j += 1
                    good_runs.append((i, j)); i = j + 1
                else: i += 1
            keep = max(good_runs, key=lambda r: r[1] - r[0]) if good_runs else None
            if keep is None or keep[1] - keep[0] + 1 < 3:
                rep[l]["traffic"][tl] = "deleted"
                if MODE == "fix": EAS.destroy_actor(ta)
                continue
            rep[l]["traffic"][tl] = "kept %d-%d of %d" % (keep[0], keep[1], tn)
            if MODE == "fix":
                for k in range(tn - 1, -1, -1):
                    if not (keep[0] <= k <= keep[1]): ts.remove_spline_point(k, False)
                rebuild(ta)
    if MODE == "fix":
        unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    return rep


result = run()
