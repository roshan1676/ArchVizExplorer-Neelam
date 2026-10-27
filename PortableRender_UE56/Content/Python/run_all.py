"""Started by RENDER_ALL.bat. Waits 90 s for the editor to settle, queues every still (8K) and panorama (6 x 4K faces)
that isn't rendered yet, renders them, then runs Tools/finalize.py (4K copies, 16K/8K panoramas -> Saved/Final)."""
import unreal, os, time, subprocess, builtins
import mrq_render as R

PROJ = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
PY = r"C:\Users\Admin\AppData\Local\Programs\Python\Python314\python.exe"
_s = {"t0": time.time(), "go": False}

def _finalize(executor=None, success=None):
    unreal.log("RENDER_ALL: renders finished -> finalize")
    subprocess.Popen([PY, os.path.join(PROJ, "Tools", "finalize.py")], creationflags=0x00000010)

def _tick(dt):
    if _s["go"] or time.time() - _s["t0"] < 90: return
    _s["go"] = True
    import pano, pano_spots                     # rebuild pano rigs so they always match pano_spots.py
    LES = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    for unit in ("2BHK", "3BHK"):
        LES.load_level(R.LEVELS[unit]); pano.make_rig(unit, pano_spots.SPOTS[unit])
        LES.save_current_level(); unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    jobs = R.render_everything()
    unreal.log("RENDER_ALL: %d jobs %s" % (len(jobs), jobs))
    if not jobs: _finalize(); return
    ex = unreal.get_editor_subsystem(unreal.MoviePipelineQueueSubsystem).get_active_executor()
    if ex: ex.on_executor_finished_delegate.add_callable(_finalize)

builtins._render_all_tick = unreal.register_slate_post_tick_callback(_tick)
