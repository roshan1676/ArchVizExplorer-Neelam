"""Smooth the key-road glow lines Road_eeh / Road_vb / Road_mar sideways (1 Oct, client: "glow weaving / not straight").
Fix_Highway_Glow.py puts them on the median between the two carriageways; where the carriageway pairs change (bridges,
ramps, junctions) the median point jumps -> the line weaves across the lanes. Only zig-zags are removed (see run()); Z is untouched (it came from
Ribbon_Heights / Ribbon_Clearance). End points stay. MODE audit / fix. Afterwards run Ribbon_Clearance fix."""
import math
import unreal
MODE = globals().get("MODE", "audit")
WS = unreal.SplineCoordinateSpace.WORLD
K = 4; TH = 60.0


def rebuild(a):
    s = a.get_component_by_class(unreal.SplineComponent); s.update_spline()
    for pr in ("spline_has_been_edited", "input_spline_points_to_construction_script"):
        try: s.set_editor_property(pr, True)
        except Exception: pass
    c = a.get_editor_property("Route_Color")
    a.set_editor_property("Route_Color", unreal.LinearColor(c.r * 0.999 + 0.0005, c.g, c.b, c.a)); a.set_editor_property("Route_Color", c)


def offsets(P):
    o = [0.0] * len(P)
    for i in range(1, len(P) - 1):
        ax, ay, bx, by = P[i - 1][0], P[i - 1][1], P[i + 1][0], P[i + 1][1]
        L = math.hypot(bx - ax, by - ay) or 1.0
        o[i] = ((bx - ax) * (P[i][1] - ay) - (by - ay) * (P[i][0] - ax)) / L      # signed distance from the chord
    return o


def run():
    """zig-zag only: a point off its neighbours' chord by > 0.8 m whose neighbour is off to the OTHER side (> 0.4 m)
    is moved onto the chord. On a real bend all offsets have the same sign -> bends are never cut."""
    rep = {}
    for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        l = a.get_actor_label()
        if not l.startswith("Road_") or a.get_class().get_name() != "BP_Route_C": continue
        s = a.get_component_by_class(unreal.SplineComponent); n = s.get_number_of_spline_points()
        P0 = [s.get_location_at_spline_point(i, WS) for i in range(n)]
        P = [[p.x, p.y] for p in P0]; moved = set(); first = None
        for it in range(8):
            o = offsets(P); z = []
            for i in range(1, n - 1):
                if abs(o[i]) > 80 and ((i > 1 and o[i - 1] * o[i] < 0 and abs(o[i - 1]) > 40) or (i < n - 2 and o[i + 1] * o[i] < 0 and abs(o[i + 1]) > 40)):
                    z.append(i)
            if first is None: first = (len(z), round(max([abs(o[i]) for i in z], default=0) / 100, 2))
            if not z: break
            for i in z:
                P[i] = [(P[i - 1][0] + P[i + 1][0]) / 2, (P[i - 1][1] + P[i + 1][1]) / 2]; moved.add(i)
        rep[l] = {"points": n, "zig_points": first, "moved": len(moved)}
        if MODE == "fix" and moved:
            for i in moved:
                s.set_location_at_spline_point(i, unreal.Vector(P[i][0], P[i][1], P0[i].z), WS, False)
            rebuild(a)
    if MODE == "fix":
        unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    return rep


result = run()
