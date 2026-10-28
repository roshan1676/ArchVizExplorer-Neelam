"""PIE: press a BP_MasterMenu_Widget button exactly as a click does (broadcast its OnClicked). Synthetic viewport clicks
do not reach the UI while PIE runs in a background editor window. Bridge job globals: BUTTON = "Button_Surroundings" ..."""
import unreal
gw = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
cls = unreal.load_class(None, "/Game/ArchVizExplorer/Blueprints/Widgets/BP_MasterMenu_Widget.BP_MasterMenu_Widget_C")
menus = [w for w in unreal.ObjectIterator(cls) if w.get_world() == gw and not w.get_name().startswith("Default__")]   # live menu in the PIE world
btn = menus[0].get_editor_property(globals().get("BUTTON", "Button_Surroundings"))
btn.on_clicked.broadcast()
result = {"menus": len(menus), "pressed": btn.get_name()}
