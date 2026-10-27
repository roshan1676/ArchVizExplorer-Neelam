"""Rebuild a Blender scene (exported by Tools/blend_export.py) in the open editor.
Bridge job:   import scene_builder as SB; result = SB.build("2BHK")
Steps can also be run one at a time: new_level, import_meshes, nanite, fix_materials, place_lights, place_cameras.

Units: Cycles scene value 1.0 == UE luminance 1.2 nits at EV100 0 (manual exposure in the post volume),
so every Cycles W -> UE physical unit below carries K = 1.2.  Tune K in one place if UE reads darker/brighter.
"""
import unreal, json, math, os, re

K = 1.2
PROJ = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
ACT = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
LES = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
EAL = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary
AT = unreal.AssetToolsHelpers.get_asset_tools()

def src(name): return os.path.join(PROJ, "SourceArt", name)
def data(name): return json.load(open(os.path.join(src(name), "scene.json"), encoding="utf-8"))
def root(name): return "/Game/Neelam/" + name
def key(s): return re.sub(r"[^a-z0-9]", "", str(s).lower())
GLASSY = re.compile(r"glass|vidro|liquid|water|wine|drink|transp|crystal|diamond", re.I)

# ---------- Blender (Z-up, m, -Y fwd)  ->  UE (Z-up, cm, left-handed) ----------
def bv(v): return unreal.Vector(v[0] * 100.0, -v[1] * 100.0, v[2] * 100.0)
def bdir(v): return unreal.Vector(v[0], -v[1], v[2])
def xform(m, fwd_axis=2, fwd_sign=-1, up_axis=1):
    """Blender world matrix (row lists) -> (UE location, UE rotator). Lights/cameras look down local -Z, up +Y."""
    col = lambda i: [m[0][i], m[1][i], m[2][i]]
    f = [fwd_sign * c for c in col(fwd_axis)]
    loc = bv(col(3))
    rot = unreal.MathLibrary.make_rot_from_xz(bdir(f), bdir(col(up_axis)))
    return loc, rot

# ---------- level ----------
def new_level(name):
    path = root(name) + "/L_" + name
    if EAL.does_asset_exist(path):
        LES.load_level(path)
    else:
        LES.new_level(path, False)
    return path

# ---------- meshes ----------
def import_meshes(name):
    """Interchange glTF scene import -> assets in <root>/Assets and actors in the current level."""
    gltf = os.path.join(src(name), "scene.gltf")
    mgr = unreal.InterchangeManager.get_interchange_manager_scripted()
    params = unreal.ImportAssetParameters()
    params.is_automated = True
    ok = mgr.import_scene(root(name) + "/Assets", unreal.InterchangeManager.create_source_data(gltf), params)
    return {"import_scene": str(ok)}

def _meshes(name):
    reg = unreal.AssetRegistryHelpers.get_asset_registry()
    f = unreal.ARFilter(package_paths=[root(name) + "/Assets"], recursive_paths=True, class_paths=[unreal.TopLevelAssetPath("/Script/Engine", "StaticMesh")])
    return [a.get_asset() for a in reg.get_assets(f)]

def nanite(name, min_tris=2000):
    sms = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
    done = 0
    for m in _meshes(name):
        if sms.get_number_verts(m, 0) < min_tris:  # ponytail: tiny meshes stay plain, Nanite gains nothing there
            continue
        ns = m.get_editor_property("nanite_settings")
        if ns.enabled: continue
        ns.enabled = True
        sms.set_nanite_settings(m, ns, apply_changes=True)
        done += 1
    return {"nanite_enabled": done}

# ---------- materials ----------
def _master(kind):
    """Small master materials for what glTF can't carry: Cycles glass and emission."""
    path = "/Game/Neelam/Shared/M_" + kind
    if EAL.does_asset_exist(path): return EAL.load_asset(path)
    m = AT.create_asset("M_" + kind, "/Game/Neelam/Shared", unreal.Material, unreal.MaterialFactoryNew())
    col = MEL.create_material_expression(m, unreal.MaterialExpressionVectorParameter, -600, 0)
    col.set_editor_property("parameter_name", "Color"); col.set_editor_property("default_value", unreal.LinearColor(1, 1, 1, 1))
    if kind == "Glass":
        m.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
        m.set_editor_property("translucency_lighting_mode", unreal.TranslucencyLightingMode.TLM_SURFACE_PER_PIXEL_LIGHTING)
        rough = MEL.create_material_expression(m, unreal.MaterialExpressionScalarParameter, -600, 200)
        rough.set_editor_property("parameter_name", "Roughness"); rough.set_editor_property("default_value", 0.02)
        op = MEL.create_material_expression(m, unreal.MaterialExpressionScalarParameter, -600, 300)
        op.set_editor_property("parameter_name", "Opacity"); op.set_editor_property("default_value", 0.15)
        ior = MEL.create_material_expression(m, unreal.MaterialExpressionScalarParameter, -600, 400)
        ior.set_editor_property("parameter_name", "IOR"); ior.set_editor_property("default_value", 1.45)
        MEL.connect_material_property(col, "", unreal.MaterialProperty.MP_BASE_COLOR)
        MEL.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
        MEL.connect_material_property(op, "", unreal.MaterialProperty.MP_OPACITY)
        MEL.connect_material_property(ior, "", unreal.MaterialProperty.MP_REFRACTION)
        spec = MEL.create_material_expression(m, unreal.MaterialExpressionConstant, -600, 500)
        spec.set_editor_property("r", 1.0)
        MEL.connect_material_property(spec, "", unreal.MaterialProperty.MP_SPECULAR)
    else:  # Emissive
        s = MEL.create_material_expression(m, unreal.MaterialExpressionScalarParameter, -600, 200)
        s.set_editor_property("parameter_name", "Strength"); s.set_editor_property("default_value", 1.0)
        mul = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, -300, 100)
        MEL.connect_material_expressions(col, "", mul, "A"); MEL.connect_material_expressions(s, "", mul, "B")
        MEL.connect_material_property(mul, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
        MEL.connect_material_property(col, "", unreal.MaterialProperty.MP_BASE_COLOR)
    MEL.recompile_material(m)
    EAL.save_loaded_asset(m)
    return m

def _mi(name, kind, info):
    folder = root(name) + "/Materials_UE"
    path = folder + "/MI_" + key(info["_name"])
    mi = EAL.load_asset(path) if EAL.does_asset_exist(path) else \
        AT.create_asset("MI_" + key(info["_name"]), folder, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    MEL.set_material_instance_parent(mi, _master(kind))
    c = info.get("color") or info.get("viewport_color") or [1, 1, 1]
    if kind == "Glass" and max(c) < 0.2: c = [0.92, 0.95, 0.95]   # linked/unknown glass colour -> clear, not opaque black
    MEL.set_material_instance_vector_parameter_value(mi, "Color", unreal.LinearColor(c[0], c[1], c[2], 1))
    if kind == "Glass":
        MEL.set_material_instance_scalar_parameter_value(mi, "Roughness", info.get("roughness") or 0.02)
        MEL.set_material_instance_scalar_parameter_value(mi, "IOR", info.get("ior") or 1.45)
    else:
        MEL.set_material_instance_scalar_parameter_value(mi, "Strength", K * (info.get("strength") or 1.0))
    EAL.save_loaded_asset(mi)
    return mi

def fix_materials(name):
    """Swap glTF materials whose Blender source was glass / emission for the UE masters above."""
    mats = data(name)["materials"]
    special = {}
    for n, info in mats.items():
        if info["kind"] == "emissive" or (info["kind"] == "glass" and (info.get("color") is not None or GLASSY.search(n))):
            info["_name"] = n
            special[key(n)] = (info["kind"], info)
    made, swapped = {}, 0
    # undo earlier swaps that are no longer special (leaf cutouts, fabrics... were once flagged as glass)
    reg = unreal.AssetRegistryHelpers.get_asset_registry()
    f = unreal.ARFilter(package_paths=[root(name) + "/Assets"], recursive_paths=True,
                        class_paths=[unreal.TopLevelAssetPath("/Script/Engine", "MaterialInstanceConstant")])
    orig = {key(a.asset_name): a.get_asset() for a in reg.get_assets(f)}
    restored = 0
    for m in _meshes(name):
        sm = m.get_editor_property("static_materials"); ch = False
        for sl in sm:
            cur = sl.get_editor_property("material_interface")
            if cur and cur.get_path_name().startswith(root(name) + "/Materials_UE/"):
                k = key(cur.get_name())[2:]
                if k not in special and k in orig:
                    sl.set_editor_property("material_interface", orig[k]); ch = True; restored += 1
        if ch: m.set_editor_property("static_materials", sm); EAL.save_loaded_asset(m)
    for a in ACT.get_all_level_actors():
        c = a.get_component_by_class(unreal.StaticMeshComponent)
        if not c: continue
        for i, cur in enumerate(c.get_materials()):
            if cur and cur.get_path_name().startswith(root(name) + "/Materials_UE/"):
                k = key(cur.get_name())[2:]
                if k not in special and k in orig: c.set_material(i, orig[k]); restored += 1
    for m in _meshes(name):
        sm = m.get_editor_property("static_materials")
        changed = False
        for s in sm:
            cur = s.get_editor_property("material_interface")
            names = [key(str(s.get_editor_property("material_slot_name")))]
            if cur: names.append(key(cur.get_name()).removeprefix("mi"))
            hit = next((special[k] for k in names if k in special), None)
            if not hit: continue
            kind, info = hit
            k = key(info["_name"])
            if k not in made: made[k] = _mi(name, "Glass" if kind == "glass" else "Emissive", info)
            s.set_editor_property("material_interface", made[k]); changed = True; swapped += 1
        if changed:
            m.set_editor_property("static_materials", sm)
            EAL.save_loaded_asset(m)
    # Interchange also writes the materials onto each actor as overrides -> swap those too
    for k, (kind, info) in special.items():
        if k not in made: made[k] = _mi(name, "Glass" if kind == "glass" else "Emissive", info)
    for a in ACT.get_all_level_actors():
        c = a.get_component_by_class(unreal.StaticMeshComponent)
        if not c: continue
        for i, cur in enumerate(c.get_materials()):
            if cur and key(cur.get_name()) in made and cur != made[key(cur.get_name())]:
                c.set_material(i, made[key(cur.get_name())]); swapped += 1
    return {"special_materials": len(special), "instances": len(made), "slots_swapped": swapped, "restored": restored}

def apply_bakes(name):
    """Plug Blender-baked base colour / roughness (Tools/bake_mats.py) into the Interchange material instances."""
    bdir = os.path.join(src(name), "baked")
    baked = json.load(open(os.path.join(bdir, "baked.json"), encoding="utf-8"))
    reg = unreal.AssetRegistryHelpers.get_asset_registry()
    f = unreal.ARFilter(package_paths=[root(name) + "/Assets"], recursive_paths=True,
                        class_paths=[unreal.TopLevelAssetPath("/Script/Engine", "MaterialInstanceConstant")])
    mis = {key(a.asset_name): a.get_asset() for a in reg.get_assets(f)}
    tasks, todo = [], []
    for mat, e in baked.items():
        mi = mis.get(key(mat))
        if not mi or "bc" not in e: continue
        for t in ("bc", "mr"):
            if t in e:
                task = unreal.AssetImportTask()
                task.filename = os.path.join(bdir, e[t]); task.destination_path = root(name) + "/Baked"
                task.automated = True; task.replace_existing = True; task.save = True
                tasks.append(task)
        todo.append((mi, e))
    AT.import_asset_tasks(tasks)
    ident = unreal.LinearColor(0, 0, 1, 1)  # offset 0,0 scale 1,1 -> bake already includes the Blender Mapping node
    done = 0
    for mi, e in todo:
        bc = EAL.load_asset(root(name) + "/Baked/" + os.path.splitext(e["bc"])[0])
        MEL.set_material_instance_texture_parameter_value(mi, "BaseColorTexture", bc)
        MEL.set_material_instance_vector_parameter_value(mi, "BaseColorFactor", unreal.LinearColor(1, 1, 1, 1))
        MEL.set_material_instance_vector_parameter_value(mi, "BaseColorTexture_OffsetScale", ident)
        if "mr" in e:
            mr = EAL.load_asset(root(name) + "/Baked/" + os.path.splitext(e["mr"])[0])
            mr.set_editor_property("srgb", False)
            mr.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_MASKS)
            MEL.set_material_instance_texture_parameter_value(mi, "MetallicRoughnessTexture", mr)
            MEL.set_material_instance_vector_parameter_value(mi, "MetallicRoughnessTexture_OffsetScale", ident)
            MEL.set_material_instance_scalar_parameter_value(mi, "RoughnessFactor", 1.0)
            MEL.set_material_instance_scalar_parameter_value(mi, "MetallicFactor", e.get("metallic", 0.0))
        EAL.save_loaded_asset(mi)
        done += 1
    return {"baked_materials": len(baked), "patched": done, "unmatched": [m for m in baked if key(m) not in mis][:20]}

# ---------- lights ----------
def _clear(tag):
    for a in ACT.get_all_level_actors():
        if tag in [str(t) for t in a.tags]: ACT.destroy_actor(a)

def place_lights(name):
    d = data(name); tag = "bl_light"
    _clear(tag)
    n = 0
    for L in d["lights"]:
        loc, rot = xform(L["matrix"])
        col = unreal.LinearColor(*L["color"], 1)
        t, W = L["type"], L["W"]
        if t == "SUN":
            a = ACT.spawn_actor_from_class(unreal.DirectionalLight, loc, rot); c = a.light_component
            c.set_intensity(K * W)  # lux
            c.set_editor_property("light_source_angle", math.degrees(L.get("angle", 0.01)))
            c.set_editor_property("atmosphere_sun_light", False)
        elif t == "AREA":
            a = ACT.spawn_actor_from_class(unreal.RectLight, loc, rot); c = a.light_component
            sx, sy = L["size"], (L["size_y"] if L["shape"] in ("RECTANGLE", "ELLIPSE") else L["size"])
            area = sx * sy * (math.pi / 4 if L["shape"] in ("DISK", "ELLIPSE") else 1)
            c.set_editor_property("intensity_units", unreal.LightUnits.NITS)
            c.set_intensity(K * W / (math.pi * max(area, 1e-4)))
            c.set_editor_property("source_width", sx * 100); c.set_editor_property("source_height", sy * 100)
            c.set_editor_property("barn_door_angle", min(90.0, math.degrees(L.get("spread", math.pi)) / 2))
            c.set_editor_property("attenuation_radius", 2000.0)
        elif t in ("POINT", "SPOT"):
            cls = unreal.SpotLight if t == "SPOT" else unreal.PointLight
            a = ACT.spawn_actor_from_class(cls, loc, rot); c = a.light_component
            c.set_editor_property("intensity_units", unreal.LightUnits.CANDELAS)
            c.set_intensity(K * W / (4 * math.pi))
            c.set_editor_property("source_radius", L.get("soft_size", 0) * 100)
            c.set_editor_property("attenuation_radius", 2000.0)
            if t == "SPOT":
                half = math.degrees(L["spot_size"]) / 2
                c.set_editor_property("outer_cone_angle", half)
                c.set_editor_property("inner_cone_angle", half * (1 - L["spot_blend"]))
        else:
            continue
        c.set_light_color(col)
        a.set_actor_label("BL_" + L["name"]); a.tags = [tag]; a.set_folder_path("Blender/Lights")
        n += 1
    return {"lights": n}

# ---------- cameras + environment ----------
def place_cameras(name):
    d = data(name); tag = "bl_cam"
    _clear(tag)
    w, h = d["res"]; out = []
    for C in d["cameras"]:
        loc, rot = xform(C["matrix"])
        a = ACT.spawn_actor_from_class(unreal.CineCameraActor, loc, rot)
        cc = a.get_cine_camera_component()
        fb = cc.get_editor_property("filmback")
        sw = C["sensor"] if (C["sensor_fit"] != "VERTICAL" and w >= h) else C["sensor"] * w / h
        fb.sensor_width = sw; fb.sensor_height = sw * h / w
        cc.set_editor_property("filmback", fb)
        cc.set_editor_property("current_focal_length", C["lens"])
        fs = cc.get_editor_property("focus_settings")
        fs.focus_method = unreal.CameraFocusMethod.MANUAL if C["dof"] else unreal.CameraFocusMethod.DISABLE
        fs.manual_focus_distance = max(C["focus"], 0.1) * 100
        cc.set_editor_property("focus_settings", fs)
        cc.set_editor_property("current_aperture", C["fstop"] if C["dof"] else 22.0)
        a.set_actor_label("BL_" + C["name"]); a.tags = [tag]; a.set_folder_path("Blender/Cameras")
        out.append(a.get_actor_label())
    return {"cameras": out}

def _sky_material():
    """Unlit two-sided material that shows a cubemap in the view direction (sky sphere seen from inside)."""
    path = "/Game/Neelam/Shared/M_HDRISky"
    if EAL.does_asset_exist(path): return EAL.load_asset(path)
    m = AT.create_asset("M_HDRISky", "/Game/Neelam/Shared", unreal.Material, unreal.MaterialFactoryNew())
    m.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    m.set_editor_property("two_sided", True)
    cv = MEL.create_material_expression(m, unreal.MaterialExpressionCameraVectorWS, -900, 0)
    neg = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, -700, 0)
    neg.set_editor_property("const_b", -1.0)
    MEL.connect_material_expressions(cv, "", neg, "A")
    tex = MEL.create_material_expression(m, unreal.MaterialExpressionTextureSampleParameterCube, -500, 0)
    tex.set_editor_property("parameter_name", "Sky")
    tex.set_editor_property("texture", unreal.load_asset("/Engine/MapTemplates/Sky/SunsetAmbientCubemap"))
    MEL.connect_material_expressions(neg, "", tex, "UVs")
    st = MEL.create_material_expression(m, unreal.MaterialExpressionScalarParameter, -500, 250)
    st.set_editor_property("parameter_name", "Strength"); st.set_editor_property("default_value", 1.0)
    mul = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, -250, 100)
    MEL.connect_material_expressions(tex, "RGB", mul, "A"); MEL.connect_material_expressions(st, "", mul, "B")
    MEL.connect_material_property(mul, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    MEL.recompile_material(m); EAL.save_loaded_asset(m)
    return m

def environment(name, sky_yaw=0.0):
    """Manual-exposure post volume (EV100 0 == Cycles exposure 0) + Blender world HDRI as sky light and visible sky sphere.
    sky_yaw: degrees to spin the HDRI if the view out of the windows doesn't line up with Blender. Re-runnable."""
    tag = "bl_env"
    _clear(tag)
    w = json.load(open(os.path.join(src(name), "world.json")))
    task = unreal.AssetImportTask()
    task.filename = os.path.join(src(name), "sky.hdr"); task.destination_path = root(name) + "/Env"
    task.destination_name = "T_Sky_" + name; task.automated = True; task.replace_existing = True; task.save = True
    AT.import_asset_tasks([task])
    cube = EAL.load_asset(root(name) + "/Env/T_Sky_" + name)
    yaw = math.degrees(w.get("rot_z", 0.0)) + sky_yaw

    pp = ACT.spawn_actor_from_class(unreal.PostProcessVolume, unreal.Vector(0, 0, 0))
    pp.set_editor_property("unbound", True)
    s = pp.get_editor_property("settings")
    s.set_editor_property("override_auto_exposure_method", True); s.set_editor_property("auto_exposure_method", unreal.AutoExposureMethod.AEM_MANUAL)
    s.set_editor_property("override_auto_exposure_apply_physical_camera_exposure", True); s.set_editor_property("auto_exposure_apply_physical_camera_exposure", False)
    s.set_editor_property("override_auto_exposure_bias", True); s.set_editor_property("auto_exposure_bias", 0.0)
    pp.set_editor_property("settings", s)

    sky = ACT.spawn_actor_from_class(unreal.SkyLight, unreal.Vector(0, 0, 500))
    sl = sky.light_component
    sl.set_editor_property("source_type", unreal.SkyLightSourceType.SLS_SPECIFIED_CUBEMAP)
    sl.set_editor_property("cubemap", cube)
    sl.set_editor_property("source_cubemap_angle", yaw)
    sl.set_editor_property("intensity", K * w["strength"])
    sl.set_editor_property("real_time_capture", False)
    sl.recapture_sky()

    sph = ACT.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(0, 0, 0), unreal.Rotator(roll=0, pitch=0, yaw=yaw))
    sph.set_actor_scale3d(unreal.Vector(2000, 2000, 2000))
    c = sph.static_mesh_component
    c.set_static_mesh(unreal.load_asset("/Engine/BasicShapes/Sphere"))
    mi_path = root(name) + "/Env/MI_Sky_" + name
    mi = EAL.load_asset(mi_path) if EAL.does_asset_exist(mi_path) else AT.create_asset("MI_Sky_" + name, root(name) + "/Env", unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    MEL.set_material_instance_parent(mi, _sky_material())
    MEL.set_material_instance_texture_parameter_value(mi, "Sky", cube)
    MEL.set_material_instance_scalar_parameter_value(mi, "Strength", K * w["strength"])
    EAL.save_loaded_asset(mi)
    c.set_material(0, mi)
    c.set_editor_property("cast_shadow", False)
    c.set_editor_property("affect_dynamic_indirect_lighting", False)
    c.set_editor_property("affect_distance_field_lighting", False)

    for a, lbl in ((pp, "BL_PostProcess"), (sky, "BL_SkyLight"), (sph, "BL_SkySphere")):
        a.set_actor_label(lbl); a.tags = [tag]; a.set_folder_path("Blender/Env")
    for a in ACT.get_all_level_actors():  # sun must not look for an atmosphere any more
        if isinstance(a, unreal.DirectionalLight): a.light_component.set_editor_property("atmosphere_sun_light", False)
    return {"hdri": w["source"], "sky_intensity": K * w["strength"], "yaw": yaw}

def build(name):
    r = {"level": new_level(name)}
    r.update(import_meshes(name)); r.update(fix_materials(name)); r.update(apply_bakes(name)); r.update(nanite_off_for_translucent(name))
    r.update(place_lights(name)); r.update(place_cameras(name)); r.update(environment(name))
    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    return r

def nanite_off_for_translucent(name):
    """Nanite can't draw translucent materials -> those meshes go back to regular rendering."""
    sms = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
    trans = (unreal.BlendMode.BLEND_TRANSLUCENT, unreal.BlendMode.BLEND_ADDITIVE, unreal.BlendMode.BLEND_MODULATE)
    used = {}
    for a in ACT.get_all_level_actors():
        c = a.get_component_by_class(unreal.StaticMeshComponent)
        if c and c.static_mesh: used.setdefault(c.static_mesh, set()).update(m for m in c.get_materials() if m)
    off = []
    for mesh, mats in used.items():
        if any(m.get_blend_mode() in trans for m in mats):
            ns = mesh.get_editor_property("nanite_settings")
            if ns.enabled:
                ns.enabled = False; sms.set_nanite_settings(mesh, ns, apply_changes=True); off.append(mesh.get_name())
    return {"nanite_off": len(off), "meshes": off[:15]}
