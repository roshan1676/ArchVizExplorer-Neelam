"""Clean continuous parapet round the AB podium roof (30 Sep, after Clean_PodiumAB_Parapet.py removed the broken stubs).
Blender/build_podium_ab_parapet.py: 27 cm wall, 1.04 m + 8 cm coping, on the deck's outer edge; deck transform."""
import os
import unreal
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem); EAL = unreal.EditorAssetLibrary
F = os.path.join(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_saved_dir()), "NeelamBridge", "SM_Podium_AB_Parapet.fbx")
DST = "/Game/Neelam/Buildings/WindTunnel/Meshes/Podium"
t = unreal.AssetImportTask(); t.filename = F; t.destination_path = DST; t.destination_name = "SM_Podium_AB_Parapet"
t.automated = True; t.replace_existing = True; t.save = True
ui = unreal.FbxImportUI(); ui.import_mesh = True; ui.import_as_skeletal = False; ui.import_materials = False; ui.import_textures = False
ui.static_mesh_import_data.combine_meshes = True; ui.static_mesh_import_data.auto_generate_collision = False
t.options = ui; unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t])
sm = unreal.load_asset(DST + "/SM_Podium_AB_Parapet")
I = "/Game/Neelam/Buildings/WindTunnel/Materials/Instances/"
for i, s in enumerate(sm.static_materials):
    sm.set_material(i, unreal.load_asset(I + ("MI_Kerb_Concrete" if "Kerb" in str(s.material_slot_name) else "MI_Paint_White_Trim")))
EAL.save_asset(sm.get_path_name())
A = {a.get_actor_label(): a for a in EAS.get_all_level_actors()}
if "SM_Podium_AB_Parapet" in A: EAS.destroy_actor(A["SM_Podium_AB_Parapet"])
deck = A["SM_Podium_Deck_AB_Top"]
a = EAS.spawn_actor_from_object(sm, deck.get_actor_location(), deck.get_actor_rotation())
a.set_actor_label("SM_Podium_AB_Parapet"); a.set_folder_path("Neelam/WindTunnel/Podium")
a.attach_to_actor(A["Neelam_WindTunnel_Root"], "", unreal.AttachmentRule.KEEP_WORLD, unreal.AttachmentRule.KEEP_WORLD, unreal.AttachmentRule.KEEP_WORLD, False)
unreal.EditorLevelLibrary.save_current_level()
result = [str(s.material_slot_name) for s in sm.static_materials]
