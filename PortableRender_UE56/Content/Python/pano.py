"""360 panoramas = 6 cube faces (92 deg, a little overlap so the stitcher never samples outside a face) at eye height.
    import pano as P
    P.SPOTS["3BHK"]["01_Living"] = (x, y)               # spots are defined in pano_spots.py
    P.preview_start("3BHK_01_Living", x, y)            # Lumen preview faces (editor can be in the background) ...
    P.preview_tick("3BHK_01_Living") x N, P.preview_finish(...)  -> Saved/Pano/preview/<name>/<F|R|B|L|U|D>.png
    P.make_rig(unit)                                    # cine cameras PANO_<spot>_<face> + SEQ_PANO_<spot> (6 camera cuts)
Final faces come from Movie Render Queue path tracer (mrq_render.render_panos) -> Saved/Pano/faces/<unit>_<spot>/<frame>.png;
Tools/stitch_pano.py turns them into 16K / 8K equirectangular JPGs."""
import unreal, os, math, builtins

EYE_Z = 163.0                     # eye level of a 5'7" (5.7 ft) person, cm
FOV = 92.0                        # per face; stitcher uses the same value
FACES = (("F", 0, 0), ("R", 90, 0), ("B", 180, 0), ("L", 270, 0), ("U", 0, 90), ("D", 0, -90))
OUT = os.path.join(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_saved_dir()), "Pano")
ACT = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
_live = builtins.__dict__.setdefault("_claude_pano", {})

def _world(): return unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
def _rot(yaw, pitch): return unreal.Rotator(roll=0, pitch=pitch, yaw=yaw)

# ---------- quick Lumen previews ----------
def preview_start(name, x, y, z=EYE_Z, size=768):
    caps = []
    for tag, yaw, pitch in FACES:
        rt = unreal.RenderingLibrary.create_render_target2d(_world(), size, size, unreal.TextureRenderTargetFormat.RTF_RGBA8_SRGB)
        cap = ACT.spawn_actor_from_class(unreal.SceneCapture2D, unreal.Vector(x, y, z), _rot(yaw, pitch))
        c = cap.capture_component2d
        c.set_editor_property("fov_angle", FOV); c.set_editor_property("texture_target", rt)
        c.set_editor_property("capture_source", unreal.SceneCaptureSource.SCS_FINAL_TONE_CURVE_HDR)
        c.set_editor_property("always_persist_rendering_state", True); c.set_editor_property("capture_every_frame", False)
        pp = c.get_editor_property("post_process_settings")
        pp.set_editor_property("override_dynamic_global_illumination_method", True)
        pp.set_editor_property("dynamic_global_illumination_method", unreal.DynamicGlobalIlluminationMethod.LUMEN)
        pp.set_editor_property("override_reflection_method", True); pp.set_editor_property("reflection_method", unreal.ReflectionMethod.LUMEN)
        c.set_editor_property("post_process_settings", pp); c.set_editor_property("post_process_blend_weight", 1.0)
        caps.append((tag, cap, rt))
    _live[name] = caps
    return name

def preview_tick(name):
    for _, cap, _ in _live[name]: cap.capture_component2d.capture_scene()
    return name

def preview_finish(name):
    d = os.path.join(OUT, "preview", name); os.makedirs(d, exist_ok=True)
    for tag, cap, rt in _live.pop(name):
        unreal.RenderingLibrary.export_render_target(_world(), rt, d, tag + ".png"); ACT.destroy_actor(cap)
    return d

# ---------- final rig ----------
def make_rig(unit, spots):
    """spots: {spot_name: (x, y)}. One cine camera per face + one-frame-per-face sequence."""
    EAL = unreal.EditorAssetLibrary; AT = unreal.AssetToolsHelpers.get_asset_tools()
    for a in ACT.get_all_level_actors():
        if "pano_cam" in [str(t) for t in a.tags]: ACT.destroy_actor(a)
    folder = "/Game/Neelam/%s/Pano" % unit; made = []
    for spot, (x, y) in spots.items():
        cams = []
        for tag, yaw, pitch in FACES:
            cam = ACT.spawn_actor_from_class(unreal.CineCameraActor, unreal.Vector(x, y, EYE_Z), _rot(yaw, pitch))
            cc = cam.get_cine_camera_component()
            fb = cc.get_editor_property("filmback"); fb.sensor_width = 36.0; fb.sensor_height = 36.0
            cc.set_editor_property("filmback", fb)
            cc.set_editor_property("current_focal_length", 18.0 / math.tan(math.radians(FOV / 2)))
            fs = cc.get_editor_property("focus_settings"); fs.focus_method = unreal.CameraFocusMethod.DISABLE
            cc.set_editor_property("focus_settings", fs); cc.set_editor_property("current_aperture", 22.0)
            cam.set_actor_label("PANO_%s_%s" % (spot, tag)); cam.tags = ["pano_cam"]; cam.set_folder_path("Pano/" + spot)
            cams.append(cam)
        sname = "SEQ_PANO_" + spot
        if EAL.does_asset_exist(folder + "/" + sname): EAL.delete_asset(folder + "/" + sname)
        seq = AT.create_asset(sname, folder, unreal.LevelSequence, unreal.LevelSequenceFactoryNew())
        seq.set_display_rate(unreal.FrameRate(24, 1)); seq.set_playback_start(0); seq.set_playback_end(len(cams))
        track = seq.add_track(unreal.MovieSceneCameraCutTrack)
        for i, cam in enumerate(cams):
            b = seq.add_possessable(cam)
            s = track.add_section(); s.set_range(i, i + 1); s.set_camera_binding_id(seq.get_binding_id(b))
        EAL.save_loaded_asset(seq); made.append(sname)
    return made
