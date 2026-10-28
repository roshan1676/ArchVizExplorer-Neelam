"""Smooth tangents on every ribbon spline (27 Oct, client: "highlight dotted / broken" at bends). All Route_/Road_/Traffic_
splines had ZERO tangents on every point (user-set, so CURVE_CLAMPED never auto-computed them): BP_Route / BP_RoadTool
then build each 15 m SplineMesh piece as a straight slab cut square at its ends -> a wedge gap at every bend.
Tangent at point k = (P[k+1] - P[k-1]) / 2 (Catmull-Rom; one-sided at the ends); its Z is 0 where the point is a local
high / low (no height overshoot -> the ribbon can't dip below its points' ground). Run AFTER Ribbon_Rebuild_Z.py
(heights first), then re-check with Ribbon_Deck_Check.py. Editor world. MODE "audit" / "fix" / "selftest"."""
import unreal
MODE = globals().get("MODE", "audit")
LS = unreal.SplineCoordinateSpace.LOCAL


def tangents(P):
    """P: list of (x, y, z) -> list of tangents"""
    n = len(P); out = []
    for k in range(n):
        a, b = P[max(k - 1, 0)], P[min(k + 1, n - 1)]
        f = 1.0 if 0 < k < n - 1 else 2.0          # one-sided at the ends keeps the same scale
        t = [(b[i] - a[i]) / 2 * f for i in range(3)]
        if 0 < k < n - 1 and (P[k][2] - a[2]) * (b[2] - P[k][2]) <= 0: t[2] = 0.0   # local peak / dip: flat
        out.append(t)
    return out


def rebuild(a):
    s = a.get_component_by_class(unreal.SplineComponent); s.update_spline()
    if a.get_class().get_name() == "BP_Route_C":
        c = a.get_editor_property("Route_Color")
        a.set_editor_property("Route_Color", unreal.LinearColor(c.r * 0.999 + 0.0005, c.g, c.b, c.a)); a.set_editor_property("Route_Color", c)
    else:
        w = a.get_editor_property("Width_Road")
        a.set_editor_property("Width_Road", w + 0.01); a.set_editor_property("Width_Road", w)


if MODE == "selftest":
    T = tangents([(0, 0, 0), (1000, 0, 100), (2000, 1000, 50), (2000, 2000, 80)])
    assert T[1] == [1000.0, 500.0, 0.0], T[1]          # z peak at point 1 -> flat
    assert T[2] == [500.0, 1000.0, 0.0], T[2]          # z dip at point 2 -> flat
    assert tangents([(0, 0, 0), (1000, 0, 100), (2000, 0, 300)])[1][2] == 150.0   # steady climb keeps its slope
    assert T[0] == [1000.0, 0.0, 100.0]
    result = "ok"
else:
    rep = {"ribbons": 0, "zero_before": 0}
    for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        l = a.get_actor_label(); cn = a.get_class().get_name()
        if not ((cn == "BP_Route_C" and l.startswith(("Route_", "Road_"))) or (cn == "BP_RoadTool_C" and l.startswith("Traffic_"))): continue
        s = a.get_component_by_class(unreal.SplineComponent); n = s.get_number_of_spline_points()
        rep["ribbons"] += 1
        rep["zero_before"] += sum(1 for k in range(n) if s.get_tangent_at_spline_point(k, LS).length() < 1)
        if MODE != "fix": continue
        P = [(p.x, p.y, p.z) for p in (s.get_location_at_spline_point(k, LS) for k in range(n))]
        a.modify(); s.modify()
        for k, t in enumerate(tangents(P)):
            s.set_tangent_at_spline_point(k, unreal.Vector(*t), LS, False)
        rebuild(a)
    if MODE == "fix": unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    result = rep
