"""Procedural frangipani (Plumeria) tree: candelabra branching, leaf rosettes at tips, 5-petal flowers.
Quad/UV'd geometry, 3 variants normalised to a 5 m canopy. Creates collection 03_Landscape/PLANT_SOURCES/Frangipani.
Run in Blender: exec(open(r'C:/Users/Admin/Desktop/commercial-office/tools/frangipani.py').read())
"""
import bpy, bmesh, math, random
from mathutils import Vector, Matrix, Quaternion
exec(open(r'C:/Users/Admin/Documents/Unreal Projects/ArchVizExplorer-Neelam/SourceArt/AmenityDeck/tools/blib.py').read())


def mat_bark():
    m = bpy.data.materials.get('M_Plumeria_Bark')
    if m:
        return m
    m = bpy.data.materials.new('M_Plumeria_Bark'); m.use_nodes = True
    nt = m.node_tree; b = nt.nodes['Principled BSDF']
    tc = nt.nodes.new('ShaderNodeTexCoord'); ns = nt.nodes.new('ShaderNodeTexNoise')
    ns.inputs['Scale'].default_value = 18; ns.inputs['Detail'].default_value = 8
    cr = nt.nodes.new('ShaderNodeValToRGB')
    cr.color_ramp.elements[0].color = (0.22, 0.2, 0.17, 1); cr.color_ramp.elements[1].color = (0.42, 0.39, 0.34, 1)
    bump = nt.nodes.new('ShaderNodeBump'); bump.inputs['Strength'].default_value = 0.35
    nt.links.new(tc.outputs['UV'], ns.inputs['Vector']); nt.links.new(ns.outputs['Fac'], cr.inputs['Fac'])
    nt.links.new(cr.outputs['Color'], b.inputs['Base Color']); nt.links.new(ns.outputs['Fac'], bump.inputs['Height'])
    nt.links.new(bump.outputs['Normal'], b.inputs['Normal'])
    b.inputs['Roughness'].default_value = 0.8
    m.diffuse_color = (0.35, 0.32, 0.28, 1)
    return m


def mat_leaf():
    m = bpy.data.materials.get('M_Plumeria_Leaf')
    if m:
        return m
    m = bpy.data.materials.new('M_Plumeria_Leaf'); m.use_nodes = True
    nt = m.node_tree; b = nt.nodes['Principled BSDF']
    tc = nt.nodes.new('ShaderNodeTexCoord'); sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    cr = nt.nodes.new('ShaderNodeValToRGB')  # lighter midrib along U=0.5
    mth = nt.nodes.new('ShaderNodeMath'); mth.operation = 'ABSOLUTE'
    sub = nt.nodes.new('ShaderNodeMath'); sub.operation = 'SUBTRACT'; sub.inputs[1].default_value = 0.5
    cr.color_ramp.elements[0].color = (0.25, 0.42, 0.12, 1); cr.color_ramp.elements[0].position = 0.0
    cr.color_ramp.elements[1].color = (0.05, 0.2, 0.03, 1); cr.color_ramp.elements[1].position = 0.04
    nt.links.new(tc.outputs['UV'], sep.inputs[0]); nt.links.new(sep.outputs['X'], sub.inputs[0])
    nt.links.new(sub.outputs[0], mth.inputs[0]); nt.links.new(mth.outputs[0], cr.inputs['Fac'])
    nt.links.new(cr.outputs['Color'], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.35
    b.inputs['Subsurface Weight'].default_value = 0.15
    b.inputs['Transmission Weight'].default_value = 0.0
    m.diffuse_color = (0.08, 0.25, 0.05, 1)
    return m


def mat_flower():
    m = bpy.data.materials.get('M_Plumeria_Flower')
    if m:
        return m
    m = bpy.data.materials.new('M_Plumeria_Flower'); m.use_nodes = True
    nt = m.node_tree; b = nt.nodes['Principled BSDF']
    tc = nt.nodes.new('ShaderNodeTexCoord'); sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    cr = nt.nodes.new('ShaderNodeValToRGB')  # yellow throat (V=0) -> cream white petal tip
    cr.color_ramp.elements[0].color = (0.98, 0.78, 0.15, 1); cr.color_ramp.elements[0].position = 0.1
    cr.color_ramp.elements[1].color = (0.97, 0.95, 0.9, 1); cr.color_ramp.elements[1].position = 0.45
    nt.links.new(tc.outputs['UV'], sep.inputs[0]); nt.links.new(sep.outputs['Y'], cr.inputs['Fac'])
    nt.links.new(cr.outputs['Color'], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.45; b.inputs['Subsurface Weight'].default_value = 0.3
    m.diffuse_color = (0.95, 0.93, 0.85, 1)
    return m


def tube(bm, pts, radii, uv, sides=12):
    """Smooth quad tube along points with per-point radius; cylindrical UVs."""
    rings = []
    up = Vector((0, 0, 1))
    acc = 0.0
    for i, p in enumerate(pts):
        t = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
        a = t.cross(up if abs(t.dot(up)) < 0.95 else Vector((1, 0, 0))).normalized()
        b_ = t.cross(a)
        if i:
            acc += (p - pts[i - 1]).length
        ring = []
        for k in range(sides + 1):
            ang = 2 * math.pi * k / sides
            ring.append((bm.verts.new(p + (a * math.cos(ang) + b_ * math.sin(ang)) * radii[i]), (k / sides, acc)))
        rings.append(ring)
    for r0, r1 in zip(rings, rings[1:]):
        for k in range(sides):
            f = bm.faces.new((r0[k][0], r0[k + 1][0], r1[k + 1][0], r1[k][0]))
            f.material_index = 0
            for loop, (v, uvv) in zip(f.loops, (r0[k], r0[k + 1], r1[k + 1], r1[k])):
                loop[uv].uv = (uvv[0], uvv[1] * 2.0)
    # cap the tip so the tube is closed
    tip = bm.verts.new(pts[-1] + (pts[-1] - pts[-2]).normalized() * radii[-1] * 0.6)
    for k in range(sides):
        f = bm.faces.new((rings[-1][k][0], rings[-1][k + 1][0], tip))
        for loop in f.loops:
            loop[uv].uv = (0.5, acc * 2.0)
    bmesh.ops.remove_doubles(bm, verts=[v for r in rings for v, _ in (r[0], r[-1])], dist=1e-6)


def leaf(bm, base, direction, length, width, uv, roll=0.0):
    """Obovate leaf with folded midrib and droop; 8x4 quad grid, UV 0-1."""
    d = direction.normalized()
    side = d.cross(Vector((0, 0, 1)))
    if side.length < 1e-3:
        side = Vector((1, 0, 0))
    side.normalize()
    side = Quaternion(d, roll) @ side
    nrm = side.cross(d).normalized()
    nu, nv = 4, 8
    grid = []
    for j in range(nv + 1):
        t = j / nv
        w = width * (math.sin(math.pi * min(1, t * 1.15)) ** 0.8) * (0.25 + 0.75 * t ** 0.6)
        row = []
        for i in range(nu + 1):
            s = i / nu - 0.5
            fold = -abs(s) * w * 0.35                 # V-fold along the midrib
            droop = -0.35 * length * t * t            # tip bends down
            p = base + d * length * t + side * s * w + nrm * fold + Vector((0, 0, droop))
            row.append(bm.verts.new(p))
        grid.append(row)
    for j in range(nv):
        for i in range(nu):
            f = bm.faces.new((grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i]))
            f.material_index = 1
            for loop, (ii, jj) in zip(f.loops, ((i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1))):
                loop[uv].uv = (ii / nu, jj / nv)


def flower(bm, c, up, size, uv):
    """5 overlapping twisted petals (pinwheel)."""
    up = up.normalized()
    a = up.cross(Vector((1, 0, 0)) if abs(up.x) < 0.9 else Vector((0, 1, 0))).normalized()
    for k in range(5):
        q = Quaternion(up, 2 * math.pi * k / 5)
        d = q @ a
        sd = up.cross(d)
        nv, nu = 5, 3
        grid = []
        for j in range(nv + 1):
            t = j / nv
            w = size * 0.55 * math.sin(math.pi * (0.15 + 0.85 * t)) ** 0.7
            row = []
            for i in range(nu + 1):
                s = i / nu - 0.5
                p = c + d * size * t + sd * (s * w + 0.25 * size * t) + up * (0.25 * size * (1 - t) - 0.1 * size * t * t + 0.06 * size * s)
                row.append(bm.verts.new(p))
            grid.append(row)
        for j in range(nv):
            for i in range(nu):
                f = bm.faces.new((grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i]))
                f.material_index = 2
                for loop, (ii, jj) in zip(f.loops, ((i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1))):
                    loop[uv].uv = (ii / nu, jj / nv)


def build(name, seed, coll):
    rnd = random.Random(seed)
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new('UVMap')
    tips = []

    def grow(p, d, r, depth, length):
        pts, radii = [p], [r]
        n = 8
        cur, dd = p.copy(), d.copy()
        for k in range(1, n + 1):
            dd = (dd + Vector((rnd.uniform(-0.08, 0.08), rnd.uniform(-0.08, 0.08), 0.03))).normalized()
            cur = cur + dd * length / n
            pts.append(cur.copy()); radii.append(r * (1 - 0.18 * k / n))
        tube(bm, pts, radii, uv)
        if depth >= 4:
            tips.append((cur, dd))
            return
        kids = 3 if depth < 2 and rnd.random() < 0.55 else 2
        for c in range(kids):
            ang = 2 * math.pi * c / kids + rnd.uniform(-0.5, 0.5)
            spread = math.radians(rnd.uniform(42, 62))
            ax = Vector((math.cos(ang), math.sin(ang), 0))
            nd = (dd * math.cos(spread) + ax * math.sin(spread)).normalized()
            grow(cur - dd * 0.03, nd, radii[-1] * 0.78, depth + 1, length * rnd.uniform(0.72, 0.86))

    grow(Vector((0, 0, 0)), Vector((rnd.uniform(-0.1, 0.1), rnd.uniform(-0.1, 0.1), 1)).normalized(), 0.14, 0, 1.15)
    for p, d in tips:
        nl = rnd.randint(20, 28)
        for k in range(nl):
            az = 2 * math.pi * k / nl + rnd.uniform(-0.15, 0.15)
            el = math.radians(rnd.uniform(15, 55))
            ld = Vector((math.cos(az) * math.cos(el), math.sin(az) * math.cos(el), math.sin(el)))
            ld = (ld + d * 0.4).normalized()
            leaf(bm, p, ld, rnd.uniform(0.45, 0.62), rnd.uniform(0.13, 0.17), uv, roll=rnd.uniform(-0.3, 0.3))
        if rnd.random() < 0.7:  # flower cluster on a short stalk above the rosette
            fc = p + d * 0.12 + Vector((0, 0, 0.06))
            for k in range(rnd.randint(5, 9)):
                off = Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(0, 0.6))).normalized() * rnd.uniform(0.03, 0.09)
                flower(bm, fc + off, (off + Vector((0, 0, 0.6))), rnd.uniform(0.07, 0.085), uv)
    old = bpy.data.objects.get(name)
    if old:
        bpy.data.objects.remove(old, do_unlink=True)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me); bm.free()
    for m in (mat_bark(), mat_leaf(), mat_flower()):
        me.materials.append(m)
    me.shade_smooth()
    o = bpy.data.objects.new(name, me)
    coll.objects.link(o)
    # normalise to a 5 m canopy diameter
    xs = [v.co.x for v in me.vertices]; ys = [v.co.y for v in me.vertices]
    span = max(max(xs) - min(xs), max(ys) - min(ys))
    o.scale = (5.0 / span,) * 3
    bpy.context.view_layer.update()
    bpy.ops.object.select_all(action='DESELECT')
    o.select_set(True); bpy.context.view_layer.objects.active = o
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return o


src = collection('03_Landscape/PLANT_SOURCES/Frangipani')
made = [build(f'Plumeria_{k}', s, src) for k, s in (('A', 3), ('B', 11), ('C', 29))]
for i, o in enumerate(made):
    o.location = (i * 7.0, -230, 0)
bpy.ops.wm.save_mainfile()
result = {o.name: {'polys': len(o.data.polygons), 'dims': [round(v, 2) for v in o.dimensions]} for o in made}
