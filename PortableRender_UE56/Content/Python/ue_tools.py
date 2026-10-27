"""Helpers for bridge jobs:  import ue_tools as T
  T.scene()              -> level name, actor count per class, cameras/lights
  T.find(text)           -> actors whose label contains text
  T.shot(name, w, h)     -> HighResShot of the active viewport -> Saved/Screenshots/WindowsEditor/<name>
  T.cam()                -> current editor viewport camera (loc, rot)
  T.set_cam(loc, rot)    -> move the editor viewport camera
  T.save()               -> save dirty levels + assets
"""
import unreal, collections

ACT = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
UES = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)

def _v(x): return [round(x.x, 1), round(x.y, 1), round(x.z, 1)]
def _r(r): return [round(r.pitch, 1), round(r.yaw, 1), round(r.roll, 1)]

def scene():
    actors = ACT.get_all_level_actors()
    kinds = collections.Counter(a.get_class().get_name() for a in actors)
    keep = ("Camera", "Light", "PostProcess", "SkyAtmosphere", "Fog", "Sky")
    special = [{"label": a.get_actor_label(), "class": a.get_class().get_name(), "loc": _v(a.get_actor_location())}
               for a in actors if any(k in a.get_class().get_name() for k in keep)]
    return {"level": UES.get_editor_world().get_name(), "actors": len(actors),
            "classes": dict(kinds.most_common()), "cameras_lights": special}

def find(text):
    t = text.lower()
    return [{"label": a.get_actor_label(), "class": a.get_class().get_name(),
             "loc": _v(a.get_actor_location()), "rot": _r(a.get_actor_rotation())}
            for a in ACT.get_all_level_actors() if t in a.get_actor_label().lower()]

def cam():
    loc, rot = UES.get_level_viewport_camera_info()
    return {"loc": _v(loc), "rot": _r(rot)}

def set_cam(loc, rot):
    UES.set_level_viewport_camera_info(unreal.Vector(*loc), unreal.Rotator(roll=rot[2], pitch=rot[0], yaw=rot[1]))

def shot(name="shot.png", w=1920, h=1080):
    # ponytail: async - the file lands a few frames later, poll for it from the caller
    unreal.AutomationLibrary.take_high_res_screenshot(w, h, name)
    return unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_saved_dir()) + "Screenshots/WindowsEditor/" + name

def save():
    return unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
