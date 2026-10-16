"""Floor View gallery photos (client, 11 Oct 2026): drone views from the site per floor, Google Drive links
(5th / 10th / 15th / 20th / 30th + an unlabelled 6th = 40th) -> SourceArt/FloorView/FloorGallery/floor_<nn>.jpg (git-ignored)
-> /Game/Neelam/FloorView/Gallery/T_FloorGallery_<nn> -> Neelam_FlatTour.FloorGallery.
Floor View: select a floor -> the detail panel shows a "Floor Gallery" card (nearest floor's photo) -> full-screen viewer with CLOSE.
run(): import + assign, saves the level."""
import os, re
import unreal
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem); EAL = unreal.EditorAssetLibrary
SRC = os.path.join(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()), "SourceArt", "FloorView", "FloorGallery")
DST = "/Game/Neelam/FloorView/Gallery"

def run():
    views, out = [], []
    for f in sorted(os.listdir(SRC)):
        m = re.match(r"floor_(\d+)\.jpe?g$", f, re.I)
        if not m: continue
        fl = int(m.group(1)); name = "T_FloorGallery_%02d" % fl
        t = unreal.AssetImportTask(); t.filename = os.path.join(SRC, f); t.destination_path = DST; t.destination_name = name
        t.automated = True; t.replace_existing = True; t.save = False
        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t])
        tx = unreal.load_asset(DST + "/" + name)
        tx.set_editor_property("lod_group", unreal.TextureGroup.TEXTUREGROUP_UI)
        tx.set_editor_property("mip_gen_settings", unreal.TextureMipGenSettings.TMGS_NO_MIPMAPS)
        tx.set_editor_property("max_texture_size", 4096)
        tx.set_editor_property("never_stream", True)
        tx.set_editor_property("srgb", True)
        EAL.save_asset(tx.get_path_name())
        v = unreal.NeelamBalconyView(); v.set_editor_property("floor", fl); v.set_editor_property("day", tx)
        views.append(v); out.append("%s %dx%d" % (name, tx.blueprint_get_size_x(), tx.blueprint_get_size_y()))
    tour = next(a for a in EAS.get_all_level_actors() if isinstance(a, unreal.NeelamFlatTour))
    tour.set_editor_property("floor_gallery", views)
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    return out
