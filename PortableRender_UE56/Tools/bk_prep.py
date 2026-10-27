"""BlenderKit asset .blend -> one joined object, pivot at bottom centre, saved as <out.blend> (source file untouched).
blender --background --factory-startup <asset.blend> --python bk_prep.py -- <out.blend>
Then run blend_export.py and bake_mats.py on <out.blend> like a scene."""
import bpy, sys
from mathutils import Vector

out = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene
objs = [o for o in sc.objects if o.type in ('MESH', 'CURVE', 'FONT', 'SURFACE') and o.visible_get() and not o.hide_render]
for o in sc.objects: o.select_set(o in objs)
bpy.context.view_layer.objects.active = objs[0]
bpy.ops.object.make_single_user(object=True, obdata=True)
bpy.ops.object.convert(target='MESH')                     # applies modifiers / realizes geometry nodes
bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
if len(bpy.context.selected_objects) > 1: bpy.ops.object.join()
ob = bpy.context.view_layer.objects.active
ob.name = "PROP"
pts = [ob.matrix_world @ v.co for v in ob.data.vertices]
lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
pivot = Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z))
ob.data.transform(__import__("mathutils").Matrix.Translation(-pivot)); ob.location = (0, 0, 0)
for o in list(sc.objects):                                 # drop everything else (lights/empties of the asset file)
    if o != ob: bpy.data.objects.remove(o)
bpy.ops.wm.save_as_mainfile(filepath=out)
print("@@PREP", out, "size_m", [round(v, 3) for v in (hi - lo)], "tris", sum(len(p.vertices) - 2 for p in ob.data.polygons))
