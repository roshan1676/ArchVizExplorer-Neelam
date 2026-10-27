"""Hand-placed cine cameras.  import cams; cams.make("LUX_Cam_Living", eye=(x,y,z), target=(x,y,z), focal=24)"""
import unreal
ACT = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

def make(label, eye, target, focal=24.0, aperture=8.0, ev_bias=None):
    a = next((x for x in ACT.get_all_level_actors() if x.get_actor_label() == label), None) or \
        ACT.spawn_actor_from_class(unreal.CineCameraActor, unreal.Vector(*eye))
    e, t = unreal.Vector(*eye), unreal.Vector(*target)
    a.set_actor_location(e, False, False)
    a.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(e, t), False)
    cc = a.get_cine_camera_component()
    fb = cc.get_editor_property("filmback"); fb.sensor_width = 36.0; fb.sensor_height = 20.25
    cc.set_editor_property("filmback", fb); cc.set_editor_property("current_focal_length", focal)
    cc.set_editor_property("current_aperture", aperture)
    fs = cc.get_editor_property("focus_settings"); fs.focus_method = unreal.CameraFocusMethod.DISABLE
    cc.set_editor_property("focus_settings", fs)
    if ev_bias is not None:
        pp = cc.get_editor_property("post_process_settings")
        pp.set_editor_property("override_auto_exposure_bias", True); pp.set_editor_property("auto_exposure_bias", ev_bias)
        cc.set_editor_property("post_process_settings", pp); cc.set_editor_property("post_process_blend_weight", 1.0)
    a.set_actor_label(label); a.tags = ["lux_cam"]; a.set_folder_path("Lux/Cameras")
    return a
