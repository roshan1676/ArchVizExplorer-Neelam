"""Re-link base colour / normal textures the glTF import dropped (materials came in plain white).
    import relink_gltf as RG; RG.run("Amenity_Pool")       # open level = that amenity
Reads SourceArt/<name>/scene.gltf, matches imported material instances by scene_builder.key(), imports the image
files into /Game/Neelam/<name>/FixTex, sets BaseColorTexture / NormalTexture, and moves alpha (BLEND / MASK) leaf
cards to the masked glTF parent so cut-outs show. Only touches MIs that are currently untextured."""
import os, re, json, urllib.parse
import unreal
import scene_builder as SB

MEL = unreal.MaterialEditingLibrary
EAL = unreal.EditorAssetLibrary
AT = unreal.AssetToolsHelpers.get_asset_tools()
MASK_PARENT = "/Interchange/gltf/MaterialInstances/MI_Default_Mask_DS"
IDENT = unreal.LinearColor(0, 0, 1, 1)


def _tex(path_on_disk, dest, srgb=True, normal=False):
    stem = re.sub(r"[^A-Za-z0-9_]", "_", os.path.splitext(os.path.basename(path_on_disk))[0])[:60]
    ap = "%s/T_%s" % (dest, stem)
    if not EAL.does_asset_exist(ap):
        t = unreal.AssetImportTask()
        t.filename, t.destination_path, t.destination_name = path_on_disk, dest, "T_" + stem
        t.automated, t.replace_existing = True, True
        AT.import_asset_tasks([t])
        tx = unreal.load_asset(ap)
        if tx and normal:
            tx.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_NORMALMAP)
            tx.set_editor_property("srgb", False)
        if tx: EAL.save_asset(ap)
    return unreal.load_asset(ap)


def _untextured(mi):
    try: t = MEL.get_material_instance_texture_parameter_value(mi, "BaseColorTexture")
    except Exception: t = None
    return t is None or t.get_name() == "T_White_srgb"


def run(name):
    src = SB.src(name)
    g = json.load(open(os.path.join(src, "scene.gltf"), encoding="utf-8"))
    tx, im = g.get("textures", []), g.get("images", [])
    uri = lambda i: os.path.join(src, urllib.parse.unquote(im[tx[i]["source"]]["uri"]))
    by_key = {}
    for m in g.get("materials", []):
        by_key.setdefault(SB.key(m["name"]), m)
    dest = "/Game/Neelam/%s/FixTex" % name
    done, missing, seen = [], set(), set()
    for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        if not isinstance(a, unreal.StaticMeshActor): continue
        for mi in a.static_mesh_component.get_materials():
            if not isinstance(mi, unreal.MaterialInstanceConstant) or mi.get_name() in seen: continue
            if mi.get_path_name().startswith("/Game/Neelam/PBR") or not _untextured(mi): continue
            seen.add(mi.get_name())
            k = SB.key(mi.get_name())
            gm = by_key.get(k) or by_key.get(re.sub(r"\d+$", "", k))   # UE adds _001 style suffixes
            b = gm and gm.get("pbrMetallicRoughness", {}).get("baseColorTexture")
            if not b or not os.path.exists(uri(b["index"])):
                missing.add(mi.get_name()); continue
            if gm.get("alphaMode", "OPAQUE") != "OPAQUE":
                mi.set_editor_property("parent", unreal.load_asset(MASK_PARENT))
            MEL.set_material_instance_texture_parameter_value(mi, "BaseColorTexture", _tex(uri(b["index"]), dest))
            MEL.set_material_instance_vector_parameter_value(mi, "BaseColorFactor", unreal.LinearColor(1, 1, 1, 1))
            MEL.set_material_instance_vector_parameter_value(mi, "BaseColorTexture_OffsetScale", IDENT)
            n = gm.get("normalTexture")
            if n and os.path.exists(uri(n["index"])):
                MEL.set_material_instance_texture_parameter_value(mi, "NormalTexture", _tex(uri(n["index"]), dest, normal=True))
                MEL.set_material_instance_vector_parameter_value(mi, "NormalTexture_OffsetScale", IDENT)
            EAL.save_loaded_asset(mi)
            done.append(mi.get_name())
    return {"relinked": done, "no_texture_in_gltf": sorted(missing)}
