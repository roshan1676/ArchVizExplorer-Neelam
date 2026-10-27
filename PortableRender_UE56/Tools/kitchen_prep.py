"""BlenderKit 'kitchen-set' -> 2BHK kitchen: drop the chimney hood, cut everything above the 2.6 m ceiling,
join into one mesh 'PROP' keeping the asset's own origin (= inside corner of the L, so placement is exact).
blender --background --factory-startup <kitchen-set.blend> --python kitchen_prep.py -- <out.blend>"""
import bpy, bmesh, sys
from mathutils import Vector

out = sys.argv[sys.argv.index("--") + 1]
CEIL = 2.6
sc = bpy.context.scene
for name in ("Box119",):                                   # chimney hood: would sit in front of the window
    if name in bpy.data.objects: bpy.data.objects.remove(bpy.data.objects[name])
objs = [o for o in sc.objects if o.type == 'MESH' and o.visible_get() and not o.hide_render]
for o in sc.objects: o.select_set(o in objs)
bpy.context.view_layer.objects.active = objs[0]
bpy.ops.object.make_single_user(object=True, obdata=True)
bpy.ops.object.convert(target='MESH')
bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
bpy.ops.object.join()
ob = bpy.context.view_layer.objects.active; ob.name = "PROP"
# clean shading: the asset's custom split normals give triangle facets on flat panels
bpy.ops.mesh.customdata_custom_splitnormals_clear()
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.remove_doubles(threshold=0.0001); bpy.ops.mesh.normals_make_consistent(inside=False)
bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.object.shade_smooth_by_angle(angle=0.5236, keep_sharp_edges=True)
bm = bmesh.new(); bm.from_mesh(ob.data)
geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
bmesh.ops.bisect_plane(bm, geom=geom, plane_co=(0, 0, CEIL), plane_no=(0, 0, 1), clear_outer=True)
bm.to_mesh(ob.data); bm.free()
for o in list(sc.objects):
    if o != ob: bpy.data.objects.remove(o)
bpy.ops.wm.save_as_mainfile(filepath=out)
pts = [v.co for v in ob.data.vertices]
print("@@KITCHEN", out, "x", round(min(p.x for p in pts), 2), round(max(p.x for p in pts), 2),
      "y", round(min(p.y for p in pts), 2), round(max(p.y for p in pts), 2), "z", round(max(p.z for p in pts), 2),
      "mats", [m.name for m in ob.data.materials if m])
