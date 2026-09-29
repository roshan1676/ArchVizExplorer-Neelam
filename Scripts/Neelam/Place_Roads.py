"""Place the Blender-built road meshes (/Game/Neelam/Roads/Meshes, absolute world vertices -> actors at origin),
assign asphalt / kerb / marking materials and cut the Google tiles under every carriageway (CesiumCartographicPolygon
added to the tileset's CesiumPolygonRasterOverlay). Re-running replaces the Neelam/Roads folder and road cut polygons."""
import json, os, math
import unreal
P = os.path.join(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()), "Scripts", "Neelam")
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem); EAL = unreal.EditorAssetLibrary; mel = unreal.MaterialEditingLibrary
B = json.load(open(os.path.join(P, "Data", "road_build.json")))["roads"]
FOLDER, CUTF = "Neelam/Roads", "Neelam/Roads/Cutouts"
for a in [a for a in EAS.get_all_level_actors() if str(a.get_folder_path()).startswith(FOLDER)]:
    EAS.destroy_actor(a)
I = "/Game/Neelam/Buildings/WindTunnel/Materials/Instances/"
def mi(name, parent, scal, vec=None):
    p = "/Game/Neelam/Roads/Materials/" + name
    m = unreal.load_asset(p)
    if m is None:
        m = unreal.AssetToolsHelpers.get_asset_tools().create_asset(name, "/Game/Neelam/Roads/Materials", unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
        m.set_editor_property("parent", unreal.load_asset(I + parent))
    for k, v in scal.items(): mel.set_material_instance_scalar_parameter_value(m, k, v)
    if vec: mel.set_material_instance_vector_parameter_value(m, "Tint", unreal.LinearColor(*vec))
    mel.update_material_instance(m); EAL.save_asset(p); return m
M_ASPH = mi("MI_Road_Asphalt", "MI_Asphalt", {"Tiling": 0.25, "Roughness": 0.75, "DetailContrast": 0.8, "MacroVariation": 0.3}, (0.22, 0.22, 0.23, 1))
M_KERB = mi("MI_Road_Kerb", "MI_Kerb_Concrete", {"Tiling": 1.0}, (0.62, 0.61, 0.58, 1))
M_MARK = mi("MI_Road_Marking", "MI_Court_Lines_White", {"Roughness": 0.5}, (0.85, 0.85, 0.82, 1))
n = 0
for k in B:
    sm = unreal.load_asset("/Game/Neelam/Roads/Meshes/" + k)
    if sm is None: continue
    for i, s in enumerate(sm.static_materials):
        nm = str(s.material_slot_name)
        sm.set_material(i, M_ASPH if "Asphalt" in nm else M_KERB if "Kerb" in nm else M_MARK)
    EAL.save_asset(sm.get_path_name())
    a = EAS.spawn_actor_from_object(sm, unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0))
    a.set_actor_label("Road_" + B[k]["group"] + "_" + k[3:]); a.set_folder_path(FOLDER)
    c = a.static_mesh_component; c.set_collision_profile_name("NoCollision"); c.set_editor_property("cast_shadow", True)
    a.tags = [unreal.Name("Neelam_Road")]; n += 1
# ---- cut the map under each carriageway (just inside the kerbs; kerb + skirt hide the seam)
tiles = next(t for t in EAS.get_all_level_actors() if t.get_actor_label() == "Google Photorealistic 3D Tiles")
ov = next(c for c in tiles.get_components_by_class(unreal.ActorComponent) if c.get_class().get_name() == "CesiumPolygonRasterOverlay")
polys = [p for p in ov.get_editor_property("polygons") if p and not str(p.get_actor_label()).startswith("RoadCut_")]
for k, r in B.items():
    pts = r["pts"]; half = r["width_m"] * 50 + 20
    idx = list(range(0, len(pts), 4)) + ([len(pts) - 1] if (len(pts) - 1) % 4 else [])
    L, R = [], []
    for i in idx:
        a_, b_ = pts[max(i - 1, 0)], pts[min(i + 1, len(pts) - 1)]
        dx, dy = b_[0] - a_[0], b_[1] - a_[1]; l = math.hypot(dx, dy) or 1.0; nx, ny = -dy / l, dx / l
        L.append(unreal.Vector(pts[i][0] + nx * half, pts[i][1] + ny * half, pts[i][2])); R.append(unreal.Vector(pts[i][0] - nx * half, pts[i][1] - ny * half, pts[i][2]))
    ring = L + R[::-1]
    cp = EAS.spawn_actor_from_class(unreal.CesiumCartographicPolygon, ring[0])
    cp.set_actor_label("RoadCut_" + k[3:]); cp.set_folder_path(CUTF)
    spl = cp.get_component_by_class(unreal.SplineComponent); spl.clear_spline_points(False)
    for v in ring: spl.add_spline_point(v, unreal.SplineCoordinateSpace.WORLD, False)
    for q in range(spl.get_number_of_spline_points()): spl.set_spline_point_type(q, unreal.SplinePointType.LINEAR, False)
    spl.set_closed_loop(True, True); polys.append(cp)
ov.set_editor_property("polygons", polys)
try: tiles.refresh_tileset()
except Exception: pass
result = {"road_actors": n, "cut_polygons": len(polys)}
