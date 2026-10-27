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


def import_all(src=SRC, suffix=""):
    """suffix "_UE" + src SourceArt/.../Panoramas/UE = the Room_render renders, imported SIDE BY SIDE (never assigned)"""
    out = []
    if not os.path.isdir(src):
        os.makedirs(src)
    tasks = []
    for f in sorted(os.listdir(src)):
        if os.path.isdir(os.path.join(src, f)): continue   # src/ = client originals
        aid, ext = os.path.splitext(f)
        if ext.lower() not in EXT:
            continue
        t = unreal.AssetImportTask()
        t.set_editor_property("filename", os.path.join(src, f))
        t.set_editor_property("destination_path", DEST)
        t.set_editor_property("destination_name", "T_Pano_Amenity_" + aid.lower() + suffix)
        t.set_editor_property("replace_existing", True)
        t.set_editor_property("automated", True)
        t.set_editor_property("save", False)
        tasks.append((aid.lower() + suffix, t))
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
        tex.set_editor_property("max_texture_size", 8192)
        EAL.save_asset(tex_path(aid))
        out.append((aid, tex_path(aid)))
    return out


def import_ue():
    return import_all(os.path.join(SRC, "UE"), "_UE")


def export_client(out_dir):
    """client pins' textures -> <out_dir>/<id>.png (for the before/after sheet)"""
    os.makedirs(out_dir, exist_ok=True)
    done = []
    for a in EAL.list_assets(DEST, recursive=False):
        n = a.split(".")[-1]
        if n.endswith("_UE"): continue
        t = unreal.AssetExportTask()
        t.set_editor_property("object", unreal.load_asset(a))
        t.set_editor_property("filename", os.path.join(out_dir, n[len("T_Pano_Amenity_"):] + ".png"))
        t.set_editor_property("automated", True); t.set_editor_property("prompt", False); t.set_editor_property("replace_identical", True)
        done.append((n, unreal.Exporter.run_asset_export_task(t)))
    return done


def assign(suffix="", keep=()):
    """Texture_360 of every Amenity_<id> pin = T_Pano_Amenity_<id><suffix> if it exists, else the client T_Pano_Amenity_<id>
    (else cleared). assign("_UE") = new Room_render panos; assign() = back to the client's."""
    out = []
    for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        lab = a.get_actor_label()
        if a.get_class().get_name() != "BP_POI_C" or not lab.startswith("Amenity_"):
            continue
        aid = lab[len("Amenity_"):]
        tp = tex_path(aid) + suffix if aid not in keep and EAL.does_asset_exist(tex_path(aid) + suffix) else tex_path(aid)
        tex = unreal.load_asset(tp) if EAL.does_asset_exist(tp) else None
        s = a.get_editor_property("POI_Info_Struct")
        # BP struct members have GUID names (Texture_360_86_<guid>) -> edit the exported text
        val = ("\"/Script/Engine.Texture2D'%s.%s'\"" % (tp, tp.rsplit("/", 1)[1])) if tex else "None"
        txt = re.sub(r'(Texture_360_[0-9A-Za-z_]+=)("[^"]*"|None)', lambda m: m.group(1) + val, s.export_text(), count=1)
        s.import_text(txt)
        a.set_editor_property("POI_Info_Struct", s)
        out.append((aid, tp.rsplit("/", 1)[1] if tex else None))
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    return out


def audit_assignments(suffix="_UE", keep=()):
    """Preview each amenity pin's panorama assignment without changing or saving the level."""
    out = []
    for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        lab = a.get_actor_label()
        if a.get_class().get_name() != "BP_POI_C" or not lab.startswith("Amenity_"):
            continue
        aid = lab[len("Amenity_"):]
        preferred = tex_path(aid) + suffix
        fallback = tex_path(aid)
        target = preferred if aid not in keep and EAL.does_asset_exist(preferred) else fallback
        struct = a.get_editor_property("POI_Info_Struct")
        match = re.search(r'Texture_360_[0-9A-Za-z_]+=("[^"]*"|None)', struct.export_text())
        current = match.group(1) if match else None
        target_exists = EAL.does_asset_exist(target)
        target_ref = ("/Script/Engine.Texture2D'%s.%s'" % (target, target.rsplit("/", 1)[1])) if target_exists else None
        out.append({
            "pin": aid,
            "current": current,
            "would_use": target_ref,
            "texture_exists": target_exists,
            "would_change": current != ('"' + target_ref + '"' if target_ref else "None"),
        })
    return out


def run():
    return {"imported": import_all(), "pins": assign()}
