"""NeelamBridge - lets Claude work live in this editor session.

Starts automatically with the editor (Content/Python/init_unreal.py) or manually:
    py "C:/Users/Admin/Documents/Unreal Projects/ArchVizExplorer-Neelam/Scripts/Neelam/NeelamBridge.py"

How it works (editor only, local files only, nothing leaves the PC):
  * Claude drops  Saved/NeelamBridge/inbox/<job>.py
  * every ~0.25 s the editor runs it (inside one Undo transaction) and writes
    Saved/NeelamBridge/outbox/<job>.json  {ok, stdout, error, result, seconds}
  * jobs can queue viewport screenshots with  shot(name, location, rotation, settle_s)
    -> Saved/NeelamBridge/outbox/shots/<name>.png   (+ <name>.json when done)
  * heartbeat: Saved/NeelamBridge/outbox/heartbeat.json every 2 s
To stop: run  unreal.neelam_bridge_stop()  or close the editor.
"""
import io, json, os, sys, time, traceback, contextlib, glob, shutil
import unreal

SAVED = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_saved_dir())
BASE = os.path.join(SAVED, "NeelamBridge")
INBOX, OUTBOX = os.path.join(BASE, "inbox"), os.path.join(BASE, "outbox")
SHOTS, DONE = os.path.join(OUTBOX, "shots"), os.path.join(BASE, "done")
SCREEN_DIR = os.path.join(SAVED, "Screenshots", "WindowsEditor")
for d in (INBOX, OUTBOX, SHOTS, DONE):
    os.makedirs(d, exist_ok=True)

ST = sys.modules.setdefault("neelam_bridge_state", type(sys)("neelam_bridge_state"))
if getattr(ST, "handle", None):                      # restart cleanly if already running
    try: unreal.unregister_slate_post_tick_callback(ST.handle)
    except Exception: pass
ST.shots, ST.shot_state, ST.last_poll, ST.last_beat, ST.jobs_run = [], None, 0.0, 0.0, getattr(ST, "jobs_run", 0)
ST.env = getattr(ST, "env", {})                      # persistent variables between jobs


def shot(name, location=None, rotation=None, settle_s=6.0, res="1600x900"):
    """Queue a viewport screenshot. location/rotation: unreal.Vector / unreal.Rotator (None = current view)."""
    ST.shots.append(dict(name=name, loc=location, rot=rotation, settle=settle_s, res=res))


def _write(path, data):
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(data, f, indent=1, default=str)
    os.replace(tmp, path)


def _run_job(path):
    name = os.path.splitext(os.path.basename(path))[0]
    code = open(path, encoding="utf-8").read()
    shutil.move(path, os.path.join(DONE, os.path.basename(path)))
    out, t0 = io.StringIO(), time.time()
    g = {"unreal": unreal, "shot": shot, "env": ST.env, "result": None, "__name__": "__neelam_job__"}
    rec = {"job": name, "ok": True, "error": None}
    try:
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
            with unreal.ScopedEditorTransaction("Claude: " + name):
                exec(compile(code, name, "exec"), g)
    except Exception:
        rec["ok"], rec["error"] = False, traceback.format_exc()
    rec.update(stdout=out.getvalue()[-20000:], result=g.get("result"), seconds=round(time.time() - t0, 2))
    _write(os.path.join(OUTBOX, name + ".json"), rec)
    ST.jobs_run += 1


def _shots_tick(now):
    s = ST.shot_state
    if s is None:
        if not ST.shots:
            return
        s = ST.shot_state = dict(ST.shots.pop(0), phase="move")
    ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    if s["phase"] == "move":
        if s["loc"] is not None:            # editor camera goes there too, so Cesium streams tiles for it
            loc, rot = s["loc"], s["rot"] or ues.get_level_viewport_camera_info()[1]
            ues.set_level_viewport_camera_info(loc, rot)
        try:
            _capture(s["name"], s["loc"], s["rot"], s["res"])   # capture every frame while settling (exposure adapts)
        except Exception:
            _write(os.path.join(SHOTS, s["name"] + ".json"), {"name": s["name"], "error": traceback.format_exc()})
            ST.shot_state = None
            return
        s["phase"], s["t"] = "settle", now
    elif s["phase"] == "settle" and now - s["t"] > s["settle"]:
        ST.cap.capture_component2d.capture_scene()
        s["phase"], s["t"] = "export", now
    elif s["phase"] == "export" and now - s["t"] > 0.5:
        ST.cap.capture_component2d.set_editor_property("capture_every_frame", False)
        dst = os.path.join(SHOTS, s["name"] + ".png")
        w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
        unreal.RenderingLibrary.export_render_target(w, ST.rt, SHOTS, s["name"] + ".png")
        _write(os.path.join(SHOTS, s["name"] + ".json"), {"name": s["name"], "file": dst, "time": time.time()})
        ST.shot_state = None


def _capture(name, loc, rot, res):
    """Render through a hidden SceneCapture2D (works even when the editor is in the background)."""
    wx, hy = (int(v) for v in res.split("x"))
    ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    if loc is None:
        loc, rot = ues.get_level_viewport_camera_info()
    cap = getattr(ST, "cap", None)
    try:
        cap.get_name()
    except Exception:
        cap = None
    if cap is None:
        cap = eas.spawn_actor_from_class(unreal.SceneCapture2D, loc, rot)
        cap.set_actor_label("_Claude_Capture"); cap.set_folder_path("_Claude")
        ST.cap = cap
    rt = getattr(ST, "rt", None)
    if rt is None or rt.get_editor_property("size_x") != wx:
        w = ues.get_editor_world()
        rt = unreal.RenderingLibrary.create_render_target2d(w, wx, hy, unreal.TextureRenderTargetFormat.RTF_RGBA8_SRGB)
        ST.rt = rt
    comp = cap.capture_component2d
    comp.set_editor_property("texture_target", rt)
    comp.set_editor_property("capture_source", unreal.SceneCaptureSource.SCS_FINAL_TONE_CURVE_HDR)
    comp.set_editor_property("capture_every_frame", True)
    comp.set_editor_property("capture_on_movement", False)
    comp.set_editor_property("always_persist_rendering_state", True)   # keeps eye adaptation between frames
    comp.set_editor_property("fov_angle", 70.0)
    pp = comp.get_editor_property("post_process_settings")        # fixed daylight exposure (EV100)
    for k, v in (("override_auto_exposure_min_brightness", True), ("auto_exposure_min_brightness", ST.env.get("ev100", 12.5)),
                 ("override_auto_exposure_max_brightness", True), ("auto_exposure_max_brightness", ST.env.get("ev100", 12.5))):
        try: pp.set_editor_property(k, v)
        except Exception: pass
    comp.set_editor_property("post_process_settings", pp)
    comp.set_editor_property("post_process_blend_weight", 1.0)
    cap.set_actor_location_and_rotation(loc, rot, False, False)
    comp.capture_scene()


def _tick(dt):
    now = time.time()
    try:
        if now - ST.last_beat > 2.0:
            ST.last_beat = now
            _write(os.path.join(OUTBOX, "heartbeat.json"), {"time": now, "jobs_run": ST.jobs_run,
                   "queued_shots": len(ST.shots) + (1 if ST.shot_state else 0)})
        _shots_tick(now)
        if now - ST.last_poll > 0.25 and ST.shot_state is None:
            ST.last_poll = now
            for p in sorted(glob.glob(os.path.join(INBOX, "*.py"))):
                _run_job(p)
                break                                 # one job per tick keeps the editor responsive
    except Exception:
        unreal.log_warning("NeelamBridge: " + traceback.format_exc())


def neelam_bridge_stop():
    if getattr(ST, "handle", None):
        unreal.unregister_slate_post_tick_callback(ST.handle)
        ST.handle = None
        unreal.log("NeelamBridge stopped")


# keep rendering (and screenshots) working while the editor is in the background
try:
    perf = unreal.get_default_object(unreal.EditorPerformanceSettings)
    perf.set_editor_property("throttle_cpu_when_not_foreground", False)
except Exception:
    pass

unreal.neelam_bridge_stop = neelam_bridge_stop
ST.handle = unreal.register_slate_post_tick_callback(_tick)
unreal.log("NeelamBridge running - inbox: " + INBOX)
