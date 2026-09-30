import bpy, bmesh
bpy.ops.wm.read_factory_settings(use_empty=True)
X0,X1,Y0,Y1 = -3477.0, 3477.0, -2761.0, 2761.0      # deck-local cm (UE)
ZT, ZB = -1.5, -40.0
me=bpy.data.meshes.new("SM_Podium_Deck_AB_Fill"); ob=bpy.data.objects.new("SM_Podium_Deck_AB_Fill", me); bpy.context.collection.objects.link(ob)
mat=bpy.data.materials.new("MI_Paving_Deck"); me.materials.append(mat)
bm=bmesh.new(); uvl=bm.loops.layers.uv.new("UVMap")
P=lambda x,y,z:(x/100.0,-y/100.0,z/100.0)
def uv(x,y): return (x/120.0-29.02, 1.0-(y/120.0-18.87))
c=[(X0,Y0),(X1,Y0),(X1,Y1),(X0,Y1)]
top=[bm.verts.new(P(x,y,ZT)) for x,y in c]; bot=[bm.verts.new(P(x,y,ZB)) for x,y in c]
faces=[bm.faces.new(top), bm.faces.new(list(reversed(bot)))]
for i in range(4):
    j=(i+1)%4; faces.append(bm.faces.new((bot[i],bot[j],top[j],top[i])))
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
for f in bm.faces:
    for l in f.loops:
        x=l.vert.co.x*100; y=-l.vert.co.y*100; z=l.vert.co.z*100
        if abs(f.normal.z)>0.5: l[uvl].uv=uv(x,y)
        else: l[uvl].uv=((x+y)/120.0, z/120.0)
bm.to_mesh(me); bm.free()
bpy.ops.export_scene.fbx(filepath="/tmp/slab/SM_Podium_Deck_AB_Fill.fbx", use_selection=False, apply_unit_scale=True, apply_scale_options="FBX_SCALE_UNITS",
                         axis_forward="-Y", axis_up="Z", object_types={"MESH"}, mesh_smooth_type="FACE", bake_space_transform=False)
print("SLAB_OK")
