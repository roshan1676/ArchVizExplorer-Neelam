"""Neelam - optimised trees and bushes around and inside the site (run INSIDE Unreal / via bridge).

One actor 'Neelam_Vegetation' holding one Hierarchical Instanced Static Mesh component per species
(= 1 draw call per species, per-instance LOD + distance culling). Candidate spots come from
Data/tree_candidates.json; each is validated with traces:
  * outside the wall: must land on the map at ground level, flat within 1.5 m over a 3 m radius,
    nothing overhead (no roofs / existing buildings / cars)
  * inside the wall: must land on lawn or planting (never on driveway, walkways, courts, podium)
Re-runnable (replaces the previous planting). Tweak BUDGET / SCALE below.
"""
import json, math, os, random, unreal

BUDGET = {"street_trees": 50, "edge_trees": 45, "lawn_trees": 22, "edge_bushes": 100}
MIN_GAP_CM = {"street_trees": 900, "edge_trees": 800, "lawn_trees": 1200, "edge_bushes": 350}
MESH = {"beech": "/Game/ArchVizExplorer/Environment/Foliage/SM_Tree_Beech_01",
        "pine": "/Game/ArchVizExplorer/Environment/Foliage/SM_Tree_Pine_01",
        "bush": "/Game/ArchVizExplorer/Environment/Foliage/SM_Bush_01"}
MIX = {"street_trees": [("beech", 0.7, (0.42, 0.56)), ("pine", 0.3, (0.85, 1.15))],
       "edge_trees":   [("beech", 0.6, (0.34, 0.46)), ("pine", 0.4, (0.75, 1.0))],
       "lawn_trees":   [("beech", 0.8, (0.30, 0.42)), ("pine", 0.2, (0.7, 0.9))],
       "edge_bushes":  [("bush", 1.0, (0.45, 0.8))]}
CULL = {"beech": (60000, 80000), "pine": (50000, 70000), "bush": (15000, 22000)}   # cm
INSIDE_OK = ("Neelam_SiteGround", "SM_Site_PlantingBeds")   # never on the amenity decks (user, 29 Sep)
LABEL = "Neelam_Vegetation"

PROJECT = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
C = json.load(open(os.path.join(PROJECT, "Scripts", "Neelam", "Data", "tree_candidates.json")))
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
EAL = unreal.EditorAssetLibrary
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
by_label = lambda l: next((a for a in EAS.get_all_level_actors() if a.get_actor_label() == l), None)
root = by_label("Neelam_WindTunnel_Root")
XF = root.get_actor_transform()
RZ = root.get_actor_location().z
old = by_label(LABEL)
if old:
    EAS.destroy_actor(old)
rnd = random.Random(11)


TILESETS = [a for a in EAS.get_all_level_actors() if isinstance(a, unreal.Cesium3DTileset)]


def trace(start, end, ignore=()):
    # note: the Cesium cut-out only hides the map visually - its collision is still there inside the wall,
    # so inside-the-wall traces ignore the tilesets
    hit = unreal.SystemLibrary.line_trace_single(world, start, end, unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,
                                                 True, list(ignore), unreal.DrawDebugTrace.NONE, True)
    if hit is None:
        return None
    t = hit.to_tuple()
    if not t[0]:
        return None
    a = t[9]
    return (t[4], a.get_actor_label() if a else "", a)


def down(w, ignore=()):
    return trace(unreal.Vector(w.x, w.y, RZ + 30000), unreal.Vector(w.x, w.y, RZ - 5000), ignore)


def clear_above(p, h=900, ignore=()):
    return trace(unreal.Vector(p.x, p.y, p.z + 60), unreal.Vector(p.x, p.y, p.z + h), ignore) is None


def valid(kind, lx, ly):
    w = XF.transform_location(unreal.Vector(lx, ly, 0))
    ign = () if kind == "street_trees" else TILESETS
    h = down(w, ign)
    if not h:
        if kind == "street_trees":
            return None
        h = (unreal.Vector(w.x, w.y, RZ - 4), "Neelam_SiteGround", None)   # open lawn (nothing above it)
    p, lbl, a = h
    if kind == "street_trees":
        if not isinstance(a, unreal.Cesium3DTileset) or abs(p.z - RZ) > 250:
            return None
        for k in range(4):                                  # flat ground around (not a roof edge / wall)
            ang = k * math.pi / 2
            q = down(unreal.Vector(w.x + 300 * math.cos(ang), w.y + 300 * math.sin(ang), 0))
            if not q or abs(q[0].z - p.z) > 150:
                return None
    else:
        if not any(lbl.startswith(s) for s in INSIDE_OK):
            return None
    return p if clear_above(p, ignore=ign) else None


placed, report = {"beech": [], "pine": [], "bush": []}, {}
taken = []
for kind, pts in C.items():
    rnd.shuffle(pts)
    n = 0
    for lx, ly in pts:
        if n >= BUDGET[kind]:
            break
        p = valid(kind, lx, ly)
        if p is None:
            continue
        if any((p.x - q.x) ** 2 + (p.y - q.y) ** 2 < MIN_GAP_CM[kind] ** 2 for q in taken):
            continue
        r, acc = rnd.random(), 0.0
        for sp, w, (s0, s1) in MIX[kind]:
            acc += w
            if r <= acc:
                break
        s = rnd.uniform(s0, s1)
        placed[sp].append(unreal.Transform(unreal.Vector(p.x, p.y, p.z - 10), unreal.Rotator(roll=0.0, pitch=rnd.uniform(-2, 2), yaw=rnd.uniform(0, 360)),
                                           unreal.Vector(s, s, s * rnd.uniform(0.92, 1.08))))
        taken.append(p); n += 1
    report[kind] = {"candidates": len(pts), "placed": n}

holder = EAS.spawn_actor_from_class(unreal.StaticMeshActor, root.get_actor_location(), root.get_actor_rotation())
holder.set_actor_label(LABEL); holder.set_folder_path("Neelam/Vegetation")
sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
lib = unreal.SubobjectDataBlueprintFunctionLibrary
for sp, xfs in placed.items():
    if not xfs:
        continue
    handles = sds.k2_gather_subobject_data_for_instance(holder)
    h, fail = sds.add_new_subobject(unreal.AddNewSubobjectParams(parent_handle=handles[0],
                                    new_class=unreal.HierarchicalInstancedStaticMeshComponent, blueprint_context=None))
    comp = lib.get_object(lib.get_data(h))
    try: sds.rename_subobject(h, "HISM_" + sp)
    except Exception: pass
    comp.set_static_mesh(EAL.load_asset(MESH[sp]))
    comp.add_instances(xfs, False, True)
    comp.set_cull_distances(*CULL[sp])
    comp.set_editor_property("cast_shadow", True)
    report[sp] = len(xfs)
holder.attach_to_actor(root, "", unreal.AttachmentRule.KEEP_WORLD, unreal.AttachmentRule.KEEP_WORLD, unreal.AttachmentRule.KEEP_WORLD, False)
result = report
