"""Which ribbon samples are COVERED by one of our road deck meshes (27 Oct, PIE shots: JBCN / Vaze routes vanished under
a neighbouring carriageway's deck). Editor world, read-only. Per 3 m sample (Data/ribbon_surface.json) every deck whose
bounds contain it is traced straight down from 6 m above the ribbon; a deck surface between the ribbon and 6 m above
it = covered (real underpasses have more headroom). Hits at the trace start (start inside the mesh) are ignored.
result: {label: [(start m, length m, max cover cm, deck), ...]}; also Data/ribbon_covered.json {label: [cover cm|None]}"""
import json
import unreal
P = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()) + "Scripts/Neelam/Data/"
RS = json.load(open(P + "ribbon_surface.json"))
acts = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors(); by = {a.get_actor_label(): a for a in acts}
decks = []
for a in acts:
    if a.get_class().get_name() == "StaticMeshActor" and a.get_actor_label().startswith("Road_"):
        o, e = a.get_actor_bounds(False); decks.append((o.x - e.x, o.y - e.y, o.x + e.x, o.y + e.y, a.static_mesh_component, a.get_actor_label()))
WS = unreal.SplineCoordinateSpace.WORLD; rep = {}; cov = {}
for l, d in RS.items():
    s = by[l].get_component_by_class(unreal.SplineComponent); C = []; runs = []
    for dd, xy in zip(d["d"], d["xy"]):
        x, y = xy; rz = s.get_location_at_distance_along_spline(dd, WS).z; best = None
        for x0, y0, x1, y1, c, dl in decks:
            if not (x0 <= x <= x1 and y0 <= y <= y1): continue
            r = c.line_trace_component(unreal.Vector(x, y, rz + 600), unreal.Vector(x, y, rz - 5), True, False, False)
            if r and r[0].z < rz + 598 and (best is None or r[0].z > best[0]): best = (r[0].z, dl)
        cz = None if best is None else round(best[0] - rz)
        C.append(cz)
        if cz is not None:
            if runs and dd / 100 - runs[-1][1] <= 6: runs[-1][1] = dd / 100; runs[-1][2] = max(runs[-1][2], cz)
            else: runs.append([dd / 100, dd / 100, cz, best[1]])
    cov[l] = C
    if runs: rep[l] = [(round(a), round(b - a), c, dl) for a, b, c, dl in runs]
json.dump(cov, open(P + "ribbon_covered.json", "w"))
result = rep
