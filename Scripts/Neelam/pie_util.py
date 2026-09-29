"""PIE helpers for NeelamBridge jobs."""
import json, os, glob, time
import unreal
L = unreal.NeelamToolsLibrary
SHOTS = os.path.join(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_saved_dir()), "Screenshots", "WindowsEditor")
def world(): return unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
def pc(): return unreal.GameplayStatics.get_player_controller(world(), 0)
def shot(name):
    """screenshot WITH UI -> Saved/Screenshots/WindowsEditor/<name>*.png (async, next frame)"""
    unreal.AutomationLibrary.take_high_res_screenshot(1600, 900, name + ".png") if False else None
    unreal.SystemLibrary.execute_console_command(world(), "Shot showui")
def rect(widget): return json.loads(L.get_widget_viewport_rect(widget))
def click_widget(widget):
    r = rect(widget)
    return L.click_game_viewport(r["x"] + r["w"] / 2, r["y"] + r["h"] / 2, "Left", False), r
