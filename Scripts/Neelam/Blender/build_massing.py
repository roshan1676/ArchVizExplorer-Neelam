# python -c "import sys; sys.argv=['x','--','massing_build.json','out_dir']; exec(open('build_massing.py').read())"  (bpy module)
# One mesh per 500 m chunk: every footprint extruded base..top as a closed prism (flat roof), single material MM_Massing.
# UE cm -> metres, Y flipped (UE is left-handed) - same convention as build_roads.py; import with Import_Massing.py.
import bpy, bmesh, json, sys, os
a = sys.argv[sys.argv.index("--") + 1:]; B = json.load(open(a[0])); out = a[1]; os.makedirs(out, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
mat = bpy.data.materials.new("MM_Massing"); mat.diffuse_color = (0.6, 0.6, 0.6, 1)
chunks = {}
for b in B: chunks.setdefault(b["chunk"], []).append(b)
n = 0
for ck, bl in chunks.items():
    me = bpy.data.meshes.new("massing_" + ck); ob = bpy.data.objects.new("massing_" + ck, me); bpy.context.collection.objects.link(ob)
    x0, y0 = bl[0]["pts"][0]; o = (x0 / 100.0, -y0 / 100.0, 0.0); ob.location = o
    me.materials.append(mat); bm = bmesh.new()
    for b in bl:
        P = [(x / 100.0 - o[0], -y / 100.0 - o[1]) for x, y in b["pts"]]
        if len(P) < 3: continue
        zb, zt = b["base"] / 100.0, b["top"] / 100.0
        bot = [bm.verts.new((x, y, zb)) for x, y in P]; top = [bm.verts.new((x, y, zt)) for x, y in P]
        try:
            fs = [bm.faces.new(top), bm.faces.new(list(reversed(bot)))]
            for i in range(len(P)):
                j = (i + 1) % len(P); fs.append(bm.faces.new((bot[i], bot[j], top[j], top[i])))
        except ValueError:
            continue
        bmesh.ops.recalc_face_normals(bm, faces=fs)
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 4])
    bm.to_mesh(me); bm.free(); n += 1
    bpy.ops.object.select_all(action="DESELECT"); ob.select_set(True)
    bpy.ops.export_scene.fbx(filepath=os.path.join(out, ob.name + ".fbx"), use_selection=True, apply_unit_scale=True, apply_scale_options="FBX_SCALE_UNITS",
                             axis_forward="-Y", axis_up="Z", object_types={"MESH"}, mesh_smooth_type="FACE", bake_space_transform=False)
print("MASSING_OK", n)
