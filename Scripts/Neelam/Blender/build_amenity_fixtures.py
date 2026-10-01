# Amenity lighting fixtures (lighting plan "Amenities Floor design", 7th podium floor).
# UE cm, +X = facing direction, Z up; Blender gets (x/100, -y/100, z/100). Slots: Body / Lens (/ Grille).
# run: python3 build_amenity_fixtures.py <outdir>
import bpy, bmesh, math, sys, os
from mathutils import Matrix, Vector
OUT = sys.argv[-1] if len(sys.argv) > 1 and not sys.argv[-1].endswith(".py") else "/tmp/fixtures_fbx"
os.makedirs(OUT, exist_ok=True)

def new_mesh(name, slots):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    me = bpy.data.meshes.new(name); ob = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(ob)
    for s in slots: me.materials.append(bpy.data.materials.new(s))
    bm = bmesh.new(); return me, ob, bm

def _xf(bm, verts, M):
    bmesh.ops.transform(bm, matrix=M, verts=verts)

def cyl(bm, r0, r1, z0, z1, mat, seg=24, M=None, cap0=True, cap1=True):
    """frustum along +Z (UE cm), optional transform M (UE space)"""
    b = [bm.verts.new((r0*math.cos(2*math.pi*k/seg), r0*math.sin(2*math.pi*k/seg), z0)) for k in range(seg)]
    t = [bm.verts.new((r1*math.cos(2*math.pi*k/seg), r1*math.sin(2*math.pi*k/seg), z1)) for k in range(seg)]
    fs = [bm.faces.new((b[k], b[(k+1)%seg], t[(k+1)%seg], t[k])) for k in range(seg)]
    if cap1: fs.append(bm.faces.new(t))
    if cap0: fs.append(bm.faces.new(list(reversed(b))))
    for f in fs: f.material_index = mat; f.smooth = True
    if M is not None: _xf(bm, b + t, M)
    return fs

def box(bm, x0, x1, y0, y1, z0, z1, mat, M=None):
    v = [bm.verts.new((x, y, z)) for z in (z0, z1) for y in (y0, y1) for x in (x0, x1)]
    idx = [(0,2,3,1),(4,5,7,6),(0,1,5,4),(2,6,7,3),(0,4,6,2),(1,3,7,5)]
    fs = [bm.faces.new([v[i] for i in q]) for q in idx]
    for f in fs: f.material_index = mat
    if M is not None: _xf(bm, v, M)
    return fs

def finish(me, ob, bm, name):
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    uvl = bm.loops.layers.uv.new("UVMap")
    for f in bm.faces:
        n = f.normal
        for l in f.loops:
            x, y, z = l.vert.co
            l[uvl].uv = (x/50, y/50) if abs(n.z) > 0.6 else ((math.atan2(y, x)/math.pi if abs(n.z) < 0.2 and False else (x + y)/50), z/50)
    # UE cm -> Blender m, flip Y
    for v in bm.verts: v.co = Vector((v.co.x/100.0, -v.co.y/100.0, v.co.z/100.0))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = False
    bpy.ops.export_scene.fbx(filepath=os.path.join(OUT, name + ".fbx"), use_selection=False, apply_unit_scale=True,
                             apply_scale_options="FBX_SCALE_UNITS", axis_forward="-Y", axis_up="Z", object_types={"MESH"},
                             mesh_smooth_type="FACE", bake_space_transform=False)
    print("OK", name, len(me.polygons))

# 1 bollard 9 W: round 80 cm, frosted lens band 62-74 cm
me, ob, bm = new_mesh("SM_Neelam_Lt_Bollard", ["Body", "Lens"])
cyl(bm, 9, 9, 0, 2, 0); cyl(bm, 7, 7, 2, 62, 0, cap0=False, cap1=False); cyl(bm, 6.4, 6.4, 62, 74, 1, cap0=False, cap1=False)
cyl(bm, 7.8, 7.8, 74, 78, 0); cyl(bm, 7.8, 6.5, 78, 80, 0, cap0=False)
for k in range(4):   # 4 thin mullions across the lens
    a = k*math.pi/2; c, s = math.cos(a), math.sin(a)
    box(bm, -0.6, 0.6, -0.6, 0.6, 62, 74, 0, M=Matrix.Translation((6.6*c, 6.6*s, 0)))
finish(me, ob, bm, "SM_Neelam_Lt_Bollard")

# 2 tree uplighter 6 W: spike luminaire, glare cowl, lens on top (light aims +Z)
me, ob, bm = new_mesh("SM_Neelam_Lt_Uplight", ["Body", "Lens"])
cyl(bm, 1.2, 0.3, -12, 0, 0, seg=8)              # spike (hidden in soil)
cyl(bm, 5, 5, 0, 1.5, 0); cyl(bm, 4.2, 4.2, 1.5, 11, 0, cap1=False); cyl(bm, 3.6, 3.6, 10.2, 10.4, 1, cap0=False)
cyl(bm, 4.6, 4.9, 10.4, 13.5, 0, cap0=False, cap1=False); cyl(bm, 4.3, 4.6, 10.4, 13.5, 0, cap0=False, cap1=False)
finish(me, ob, bm, "SM_Neelam_Lt_Uplight")

# 3 underwater focus light 10 W: wall-mounted disc facing +X (back plate at x=0)
me, ob, bm = new_mesh("SM_Neelam_Lt_PoolLight", ["Body", "Lens"])
Ry = Matrix.Rotation(math.radians(90), 4, 'Y')
cyl(bm, 11, 10.5, 0, 2.2, 0, seg=32, M=Ry); cyl(bm, 8.5, 8.5, 2.2, 2.6, 1, seg=32, M=Ry, cap0=False)
finish(me, ob, bm, "SM_Neelam_Lt_PoolLight")

# 4 flood light 60 W on a 7 m pole: head faces +X, tilted 25 deg down
me, ob, bm = new_mesh("SM_Neelam_Lt_FloodPole", ["Body", "Lens"])
box(bm, -17, 17, -17, 17, 0, 2, 0); cyl(bm, 7.5, 5, 2, 700, 0, seg=16)
box(bm, -3, 30, -3, 3, 684, 690, 0)                         # bracket arm
H = Matrix.Translation((34, 0, 690)) @ Matrix.Rotation(math.radians(25), 4, 'Y')   # +Y rot tips +X face downwards
box(bm, -8, 0, -26, 26, -20, 20, 0, M=H)                    # housing
box(bm, -12, -8, -22, 22, -16, 16, 0, M=H)                  # driver/heat sink
for k in range(-4, 5):                                      # fins
    box(bm, -16, -12, -0.4 + 5*k, 0.4 + 5*k, -16, 16, 0, M=H)
box(bm, 0, 0.8, -23.5, 23.5, -17.5, 17.5, 1, M=H)           # front glass
box(bm, -4, 4, -1.5, 1.5, -24, -20, 0, M=H)                 # yoke foot
finish(me, ob, bm, "SM_Neelam_Lt_FloodPole")

# 5 garden speaker: 38 cm column, perforated band (Grille)
me, ob, bm = new_mesh("SM_Neelam_Speaker", ["Body", "Grille"])
cyl(bm, 10.5, 10.5, 0, 2, 0); cyl(bm, 9.5, 9.5, 2, 20, 0, cap0=False, cap1=False); cyl(bm, 9.2, 9.2, 20, 33, 1, cap0=False, cap1=False)
cyl(bm, 9.8, 9.8, 33, 36, 0, cap0=False); cyl(bm, 9.8, 5, 36, 38.5, 0, cap0=False)
finish(me, ob, bm, "SM_Neelam_Speaker")

# 6 in-ground LED strip, 100 cm long along +X (scaled per run): alu channel + opal diffuser
me, ob, bm = new_mesh("SM_Neelam_Lt_Strip", ["Body", "Lens"])
box(bm, 0, 100, -1.9, 1.9, -1.0, 0.6, 0); box(bm, 0, 100, -1.3, 1.3, 0.6, 0.9, 1)
finish(me, ob, bm, "SM_Neelam_Lt_Strip")
