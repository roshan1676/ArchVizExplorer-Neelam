"""UI previews without the user: render the live PIE MasterMenu off-screen + a scene shot, composite -> PNG."""
import os, unreal
L = unreal.NeelamToolsLibrary
OUT = os.path.join(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_saved_dir()), "NeelamBridge", "outbox", "ui")
os.makedirs(OUT, exist_ok=True)
def world(): return unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
def pc(): return unreal.GameplayStatics.get_player_controller(world(), 0)
def render(widget, name, w=1920, h=1080):
    return L.render_widget_to_png(widget, w, h, os.path.join(OUT, name + ".png"))
def scene(name):
    unreal.SystemLibrary.execute_console_command(world(), "HighResShot 1920x1080 filename=%s_scene" % name)
def viewport_widgets():
    return unreal.WidgetBlueprintLibrary.get_all_widgets_of_class(world(), [], unreal.UserWidget, True) if hasattr(unreal, "WidgetBlueprintLibrary") else []
