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
    # optional "ext": {"start": m, "end": m, "drop": cm (default 2)} - run the deck that far past its end, that much lower, so it tucks under the
    # neighbouring carriageway: hides the V-notch between two square-cut kerb ends at a joint (json pts stay as they are)
    ext = r.get("ext") or {}; GR = list(r.get("ground", [None] * len(P))); WD = list(r["widths"]) if r.get("widths") else None
    ZP = [p_[2] for p_ in r["pts"]]
    if ext.get("start"):
        t0 = (P[0] - P[1]); t0.z = 0; t0.normalize(); P.insert(0, P[0] + t0 * ext["start"] - Vector((0, 0, ext.get("drop", 2) / 100.0)))
        GR.insert(0, GR[0]); ZP.insert(0, ZP[0] - 2); WD and WD.insert(0, WD[0])
    if ext.get("end"):
        t1 = (P[-1] - P[-2]); t1.z = 0; t1.normalize(); P.append(P[-1] + t1 * ext["end"] - Vector((0, 0, ext.get("drop", 2) / 100.0)))
        GR.append(GR[-1]); ZP.append(ZP[-1] - 2); WD and WD.append(WD[-1])
    o = P[0].copy(); origins[key] = [o.x * 100.0, -o.y * 100.0, o.z * 100.0]
    W = r["width_m"]; half = W / 2.0
    HALF = [w / 2.0 for w in WD] if WD else [half] * len(P)   # optional per-point width (taper at joints)
    me = bpy.data.meshes.new(key); ob = bpy.data.objects.new(key, me); bpy.context.collection.objects.link(ob); ob.location = o
    for m in mats.values(): me.materials.append(m)
    bm = bmesh.new(); uv = bm.loops.layers.uv.new("UVMap")
    s = 0.0; rows = []
    for i, p in enumerate(P):
        if i > 0: s += (p - P[i - 1]).length
        t = (P[min(i + 1, len(P) - 1)] - P[max(i - 1, 0)]); t.z = 0; t.normalize()
        n = Vector((-t.y, t.x, 0.0))
        # side wall reaches down to the traced ground where Flatten_Roads.py lifted the deck (capped 3 m -> embankment look)
        gz = GR[i]
        sk = SKIRT - (min(3.0, max(0.0, (ZP[i] - gz) / 100.0)) if gz is not None else 0.0)
        h = HALF[i]
        prof = [(-h - KW, sk), (-h - KW, KERB), (-h, KERB), (-h, DECK), (h, DECK), (h, KERB), (h + KW, KERB), (h + KW, sk)]
        rows.append((s, [bm.verts.new(p - o + n * off + Vector((0, 0, dz))) for off, dz in prof], p, n, h))
    segmat = [1, 1, 1, 0, 1, 1, 1]     # skirt, kerb top, kerb face, ASPHALT, kerb face, kerb top, skirt
    for (s0, r0, _, _, _), (s1, r1, _, _, _) in zip(rows, rows[1:]):
        for c in range(7):
            f = bm.faces.new((r0[c], r0[c + 1], r1[c + 1], r1[c])); f.material_index = segmat[c]
            for lp, (vv, ss) in zip(f.loops, ((r0[c], s0), (r0[c + 1], s0), (r1[c + 1], s1), (r1[c], s1))):
                lp[uv].uv = ((vv.co - (vv.co.project(Vector((0, 0, 1))))).length * 0 + (c + (vv in (r0[c + 1], r1[c + 1]))) * (W / 4.0 if c == 3 else 0.1), ss / 4.0)
    # lane markings: solid edge lines 0.3 m inside the kerbs, dashed dividers every 3.5 m (3 m on / 6 m off)
    # (side, distance from that edge): -1 = from the left edge, +1 = from the right edge - follows a width taper
    lines = [(-1, 0.3, True), (1, 0.3, True)] + [(-1, 3.5 * k, False) for k in range(1, int(r["lanes"]))]
    for side, d, solid in lines:
        for i, ((s0, _, p0, n0, h0), (s1, _, p1, n1, h1)) in enumerate(zip(rows, rows[1:])):
            if not solid and (int(s0 // 3.0) % 3) != 0: continue
            hw = 0.1 if solid else 0.075; z = Vector((0, 0, DECK + 0.012))
            o0 = side * (h0 - d); o1 = side * (h1 - d)
            q = [bm.verts.new(p0 - o + n0 * (o0 - hw) + z), bm.verts.new(p0 - o + n0 * (o0 + hw) + z),
                 bm.verts.new(p1 - o + n1 * (o1 + hw) + z), bm.verts.new(p1 - o + n1 * (o1 - hw) + z)]
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
