"""Bake Blender materials that glTF can't express (colour mixes, ramps, procedural, node groups)
into plain textures for Unreal. NEVER saves the .blend.
blender --background --factory-startup <file.blend> --python bake_mats.py -- <out_dir>
Writes <out_dir>/baked/*.png + baked.json {material: {"bc": png, "mr": png, "metallic": v}}.
Bakes on a 0..1 UV plane, so UV-mapped graphs come out exact; Generated/Object-coordinate graphs are approximate."""
import bpy, sys, os, json, re
import numpy as np

out = os.path.join(sys.argv[sys.argv.index("--") + 1], "baked")
os.makedirs(out, exist_ok=True)
RES = 2048

def rendered(o):
    if not o.visible_get() or o.hide_render: return False
    def hidden_path(c, target, path):
        if c == target: return any(x.hide_render for x in path)
        return any(hidden_path(ch, target, path + [ch]) for ch in c.children)
    return not any(hidden_path(bpy.context.scene.collection, uc, []) for uc in o.users_collection)

def skip_kind(m):
    t = {n.type for n in m.node_tree.nodes}
    return bool(t & {'BSDF_GLASS', 'BSDF_TRANSPARENT'}) or ('EMISSION' in t and 'BSDF_PRINCIPLED' not in t)

def needs(m, sock):
    """True when Principled <sock> is driven by something other than a lone image texture."""
    bs = next((n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    if bs is None: return True  # shader built from groups/mixes -> bake
    s = bs.inputs[sock]
    if not s.is_linked: return False
    src = s.links[0].from_node
    if src.type == 'TEX_IMAGE': return False
    if src.type in ('SEPARATE_COLOR', 'SEPRGB') and src.inputs[0].is_linked and src.inputs[0].links[0].from_node.type == 'TEX_IMAGE': return False
    return True

def metallic(m):
    bs = next((n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
    if bs is None or bs.inputs["Metallic"].is_linked: return 0.0  # ponytail: linked metallic flattened to 0, bake it if metals look wrong
    return float(bs.inputs["Metallic"].default_value)

mats = {}
for o in bpy.context.scene.objects:
    if o.type in ('MESH', 'CURVE') and rendered(o):
        for s in o.material_slots:
            m = s.material
            if m and m.use_nodes and not skip_kind(m) and (needs(m, "Base Color") or needs(m, "Roughness")):
                mats[m.name] = m

# empty the scene so Cycles bakes only the plane (materials stay in memory; file is never saved)
bpy.data.batch_remove(list(bpy.data.objects))
me = bpy.data.meshes.new("bakeplane")
me.from_pydata([(-1, -1, 0), (1, -1, 0), (1, 1, 0), (-1, 1, 0)], [], [(0, 1, 2, 3)])
uv = me.uv_layers.new(name="UVMap")
for li, c in zip(range(4), [(0, 0), (1, 0), (1, 1), (0, 1)]): uv.data[li].uv = c
plane = bpy.data.objects.new("bakeplane", me)
bpy.context.scene.collection.objects.link(plane)
bpy.context.view_layer.objects.active = plane; plane.select_set(True)
sc = bpy.context.scene
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = 1
sc.render.bake.margin = 0; sc.render.bake.use_clear = True

def key(s): return re.sub(r"[^a-z0-9]", "", s.lower())

def bake(m, kind):
    img = bpy.data.images.new("bk", RES, RES, float_buffer=(kind == 'ROUGHNESS'))
    if kind == 'DIFFUSE': img.colorspace_settings.name = 'sRGB'
    n = m.node_tree.nodes.new('ShaderNodeTexImage'); n.image = img
    m.node_tree.nodes.active = n
    try:
        if kind == 'DIFFUSE': bpy.ops.object.bake(type='DIFFUSE', pass_filter={'COLOR'})
        else: bpy.ops.object.bake(type='ROUGHNESS')
    finally:
        m.node_tree.nodes.remove(n)
    return img

result = {}
for i, (name, m) in enumerate(sorted(mats.items())):
    me.materials.clear(); me.materials.append(m)
    k = key(name); entry = {"metallic": metallic(m)}
    try:
        img = bake(m, 'DIFFUSE')
        img.filepath_raw = os.path.join(out, k + "_bc.png"); img.file_format = 'PNG'; img.save()
        entry["bc"] = k + "_bc.png"; bpy.data.images.remove(img)
        r = bake(m, 'ROUGHNESS')
        px = np.array(r.pixels[:], dtype=np.float32).reshape(-1, 4)
        mr = bpy.data.images.new("mr", RES, RES)
        mr.colorspace_settings.name = 'Non-Color'
        packed = np.zeros_like(px); packed[:, 1] = px[:, 0]; packed[:, 2] = 1.0; packed[:, 3] = 1.0  # glTF: G rough, B metal
        mr.pixels.foreach_set(packed.ravel())
        mr.filepath_raw = os.path.join(out, k + "_mr.png"); mr.file_format = 'PNG'; mr.save()
        entry["mr"] = k + "_mr.png"
        bpy.data.images.remove(r); bpy.data.images.remove(mr)
    except Exception as e:
        entry["error"] = str(e)
    result[name] = entry
    print("@@BAKED %d/%d %s" % (i + 1, len(mats), name), flush=True)

json.dump(result, open(os.path.join(out, "baked.json"), "w"), indent=1)
print("@@DONE", len(result))
