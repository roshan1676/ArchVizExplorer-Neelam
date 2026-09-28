"""Neelam - capture review screenshots of the Wind Tunnel development (run INSIDE Unreal).

    py "C:/Users/Admin/Documents/Unreal Projects/ArchVizExplorer-Neelam/Scripts/Neelam/Capture_Review_Shots.py"

Moves the viewport camera to 4 views around Neelam_WindTunnel_Root (the model's own
reference angles), waits for Cesium tiles / Lumen to settle, and saves 1600x900 shots to
Saved/Neelam/Review/. Don't touch the viewport for ~40 s while it runs.
"""
import os, sys, shutil, glob, time
try:
    import unreal
except ImportError:
    sys.exit("Run this INSIDE the Unreal Editor.")

ROOT_LABEL = "Neelam_WindTunnel_Root"
SETTLE_S, AFTER_SHOT_S = 20.0, 3.0
# (name, camera local cm, target local cm) in the root's frame: +X = frontage, -Y = road/gate side
VIEWS = [
    ("01_front_road",     (-2000, -32000,  2500), (0, 0, 9000)),
    ("02_aerial",         (-26000, -28000, 24000), (0, 0, 5000)),
    ("03_facade_close",   (1500, 5500, 4500),      (500, -1000, 5000)),
    ("04_podium_entrance",(-6500, -9800, 350),     (-2500, -5200, 900)),
    ("05_edge_corner_low", (13500, -9500, 250),     (9900, -6300, 50)),     # platform corner vs map
    ("06_edge_side_low",   (-14500, 1500, 350),     (-9900, 0, 50)),
]

ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
root = next((a for a in eas.get_all_level_actors() if a.get_actor_label() == ROOT_LABEL), None)
if root is None:
    raise RuntimeError(ROOT_LABEL + " not found - run Place_WindTunnel.py first")
xf = root.get_actor_transform()
SAVED = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_saved_dir())
SHOT_DIR = os.path.join(SAVED, "Screenshots", "WindowsEditor")
OUT = os.path.join(SAVED, "Neelam", "Review")
os.makedirs(OUT, exist_ok=True)
for f in glob.glob(os.path.join(OUT, "*.png")):
    os.remove(f)

def world(v): return xf.transform_location(unreal.Vector(*v))
def existing(): return set(glob.glob(os.path.join(SHOT_DIR, "*.png")))

state = {"i": 0, "phase": "move", "t": time.time(), "before": set(), "handle": None}

def tick(dt):
    s = state
    if s["i"] >= len(VIEWS):
        unreal.unregister_slate_post_tick_callback(s["handle"])
        unreal.log("Neelam review shots saved to " + OUT)
        return
    name, cam, tgt = VIEWS[s["i"]]
    now = time.time()
    if s["phase"] == "move":
        c, t = world(cam), world(tgt)
        ues.set_level_viewport_camera_info(c, unreal.MathLibrary.find_look_at_rotation(c, t))
        s["phase"], s["t"] = "settle", now
    elif s["phase"] == "settle" and now - s["t"] > SETTLE_S:
        s["before"] = existing()
        unreal.SystemLibrary.execute_console_command(None, "HighResShot 1600x900")
        s["phase"], s["t"] = "wait", now
    elif s["phase"] == "wait" and now - s["t"] > AFTER_SHOT_S:
        new = sorted(existing() - s["before"], key=os.path.getmtime)
        if new:                                          # wait for the file to appear (editor may be busy)
            time.sleep(0.5)
            shutil.copy2(new[-1], os.path.join(OUT, name + ".png"))
            s["i"] += 1; s["phase"] = "move"
        elif now - s["t"] > 45.0:
            unreal.log_warning("No screenshot found for " + name + " (keep the Unreal window in front)")
            s["i"] += 1; s["phase"] = "move"

state["handle"] = unreal.register_slate_post_tick_callback(tick)
unreal.log("Neelam: capturing %d review shots (~%d s)..." % (len(VIEWS), len(VIEWS) * (SETTLE_S + AFTER_SHOT_S)))
