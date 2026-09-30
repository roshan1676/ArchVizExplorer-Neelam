"""Neelam - 360 panoramas for the Amenities pins (re-run safe).
HOW TO ADD ONE:
  1. Save the equirectangular panorama (2:1, jpg/png/hdr/exr) as
       SourceArt/Amenities/Panoramas/<id>.jpg      e.g. pool.jpg, court.jpg, sky.jpg
     ids = the pins in Build_Amenities_POI.AMENITIES: court padel track lawn pool toddler pergola garden sky parking
     (a new amenity just needs its row there with the same id).
  2. Run  run()  (bridge job or Python console):  imports -> /Game/Neelam/Amenities/Panoramas/T_Pano_Amenity_<id>
     and puts it on the pin (POI_Info_Struct.Texture_360). Save.
  In the app: pick the amenity -> the info card shows the 360 button -> 360 view (template 360 pawn).
  Manual way: select the pin Amenity_<id> in the Outliner -> Details -> POI Info Struct -> Texture 360.
Removing the file + re-running clears nothing (safe); to remove a pano, delete the texture asset and run assign()."""
import os, re
import unreal
EAL = unreal.EditorAssetLibrary
PROJ = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
SRC = os.path.join(PROJ, "SourceArt", "Amenities", "Panoramas")
DEST = "/Game/Neelam/Amenities/Panoramas"
EXT = (".jpg", ".jpeg", ".png", ".hdr", ".exr", ".tga")


def tex_path(aid):
    return "%s/T_Pano_Amenity_%s" % (DEST, aid)


def import_all():
    out = []
    if not os.path.isdir(SRC):
        os.makedirs(SRC)
    tasks = []
    for f in sorted(os.listdir(SRC)):
        aid, ext = os.path.splitext(f)
        if ext.lower() not in EXT:
            continue
        t = unreal.AssetImportTask()
        t.set_editor_property("filename", os.path.join(SRC, f))
        t.set_editor_property("destination_path", DEST)
        t.set_editor_property("destination_name", "T_Pano_Amenity_" + aid.lower())
        t.set_editor_property("replace_existing", True)
        t.set_editor_property("automated", True)
        t.set_editor_property("save", False)
        tasks.append((aid.lower(), t))
    if tasks:
        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t for _, t in tasks])
    for aid, t in tasks:
        tex = unreal.load_asset(tex_path(aid))
        if not tex:
            out.append((aid, "import failed")); continue
        # same settings as the Floor View panoramas (sharp, never streamed / blurred)
        tex.set_editor_property("lod_group", unreal.TextureGroup.TEXTUREGROUP_SKYBOX)
        tex.set_editor_property("never_stream", True)
        tex.set_editor_property("power_of_two_mode", unreal.TexturePowerOfTwoSetting.NONE)
        tex.set_editor_property("mip_gen_settings", unreal.TextureMipGenSettings.TMGS_NO_MIPMAPS)
        EAL.save_asset(tex_path(aid))
        out.append((aid, tex_path(aid)))
    return out


def assign():
    """Texture_360 of every Amenity_<id> pin = T_Pano_Amenity_<id> if that texture exists (else cleared)"""
    out = []
    for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        lab = a.get_actor_label()
        if a.get_class().get_name() != "BP_POI_C" or not lab.startswith("Amenity_"):
            continue
        aid = lab[len("Amenity_"):]
        tex = unreal.load_asset(tex_path(aid)) if EAL.does_asset_exist(tex_path(aid)) else None
        s = a.get_editor_property("POI_Info_Struct")
        # BP struct members have GUID names (Texture_360_86_<guid>) -> edit the exported text
        val = ("\"/Script/Engine.Texture2D'%s.%s'\"" % (tex_path(aid), tex_path(aid).rsplit("/", 1)[1])) if tex else "None"
        txt = re.sub(r'(Texture_360_[0-9A-Za-z_]+=)("[^"]*"|None)', lambda m: m.group(1) + val, s.export_text(), count=1)
        s.import_text(txt)
        a.set_editor_property("POI_Info_Struct", s)
        out.append((aid, bool(tex)))
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    return out


def run():
    return {"imported": import_all(), "pins": assign()}
