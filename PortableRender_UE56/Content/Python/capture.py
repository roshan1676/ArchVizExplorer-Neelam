"""Offscreen camera render with Lumen (works with the editor unfocused). Two bridge jobs, a few seconds apart:
    import capture; capture.start("BL_Camera", "2bhk_cam")     # spawns a live SceneCapture2D on the camera
    capture.tick("2bhk_cam")  x ~30, as separate jobs (Tools/shot.sh does all of this)
    import capture; capture.finish("2bhk_cam")                 # writes Saved/ClaudeBridge/shots/2bhk_cam.png
"""
import unreal, math, os, builtins

OUT = os.path.join(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_saved_dir()), "ClaudeBridge", "shots")
ACT = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
_live = builtins.__dict__.setdefault("_claude_captures", {})

def _world(): return unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()

def start(cam_label, name, w=1920, h=1080):
    os.makedirs(OUT, exist_ok=True)
    cam = next(a for a in ACT.get_all_level_actors() if a.get_actor_label() == cam_label)
    cc = cam.get_cine_camera_component()
    fov = math.degrees(2 * math.atan(cc.get_editor_property("filmback").sensor_width / (2 * cc.get_editor_property("current_focal_length"))))
    rt = unreal.RenderingLibrary.create_render_target2d(_world(), w, h, unreal.TextureRenderTargetFormat.RTF_RGBA8_SRGB)
    cap = ACT.spawn_actor_from_class(unreal.SceneCapture2D, cam.get_actor_location(), cam.get_actor_rotation())
    cap.set_actor_label("_capture_" + name)
    c = cap.capture_component2d
    c.set_editor_property("fov_angle", fov)
    c.set_editor_property("texture_target", rt)
    c.set_editor_property("capture_source", unreal.SceneCaptureSource.SCS_FINAL_TONE_CURVE_HDR)
    c.set_editor_property("always_persist_rendering_state", True)  # Lumen/VSM history lives across frames
    c.set_editor_property("capture_every_frame", False)
    pp = c.get_editor_property("post_process_settings")
    pp.set_editor_property("override_dynamic_global_illumination_method", True)
    pp.set_editor_property("dynamic_global_illumination_method", unreal.DynamicGlobalIlluminationMethod.LUMEN)
    pp.set_editor_property("override_reflection_method", True)
    pp.set_editor_property("reflection_method", unreal.ReflectionMethod.LUMEN)
    c.set_editor_property("post_process_settings", pp)
    c.set_editor_property("post_process_blend_weight", 1.0)
    _live[name] = (cap, rt)
    return "capturing " + name

def tick(name):
    """One capture; call from separate bridge jobs so real frames pass in between (Lumen accumulates)."""
    _live[name][0].capture_component2d.capture_scene()
    return name

def finish(name):
    cap, rt = _live.pop(name)
    unreal.RenderingLibrary.export_render_target(_world(), rt, OUT, name + ".png")
    ACT.destroy_actor(cap)
    return os.path.join(OUT, name + ".png")
