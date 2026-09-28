"""Neelam - site finishing for the Wind Tunnel development (run INSIDE Unreal, after the other scripts).

    py "C:/Users/Admin/Documents/Unreal Projects/ArchVizExplorer-Neelam/Scripts/Neelam/Site_Finishing.py"

  1. Scene report  -> Saved/Neelam/scene_report.json (Cesium, sun, sky, post-process actors)
  2. Daylight      -> sun placed in front of the road-side facade, like the reference renders
                      (CesiumSunSky solar time, or the DirectionalLight's rotation)
  3. Cesium cut-out-> Neelam_SiteCutout polygon over the plot + Polygon Raster Overlay on the
                      photoreal tilesets, so the old buildings/ground inside the plot disappear
  4. Site ground   -> Neelam_SiteGround lawn plane under the development (fills the cut-out)
  Then captures the review shots. Re-runnable. SAVE THE LEVEL afterwards (Ctrl+S).
"""
import json, math, os, sys, traceback
try:
    import unreal
except ImportError:
    sys.exit("Run this INSIDE the Unreal Editor.")

ROOT_LABEL = "Neelam_WindTunnel_Root"
CUT_LABEL, GROUND_LABEL = "Neelam_SiteCutout", "Neelam_SiteGround"
HALF_CM = (9905.0 - 60.0, 6331.0 - 60.0)        # cut just inside the boundary wall (see Ground_Development.py)
OUTLINER = "Neelam/WindTunnel/Site"
GROUND_MI = "/Game/Neelam/Buildings/WindTunnel/Materials/Instances/MI_Site_GroundLawn"
SURFACE_MASTER = "/Game/Neelam/Buildings/WindTunnel/Materials/Master/M_Neelam_Surface"
GOOGLE_ION = 2275207
PROJECT = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())

EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
EAL, MEL = unreal.EditorAssetLibrary, unreal.MaterialEditingLibrary
R = {"actors": [], "steps": {}, "errors": []}


def cls(name):
    return getattr(unreal, name, None)


def actors_of(name):
    c = cls(name)
    return [a for a in EAS.get_all_level_actors() if c and isinstance(a, c)]


def by_label(label):
    return next((a for a in EAS.get_all_level_actors() if a.get_actor_label() == label), None)


def gp(obj, prop, default=None):
    try:
        return obj.get_editor_property(prop)
    except Exception:
        return default


def step(name):
    def deco(fn):
        def run(*a):
            try:
                R["steps"][name] = fn(*a)
            except Exception as e:
                R["steps"][name] = "FAILED: %s" % e
                R["errors"].append(traceback.format_exc())
                unreal.log_warning("Neelam %s failed: %s" % (name, e))
        return run
    return deco


root = by_label(ROOT_LABEL)
if root is None:
    raise RuntimeError(ROOT_LABEL + " not found - run Place_WindTunnel.py first")
XF = root.get_actor_transform()
YAW = root.get_actor_rotation().yaw


def W(x, y, z=0.0):
    return XF.transform_location(unreal.Vector(x, y, z))


# ------------------------------------------------------------------ 1. report
@step("report")
def report():
    keys = ("Cesium", "Light", "Sky", "Fog", "PostProcess", "Cloud")
    for a in EAS.get_all_level_actors():
        cn = a.get_class().get_name()
        if any(k in cn for k in keys):
            e = {"label": a.get_actor_label(), "class": cn}
            if "Tileset" in cn:
                e.update(ion=gp(a, "ion_asset_id"), url=str(gp(a, "url", "")), source=str(gp(a, "tileset_source")))
            if "Georeference" in cn:
                e.update(lat=gp(a, "origin_latitude"), lon=gp(a, "origin_longitude"), h=gp(a, "origin_height"))
            if "SunSky" in cn:
                e.update(solar_time=gp(a, "solar_time"), tz=gp(a, "time_zone"), day=gp(a, "day"), month=gp(a, "month"))
            R["actors"].append(e)
    return len(R["actors"])


# ------------------------------------------------------------------ 2. daylight
@step("daylight")
def daylight():
    # compass azimuth the road-side facade faces (root local -Y); Cesium: +X east, +Y south
    vx, vy = math.sin(math.radians(YAW)), -math.cos(math.radians(YAW))
    face_az = math.degrees(math.atan2(vx, -vy)) % 360.0
    out = {"road_facade_faces_azimuth": round(face_az, 1)}
    suns = actors_of("CesiumSunSky")
    if suns:
        sun_az = face_az + (35.0 if face_az < 180 else -35.0)      # light a little from the side, for relief
        hour = max(8.5, min(16.5, 12.0 + (sun_az - 180.0) / 15.0))
        if face_az < 60 or face_az > 300:
            hour = 16.0                                            # north-facing: late sun rakes the facade
        s = suns[0]
        s.set_editor_property("solar_time", hour)
        try:
            s.set_editor_property("month", 11); s.set_editor_property("day", 15)   # clear winter light
        except Exception:
            pass
        s.update_sun()
        out.update(mode="CesiumSunSky", solar_time=hour)
        return out
    # Unreal's SunPosition "SunSky" blueprint (BP_AVE_SunSky_01): search the time of day whose sun
    # direction best lights the road facade from the front at a pleasant 20-50 deg elevation
    bps = [a for a in EAS.get_all_level_actors() if a.get_class().get_name().startswith("SunSky")]
    if bps:
        s = bps[0]
        geo = (actors_of("CesiumGeoreference") or [None])[0]
        for prop, val in (("Latitude", gp(geo, "origin_latitude", 19.16) if geo else 19.16),
                          ("Longitude", gp(geo, "origin_longitude", 72.96) if geo else 72.96),
                          ("TimeZone", 5.5), ("bUseDaylightSavingTime", False)):
            try: s.set_editor_property(prop, val)
            except Exception: pass
        dlc = s.get_component_by_class(unreal.DirectionalLightComponent)
        side = 0.45
        fw, rt = root.get_actor_forward_vector(), root.get_actor_right_vector()   # local +X, +Y
        want = unreal.Vector(fw.x * side + rt.x, fw.y * side + rt.y, 0.0); wl = math.hypot(want.x, want.y)
        best = None
        for month in (11, 2, 9):
            for q in range(28, 72):                      # 07:00 .. 17:45
                hour = q / 4.0
                try:
                    s.set_editor_property("Month", month); s.set_editor_property("Day", 15)
                    s.set_editor_property("SolarTime", hour)
                    s.call_method("UpdateSun")
                except Exception as e:
                    return "SunSky could not be driven: %s" % e
                f = dlc.get_forward_vector()
                elev = -f.z
                h = math.hypot(f.x, f.y) or 1e-6
                score = (f.x * want.x + f.y * want.y) / (h * wl)
                if 0.34 < elev < 0.78 and (best is None or score > best[0]):
                    best = (score, month, hour, round(math.degrees(math.asin(elev)), 1))
        if best:
            _, month, hour, el = best
            s.set_editor_property("Month", month); s.set_editor_property("SolarTime", hour); s.call_method("UpdateSun")
            out.update(mode="SunSky BP", label=s.get_actor_label(), month=month, solar_time=hour,
                       sun_elevation_deg=el, front_light_score=round(best[0], 2))
            return out
    dls = [d for d in actors_of("DirectionalLight") if "night" not in d.get_actor_label().lower()]
    if dls:
        d = dls[0]
        travel_yaw = YAW + 90.0 + 35.0                             # travels towards +Y local = lights the -Y face
        d.set_actor_rotation(unreal.Rotator(roll=0.0, pitch=-38.0, yaw=travel_yaw), False)
        out.update(mode="DirectionalLight", label=d.get_actor_label(), yaw=travel_yaw)
        return out
    return "no sun actor found"


# ------------------------------------------------------------------ 3. Cesium cut-out
@step("cesium_cutout")
def cutout():
    Poly, Overlay, Tileset = cls("CesiumCartographicPolygon"), cls("CesiumPolygonRasterOverlay"), cls("Cesium3DTileset")
    if not (Poly and Overlay and Tileset):
        return "Cesium classes not available"
    poly = by_label(CUT_LABEL)
    if poly is None:
        poly = EAS.spawn_actor_from_class(Poly, W(0, 0, 0))
        poly.set_actor_label(CUT_LABEL); poly.set_folder_path(OUTLINER)
    spline = gp(poly, "polygon") or poly.get_component_by_class(unreal.SplineComponent)
    hx, hy = HALF_CM
    spline.clear_spline_points(True)
    for (x, y) in ((-hx, -hy), (hx, -hy), (hx, hy), (-hx, hy)):
        spline.add_spline_point(W(x, y, 0), unreal.SplineCoordinateSpace.WORLD, False)
    for i in range(4):
        spline.set_spline_point_type(i, unreal.SplinePointType.LINEAR, False)
    spline.set_closed_loop(True, True)

    sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    lib = unreal.SubobjectDataBlueprintFunctionLibrary
    done = []
    for ts in actors_of("Cesium3DTileset"):
        ion = gp(ts, "ion_asset_id")
        url = str(gp(ts, "url", "")).lower()
        if ion == 1 and "google" not in url:
            continue                                               # keep Cesium World Terrain as the ground
        ov = ts.get_component_by_class(Overlay)
        if ov is None:
            handles = sds.k2_gather_subobject_data_for_instance(ts)
            params = unreal.AddNewSubobjectParams(parent_handle=handles[0], new_class=Overlay, blueprint_context=None)
            h, fail = sds.add_new_subobject(params)
            ov = ts.get_component_by_class(Overlay)
            if ov is None:
                try: ov = lib.get_object(lib.get_data(h))
                except Exception: ov = None
        if ov is None:
            R["errors"].append("could not add overlay to " + ts.get_actor_label()); continue
        ov.set_editor_property("polygons", [poly])
        for prop, val in (("exclude_selected_tiles", True), ("invert_selection", False)):
            try: ov.set_editor_property(prop, val)
            except Exception: pass
        try: ts.refresh_tileset()
        except Exception: pass
        done.append(ts.get_actor_label())
    return {"polygon": CUT_LABEL, "tilesets_clipped": done}


# ------------------------------------------------------------------ 4. site ground
@step("site_ground")
def ground():
    surf = EAL.load_asset(SURFACE_MASTER)
    if not EAL.does_asset_exist(GROUND_MI):
        folder, name = GROUND_MI.rsplit("/", 1)
        mi = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            name, folder, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    else:
        mi = EAL.load_asset(GROUND_MI)
    MEL.set_material_instance_parent(mi, surf)
    base = "/Game/Neelam/Buildings/WindTunnel/Textures/PolyHaven/leafy_grass/T_LeafyGrass_"
    for k, pn in (("D", "BaseColor"), ("N", "Normal"), ("R", "Roughness"), ("AO", "AmbientOcclusion")):
        t = EAL.load_asset(base + k)
        if t: MEL.set_material_instance_texture_parameter_value(mi, pn, t)
    hx, hy = HALF_CM
    MEL.set_material_instance_scalar_parameter_value(mi, "Tiling", (2 * hx / 100.0) / 2.0)   # 2 m texture repeat
    MEL.set_material_instance_scalar_parameter_value(mi, "TilingAspectY", hy / hx)
    MEL.set_material_instance_vector_parameter_value(mi, "Tint", unreal.LinearColor(0.16, 0.30, 0.08, 1))
    MEL.set_material_instance_scalar_parameter_value(mi, "TintAmount", 0.35)
    MEL.set_material_instance_scalar_parameter_value(mi, "UseTextureRoughness", 1.0)
    MEL.set_material_instance_scalar_parameter_value(mi, "MacroVariation", 0.6)
    EAL.save_loaded_asset(mi)

    plane = EAL.load_asset("/Engine/BasicShapes/Plane")
    g = by_label(GROUND_LABEL)
    if g is None:
        g = EAS.spawn_actor_from_object(plane, W(0, 0, -4.0), root.get_actor_rotation())
        g.set_actor_label(GROUND_LABEL); g.set_folder_path(OUTLINER)
    g.set_actor_location(W(0, 0, -4.0), False, False)
    g.set_actor_rotation(root.get_actor_rotation(), False)
    g.set_actor_scale3d(unreal.Vector(2 * hx / 100.0, 2 * hy / 100.0, 1.0))
    g.static_mesh_component.set_material(0, mi)
    g.attach_to_actor(root, "", unreal.AttachmentRule.KEEP_WORLD, unreal.AttachmentRule.KEEP_WORLD,
                      unreal.AttachmentRule.KEEP_WORLD, False)
    return {"size_m": [2 * hx / 100.0, 2 * hy / 100.0]}


# rebuild materials first (adds TilingAspectY to the master), without its own review capture
_mat = os.path.join(PROJECT, "Scripts", "Neelam", "Apply_WindTunnel_Materials.py")
exec(compile(open(_mat).read(), _mat, "exec"), {"__name__": "__main__", "__file__": _mat, "NEELAM_RUN_REVIEW": False})

with unreal.ScopedEditorTransaction("Neelam site finishing"):
    report(); daylight(); cutout(); ground()

out = os.path.join(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_saved_dir()), "Neelam")
os.makedirs(out, exist_ok=True)
json.dump(R, open(os.path.join(out, "scene_report.json"), "w"), indent=1, default=str)
unreal.log("Neelam site finishing: %s" % json.dumps(R["steps"], default=str))

_cap = os.path.join(PROJECT, "Scripts", "Neelam", "Capture_Review_Shots.py")
exec(compile(open(_cap).read(), _cap, "exec"), {"__name__": "__main__", "__file__": _cap})
