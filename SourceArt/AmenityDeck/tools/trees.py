"""DWG trees for the amenity deck, procedural (no tree of these species in the free stores):
  KIT_Plumeria_A/B/C   Plumeria alba (frangipani): candelabra branching, leaf rosettes, 5-petal white/yellow flowers.
                       DWG canopy circle r 1.573 -> normalised to 3.2 m canopy.
  KIT_Terminalia_A/B   Terminalia mantaly (Madagascar almond): straight trunk, 6-7 whorls of horizontal tiered
                       branches, small spoon leaves in rosettes. DWG canopy r 2.0 -> 4.0 m canopy, ~5.5 m tall.
Textures are painted here (numpy/Pillow-free: written by Blender's image API) and exported with a materials.json in the
same format as extract_kit.py, so Scripts/Neelam/AmenityDeck_Kit.py imports them like every other kit.
Run in the live Blender:  exec(open(r'<this file>').read()); result = build_all()
"""
import bpy, bmesh, json, math, os, random
from mathutils import Vector, Quaternion

KIT = r'C:/Users/Admin/Documents/Unreal Projects/ArchVizExplorer-Neelam/SourceArt/AmenityDeck/kit'
BARK_SRC = r'C:/Users/Admin/Documents/Unreal Projects/ArchVizExplorer-Neelam/SourceArt/PolyHaven/bark_brown_02'


# ---------------------------------------------------------------- textures (written with bpy images, no deps)
def paint(name, w, h, fn, path):
    """fn(u, v) -> (r, g, b, a) in 0..1, u/v in 0..1."""
    if os.path.exists(path):
        return path
    im = bpy.data.images.new(name, w, h, alpha=True)
    px = [0.0] * (w * h * 4)
    for j in range(h):
        v = (j + 0.5) / h
        for i in range(w):
            r, g, b, a = fn((i + 0.5) / w, v)
            k = (j * w + i) * 4
            px[k:k + 4] = (r, g, b, a)
    im.pixels.foreach_set(px)
    im.filepath_raw = path; im.file_format = 'PNG'; im.save()
    bpy.data.images.remove(im)
    return path


def leaf_fn(base, rib, edge_dark=0.75):
    """Leaf colour: base green, lighter midrib along u = 0.5, faint pinnate veins, darker margin."""
    def f(u, v):
        d = abs(u - 0.5)
        rib_k = max(0.0, 1 - d / 0.035)
        vein = max(0.0, 1 - abs(((d * 6 + v * 2.2) % 1.0) - 0.5) / 0.08) * 0.18 * (1 - rib_k)
        m = 1 - (1 - edge_dark) * max(0.0, (d - 0.38) / 0.12)
        c = [base[i] * m + (rib[i] - base[i]) * (rib_k + vein) for i in range(3)]
        return (*c, 1.0)
    return f


def flower_fn(u, v):
    t = min(1.0, max(0.0, (v - 0.08) / 0.4))          # yellow throat -> cream-white petal
    c = [0.98 * (1 - t) + 0.97 * t, 0.74 * (1 - t) + 0.95 * t, 0.12 * (1 - t) + 0.88 * t]
    return (*c, 1.0)


def rough_fn(k):
    return lambda u, v: (k, k, k, 1.0)


# ---------------------------------------------------------------- geometry helpers
def tube(bm, uv, pts, radii, sides=10, mat=0):
    up = Vector((0, 0, 1)); rings = []; acc = 0.0
    for i, p in enumerate(pts):
        t = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
        a = t.cross(up if abs(t.dot(up)) < 0.95 else Vector((1, 0, 0))).normalized(); b_ = t.cross(a)
        if i:
            acc += (p - pts[i - 1]).length
        rings.append([(bm.verts.new(p + (a * math.cos(2 * math.pi * k / sides) + b_ * math.sin(2 * math.pi * k / sides)) * radii[i]),
                       (k / sides, acc)) for k in range(sides + 1)])
    for r0, r1 in zip(rings, rings[1:]):
        for k in range(sides):
            f = bm.faces.new((r0[k][0], r0[k + 1][0], r1[k + 1][0], r1[k][0])); f.material_index = mat
            for loop, (v, q) in zip(f.loops, (r0[k], r0[k + 1], r1[k + 1], r1[k])):
                loop[uv].uv = (q[0], q[1] * 1.5)
    tip = bm.verts.new(pts[-1] + (pts[-1] - pts[-2]).normalized() * radii[-1] * 0.6)
    for k in range(sides):
        f = bm.faces.new((rings[-1][k][0], rings[-1][k + 1][0], tip)); f.material_index = mat
        for loop in f.loops:
            loop[uv].uv = (0.5, acc * 1.5)


def leaf(bm, uv, base, direction, length, width, roll=0.0, droop=0.35, nu=4, nv=6, mat=1, obovate=False):
    d = direction.normalized(); side = d.cross(Vector((0, 0, 1)))
    side = Vector((1, 0, 0)) if side.length < 1e-3 else side.normalized()
    side = Quaternion(d, roll) @ side; nrm = side.cross(d).normalized()
    grid = []
    for j in range(nv + 1):
        t = j / nv
        shape = (math.sin(math.pi * min(1, t * 1.15)) ** 0.8) * ((0.25 + 0.75 * t ** 0.6) if obovate else 1.0)
        w = width * shape
        grid.append([bm.verts.new(base + d * length * t + side * (i / nu - 0.5) * w + nrm * (-abs(i / nu - 0.5) * w * 0.35)
                                  + Vector((0, 0, -droop * length * t * t))) for i in range(nu + 1)])
    for j in range(nv):
        for i in range(nu):
            f = bm.faces.new((grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i])); f.material_index = mat
            for loop, (ii, jj) in zip(f.loops, ((i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1))):
                loop[uv].uv = (ii / nu, jj / nv)


def flower(bm, uv, c, up, size, mat=2):
    up = up.normalized(); a = up.cross(Vector((1, 0, 0)) if abs(up.x) < 0.9 else Vector((0, 1, 0))).normalized()
    for k in range(5):
        d = Quaternion(up, 2 * math.pi * k / 5) @ a; sd = up.cross(d); grid = []
        for j in range(6):
            t = j / 5; w = size * 0.55 * math.sin(math.pi * (0.15 + 0.85 * t)) ** 0.7
            grid.append([bm.verts.new(c + d * size * t + sd * ((i / 3 - 0.5) * w + 0.25 * size * t)
                                      + up * (0.25 * size * (1 - t) - 0.1 * size * t * t + 0.06 * size * (i / 3 - 0.5))) for i in range(4)])
        for j in range(5):
            for i in range(3):
                f = bm.faces.new((grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i])); f.material_index = mat
                for loop, (ii, jj) in zip(f.loops, ((i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1))):
                    loop[uv].uv = (ii / 3, jj / 5)


# ---------------------------------------------------------------- species
def plumeria(seed):
    rnd = random.Random(seed); bm = bmesh.new(); uv = bm.loops.layers.uv.new('UVMap'); tips = []

    def grow(p, d, r, depth, length):
        pts, radii = [p], [r]; cur, dd = p.copy(), d.copy()
        for k in range(1, 9):
            dd = (dd + Vector((rnd.uniform(-0.08, 0.08), rnd.uniform(-0.08, 0.08), 0.03))).normalized()
            cur = cur + dd * length / 8; pts.append(cur.copy()); radii.append(r * (1 - 0.18 * k / 8))
        tube(bm, uv, pts, radii)
        if depth >= 4:
            tips.append((cur, dd)); return
        for c in range(3 if depth < 2 and rnd.random() < 0.55 else 2):
            ang = 2 * math.pi * c / 3 + rnd.uniform(-0.5, 0.5); spread = math.radians(rnd.uniform(42, 62))
            nd = (dd * math.cos(spread) + Vector((math.cos(ang), math.sin(ang), 0)) * math.sin(spread)).normalized()
            grow(cur - dd * 0.03, nd, radii[-1] * 0.78, depth + 1, length * rnd.uniform(0.72, 0.86))
    grow(Vector((0, 0, 0)), Vector((rnd.uniform(-0.1, 0.1), rnd.uniform(-0.1, 0.1), 1)).normalized(), 0.14, 0, 1.15)
    for p, d in tips:
        nl = rnd.randint(20, 28)
        for k in range(nl):
            az = 2 * math.pi * k / nl + rnd.uniform(-0.15, 0.15); el = math.radians(rnd.uniform(15, 55))
            ld = (Vector((math.cos(az) * math.cos(el), math.sin(az) * math.cos(el), math.sin(el))) + d * 0.4).normalized()
            leaf(bm, uv, p, ld, rnd.uniform(0.45, 0.62), rnd.uniform(0.13, 0.17), roll=rnd.uniform(-0.3, 0.3), obovate=True, nv=8)
        if rnd.random() < 0.7:
            fc = p + d * 0.12 + Vector((0, 0, 0.06))
            for k in range(rnd.randint(5, 9)):
                off = Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(0, 0.6))).normalized() * rnd.uniform(0.03, 0.09)
                flower(bm, uv, fc + off, off + Vector((0, 0, 0.6)), rnd.uniform(0.07, 0.085))
    return bm, 3.2


def terminalia(seed):
    """Pagoda tree: vertical trunk, tiers of 4-6 near-horizontal branches; each branch ends in sub-branches whose tips
    carry rosettes of small spoon-shaped leaves; tiers shrink upward (DWG canopy 4 m)."""
    rnd = random.Random(seed); bm = bmesh.new(); uv = bm.loops.layers.uv.new('UVMap')
    H = rnd.uniform(5.2, 5.8)
    trunk = [Vector((rnd.uniform(-0.006, 0.006) * k, rnd.uniform(-0.006, 0.006) * k, H * k / 10)) for k in range(11)]
    tube(bm, uv, trunk, [0.11 * (1 - 0.75 * k / 10) + 0.012 for k in range(11)], sides=12)
    tiers = 7; z0 = 1.9
    for t in range(tiers):
        z = z0 + (H - 0.3 - z0) * t / (tiers - 1)
        reach = 2.0 * (1 - 0.72 * t / (tiers - 1)) * rnd.uniform(0.9, 1.05)
        nb = rnd.randint(4, 6); rot = rnd.uniform(0, 6.283)
        for b in range(nb):
            ang = rot + 2 * math.pi * b / nb + rnd.uniform(-0.25, 0.25)
            ax = Vector((math.cos(ang), math.sin(ang), 0)); p0 = Vector((0, 0, z))
            pts = [p0 + ax * reach * s + Vector((0, 0, 0.12 * math.sin(s * 2.4) * reach)) for s in (0, 0.25, 0.5, 0.75, 1.0)]
            tube(bm, uv, pts, [0.035 * (1 - 0.6 * s) for s in (0, 0.25, 0.5, 0.75, 1.0)], sides=6)
            # rosettes along the outer half of each branch + twig forks
            for s in (0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0):          # dense flat leaf pads = the tiered 'shelves'
                for fork in (-1, 1) if s < 1.0 else (-1, 0, 1):
                    base = pts[0] + ax * reach * s + Vector((0, 0, 0.12 * math.sin(s * 2.4) * reach))
                    tw = (ax + ax.cross(Vector((0, 0, 1))) * 0.8 * fork).normalized()
                    tipp = base + tw * rnd.uniform(0.14, 0.26) + Vector((0, 0, 0.04))
                    tube(bm, uv, [base, tipp], [0.012, 0.006], sides=4)
                    nl = rnd.randint(10, 14)
                    for k in range(nl):
                        az = 2 * math.pi * k / nl + rnd.uniform(-0.2, 0.2)
                        ld = Vector((math.cos(az), math.sin(az), rnd.uniform(0.15, 0.45))).normalized()
                        leaf(bm, uv, tipp, ld, rnd.uniform(0.10, 0.15), rnd.uniform(0.045, 0.065), roll=rnd.uniform(-0.4, 0.4),
                             droop=0.15, nu=2, nv=4, obovate=True)
    return bm, 4.0


# ---------------------------------------------------------------- materials / export
def mats(kit, leaf_cols):
    tdir = os.path.join(KIT, kit, 'textures'); os.makedirs(tdir, exist_ok=True)
    paint('leaf_' + kit, 128, 256, leaf_fn(*leaf_cols), os.path.join(tdir, 'leaf_diff.png'))
    paint('leafr_' + kit, 8, 8, rough_fn(0.42), os.path.join(tdir, 'leaf_rough.png'))
    paint('flower_' + kit, 64, 128, flower_fn, os.path.join(tdir, 'flower_diff.png'))
    for f, dst in (('bark_brown_02_diff_2k.jpg', 'bark_diff.jpg'), ('bark_brown_02_nor_gl_2k.jpg', 'bark_nor.jpg'), ('bark_brown_02_rough_2k.jpg', 'bark_rough.jpg')):
        src = os.path.join(BARK_SRC, f)
        if os.path.exists(src) and not os.path.exists(os.path.join(tdir, dst)):
            open(os.path.join(tdir, dst), 'wb').write(open(src, 'rb').read())
    # foliage needs an alpha texture to use the foliage master; leaves are real geometry -> solid white mask
    paint('mask_' + kit, 8, 8, lambda u, v: (1, 1, 1, 1), os.path.join(tdir, 'solid_mask.png'))
    return [
        {'name': 'Bark', 'foliage': False, 'color': [0.35, 0.3, 0.26], 'rough': 0.85, 'metal': 0.0, 'masked': False,
         'base': 'bark_diff.jpg', 'normal': 'bark_nor.jpg', 'rough_tex': 'bark_rough.jpg'},
        {'name': 'Leaf', 'foliage': True, 'color': [0.2, 0.4, 0.1], 'rough': 0.42, 'metal': 0.0, 'masked': True,
         'base': 'leaf_diff.png', 'rough_tex': 'leaf_rough.png', 'alpha': 'solid_mask.png', 'transl': 'leaf_diff.png'},
        {'name': 'Flower', 'foliage': True, 'color': [0.95, 0.93, 0.85], 'rough': 0.5, 'metal': 0.0, 'masked': True,
         'base': 'flower_diff.png', 'rough_tex': 'leaf_rough.png', 'alpha': 'solid_mask.png', 'transl': 'flower_diff.png'},
    ]


def export(kit, bm, canopy, leaf_cols):
    col = bpy.data.collections.get('AD_Trees') or bpy.data.collections.new('AD_Trees')
    if col.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(col)
    old = bpy.data.objects.get(kit)
    if old:
        bpy.data.objects.remove(old, do_unlink=True)
    me = bpy.data.meshes.new(kit); bm.to_mesh(me); bm.free()
    for n in ('M_Tree_Bark', 'M_Tree_Leaf', 'M_Tree_Flower'):
        me.materials.append(bpy.data.materials.get(n) or bpy.data.materials.new(n))
    me.shade_smooth()
    xs = [v.co.x for v in me.vertices]; ys = [v.co.y for v in me.vertices]
    k = canopy / max(max(xs) - min(xs), max(ys) - min(ys))
    for v in me.vertices:
        v.co *= k
    o = bpy.data.objects.new(kit, me); col.objects.link(o)
    os.makedirs(os.path.join(KIT, kit), exist_ok=True)
    bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active = o
    bpy.ops.export_scene.fbx(filepath=os.path.join(KIT, kit, kit + '.fbx'), use_selection=True, apply_unit_scale=True,
                             apply_scale_options='FBX_SCALE_UNITS', mesh_smooth_type='FACE', add_leaf_bones=False, bake_anim=False,
                             object_types={'MESH'})
    zs = [v.co.z for v in me.vertices]
    info = {'kit': kit, 'faces': len(me.polygons), 'size_m': [round(canopy, 2), round(canopy, 2), round(max(zs), 2)],
            'source': 'procedural tools/trees.py', 'materials': mats(kit, leaf_cols)}
    json.dump(info, open(os.path.join(KIT, kit, 'materials.json'), 'w'), indent=1)
    return {'faces': info['faces'], 'size_m': info['size_m']}


PLUMERIA_LEAF = ((0.10, 0.26, 0.05), (0.42, 0.55, 0.20))
TERMINALIA_LEAF = ((0.16, 0.34, 0.07), (0.38, 0.52, 0.18))


def build_all():
    res = {}
    for k, s in (('A', 3), ('B', 11), ('C', 29)):
        bm, c = plumeria(s); res['KIT_Plumeria_' + k] = export('KIT_Plumeria_' + k, bm, c, PLUMERIA_LEAF)
    for k, s in (('A', 5), ('B', 17)):
        bm, c = terminalia(s); res['KIT_Terminalia_' + k] = export('KIT_Terminalia_' + k, bm, c, TERMINALIA_LEAF)
    return res
