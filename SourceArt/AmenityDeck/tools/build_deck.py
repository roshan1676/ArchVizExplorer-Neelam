"""Neelam amenity deck - hardscape, built to the client DWG "7TH PODIUM FLOOR PLAN" (28 Oct 2026).

Run inside Blender (live bridge or Text editor):  exec(open(r'<this file>').read())
Frame: model metres, x = DWG X - 42617.4 + SH.x, y = DWG Y + 5314 + SH.y (SH = registration to the app's podium,
measured from the old pool blockout = DWG pool exactly). z = 0 is the deck FFL (UE world z 2477.5).
FBX export (default axes) lands in UE as (x*100, -y*100) = the WindTunnel root's local frame -> one actor at the root.
Levels are the DWG grading notes (FL / TW / WL / PBL). Collection AD_Hardscape, materials M_AD_* (UE swaps them).
"""
import bpy, bmesh, math
from mathutils import Vector, Matrix

exec(open(r'C:/Users/Admin/Documents/Unreal Projects/ArchVizExplorer-Neelam/SourceArt/AmenityDeck/tools/blib.py').read())

SH = Vector((0.35, 1.96, 0))
COL = collection('AD_Hardscape')


def V(x, y, z=0.0):
    return Vector((x + SH.x, y + SH.y, z))


def poly(pts):
    return [V(x, y) for x, y in pts]


def rect(x0, y0, x1, y1):
    return poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)])


M = {  # name -> preview colour, roughness (UE replaces these by name)
    'Timber': ((0.33, 0.2, 0.11), .6), 'KotaPath': ((0.42, 0.44, 0.4), .55), 'KotaTrackA': ((0.3, 0.33, 0.3), .5),
    'KotaTrackB': ((0.55, 0.53, 0.47), .5), 'Granite': ((0.72, 0.7, 0.66), .35), 'PoolTile': ((0.2, 0.55, 0.75), .2),
    'Water': ((0.1, 0.4, 0.6), .02), 'PlanterClad': ((0.6, 0.57, 0.52), .7), 'Soil': ((0.12, 0.08, 0.05), .95),
    'LawnBase': ((0.15, 0.3, 0.08), .9), 'CourtGreen': ((0.13, 0.38, 0.24), .55), 'CourtBlue': ((0.08, 0.2, 0.55), .55),
    'CourtBlueDark': ((0.05, 0.1, 0.28), .55), 'CourtLine': ((0.95, 0.95, 0.95), .5), 'SteelBlack': ((0.02, 0.02, 0.02), .4),
    'Glass': ((0.8, 0.9, 0.9), .02), 'PergolaWood': ((0.22, 0.12, 0.06), .55), 'RubberMat': ((0.25, 0.08, 0.06), .8),
    'ClimbPanel': ((0.85, 0.85, 0.82), .7), 'ClimbHolds': ((0.9, 0.4, 0.05), .6), 'StoneSeat': ((0.78, 0.74, 0.66), .4),
    'Concrete': ((0.5, 0.5, 0.5), .8), 'NetMesh': ((0.05, 0.05, 0.05), .6),
}


def mat(name):
    c, r = M[name]
    return material('M_AD_' + name, c, rough=r)


def prism_obj(name, loop, z0, z1, m, bevel=0.006):
    bm = bmesh.new(); add_prism(bm, ccw(loop), z0, z1 - z0)
    return finish(bm, name, COL, [mat(m)], bevel=bevel)


def ring_obj(name, outer, inner_d, z0, z1, m, bevel=0.008):
    """Closed wall of thickness inner_d inside `outer` (planter walls, kerbs)."""
    out = ccw(outer); inn = inset(out, inner_d)
    bm = bmesh.new()
    ob = [bm.verts.new((p.x, p.y, z0)) for p in out]; ot = [bm.verts.new((p.x, p.y, z1)) for p in out]
    ib = [bm.verts.new((p.x, p.y, z0)) for p in inn]; it = [bm.verts.new((p.x, p.y, z1)) for p in inn]
    n = len(out)
    for i in range(n):
        j = (i + 1) % n
        for q in ((ob[i], ob[j], ot[j], ot[i]), (it[i], it[j], ib[j], ib[i]), (ot[i], ot[j], it[j], it[i]), (ib[i], ib[j], ob[j], ob[i])):
            bm.faces.new(q)
    return finish(bm, name, COL, [mat(m)], bevel=bevel)


def cut(obj, cutters, delete=True):
    """Exact boolean difference, applied."""
    for c in cutters:
        md = obj.modifiers.new('cut', 'BOOLEAN'); md.operation = 'DIFFERENCE'; md.solver = 'EXACT'; md.object = c
        bpy.context.view_layer.objects.active = obj
        with bpy.context.temp_override(object=obj, active_object=obj):
            bpy.ops.object.modifier_apply(modifier=md.name)
        if delete:
            bpy.data.objects.remove(c, do_unlink=True)
    # keep bevel last
    bev = obj.modifiers.get('Bevel')
    if bev:
        obj.modifiers.move(obj.modifiers.find('Bevel'), len(obj.modifiers) - 1)
    return obj


def cutter(loop, z0=-3, z1=3):
    bm = bmesh.new(); add_prism(bm, ccw(loop), z0, z1 - z0)
    me = bpy.data.meshes.new('_cut'); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new('_cut', me); COL.objects.link(o); o.hide_set(True)
    return o


def boards(name, x0, y0, x1, y1, z_top, w=0.145, gap=0.006, t=0.028, along='x', holes=()):
    """Individual deck boards (staggered butt joints, 2.4-3.6 m lengths), cut around rect holes (DWG coords)."""
    bm = bmesh.new()
    bm.loops.layers.uv.new('UV_World'); bm.loops.layers.color.new('Col')   # layers first: adding them later invalidates element refs
    span = (y1 - y0) if along == 'x' else (x1 - x0)
    n = int(span / (w + gap))
    lengths = (3.0, 2.4, 3.6)
    a0, a1 = (x0, x1) if along == 'x' else (y0, y1)
    made = []
    for i in range(n):
        c0 = (y0 if along == 'x' else x0) + gap / 2 + i * (w + gap); c1 = c0 + w
        free = [(a0, a1)]                       # along-axis intervals left after the holes crossing this row
        for h in holes:
            h0, h1, k0, k1 = (h[0], h[2], h[1], h[3]) if along == 'x' else (h[1], h[3], h[0], h[2])
            if k0 < c1 and k1 > c0:
                free = [seg for f in free for seg in ((f[0], min(f[1], h0)), (max(f[0], h1), f[1])) if seg[1] - seg[0] > 0.04]
        for f0, f1 in free:
            s = a0 - (i * 0.9) % lengths[i % 3]
            while s < f1:
                e = min(s + lengths[i % 3], f1); b0 = max(s, f0)
                if e - b0 > 0.04:
                    p0, p1 = b0 + gap / 2, e - gap / 2
                    if along == 'x':
                        vs = add_box(bm, V((p0 + p1) / 2, (c0 + c1) / 2, z_top - t / 2), (p1 - p0, w, t))
                    else:
                        vs = add_box(bm, V((c0 + c1) / 2, (p0 + p1) / 2, z_top - t / 2), (w, p1 - p0, t))
                    made.append(vs)
                s = e
    vary(bm, made)
    return finish(bm, name, COL, [mat('Timber')], bevel=0.003, segments=1, uv=False)


def vary(bm, groups, seed=3, lo=0.72, hue=0.06):
    """Per-piece random grain offset (UV) and colour (vertex colour, multiplied in M_AD_Surface) so every board /
    hold reads as its own piece of material instead of one continuous texture."""
    import random
    rnd = random.Random(seed)
    uv_box(bm)
    uvl = bm.loops.layers.uv['UV_World']
    col = bm.loops.layers.color['Col']
    for vs in groups:
        du, dv = rnd.uniform(0, 8), rnd.uniform(0, 8)
        k = rnd.uniform(lo, 1.0); h = rnd.uniform(-hue, hue)
        c = (min(1, k * (1 + h)), k, max(0, k * (1 - h)), 1.0)
        for f in {f for v in vs for f in v.link_faces}:
            for l in f.loops:
                l[uvl].uv = (l[uvl].uv.x + du, l[uvl].uv.y + dv)
                l[col] = c


def build():
    for o in list(COL.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    made = []

    # ---------- pathways (Kota, FL -0.05) = the DWG paving outline minus lawns / courts / track bands ----------
    PAVE = [(47.152, 19.193), (69.653, 19.193), (69.653, 17.393), (-14.621, 17.393), (-14.621, 30.293),
            (24.096, 30.293), (24.079, 47.567), (47.125, 47.567)]
    # fill: podium top between the towers and the parapet (the old CDE deck slab is hidden), under everything else
    made.append(prism_obj('AD_DeckFill', poly([(-15.821, 14.0), (69.653, 14.0), (69.653, 52.82), (-15.821, 49.33)]), -0.30, -0.115, 'KotaPath', bevel=0))
    path = prism_obj('AD_Path_Kota', poly(PAVE), -0.12, -0.05, 'KotaPath', bevel=0)
    holes = [rect(-12.821, 19.193, 24.079, 28.493), rect(25.881, 19.193, 45.341, 28.493),
             rect(25.881, 30.293, 45.341, 45.767), poly(KOT[0])]
    cut(path, [cutter(h) for h in holes])
    made.append(path)
    # jogging track: 4 Kota bands of 0.3 m between the 5 DWG polylines (outer two have the court leg)
    for i in range(4):
        b = prism_obj('AD_Track_Band%d' % i, poly(KOT[i]), -0.12, -0.05, 'KotaTrackA' if i in (0, 3) else 'KotaTrackB', bevel=0)
        cut(b, [cutter(poly(KOT[i + 1]))])
        made.append(b)

    # ---------- lawns (FG -0.10): soil bed + 60 mm steel edging flush with the path ----------
    for nm, r in (('Party', (-12.821, 19.193, 24.079, 28.493)), ('Central', (25.881, 30.293, 41.331, 41.743))):
        made.append(prism_obj('AD_Lawn_%s' % nm, rect(*r), -0.25, -0.10, 'LawnBase', bevel=0))
        made.append(ring_obj('AD_LawnEdge_%s' % nm, rect(*r), 0.006, -0.16, -0.045, 'SteelBlack', bevel=0))

    # ---------- timber pool deck (FL +0.10), boards along the pool ----------
    planters_sq = [(1.455, 36.353), (7.305, 36.353), (13.155, 36.353), (17.825, 36.343)]
    copings = [(-11.851, 37.563, 19.605, 47.847), (-11.851, 32.916, -2.505, 37.823)]   # pool + kids pool coping bands
    sq_holes = [(x, y, x + 1.5, y + 1.5) for x, y in planters_sq] + copings
    made.append(boards('AD_Deck_South', -2.785, 30.293, 22.579, 37.843, 0.10, holes=sq_holes))
    made.append(boards('AD_Deck_West', -14.595, 30.293, -2.785, 33.196, 0.10, holes=copings))
    made.append(boards('AD_Deck_East', 19.325, 37.843, 22.579, 47.567, 0.10, along='y', holes=copings))
    for nm, r in (('South', (-2.785, 30.293, 22.579, 37.843)), ('West', (-14.595, 30.293, -2.785, 33.196)), ('East', (19.325, 37.843, 22.579, 47.567))):
        made.append(prism_obj('AD_DeckBase_%s' % nm, rect(*r), -0.12, 0.072, 'Concrete', bevel=0))

    # ---------- swimming pool + kids pool ----------
    made += pool('Main', (-11.571, 37.843, 19.325, 47.567), floor=-1.25)
    made += pool('Kids', (-11.571, 33.196, -2.785, 37.543), floor=-0.50)
    # main pool entry steps, SE corner (DWG risers 0.30 apart): upper flight to a -0.60 bench, lower flight to the floor
    st = bmesh.new()
    for k, x in enumerate((18.13, 18.43, 18.73, 19.03)):
        z = -0.05 - 0.15 * (4 - k)
        add_box(st, V((x + 19.325) / 2, 39.57, (z - 1.25) / 2), (19.325 - x, 3.46, z + 1.25))
    for k, x in enumerate((15.73, 16.03, 16.33)):
        z = -0.65 - 0.2 * (3 - k)
        add_box(st, V((x + 18.13) / 2, 39.57, (z - 1.25) / 2), (18.13 - x, 3.46, z + 1.25))
    made.append(finish(st, 'AD_Pool_Main_Steps', COL, [mat('PoolTile')], bevel=0.01))
    st = bmesh.new()
    for k, x in enumerate((-3.98, -3.68, -3.38, -3.08)):
        z = -0.05 - 0.1125 * (4 - k)
        add_box(st, V((x + -2.785) / 2, 35.37, (z - 0.5) / 2), (-2.785 - x, 4.347, z + 0.5))
    made.append(finish(st, 'AD_Pool_Kids_Steps', COL, [mat('PoolTile')], bevel=0.01))
    # north pool wall (TW +0.30) with frameless glass balustrade to +1.50 (top of rail) at the podium edge
    made.append(prism_obj('AD_Pool_NorthWall', rect(-11.571, 47.567, 19.325, 47.867), -1.25, 0.30, 'Granite', bevel=0.01))
    made.append(prism_obj('AD_Pool_GlassRail', rect(-11.571, 47.712, 19.325, 47.724), 0.30, 1.50, 'Glass', bevel=0.002))
    made.append(prism_obj('AD_Pool_GlassShoe', rect(-11.571, 47.69, 19.325, 47.746), 0.28, 0.36, 'SteelBlack', bevel=0.003))

    # ---------- planters: walls 0.3, clad, granite coping, soil 50 mm below TW ----------
    def planter(nm, outer, tw, wall=0.30):
        made.append(ring_obj('AD_Planter_%s' % nm, outer, wall, -0.10, tw - 0.04, 'PlanterClad'))
        made.append(ring_obj('AD_Planter_%s_Coping' % nm, outer, wall + 0.02, tw - 0.04, tw, 'Granite', bevel=0.012))
        made.append(prism_obj('AD_Planter_%s_Soil' % nm, inset(ccw(outer), wall), -0.10, tw - 0.05, 'Soil', bevel=0))
    for i, (x, y) in enumerate(planters_sq):
        planter('PoolSq%d' % i, rect(x, y, x + 1.5, y + 1.5), 0.30)
    planter('StripMid', rect(22.579, 30.293, 24.079, 49.08), 0.55)
    planter('West', rect(-15.821, 17.693, -14.595, 48.349), 0.55, wall=0.15)
    planter('WestTrees', rect(-14.595, 33.196, -11.571, 48.349), 0.55)
    planter('East', rect(68.025, 19.193, 69.653, 52.988), 0.55)
    planter('NorthMid', rect(24.079, 47.567, 47.125, 50.67), 0.55)
    planter('NorthPool', rect(19.325, 47.567, 22.579, 49.08), 0.55)
    planter('TreeNW', rect(25.881, 44.267, 27.381, 45.767), 0.55)
    planter('TreeSE', rect(41.877, 30.293, 43.377, 31.793), 0.55)
    for i, x in enumerate((1.13, 23.93)):
        planter('South%d' % i, rect(x, 15.89, x + 2.8, 17.39), 0.40)

    # ---------- central lawn: L-shaped seating steps (+0.25) and planted mound behind (+0.55 TW) ----------
    S1 = [(25.881, 41.743), (41.331, 41.743), (41.331, 33.771), (40.128, 33.771), (40.128, 30.293)]
    S2 = [(30.645, 43.209), (42.777, 43.204), (42.777, 31.793)]
    tier1 = poly([(25.881, 41.743), (41.331, 41.743), (41.331, 33.771), (40.128, 33.771), (40.128, 30.293), (41.877, 30.293),
                  (41.877, 31.793), (42.777, 31.793), (42.777, 43.204), (30.645, 43.209), (30.645, 44.267), (25.881, 44.267)])
    made.append(prism_obj('AD_Seating_Tier1', tier1, -0.10, 0.25, 'StoneSeat', bevel=0.015))
    tier2 = poly([(27.381, 44.267), (30.645, 44.267), (30.645, 43.209), (42.777, 43.204), (42.777, 31.793), (43.377, 31.793),
                  (45.341, 31.793), (45.341, 45.767), (27.381, 45.767)])
    made.append(ring_obj('AD_Mound_Wall', tier2, 0.25, -0.10, 0.55, 'StoneSeat', bevel=0.015))
    made.append(prism_obj('AD_Mound_Soil', inset(ccw(tier2), 0.25), -0.10, 0.62, 'Soil', bevel=0))

    # ---------- pickleball (FL -0.05) ----------
    made += pickleball((25.881, 19.193, 45.341, 28.493))
    # ---------- multipurpose court (FL -0.05) ----------
    made += court((47.152, 19.193, 68.025, 52.988))
    # ---------- pergola over the dining deck ----------
    made += pergola((-1.9, 30.75, 21.9, 35.95))
    # ---------- rock climbing wall (DWG: FG +0.35 safety surface west of the wall) ----------
    made += climbing_wall(49.38, 14.277, 3.116)   # DWG: in the recess between Tower D wings, holds face west
    return made


KOT = [[(46.853, 18.893), (69.353, 18.893), (69.353, 17.693), (-14.321, 17.693), (-14.321, 29.993), (24.396, 29.993), (24.379, 47.267), (46.826, 47.267)],
       [(46.553, 18.593), (69.053, 18.593), (69.053, 17.993), (-14.021, 17.993), (-14.021, 29.693), (24.696, 29.693), (24.68, 46.967), (46.526, 46.967)],
       [(46.253, 18.293), (-13.721, 18.293), (-13.721, 29.393), (24.996, 29.393), (24.98, 46.667), (46.226, 46.667)],
       [(45.953, 18.593), (-13.421, 18.593), (-13.421, 29.093), (25.297, 29.093), (25.28, 46.367), (45.927, 46.367)],
       [(45.653, 18.893), (-13.121, 18.893), (-13.121, 28.793), (25.597, 28.793), (25.581, 46.067), (45.627, 46.067)]]


def pool(nm, r, floor):
    """Tiled shell (walls 0.3 below the deck), granite coping 0.30 wide with 20 mm nosing, water plane at WL -0.05."""
    x0, y0, x1, y1 = r
    out = []
    inner = rect(x0, y0, x1, y1)
    shell = ring_obj('AD_Pool_%s_Shell' % nm, rect(x0 - 0.3, y0 - 0.3, x1 + 0.3, y1 + 0.3), 0.3, floor - 0.3, 0.06, 'PoolTile', bevel=0.01)
    out.append(shell)
    out.append(prism_obj('AD_Pool_%s_Floor' % nm, inner, floor - 0.3, floor, 'PoolTile', bevel=0))
    out.append(ring_obj('AD_Pool_%s_Coping' % nm, rect(x0 - 0.28, y0 - 0.28, x1 + 0.28, y1 + 0.28), 0.30, 0.06, 0.10, 'Granite', bevel=0.015))
    out.append(prism_obj('AD_Pool_%s_Water' % nm, inner, -0.06, -0.05, 'Water', bevel=0))
    # underwater lights every ~3 m on the long walls
    bm = bmesh.new()
    n = max(2, int((x1 - x0) / 3.0))
    for i in range(n):
        x = x0 + (i + 0.5) * (x1 - x0) / n
        for y, s in ((y0, 1), (y1, -1)):
            bmesh.ops.create_cone(bm, cap_ends=True, segments=24, radius1=0.12, radius2=0.11, depth=0.02,
                                  matrix=Matrix.Translation(V(x, y + s * 0.01, min(-0.35, floor + 0.2)))
                                  @ Matrix.Rotation(math.pi / 2, 4, 'X'))
    out.append(finish(bm, 'AD_Pool_%s_Lights' % nm, COL, [material('M_AD_PoolLight', (1, 0.95, 0.85), rough=0.1)], bevel=0))
    return out


def fence(nm, r, h, gate=None, post=3.0):
    """Black powder-coated fence: 60 mm posts every ~3 m, top/mid/bottom rails, chain-link panel (masked material)."""
    x0, y0, x1, y1 = r
    corners = [V(x0, y0), V(x1, y0), V(x1, y1), V(x0, y1)]
    pb = bmesh.new(); nb = bmesh.new()
    for a, b in zip(corners, corners[1:] + corners[:1]):
        L = (b - a).length; n = max(1, round(L / post)); d = (b - a) / n
        for i in range(n):
            p = a + d * i
            add_box(pb, Vector((p.x, p.y, h / 2 - 0.05)), (0.06, 0.06, h + 0.1))
        ang = math.atan2(d.y, d.x)
        for z in (0.05, h * 0.5, h - 0.03):
            add_box(pb, (a + b) / 2 + Vector((0, 0, z)), (L, 0.045, 0.045), rot_z=ang)
        add_box(nb, (a + b) / 2 + Vector((0, 0, h / 2 + 0.02)), (L, 0.004, h - 0.08), rot_z=ang)
    return [finish(pb, 'AD_Fence_%s_Frame' % nm, COL, [mat('SteelBlack')], bevel=0.004, segments=1),
            finish(nb, 'AD_Fence_%s_Mesh' % nm, COL, [mat('NetMesh')], bevel=0)]


def lines_obj(nm, segs, w=0.05, z=-0.046):
    """Court markings: list of polylines (model metres, already shifted) as 50 mm strips 4 mm proud."""
    bm = bmesh.new()
    for line in segs:
        add_strip(bm, [Vector((p.x, p.y, 0)) for p in line], w, z, 0.004)
    return finish(bm, nm, COL, [mat('CourtLine')], bevel=0)


def arc(c, r, a0, a1, n=48):
    return [c + Vector((math.cos(a0 + (a1 - a0) * i / n) * r, math.sin(a0 + (a1 - a0) * i / n) * r, 0)) for i in range(n + 1)]


def pickleball(r):
    x0, y0, x1, y1 = r
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    out = [prism_obj('AD_Pickle_Surround', rect(*r), -0.12, -0.05, 'CourtBlueDark', bevel=0)]
    L, W = 13.41, 6.10           # official court, long axis along x (DWG block)
    out.append(prism_obj('AD_Pickle_Court', rect(cx - L / 2, cy - W / 2, cx + L / 2, cy + W / 2), -0.05, -0.048, 'CourtBlue', bevel=0))
    c = V(cx, cy)
    segs = [[c + Vector((-L / 2, -W / 2, 0)), c + Vector((L / 2, -W / 2, 0)), c + Vector((L / 2, W / 2, 0)), c + Vector((-L / 2, W / 2, 0)), c + Vector((-L / 2, -W / 2, 0))]]
    for s in (-1, 1):
        segs.append([c + Vector((s * 2.13, -W / 2, 0)), c + Vector((s * 2.13, W / 2, 0))])          # kitchen lines (7 ft)
        segs.append([c + Vector((s * 2.13, 0, 0)), c + Vector((s * L / 2, 0, 0))])                   # centre service lines
    out.append(lines_obj('AD_Pickle_Lines', segs))
    # net: 2 posts + 0.91 m (sideline) / 0.86 m (centre) net with white top band
    pb = bmesh.new()
    for s in (-1, 1):
        add_box(pb, c + Vector((0, s * (W / 2 + 0.3), 0.45)), (0.07, 0.07, 1.0))
    out.append(finish(pb, 'AD_Pickle_NetPosts', COL, [mat('SteelBlack')], bevel=0.005))
    out.append(prism_obj('AD_Pickle_Net', [c + Vector((-0.002, -W / 2 - 0.3, 0)), c + Vector((0.002, -W / 2 - 0.3, 0)), c + Vector((0.002, W / 2 + 0.3, 0)), c + Vector((-0.002, W / 2 + 0.3, 0))],
                         0.08, 0.86, 'NetMesh', bevel=0))
    out.append(prism_obj('AD_Pickle_NetBand', [c + Vector((-0.012, -W / 2 - 0.3, 0)), c + Vector((0.012, -W / 2 - 0.3, 0)), c + Vector((0.012, W / 2 + 0.3, 0)), c + Vector((-0.012, W / 2 + 0.3, 0))],
                         0.82, 0.88, 'CourtLine', bevel=0.004))
    out += fence('Pickle', (x0 + 0.15, y0 + 0.15, x1 - 0.15, y1 - 0.15), 3.0)
    return out


def court(r):
    """Full FIBA basketball court (28 x 15) on green acrylic, 4.5 m fence, 4 floodlight masts, 2 hoops."""
    x0, y0, x1, y1 = r
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    out = [prism_obj('AD_Court_Surround', rect(*r), -0.12, -0.05, 'CourtGreen', bevel=0)]
    c = V(cx, cy); L, W = 28.0, 15.0     # long axis along y
    P_ = lambda dx, dy: c + Vector((dx, dy, 0))
    segs = [[P_(-W / 2, -L / 2), P_(W / 2, -L / 2), P_(W / 2, L / 2), P_(-W / 2, L / 2), P_(-W / 2, -L / 2)],
            [P_(-W / 2, 0), P_(W / 2, 0)], arc(c, 1.8, 0, 2 * math.pi, 64)]
    for s in (-1, 1):
        base = P_(0, s * L / 2); hoop = P_(0, s * (L / 2 - 1.575))
        segs.append([base + Vector((-2.45, 0, 0)), base + Vector((-2.45, -s * 5.8, 0)), base + Vector((2.45, -s * 5.8, 0)), base + Vector((2.45, 0, 0))])
        segs.append(arc(base + Vector((0, -s * 5.8, 0)), 1.8, 0, math.pi if s < 0 else -math.pi))
        dy = math.sqrt(6.75 ** 2 - 6.6 ** 2)       # 3-pt: straight 6.6 m from the hoop line, then R 6.75 arc
        a0, a1 = math.atan2(-s * dy, -6.6), math.atan2(-s * dy, 6.6)
        segs.append([base + Vector((-6.6, 0, 0))] + arc(hoop, 6.75, a0, a1, 64) + [base + Vector((6.6, 0, 0))])
    out.append(lines_obj('AD_Court_Lines', segs))
    out.append(prism_obj('AD_Court_Play', [P_(-W / 2, -L / 2), P_(W / 2, -L / 2), P_(W / 2, L / 2), P_(-W / 2, L / 2)], -0.05, -0.048, 'CourtGreen', bevel=0))
    out += fence('Court', (x0 + 0.15, y0 + 0.15, x1 - 0.15, y1 - 0.15), 4.5)
    out += hoops(c, L)
    out += masts([(x0 + 0.35, y0 + 6), (x1 - 0.35, y0 + 6), (x0 + 0.35, y1 - 6), (x1 - 0.35, y1 - 6)], cx)
    return out


def hoops(c, L):
    """In-ground hoop: 150 mm square pole, 1.2 m overhang arm, tempered-glass board 1.8 x 1.05, ring at 3.05 m."""
    sb = bmesh.new(); gb = bmesh.new(); rb = bmesh.new()
    for s in (-1, 1):
        base = c + Vector((0, s * (L / 2 + 0.6), 0))
        add_box(sb, base + Vector((0, 0, 1.75)), (0.15, 0.15, 3.5))
        add_box(sb, base + Vector((0, -s * 0.55, 3.35)), (0.1, 1.1, 0.1))
        add_box(sb, base + Vector((0, -s * 0.55, 2.95)), (0.08, 1.1, 0.08), )
        board = c + Vector((0, s * (L / 2 - 1.2), 3.375))
        add_box(gb, board, (1.8, 0.02, 1.05))
        add_box(rb, board + Vector((0, -s * 0.02, -0.075)), (0.59, 0.012, 0.45))     # target square frame (simplified)
        ring = c + Vector((0, s * (L / 2 - 1.575), 3.05))
        bmesh.ops.create_cone(rb, cap_ends=False, segments=32, radius1=0.2325, radius2=0.2325, depth=0.018, matrix=Matrix.Translation(ring))
        bmesh.ops.create_cone(rb, cap_ends=False, segments=24, radius1=0.2325, radius2=0.16, depth=0.4, matrix=Matrix.Translation(ring + Vector((0, 0, -0.2))))
    return [finish(sb, 'AD_Hoop_Poles', COL, [mat('SteelBlack')], bevel=0.008),
            finish(gb, 'AD_Hoop_Boards', COL, [mat('Glass')], bevel=0.004),
            finish(rb, 'AD_Hoop_Rings', COL, [material('M_AD_HoopOrange', (0.9, 0.3, 0.02), rough=0.4)], bevel=0)]


def masts(pts, cx):
    """8 m floodlight masts with twin LED flood heads aimed at the court."""
    sb = bmesh.new(); hb = bmesh.new()
    for x, y in pts:
        p = V(x, y)
        bmesh.ops.create_cone(sb, cap_ends=True, segments=16, radius1=0.09, radius2=0.06, depth=8.0, matrix=Matrix.Translation(p + Vector((0, 0, 4.0))))
        d = 1 if x < cx else -1
        add_box(sb, p + Vector((d * 0.3, 0, 7.85)), (0.7, 0.08, 0.08))
        for k in (-0.22, 0.22):
            add_box(hb, p + Vector((d * 0.55, k, 7.7)), (0.06, 0.38, 0.28))
    return [finish(sb, 'AD_Mast_Poles', COL, [mat('SteelBlack')], bevel=0.006),
            finish(hb, 'AD_Mast_Heads', COL, [material('M_AD_LEDHead', (0.15, 0.15, 0.16), rough=0.3)], bevel=0.008)]


def pergola(r):
    """Timber pergola (reference: dark louvred roof over dining): 200 mm posts on a 4 x 2 grid, 150x450 beams,
    50x200 louvres at 300 c/c across the short span. Underside of louvres at 3.0 m."""
    x0, y0, x1, y1 = r
    pb = bmesh.new()
    nx = 5
    xs = [x0 + (x1 - x0) * i / (nx - 1) for i in range(nx)]
    for x in xs:
        for y in (y0 + 0.2, y1 - 0.2):
            add_box(pb, V(x, y, 0.1 + 1.45), (0.2, 0.2, 2.9))
            add_box(pb, V(x, y, 0.1 + 0.015), (0.32, 0.32, 0.03))                   # steel base plate
    for y in (y0 + 0.2, y1 - 0.2):
        add_box(pb, V((x0 + x1) / 2, y, 3.0 + 0.225 - 0.1), (x1 - x0 + 0.6, 0.15, 0.45))
    for x in xs:
        add_box(pb, V(x, (y0 + y1) / 2, 3.35), (0.12, y1 - y0 + 0.5, 0.3))
    n = int((x1 - x0 + 0.4) / 0.3)
    for i in range(n + 1):
        x = x0 - 0.2 + i * 0.3
        add_box(pb, V(x, (y0 + y1) / 2, 3.6), (0.05, y1 - y0 + 0.8, 0.2))
    return [finish(pb, 'AD_Pergola_Dining', COL, [mat('PergolaWood')], bevel=0.006, segments=2)]


def climbing_wall(x, y, w):
    """4.5 m bouldering wall (plywood panels on steel frame) with resin holds; 350 mm rubber safety surface."""
    out = [prism_obj('AD_Climb_SafetyMat', rect(46.98, y, x, y + w), -0.05, 0.35, 'RubberMat', bevel=0.02)]
    out.append(prism_obj('AD_Climb_Panel', rect(x, y, x + 0.146, y + w), 0.35, 4.85, 'ClimbPanel', bevel=0.006))
    fb = bmesh.new()
    for yy in (y + 0.05, y + w - 0.05):
        add_box(fb, V(x + 0.25, yy, 2.5), (0.1, 0.1, 5.0))
    out.append(finish(fb, 'AD_Climb_Frame', COL, [mat('SteelBlack')], bevel=0.005))
    import random
    random.seed(7)
    hb = bmesh.new(); holds = []
    hb.loops.layers.uv.new('UV_World'); hb.loops.layers.color.new('Col')   # layers first: adding them later invalidates element refs
    for i in range(70):
        yy = y + 0.15 + random.random() * (w - 0.3); zz = 0.6 + random.random() * 4.1
        s = 0.05 + random.random() * 0.08
        f0 = len(hb.faces)
        r = bmesh.ops.create_icosphere(hb, subdivisions=2, radius=s)
        bmesh.ops.transform(hb, verts=r['verts'], matrix=Matrix.Translation(V(x - 0.01, yy, zz))
                            @ Matrix.Diagonal((0.45, 1.0, 0.7 + random.random() * 0.4, 1)))
        holds.append((f0, len(hb.faces)))           # face index range (element refs don't survive later ops)
    uv_box(hb)
    hb.faces.ensure_lookup_table()
    col = hb.loops.layers.color['Col']
    palette = [(0.85, 0.12, 0.08, 1), (0.95, 0.55, 0.05, 1), (0.1, 0.35, 0.8, 1), (0.1, 0.6, 0.25, 1), (0.95, 0.85, 0.1, 1), (0.08, 0.08, 0.08, 1)]
    for i, (a, b) in enumerate(holds):
        for k in range(a, b):
            for l in hb.faces[k].loops:
                l[col] = palette[i % len(palette)]
    out.append(finish(hb, 'AD_Climb_Holds', COL, [mat('ClimbHolds')], bevel=0, uv=False))
    return out


result = [o.name for o in build()]
