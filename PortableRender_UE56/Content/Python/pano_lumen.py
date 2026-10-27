"""Fast Lumen panoramas (minutes, not hours) - same 6-cube-face rig as pano.py but full res.

ROOT CAUSE of the 2026-10-26 exposure mess: the level's manual-exposure post process volume
(scene_builder.environment(): AEM_MANUAL, apply_physical_camera_exposure=False, bias=0.0 - see its
docstring "EV100 0 == Cycles exposure 0") was never being explicitly matched on the capture's OWN
post_process_settings, which only overrode GI/reflection method. Guessing auto_exposure_bias values
(-1.2, -0.5, 10.0 ...) on top of that inconsistent base never converged. Fix: bake the SAME manual
AEM_MANUAL / bias=EXPOSURE_BIAS onto the capture explicitly, every time - no more guessing.

ROOT CAUSE of the 2026-10-26 "Out of video memory" crash: a batch of up to 24 full 4096x4096
SceneCapture2D + render targets was left alive across many bridge calls. render_spot() below does
ONE spot (6 captures) at a time, start -> tick -> finish -> destroy, so nothing heavy sits in the
level between calls.

    import pano_lumen as PL
    PL.render_spot("2BHK", "01_Living", 60, -900)        # one spot, ~6 ticks, destroys itself, returns face dir
    # repeat per spot (separate bridge calls so Lumen gets real wall-clock time to bounce-light between ticks)
"""
import unreal, os, sys, builtins
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pano as P

FACE_RES = 4096
EXPOSURE_BIAS = 0.0   # matches scene_builder.environment()'s manual-exposure baseline (EV100 0) - the project's
                       # own convention, not a guess. Tune per-spot later only if a specific room is genuinely too dark/bright.
_batch = builtins.__dict__.setdefault("_claude_pano_batch", {})   # {(unit,spot,tag): (cap_actor, render_target)}

def _set_manual_exposure(pp, bias):
    pp.set_editor_property("override_auto_exposure_method", True)
    pp.set_editor_property("auto_exposure_method", unreal.AutoExposureMethod.AEM_MANUAL)
    pp.set_editor_property("override_auto_exposure_apply_physical_camera_exposure", True)
    pp.set_editor_property("auto_exposure_apply_physical_camera_exposure", False)
    pp.set_editor_property("override_auto_exposure_bias", True)
    pp.set_editor_property("auto_exposure_bias", bias)
    return pp

def start_batch(unit, spots, bias=EXPOSURE_BIAS, z=None):
    """spots: {spot_name: (x, y)}. Spawns 6 full-res Lumen SceneCapture2D per spot.
    Prefer render_spot() for one spot at a time - this stays for multi-spot batches if VRAM allows."""
    for cap, _ in _batch.values():   # destroy any still-tracked captures from a previous start_batch/retry
        if unreal.SystemLibrary.is_valid(cap): P.ACT.destroy_actor(cap)
    _batch.clear()
    for spot, (x, y) in spots.items():
        for tag, yaw, pitch in P.FACES:
            rt = unreal.RenderingLibrary.create_render_target2d(P._world(), FACE_RES, FACE_RES, unreal.TextureRenderTargetFormat.RTF_RGBA8_SRGB)
            cap = P.ACT.spawn_actor_from_class(unreal.SceneCapture2D, unreal.Vector(x, y, P.EYE_Z if z is None else z), P._rot(yaw, pitch))
            c = cap.capture_component2d
            c.set_editor_property("fov_angle", P.FOV); c.set_editor_property("texture_target", rt)
            c.set_editor_property("capture_source", unreal.SceneCaptureSource.SCS_FINAL_TONE_CURVE_HDR)
            c.set_editor_property("always_persist_rendering_state", True); c.set_editor_property("capture_every_frame", False)
            pp = c.get_editor_property("post_process_settings")
            pp.set_editor_property("override_dynamic_global_illumination_method", True)
            pp.set_editor_property("dynamic_global_illumination_method", unreal.DynamicGlobalIlluminationMethod.LUMEN)
            pp.set_editor_property("override_reflection_method", True); pp.set_editor_property("reflection_method", unreal.ReflectionMethod.LUMEN)
            pp = _set_manual_exposure(pp, bias)
            c.set_editor_property("post_process_settings", pp); c.set_editor_property("post_process_blend_weight", 1.0)
            _batch[(unit, spot, tag)] = (cap, rt)
    return {"spots": list(spots.keys()), "captures": len(_batch)}

def tick_batch():
    for cap, _ in _batch.values():
        cap.capture_component2d.capture_scene()
    return len(_batch)

def finish_batch(unit):
    out_root = os.path.join(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_saved_dir()), "Pano", "faces")
    spots = sorted({s for (u, s, t) in _batch if u == unit})
    for spot in spots:
        d = os.path.join(out_root, "%s_%s" % (unit, spot)); os.makedirs(d, exist_ok=True)
        for tag, yaw, pitch in P.FACES:
            cap, rt = _batch.pop((unit, spot, tag))
            unreal.RenderingLibrary.export_render_target(P._world(), rt, d, tag + ".png")
            P.ACT.destroy_actor(cap)
    return spots

def cleanup_orphans():
    """Destroy every SceneCapture2D actor in the level, whether or not this module's _batch dict knows about it
    (covers a previous bridge session's leftovers after an editor restart, when _batch starts out empty)."""
    n = 0
    for a in P.ACT.get_all_level_actors():
        if isinstance(a, unreal.SceneCapture2D):
            P.ACT.destroy_actor(a); n += 1
    _batch.clear()
    return {"destroyed": n}

def render_spot_start(unit, spot, x, y, bias=EXPOSURE_BIAS, z=None):
    return start_batch(unit, {spot: (x, y)}, bias=bias, z=z)

def amenity_spot(grid=25):
    """(x, y, z) for an amenity pano: on the main floor (most common surface height seen from above, on a
    grid over the model's bounds), the open point nearest the model's centre, at eye height."""
    acts = [a for a in P.ACT.get_all_level_actors() if isinstance(a, unreal.StaticMeshActor)
            and a.get_actor_bounds(False)[1].length() < 30000]   # skip the HDRI sky sphere
    lo, hi = [1e9] * 3, [-1e9] * 3
    for a in acts:
        o, e = a.get_actor_bounds(False)
        for i, k in enumerate("xyz"):
            lo[i] = min(lo[i], getattr(o, k) - getattr(e, k)); hi[i] = max(hi[i], getattr(o, k) + getattr(e, k))
    cx, cy = (lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2
    hits = []
    for i in range(grid):
        for j in range(grid):
            x = lo[0] + (hi[0] - lo[0]) * (i + 0.5) / grid; y = lo[1] + (hi[1] - lo[1]) * (j + 0.5) / grid
            h = unreal.SystemLibrary.line_trace_single(P._world(), unreal.Vector(x, y, hi[2] + 100), unreal.Vector(x, y, lo[2] - 100),
                                                       unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, [], unreal.DrawDebugTrace.NONE, True)
            if h: hits.append((x, y, h.to_tuple()[4].z))
    if not hits: return [cx, cy, lo[2] + P.EYE_Z]
    bins = {}
    for x, y, z in hits: bins.setdefault(round(z / 20), []).append((x, y, z))
    floor = max(bins.values(), key=len)   # ponytail: biggest flat area = the deck/floor people stand on
    x, y, z = min(floor, key=lambda p: (p[0] - cx) ** 2 + (p[1] - cy) ** 2)
    return [x, y, z + P.EYE_Z]

def render_spot_finish(unit):
    return finish_batch(unit)

# NOTE: tick_batch() must be called from SEPARATE bridge jobs (separate `bash ue.sh` processes), one per tick -
# a Python loop with time.sleep() inside a single job blocks the engine's own tick too, so Lumen never gets a
# real frame to bounce light into and the sleep is wasted. See Tools/pano_lumen_spot.sh for the driver that does
# this correctly (same external-loop pattern as the already-working Tools/pano_preview.sh).

def _bounds():
    acts = [a for a in P.ACT.get_all_level_actors() if isinstance(a, unreal.StaticMeshActor)
            and a.get_actor_bounds(False)[1].length() < 30000]   # skip the HDRI sky sphere
    lo, hi = [1e9] * 3, [-1e9] * 3
    for a in acts:
        o, e = a.get_actor_bounds(False)
        for i, k in enumerate("xyz"):
            lo[i] = min(lo[i], getattr(o, k) - getattr(e, k)); hi[i] = max(hi[i], getattr(o, k) + getattr(e, k))
    return lo, hi

def topdown(name, res=1600):
    """Ortho top view of the open level -> Saved/Pano/_topdown/<name>.png; returns the world box it covers
    (image x = world +X, image y = world +Y, square, centred on the model bounds)."""
    lo, hi = _bounds()
    cx, cy = (lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2; w = max(hi[0] - lo[0], hi[1] - lo[1]) * 1.05
    rt = unreal.RenderingLibrary.create_render_target2d(P._world(), res, res, unreal.TextureRenderTargetFormat.RTF_RGBA8_SRGB)
    cap = P.ACT.spawn_actor_from_class(unreal.SceneCapture2D, unreal.Vector(cx, cy, hi[2] + 2000), unreal.Rotator(roll=0, pitch=-90, yaw=-90))
    c = cap.capture_component2d
    c.set_editor_property("projection_type", unreal.CameraProjectionMode.ORTHOGRAPHIC); c.set_editor_property("ortho_width", w)
    c.set_editor_property("texture_target", rt); c.set_editor_property("capture_source", unreal.SceneCaptureSource.SCS_FINAL_TONE_CURVE_HDR)
    pp = _set_manual_exposure(c.get_editor_property("post_process_settings"), EXPOSURE_BIAS)
    c.set_editor_property("post_process_settings", pp); c.set_editor_property("post_process_blend_weight", 1.0)
    for _ in range(3): c.capture_scene()
    d = os.path.join(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_saved_dir()), "Pano", "_topdown"); os.makedirs(d, exist_ok=True)
    unreal.RenderingLibrary.export_render_target(P._world(), rt, d, name + ".png")
    P.ACT.destroy_actor(cap)
    return {"cx": cx, "cy": cy, "w": w, "res": res, "zlo": lo[2], "zhi": hi[2]}

def spot_at(name, u, v, h0=250):
    """Pano spot from a top-down grid pick (u, v in 0..10 cell units, Tools/topdown_sheet.py): floor found by a
    trace starting 2.5 m above the model's lowest point, so roofs/canopies are skipped. Returns [x, y, eye z]."""
    import json
    j = json.load(open(os.path.join(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_saved_dir()), "Pano", "_topdown", name + ".json")))
    x, y = j["cx"] + (u / 10 - 0.5) * j["w"], j["cy"] + (v / 10 - 0.5) * j["w"]
    h = unreal.SystemLibrary.line_trace_single(P._world(), unreal.Vector(x, y, j["zlo"] + h0), unreal.Vector(x, y, j["zlo"] - 500),
                                               unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, [], unreal.DrawDebugTrace.NONE, True)
    return [x, y, (h.to_tuple()[4].z if h else j["zlo"]) + P.EYE_Z]

def add_sun(intensity=4.8, yaw=90.0, pitch=-23.4, color=(1.0, 0.9, 0.78)):
    """Warm directional sun lined up with aerial_city_sunny.hdr's sun (lon -90 deg = world -Y, elev 23 deg; light travels
    along its forward, so yaw 90 / pitch -23.4). Amenity exports had no sun lamp -> sky-only light read as blue/navy.
    intensity in the project's scaled units (scene_builder.K * Blender W/m2); re-runnable (replaces the previous one)."""
    for a in P.ACT.get_all_level_actors():
        if "pano_sun" in [str(t) for t in a.tags]: P.ACT.destroy_actor(a)
    a = P.ACT.spawn_actor_from_class(unreal.DirectionalLight, unreal.Vector(0, 0, 2000), unreal.Rotator(roll=0, pitch=pitch, yaw=yaw))
    c = a.light_component
    c.set_mobility(unreal.ComponentMobility.MOVABLE)   # Stationary + no lighting build = unbuilt/preview shadowing (dark decks)
    c.set_intensity(intensity); c.set_light_color(unreal.LinearColor(*color, 1))
    c.set_editor_property("light_source_angle", 0.6); c.set_editor_property("atmosphere_sun_light", False)
    a.tags = ["pano_sun"]; a.set_actor_label("Pano_Sun"); a.set_folder_path("Pano")
    return a.get_actor_label()
