"""Real-site 360 backdrops for the Room_render amenity panoramas (run in PIE through the bridge).
Captures 6 cube faces (F R B L U D, 92 deg, Room_render's stitch_pano.py layout) from a CameraActor at a world
position, with the amenity deck dressing + pins hidden, so only the real towers / podium / Mulund city remain.
    setup(name, x, y, z)   # hide amenity actors, park the view there (Cesium streams around the view) -> wait ~40 s
    capture(name)          # -> Saved/Backdrops/<name>/{F,R,B,L,U,D}.png
"""
import os
import unreal

OUT = os.path.join(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_saved_dir()), "Backdrops")
FACES = (("F", 0, 0), ("R", 90, 0), ("B", 180, 0), ("L", 270, 0), ("U", 0, 90), ("D", 0, -90))
_st = {}


def _world():
    return unreal.EditorLevelLibrary.get_game_world()


CAP_LABEL = "_BG_Cap"


def prepare_editor():
    """EDITOR (not PIE): Python cannot spawn into a PIE world, so drop the capture actor in the editor level first
    (PIE copies it). Not saved - remove with cleanup_editor()."""
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    if not [a for a in eas.get_all_level_actors() if a.get_actor_label() == CAP_LABEL]:
        c = eas.spawn_actor_from_class(unreal.SceneCapture2D, unreal.Vector(0, 0, 0)); c.set_actor_label(CAP_LABEL)
    return [a.get_actor_label() for a in eas.get_all_level_actors() if a.get_actor_label() in (CAP_LABEL, "Neelam_AlignCam")]


def cleanup_editor():
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for a in eas.get_all_level_actors():
        if a.get_actor_label() == CAP_LABEL: eas.destroy_actor(a)


def _find(w, label):
    for a in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.Actor):
        if a.get_actor_label() == label: return a


def _amenity_dressing(a):
    s = (a.get_actor_label() + " " + str(a.get_folder_path()) + " " + " ".join(str(t) for t in a.tags)).lower()
    return "amenit" in s


def setup(name, x, y, z):
    w = _world()
    hidden = 0
    for a in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.Actor):
        if _amenity_dressing(a):
            a.set_actor_hidden_in_game(True); hidden += 1
    cam = _find(w, "Neelam_AlignCam")
    cam.set_actor_rotation(unreal.Rotator(roll=0, pitch=0, yaw=0), False)
    cam.set_actor_location(unreal.Vector(x, y, z), False, False)
    unreal.GameplayStatics.get_player_controller(w, 0).set_view_target_with_blend(cam, 0.0)
    _st["loc"] = unreal.Vector(x, y, z)
    return {"hidden": hidden, "at": [x, y, z]}


def arm(name, size=2048, bias=-13.0):
    """capture component renders every frame (export in a LATER bridge call - same-call exports read a stale target)"""
    w = _world()
    cap = _find(w, CAP_LABEL); cap.set_actor_location(_st["loc"], False, False)
    comp = cap.capture_component2d
    rt = unreal.RenderingLibrary.create_render_target2d(w, size, size, unreal.TextureRenderTargetFormat.RTF_RGBA8_SRGB)
    comp.set_editor_property("texture_target", rt)
    comp.set_editor_property("capture_source", unreal.SceneCaptureSource.SCS_FINAL_TONE_CURVE_HDR)
    comp.set_editor_property("capture_every_frame", True)
    comp.set_editor_property("always_persist_rendering_state", True)
    comp.set_editor_property("fov_angle", 92.0)
    pp = comp.get_editor_property("post_process_settings")
    for k, v in (("override_auto_exposure_method", True), ("auto_exposure_method", unreal.AutoExposureMethod.AEM_MANUAL),
                 ("override_auto_exposure_apply_physical_camera_exposure", True), ("auto_exposure_apply_physical_camera_exposure", False),
                 ("override_auto_exposure_bias", True), ("auto_exposure_bias", bias),
                 ("override_motion_blur_amount", True), ("motion_blur_amount", 0.0)):
        try: pp.set_editor_property(k, v)
        except Exception: pass
    comp.set_editor_property("post_process_settings", pp)
    comp.set_editor_property("post_process_blend_weight", 1.0)
    _st.update(cap=cap, rt=rt, name=name)
    return str(rt)


def face(tag):
    yaw, pitch = {f[0]: (f[1], f[2]) for f in FACES}[tag]
    _st["cap"].set_actor_rotation(unreal.Rotator(roll=0, pitch=pitch, yaw=yaw), False)
    return tag


def export(tag):
    d = os.path.join(OUT, _st["name"]); os.makedirs(d, exist_ok=True)
    unreal.RenderingLibrary.export_render_target(_world(), _st["rt"], d, tag + ".png")
    return os.path.join(d, tag + ".png")
