"""Remove individual grey massing blocks (editor, 30 Sep). The blocks are merged into one mesh per 500 m chunk, so a
click selects the whole chunk. To drop single blocks: place a Target Point (Place Actors > Basic) ON each unwanted
block and name it RemoveBlock (RemoveBlock_1, ... any name starting with RemoveBlock), then run this job:
the footprint under each marker goes into Data/massing_exclude.json and the markers are deleted.
Then rebuild: make_massing.py -> Blender/build_massing.py -> Import_Massing.py."""
import json, os
import unreal
P = os.path.join(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()), "Scripts", "Neelam", "Data")
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
B = json.load(open(os.path.join(P, "massing_build.json")))
EXF = os.path.join(P, "massing_exclude.json")
ex = set(json.load(open(EXF))) if os.path.exists(EXF) else set()
def inside(x, y, poly):
    c = False
    for i in range(len(poly)):
        x1, y1 = poly[i]; x2, y2 = poly[i - 1]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / ((y2 - y1) or 1e-9) + x1: c = not c
    return c
found, missed = [], []
for a in [a for a in EAS.get_all_level_actors() if a.get_actor_label().startswith("RemoveBlock")]:
    p = a.get_actor_location()
    hit = [b for b in B if inside(p.x, p.y, b["pts"])]
    if not hit:   # nearest footprint centre within 15 m
        hit = sorted(B, key=lambda b: (sum(q[0] for q in b["pts"]) / len(b["pts"]) - p.x) ** 2 + (sum(q[1] for q in b["pts"]) / len(b["pts"]) - p.y) ** 2)[:1]
        c = hit[0]["pts"]; cx = sum(q[0] for q in c) / len(c); cy = sum(q[1] for q in c) / len(c)
        if (cx - p.x) ** 2 + (cy - p.y) ** 2 > 1500 ** 2: missed.append(a.get_actor_label()); continue
    for b in hit: ex.add(b["id"]); found.append(b["id"])
    EAS.destroy_actor(a)
json.dump(sorted(ex), open(EXF, "w"))
result = {"removed_ids": found, "markers_without_block": missed, "excluded_total": len(ex)}
