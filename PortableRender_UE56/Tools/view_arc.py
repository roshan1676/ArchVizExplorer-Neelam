"""Curved photo backdrop: a cylinder arc (radius 1 m) whose rows sit at the right elevation angle for a photo.
blender --background --factory-startup --python view_arc.py -- <out.gltf> <hfov_deg> <aspect w/h> <horizon_row 0..1 from top>
Unreal: scale by the radius in metres*100 and put the pivot at eye height."""
import bpy, bmesh, sys, math
out, hfov, aspect, horizon = sys.argv[sys.argv.index("--") + 1:][:4]
hfov, aspect, horizon = float(hfov), float(aspect), float(horizon)
vfov = hfov / aspect
bpy.ops.wm.read_factory_settings(use_empty=True)
me = bpy.data.meshes.new("ViewArc"); bm = bmesh.new(); uv = bm.loops.layers.uv.new("UVMap")
NU, NV = 96, 24
grid = []
for j in range(NV + 1):
    v = j / NV                                      # 0 = top row of the photo
    elev = math.radians((horizon - v) * vfov)       # row at the horizon line -> 0 deg
    row = []
    for i in range(NU + 1):
        u = i / NU
        az = math.radians((u - 0.5) * hfov)         # centre of the photo looks down -Y (Blender), i.e. +Y... see note
        row.append(bm.verts.new((math.sin(az), -math.cos(az), math.tan(elev))))
    grid.append(row)
for j in range(NV):
    for i in range(NU):
        f = bm.faces.new((grid[j][i], grid[j + 1][i], grid[j + 1][i + 1], grid[j][i + 1]))
        for l, (uu, vv) in zip(f.loops, ((i / NU, 1 - j / NV), (i / NU, 1 - (j + 1) / NV), ((i + 1) / NU, 1 - (j + 1) / NV), ((i + 1) / NU, 1 - j / NV))):
            l[uv].uv = (uu, vv)
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
bm.to_mesh(me); bm.free()
ob = bpy.data.objects.new("ViewArc", me); bpy.context.scene.collection.objects.link(ob)
# normals must face the centre (viewer): flip if they point outward
if (me.polygons[len(me.polygons) // 2].normal @ me.polygons[len(me.polygons) // 2].center) > 0:
    me.flip_normals()
# UVs from each corner's direction (robust to any face flipping above)
uvl = me.uv_layers[0].data
for poly in me.polygons:
    for li in poly.loop_indices:
        x, y, z = me.vertices[me.loops[li].vertex_index].co
        az = math.degrees(math.atan2(x, -y)); el = math.degrees(math.atan(z))
        uvl[li].uv = (az / hfov + 0.5, 1.0 - (horizon - el / vfov))
m = bpy.data.materials.new("ViewBackdrop"); me.materials.append(m)
ob.select_set(True); bpy.context.view_layer.objects.active = ob
bpy.ops.export_scene.gltf(filepath=out, export_format='GLTF_SEPARATE', use_selection=True, export_yup=True)
print("@@ARC", out, "vfov", round(vfov, 1))
