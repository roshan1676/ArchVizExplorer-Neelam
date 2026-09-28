"""Neelam - realistic materials for the Wind Tunnel development (UE 5.5).

Run INSIDE the Unreal Editor:
    Output Log > Cmd dropdown "Python" >
    py "C:/Users/Admin/Documents/Unreal Projects/ArchVizExplorer-Neelam/Scripts/Neelam/Apply_WindTunnel_Materials.py"

Steps (safe to re-run; already-downloaded files are skipped):
  1. Downloads 20 CC0 PBR texture sets (2K: colour, normal, roughness, AO) from Poly Haven
     into <Project>/SourceArt/PolyHaven/<id>/            (~210 MB, first run only)
  2. Imports them to /Game/Neelam/Buildings/WindTunnel/Textures/PolyHaven/<id>/
     (normal maps: OpenGL -> green flipped; roughness/AO: linear masks)
  3. Builds 3 master materials in .../Materials/Master/
       M_Neelam_Surface  - PBR, real-world tiling, design-colour tint, anti-tiling macro variation
       M_Neelam_Glass    - translucent, fresnel reflections (glass, water, nets)
       M_Neelam_Emissive - light fixtures
  4. Creates one instance per design material in .../Materials/Instances/MI_<name>
     (colour/roughness/metallic/tile size taken from the model's own material definitions)
  5. Swaps them onto every mesh slot (the old M_ placeholders are kept, so it's reversible:
     set APPLY_TO_MESHES = False and re-run with RESTORE = True to go back).
  6. Writes Saved/Neelam/materials_report.json
"""
import json, os, sys, time, urllib.request, ssl
try:
    import unreal
except ImportError:
    sys.exit("Run this INSIDE the Unreal Editor (Output Log > Python), not in VS Code.")

ROOT      = "/Game/Neelam/Buildings/WindTunnel"
TEX_ROOT  = ROOT + "/Textures/PolyHaven"
MASTER    = ROOT + "/Materials/Master"
INST      = ROOT + "/Materials/Instances"
OLD_MATS  = ROOT + "/Materials"
MACRO_TEX = "/Game/ArchVizExplorer/Textures/T_MacroVariation"
APPLY_TO_MESHES = True
RESTORE   = False
RUN_REVIEW = globals().get("NEELAM_RUN_REVIEW", True)         # capture review screenshots afterwards (Capture_Review_Shots.py)          # True = put the original M_ placeholders back on the meshes
RES = "2k"
PROJECT = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
SRC_DIR = os.path.join(PROJECT, "SourceArt", "PolyHaven")

# Poly Haven sets: id -> real-world size of one texture repeat (metres)
TEXSETS = {
    "asphalt_02": 3.0, "concrete": 4.0, "painted_concrete": 2.0, "white_stucco": 2.0,
    "slate_floor": 2.29, "granite_tile": 2.3, "precast_stone_paving": 2.24,
    "concrete_pavers_02": 2.0, "rectangular_paving": 2.0, "leafy_grass": 2.0,
    "brown_mud_02": 1.3, "bark_brown_02": 1.0, "oak_wood_planks": 1.2,
    "rubberized_track": 2.0, "rubber_tiles": 2.0, "blue_floor_tiles_01": 2.0,
    "metal_plate": 0.5, "anti_slip_concrete": 2.5, "climbing_wall_02": 1.9,
    "large_sandstone_blocks": 3.0,
}
MAPS = {"D": "diff", "N": "nor_gl", "R": "rough", "AO": "ao"}

# Design materials (from the model's build scripts): colour (linear), roughness, metallic, UV0 tile (m)
# kind: S = surface, G = glass/translucent, E = emissive
# S params: texset, tint amount (0 = texture colour, 1 = design colour), use texture roughness, normal strength
M = {
 "M_Asphalt":               ("S", (0.13,0.13,0.135), 0.90, 0.0, 4.0, "asphalt_02", 0.35, 1, 1.0),
 "M_Bark":                  ("S", (0.25,0.17,0.10), 0.90, 0.0, 1.0, "bark_brown_02", 0.3, 1, 1.0),
 "M_BoundaryWall_Paint":    ("S", (0.62,0.52,0.37), 0.85, 0.0, 1.6, "white_stucco", 1.0, 0, 0.50),
 "M_ChainLink":             ("G", (0.04,0.05,0.05), 0.50, 0.6, 0.35),
 "M_ClimbingWall":          ("S", (0.62,0.55,0.45), 0.80, 0.0, 1.0, "climbing_wall_02", 0.4, 1, 1.0),
 "M_Climbing_Holds":        ("S", (0.85,0.35,0.10), 0.60, 0.0, 1.0, "rubber_tiles", 1.0, 0, 0.2),
 "M_Concrete_Roof":         ("S", (0.52,0.50,0.47), 0.85, 0.0, 1.2, "concrete", 0.5, 1, 1.0),
 "M_Court_Acrylic_Blue":    ("S", (0.10,0.25,0.50), 0.70, 0.0, 2.0, "anti_slip_concrete", 1.0, 0, 0.4),
 "M_Court_Acrylic_Blue_Dark":("S",(0.08,0.18,0.42), 0.70, 0.0, 2.0, "anti_slip_concrete", 1.0, 0, 0.4),
 "M_Court_Acrylic_Green":   ("S", (0.12,0.35,0.22), 0.70, 0.0, 2.0, "anti_slip_concrete", 1.0, 0, 0.4),
 "M_Court_Lines_White":     ("S", (0.92,0.92,0.90), 0.60, 0.0, 1.0, "anti_slip_concrete", 1.0, 0, 0.3),
 "M_Fabric_Cushion":        ("S", (0.86,0.83,0.76), 0.90, 0.0, 1.0, "white_stucco", 1.0, 0, 0.2),
 "M_Fence_Post":            ("S", (0.06,0.06,0.07), 0.40, 1.0, 1.0, "metal_plate", 1.0, 0, 0.3),
 "M_Furniture_Metal":       ("S", (0.15,0.15,0.16), 0.40, 1.0, 1.0, "metal_plate", 1.0, 0, 0.3),
 "M_Furniture_Wood":        ("S", (0.40,0.27,0.16), 0.60, 0.0, 1.0, "oak_wood_planks", 0.5, 1, 1.0),
 "M_Gate_Metal":            ("S", (0.09,0.09,0.10), 0.40, 1.0, 1.0, "metal_plate", 1.0, 0, 0.3),
 "M_Glass_Railing":         ("G", (0.45,0.55,0.58), 0.03, 0.0, 0.28),
 "M_Glass_Railing_Tinted":  ("G", (0.08,0.15,0.26), 0.03, 0.2, 0.62),
 "M_Glass_Residential":     ("G", (0.20,0.30,0.40), 0.02, 0.5, 0.72),
 "M_Glass_Retail":          ("G", (0.34,0.42,0.46), 0.02, 0.2, 0.40),
 "M_Grass_Lawn":            ("S", (0.16,0.33,0.08), 0.95, 0.0, 2.0, "leafy_grass", 0.4, 1, 1.0),
 "M_GreenWall":             ("S", (0.10,0.22,0.07), 0.90, 0.0, 1.0, "leafy_grass", 0.6, 1, 1.0),
 "M_Ground_Reserved":       ("S", (0.36,0.35,0.30), 0.95, 0.0, 4.0, "brown_mud_02", 0.4, 1, 1.0),
 "M_Interior_Dark":         ("S", (0.025,0.025,0.028),0.90,0.0, 1.0, "concrete", 1.0, 0, 0.0),
 "M_Jogging_EPDM":          ("S", (0.52,0.19,0.14), 0.90, 0.0, 2.0, "rubberized_track", 0.5, 1, 1.0),
 "M_Kerb_Concrete":         ("S", (0.58,0.57,0.55), 0.85, 0.0, 1.0, "concrete", 0.5, 1, 1.0),
 "M_Kotah_Stone":           ("S", (0.40,0.43,0.39), 0.75, 0.0, 1.2, "slate_floor", 0.6, 1, 1.0),
 "M_Leaves":                ("S", (0.13,0.30,0.08), 0.90, 0.0, 2.0, "leafy_grass", 0.7, 1, 0.6),
 "M_Light_Emissive":        ("E", (1.0,0.82,0.55), 16.0),
 "M_Louvre_Dark":           ("S", (0.07,0.07,0.075),0.50, 0.5, 1.0, "metal_plate", 1.0, 0, 0.3),
 "M_Metal_Grill":           ("S", (0.12,0.12,0.13), 0.40, 1.0, 1.0, "metal_plate", 1.0, 0, 0.3),
 "M_Metal_Railing":         ("S", (0.16,0.16,0.17), 0.35, 1.0, 1.0, "metal_plate", 1.0, 0, 0.3),
 "M_Metal_Screen_Champagne":("S", (0.70,0.60,0.44), 0.35, 1.0, 1.0, "metal_plate", 1.0, 0, 0.20),
 "M_Metal_WindowFrame":     ("S", (0.10,0.10,0.11), 0.40, 1.0, 1.0, "metal_plate", 1.0, 0, 0.2),
 "M_Net":                   ("G", (0.05,0.05,0.05), 0.80, 0.0, 0.60),
 "M_Paint_Accent_Taupe":    ("S", (0.40,0.30,0.20), 0.75, 0.0, 1.6, "white_stucco", 1.0, 0, 0.40),
 "M_Paint_Cream":           ("S", (0.66,0.52,0.32), 0.80, 0.0, 1.6, "white_stucco", 1.0, 0, 0.35),
 "M_Paint_White_Trim":      ("S", (0.78,0.70,0.54), 0.70, 0.0, 1.6, "white_stucco", 1.0, 0, 0.30),
 "M_Paving_Deck":           ("S", (0.62,0.59,0.54), 0.80, 0.0, 1.2, "rectangular_paving", 0.5, 1, 1.0),
 "M_Paving_Walkway":        ("S", (0.62,0.59,0.54), 0.80, 0.0, 1.2, "concrete_pavers_02", 0.5, 1, 1.0),
 "M_Planting_Soil":         ("S", (0.14,0.20,0.08), 0.95, 0.0, 2.0, "brown_mud_02", 0.3, 1, 1.0),
 "M_Plumeria_Leaves":       ("S", (0.16,0.36,0.10), 0.90, 0.0, 2.0, "leafy_grass", 0.7, 1, 0.6),
 "M_Podium_Arch_Terracotta":("S", (0.52,0.26,0.12), 0.55, 0.0, 1.6, "white_stucco", 1.0, 0, 0.30),
 "M_Podium_Screen_Bronze":  ("S", (0.50,0.24,0.10), 0.55, 0.0, 1.0, "oak_wood_planks", 0.9, 0, 0.15),
 "M_Pool_Coping_Stone":     ("S", (0.78,0.76,0.70), 0.60, 0.0, 1.2, "large_sandstone_blocks", 0.7, 1, 0.8),
 "M_Pool_Light":            ("E", (0.75,0.90,1.0), 24.0),
 "M_Pool_Tile":             ("S", (0.55,0.78,0.82), 0.25, 0.0, 1.0, "blue_floor_tiles_01", 0.5, 0, 1.0),
 "M_Pool_Water":            ("G", (0.10,0.45,0.60), 0.02, 0.0, 0.55),
 "M_Safety_Mat":            ("S", (0.15,0.20,0.35), 0.90, 0.0, 1.0, "rubber_tiles", 1.0, 1, 1.0),
 "M_Stone_Plinth":          ("S", (0.60,0.56,0.50), 0.70, 0.0, 2.0, "large_sandstone_blocks", 0.5, 1, 1.0),
 "M_Stone_PoolDeck":        ("S", (0.74,0.72,0.67), 0.70, 0.0, 1.2, "precast_stone_paving", 0.5, 1, 1.0),
 "M_Stone_Tabletop":        ("S", (0.85,0.84,0.80), 0.30, 0.0, 1.0, "granite_tile", 0.5, 0, 0.5),
 "M_Timber_Deck":           ("S", (0.42,0.27,0.16), 0.70, 0.0, 1.0, "oak_wood_planks", 0.5, 1, 1.0),
 "M_Timber_Pergola":        ("S", (0.30,0.19,0.11), 0.70, 0.0, 1.0, "oak_wood_planks", 0.5, 1, 1.0),
 "M_Track_Grey":            ("S", (0.50,0.50,0.48), 0.90, 0.0, 2.0, "rubberized_track", 1.0, 1, 1.0),
}

# how much of the photo texture's light/dark pattern shows through the design colour (0 = flat paint)
DETAIL = {"M_Paint_Cream": 0.22, "M_Paint_White_Trim": 0.18, "M_BoundaryWall_Paint": 0.3,
          "M_Paint_Accent_Taupe": 0.25, "M_Podium_Arch_Terracotta": 0.25, "M_Podium_Screen_Bronze": 0.2,
          "M_Court_Acrylic_Blue": 0.3, "M_Court_Acrylic_Blue_Dark": 0.3, "M_Court_Acrylic_Green": 0.3,
          "M_Interior_Dark": 0.0, "M_Climbing_Holds": 0.2, "M_Fabric_Cushion": 0.3}
MACRO = {"M_Paint_Cream": 0.12, "M_Paint_White_Trim": 0.1, "M_Podium_Screen_Bronze": 0.3, "M_Interior_Dark": 0.0}

EAL = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary
AT = unreal.AssetToolsHelpers.get_asset_tools()
REPORT = {"downloaded": 0, "skipped": 0, "download_errors": [], "imported": 0,
          "instances": 0, "slots_changed": 0, "meshes_saved": 0, "nanite_off": [], "unmapped": []}


# ---------------------------------------------------------------- 1. download
def download_all(task):
    ctx = ssl.create_default_context()
    for tid in TEXSETS:
        d = os.path.join(SRC_DIR, tid)
        os.makedirs(d, exist_ok=True)
        for key, suffix in MAPS.items():
            task.enter_progress_frame(1, "Downloading %s %s" % (tid, suffix))
            fn = "%s_%s_%s.jpg" % (tid, suffix, RES)
            dst = os.path.join(d, fn)
            if os.path.exists(dst) and os.path.getsize(dst) > 10000:
                REPORT["skipped"] += 1
                continue
            url = "https://dl.polyhaven.org/file/ph-assets/Textures/jpg/%s/%s/%s" % (RES, tid, fn)
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "Neelam-UE-Importer/1.0"})
                with urllib.request.urlopen(req, timeout=120, context=ctx) as r, open(dst + ".part", "wb") as f:
                    f.write(r.read())
                os.replace(dst + ".part", dst)
                REPORT["downloaded"] += 1
            except Exception as e:
                REPORT["download_errors"].append("%s: %s" % (fn, e))
                unreal.log_warning("Download failed %s: %s" % (url, e))


# ---------------------------------------------------------------- 2. import textures
def tex_asset(tid, key):
    name = "T_%s_%s" % ("".join(p.capitalize() for p in tid.split("_")), key)
    return "%s/%s" % (TEX_ROOT, tid), name


def import_all(task):
    tasks = []
    for tid in TEXSETS:
        for key, suffix in MAPS.items():
            task.enter_progress_frame(1, "Importing %s %s" % (tid, key))
            folder, name = tex_asset(tid, key)
            src = os.path.join(SRC_DIR, tid, "%s_%s_%s.jpg" % (tid, suffix, RES))
            if EAL.does_asset_exist(folder + "/" + name) or not os.path.exists(src):
                continue
            t = unreal.AssetImportTask()
            t.filename = src; t.destination_path = folder; t.destination_name = name
            t.automated = True; t.replace_existing = True; t.save = False
            tasks.append((t, key))
    if tasks:
        AT.import_asset_tasks([t for t, _ in tasks])
    for t, key in tasks:
        tex = EAL.load_asset(t.destination_path + "/" + t.destination_name)
        if not tex:
            continue
        tex.set_editor_property("lod_group", unreal.TextureGroup.TEXTUREGROUP_WORLD)
        if key == "N":
            tex.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_NORMALMAP)
            tex.set_editor_property("srgb", False)
            tex.set_editor_property("flip_green_channel", True)       # Poly Haven nor_gl = OpenGL
            tex.set_editor_property("lod_group", unreal.TextureGroup.TEXTUREGROUP_WORLD_NORMAL_MAP)
        elif key in ("R", "AO"):
            tex.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_MASKS)
            tex.set_editor_property("srgb", False)
        EAL.save_loaded_asset(tex)
        REPORT["imported"] += 1


def load_tex(tid, key):
    folder, name = tex_asset(tid, key)
    return EAL.load_asset(folder + "/" + name)


# ---------------------------------------------------------------- 3. master materials
def sampler_for(tex):
    cs = tex.get_editor_property("compression_settings"); srgb = tex.get_editor_property("srgb")
    C, S = unreal.TextureCompressionSettings, unreal.MaterialSamplerType
    if cs == C.TC_NORMALMAP: return S.SAMPLERTYPE_NORMAL
    if cs == C.TC_MASKS: return S.SAMPLERTYPE_MASKS
    if cs == C.TC_GRAYSCALE: return S.SAMPLERTYPE_GRAYSCALE if srgb else S.SAMPLERTYPE_LINEAR_GRAYSCALE
    if cs == C.TC_ALPHA: return S.SAMPLERTYPE_ALPHA
    return S.SAMPLERTYPE_COLOR if srgb else S.SAMPLERTYPE_LINEAR_COLOR


def get_or_create_material(name):
    path = MASTER + "/" + name
    if EAL.does_asset_exist(path):
        mat = EAL.load_asset(path)
        MEL.delete_all_material_expressions(mat)
    else:
        mat = AT.create_asset(name, MASTER, unreal.Material, unreal.MaterialFactoryNew())
    return mat


class G:
    def __init__(self, mat): self.m = mat
    def n(self, cls, x, y, **props):
        e = MEL.create_material_expression(self.m, cls, x, y)
        for k, v in props.items(): e.set_editor_property(k, v)
        return e
    def c(self, a, ao, b, bi): MEL.connect_material_expressions(a, ao, b, bi)
    def out(self, a, ao, prop): MEL.connect_material_property(a, ao, prop)
    def scalar(self, name, v, x, y, grp="Surface"):
        return self.n(unreal.MaterialExpressionScalarParameter, x, y, parameter_name=name, default_value=v, group=grp)
    def vector(self, name, col, x, y, grp="Surface"):
        return self.n(unreal.MaterialExpressionVectorParameter, x, y, parameter_name=name,
                      default_value=unreal.LinearColor(*col, 1.0), group=grp)
    def texp(self, name, tex, x, y, grp="Textures"):
        return self.n(unreal.MaterialExpressionTextureSampleParameter2D, x, y, parameter_name=name,
                      texture=tex, sampler_type=sampler_for(tex), group=grp)


def build_surface_master():
    mat = get_or_create_material("M_Neelam_Surface")
    g = G(mat); P = unreal.MaterialProperty
    Lerp, Mul = unreal.MaterialExpressionLinearInterpolate, unreal.MaterialExpressionMultiply
    dD, dN, dR, dA = (load_tex("concrete", k) for k in ("D", "N", "R", "AO"))

    uvc = g.n(unreal.MaterialExpressionTextureCoordinate, -2200, 0)
    til = g.scalar("Tiling", 1.0, -2200, 120)
    asp = g.scalar("TilingAspectY", 1.0, -2200, 220)
    tv = g.n(unreal.MaterialExpressionAppendVector, -2100, 160, ); g.c(til, "", tv, "A")
    tyy = g.n(Mul, -2150, 260); g.c(til, "", tyy, "A"); g.c(asp, "", tyy, "B"); g.c(tyy, "", tv, "B")
    uv = g.n(Mul, -2000, 40); g.c(uvc, "", uv, "A"); g.c(tv, "", uv, "B")

    # base colour: texture -> luminance-preserving design tint -> macro variation
    tD = g.texp("BaseColor", dD, -1700, -400); g.c(uv, "", tD, "UVs")
    tAvg = g.texp("BaseColor", dD, -1700, -150)                      # same parameter, lowest mip = average colour
    tAvg.set_editor_property("mip_value_mode", unreal.TextureMipValueMode.TMVM_MIP_LEVEL)
    tAvg.set_editor_property("const_mip_value", 12)
    g.c(uv, "", tAvg, "UVs")
    lw = g.n(unreal.MaterialExpressionConstant3Vector, -1500, -250, constant=unreal.LinearColor(0.2126, 0.7152, 0.0722, 1))
    lum = g.n(unreal.MaterialExpressionDotProduct, -1300, -400); g.c(tD, "RGB", lum, "A"); g.c(lw, "", lum, "B")
    alum = g.n(unreal.MaterialExpressionDotProduct, -1300, -200); g.c(tAvg, "RGB", alum, "A"); g.c(lw, "", alum, "B")
    amax = g.n(unreal.MaterialExpressionMax, -1150, -200, const_b=0.02); g.c(alum, "", amax, "A")
    ratio0 = g.n(unreal.MaterialExpressionDivide, -1000, -350); g.c(lum, "", ratio0, "A"); g.c(amax, "", ratio0, "B")
    dcon = g.scalar("DetailContrast", 1.0, -1000, -250)
    ratio = g.n(Lerp, -900, -350, const_a=1.0); g.c(ratio0, "", ratio, "B"); g.c(dcon, "", ratio, "Alpha")
    tint = g.vector("Tint", (0.8, 0.8, 0.8), -1000, -550)
    tinted = g.n(Mul, -800, -450); g.c(tint, "", tinted, "A"); g.c(ratio, "", tinted, "B")
    tamt = g.scalar("TintAmount", 0.5, -800, -300)
    base = g.n(Lerp, -600, -450); g.c(tD, "RGB", base, "A"); g.c(tinted, "", base, "B"); g.c(tamt, "", base, "Alpha")

    macro_tex = EAL.load_asset(MACRO_TEX)
    col = base
    if macro_tex:
        wp = g.n(unreal.MaterialExpressionWorldPosition, -1700, 150)
        # (X+Y, Z) projection: varies on walls AND floors (XY-only made vertical streaks on the towers)
        wx = g.n(unreal.MaterialExpressionComponentMask, -1550, 100, r=True, g=False, b=False, a=False); g.c(wp, "", wx, "")
        wy = g.n(unreal.MaterialExpressionComponentMask, -1550, 180, r=False, g=True, b=False, a=False); g.c(wp, "", wy, "")
        wz = g.n(unreal.MaterialExpressionComponentMask, -1550, 260, r=False, g=False, b=True, a=False); g.c(wp, "", wz, "")
        wxy_ = g.n(unreal.MaterialExpressionAdd, -1400, 140); g.c(wx, "", wxy_, "A"); g.c(wy, "", wxy_, "B")
        wxy = g.n(unreal.MaterialExpressionAppendVector, -1300, 180); g.c(wxy_, "", wxy, "A"); g.c(wz, "", wxy, "B")
        wuv = g.n(Mul, -1200, 150, const_b=0.00005); g.c(wxy, "", wuv, "A")          # one repeat per 200 m
        mt = g.n(unreal.MaterialExpressionTextureSample, -1100, 150, texture=macro_tex, sampler_type=sampler_for(macro_tex))
        g.c(wuv, "", mt, "UVs")
        mv = g.n(Lerp, -850, 150, const_a=0.9, const_b=1.06); g.c(mt, "R", mv, "Alpha")
        ms = g.scalar("MacroVariation", 0.5, -850, 300)
        mf = g.n(Lerp, -650, 200, const_a=1.0); g.c(mv, "", mf, "B"); g.c(ms, "", mf, "Alpha")
        col = g.n(Mul, -400, -350); g.c(base, "", col, "A"); g.c(mf, "", col, "B")
    g.out(col, "", P.MP_BASE_COLOR)

    # roughness: design value with texture detail, or pure texture roughness
    tR = g.texp("Roughness", dR, -1700, 450); g.c(uv, "", tR, "UVs")
    rc = g.n(unreal.MaterialExpressionSubtract, -1450, 450, const_b=0.5); g.c(tR, "R", rc, "A")
    rv = g.scalar("RoughnessDetail", 0.35, -1450, 580)
    rd = g.n(Mul, -1250, 480); g.c(rc, "", rd, "A"); g.c(rv, "", rd, "B")
    rb = g.scalar("Roughness", 0.7, -1250, 620)
    r1 = g.n(unreal.MaterialExpressionAdd, -1050, 500); g.c(rb, "", r1, "A"); g.c(rd, "", r1, "B")
    ut = g.scalar("UseTextureRoughness", 0.0, -1050, 650)
    r2 = g.n(Lerp, -850, 500); g.c(r1, "", r2, "A"); g.c(tR, "R", r2, "B"); g.c(ut, "", r2, "Alpha")
    rs = g.n(unreal.MaterialExpressionSaturate, -650, 500); g.c(r2, "", rs, "")
    g.out(rs, "", P.MP_ROUGHNESS)

    met = g.scalar("Metallic", 0.0, -650, 380); g.out(met, "", P.MP_METALLIC)

    tN = g.texp("Normal", dN, -1700, 800); g.c(uv, "", tN, "UVs")
    flat = g.n(unreal.MaterialExpressionConstant3Vector, -1450, 750, constant=unreal.LinearColor(0, 0, 1, 1))
    ns = g.scalar("NormalStrength", 1.0, -1450, 950)
    nl = g.n(Lerp, -1150, 800); g.c(flat, "", nl, "A"); g.c(tN, "RGB", nl, "B"); g.c(ns, "", nl, "Alpha")
    g.out(nl, "", P.MP_NORMAL)

    tA = g.texp("AmbientOcclusion", dA, -1700, 1150); g.c(uv, "", tA, "UVs")
    aos = g.scalar("AOStrength", 1.0, -1450, 1300)
    al = g.n(Lerp, -1150, 1150, const_a=1.0); g.c(tA, "R", al, "B"); g.c(aos, "", al, "Alpha")
    g.out(al, "", P.MP_AMBIENT_OCCLUSION)

    MEL.layout_material_expressions(mat); MEL.recompile_material(mat); EAL.save_loaded_asset(mat)
    return mat


def build_glass_master():
    mat = get_or_create_material("M_Neelam_Glass")
    mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
    mat.set_editor_property("two_sided", True)
    mat.set_editor_property("translucency_lighting_mode", unreal.TranslucencyLightingMode.TLM_SURFACE_PER_PIXEL_LIGHTING)
    g = G(mat); P = unreal.MaterialProperty
    g.out(g.vector("Tint", (0.3, 0.38, 0.42), -800, -200), "", P.MP_BASE_COLOR)
    g.out(g.scalar("Metallic", 0.0, -800, 0), "", P.MP_METALLIC)
    g.out(g.scalar("Roughness", 0.05, -800, 100), "", P.MP_ROUGHNESS)
    g.out(g.scalar("Specular", 0.5, -800, 200), "", P.MP_SPECULAR)
    op = g.scalar("Opacity", 0.5, -800, 320)
    fr = g.n(unreal.MaterialExpressionFresnel, -800, 450, exponent=4.0, base_reflect_fraction=0.04)
    fl = g.n(unreal.MaterialExpressionLinearInterpolate, -500, 380, const_b=1.0)
    g.c(op, "", fl, "A"); g.c(fr, "", fl, "Alpha")                  # more opaque/reflective at grazing angles
    g.out(fl, "", P.MP_OPACITY)
    MEL.recompile_material(mat); EAL.save_loaded_asset(mat)
    return mat


def build_emissive_master():
    mat = get_or_create_material("M_Neelam_Emissive")
    g = G(mat); P = unreal.MaterialProperty
    colr = g.vector("Color", (1.0, 0.82, 0.55), -800, -100)
    inten = g.scalar("Intensity", 16.0, -800, 100)
    em = g.n(unreal.MaterialExpressionMultiply, -500, 0); g.c(colr, "", em, "A"); g.c(inten, "", em, "B")
    g.out(colr, "", P.MP_BASE_COLOR); g.out(em, "", P.MP_EMISSIVE_COLOR)
    g.out(g.scalar("Roughness", 0.4, -500, 200), "", P.MP_ROUGHNESS)
    MEL.recompile_material(mat); EAL.save_loaded_asset(mat)
    return mat


# ---------------------------------------------------------------- 4. instances
def get_or_create_mi(name, parent):
    path = INST + "/" + name
    mi = EAL.load_asset(path) if EAL.does_asset_exist(path) else \
        AT.create_asset(name, INST, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    MEL.set_material_instance_parent(mi, parent)
    return mi


def build_instances(masters):
    surf, glass, emis = masters
    out = {}
    S, V, T = (MEL.set_material_instance_scalar_parameter_value,
               MEL.set_material_instance_vector_parameter_value,
               MEL.set_material_instance_texture_parameter_value)
    for mname, spec in M.items():
        kind = spec[0]
        mi_name = "MI_" + mname[2:]
        if kind == "S":
            _, colr, rough, metal, tile, tid, tamt, usetex, nstr = spec
            mi = get_or_create_mi(mi_name, surf)
            for key, pname in (("D", "BaseColor"), ("N", "Normal"), ("R", "Roughness"), ("AO", "AmbientOcclusion")):
                tx = load_tex(tid, key)
                if tx: T(mi, pname, tx)
            S(mi, "Tiling", tile / TEXSETS[tid])          # UV0: 1 unit = <tile> m; texture covers TEXSETS[tid] m
            V(mi, "Tint", unreal.LinearColor(*colr, 1.0))
            S(mi, "TintAmount", tamt)
            S(mi, "Roughness", rough); S(mi, "UseTextureRoughness", float(usetex))
            S(mi, "RoughnessDetail", 0.25 if metal > 0.5 else 0.35)
            S(mi, "Metallic", metal); S(mi, "NormalStrength", nstr)
            S(mi, "MacroVariation", MACRO.get(mname, 0.25 if metal > 0.5 else (0.2 if tamt >= 1 else 0.45)))
            S(mi, "DetailContrast", DETAIL.get(mname, 0.15 if metal > 0.5 else (0.35 if tamt >= 1 else 1.0)))
        elif kind == "G":
            _, colr, rough, metal, alpha = spec
            mi = get_or_create_mi(mi_name, glass)
            V(mi, "Tint", unreal.LinearColor(*colr, 1.0))
            S(mi, "Roughness", rough); S(mi, "Metallic", metal); S(mi, "Opacity", alpha)
            S(mi, "Specular", 0.7 if "Glass" in mname or "Water" in mname else 0.3)
        else:
            _, colr, inten = spec
            mi = get_or_create_mi(mi_name, emis)
            V(mi, "Color", unreal.LinearColor(*colr, 1.0)); S(mi, "Intensity", inten)
        EAL.save_loaded_asset(mi)
        out[mname] = mi
        REPORT["instances"] += 1
    return out


# ---------------------------------------------------------------- 5. assign to meshes
def assign(instances, task):
    paths = [p for p in EAL.list_assets(ROOT + "/Meshes", recursive=True, include_folder=False)]
    for p in paths:
        task.enter_progress_frame(1, "Assigning materials")
        sm = EAL.load_asset(p)
        if not isinstance(sm, unreal.StaticMesh):
            continue
        changed, translucent = False, False
        for i, slot in enumerate(sm.get_editor_property("static_materials")):
            cur = slot.get_editor_property("material_interface")
            cname = cur.get_name() if cur else str(slot.get_editor_property("material_slot_name"))
            base = ("M_" + cname[3:]) if cname.startswith("MI_") else cname
            if RESTORE:
                new = EAL.load_asset(OLD_MATS + "/" + base) if cname.startswith("MI_") else None
            else:
                new = instances.get(base)
                if new is None and not cname.startswith("MI_"):
                    REPORT["unmapped"].append("%s: %s" % (sm.get_name(), cname))
            if new and new != cur:
                sm.set_material(i, new); changed = True; REPORT["slots_changed"] += 1
            if not RESTORE and M.get(base, ("S",))[0] == "G":
                translucent = True
        if translucent:                                   # Nanite can't render translucent sections
            ns = sm.get_editor_property("nanite_settings")
            if ns.enabled:
                ns.enabled = False; sm.set_editor_property("nanite_settings", ns); changed = True
                REPORT["nanite_off"].append(sm.get_name())
        if changed:
            EAL.save_loaded_asset(sm); REPORT["meshes_saved"] += 1


def main():
    t0 = time.time()
    n_mesh = len(EAL.list_assets(ROOT + "/Meshes", recursive=True, include_folder=False))
    total = len(TEXSETS) * len(MAPS) * 2 + n_mesh + 5
    with unreal.ScopedSlowTask(total, "Neelam: realistic materials") as task:
        task.make_dialog(True)
        if not RESTORE:
            download_all(task)
            import_all(task)
            task.enter_progress_frame(1, "Building master materials")
            masters = (build_surface_master(), build_glass_master(), build_emissive_master())
            task.enter_progress_frame(1, "Creating material instances")
            inst = build_instances(masters)
        else:
            inst = {}
        if APPLY_TO_MESHES or RESTORE:
            assign(inst, task)
    REPORT["seconds"] = round(time.time() - t0, 1)
    out = os.path.join(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_saved_dir()), "Neelam")
    os.makedirs(out, exist_ok=True)
    json.dump(REPORT, open(os.path.join(out, "materials_report.json"), "w"), indent=1)
    unreal.log("Neelam materials: downloaded %(downloaded)d, imported %(imported)d, instances %(instances)d, "
               "slots %(slots_changed)d, errors %(download_errors)s" % REPORT)


main()
if RUN_REVIEW:
    _cap = os.path.join(PROJECT, "Scripts", "Neelam", "Capture_Review_Shots.py")
    exec(compile(open(_cap).read(), _cap, "exec"), {"__name__": "__main__", "__file__": _cap})
