"""Blender -> Unreal export.  NEVER saves the .blend.
blender --background --factory-startup <file.blend> --python blend_export.py -- <out_dir>
Writes <out_dir>/scene.gltf (+bin, tex/) and scene.json (lights, cameras, world, materials)."""
import bpy, sys, os, json, math

out = sys.argv[sys.argv.index("--") + 1]
os.makedirs(out, exist_ok=True)
sc = bpy.context.scene
vl = bpy.context.view_layer

def M(o): return [list(r) for r in o.matrix_world]

def rendered(o):
    """Visible in the viewport AND in renders (object + every parent collection)."""
    if not o.visible_get() or o.hide_render: return False
    if not o.visible_camera or o.display_type in ('WIRE', 'BOUNDS'): return False   # cutters / helpers (e.g. window_cut boxes)
    def hidden_path(c, target, path):
        if c == target: return any(x.hide_render for x in path)
        return any(hidden_path(ch, target, path + [ch]) for ch in c.children)
    return not any(hidden_path(sc.collection, uc, []) for uc in o.users_collection)

# ---------- lights / cameras / world ----------
lights, cams = [], []
for o in sc.objects:
    if not rendered(o): continue
    if o.type == 'LIGHT':
        d = o.data
        L = {"name": o.name, "type": d.type, "W": d.energy, "color": list(d.color)[:3], "matrix": M(o),
             "soft_size": getattr(d, "shadow_soft_size", 0.0)}
        if d.type == 'AREA': L.update(shape=d.shape, size=d.size, size_y=d.size_y, spread=getattr(d, "spread", math.pi))
        if d.type == 'SPOT': L.update(spot_size=d.spot_size, spot_blend=d.spot_blend)
        if d.type == 'SUN': L.update(angle=d.angle)
        lights.append(L)
for o in sc.objects:
    if o.type == 'CAMERA':
        c = o.data
        cams.append({"name": o.name, "matrix": M(o), "lens": c.lens, "sensor": c.sensor_width, "sensor_fit": c.sensor_fit,
                     "dof": c.dof.use_dof, "fstop": c.dof.aperture_fstop, "focus": c.dof.focus_distance, "active": o == sc.camera})
world = {}
if sc.world and sc.world.use_nodes:
    for n in sc.world.node_tree.nodes:
        if n.type == 'TEX_ENVIRONMENT' and n.image: world["hdri"] = bpy.path.abspath(n.image.filepath)
        if n.type == 'BACKGROUND':
            world["strength"] = n.inputs["Strength"].default_value
            if not n.inputs["Color"].is_linked: world["color"] = list(n.inputs["Color"].default_value)[:3]
        if n.type == 'MAPPING': world["rot_z"] = n.inputs["Rotation"].default_value[2]

# ---------- materials (UE side rebuilds the non-PBR ones by name) ----------
PROC = {'TEX_NOISE','TEX_VORONOI','TEX_WAVE','TEX_GRADIENT','TEX_BRICK','TEX_CHECKER','TEX_MAGIC'}
def sock(n, k, d=None):
    s = n.inputs.get(k)
    if s is None or s.is_linked or not hasattr(s, "default_value"): return d
    v = s.default_value
    return list(v)[:3] if hasattr(v, "__len__") else v
mats = {}
for m in bpy.data.materials:
    if m.users == 0: continue
    info = {"kind": "pbr"}
    if m.use_nodes:
        nodes = m.node_tree.nodes; types = {n.type for n in nodes}
        bs = [n for n in nodes if n.type == 'BSDF_PRINCIPLED']
        if types & {'BSDF_GLASS', 'BSDF_TRANSPARENT'} or (bs and (sock(bs[0], "Transmission Weight", 0) or 0) > 0.5):
            info["kind"] = "glass"
            g = next((n for n in nodes if n.type == 'BSDF_GLASS'), None)
            if g: info.update(color=sock(g, "Color"), roughness=sock(g, "Roughness"), ior=sock(g, "IOR"))
        elif 'EMISSION' in types and not bs:
            e = next(n for n in nodes if n.type == 'EMISSION')
            info.update(kind="emissive", color=sock(e, "Color", [1, 1, 1]), strength=sock(e, "Strength", 1))
        elif bs and (sock(bs[0], "Emission Strength", 0) or 0) > 0 and sock(bs[0], "Emission Color", [0, 0, 0]) != [0, 0, 0]:
            info.update(kind="emissive", color=sock(bs[0], "Emission Color"), strength=sock(bs[0], "Emission Strength"))
        elif types & PROC or not bs:
            info["kind"] = "procedural"
        if bs and info["kind"] in ("pbr", "procedural"):
            info.update(color=sock(bs[0], "Base Color"), roughness=sock(bs[0], "Roughness"), metallic=sock(bs[0], "Metallic"))
    info["viewport_color"] = list(m.diffuse_color)[:3]
    mats[m.name] = info

# ---------- geometry: realize everything visible into plain meshes ----------
for o in list(sc.objects):
    if o.type in ('MESH', 'CURVE', 'FONT', 'SURFACE', 'META') and rendered(o):
        o.hide_select = False; o.select_set(True)
    else:
        o.select_set(False)
sel = bpy.context.selected_objects
vl.objects.active = sel[0]
for o in sel:
    for m in o.modifiers:
        if m.type == 'SUBSURF': m.levels = min(m.levels, 2)  # ponytail: viewport subsurf capped at 2, Nanite handles the rest
bpy.ops.object.make_single_user(object=True, obdata=True)
bpy.ops.object.convert(target='MESH')
bpy.ops.export_scene.gltf(filepath=os.path.join(out, "scene.gltf"), export_format='GLTF_SEPARATE', export_texture_dir="tex",
                          use_selection=True, export_apply=True, export_lights=False, export_cameras=False,
                          export_extras=False, export_animations=False, export_yup=True)
json.dump({"source": bpy.data.filepath, "fps": sc.render.fps, "res": [sc.render.resolution_x, sc.render.resolution_y],
           "lights": lights, "cameras": cams, "world": world, "materials": mats,
           "objects": len(bpy.context.selected_objects)}, open(os.path.join(out, "scene.json"), "w"), indent=1)
print("@@DONE", out, len(lights), "lights", len(cams), "cams", len(mats), "mats")
