"""Where does the player camera end up? (28 Oct, client: "Home button and camera broken - inside buildings, under the map")
Bridge job in PIE, globals MODE / ARG:
  MODE "press"  ARG = button name on BP_MasterMenu_Widget (Button_Home / Button_Surroundings / Button_Amenities ...)
  MODE "pin"    ARG = BP_POI label (POI_fortis, Amenity_gym ...) -> Select_POI (what clicking the pin does)
  MODE "state"  -> camera + pivot + verdict:
     under_map : the photo map (Cesium) has a surface ABOVE the camera within 300 m straight up
     inside    : the first thing straight up AND straight down from the camera is the same non-map mesh (in a box)
     clear_m   : camera height above the map / mesh directly below
Run "press"/"pin", wait for the flight (~4 s), then "state"."""
import unreal
MODE = globals().get("MODE", "state"); ARG = globals().get("ARG")
gw = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
pc = unreal.GameplayStatics.get_player_controller(gw, 0)


def first_hit(a, b, ign):
    h = unreal.SystemLibrary.line_trace_single(gw, a, b, unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, ign, unreal.DrawDebugTrace.NONE, True)
    t = h.to_tuple() if h else None
    return (t[9], t[4]) if t and t[0] and t[9] else (None, None)


if MODE == "press":
    BUTTON = ARG
    exec(open(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()) + "Scripts/Neelam/ui_press.py").read())
elif MODE == "pin":
    a = next(x for x in unreal.GameplayStatics.get_all_actors_of_class(gw, unreal.Actor) if x.get_actor_label() == ARG)
    a.call_method("Select_POI"); result = str(a.get_actor_location())
elif MODE == "state":
    cm = unreal.GameplayStatics.get_player_camera_manager(gw, 0); c = cm.get_camera_location(); pn = pc.get_controlled_pawn()
    ign = [pn]
    up_a, up_p = first_hit(c, c + unreal.Vector(0, 0, 30000), ign)
    dn_a, dn_p = first_hit(c, c - unreal.Vector(0, 0, 100000), ign)
    cesium = lambda a: a is not None and "Cesium" in a.get_class().get_name()
    under = cesium(up_a)
    inside = up_a is not None and not cesium(up_a) and up_a == dn_a
    result = {"cam": [round(c.x), round(c.y), round(c.z)], "pivot": [round(v) for v in (pn.get_actor_location().x, pn.get_actor_location().y, pn.get_actor_location().z)],
              "view_target": pc.get_view_target().get_name(), "pawn": pn.get_class().get_name(),
              "above": up_a.get_actor_label() if up_a else None, "below": dn_a.get_actor_label() if dn_a else None,
              "clear_m": round((c.z - dn_p.z) / 100, 1) if dn_p else None,
              "UNDER_MAP": under, "INSIDE": inside}
