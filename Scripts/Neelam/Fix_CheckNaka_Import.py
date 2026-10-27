"""UE side of Fix_CheckNaka_Road.py: re-import the 3 Check Naka carriageways over /Game/Neelam/Roads/Meshes/rd_* (the
level actors keep their placement - vertices are absolute) and rebuild their RoadCut_* map cut-outs (same ring logic
as Place_Roads.py). Bridge job; saves the level."""
import os, json, math
import unreal
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
PROJ = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
SRC = os.path.join(PROJ, "Saved", "NeelamBridge", "road_fbx_checknaka")
B = json.load(open(os.path.join(PROJ, "Scripts", "Neelam", "Data", "road_checknaka.json")))["roads"]
tasks = []
for k in B:
    t = unreal.AssetImportTask(); t.filename = os.path.join(SRC, k + ".fbx"); t.destination_path = "/Game/Neelam/Roads/Meshes"
    t.destination_name = k; t.automated = True; t.replace_existing = True; t.save = True
    ui = unreal.FbxImportUI(); ui.import_mesh = True; ui.import_as_skeletal = False; ui.import_materials = False; ui.import_textures = False
    ui.static_mesh_import_data.combine_meshes = True; ui.static_mesh_import_data.auto_generate_collision = False
    ui.static_mesh_import_data.generate_lightmap_u_vs = False
    t.options = ui; tasks.append(t)
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)
M = {n: unreal.load_asset("/Game/Neelam/Roads/Materials/" + n) or unreal.load_asset("/Game/Neelam/Roads/" + n) for n in ("MI_Road_Asphalt", "MI_Road_Kerb", "MI_Road_Marking")}
for k in B:   # re-import resets slots -> same assignment as Place_Roads.py
    sm = unreal.load_asset("/Game/Neelam/Roads/Meshes/" + k)
    for i, s in enumerate(sm.static_materials):
        nm = str(s.material_slot_name)
        m = M["MI_Road_Asphalt"] if "Asphalt" in nm else M["MI_Road_Kerb"] if "Kerb" in nm else M["MI_Road_Marking"]
        if m: sm.set_material(i, m)
    unreal.EditorAssetLibrary.save_asset(sm.get_path_name())
cuts = 0
for a in EAS.get_all_level_actors():
    k = "rd_" + a.get_actor_label()[len("RoadCut_"):] if a.get_actor_label().startswith("RoadCut_") else None
    if k not in B: continue
    pts = B[k]["pts"]; half = B[k]["width_m"] * 50 + 20
    idx = list(range(0, len(pts), 4)) + ([len(pts) - 1] if (len(pts) - 1) % 4 else [])
    L, R = [], []
    for i in idx:
        p, q = pts[max(i - 1, 0)], pts[min(i + 1, len(pts) - 1)]
        dx, dy = q[0] - p[0], q[1] - p[1]; l = math.hypot(dx, dy) or 1.0; nx, ny = -dy / l, dx / l
        L.append(unreal.Vector(pts[i][0] + nx * half, pts[i][1] + ny * half, pts[i][2])); R.append(unreal.Vector(pts[i][0] - nx * half, pts[i][1] - ny * half, pts[i][2]))
    a.modify(); spl = a.get_component_by_class(unreal.SplineComponent); spl.clear_spline_points(False)
    for v in L + R[::-1]: spl.add_spline_point(v, unreal.SplineCoordinateSpace.WORLD, False)
    for q in range(spl.get_number_of_spline_points()): spl.set_spline_point_type(q, unreal.SplinePointType.LINEAR, False)
    spl.set_closed_loop(True, True); cuts += 1
tiles = next((t for t in EAS.get_all_level_actors() if t.get_actor_label() == "Google Photorealistic 3D Tiles"), None)
try: tiles.refresh_tileset()
except Exception: pass
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
result = {"imported": sum(1 for t in tasks if t.imported_object_paths), "cuts": cuts, "mats": [n for n, m in M.items() if m]}
