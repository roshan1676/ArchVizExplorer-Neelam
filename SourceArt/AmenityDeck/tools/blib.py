"""Shared helpers for building the Vasai office site in Blender.

Run inside Blender: exec(open(r'...tools/blib.py').read())
Coordinates `px, py` are pixels of the 1740-px-wide plan preview (A.001 cropped to 8700 px, /5),
mapped to world space through the aligned REF_SitePlan_A001 image empty.
"""
import bpy, bmesh, math
from mathutils import Vector, Matrix

PLAN = 'REF_SitePlan_A001'


def P(px, py, z=0.0):
    e = bpy.data.objects[PLAN]
    w, h = e.data.size
    u, v = px * 5 / w, py * 5 / h
    size = e.empty_display_size
    local = Vector(((u + e.empty_image_offset[0]) * size, (0.5 - v) * size * h / w, 0))
    p = e.matrix_world @ local
    p.z = z
    return p


def M_PER_PX():
    return (P(0, 0) - P(100, 0)).length / 100


def smooth(pts, n=8, closed=False):
    """Catmull-Rom through points -> dense polyline (list of Vector)."""
    pts = [Vector(p) for p in pts]
    out = []
    m = len(pts)
    segs = m if closed else m - 1
    for i in range(segs):
        p0 = pts[(i - 1) % m] if closed or i > 0 else pts[0]
        p1, p2 = pts[i], pts[(i + 1) % m]
        p3 = pts[(i + 2) % m] if closed or i + 2 < m else pts[-1]
        for k in range(n):
            t = k / n
            t2, t3 = t * t, t * t * t
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    if not closed:
        out.append(pts[-1])
    return out


def collection(path):
    parent = bpy.context.scene.collection
    for name in path.split('/'):
        c = bpy.data.collections.get(name)
        if not c:
            c = bpy.data.collections.new(name)
        if name not in parent.children:
            parent.children.link(c)
        parent = c
    return parent


def material(name, color, rough=0.6, metal=0.0, transmission=0.0, ior=1.45):
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*color, 1)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    b.inputs['Transmission Weight'].default_value = transmission
    b.inputs['IOR'].default_value = ior
    m.diffuse_color = (*color, 1)
    return m


def uv_box(bm, mw=Matrix()):
    uv = bm.loops.layers.uv.get('UV_World') or bm.loops.layers.uv.new('UV_World')
    nm = mw.to_3x3().inverted().transposed()
    for f in bm.faces:
        n = nm @ f.normal
        a = [abs(n.x), abs(n.y), abs(n.z)]
        ax = a.index(max(a))
        for l in f.loops:
            p = mw @ l.vert.co
            if ax == 2:
                l[uv].uv = (p.x, p.y)
            elif ax == 0:
                l[uv].uv = (p.y * (1 if n.x > 0 else -1), p.z)
            else:
                l[uv].uv = (p.x * (-1 if n.y > 0 else 1), p.z)


def finish(bm, name, coll, mats, bevel=0.01, segments=2, uv=True):
    """bmesh -> object with UVs (uv=False: caller already set them), bevel (harden normals) and smooth shading."""
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    if uv:
        uv_box(bm)
    old = bpy.data.objects.get(name)
    if old:
        bpy.data.objects.remove(old, do_unlink=True)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for m in mats:
        me.materials.append(m)
    if bevel:
        me.shade_smooth()  # bevel modifier harden_normals keeps flats crisp
    else:
        me.shade_flat()
    o = bpy.data.objects.new(name, me)
    coll.objects.link(o)
    if bevel:
        mod = o.modifiers.new('Bevel', 'BEVEL')
        mod.width = bevel
        mod.segments = segments
        mod.limit_method = 'ANGLE'
        mod.angle_limit = math.radians(40)
        mod.harden_normals = True
    return o


def add_prism(bm, outline, z0, h, mat_index=0):
    """Closed outline (Vectors) extruded from z0 to z0+h. Returns top face."""
    pts = list(outline)
    area = sum(a.x * b.y - b.x * a.y for a, b in zip(pts, pts[1:] + pts[:1]))
    if area < 0:
        pts.reverse()  # counter-clockwise
    bot = [bm.verts.new((p.x, p.y, z0)) for p in pts]
    top = [bm.verts.new((p.x, p.y, z0 + h)) for p in pts]
    n = len(pts)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((bot[i], bot[j], top[j], top[i])).material_index = mat_index
    ft = bm.faces.new(top)
    ft.material_index = mat_index
    bm.faces.new(list(reversed(bot))).material_index = mat_index
    return ft


def add_box(bm, center, size, rot_z=0.0, mat_index=0):
    """Axis box, quads only. center = bottom-centre? no: geometric centre."""
    r = bmesh.ops.create_cube(bm, size=1.0)
    vs = r['verts']
    m = Matrix.Translation(center) @ Matrix.Rotation(rot_z, 4, 'Z') @ Matrix.Diagonal((*size, 1))
    bmesh.ops.transform(bm, matrix=m, verts=vs)
    for f in {f for v in vs for f in v.link_faces}:
        f.material_index = mat_index
    return vs


def offset_line(line, d):
    """Offset an open polyline sideways by d (left positive)."""
    out = []
    for i, p in enumerate(line):
        a = line[max(i - 1, 0)]
        b = line[min(i + 1, len(line) - 1)]
        t = (b - a).normalized()
        n = Vector((-t.y, t.x, 0))
        out.append(p + n * d)
    return out


def add_strip(bm, line, width, z0, h, mat_index=0):
    """Quad-strip solid of given width along an open polyline."""
    L = offset_line(line, width / 2)
    R = offset_line(line, -width / 2)
    rows = []
    for z in (z0, z0 + h):
        rows.append(([bm.verts.new((p.x, p.y, z)) for p in L], [bm.verts.new((p.x, p.y, z)) for p in R]))
    (bl, br), (tl, tr) = rows
    for i in range(len(line) - 1):
        for quad in ((tl[i], tr[i], tr[i + 1], tl[i + 1]), (bl[i + 1], br[i + 1], br[i], bl[i]),
                     (bl[i], tl[i], tl[i + 1], bl[i + 1]), (br[i + 1], tr[i + 1], tr[i], br[i])):
            bm.faces.new(quad).material_index = mat_index
    for q in ((bl[0], br[0], tr[0], tl[0]), (tl[-1], tr[-1], br[-1], bl[-1])):
        bm.faces.new(q).material_index = mat_index


def add_ring(bm, loop, width, z0, h, mat_index=0):
    """Closed wall/kerb of given width centred on a closed polyline (no caps)."""
    pts = list(loop)
    area = sum(a.x * b.y - b.x * a.y for a, b in zip(pts, pts[1:] + pts[:1]))
    if area < 0:
        pts.reverse()
    n = len(pts)

    def off(d):
        out = []
        for i in range(n):
            t = (pts[(i + 1) % n] - pts[i - 1]).normalized()
            out.append(pts[i] + Vector((-t.y, t.x, 0)) * d)
        return out
    inner, outer = off(width / 2), off(-width / 2)
    ib = [bm.verts.new((p.x, p.y, z0)) for p in inner]
    it = [bm.verts.new((p.x, p.y, z0 + h)) for p in inner]
    ob = [bm.verts.new((p.x, p.y, z0)) for p in outer]
    ot = [bm.verts.new((p.x, p.y, z0 + h)) for p in outer]
    for i in range(n):
        j = (i + 1) % n
        for q in ((it[i], it[j], ot[j], ot[i]), (ob[i], ob[j], ib[j], ib[i]),
                  (ib[i], ib[j], it[j], it[i]), (ot[i], ot[j], ob[j], ob[i])):
            bm.faces.new(q).material_index = mat_index


def ccw(loop):
    pts = list(loop)
    if pts and (pts[0] - pts[-1]).length < 1e-6:
        pts = pts[:-1]
    area = sum(a.x * b.y - b.x * a.y for a, b in zip(pts, pts[1:] + pts[:1]))
    return pts if area > 0 else pts[::-1]


def inset(loop, d):
    """Offset a closed loop inward by d (miter, clamped)."""
    pts = ccw(loop)
    n = len(pts)
    out = []
    for i in range(n):
        a, p, b = pts[i - 1], pts[i], pts[(i + 1) % n]
        t1 = (p - a).normalized(); t2 = (b - p).normalized()
        n1 = Vector((-t1.y, t1.x, 0)); n2 = Vector((-t2.y, t2.x, 0))
        m = (n1 + n2)
        if m.length < 1e-6:
            m = n1
        m.normalize()
        s = min(1 / max(m.dot(n1), 0.3), 3)
        out.append(p + m * d * s)
    return out


def region_world(ext, z=0.0):
    pts = [P(x, y, z) for x, y in ext]
    return ccw(pts)


def resample(line, step):
    """Evenly spaced points along a polyline."""
    out = [line[0]]
    carry = 0.0
    for a, b in zip(line, line[1:]):
        seg = (b - a).length
        d = step - carry
        while d <= seg:
            out.append(a.lerp(b, d / seg))
            d += step
        carry = seg - (d - step)
    return out
