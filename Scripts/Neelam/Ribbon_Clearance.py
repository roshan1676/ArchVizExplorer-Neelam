"""Ribbon clearance pass (30 Sep, client): no route / road glow / traffic ribbon may dip into the map.
Ribbon_Heights.py builds the heights from a CLEANED ground (7 % cones cut bumps away), so on embankments, ramps,
parapets and raised tile patches a ribbon could run inside the photogrammetry. Here every 3 m sample of the traced
map surface (Data/ribbon_surface.json, median of 5 traces across the ribbon, Ribbon_Surface_PIE.py) is compared with
the ribbon at that spot; where the ribbon is lower than surface + clearance, ONLY the spline point(s) around that spot
are raised (split by the spline key fraction, repeated until clear). Everything else stays untouched.
Clearance = the ribbon's normal lift: routes 30 cm + 4 cm per route (stacking order), road glows 35 cm, traffic 20 cm.
Run in the editor (not PIE). MODE "audit" only reports; "fix" edits + saves."""
import json, os, math
import unreal
P = os.path.join(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()), "Scripts", "Neelam")
MODE = globals().get("MODE", "audit")
RS = json.load(open(os.path.join(P, "Data", "ribbon_surface.json")))
CUT = json.load(open(os.path.join(P, "Data", "site_outline.json")))["cut"]
WS = unreal.SplineCoordinateSpace.WORLD
TOL = 2.0          # cm


def inside(x, y, poly=CUT):
    c = False; n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]; x2, y2 = poly[(i + 1) % n]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / ((y2 - y1) or 1e-9) + x1: c = not c
    return c


def lift(label, routes):
    if label.startswith("Route_"): return 30.0 + 4.0 * routes.index(label)
    if label.startswith("Road_"): return 35.0
    return 20.0


def deficits(s, samples, clr):
    out = []
    for x, y, z in samples:
        p = s.find_location_closest_to_world_location(unreal.Vector(x, y, z), WS)
        if math.hypot(p.x - x, p.y - y) > 150: continue
        need = z + clr
        if p.z < need - TOL:
            out.append((need - p.z, s.find_input_key_closest_to_world_location(unreal.Vector(x, y, z))))
    return out


def rebuild(a):
    s = a.get_component_by_class(unreal.SplineComponent)
    s.update_spline()
    for pr in ("spline_has_been_edited", "input_spline_points_to_construction_script"):
        try: s.set_editor_property(pr, True)
        except Exception: pass
    if a.get_class().get_name() == "BP_Route_C":
        c = a.get_editor_property("Route_Color")
        a.set_editor_property("Route_Color", unreal.LinearColor(c.r * 0.999 + 0.0005, c.g, c.b, c.a)); a.set_editor_property("Route_Color", c)
    else:
        w = a.get_editor_property("Width_Road")
        a.set_editor_property("Width_Road", w + 0.01); a.set_editor_property("Width_Road", w)


def run():
    acts = {a.get_actor_label(): a for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()}
    routes = sorted(l for l in RS if l.startswith("Route_"))
    rep = {}; tot_pts = 0
    for l, d in RS.items():
        a = acts.get(l)
        if a is None: continue
        s = a.get_component_by_class(unreal.SplineComponent)
        samples = [(xy[0], xy[1], z) for xy, z in zip(d["xy"], d["z"]) if xy is not None and z is not None and not inside(*xy)]
        clr = lift(l, routes)
        df = deficits(s, samples, clr)
        if not df: continue
        before = (len(df), round(max(x[0] for x in df) / 100, 2))
        if MODE != "fix":
            rep[l] = before; continue
        n = s.get_number_of_spline_points(); raised = {}
        orig = [s.get_location_at_spline_point(k, WS).z for k in range(n)]
        # 1) each spline point exactly to the highest need among the samples nearest to it (its half segments)
        want = {}
        for dz, k in df:
            j = min(n - 1, max(0, int(round(k))))
            p = s.get_location_at_spline_point(j, WS)
            need = s.get_location_at_spline_input_key(k, WS).z + dz
            want[j] = max(want.get(j, -1e9), need)
        for j, zt in want.items():
            p = s.get_location_at_spline_point(j, WS)
            if zt > p.z: s.set_location_at_spline_point(j, unreal.Vector(p.x, p.y, zt), WS, False)
        s.update_spline()
        # 2) residual dips of the curve between points: small steps on the nearer point only
        for it in range(10):
            df2 = deficits(s, samples, clr)
            if not df2: break
            step = {}
            for dz, k in df2:
                i0 = min(n - 1, max(0, int(math.floor(k)))); t = k - i0
                js = [i0, i0 + 1] if 0.3 < t < 0.7 else [i0 if t <= 0.5 else i0 + 1]
                for j in js:
                    if j < n: step[j] = max(step.get(j, 0.0), dz + 1.0)
            for j, dz in step.items():
                p = s.get_location_at_spline_point(j, WS)
                s.set_location_at_spline_point(j, unreal.Vector(p.x, p.y, p.z + dz), WS, False)
            s.update_spline()
        for k2 in range(n):
            dzk = s.get_location_at_spline_point(k2, WS).z - orig[k2]
            if dzk > 0.5: raised[k2] = dzk
        left = deficits(s, samples, clr)
        rebuild(a)
        tot_pts += len(raised)
        rep[l] = {"before": before, "points_raised": len(raised), "max_raise_m": round(max(raised.values()) / 100, 2) if raised else 0,
                  "left": len(left), "of_points": n}
    if MODE == "fix":
        unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    return {"mode": MODE, "ribbons": len(rep), "points_raised": tot_pts, "detail": rep}


if __name__ == "__main__" or "env" in globals():
    result = run()
