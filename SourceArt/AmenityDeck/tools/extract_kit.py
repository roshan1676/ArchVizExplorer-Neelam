"""Pull single assets out of the client amenity .blend files (READ-ONLY: the source file is never saved) into
SourceArt/AmenityDeck/kit/<KIT_name>/ :  <KIT_name>.fbx  (one joined mesh, base centred on the origin, metres)
                                         textures/*  (packed images written as-is, original bytes)
                                         materials.json (per material slot: images on base colour / alpha / normal /
                                         roughness, constant colour, foliage guess)  -> Scripts/Neelam/AmenityDeck_Kit.py
Usage (live Blender, source file already open):
    exec(open(r'.../extract_kit.py').read()); extract('KIT_Lounger', objs)   objs = list of object names
`cluster(names_prefixes, pick=0)` returns the object names of one copy when a set is repeated around the scene."""
import bpy, bmesh, json, os, re
from mathutils import Vector

KIT = r'C:/Users/Admin/Documents/Unreal Projects/ArchVizExplorer-Neelam/SourceArt/AmenityDeck/kit'
FOLIAGE = re.compile(r'leaf|leav|gras|flowe|plant|palm|fond|fern|bush|hedge|ivy|bamboo|miscanth|laurel|huckle|frond|petal', re.I)


def upstream(sock, depth=0, chan=None):
    """(image, channel) feeding a socket, walking back through colour-adjust / mix / reroute / separate-colour /
    normal-map nodes. channel = 'R'/'G'/'B'/'A' when a single channel is taken, else None."""
    if not sock or not sock.is_linked or depth > 8:
        return None, None
    l = sock.links[0]; n = l.from_node
    if n.type == 'TEX_IMAGE' and n.image:
        return n.image, ('A' if l.from_socket.name == 'Alpha' else chan)
    if n.type in ('SEPARATE_COLOR', 'SEPARATE_RGB'):
        chan = {'Red': 'R', 'Green': 'G', 'Blue': 'B', 'R': 'R', 'G': 'G', 'B': 'B'}.get(l.from_socket.name, chan)
    for i in n.inputs:
        if i.is_linked and i.type in ('RGBA', 'VALUE', 'VECTOR', 'CUSTOM'):
            im, c = upstream(i, depth + 1, chan)
            if im:
                return im, c
    return None, None


def write_image(im, tdir):
    ext = {'JPEG': '.jpg', 'PNG': '.png', 'TARGA': '.tga', 'OPEN_EXR': '.exr', 'TIFF': '.tif'}.get(im.file_format, '.png')
    name = re.sub(r'[^A-Za-z0-9]+', '_', im.name).strip('_') + ext          # keep .001 suffixes: they are different images
    p = os.path.join(tdir, name)
    if not os.path.exists(p):
        if im.packed_file:
            open(p, 'wb').write(im.packed_file.data)
        else:
            src = bpy.path.abspath(im.filepath)
            if not os.path.exists(src):
                return None
            open(p, 'wb').write(open(src, 'rb').read())
    return name


def material_info(m, tdir):
    d = {'name': m.name, 'foliage': bool(FOLIAGE.search(m.name)), 'color': [0.5, 0.5, 0.5], 'rough': 0.6, 'metal': 0.0,
         'masked': getattr(m, 'blend_method', 'OPAQUE') in ('CLIP', 'HASHED', 'BLEND')}
    if not m.use_nodes:
        d['color'] = list(m.diffuse_color[:3]); return d
    nodes = m.node_tree.nodes
    bsdf = next((n for n in nodes if n.type == 'BSDF_PRINCIPLED'), None)
    grp = next((n for n in nodes if n.type == 'GROUP'), None)
    socks = {}
    if bsdf:
        d['color'] = list(bsdf.inputs['Base Color'].default_value[:3])
        d['rough'] = bsdf.inputs['Roughness'].default_value; d['metal'] = bsdf.inputs['Metallic'].default_value
        socks = {'base': bsdf.inputs['Base Color'], 'alpha': bsdf.inputs['Alpha'], 'rough_tex': bsdf.inputs['Roughness'],
                 'metal_tex': bsdf.inputs['Metallic'], 'normal': bsdf.inputs['Normal']}
    elif grp:
        pick = lambda *ks: next((i for i in grp.inputs if i.name.lower() in ks and i.is_linked), None)
        socks = {'base': pick('diffuse', 'base color', 'albedo', 'color'), 'alpha': pick('alpha', 'opacity', 'mask'),
                 'rough_tex': pick('rough', 'roughness'), 'normal': pick('normal'), 'transl': pick('translucency', 'subsurface')}
    tr = next((n for n in nodes if n.type == 'BSDF_TRANSLUCENT'), None)
    if tr:
        socks['transl'] = tr.inputs['Color']
    mix = next((n for n in nodes if n.type == 'MIX_SHADER' and any(l.from_node.type == 'BSDF_TRANSPARENT' for i in n.inputs for l in i.links)), None)
    if mix and not (socks.get('alpha') and socks['alpha'].is_linked):
        socks['alpha'] = mix.inputs['Fac'] if 'Fac' in mix.inputs else mix.inputs[0]
    for key, sock in socks.items():
        im, ch = upstream(sock)
        if im:
            d[key] = write_image(im, tdir)
            if ch:
                d[key + '_ch'] = ch
    if d['masked'] and not d.get('alpha') and d.get('base'):
        d['alpha'] = d['base']; d['alpha_ch'] = 'A'
    return d


def cluster(prefixes, pick=0, radius=3.0):
    objs = [o for o in bpy.data.objects if o.type == 'MESH' and any(o.name.startswith(p) for p in prefixes)]
    groups = []
    for o in sorted(objs, key=lambda o: (round(o.matrix_world.translation.x, 1), o.name)):
        c = o.matrix_world.translation
        for g in groups:
            if (g[0].matrix_world.translation - c).length < radius:
                g.append(o); break
        else:
            groups.append([o])
    return [o.name for o in groups[pick]] if groups else []


def extract(kit_name, names, max_faces=2_500_000):
    out = os.path.join(KIT, kit_name); tdir = os.path.join(out, 'textures')
    os.makedirs(tdir, exist_ok=True)
    src = [bpy.data.objects[n] for n in names if n in bpy.data.objects and bpy.data.objects[n].type == 'MESH']
    dg = bpy.context.evaluated_depsgraph_get()
    bm = bmesh.new(); mats = []
    for o in src:
        me = o.evaluated_get(dg).to_mesh()
        me.transform(o.matrix_world)
        while len(me.uv_layers) > 1:          # one UV channel, same name for every part (UE UV0)
            me.uv_layers.remove(me.uv_layers[-1])
        if me.uv_layers:
            me.uv_layers[0].name = 'UVMap'
        slot_map = []
        for m in o.data.materials:
            if m and m not in mats:
                mats.append(m)
            slot_map.append(mats.index(m) if m else 0)
        tmp = bmesh.new(); tmp.from_mesh(me)
        for f in tmp.faces:
            f.material_index = slot_map[f.material_index] if f.material_index < len(slot_map) else 0
        tmp.to_mesh(me)
        bm.from_mesh(me)                      # appends (keeps UVs of the same layer name)
        tmp.free(); o.evaluated_get(dg).to_mesh_clear()
    if len(bm.faces) > max_faces:
        raise RuntimeError('%s: %d faces, over budget' % (kit_name, len(bm.faces)))
    # base centre -> origin
    xs = [v.co.x for v in bm.verts]; ys = [v.co.y for v in bm.verts]; zs = [v.co.z for v in bm.verts]
    off = Vector(((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, min(zs)))
    for v in bm.verts:
        v.co -= off
    me = bpy.data.meshes.new(kit_name); bm.to_mesh(me); bm.free()
    for m in mats:
        me.materials.append(m)
    ob = bpy.data.objects.new(kit_name, me)
    bpy.context.scene.collection.objects.link(ob)
    bpy.ops.object.select_all(action='DESELECT'); ob.select_set(True); bpy.context.view_layer.objects.active = ob
    bpy.ops.export_scene.fbx(filepath=os.path.join(out, kit_name + '.fbx'), use_selection=True, apply_unit_scale=True,
                             apply_scale_options='FBX_SCALE_UNITS', mesh_smooth_type='FACE', add_leaf_bones=False,
                             bake_anim=False, object_types={'MESH'}, path_mode='STRIP')
    info = {'kit': kit_name, 'faces': len(me.polygons), 'size_m': [round(max(xs) - min(xs), 3), round(max(ys) - min(ys), 3), round(max(zs) - min(zs), 3)],
            'source': bpy.data.filepath, 'objects': names, 'materials': [material_info(m, tdir) for m in mats]}
    json.dump(info, open(os.path.join(out, 'materials.json'), 'w'), indent=1)
    bpy.data.objects.remove(ob, do_unlink=True); bpy.data.meshes.remove(me)
    return {k: info[k] for k in ('kit', 'faces', 'size_m')} | {'mats': len(mats)}
