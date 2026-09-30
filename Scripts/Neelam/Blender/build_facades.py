# python -c "import sys; sys.argv=['x','--','massing_build.json','massing_textured.json','out_dir']; exec(open('build_facades.py').read())"  (bpy module)
# Realistic-facade context buildings (30 Sep): the ids in massing_textured.json, one mesh per 400 m chunk (facade_<i>_<j>).
#  slot 0 MM_Facade (walls): UV0 u = perimeter metres / bay width, v = height above ground / floor height (1 unit = 1 bay x 1 floor)
#  slot 1 MM_Roof   (roof):  UV0 = plan metres / 8
#  UV1.x = number of floors (parapet / top floor in the shader), UV1.y = building height m / 100
#  vertex colour (linear): R tint, G facade style, B random seed  - all per building, stable (random.Random(id))
# Same axis convention as build_massing.py (UE cm -> m, Y flipped, object at its first vertex, import combine_meshes).
import bpy, bmesh, json, sys, os, math, random
a = sys.argv[sys.argv.index("--") + 1:]; B = json.load(open(a[0])); SEL = set(json.load(open(a[1]))); out = a[2]; os.makedirs(out, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
mf = bpy.data.materials.new("MM_Facade"); mr = bpy.data.materials.new("MM_Roof")
FLOOR_M = 3.1
chunks = {}
for b in B:
    if b["id"] not in SEL: continue
    xs = [p[0] for p in b["pts"]]; ys = [p[1] for p in b["pts"]]
    chunks.setdefault("%d_%d" % (math.floor(sum(xs) / len(xs) / 40000), math.floor(sum(ys) / len(ys) / 40000)), []).append(b)
n = nb = 0
for ck, bl in sorted(chunks.items()):
    me = bpy.data.meshes.new("facade_" + ck); ob = bpy.data.objects.new("facade_" + ck, me); bpy.context.collection.objects.link(ob)
    x0, y0 = bl[0]["pts"][0]; o = (x0 / 100.0, -y0 / 100.0, 0.0); ob.location = o
    me.materials.append(mf); me.materials.append(mr)
    bm = bmesh.new(); uv0 = bm.loops.layers.uv.new("UVMap"); uv1 = bm.loops.layers.uv.new("UVInfo"); col = bm.loops.layers.color.new("Col")
    for b in bl:
        P = [(x / 100.0 - o[0], -y / 100.0 - o[1]) for x, y in b["pts"]]
        if len(P) > 2 and P[0] == P[-1]: P = P[:-1]
        if len(P) < 3: continue
        # counter-clockwise (after the Y flip) so walls face outwards
        area = sum(P[i][0] * P[(i + 1) % len(P)][1] - P[(i + 1) % len(P)][0] * P[i][1] for i in range(len(P)))
        if area < 0: P = P[::-1]
        R = random.Random(b["id"])
        zb, zt = b["base"] / 100.0, b["top"] / 100.0; zg = zb + 3.0            # base = ground - 3 m
        h = zt - zg; floors = max(1.0, round(h / FLOOR_M, 2))
        bay = R.uniform(3.2, 4.4)
        c = (R.random(), R.random(), R.random(), 1.0)
        info = (floors, h / 100.0)
        # walls
        per = 0.0
        for i in range(len(P)):
            p, q = P[i], P[(i + 1) % len(P)]; L = math.hypot(q[0] - p[0], q[1] - p[1])
            if L < 0.05: continue
            vs = [bm.verts.new((p[0], p[1], zb)), bm.verts.new((q[0], q[1], zb)), bm.verts.new((q[0], q[1], zt)), bm.verts.new((p[0], p[1], zt))]
            f = bm.faces.new(vs); f.material_index = 0; f.smooth = False
            # every wall holds a whole number of bays (bay width stretched <= ~15 %) -> no windows cut at corners
            u0, u1 = 0.0, (float(max(1, round(L / bay))) if L >= bay * 0.8 else L / bay)
            for lp, uv in zip(f.loops, [(u0, (zb - zg) / FLOOR_M), (u1, (zb - zg) / FLOOR_M), (u1, h / FLOOR_M), (u0, h / FLOOR_M)]):
                lp[uv0].uv = uv; lp[uv1].uv = info; lp[col] = c
            per += L
        # roof
        top = [bm.verts.new((x, y, zt)) for x, y in P]
        try:
            f = bm.faces.new(top); f.material_index = 1
            for lp in f.loops:
                lp[uv0].uv = ((lp.vert.co.x + o[0]) / 8.0, (lp.vert.co.y + o[1]) / 8.0); lp[uv1].uv = info; lp[col] = c
        except ValueError:
            pass
        nb += 1
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 4])
    bm.to_mesh(me); bm.free(); n += 1
    bpy.ops.object.select_all(action="DESELECT"); ob.select_set(True)
    bpy.ops.export_scene.fbx(filepath=os.path.join(out, ob.name + ".fbx"), use_selection=True, apply_unit_scale=True, apply_scale_options="FBX_SCALE_UNITS",
                             axis_forward="-Y", axis_up="Z", object_types={"MESH"}, mesh_smooth_type="FACE", bake_space_transform=False, colors_type="LINEAR")
print("FACADES_OK", n, "chunks", nb, "buildings")
