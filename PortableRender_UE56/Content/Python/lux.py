"""Luxury look pass for the Neelam levels (on top of scene_builder's straight import).
    import lux; lux.environment("3BHK", "kloppenheim_06_puresky", sky_yaw=0, sun_elev=14)
HDRIs live in SourceArt/HDRI/<name>.hdr (Poly Haven, CC0)."""
import unreal, os, math
import scene_builder as SB

ACT, EAL, AT, MEL = SB.ACT, SB.EAL, SB.AT, SB.MEL
HDRI_DIR = os.path.join(SB.PROJ, "SourceArt", "HDRI")

def hdri_cube(name):
    path = "/Game/Neelam/Shared/HDRI/" + name
    if not EAL.does_asset_exist(path):
        t = unreal.AssetImportTask()
        t.filename = os.path.join(HDRI_DIR, name + ".hdr"); t.destination_path = "/Game/Neelam/Shared/HDRI"
        t.automated = True; t.save = True
        AT.import_asset_tasks([t])
    return EAL.load_asset(path)

def sky_probe(hdri, out_dir):
    """Capture the HDRI sky sphere looking +X,+Y,-X,-Y (90 deg FOV) from 1 km up -> tells which way the cubemap faces."""
    cube = hdri_cube(hdri)
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    sph = next((a for a in ACT.get_all_level_actors() if a.get_actor_label() == "BL_SkySphere"), None)
    mi = sph.static_mesh_component.get_material(0)
    MEL.set_material_instance_texture_parameter_value(mi, "Sky", cube)
    sph.set_actor_rotation(unreal.Rotator(roll=0, pitch=0, yaw=0), False)
    files = []
    for yaw in range(0, 360, 45):
        tag = "y%03d" % yaw
        rt = unreal.RenderingLibrary.create_render_target2d(world, 512, 512, unreal.TextureRenderTargetFormat.RTF_RGBA8_SRGB)
        cap = ACT.spawn_actor_from_class(unreal.SceneCapture2D, unreal.Vector(0, 0, 150), unreal.Rotator(roll=0, pitch=0, yaw=yaw))  # NB positional order is (roll, pitch, yaw)
        c = cap.capture_component2d
        c.set_editor_property("fov_angle", 90.0); c.set_editor_property("texture_target", rt)
        c.set_editor_property("capture_source", unreal.SceneCaptureSource.SCS_FINAL_TONE_CURVE_HDR)
        c.set_editor_property("primitive_render_mode", unreal.SceneCapturePrimitiveRenderMode.PRM_USE_SHOW_ONLY_LIST)
        c.show_only_actor_components(sph)
        c.capture_scene()
        unreal.RenderingLibrary.export_render_target(world, rt, out_dir, "probe_%s.png" % tag)
        ACT.destroy_actor(cap); files.append(tag)
    return files

def sky_material():
    """M_HDRISky v2: unlit two-sided cubemap in view direction, with Strength and Yaw (degrees) parameters."""
    path = "/Game/Neelam/Shared/M_HDRISky"
    m = EAL.load_asset(path)
    if m and any(str(n) == "Yaw" for n in MEL.get_scalar_parameter_names(m)): return m
    MEL.delete_all_material_expressions(m)
    cv = MEL.create_material_expression(m, unreal.MaterialExpressionCameraVectorWS, -1400, 0)
    neg = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, -1200, 0); neg.set_editor_property("const_b", -1.0)
    MEL.connect_material_expressions(cv, "", neg, "A")
    yaw = MEL.create_material_expression(m, unreal.MaterialExpressionScalarParameter, -1400, 250)
    yaw.set_editor_property("parameter_name", "Yaw"); yaw.set_editor_property("default_value", 0.0)
    turns = MEL.create_material_expression(m, unreal.MaterialExpressionDivide, -1200, 250); turns.set_editor_property("const_b", -360.0)
    MEL.connect_material_expressions(yaw, "", turns, "A")
    rot = MEL.create_material_expression(m, unreal.MaterialExpressionRotateAboutAxis, -1000, 100)
    rot.set_editor_property("period", 1.0)
    axis = MEL.create_material_expression(m, unreal.MaterialExpressionConstant3Vector, -1200, 400); axis.set_editor_property("constant", unreal.LinearColor(0, 0, 1, 0))
    zero = MEL.create_material_expression(m, unreal.MaterialExpressionConstant3Vector, -1200, 500)
    MEL.connect_material_expressions(axis, "", rot, "NormalizedRotationAxis")
    MEL.connect_material_expressions(turns, "", rot, "RotationAngle")
    MEL.connect_material_expressions(zero, "", rot, "PivotPoint")
    MEL.connect_material_expressions(neg, "", rot, "Position")
    add = MEL.create_material_expression(m, unreal.MaterialExpressionAdd, -800, 0)
    MEL.connect_material_expressions(neg, "", add, "A"); MEL.connect_material_expressions(rot, "", add, "B")
    tex = MEL.create_material_expression(m, unreal.MaterialExpressionTextureSampleParameterCube, -600, 0)
    tex.set_editor_property("parameter_name", "Sky"); tex.set_editor_property("texture", unreal.load_asset("/Engine/MapTemplates/Sky/SunsetAmbientCubemap"))
    MEL.connect_material_expressions(add, "", tex, "UVs")
    st = MEL.create_material_expression(m, unreal.MaterialExpressionScalarParameter, -600, 250)
    st.set_editor_property("parameter_name", "Strength"); st.set_editor_property("default_value", 1.0)
    mul = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, -300, 100)
    MEL.connect_material_expressions(tex, "RGB", mul, "A"); MEL.connect_material_expressions(st, "", mul, "B")
    MEL.connect_material_property(mul, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    MEL.recompile_material(m); EAL.save_loaded_asset(m)
    return m

def environment(name, hdri="kloppenheim_06_puresky", hdri_sun_yaw=300.0, sun_yaw=180.0, sun_elev=14.0,
                sky_intensity=1.2, sun_lux=7.0, sun_kelvin=4300.0):
    """Swap the level's sky to <hdri>, spun so its sun sits at sun_yaw, plus a matching warm directional sun.
    hdri_sun_yaw: where the HDRI's sun lands with no rotation (sky_probe). sun_elev: raised a bit above the HDRI's
    for longer light patches indoors."""
    cube = hdri_cube(hdri); sky_material()
    spin = sun_yaw - hdri_sun_yaw
    by = {a.get_actor_label(): a for a in ACT.get_all_level_actors()}
    mi = by["BL_SkySphere"].static_mesh_component.get_material(0)
    MEL.set_material_instance_texture_parameter_value(mi, "Sky", cube)
    MEL.set_material_instance_scalar_parameter_value(mi, "Strength", sky_intensity)
    MEL.set_material_instance_scalar_parameter_value(mi, "Yaw", spin)
    EAL.save_loaded_asset(mi)
    sl = by["BL_SkyLight"].light_component
    sl.set_editor_property("cubemap", cube); sl.set_editor_property("source_cubemap_angle", spin)
    sl.set_editor_property("intensity", sky_intensity); sl.recapture_sky()
    sun = next(a for a in by.values() if isinstance(a, unreal.DirectionalLight))
    sun.set_actor_rotation(unreal.Rotator(roll=0, pitch=-sun_elev, yaw=sun_yaw + 180.0), False)  # light travels away from the sun
    c = sun.light_component
    c.set_intensity(sun_lux); c.set_editor_property("use_temperature", True); c.set_editor_property("temperature", sun_kelvin)
    c.set_light_color(unreal.LinearColor(1, 1, 1, 1)); c.set_editor_property("light_source_angle", 0.6)
    return {"hdri": hdri, "spin": spin, "sun_yaw": sun_yaw, "sun_elev": sun_elev}

def glass_material():
    """Rebuild /Game/Neelam/Shared/M_Glass as Thin Translucent (correct in Lumen AND the path tracer).
    Keeps the Color/Roughness/Opacity/IOR parameter names so existing instances still work."""
    m = EAL.load_asset("/Game/Neelam/Shared/M_Glass")
    MEL.delete_all_material_expressions(m)
    m.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
    m.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_THIN_TRANSLUCENT)
    m.set_editor_property("translucency_lighting_mode", unreal.TranslucencyLightingMode.TLM_SURFACE_PER_PIXEL_LIGHTING)
    m.set_editor_property("two_sided", True)
    def p(kind, name, val, x, y):
        e = MEL.create_material_expression(m, kind, x, y); e.set_editor_property("parameter_name", name)
        e.set_editor_property("default_value", val); return e
    col = p(unreal.MaterialExpressionVectorParameter, "Color", unreal.LinearColor(0.92, 0.95, 0.95, 1), -700, 0)
    rough = p(unreal.MaterialExpressionScalarParameter, "Roughness", 0.02, -700, 200)
    op = p(unreal.MaterialExpressionScalarParameter, "Opacity", 0.0, -700, 300)
    blk = MEL.create_material_expression(m, unreal.MaterialExpressionConstant3Vector, -700, -150)
    blk.set_editor_property("constant", unreal.LinearColor(0, 0, 0, 1))
    spec = MEL.create_material_expression(m, unreal.MaterialExpressionConstant, -700, 400); spec.set_editor_property("r", 0.5)
    MEL.connect_material_property(blk, "", unreal.MaterialProperty.MP_BASE_COLOR)   # clear glass: no diffuse
    MEL.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    MEL.connect_material_property(op, "", unreal.MaterialProperty.MP_OPACITY)
    MEL.connect_material_property(spec, "", unreal.MaterialProperty.MP_SPECULAR)
    out = MEL.create_material_expression(m, unreal.MaterialExpressionThinTranslucentMaterialOutput, -300, 0)
    MEL.connect_material_expressions(col, "", out, "")
    MEL.recompile_material(m); EAL.save_loaded_asset(m)
    return "M_Glass -> thin translucent"

def lighting(name, kelvin=3200.0, sun_lux=12.0, sun_kelvin=4500.0, strip_tint=(1.0, 0.88, 0.74), white_balance=4800.0,
             contrast=1.08, saturation=1.05, vignette=0.3, bloom=0.35, exposure_bias=-0.2):
    """Warm luxury mood: interior lights to <kelvin>, emissive strips tinted warm, stronger golden sun, gentle grade."""
    n = 0
    for a in ACT.get_all_level_actors():
        if isinstance(a, (unreal.RectLight, unreal.PointLight, unreal.SpotLight)):
            c = a.light_component
            c.set_editor_property("use_temperature", True); c.set_editor_property("temperature", kelvin); n += 1
        elif isinstance(a, unreal.DirectionalLight):
            c = a.light_component
            c.set_intensity(sun_lux); c.set_editor_property("temperature", sun_kelvin)
    reg = unreal.AssetRegistryHelpers.get_asset_registry()
    f = unreal.ARFilter(package_paths=[SB.root(name) + "/Materials_UE"], class_paths=[unreal.TopLevelAssetPath("/Script/Engine", "MaterialInstanceConstant")])
    strips = 0
    for ad in reg.get_assets(f):
        mi = ad.get_asset()
        if mi.get_base_material().get_name() == "M_Emissive":
            c = MEL.get_material_instance_vector_parameter_value(mi, "Color")
            if min(c.r, c.g, c.b) > 0.6:   # only near-white LEDs; coloured emissives (screens, signs) keep their colour
                MEL.set_material_instance_vector_parameter_value(mi, "Color", unreal.LinearColor(*strip_tint, 1)); EAL.save_loaded_asset(mi); strips += 1
    pp = next(a for a in ACT.get_all_level_actors() if a.get_actor_label() == "BL_PostProcess")
    s = pp.get_editor_property("settings")
    for k, v in (("auto_exposure_bias", exposure_bias), ("color_contrast", unreal.Vector4(contrast, contrast, contrast, 1)),
                 ("color_saturation", unreal.Vector4(saturation, saturation, saturation, 1)), ("vignette_intensity", vignette),
                 ("bloom_intensity", bloom), ("white_temp", white_balance)):
        s.set_editor_property("override_" + k, True); s.set_editor_property(k, v)
    pp.set_editor_property("settings", s)
    return {"lights_warmed": n, "led_strips": strips}


def warm_emissives(factor=(1.0, 0.82, 0.6)):
    """Interchange (glTF) emissives that are bright near-white get a warm tint (white balance otherwise turns them blue)."""
    seen, warmed = set(), []
    for a in ACT.get_all_level_actors():
        c = a.get_component_by_class(unreal.StaticMeshComponent)
        if not c: continue
        for m in c.get_materials():
            if not m or m.get_name() in seen or not isinstance(m, unreal.MaterialInstanceConstant): continue
            seen.add(m.get_name())
            if "EmissiveFactor" not in [str(n) for n in MEL.get_vector_parameter_names(m)]: continue
            e = MEL.get_material_instance_vector_parameter_value(m, "EmissiveFactor")
            if min(e.r, e.g, e.b) > 0.3 and max(e.r, e.g, e.b) - min(e.r, e.g, e.b) < 0.15 * max(e.r, e.g, e.b):
                MEL.set_material_instance_vector_parameter_value(m, "EmissiveFactor", unreal.LinearColor(e.r * factor[0], e.g * factor[1], e.b * factor[2], 1))
                EAL.save_loaded_asset(m); warmed.append(m.get_name())
    return warmed

def depth_pass(name, sky=0.45, sun_lux=18.0, barn=40.0, barn_len=20.0, rect_scale=1.0, ev_bias=0.0,
               contrast=1.14, saturation=1.06, vignette=0.42, wall_tint=(0.80, 0.73, 0.64)):
    """Lighting/material pass for depth: focused area lights, less sky fill, stronger sun, mid-tone plaster walls, punchier grade.
    Re-runnable: rect intensities scale from the value stored the first time (tag 'base=<nits>')."""
    import lux_mat as LM
    plaster = LM.mi("WallPlaster", "Marble021/Marble021_4K-JPG_Color.jpg", "Marble021/Marble021_4K-JPG_NormalDX.jpg",
                    "Marble021/Marble021_4K-JPG_Roughness.jpg", world_tiles=True, TileCm=300.0, TexCm=220.0, GroutCm=0.0,
                    RoughMin=0.30, RoughMax=0.45, NormalStrength=0.15, Tint=(*wall_tint, 1))
    walls = 0
    for a in ACT.get_all_level_actors():
        if a.get_actor_label() != "Vert": continue
        c = a.static_mesh_component
        for i, m in enumerate(c.get_materials()):
            if m and m.get_name() in ("MI_Statuario", "Limestone_Wall", "MI_WallPlaster"): c.set_material(i, plaster); walls += 1
    rects = 0
    for a in ACT.get_all_level_actors():
        if isinstance(a, unreal.RectLight) and not a.get_actor_label().startswith("LUX_"):
            c = a.light_component
            tags = [str(t) for t in a.tags]; base = next((float(t[5:]) for t in tags if t.startswith("base=")), None)
            if base is None:
                base = c.get_editor_property("intensity"); a.tags = list(a.tags) + ["base=%.4f" % base]
            c.set_intensity(base * rect_scale)
            c.set_editor_property("barn_door_angle", barn); c.set_editor_property("barn_door_length", barn_len)
            rects += 1
        elif isinstance(a, unreal.SkyLight):
            a.light_component.set_editor_property("intensity", sky)
        elif isinstance(a, unreal.DirectionalLight):
            a.light_component.set_intensity(sun_lux)
    pp = next(a for a in ACT.get_all_level_actors() if a.get_actor_label() == "BL_PostProcess")
    s = pp.get_editor_property("settings")
    for k, v in (("auto_exposure_bias", ev_bias), ("color_contrast", unreal.Vector4(contrast, contrast, contrast, 1)),
                 ("color_saturation", unreal.Vector4(saturation, saturation, saturation, 1)), ("vignette_intensity", vignette)):
        s.set_editor_property("override_" + k, True); s.set_editor_property(k, v)
    pp.set_editor_property("settings", s)
    return {"walls": walls, "rects": rects}

def track_spots(name, cd=135.0, kelvin=3000.0, outer=30.0, inner=6.0, spacing=32.0, keys=("Ceiling_Lights", "Magnetic_Track", "Spot_Light", "Track")):
    """Give modelled track/spot fixtures real light: narrow warm spots along each fixture, aimed down at ~35 deg toward the
    nearest wall (scalloped wall wash). Re-runnable (tag lux_track)."""
    import inspect_px as IP
    for a in ACT.get_all_level_actors():
        if "lux_track" in [str(t) for t in a.tags]: ACT.destroy_actor(a)
    made = 0
    fixtures = [a for a in ACT.get_all_level_actors() if isinstance(a, unreal.StaticMeshActor) and any(k.lower() in a.get_actor_label().lower() for k in keys)]
    for f in fixtures:
        o, e = f.get_actor_bounds(False)
        if o.z < 200 or max(e.x, e.y) > 300: continue
        along_x = e.x >= e.y; L = 2 * (e.x if along_x else e.y); n = max(1, int(L // spacing))
        z = o.z - e.z - 3
        for i in range(n):
            t = -L / 2 + (i + 0.5) * L / n
            p = unreal.Vector(o.x + (t if along_x else 0), o.y + (0 if along_x else t), z)
            best = None
            for d in (unreal.Vector(1, 0, 0), unreal.Vector(-1, 0, 0), unreal.Vector(0, 1, 0), unreal.Vector(0, -1, 0)):
                h = IP._trace(p - unreal.Vector(0, 0, 20), p - unreal.Vector(0, 0, 20) + d * 250, [f])
                if h and (best is None or h[3] < best[0]): best = (h[3], d)
            aim = (best[1] * 0.42 + unreal.Vector(0, 0, -1)) if best else unreal.Vector(0, 0, -1)
            s = ACT.spawn_actor_from_class(unreal.SpotLight, p, unreal.MathLibrary.make_rot_from_x(aim))
            c = s.light_component
            c.set_editor_property("intensity_units", unreal.LightUnits.CANDELAS); c.set_intensity(cd)
            c.set_editor_property("outer_cone_angle", outer); c.set_editor_property("inner_cone_angle", inner)
            c.set_editor_property("source_radius", 3.0); c.set_editor_property("use_temperature", True); c.set_editor_property("temperature", kelvin)
            c.set_editor_property("attenuation_radius", 900.0)
            s.set_actor_label("LUX_Track_%s_%d" % (f.get_actor_label()[:20], i)); s.tags = ["lux_track"]; s.set_folder_path("Lux/TrackSpots")
            made += 1
    return {"fixtures": len(fixtures), "spots": made}
