# run: blender -b file.blend --python inspect_blend.py -- out.json
import bpy, mathutils, json, sys
out = sys.argv[sys.argv.index("--") + 1]
mn = [1e18] * 3; mx = [-1e18] * 3; objs = []; tris = 0
for o in bpy.data.objects:
    d = {"name": o.name, "type": o.type, "loc": [round(v, 2) for v in o.location], "rot": [round(v, 3) for v in o.rotation_euler],
         "scale": [round(v, 3) for v in o.scale], "parent": o.parent.name if o.parent else None}
    if o.type == "MESH":
        d["verts"] = len(o.data.vertices); d["mats"] = [m.name for m in o.data.materials if m]
        tris += sum(len(p.vertices) - 2 for p in o.data.polygons)
        for c in o.bound_box:
            w = o.matrix_world @ mathutils.Vector(c)
            for i in range(3): mn[i] = min(mn[i], w[i]); mx[i] = max(mx[i], w[i])
    objs.append(d)
sc = bpy.context.scene
props = {k: str(v)[:300] for k, v in sc.items()}
for o in bpy.data.objects:
    for k, v in o.items(): props[o.name + "." + k] = str(v)[:300]
res = {"objects": len(objs), "meshes": sum(1 for o in objs if o["type"] == "MESH"), "tris": tris, "list": objs[:12],
       "bbox_min": [round(v, 2) for v in mn], "bbox_max": [round(v, 2) for v in mx], "size": [round(b - a, 2) for a, b in zip(mn, mx)],
       "unit_scale": sc.unit_settings.scale_length, "props": props,
       "images": [(i.name, i.filepath, i.packed_file is not None) for i in bpy.data.images][:15],
       "materials": [m.name for m in bpy.data.materials][:20], "addons_georef": [k for k in sc.keys() if "lat" in k.lower() or "geo" in k.lower() or "crs" in k.lower()]}
json.dump(res, open(out, "w"), indent=1)
