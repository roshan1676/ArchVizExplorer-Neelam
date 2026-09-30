"""Import the per-carriageway FBX files (Blender/build_roads.py ... --split) into /Game/Neelam/Roads/Meshes/rd_*,
replacing the existing meshes in place. Source folder: Saved/NeelamBridge/road_fbx (not in git - rebuild with Blender).
Then run Place_Roads.py -> Place_RoadPoles.py -> Build_Traffic.py -> Fix_Highway_Glow.py (all read road_build.json)."""
import os, glob
import unreal
SRC = os.path.join(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()), "Saved", "NeelamBridge", "road_fbx")
tasks = []
for f in sorted(glob.glob(os.path.join(SRC, "rd_*.fbx"))):
    t = unreal.AssetImportTask(); t.filename = f; t.destination_path = "/Game/Neelam/Roads/Meshes"
    t.destination_name = os.path.splitext(os.path.basename(f))[0]
    t.automated = True; t.replace_existing = True; t.save = True
    ui = unreal.FbxImportUI(); ui.import_mesh = True; ui.import_as_skeletal = False; ui.import_materials = False; ui.import_textures = False
    ui.static_mesh_import_data.combine_meshes = True; ui.static_mesh_import_data.auto_generate_collision = False
    ui.static_mesh_import_data.generate_lightmap_u_vs = False
    t.options = ui; tasks.append(t)
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)
result = {"imported": sum(1 for t in tasks if t.imported_object_paths), "total": len(tasks)}
