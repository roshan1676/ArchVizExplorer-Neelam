# AB podium roof parapet (deck-local UE cm; Y flipped for Blender): wall 27 cm thick, 104 cm + 8 cm coping (37 cm wide)
import bpy, bmesh
bpy.ops.wm.read_factory_settings(use_empty=True)
me=bpy.data.meshes.new("SM_Podium_AB_Parapet"); ob=bpy.data.objects.new("SM_Podium_AB_Parapet", me); bpy.context.collection.objects.link(ob)
for n in ("MI_Paint_White_Trim","MI_Kerb_Concrete"): me.materials.append(bpy.data.materials.new(n))
bm=bmesh.new(); uvl=bm.loops.layers.uv.new("UVMap")
P=lambda x,y,z:(x/100.0,-y/100.0,z/100.0)
def ring(xo,yo,xi,yi,z0,z1,mat):
    o=[(-xo,-yo),(xo,-yo),(xo,yo),(-xo,yo)]; i=[(-xi,-yi),(xi,-yi),(xi,yi),(-xi,yi)]
    ob_=[bm.verts.new(P(x,y,z0)) for x,y in o]; ot=[bm.verts.new(P(x,y,z1)) for x,y in o]
    ib=[bm.verts.new(P(x,y,z0)) for x,y in i]; it=[bm.verts.new(P(x,y,z1)) for x,y in i]
    fs=[]
    for k in range(4):
        j=(k+1)%4
        fs.append(bm.faces.new((ob_[k],ob_[j],ot[j],ot[k])))      # outer
        fs.append(bm.faces.new((ib[j],ib[k],it[k],it[j])))        # inner
        fs.append(bm.faces.new((ot[k],ot[j],it[j],it[k])))        # top
        fs.append(bm.faces.new((ib[k],ib[j],ob_[j],ob_[k])))      # bottom
    for f in fs: f.material_index=mat
    return fs
fs=ring(3504,2788,3477,2761,-2,104,0)+ring(3509,2793,3472,2756,104,112,1)
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
for f in bm.faces:
    n=f.normal
    for l in f.loops:
        x,y,z=l.vert.co.x*100,-l.vert.co.y*100,l.vert.co.z*100
        l[uvl].uv=(x/100,y/100) if abs(n.z)>0.5 else (((x if abs(n.y)>abs(n.x) else y))/100, z/100)
bm.to_mesh(me); bm.free()
bpy.ops.export_scene.fbx(filepath="/tmp/slab/SM_Podium_AB_Parapet.fbx", use_selection=False, apply_unit_scale=True, apply_scale_options="FBX_SCALE_UNITS",
                         axis_forward="-Y", axis_up="Z", object_types={"MESH"}, mesh_smooth_type="FACE", bake_space_transform=False)
print("PAR_OK")
