"""Grey context massing into the level (30 Sep): imports Saved/NeelamBridge/massing_fbx/massing_*.fbx
(Blender/build_massing.py) -> /Game/Neelam/Massing/Meshes, one untextured matte grey material, one actor per 500 m chunk
at the origin (absolute vertices), folder Neelam/Massing, tag Neelam_Massing, no collision. Re-run safe."""
import os, glob
import unreal
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem); EAL = unreal.EditorAssetLibrary; mel = unreal.MaterialEditingLibrary
SRC = os.path.join(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_saved_dir()), "NeelamBridge", "massing_fbx")
MP = "/Game/Neelam/Massing/M_Neelam_Massing"
m = unreal.load_asset(MP)
if m is None:
    m = unreal.AssetToolsHelpers.get_asset_tools().create_asset("M_Neelam_Massing", "/Game/Neelam/Massing", unreal.Material, unreal.MaterialFactoryNew())
    c = mel.create_material_expression(m, unreal.MaterialExpressionVectorParameter, -400, 0); c.set_editor_property("parameter_name", "Color")
    c.set_editor_property("default_value", unreal.LinearColor(0.42, 0.42, 0.43, 1))
    r = mel.create_material_expression(m, unreal.MaterialExpressionScalarParameter, -400, 200); r.set_editor_property("parameter_name", "Roughness"); r.set_editor_property("default_value", 0.9)
    s = mel.create_material_expression(m, unreal.MaterialExpressionConstant, -400, 300); s.set_editor_property("r", 0.25)
    mel.connect_material_property(c, "", unreal.MaterialProperty.MP_BASE_COLOR)
    mel.connect_material_property(r, "", unreal.MaterialProperty.MP_ROUGHNESS)
    mel.connect_material_property(s, "", unreal.MaterialProperty.MP_SPECULAR)
    mel.recompile_material(m); EAL.save_asset(MP)
MI = unreal.load_asset("/Game/Neelam/Massing/MI_Neelam_Massing_Grey") or m     # mid grey 0.2 (parent default 0.42 reads as white)
for a in [a for a in EAS.get_all_level_actors() if str(a.get_folder_path()).startswith("Neelam/Massing")]: EAS.destroy_actor(a)
tasks = []
import json
_D = os.path.join(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()), "Scripts", "Neelam", "Data")
_TX = set(json.load(open(os.path.join(_D, "massing_textured.json")))) if os.path.exists(os.path.join(_D, "massing_textured.json")) else set()
KEEP = {"massing_" + b["chunk"] for b in json.load(open(os.path.join(_D, "massing_build.json"))) if b["id"] not in _TX}   # textured ones: Build_Facades.py
for f in sorted(glob.glob(os.path.join(SRC, "massing_*.fbx"))):
    if os.path.splitext(os.path.basename(f))[0] not in KEEP: continue      # stale chunk (emptied by make_massing filters)
    t = unreal.AssetImportTask(); t.filename = f; t.destination_path = "/Game/Neelam/Massing/Meshes"; t.destination_name = os.path.splitext(os.path.basename(f))[0]
    t.automated = True; t.replace_existing = True; t.save = True
    ui = unreal.FbxImportUI(); ui.import_mesh = True; ui.import_as_skeletal = False; ui.import_materials = False; ui.import_textures = False
    ui.static_mesh_import_data.combine_meshes = True; ui.static_mesh_import_data.auto_generate_collision = False; ui.static_mesh_import_data.generate_lightmap_u_vs = False
    t.options = ui; tasks.append(t)
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)
n = 0; tris = 0
for t in tasks:
    sm = unreal.load_asset("/Game/Neelam/Massing/Meshes/" + t.destination_name)
    if sm is None: continue
    for i in range(len(sm.static_materials)): sm.set_material(i, MI)
    EAL.save_asset(sm.get_path_name()); tris += sm.get_num_triangles(0)
    a = EAS.spawn_actor_from_object(sm, unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0))
    a.set_actor_label("Massing_" + t.destination_name[8:]); a.set_folder_path("Neelam/Massing"); a.tags = [unreal.Name("Neelam_Massing")]
    c = a.static_mesh_component; c.set_collision_profile_name("NoCollision"); c.set_editor_property("cast_shadow", True); n += 1
unreal.EditorLevelLibrary.save_current_level()
result = {"chunks": n, "triangles": tris}
