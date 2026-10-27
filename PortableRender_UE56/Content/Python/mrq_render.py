"""Final stills through Movie Render Queue (needs the MovieRenderPipeline plugin, enabled in the .uproject).
1. make_sequences(level_name)   - with that level open: one-frame LevelSequence per BL_ camera -> /Game/Neelam/<L>/Shots/SEQ_<cam>
2. render_all()                 - queues every SEQ_ in both levels, 3840x2160 PNG, Lumen warm-up, PIE executor (async)
Output: Saved/MovieRenders/<level>/<cam>.png
"""
import unreal, os, glob

LEVELS = {"2BHK": "/Game/Neelam/2BHK/L_2BHK", "3BHK": "/Game/Neelam/3BHK/L_3BHK"}
EAL = unreal.EditorAssetLibrary
ACT = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
AT = unreal.AssetToolsHelpers.get_asset_tools()

def _seq_name(label): return "SEQ_" + label.replace("BL_", "").replace("LUX_Cam_", "").replace(".", "_")

def make_sequences(name):
    folder = "/Game/Neelam/%s/Shots" % name
    made = []
    for cam in [a for a in ACT.get_all_level_actors() if isinstance(a, unreal.CineCameraActor) and a.get_actor_label().startswith(("BL_", "LUX_Cam_"))]:
        sname = _seq_name(cam.get_actor_label())
        if EAL.does_asset_exist(folder + "/" + sname): EAL.delete_asset(folder + "/" + sname)
        seq = AT.create_asset(sname, folder, unreal.LevelSequence, unreal.LevelSequenceFactoryNew())
        seq.set_display_rate(unreal.FrameRate(24, 1))
        seq.set_playback_start(0); seq.set_playback_end(1)
        binding = seq.add_possessable(cam)
        cut = seq.add_track(unreal.MovieSceneCameraCutTrack).add_section()
        cut.set_range(0, 1)
        cut.set_camera_binding_id(seq.get_binding_id(binding))
        EAL.save_loaded_asset(seq)
        made.append(sname)
    return made

def render_all(res=(3840, 2160), temporal=16, warmup=96):
    subsys = unreal.get_editor_subsystem(unreal.MoviePipelineQueueSubsystem)
    q = subsys.get_queue(); q.delete_all_jobs()
    out_root = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_saved_dir()) + "MovieRenders"
    reg = unreal.AssetRegistryHelpers.get_asset_registry()
    jobs = []
    for name, level in LEVELS.items():
        for a in reg.get_assets_by_path("/Game/Neelam/%s/Shots" % name):
            seq_path = str(a.package_name) + "." + str(a.asset_name)
            job = q.allocate_new_job(unreal.MoviePipelineExecutorJob)
            job.job_name = "%s_%s" % (name, a.asset_name)
            job.map = unreal.SoftObjectPath(level + "." + level.rsplit("/", 1)[1])
            job.sequence = unreal.SoftObjectPath(seq_path)
            cfg = job.get_configuration()
            o = cfg.find_or_add_setting_by_class(unreal.MoviePipelineOutputSetting)
            o.output_resolution = unreal.IntPoint(*res)
            o.output_directory = unreal.DirectoryPath(os.path.join(out_root, name))
            o.file_name_format = str(a.asset_name).replace("SEQ_", "")
            o.override_existing_output = True
            cfg.find_or_add_setting_by_class(unreal.MoviePipelineDeferredPassBase)
            cfg.find_or_add_setting_by_class(unreal.MoviePipelineImageSequenceOutput_PNG)
            aa = cfg.find_or_add_setting_by_class(unreal.MoviePipelineAntiAliasingSetting)
            aa.spatial_sample_count = 1
            aa.temporal_sample_count = temporal          # ponytail: 16 TAA samples; raise for cleaner glass/hair
            aa.override_anti_aliasing = True
            aa.anti_aliasing_method = unreal.AntiAliasingMethod.AAM_NONE
            aa.engine_warm_up_count = warmup             # Lumen + VSM need frames to converge on a still
            aa.render_warm_up_count = warmup
            aa.use_camera_cut_for_warm_up = False
            cv = cfg.find_or_add_setting_by_class(unreal.MoviePipelineConsoleVariableSetting)
            for k, v in (("r.Lumen.ScreenProbeGather.TemporalFilterProbes", 1), ("r.Shadow.Virtual.SMRT.RayCountDirectional", 16),
                         ("r.Shadow.Virtual.SMRT.RayCountLocal", 16), ("r.MotionBlurQuality", 0)):
                cv.add_or_update_console_variable(k, v)
            cfg.find_or_add_setting_by_class(unreal.MoviePipelineGameOverrideSetting)
            jobs.append(job.job_name)
    subsys.render_queue_with_executor_instance(unreal.MoviePipelinePIEExecutor())
    return {"jobs": jobs, "out": out_root}

def render(shots, res=(1920, 1080), path_tracer=False, spp=128, tag="", warmup=96, temporal=16):
    """shots: list of (unit, seq_name) e.g. [("3BHK", "SEQ_Camera")]. Path tracer: spp samples/pixel + denoiser.
    Output Saved/MovieRenders/<unit>/<seq without SEQ_><tag>.png"""
    subsys = unreal.get_editor_subsystem(unreal.MoviePipelineQueueSubsystem)
    q = subsys.get_queue(); q.delete_all_jobs()
    out_root = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_saved_dir()) + "MovieRenders"
    for unit, seq in shots:
        level = LEVELS[unit]
        job = q.allocate_new_job(unreal.MoviePipelineExecutorJob)
        job.job_name = "%s_%s%s" % (unit, seq, tag)
        job.map = unreal.SoftObjectPath(level + "." + level.rsplit("/", 1)[1])
        job.sequence = unreal.SoftObjectPath("/Game/Neelam/%s/Shots/%s.%s" % (unit, seq, seq))
        cfg = job.get_configuration()
        o = cfg.find_or_add_setting_by_class(unreal.MoviePipelineOutputSetting)
        o.output_resolution = unreal.IntPoint(*res)
        o.output_directory = unreal.DirectoryPath(os.path.join(out_root, unit))
        o.file_name_format = seq.replace("SEQ_", "") + tag
        o.override_existing_output = True
        cfg.find_or_add_setting_by_class(unreal.MoviePipelineImageSequenceOutput_PNG)
        aa = cfg.find_or_add_setting_by_class(unreal.MoviePipelineAntiAliasingSetting)
        aa.override_anti_aliasing = True; aa.anti_aliasing_method = unreal.AntiAliasingMethod.AAM_NONE
        cv = cfg.find_or_add_setting_by_class(unreal.MoviePipelineConsoleVariableSetting)
        if path_tracer:
            cfg.find_or_add_setting_by_class(unreal.MoviePipelineDeferredPass_PathTracer)
            aa.spatial_sample_count = spp; aa.temporal_sample_count = 1
            aa.engine_warm_up_count = 32; aa.render_warm_up_count = 0   # lets textures stream in
            for k, v in (("r.PathTracing.Denoiser", 1), ("r.PathTracing.MaxBounces", 12), ("r.PathTracing.SkylightCaching", 1),
                         ("r.PathTracing.ApproximateCaustics", 1), ("r.PathTracing.MaxPathIntensity", 24)):
                cv.add_or_update_console_variable(k, v)
        else:
            cfg.find_or_add_setting_by_class(unreal.MoviePipelineDeferredPassBase)
            aa.spatial_sample_count = 1; aa.temporal_sample_count = temporal
            aa.engine_warm_up_count = warmup; aa.render_warm_up_count = warmup; aa.use_camera_cut_for_warm_up = False
        cfg.find_or_add_setting_by_class(unreal.MoviePipelineGameOverrideSetting)
    subsys.render_queue_with_executor_instance(unreal.MoviePipelinePIEExecutor())
    return [j.job_name for j in q.get_jobs()]

def render_panos(units_spots, face_res=4096, spp=192):
    """units_spots: {unit: [spot,...]}. One MRQ job per spot (6 frames = 6 cube faces, path traced).
    Faces -> Saved/Pano/faces/<unit>_<spot>/face.0000.png .. face.0005.png (order F R B L U D)."""
    subsys = unreal.get_editor_subsystem(unreal.MoviePipelineQueueSubsystem)
    q = subsys.get_queue(); q.delete_all_jobs()
    root = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_saved_dir()) + "Pano/faces"
    for unit, spots in units_spots.items():
        level = LEVELS[unit]
        for spot in spots:
            seq = "/Game/Neelam/%s/Pano/SEQ_PANO_%s.SEQ_PANO_%s" % (unit, spot, spot)
            job = q.allocate_new_job(unreal.MoviePipelineExecutorJob)
            job.job_name = "%s_%s" % (unit, spot)
            job.map = unreal.SoftObjectPath(level + "." + level.rsplit("/", 1)[1]); job.sequence = unreal.SoftObjectPath(seq)
            cfg = job.get_configuration()
            o = cfg.find_or_add_setting_by_class(unreal.MoviePipelineOutputSetting)
            o.output_resolution = unreal.IntPoint(face_res, face_res)
            o.output_directory = unreal.DirectoryPath(os.path.join(root, "%s_%s" % (unit, spot)))
            o.file_name_format = "face.{frame_number}"; o.override_existing_output = True
            cfg.find_or_add_setting_by_class(unreal.MoviePipelineImageSequenceOutput_PNG)
            cfg.find_or_add_setting_by_class(unreal.MoviePipelineDeferredPass_PathTracer)
            aa = cfg.find_or_add_setting_by_class(unreal.MoviePipelineAntiAliasingSetting)
            aa.override_anti_aliasing = True; aa.anti_aliasing_method = unreal.AntiAliasingMethod.AAM_NONE
            aa.spatial_sample_count = spp; aa.temporal_sample_count = 1
            aa.engine_warm_up_count = 32; aa.render_warm_up_count = 0
            cv = cfg.find_or_add_setting_by_class(unreal.MoviePipelineConsoleVariableSetting)
            for k, v in (("r.PathTracing.Denoiser", 1), ("r.PathTracing.MaxBounces", 12), ("r.PathTracing.SkylightCaching", 1),
                         ("r.PathTracing.ApproximateCaustics", 1), ("r.PathTracing.MaxPathIntensity", 24), ("r.MotionBlurQuality", 0)):
                cv.add_or_update_console_variable(k, v)
            cfg.find_or_add_setting_by_class(unreal.MoviePipelineGameOverrideSetting)
    subsys.render_queue_with_executor_instance(unreal.MoviePipelinePIEExecutor())
    return [j.job_name for j in q.get_jobs()]

# ---------------- everything in one queue ----------------
STILLS = {   # sequence -> final file name
    "2BHK": {"SEQ_Living": "2BHK_01_Living_A", "SEQ_Living2": "2BHK_02_Living_B", "SEQ_Dining": "2BHK_03_Dining",
             "SEQ_Kitchen": "2BHK_04_Kitchen", "SEQ_Bed1": "2BHK_05_Bedroom1", "SEQ_Bed2": "2BHK_06_Bedroom2",
             "SEQ_Camera": "2BHK_07_Bathroom"},
    "3BHK": {"SEQ_Camera": "3BHK_01_Living_A", "SEQ_Camera_001": "3BHK_02_Living_B", "SEQ_Camera_003": "3BHK_03_Kitchen",
             "SEQ_Camera_002": "3BHK_04_Corridor"},
}

def _pt(cfg, spp, warmup=32):
    cfg.find_or_add_setting_by_class(unreal.MoviePipelineImageSequenceOutput_PNG)
    cfg.find_or_add_setting_by_class(unreal.MoviePipelineDeferredPass_PathTracer)
    aa = cfg.find_or_add_setting_by_class(unreal.MoviePipelineAntiAliasingSetting)
    aa.override_anti_aliasing = True; aa.anti_aliasing_method = unreal.AntiAliasingMethod.AAM_NONE
    aa.spatial_sample_count = spp; aa.temporal_sample_count = 1; aa.engine_warm_up_count = warmup; aa.render_warm_up_count = 0
    cv = cfg.find_or_add_setting_by_class(unreal.MoviePipelineConsoleVariableSetting)
    for k, v in (("r.PathTracing.Denoiser", 1), ("r.PathTracing.MaxBounces", 12), ("r.PathTracing.SkylightCaching", 1),
                 ("r.PathTracing.ApproximateCaustics", 1), ("r.PathTracing.MaxPathIntensity", 24), ("r.MotionBlurQuality", 0)):
        cv.add_or_update_console_variable(k, v)
    cfg.find_or_add_setting_by_class(unreal.MoviePipelineGameOverrideSetting)

def render_everything(still_res=(7680, 4320), still_spp=256, face_res=4096, face_spp=192, render=True, panos=True):
    """8K path-traced stills of every room camera + 6-face panoramas of every spot in pano_spots.py.
    Skips outputs that already exist (so it can be restarted). Raw output: Saved/Final/_raw/..."""
    import pano_spots
    subsys = unreal.get_editor_subsystem(unreal.MoviePipelineQueueSubsystem)
    q = subsys.get_queue(); q.delete_all_jobs()
    raw = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_saved_dir()) + "Final/_raw"
    names = []
    def job(unit, seq_path, name):
        level = LEVELS[unit]
        j = q.allocate_new_job(unreal.MoviePipelineExecutorJob); j.job_name = name
        j.map = unreal.SoftObjectPath(level + "." + level.rsplit("/", 1)[1]); j.sequence = unreal.SoftObjectPath(seq_path)
        names.append(name); return j.get_configuration()
    for unit, seqs in STILLS.items():
        for seq, name in seqs.items():
            if os.path.exists(os.path.join(raw, "stills", name + ".png")): continue
            cfg = job(unit, "/Game/Neelam/%s/Shots/%s.%s" % (unit, seq, seq), name)
            o = cfg.find_or_add_setting_by_class(unreal.MoviePipelineOutputSetting)
            o.output_resolution = unreal.IntPoint(*still_res); o.output_directory = unreal.DirectoryPath(os.path.join(raw, "stills"))
            o.file_name_format = name; o.override_existing_output = True
            _pt(cfg, still_spp)
    old = os.path.join(raw, "..", "..", "Pano", "faces")   # faces already rendered by the earlier pano run count too
    for unit, spots in (pano_spots.SPOTS.items() if panos else []):
        for spot in spots:
            name = "%s_%s" % (unit, spot)
            done = any(len(glob.glob(os.path.join(d, name, "face.*.png"))) >= 6 for d in (os.path.join(raw, "faces"), old))
            if done: continue
            cfg = job(unit, "/Game/Neelam/%s/Pano/SEQ_PANO_%s.SEQ_PANO_%s" % (unit, spot, spot), "PANO_" + name)
            o = cfg.find_or_add_setting_by_class(unreal.MoviePipelineOutputSetting)
            o.output_resolution = unreal.IntPoint(face_res, face_res)
            o.output_directory = unreal.DirectoryPath(os.path.join(raw, "faces", name))
            o.file_name_format = "face.{frame_number}"; o.override_existing_output = True
            _pt(cfg, face_spp)
    if render and names:
        subsys.render_queue_with_executor_instance(unreal.MoviePipelinePIEExecutor())
    return names
