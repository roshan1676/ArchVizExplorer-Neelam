# blender -b --factory-startup --python build_roads.py -- road_build.json out.fbx   (or: -- road_build.json out_dir --split)
# One object per carriageway (origin = first centreline point): asphalt deck, kerbs, skirt under the map edge,
# lane markings (solid edges + dashed dividers). Units: UE cm in the json -> metres here (Y flipped: UE is left-handed).
import bpy, bmesh, json, sys, math
from mathutils import Vector
a = sys.argv[sys.argv.index("--") + 1:]; data = json.load(open(a[0]))["roads"]; out = a[1]
bpy.ops.wm.read_factory_settings(use_empty=True)
mats = {}
for n, c in (("MR_Asphalt", (0.05, 0.05, 0.05, 1)), ("MR_Kerb", (0.5, 0.5, 0.48, 1)), ("MR_Marking", (0.9, 0.9, 0.9, 1))):
    m = bpy.data.materials.new(n); m.diffuse_color = c; mats[n] = m
DECK, KERB, SKIRT, KW = 0.12, 0.25, -0.9, 0.35
origins = {}
for key, r in data.items():
    P = [Vector((x / 100.0, -y / 100.0, z / 100.0)) for x, y, z in r["pts"]]
    if len(P) < 2: continue
    o = P[0].copy(); origins[key] = [r["pts"][0][0], r["pts"][0][1], r["pts"][0][2]]
    W = r["width_m"]; half = W / 2.0
    me = bpy.data.meshes.new(key); ob = bpy.data.objects.new(key, me); bpy.context.collection.objects.link(ob); ob.location = o
    for m in mats.values(): me.materials.append(m)
    bm = bmesh.new(); uv = bm.loops.layers.uv.new("UVMap")
    s = 0.0; rows = []
    for i, p in enumerate(P):
        if i > 0: s += (p - P[i - 1]).length
        t = (P[min(i + 1, len(P) - 1)] - P[max(i - 1, 0)]); t.z = 0; t.normalize()
        n = Vector((-t.y, t.x, 0.0))
        # side wall reaches down to the traced ground where Flatten_Roads.py lifted the deck (capped 3 m -> embankment look)
        gz = r.get("ground", [None] * len(P))[i]
        sk = SKIRT - (min(3.0, max(0.0, (r["pts"][i][2] - gz) / 100.0)) if gz is not None else 0.0)
        prof = [(-half - KW, sk), (-half - KW, KERB), (-half, KERB), (-half, DECK), (half, DECK), (half, KERB), (half + KW, KERB), (half + KW, sk)]
        rows.append((s, [bm.verts.new(p - o + n * off + Vector((0, 0, dz))) for off, dz in prof], p, n))
    segmat = [1, 1, 1, 0, 1, 1, 1]     # skirt, kerb top, kerb face, ASPHALT, kerb face, kerb top, skirt
    for (s0, r0, _, _), (s1, r1, _, _) in zip(rows, rows[1:]):
        for c in range(7):
            f = bm.faces.new((r0[c], r0[c + 1], r1[c + 1], r1[c])); f.material_index = segmat[c]
            for lp, (vv, ss) in zip(f.loops, ((r0[c], s0), (r0[c + 1], s0), (r1[c + 1], s1), (r1[c], s1))):
                lp[uv].uv = ((vv.co - (vv.co.project(Vector((0, 0, 1))))).length * 0 + (c + (vv in (r0[c + 1], r1[c + 1]))) * (W / 4.0 if c == 3 else 0.1), ss / 4.0)
    # lane markings: solid edge lines 0.3 m inside the kerbs, dashed dividers every 3.5 m (3 m on / 6 m off)
    lines = [(-half + 0.3, True), (half - 0.3, True)] + [(-half + 3.5 * k, False) for k in range(1, int(r["lanes"]))]
    for off, solid in lines:
        for i, ((s0, _, p0, n0), (s1, _, p1, n1)) in enumerate(zip(rows, rows[1:])):
            if not solid and (int(s0 // 3.0) % 3) != 0: continue
            hw = 0.1 if solid else 0.075; z = Vector((0, 0, DECK + 0.012))
            q = [bm.verts.new(p0 - o + n0 * (off - hw) + z), bm.verts.new(p0 - o + n0 * (off + hw) + z),
                 bm.verts.new(p1 - o + n1 * (off + hw) + z), bm.verts.new(p1 - o + n1 * (off - hw) + z)]
            f = bm.faces.new(q); f.material_index = 2
            for lp, u in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))): lp[uv].uv = u
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me); bm.free()
if "--split" in sys.argv:              # one FBX per carriageway (out = folder) -> Import_Roads.py
    import os
    os.makedirs(out, exist_ok=True)
    for ob in list(bpy.data.objects):
        bpy.ops.object.select_all(action="DESELECT"); ob.select_set(True)
        bpy.ops.export_scene.fbx(filepath=os.path.join(out, ob.name + ".fbx"), use_selection=True, apply_unit_scale=True, apply_scale_options="FBX_SCALE_UNITS",
                                 axis_forward="-Y", axis_up="Z", object_types={"MESH"}, mesh_smooth_type="FACE", use_mesh_modifiers=True, bake_space_transform=False)
    print("ROADS_OK", len(origins)); sys.exit(0)
bpy.ops.export_scene.fbx(filepath=out, use_selection=False, apply_unit_scale=True, apply_scale_options="FBX_SCALE_UNITS",
                         axis_forward="-Y", axis_up="Z", object_types={"MESH"}, mesh_smooth_type="FACE", use_mesh_modifiers=True, bake_space_transform=False)
json.dump(origins, open(out + ".origins.json", "w"))
print("ROADS_OK", len(origins))
