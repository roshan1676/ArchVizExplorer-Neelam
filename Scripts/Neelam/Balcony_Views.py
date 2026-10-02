"""Balcony photo galleries + top-floor panorama (client, 2 Oct 2026).
Source: C:\\Users\\rosha\\Downloads\\neelam_balcony  (5th/10th/15th/20th/30th/40th .JPG + *_night.JPG, "panaroma from top.JPG")
 - copied to SourceArt/FloorView/Balcony (git-ignored), imported to /Game/Neelam/FloorView/Balcony/T_Balcony_<floor>_Day|Night
 - Neelam_FlatTour.BalconyViews = one set per floor -> a flat's Balcony room shows the photos of the NEAREST floor as a
   full-screen gallery with DAY / NIGHT (opens on night when the app is at night) instead of a panorama.
 - "panaroma from top" -> /Game/Neelam/FloorView/Textures/T_Pano_TopFloor, used by unit type TOPVIEW / flat E_41_TOP
   (FloorView_Setup.py: Tower E floor 41 = "Top Floor View" 360).
run(): step_import() then step_views() (needs the C++ BalconyViews property) and FloorView_Setup.step_tables()."""
import os, re, shutil
import unreal
EAL = unreal.EditorAssetLibrary
SRC = r"C:\Users\rosha\Downloads\neelam_balcony"
PROJ = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
LOCAL = os.path.join(PROJ, "SourceArt", "FloorView", "Balcony")
DST = "/Game/Neelam/FloorView/Balcony"
PANO_DST = "/Game/Neelam/FloorView/Textures"

def _files():
    d = SRC if os.path.isdir(SRC) else LOCAL
    out = {}
    for f in os.listdir(d):
        m = re.match(r"(\d+)(st|nd|rd|th)(_night)?\.jpe?g$", f, re.I)
        if m: out[(int(m.group(1)), bool(m.group(3)))] = os.path.join(d, f)
        elif "panaroma" in f.lower() or "panorama" in f.lower(): out["pano"] = os.path.join(d, f)
    return out

def _import(path, dest, name):
    os.makedirs(LOCAL, exist_ok=True)
    loc = os.path.join(LOCAL, os.path.basename(path))
    if os.path.abspath(path) != os.path.abspath(loc) and not os.path.exists(loc): shutil.copy2(path, loc)
    t = unreal.AssetImportTask(); t.filename = loc; t.destination_path = dest; t.destination_name = name
    t.automated = True; t.replace_existing = True; t.save = False
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t])
    return unreal.load_asset(dest + "/" + name)

def step_import():
    fs = _files(); out = []
    for k, p in sorted((k, v) for k, v in fs.items() if k != "pano"):
        fl, night = k; n = "T_Balcony_%02d_%s" % (fl, "Night" if night else "Day")
        tx = _import(p, DST, n)
        tx.set_editor_property("lod_group", unreal.TextureGroup.TEXTUREGROUP_UI)
        tx.set_editor_property("mip_gen_settings", unreal.TextureMipGenSettings.TMGS_NO_MIPMAPS)
        tx.set_editor_property("max_texture_size", 3840)
        tx.set_editor_property("srgb", True)
        EAL.save_asset(tx.get_path_name()); out.append(n)
    if "pano" in fs:
        tx = _import(fs["pano"], PANO_DST, "T_Pano_TopFloor")
        tx.set_editor_property("lod_group", unreal.TextureGroup.TEXTUREGROUP_SKYBOX)
        tx.set_editor_property("mip_gen_settings", unreal.TextureMipGenSettings.TMGS_NO_MIPMAPS)
        tx.set_editor_property("max_texture_size", 8192)
        tx.set_editor_property("never_stream", True)
        EAL.save_asset(tx.get_path_name()); out.append("T_Pano_TopFloor %dx%d" % (tx.blueprint_get_size_x(), tx.blueprint_get_size_y()))
    return out

def step_views():
    fs = _files(); floors = sorted({k[0] for k in fs if k != "pano"})
    views = []
    for fl in floors:
        v = unreal.NeelamBalconyView(); v.set_editor_property("floor", fl)
        for night, prop in ((False, "day"), (True, "night")):
            p = "%s/T_Balcony_%02d_%s" % (DST, fl, "Night" if night else "Day")
            if EAL.does_asset_exist(p): v.set_editor_property(prop, unreal.load_asset(p))
        views.append(v)
    m = [a for a in unreal.EditorLevelLibrary.get_all_level_actors() if a.get_class().get_name() == "NeelamFlatTour"][0]
    m.set_editor_property("balcony_views", views)
    unreal.EditorLevelLibrary.save_current_level()
    return floors
