"""Headless, read-only: list objects of the client amenity .blend (name, type, faces, materials, size, collection).
blender -b <file> --python inventory_blend.py -- <out.json>   (never saves, never renders)"""
import bpy, sys, json
out = sys.argv[sys.argv.index("--") + 1]
rows = []
for o in bpy.data.objects:
    if o.type not in ("MESH", "EMPTY", "LIGHT", "CURVE"): continue
    f = len(o.data.polygons) if o.type == "MESH" else 0
    d = [round(v, 2) for v in o.dimensions]
    rows.append({"n": o.name, "t": o.type, "f": f, "dim": d, "loc": [round(v, 2) for v in o.matrix_world.translation],
                 "col": [c.name for c in o.users_collection][:2], "mat": [m.name for m in getattr(o.data, "materials", []) if m][:4] if o.type == "MESH" else [],
                 "inst": o.instance_collection.name if o.instance_collection else None, "parent": o.parent.name if o.parent else None})
cols = {c.name: len(c.all_objects) for c in bpy.data.collections}
json.dump({"objects": rows, "collections": cols, "images": len(bpy.data.images), "materials": len(bpy.data.materials)}, open(out, "w"))
