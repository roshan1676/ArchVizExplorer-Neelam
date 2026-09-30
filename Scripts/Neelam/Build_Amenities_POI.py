"""Neelam - Amenities menu pins (BP_POI) on the CDE amenity deck + AB roof deck.  Re-run safe.
Each pin carries tags Amenities + its list tag (Leisure / Fitness / Facilities) so BP_Amenities_Widget lists it
and BP_MasterMenu shows it only while the Amenities menu is open. POI_Geometry (hologram box) = the amenity footprint.
Positions: top-down capture of the deck (30 Sep), deck axes yaw 40. Add new amenities to AMENITIES below."""
import math
import unreal
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
POI = unreal.EditorAssetLibrary.load_blueprint_class("/Game/ArchVizExplorer/Blueprints/BP_POI")
FOLDER = "Neelam/Amenities_POI"
ICONS = "/Game/ArchVizExplorer/Textures/UI/Icons/"
DECK_Z, ABDECK_Z = 2480.0, 3768.0
HOLO = "/Game/Neelam/Materials/FX/MI_Neelam_HoloFX"
BOX_YAW = 130.0                       # box X along the deck's long edge (screen left-right in the Amenities view)
LISTS = {  # list widget in BP_Amenities_Widget -> (tag, title, colour)
    "BP_POI_List_Leisure":        ("Leisure",    "LEISURE",    (0.85, 0.35, 0.20)),
    "BP_POI_List_Fitness":        ("Fitness",    "FITNESS",    (0.00, 0.74, 0.86)),
    "BP_POI_List_Transportation": ("Facilities", "FACILITIES", (0.95, 0.70, 0.25)),
}
CAT_COLOR = {v[0]: v[2] for v in LISTS.values()}
CAM = {"parking": (-12.0, 7000.0), "track": (-40.0, 7500.0), "sky": (-35.0, 5000.0)}   # per-pin (pitch, arm) overrides
# id, name, info, footer, list tag, icon, (x, y, base z), box (w along yaw 130, d along yaw 40, h) in m
AMENITIES = [
    ("court",   "Multipurpose Court",        "Basketball / multi-sport court",       "Floodlit, fenced",            "Fitness",    "T_Icon_Fitness_01", (7860, 5455, DECK_Z), (31, 18, 4)),
    ("padel",   "Sports Court",              "Tennis / padel court",                 "Floodlit, fenced",            "Fitness",    "T_Icon_Fitness_01", (5398, 4820, DECK_Z), (9.5, 20, 4)),
    ("track",   "Jogging Track & Walkways",  "Paved loop around the podium deck",    "Lit walkways",                "Fitness",    "T_Icon_Fitness_01", (7164, 4486, DECK_Z), (45, 3, 1)),
    ("lawn",    "Party Lawn",                "Lawn with landscaped garden",          "Events & gatherings",         "Leisure",    "T_Icon_Nature_01",  (6020, 3714, DECK_Z), (11.5, 15.5, 1.5)),
    ("pool",    "Swimming Pool",             "Lap pool with deck",                   "Pool lighting at night",      "Leisure",    "T_Icon_Pool_01",    (4029, 1469, DECK_Z), (14.5, 31, 1.5)),
    ("toddler", "Toddler's Pool",            "Shallow pool for kids",                "Next to the main pool",       "Leisure",    "T_Icon_Pool_01",    (4907, 1931, DECK_Z), (9.5, 11, 1.5)),
    ("pergola", "Pergola Lounge",            "Shaded seating by the pool",           "Poolside",                    "Leisure",    "T_Icon_Dining_01",  (3956, 2343, DECK_Z), (7, 26, 3.5)),
    ("garden",  "Landscaped Garden",         "Green walk beside the pool",           "Planting & trees",            "Leisure",    "T_Icon_Nature_01",  (3074, 2869, DECK_Z), (9.5, 36, 1.5)),
    ("sky",     "Sky Garden",                "Rooftop lawn with pergola",            "Podium roof, Towers A & B",   "Leisure",    "T_Icon_Nature_01",  (1173, -467, ABDECK_Z), (20, 20, 3)),
    ("parking", "Multi-level Parking",       "Podium parking levels",                "Below the amenity deck",      "Facilities", "T_Icon_Parking_01", (4753, 755, 1300), (2, 30, 7)),
]


def txt(s):
    return 'INVTEXT("%s")' % s.replace('"', "'")


def set_info(poi, name, info, footer, color, icon):
    s = poi.get_editor_property("POI_Info_Struct")
    ico = "\"/Script/Engine.Texture2D'%s%s.%s'\"" % (ICONS, icon, icon)
    s.import_text("(Name_25_4748782941ED18FE2304D484A513143E=%s,Information_27_C6F10FCE43C331CB9E996BA1CC9C8519=%s,"
                  "Footer_48_614C73F541F0F937071671A9E3E3A90B=\"%s\",Color_31_7C59AD004573552ECE0FA9BA31C6F514=(R=%f,G=%f,B=%f,A=1.0),"
                  "Icon_34_E4C0A1FB4BCEA6793DD975B5EE116A1C=%s)" % (txt(name), txt(info), footer, color[0], color[1], color[2], ico))
    poi.set_editor_property("POI_Info_Struct", s)


def step_lists():
    """rename the 3rd list Transportation -> Facilities, set tags / colours"""
    path = "/Game/ArchVizExplorer/Blueprints/Widgets/BP_Amenities_Widget"
    bp = unreal.load_asset(path)
    for wname, (tag, title, col) in LISTS.items():
        w = unreal.find_object(None, path + ".BP_Amenities_Widget:WidgetTree." + wname)
        w.set_editor_property("TagOfActors", unreal.Name(tag))
        w.set_editor_property("NameOfList", title)
        w.set_editor_property("List_Color", unreal.LinearColor(col[0], col[1], col[2], 1.0))
    r = unreal.NeelamToolsLibrary.compile_and_report(bp)
    unreal.EditorLoadingAndSavingUtils.save_packages([bp.get_outermost()], False)
    return r


def step_pois():
    for a in [a for a in EAS.get_all_level_actors() if str(a.get_folder_path()).startswith(FOLDER)]:
        EAS.destroy_actor(a)
    out = []
    for aid, name, info, footer, cat, icon, (x, y, z), (w, d, h) in AMENITIES:
        a = EAS.spawn_actor_from_class(POI, unreal.Vector(x, y, z + 150))
        a.set_actor_label("Amenity_" + aid); a.set_folder_path(FOLDER)
        set_info(a, name, info, footer, CAT_COLOR[cat], icon)
        a.set_editor_property("Widget_Text_Color", unreal.LinearColor(1, 1, 1, 1))
        a.tags = [unreal.Name(t) for t in ("Amenities", cat, "Neelam_Amenities", "Neelam_Amenity_" + aid)]
        for k in ("Change_Yaw?", "Change_Pitch?", "Change_Distance?"):
            a.set_editor_property(k, True)
        # camera when the pin is picked: BP_POI construction aims its SpringArm at LookAt_Target_Location and
        # Select_POI copies that rotation + arm length to the pawn (Change_* on) -> put the target in front, below
        pitch, arm = CAM.get(aid, (-35.0, 3500.0 + 60.0 * max(w, d)))
        p, yw = math.radians(pitch), math.radians(BOX_YAW)
        loc = a.get_actor_location()
        tgt = unreal.Vector(loc.x + 10000 * math.cos(p) * math.cos(yw), loc.y + 10000 * math.cos(p) * math.sin(yw), loc.z + 10000 * math.sin(p))
        a.set_editor_property("LookAt_Target_Location", tgt)
        a.set_editor_property("Use_LookAt_Target?", True)
        for sa in a.get_components_by_class(unreal.SpringArmComponent):
            sa.set_editor_property("target_arm_length", arm)
        geo = [c for c in a.get_components_by_class(unreal.StaticMeshComponent) if c.get_name() == "POI_Geometry"][0]
        geo.set_world_location_and_rotation(unreal.Vector(x, y, z + h * 50), unreal.Rotator(roll=0.0, pitch=0.0, yaw=BOX_YAW), False, False)
        geo.set_world_scale3d(unreal.Vector(w, d, h))
        if unreal.EditorAssetLibrary.does_asset_exist(HOLO):
            geo.set_material(0, unreal.load_asset(HOLO))   # Build_HoloFX.py premium hologram
        out.append(a.get_actor_label())
    try:   # 360 panoramas: SourceArt/Amenities/Panoramas/<id>.jpg -> Amenity_Panoramas.py
        import importlib, Amenity_Panoramas as AP; importlib.reload(AP); AP.assign()
    except Exception as e:
        unreal.log_warning("amenity panoramas: %s" % e)
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    return out


def run():
    return {"lists": step_lists(), "pois": step_pois()}
