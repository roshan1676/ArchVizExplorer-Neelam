"""Floor View start camera (client reference shot, 30 Sep) + Tower E demo-flat hint text.
Needs the NeelamRuntime build with ANeelamFlatTour::OverviewPivotOffset. Re-run safe."""
import unreal
YAW, PITCH, ARM = 47.0, -8.0, 45000.0            # FocusOverview uses ARM * 0.75 for a single tower (~338 m), Tower E centred, compass SE
PIVOT_OFFSET = unreal.Vector(0.0, 0.0, 0.0)       # added to the Tower E centre (0 = tower in the middle of the screen)
HINT = "Demo flats are on Tower E · Floor 20 (2BHK + 3BHK)."

def run():
    out = {}
    es = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for a in es.get_all_level_actors():
        if a.get_class().get_name() == "NeelamFlatTour":
            a.set_editor_property("overview_yaw", YAW); a.set_editor_property("overview_pitch", PITCH)
            a.set_editor_property("overview_arm_length", ARM)
            try: a.set_editor_property("overview_pivot_offset", PIVOT_OFFSET)
            except Exception: pass   # older NeelamRuntime build
            out["tour"] = a.get_actor_label()
    ar = unreal.AssetRegistryHelpers.get_asset_registry()
    for d in ar.get_assets_by_path("/Game/Neelam/FloorView/UI", recursive=True):
        path = str(d.package_name) + "." + str(d.asset_name)
        t = unreal.find_object(None, path + ":WidgetTree.EmptyText")
        if t is None:
            wbp = unreal.load_asset(path)
            t = unreal.find_object(None, path + ":WidgetTree.EmptyText") if wbp else None
        if t:
            t.set_editor_property("text", HINT)
            wbp = unreal.load_asset(path)
            out[str(d.asset_name)] = unreal.NeelamToolsLibrary.compile_and_report(wbp)[:120]
            unreal.EditorAssetLibrary.save_asset(path, only_if_is_dirty=False)
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    return out

if __name__ == "__main__":
    print(run())
