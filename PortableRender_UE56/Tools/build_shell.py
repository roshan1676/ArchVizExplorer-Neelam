"""Build an apartment shell from a traced layout JSON (Tools/layouts/<unit>.json).
blender --background --factory-startup --python build_shell.py -- <layout.json> <out.blend> [overlay.png]
Objects: WALL_*, FLOOR_<room>, CEIL_<room>, SLAB_*, WIN_*, RAIL_*. World-scale box UVs (1 UV unit = 1 m).
overlay.png: top-down X-ray render of the shell over the plan image, to check the trace."""
import bpy, bmesh, json, os, sys
from mathutils import Vector

args = sys.argv[sys.argv.index("--") + 1:]
L = json.load(open(args[0]))
out_blend = args[1]
overlay = args[2] if len(args) > 2 else None
S, (PW, PH) = L["scale"], L["plan_px"]
H, SLAB = L["clear_height"], L["slab"]

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene

def X(px): return px / S
def Y(py): return (PH - py) / S

def mat(name, rgb, alpha=1.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*rgb, 1)
    if alpha < 1:
        b.inputs["Transmission Weight"].default_value = 1.0; b.inputs["Roughness"].default_value = 0.02
    m.diffuse_color = (*rgb, alpha)
    return m

M = {"rcc": mat("M_Wall_Paint", (0.85, 0.83, 0.80)), "block": mat("M_Wall_Paint", (0.85, 0.83, 0.80)),
     "floor": mat("M_Floor", (0.9, 0.9, 0.88)), "ceil": mat("M_Ceiling", (0.95, 0.95, 0.95)),
     "slab": mat("M_Slab", (0.5, 0.5, 0.5)), "frame": mat("M_WindowFrame", (0.12, 0.12, 0.12)),
     "glass": mat("Window Glass", (0.95, 0.97, 0.98), 0.3), "rail": mat("M_Handrail", (0.8, 0.8, 0.8))}
for k, rgb in (("floor_wet", (0.75, 0.74, 0.72)), ("floor_balcony", (0.8, 0.78, 0.74))):
    M[k] = mat("M_" + k.title().replace("_", ""), rgb)

def box_uv(obj):
    """World-scale box projection: each face takes the two axes it doesn't face."""
    bm = bmesh.new(); bm.from_mesh(obj.data)
    uv = bm.loops.layers.uv.new("UVMap")
    mw = obj.matrix_world
    for f in bm.faces:
        n = f.normal; ax = max(range(3), key=lambda i: abs(n[i]))
        u_i, v_i = [(1, 2), (0, 2), (0, 1)][ax]
        for l in f.loops:
            w = mw @ l.vert.co
            l[uv].uv = (w[u_i], w[v_i])
    bm.to_mesh(obj.data); bm.free()

def cuboid(name, x0, x1, y0, y1, z0, z1, material, coll):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector(((x0 + x1) / 2 + v.co.x * (x1 - x0), (y0 + y1) / 2 + v.co.y * (y1 - y0), (z0 + z1) / 2 + v.co.z * (z1 - z0)))
    bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); coll.objects.link(o)
    me.materials.append(material)
    return o

def rect(r):  # plan px rect -> metres (x0,x1,y0,y1) with y flipped
    return X(min(r[0], r[1])), X(max(r[0], r[1])), Y(max(r[2], r[3])), Y(min(r[2], r[3]))

def coll(name):
    c = bpy.data.collections.new(name); sc.collection.children.link(c); return c

C_W, C_F, C_C, C_O = coll("Walls"), coll("Floors"), coll("Ceilings"), coll("Openings")

# ---- walls with boolean openings ----
cutters = []
for op in L["openings"]:
    x0, x1, y0, y1 = rect(op["r"])
    c = cuboid("CUT_" + op["name"], x0, x1, y0, y1, op["z"][0], op["z"][1], M["slab"], C_O)
    c.display_type = 'WIRE'; c.hide_render = True
    cutters.append((op, c))
walls = []
for name, w in L["walls"].items():
    x0, x1, y0, y1 = rect(w["r"])
    o = cuboid("WALL_" + name, x0, x1, y0, y1, 0.0, H, M[w["kind"]], C_W)
    for op, c in cutters:
        cx0, cx1, cy0, cy1 = rect(op["r"])
        if cx0 < x1 and cx1 > x0 and cy0 < y1 and cy1 > y0:
            mod = o.modifiers.new("cut_" + op["name"], 'BOOLEAN'); mod.object = c; mod.operation = 'DIFFERENCE'; mod.solver = 'EXACT'
    walls.append(o)
dg = bpy.context.evaluated_depsgraph_get()
for o in walls:
    if o.modifiers:
        me = bpy.data.meshes.new_from_object(o.evaluated_get(dg))
        o.modifiers.clear(); old = o.data; o.data = me; bpy.data.meshes.remove(old)
    box_uv(o)
for _, c in cutters: bpy.data.objects.remove(c)

# ---- floors / ceilings / slabs ----
xs = [v for w in L["walls"].values() for v in w["r"][:2]]; ys = [v for w in L["walls"].values() for v in w["r"][2:]]
bx0, bx1, by0, by1 = rect([min(xs), max(xs), min(ys), max(ys)])
cuboid("SLAB_floor", bx0, bx1, by0, by1, -SLAB, -0.02, M["slab"], C_F)
cuboid("SLAB_roof", bx0, bx1, by0, by1, H, H + SLAB, M["slab"], C_C)
for room, r in L["rooms"].items():
    x0, x1, y0, y1 = rect(r)
    fm = M["floor_wet"] if room.startswith("toilet") else M["floor_balcony"] if room == "balcony" else M["floor"]
    top = -0.02 if room in ("balcony",) or room.startswith("toilet") else 0.0   # wet areas sunk 20 mm
    f = cuboid("FLOOR_" + room, x0, x1, y0, y1, -0.04, top, fm, C_F); box_uv(f)
    c = cuboid("CEIL_" + room, x0, x1, y0, y1, H - 0.01, H, M["ceil"], C_C); box_uv(c)

# ---- windows / sliders: glass + frame ----
for op in L["openings"]:
    if op["type"] not in ("window", "slider"): continue
    x0, x1, y0, y1 = rect(op["r"]); z0, z1 = op["z"]
    along_x = (x1 - x0) > (y1 - y0)
    mid = ((x0 + x1) / 2, (y0 + y1) / 2); fw, gt = 0.05, 0.012
    def pane(n, a0, a1, off=0.0):
        if along_x: return cuboid(n, a0, a1, mid[1] - gt / 2 + off, mid[1] + gt / 2 + off, z0 + fw, z1 - fw, M["glass"], C_O)
        return cuboid(n, mid[0] - gt / 2 + off, mid[0] + gt / 2 + off, a0, a1, z0 + fw, z1 - fw, M["glass"], C_O)
    a0, a1 = (x0, x1) if along_x else (y0, y1)
    if op["type"] == "slider":
        m = (a0 + a1) / 2; pane("WIN_" + op["name"] + "_a", a0 + fw, m + 0.03, -0.03); pane("WIN_" + op["name"] + "_b", m - 0.03, a1 - fw, 0.03)
    else:
        pane("WIN_" + op["name"] + "_glass", a0 + fw, a1 - fw)
    t = 0.07  # frame depth
    for n, (fa0, fa1, fz0, fz1) in {"l": (a0, a0 + fw, z0, z1), "r": (a1 - fw, a1, z0, z1), "b": (a0, a1, z0, z0 + fw), "t": (a0, a1, z1 - fw, z1)}.items():
        if along_x: cuboid("WIN_%s_frame_%s" % (op["name"], n), fa0, fa1, mid[1] - t / 2, mid[1] + t / 2, fz0, fz1, M["frame"], C_O)
        else: cuboid("WIN_%s_frame_%s" % (op["name"], n), mid[0] - t / 2, mid[0] + t / 2, fa0, fa1, fz0, fz1, M["frame"], C_O)

# ---- glass railings ----
for r in L.get("railings", []):
    x0, x1, y0, y1 = rect(r["r"]); along_x = (x1 - x0) > (y1 - y0); mid = ((x0 + x1) / 2, (y0 + y1) / 2)
    if along_x:
        cuboid("RAIL_" + r["name"] + "_glass", x0, x1, mid[1] - 0.006, mid[1] + 0.006, 0.0, r["h"] - 0.05, M["glass"], C_O)
        cuboid("RAIL_" + r["name"] + "_cap", x0, x1, mid[1] - 0.03, mid[1] + 0.03, r["h"] - 0.05, r["h"], M["rail"], C_O)
    else:
        cuboid("RAIL_" + r["name"] + "_glass", mid[0] - 0.006, mid[0] + 0.006, y0, y1, 0.0, r["h"] - 0.05, M["glass"], C_O)
        cuboid("RAIL_" + r["name"] + "_cap", mid[0] - 0.03, mid[0] + 0.03, y0, y1, r["h"] - 0.05, r["h"], M["rail"], C_O)

os.makedirs(os.path.dirname(out_blend), exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=out_blend)
print("@@SAVED", out_blend, len(walls), "walls", len(L["rooms"]), "rooms")

# ---- overlay check ----
if overlay:
    img = bpy.data.images.load(os.path.join(os.path.dirname(args[0]), L["plan"]))
    pm = bpy.data.materials.new("M_Plan"); pm.use_nodes = True
    t = pm.node_tree.nodes.new("ShaderNodeTexImage"); t.image = img
    pm.node_tree.links.new(t.outputs["Color"], pm.node_tree.nodes["Principled BSDF"].inputs["Base Color"])
    bpy.ops.mesh.primitive_plane_add(size=1, location=(X(PW) / 2, (PH / S) / 2, -0.5))
    p = bpy.context.object; p.scale = (X(PW), PH / S, 1); p.data.materials.append(pm)
    for o in sc.objects:
        if o.name.startswith(("CEIL_", "SLAB_roof", "FLOOR_", "SLAB_floor")): o.hide_render = True
    cd = bpy.data.cameras.new("top"); cd.type = 'ORTHO'; cd.ortho_scale = PH / S; cd.clip_start = 0.01; cd.clip_end = 10
    cam = bpy.data.objects.new("top", cd); sc.collection.objects.link(cam); cam.location = (X(PW) / 2, (PH / S) / 2, 1.5); sc.camera = cam
    sc.render.engine = 'BLENDER_WORKBENCH'; sh = sc.display.shading
    sh.light = 'FLAT'; sh.color_type = 'TEXTURE'; sh.show_xray = True; sh.xray_alpha = 0.55
    for o in sc.objects:
        if o.name.startswith("WALL_"): o.color = (1, 0, 0, 1)
    sh.color_type = 'TEXTURE'
    sc.render.resolution_x, sc.render.resolution_y = PW, PH; sc.render.filepath = overlay
    bpy.ops.render.render(write_still=True); print("@@OVERLAY", overlay)
