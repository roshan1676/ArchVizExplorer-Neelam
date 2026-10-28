"""Fill short valleys in ribbon heights (27 Oct): a ribbon must not dive into a gap between two decks / under a bridge
whose deck was not detected (Road_mar dived 6.9 m at a creek bridge). Morphological closing of the spline point heights
over +-HALF metres along the spline: z_fill = min(max z behind, max z ahead); a point is raised to z_fill where that is
more than DEPTH higher - i.e. dips up to HALF wide and deeper than DEPTH; steady slopes / ramps are untouched.
Editor world. MODE "audit" / "fix" (rebuilds the ribbons, saves the level)."""
import bisect
import unreal
MODE = globals().get("MODE", "audit"); HALF, DEPTH = 10000.0, 100.0   # fills dips up to HALF wide (MAR bridge deck gap ~65 m)
WS = unreal.SplineCoordinateSpace.WORLD


def closing(D, Z):
    out = []
    for k, d in enumerate(D):
        i, j = bisect.bisect_left(D, d - HALF), bisect.bisect_right(D, d + HALF)
        out.append(min(max(Z[i:k + 1]), max(Z[k:j])))
    return out


def rebuild(a):
    s = a.get_component_by_class(unreal.SplineComponent); s.update_spline()
    if a.get_class().get_name() == "BP_Route_C":
        c = a.get_editor_property("Route_Color")
        a.set_editor_property("Route_Color", unreal.LinearColor(c.r * 0.999 + 0.0005, c.g, c.b, c.a)); a.set_editor_property("Route_Color", c)
    else:
        w = a.get_editor_property("Width_Road")
        a.set_editor_property("Width_Road", w + 0.01); a.set_editor_property("Width_Road", w)


def selftest():
    D = [i * 1500.0 for i in range(20)]; Z = [1000.0] * 20; Z[9] = Z[10] = 300.0     # 3 m deep, 3 m wide dip
    F = closing(D, Z); assert F[9] == 1000 and F[10] == 1000 and F[0] == 1000
    Z2 = [i * 50.0 for i in range(20)]; assert closing(D, Z2) == Z2                      # steady ramp untouched
    Z3 = [700.0] * 30; Z3[10:16] = [50.0, 40.0, 60.0, 30.0, 100.0, 120.0]                # 6-point (~75 m) bridge gap
    assert all(v == 700 for v in closing(D, Z3)), closing(D, Z3)
    return "ok"


rep = {}
if MODE == "selftest": result = selftest()
else:
    for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        l = a.get_actor_label(); cn = a.get_class().get_name()
        if not ((cn == "BP_Route_C" and l.startswith(("Route_", "Road_"))) or (cn == "BP_RoadTool_C" and l.startswith("Traffic_"))): continue
        s = a.get_component_by_class(unreal.SplineComponent); n = s.get_number_of_spline_points()
        D = [s.get_distance_along_spline_at_spline_point(k) for k in range(n)]; Z = [s.get_location_at_spline_point(k, WS).z for k in range(n)]
        F = closing(D, Z); up = [(k, F[k] - Z[k]) for k in range(n) if F[k] - Z[k] > DEPTH]
        if not up: continue
        rep[l] = {"points": len(up), "max_fill_m": round(max(u[1] for u in up) / 100, 2), "at_m": round(D[max(up, key=lambda u: u[1])[0]] / 100)}
        if MODE == "fix":
            a.modify(); s.modify()
            for k, dz in up:
                p = s.get_location_at_spline_point(k, WS); s.set_location_at_spline_point(k, unreal.Vector(p.x, p.y, p.z + dz), WS, False)
            rebuild(a)
    if MODE == "fix": unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    result = {"mode": MODE, "ribbons": len(rep), "detail": rep}
