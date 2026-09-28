"""Neelam - platform, lawn and Cesium cut-out following the REAL site boundary (curved corners)
instead of a rectangle. Data from Data/site_outline.json (make_site_outline.py). Run INSIDE Unreal."""
import json, os, unreal

FLIP = globals().get("NEELAM_FLIP_WINDING", False)
DEPTH = globals().get("NEELAM_PLATFORM_DEPTH", 800.0)
PROJECT = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
D = json.load(open(os.path.join(PROJECT, "Scripts", "Neelam", "Data", "site_outline.json")))
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
EAL, AT = unreal.EditorAssetLibrary, unreal.AssetToolsHelpers.get_asset_tools()
MESH_DIR = "/Game/Neelam/Buildings/WindTunnel/Meshes/Site/Ground"
MI = "/Game/Neelam/Buildings/WindTunnel/Materials/Instances/"
by_label = lambda l: next((a for a in EAS.get_all_level_actors() if a.get_actor_label() == l), None)
root = by_label("Neelam_WindTunnel_Root")
info = {}


def ccw(t):
    (ax, ay), (bx, by), (cx, cy) = t
    return (bx - ax) * (cy - ay) - (by - ay) * (cx - ax) > 0


def build_mesh(name, tris, ring=None, top=-4.0, bottom=None, mat=None, uv_m=2.0):
    path = MESH_DIR + "/" + name
    sm = EAL.load_asset(path) if EAL.does_asset_exist(path) else AT.create_asset(name, MESH_DIR, unreal.StaticMesh, None)
    desc = sm.create_static_mesh_description(sm)
    g = desc.create_polygon_group()
    desc.set_polygon_group_material_slot_name(g, "Main")
    def face(pts3, uvs):
        vis = []
        for p, uv in zip(pts3, uvs):
            v = desc.create_vertex(); desc.set_vertex_position(v, unreal.Vector(*p))
            vi = desc.create_vertex_instance(v); desc.set_vertex_instance_uv(vi, unreal.Vector2D(*uv), 0)
            vis.append(vi)
        desc.create_triangle(g, vis)
    s = 1.0 / (uv_m * 100.0)
    for t in tris:                                   # top, facing +Z
        if ccw(t) == (not FLIP):
            t = [t[0], t[2], t[1]]
        face([(x, y, top) for x, y in t], [(x * s, y * s) for x, y in t])
    if ring and bottom is not None:                  # vertical sides
        n = len(ring)
        orient = sum((ring[(i + 1) % n][0] - ring[i][0]) * (ring[(i + 1) % n][1] + ring[i][1]) for i in range(n))
        for i in range(n):
            a, b = ring[i], ring[(i + 1) % n]
            if (orient > 0) == FLIP:
                a, b = b, a
            L = ((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2) ** 0.5 * s
            q = [(a[0], a[1], top), (b[0], b[1], top), (b[0], b[1], bottom), (a[0], a[1], bottom)]
            uq = [(0, 0), (L, 0), (L, (top - bottom) * s), (0, (top - bottom) * s)]
            face([q[0], q[1], q[2]], [uq[0], uq[1], uq[2]]); face([q[0], q[2], q[3]], [uq[0], uq[2], uq[3]])
    sm.set_editor_property("static_materials", [unreal.StaticMaterial(material_interface=EAL.load_asset(mat), material_slot_name="Main")])
    sm.build_from_static_mesh_descriptions([desc], True)
    bs = sm.get_editor_property("body_setup")
    if bs: bs.set_editor_property("collision_trace_flag", unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
    EAL.save_loaded_asset(sm)
    return sm


def place(label, sm):
    old = by_label(label)
    if old: EAS.destroy_actor(old)
    a = EAS.spawn_actor_from_object(sm, root.get_actor_location(), root.get_actor_rotation())
    a.set_actor_label(label); a.set_folder_path("Neelam/WindTunnel/Site")
    a.attach_to_actor(root, "", unreal.AttachmentRule.KEEP_WORLD, unreal.AttachmentRule.KEEP_WORLD, unreal.AttachmentRule.KEEP_WORLD, False)
    return a


plat = build_mesh("SM_Site_Platform", D["platform_tris"], D["platform_ring"], top=-6.0, bottom=-6.0 - DEPTH, mat=MI + "MI_Site_Platform", uv_m=3.0)
lawn = build_mesh("SM_Site_Lawn", D["lawn_tris"], None, top=-4.0, mat=MI + "MI_Ground_Reserved", uv_m=2.0)
place("Neelam_SitePlatform", plat)
place("Neelam_SiteGround", lawn)

poly = by_label("Neelam_SiteCutout")
spl = poly.get_component_by_class(unreal.SplineComponent)
xf = root.get_actor_transform()
spl.clear_spline_points(True)
for x, y in D["cut"]:
    spl.add_spline_point(xf.transform_location(unreal.Vector(x, y, 0)), unreal.SplineCoordinateSpace.WORLD, False)
for i in range(len(D["cut"])):
    spl.set_spline_point_type(i, unreal.SplinePointType.LINEAR, False)
spl.set_closed_loop(True, True)
for ts in [a for a in EAS.get_all_level_actors() if isinstance(a, unreal.Cesium3DTileset)]:
    try: ts.refresh_tileset()
    except Exception: pass
info.update(cut_points=len(D["cut"]), platform_tris=len(D["platform_tris"]), flip=FLIP)
result = info
