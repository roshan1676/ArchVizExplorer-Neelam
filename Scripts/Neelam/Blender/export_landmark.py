# blender -b --factory-startup file.blend --python export_landmark.py -- out.fbx
# Drops the reference image sheet(s) (objects named 'ChatGPT Image...'), moves the building so its bounding-box
# bottom-centre is at the origin, exports FBX with embedded textures + a json with the size (m).
import bpy, sys, json, mathutils, bmesh
for _o in bpy.data.objects:
    if _o.type == 'MESH' and _o.data.is_editmode:
        bm_ = bmesh.from_edit_mesh(_o.data); bmesh.update_edit_mesh(_o.data)
try:
    bpy.ops.object.mode_set(mode='OBJECT')
except Exception:
    pass
out = sys.argv[sys.argv.index("--") + 1]
for o in list(bpy.data.objects):
    if o.name.startswith("ChatGPT") or o.type != "MESH": bpy.data.objects.remove(o, do_unlink=True)
for o in bpy.data.objects:                       # apply transforms without operators (works for hidden objects too)
    o.hide_set(False) if o.name in bpy.context.view_layer.objects else None; o.hide_viewport = False; o.hide_render = False
    if o.data.users > 1: o.data = o.data.copy()
    o.data.transform(o.matrix_world); o.matrix_world = mathutils.Matrix.Identity(4)
mn = mathutils.Vector((1e9,) * 3); mx = mathutils.Vector((-1e9,) * 3)
for o in bpy.data.objects:
    for v in o.data.vertices:
        w = o.matrix_world @ v.co; mn = mathutils.Vector(map(min, mn, w)); mx = mathutils.Vector(map(max, mx, w))
off = mathutils.Vector(((mn.x + mx.x) / 2, (mn.y + mx.y) / 2, mn.z))
for o in bpy.data.objects:
    o.data.transform(mathutils.Matrix.Translation(-off))
import bmesh
for o in bpy.data.objects:                       # some client boxes have inward normals -> make every face point outward
    if o.data.is_editmode:
        bm = bmesh.from_edit_mesh(o.data)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bmesh.update_edit_mesh(o.data)
    else:
        bm = bmesh.new(); bm.from_mesh(o.data)
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0001)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bm.to_mesh(o.data); bm.free()
    for poly in o.data.polygons: poly.use_smooth = False
bpy.ops.file.pack_all()
bpy.ops.export_scene.fbx(filepath=out, use_selection=False, apply_unit_scale=True, apply_scale_options="FBX_SCALE_UNITS", axis_forward="-Y", axis_up="Z",
                         object_types={"MESH"}, path_mode="COPY", embed_textures=True, mesh_smooth_type="FACE")
json.dump({"size_m": [mx.x - mn.x, mx.y - mn.y, mx.z - mn.z], "objects": [o.name for o in bpy.data.objects]}, open(out + ".json", "w"))
print("LM_OK", out)
