"""Ribbon tidy (1 Oct): remove spline points that make hooks / kinks.
 - duplicate points (< 1.5 m from the previous one) - the key-road glows were stitched from carriageway pieces and had
   pairs of identical points -> the spline tangent flips there and the ribbon draws a hook
 - hairpin points: the line doubles back (turn > 100 deg) at a single point
Repeated until clean; route end points are never removed. MODE audit / fix. Run before Ribbon_Clearance."""
import math
import unreal
MODE = globals().get("MODE", "audit")
WS = unreal.SplineCoordinateSpace.WORLD


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


def bad_points(P):
    n = len(P); out = []
    for i in range(1, n - 1):
        if math.hypot(P[i][0] - P[i - 1][0], P[i][1] - P[i - 1][1]) < 150: out.append(i); continue
        h1 = math.atan2(P[i][1] - P[i - 1][1], P[i][0] - P[i - 1][0]); h2 = math.atan2(P[i + 1][1] - P[i][1], P[i + 1][0] - P[i][0])
        if abs((h2 - h1 + math.pi) % (2 * math.pi) - math.pi) > math.radians(100): out.append(i)
    return out


def run():
    rep = {}
    for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        l = a.get_actor_label()
        if a.get_class().get_name() not in ("BP_Route_C", "BP_RoadTool_C") or l.startswith("Poles"): continue
        s = a.get_component_by_class(unreal.SplineComponent)
        removed = 0
        for it in range(20):
            n = s.get_number_of_spline_points()
            P = [(lambda v: (v.x, v.y))(s.get_location_at_spline_point(i, WS)) for i in range(n)]
            b = bad_points(P)
            if not b or n <= 3: break
            # remove one per 3 so neighbours are re-evaluated
            last = -9; sel = []
            for i in b:
                if i - last >= 2: sel.append(i); last = i
            removed += len(sel)
            if MODE != "fix": break
            for i in reversed(sel): s.remove_spline_point(i, False)
            s.update_spline()
        if removed:
            rep[l] = removed
            if MODE == "fix": rebuild(a)
    if MODE == "fix" and rep:
        unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    return rep


result = run()
