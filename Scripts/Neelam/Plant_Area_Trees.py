"""Neelam - trees across the whole surrounding area, where the map shows tree canopy.
Points: Data/area_tree_points.json (from a top-down base-colour capture, green-canopy detection).
Each point: trace canopy top + 6 ground samples (7 m ring) -> ground height and canopy height;
rejects roofs (> 30 m) and the Neelam site itself. One actor 'Neelam_Vegetation_Area' with HISM
per species (instanced, LOD + distance culling). Re-runnable."""
import json, math, os, random, unreal

LABEL = "Neelam_Vegetation_Area"
MESH = {"beech": "/Game/ArchVizExplorer/Environment/Foliage/SM_Tree_Beech_01",
        "pine": "/Game/ArchVizExplorer/Environment/Foliage/SM_Tree_Pine_01",
        "bush": "/Game/ArchVizExplorer/Environment/Foliage/SM_Bush_01"}
HEIGHT = {"beech": 2500.0, "pine": 1040.0, "bush": 290.0}
CULL = {"beech": (200000, 300000), "pine": (150000, 220000), "bush": (40000, 60000)}
SINK = 80.0
PROJECT = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
PTS = json.load(open(os.path.join(PROJECT, "Scripts", "Neelam", "Data", "area_tree_points.json")))["points"]
CUT = json.load(open(os.path.join(PROJECT, "Scripts", "Neelam", "Data", "site_outline.json")))["platform_ring"]
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
EAL = unreal.EditorAssetLibrary
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
by_label = lambda l: next((a for a in EAS.get_all_level_actors() if a.get_actor_label() == l), None)
root = by_label("Neelam_WindTunnel_Root")
XF = root.get_actor_transform(); RZ = root.get_actor_location().z
old = by_label(LABEL)
if old: EAS.destroy_actor(old)
IGN = [root] + list(root.get_attached_actors())
rnd = random.Random(5)


def inside_site(lx, ly, margin=1500.0):
    xs = [p[0] for p in CUT]; ys = [p[1] for p in CUT]
    if not (min(xs) - margin < lx < max(xs) + margin and min(ys) - margin < ly < max(ys) + margin):
        return False
    return True                                         # near/inside the site: already planted by hand


def z_at(x, y):
    hit = unreal.SystemLibrary.line_trace_single(world, unreal.Vector(x, y, RZ + 80000), unreal.Vector(x, y, RZ - 20000),
                                                 unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, IGN, unreal.DrawDebugTrace.NONE, True)
    if hit is None: return None
    t = hit.to_tuple()
    return float(t[4].z) if t[0] else None


xfs = {"beech": [], "pine": [], "bush": []}
stats = {"points": len(PTS), "site": 0, "nohit": 0, "roof": 0}
for x, y, f in PTS:
    lp = XF.inverse_transform_location(unreal.Vector(x, y, RZ))
    if inside_site(lp.x, lp.y):
        stats["site"] += 1; continue
    top = z_at(x, y)
    if top is None:
        stats["nohit"] += 1; continue
    ring = [z_at(x + 700 * math.cos(k * math.pi / 3), y + 700 * math.sin(k * math.pi / 3)) for k in range(6)]
    ring = [z for z in ring if z is not None]
    if len(ring) < 3:
        stats["nohit"] += 1; continue
    ground = min(ring + [top])
    h = top - ground
    if h > 3000:
        stats["roof"] += 1; continue
    # map tiles at this distance are too smooth to measure canopy height -> natural size mix
    r = rnd.random()
    if r < 0.12:
        sp, target = "bush", rnd.uniform(200, 330)
    elif r < 0.25:
        sp, target = "pine", rnd.uniform(800, 1250)
    else:
        sp, target = "beech", rnd.uniform(800, 1500) if f < 0.8 else rnd.uniform(1100, 1700)
    s = target / HEIGHT[sp]
    xfs[sp].append(unreal.Transform(unreal.Vector(x, y, ground - SINK),
                                    unreal.Rotator(roll=0.0, pitch=rnd.uniform(-2, 2), yaw=rnd.uniform(0, 360)),
                                    unreal.Vector(s, s, s * rnd.uniform(0.9, 1.1))))

holder = EAS.spawn_actor_from_class(unreal.StaticMeshActor, root.get_actor_location(), root.get_actor_rotation())
holder.set_actor_label(LABEL); holder.set_folder_path("Neelam/Vegetation")
sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
lib = unreal.SubobjectDataBlueprintFunctionLibrary
for sp, lst in xfs.items():
    if not lst: continue
    handles = sds.k2_gather_subobject_data_for_instance(holder)
    h, fail = sds.add_new_subobject(unreal.AddNewSubobjectParams(parent_handle=handles[0],
                                    new_class=unreal.HierarchicalInstancedStaticMeshComponent, blueprint_context=None))
    comp = lib.get_object(lib.get_data(h))
    try: sds.rename_subobject(h, "HISM_Area_" + sp)
    except Exception: pass
    comp.set_static_mesh(EAL.load_asset(MESH[sp]))
    comp.add_instances(lst, False, True)
    comp.set_cull_distances(*CULL[sp])
    comp.set_collision_profile_name("NoCollision")      # optimisation: no physics for background trees
    stats[sp] = len(lst)
result = stats
