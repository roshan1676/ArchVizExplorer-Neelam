"""Neelam - seat the Wind Tunnel development firmly on the map (run INSIDE Unreal).

    py "C:/Users/Admin/Documents/Unreal Projects/ArchVizExplorer-Neelam/Scripts/Neelam/Ground_Development.py"

  1. Measures the real ground around the plot (ring of downward traces just outside the
     cut-out, ignoring our own actors; low percentile so existing buildings/trees don't count).
  2. Moves Neelam_WindTunnel_Root (and everything attached) so the site's ground level sits
     exactly on that ground - nothing floats.
  3. Clips Cesium World Terrain under the plot too (same Neelam_SiteCutout polygon), so no
     terrain bumps poke through the site.
  4. Builds Neelam_SitePlatform: a solid flat slab filling the plot from site level down below
     the lowest surrounding ground, slightly larger than the cut-out -> no gaps or see-through
     edges between the development and the map.
  5. Report -> Saved/Neelam/ground_report.json, then review shots (incl. two low edge views).
  Re-runnable; one Undo step. Save the level (Ctrl+S) afterwards.
"""
import json, math, os, sys
try:
    import unreal
except ImportError:
    sys.exit("Run this INSIDE the Unreal Editor.")

ROOT_LABEL, CUT_LABEL = "Neelam_WindTunnel_Root", "Neelam_SiteCutout"
PLATFORM_LABEL, GROUND_LABEL = "Neelam_SitePlatform", "Neelam_SiteGround"
WALL_HALF = (9905.0, 6331.0)                      # outer face of the boundary wall (local cm)
CUT_HALF = (WALL_HALF[0] - 60.0, WALL_HALF[1] - 60.0)   # map is cut just INSIDE the wall -> the wall hides the seam
PLATFORM_OVERLAP = 70.0                           # platform ends 10 cm past the wall face, hidden under the wall
RING_OFFSET = 860.0                               # ~8 m outside the wall (outside the old, larger cut-out, so the map is loaded there)
EXTRA_DEPTH = 500.0                               # platform goes 5 m below the lowest ground sample
GROUND_PERCENTILE = 0.5                            # median: splits any slope along the wall
OUTLINER = "Neelam/WindTunnel/Site"
PLATFORM_MI = "/Game/Neelam/Buildings/WindTunnel/Materials/Instances/MI_Site_Platform"
LAWN_MI = "/Game/Neelam/Buildings/WindTunnel/Materials/Instances/MI_Site_GroundLawn"
SURFACE_MASTER = "/Game/Neelam/Buildings/WindTunnel/Materials/Master/M_Neelam_Surface"
PROJECT = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())

EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
EAL, MEL = unreal.EditorAssetLibrary, unreal.MaterialEditingLibrary
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
R = {}


def by_label(label):
    return next((a for a in EAS.get_all_level_actors() if a.get_actor_label() == label), None)


root = by_label(ROOT_LABEL)
if root is None:
    raise RuntimeError(ROOT_LABEL + " not found")
ours = [root] + list(root.get_attached_actors())
for lbl in (CUT_LABEL, PLATFORM_LABEL, GROUND_LABEL, "Neelam_SiteAnchor"):
    a = by_label(lbl)
    if a and a not in ours:
        ours.append(a)
old_plat = by_label(PLATFORM_LABEL)
if old_plat:
    ours.append(old_plat)


def trace_z(x, y):
    hit = unreal.SystemLibrary.line_trace_single(
        world, unreal.Vector(x, y, 1500000.0), unreal.Vector(x, y, -1500000.0),
        unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, ours, unreal.DrawDebugTrace.NONE, True)
    if hit is None:
        return None
    t = hit.to_tuple()
    return float(t[4].z) if t[0] else None


def pct(vals, p):
    v = sorted(vals)
    return v[min(len(v) - 1, max(0, int(round((len(v) - 1) * p))))]


# ---------------------------------------------------------------- 1. measure ground
xf = root.get_actor_transform()
hx, hy = CUT_HALF[0] + RING_OFFSET, CUT_HALF[1] + RING_OFFSET
ring = []
N = 16
for i in range(N + 1):
    f = i / N
    for (lx, ly) in ((-hx + 2 * hx * f, -hy), (-hx + 2 * hx * f, hy), (-hx, -hy + 2 * hy * f), (hx, -hy + 2 * hy * f)):
        w = xf.transform_location(unreal.Vector(lx, ly, 0))
        z = trace_z(w.x, w.y)
        if z is not None:
            ring.append(z)
if len(ring) < 8:
    raise RuntimeError("Too few ground hits (%d) - is the Cesium map loaded around the site?" % len(ring))
ground = pct(ring, GROUND_PERCENTILE)
lowest = min(ring)
old_z = root.get_actor_location().z
R.update(ring_samples=len(ring), ring_min=lowest, ring_p30=ground, ring_median=pct(ring, 0.5),
         ring_max=max(ring), root_z_before=old_z)

with unreal.ScopedEditorTransaction("Neelam ground development"):
    # ------------------------------------------------------------ 2. seat the development
    loc = root.get_actor_location()
    root.set_actor_location(unreal.Vector(loc.x, loc.y, ground), False, False)
    R["root_z_after"] = ground
    R["moved_cm"] = ground - old_z

    # ------------------------------------------------------------ 3. clip terrain under the plot too
    Overlay, poly = getattr(unreal, "CesiumPolygonRasterOverlay", None), by_label(CUT_LABEL)
    if poly:
        spline = poly.get_component_by_class(unreal.SplineComponent)
        cx, cy = CUT_HALF
        xf1 = root.get_actor_transform()
        spline.clear_spline_points(True)
        for (x, y) in ((-cx, -cy), (cx, -cy), (cx, cy), (-cx, cy)):
            spline.add_spline_point(xf1.transform_location(unreal.Vector(x, y, 0)), unreal.SplineCoordinateSpace.WORLD, False)
        for i in range(4):
            spline.set_spline_point_type(i, unreal.SplinePointType.LINEAR, False)
        spline.set_closed_loop(True, True)
    clipped = []
    if Overlay and poly:
        sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
        Tileset = unreal.Cesium3DTileset
        for ts in [a for a in EAS.get_all_level_actors() if isinstance(a, Tileset)]:
            ov = ts.get_component_by_class(Overlay)
            if ov is None:
                handles = sds.k2_gather_subobject_data_for_instance(ts)
                sds.add_new_subobject(unreal.AddNewSubobjectParams(
                    parent_handle=handles[0], new_class=Overlay, blueprint_context=None))
                ov = ts.get_component_by_class(Overlay)
            if ov:
                ov.set_editor_property("polygons", [poly])
                # False = clip per pixel exactly on the polygon edge (True dropped whole tiles and left
                # a dark gap between the platform and the map)
                try: ov.set_editor_property("exclude_selected_tiles", False)
                except Exception: pass
                try: ts.refresh_tileset()
                except Exception: pass
                clipped.append(ts.get_actor_label())
    R["tilesets_clipped"] = clipped

    # ------------------------------------------------------------ 4. solid platform
    if not EAL.does_asset_exist(PLATFORM_MI):
        folder, name = PLATFORM_MI.rsplit("/", 1)
        mi = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            name, folder, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    else:
        mi = EAL.load_asset(PLATFORM_MI)
    MEL.set_material_instance_parent(mi, EAL.load_asset(SURFACE_MASTER))
    base = "/Game/Neelam/Buildings/WindTunnel/Textures/PolyHaven/concrete/T_Concrete_"
    for k, pn in (("D", "BaseColor"), ("N", "Normal"), ("R", "Roughness"), ("AO", "AmbientOcclusion")):
        t = EAL.load_asset(base + k)
        if t: MEL.set_material_instance_texture_parameter_value(mi, pn, t)
    for pn, v in (("Tiling", 30.0), ("TintAmount", 1.0), ("DetailContrast", 0.25), ("NormalStrength", 0.3),
                  ("Roughness", 0.9), ("UseTextureRoughness", 0.0), ("MacroVariation", 0.4)):
        MEL.set_material_instance_scalar_parameter_value(mi, pn, v)
    MEL.set_material_instance_vector_parameter_value(mi, "Tint", unreal.LinearColor(0.55, 0.47, 0.35, 1))
    EAL.save_loaded_asset(mi)

    px, py = CUT_HALF[0] + PLATFORM_OVERLAP, CUT_HALF[1] + PLATFORM_OVERLAP
    depth = max(300.0, ground - lowest) + EXTRA_DEPTH
    top_offset = -6.0                                   # just under the lawn plane (-4 cm)
    cube = EAL.load_asset("/Engine/BasicShapes/Cube")
    plat = old_plat or EAS.spawn_actor_from_object(cube, root.get_actor_location(), root.get_actor_rotation())
    plat.set_actor_label(PLATFORM_LABEL); plat.set_folder_path(OUTLINER)
    plat.detach_from_actor(unreal.DetachmentRule.KEEP_WORLD, unreal.DetachmentRule.KEEP_WORLD, unreal.DetachmentRule.KEEP_WORLD)
    xf2 = root.get_actor_transform()
    plat.set_actor_location(xf2.transform_location(unreal.Vector(0, 0, top_offset - depth / 2.0)), False, False)
    plat.set_actor_rotation(root.get_actor_rotation(), False)
    plat.set_actor_scale3d(unreal.Vector(2 * px / 100.0, 2 * py / 100.0, depth / 100.0))
    smc = plat.static_mesh_component
    smc.set_material(0, mi)
    smc.set_collision_profile_name("BlockAll")
    plat.attach_to_actor(root, "", unreal.AttachmentRule.KEEP_WORLD, unreal.AttachmentRule.KEEP_WORLD,
                         unreal.AttachmentRule.KEEP_WORLD, False)
    R["platform_size_m"] = [round(2 * px / 100, 1), round(2 * py / 100, 1), round(depth / 100, 1)]

    g = by_label(GROUND_LABEL)                          # lawn: 4 cm under site level, inside the wall
    if g:
        g.set_actor_location(xf2.transform_location(unreal.Vector(0, 0, -4.0)), False, False)
        g.set_actor_scale3d(unreal.Vector(2 * WALL_HALF[0] / 100.0, 2 * WALL_HALF[1] / 100.0, 1.0))
        lm = EAL.load_asset(LAWN_MI)
        if lm:                                          # more natural, less "flat green card"
            MEL.set_material_instance_scalar_parameter_value(lm, "Tiling", WALL_HALF[0] / 100.0 / 1.5)
            MEL.set_material_instance_scalar_parameter_value(lm, "TilingAspectY", WALL_HALF[1] / WALL_HALF[0])
            MEL.set_material_instance_scalar_parameter_value(lm, "TintAmount", 0.2)
            MEL.set_material_instance_scalar_parameter_value(lm, "MacroVariation", 1.0)
            MEL.set_material_instance_vector_parameter_value(lm, "Tint", unreal.LinearColor(0.11, 0.20, 0.05, 1))
            EAL.save_loaded_asset(lm)

out = os.path.join(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_saved_dir()), "Neelam")
os.makedirs(out, exist_ok=True)
json.dump(R, open(os.path.join(out, "ground_report.json"), "w"), indent=1)
unreal.log("Neelam ground: %s" % json.dumps(R))

if globals().get("NEELAM_RUN_REVIEW", True):
    _cap = os.path.join(PROJECT, "Scripts", "Neelam", "Capture_Review_Shots.py")
    exec(compile(open(_cap).read(), _cap, "exec"), {"__name__": "__main__", "__file__": _cap})
