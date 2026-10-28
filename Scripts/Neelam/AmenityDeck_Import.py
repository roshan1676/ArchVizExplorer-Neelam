"""Neelam amenity deck (28 Oct 2026): import SourceArt/AmenityDeck/export/<FBX> and place it in its own sublevel.
Bridge job, globals FBX (default "AD_Hardscape.fbx"), MODE "import" | "place" | "both".
- Meshes -> /Game/Neelam/AmenityDeck/Meshes (one static mesh per Blender object, pivot = deck origin), Nanite on except
  translucent/masked parts (glass, water, nets).
- Sublevel /Game/Neelam/AmenityDeck/Maps/L_AmenityDeck (always loaded) holds every AD_* actor, so this work never mixes
  with edits to Realistic_01 itself; only the sublevel package is saved here.
- Every actor sits at the deck origin: WindTunnel root xy (950, 4430), yaw 40, z 2477.5 (deck FFL)."""
import os
import unreal

FBX = globals().get("FBX", "AD_Hardscape.fbx"); MODE = globals().get("MODE", "both")
PROJ = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
SRC = os.path.join(PROJ, "SourceArt", "AmenityDeck", "export", FBX)
DST = "/Game/Neelam/AmenityDeck/Meshes"
SUB = "/Game/Neelam/AmenityDeck/Maps/L_AmenityDeck"
ORIGIN, YAW = unreal.Vector(950.0, 4430.0, 2477.5), 40.0
NO_NANITE = ("Glass", "Water", "Net", "Fence_", "Lights", "Rings", "Boards")
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
out = {}


def do_import():
    t = unreal.AssetImportTask()
    t.filename = SRC; t.destination_path = DST; t.automated = True; t.replace_existing = True; t.save = True
    o = unreal.FbxImportUI()
    o.import_mesh = True; o.import_materials = True; o.import_textures = False; o.import_as_skeletal = False
    o.mesh_type_to_import = unreal.FBXImportType.FBXIT_STATIC_MESH
    sm = o.static_mesh_import_data
    sm.combine_meshes = False; sm.auto_generate_collision = False; sm.generate_lightmap_u_vs = False
    sm.import_uniform_scale = 1.0; sm.normal_import_method = unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS_AND_TANGENTS
    sm.convert_scene = True; sm.force_front_x_axis = False
    sm.vertex_color_import_option = unreal.VertexColorImportOption.REPLACE
    t.options = o
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t])
    paths = [p for p in t.imported_object_paths]
    meshes = []
    for p in paths:
        a = unreal.load_asset(p)
        if isinstance(a, unreal.StaticMesh):
            meshes.append(a)
            ns = a.get_editor_property("nanite_settings")
            want = not any(k in a.get_name() for k in NO_NANITE)
            if ns.enabled != want:
                ns.enabled = want; a.set_editor_property("nanite_settings", ns)
            # simple box collision only for things people walk on / bump into (camera clamp ignores floors anyway)
            unreal.EditorAssetLibrary.save_loaded_asset(a)
    out["imported"] = len(meshes)
    return meshes


LES = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)


def sublevel():
    """Make sure L_AmenityDeck is in the world (always loaded) and make it the current level."""
    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    if not any(SUB in s.get_path_name() for s in unreal.EditorLevelUtils.get_levels(w)):
        if unreal.EditorAssetLibrary.does_asset_exist(SUB):
            unreal.EditorLevelUtils.add_level_to_world(w, SUB, unreal.LevelStreamingAlwaysLoaded)
        else:
            unreal.EditorLevelUtils.create_new_streaming_level(unreal.LevelStreamingAlwaysLoaded, SUB, False)
    LES.set_current_level_by_name("L_AmenityDeck")
    return next(s for s in unreal.EditorLevelUtils.get_levels(w) if SUB in s.get_path_name())


def place(meshes):
    lvl = sublevel()
    have = {a.get_actor_label(): a for a in EAS.get_all_level_actors() if a.get_actor_label().startswith("AD_")}
    n = 0
    for m in meshes:
        a = have.get(m.get_name())
        if a is None:
            a = EAS.spawn_actor_from_object(m, ORIGIN, unreal.Rotator(0.0, 0.0, YAW))
            a.set_actor_label(m.get_name()); n += 1
        a.set_actor_location_and_rotation(ORIGIN, unreal.Rotator(roll=0.0, pitch=0.0, yaw=YAW), False, True)
        a.set_folder_path("Neelam/AmenityDeck")
        a.static_mesh_component.set_editor_property("mobility", unreal.ComponentMobility.STATIC)
    cur = LES.get_current_level().get_path_name()
    if "L_AmenityDeck" not in cur:      # never save Realistic_01 itself from here
        raise RuntimeError("current level is %s, not the amenity sublevel - not saving" % cur)
    LES.save_current_level()
    out["spawned"] = n; out["level"] = lvl.get_path_name()
    # back to the persistent level as current so nobody else's spawns land in the sublevel
    LES.set_current_level_by_name("Realistic_01")


if MODE in ("import", "both"):
    ms = do_import()
else:
    ms = [unreal.load_asset(p) for p in unreal.EditorAssetLibrary.list_assets(DST, False, False)
          if isinstance(unreal.load_asset(p), unreal.StaticMesh)]
if MODE in ("place", "both"):
    place(ms)
result = out
