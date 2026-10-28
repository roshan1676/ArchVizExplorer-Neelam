"""Static audit of every route ribbon (27 Oct, client: "check each and every route, none shall be broken, each landmark
one dedicated smooth path"). Editor world, read-only. Per landmark pin (BP_POI with an LM_<id> tag): exactly one
Route_* (BP_Route, tags Neelam_Route + LM_<id>), its end close to the pin, its start at the site. Per ribbon
(Route_* / Road_* / Traffic_*): duplicate points, hairpins / sharp kinks, height spikes and steep grades.
Ground clearance is NOT checked here (needs PIE tiles): Ribbon_Surface_PIE.py -> Ribbon_Clearance.py does that.
result = {"landmarks": {...}, "problems": {label: [..]}, "counts": {...}}"""
import math
import unreal
WS = unreal.SplineCoordinateSpace.WORLD
SITE = (4000.0, 3000.0)          # project centre (towers C/D/E deck)
END_MAX = 25000.0                # route end within 250 m of its pin (pins sit on the building, routes end on the road)
START_MAX = 40000.0              # route start within 400 m of the site centre


def pts(a):
    s = a.get_component_by_class(unreal.SplineComponent)
    return s, [s.get_location_at_spline_point(k, WS) for k in range(s.get_number_of_spline_points())]


def shape_problems(P):
    out = []
    for k in range(1, len(P)):
        d = math.hypot(P[k].x - P[k - 1].x, P[k].y - P[k - 1].y)
        if d < 150: out.append(("dup", k, round(d)))
        elif d > 500:
            g = abs(P[k].z - P[k - 1].z) / d
            if g > 0.15: out.append(("steep", k, round(g * 100), round(P[k].z - P[k - 1].z)))
    for k in range(1, len(P) - 1):
        ax, ay = P[k].x - P[k - 1].x, P[k].y - P[k - 1].y; bx, by = P[k + 1].x - P[k].x, P[k + 1].y - P[k].y
        la, lb = math.hypot(ax, ay), math.hypot(bx, by)
        if la < 1 or lb < 1: continue
        turn = math.degrees(math.acos(max(-1, min(1, (ax * bx + ay * by) / (la * lb)))))
        if turn > 100: out.append(("hairpin", k, round(turn)))
        elif turn > 60 and min(la, lb) < 3000: out.append(("kink", k, round(turn), round(min(la, lb) / 100)))
        # z spike: point far off the line between its neighbours
        t = la / (la + lb); zl = P[k - 1].z + (P[k + 1].z - P[k - 1].z) * t
        if abs(P[k].z - zl) > 300 and la + lb < 20000: out.append(("zspike", k, round((P[k].z - zl) / 100, 1)))
    return out


acts = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
pois = {}; routes = {}; ribbons = []
for a in acts:
    cn = a.get_class().get_name(); l = a.get_actor_label(); tags = [str(t) for t in a.tags]
    lm = next((t[3:] for t in tags if t.startswith("LM_")), None)
    if cn == "BP_POI_C" and lm: pois[lm] = a
    if cn == "BP_Route_C" and (l.startswith("Route_") or l.startswith("Road_")) or (cn == "BP_RoadTool_C" and l.startswith("Traffic_")):
        ribbons.append(a)
        if "Neelam_Route" in tags and lm and cn == "BP_Route_C": routes.setdefault(lm, []).append(a)

land = {}
for lm, poi in sorted(pois.items()):
    rs = routes.get(lm, [])
    e = {"pin": poi.get_actor_label(), "routes": [r.get_actor_label() for r in rs]}
    if len(rs) == 1:
        s, P = pts(rs[0]); pl = poi.get_actor_location()
        ends = [P[0], P[-1]]
        de = [math.hypot(p.x - pl.x, p.y - pl.y) for p in ends]; ds = [math.hypot(p.x - SITE[0], p.y - SITE[1]) for p in ends]
        e.update(points=len(P), km=round(s.get_spline_length() / 100000, 2),
                 end_to_pin_m=round(min(de) / 100), start_to_site_m=round(min(ds) / 100),
                 hidden=rs[0].is_hidden_ed(), hidden_game=rs[0].get_editor_property("hidden"))
        if min(de) > END_MAX: e["PROBLEM"] = "route ends %d m from its pin" % (min(de) / 100)
        elif min(ds) > START_MAX: e["PROBLEM"] = "route does not start at the site (%d m)" % (min(ds) / 100)
    else:
        e["PROBLEM"] = "%d routes (want exactly 1)" % len(rs)
    land[lm] = e

probs = {}
for a in ribbons:
    s, P = pts(a)
    pr = shape_problems(P)
    if pr: probs[a.get_actor_label()] = pr[:12] + ([("...", len(pr))] if len(pr) > 12 else [])
orphans = sorted(lm for lm in routes if lm not in pois)
result = {"landmarks": land, "landmark_problems": {k: v["PROBLEM"] for k, v in land.items() if "PROBLEM" in v},
          "routes_without_pin": orphans, "shape_problems": probs,
          "counts": {"pins": len(pois), "ribbons": len(ribbons), "route_actors": sum(len(v) for v in routes.values())}}
