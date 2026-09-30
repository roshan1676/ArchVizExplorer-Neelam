"""Close the AB podium roof after Towers A/B were removed (30 Sep): the deck mesh has cut-outs where the towers stood.
SM_Podium_Deck_AB_Fill (Blender/build_deck_ab_fill.py: 69.5 x 55.2 m slab, 38 cm thick, top 1.5 cm under the deck,
same UV scale/offset as the deck so the paving continues) placed with the deck's transform, MI_Paving_Deck."""
import os
import unreal
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem); EAL = unreal.EditorAssetLibrary
F = os.path.join(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_saved_dir()), "NeelamBridge", "SM_Podium_Deck_AB_Fill.fbx")
DST = "/Game/Neelam/Buildings/WindTunnel/Meshes/Podium"
t = unreal.AssetImportTask(); t.filename = F; t.destination_path = DST; t.destination_name = "SM_Podium_Deck_AB_Fill"
t.automated = True; t.replace_existing = True; t.save = True
ui = unreal.FbxImportUI(); ui.import_mesh = True; ui.import_as_skeletal = False; ui.import_materials = False; ui.import_textures = False
ui.static_mesh_import_data.combine_meshes = True; ui.static_mesh_import_data.auto_generate_collision = False
t.options = ui; unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t])
sm = unreal.load_asset(DST + "/SM_Podium_Deck_AB_Fill")
mat = unreal.load_asset("/Game/Neelam/Buildings/WindTunnel/Materials/Instances/MI_Paving_Deck")
for i in range(len(sm.static_materials)): sm.set_material(i, mat)
EAL.save_asset(sm.get_path_name())
acts = {a.get_actor_label(): a for a in EAS.get_all_level_actors()}
if "SM_Podium_Deck_AB_Fill" in acts: EAS.destroy_actor(acts["SM_Podium_Deck_AB_Fill"])
deck = acts["SM_Podium_Deck_AB_Top"]
a = EAS.spawn_actor_from_object(sm, deck.get_actor_location(), deck.get_actor_rotation())
a.set_actor_label("SM_Podium_Deck_AB_Fill"); a.set_folder_path("Neelam/WindTunnel/Podium")
a.attach_to_actor(acts["Neelam_WindTunnel_Root"], "", unreal.AttachmentRule.KEEP_WORLD, unreal.AttachmentRule.KEEP_WORLD, unreal.AttachmentRule.KEEP_WORLD, False)
unreal.EditorLevelLibrary.save_current_level()
o, e = a.get_actor_bounds(False)
result = [str(o), str(e), sm.get_num_triangles(0)]
