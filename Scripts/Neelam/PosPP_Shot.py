"""PIE: nadir position-encoded screenshots with Neelam_AlignCam + M_Neelam_PosPP (see Make_PosPP.py).
Globals: NAME, CX, CY, H (camera), AXES e.g. "xyz", SCALE (cm range), MODE 'go' (move + keep) / 'shot' (one axis per call)."""
import unreal, json, os
gw = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
pc = unreal.GameplayStatics.get_player_controller(gw, 0)
cam = next(a for a in unreal.GameplayStatics.get_all_actors_of_class(gw, unreal.CameraActor) if a.get_actor_label() == "Neelam_AlignCam")
cc = cam.camera_component
if MODE == "go":
    cam.set_actor_location_and_rotation(unreal.Vector(CX, CY, H), unreal.Rotator(roll=0.0, pitch=-90.0, yaw=0.0), False, True)
    cc.set_editor_property("field_of_view", 90.0); pc.set_view_target_with_blend(cam, 0.0)
    pps = cc.get_editor_property("post_process_settings"); pps.weighted_blendables = unreal.WeightedBlendables([]); cc.set_editor_property("post_process_settings", pps)
    result = 1
elif MODE == "shot":
    if "pp_mid" not in env or env.get("pp_world") != gw.get_path_name():
        env["pp_mid"] = unreal.MaterialLibrary.create_dynamic_material_instance(gw, unreal.load_asset("/Game/Neelam/Massing/M_Neelam_PosPP"))
        env["pp_world"] = gw.get_path_name()
    mid = env["pp_mid"]
    ax = {"x": (1, 0, 0), "y": (0, 1, 0), "z": (0, 0, 1), "none": None}[AXIS]
    pps = cc.get_editor_property("post_process_settings")
    if ax is None:
        pps.weighted_blendables = unreal.WeightedBlendables([])
    else:
        mid.set_vector_parameter_value("Origin", unreal.LinearColor(CX, CY, ZO, 0)); mid.set_vector_parameter_value("Axis", unreal.LinearColor(ax[0], ax[1], ax[2], 0))
        mid.set_scalar_parameter_value("Scale", SCALE)
        pps.weighted_blendables = unreal.WeightedBlendables([unreal.WeightedBlendable(1.0, mid)])
    pps.set_editor_property("override_motion_blur_amount", True); pps.set_editor_property("motion_blur_amount", 0.0)
    cc.set_editor_property("post_process_settings", pps); cc.set_editor_property("post_process_blend_weight", 1.0)
    unreal.SystemLibrary.execute_console_command(gw, "r.AntiAliasingMethod 0")
    unreal.SystemLibrary.execute_console_command(gw, "HighResShot 1600x900 filename=%s_%s" % (NAME, AXIS))
    result = [NAME, AXIS]
