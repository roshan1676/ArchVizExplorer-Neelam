"""Which assets come out of which client .blend (read-only). Run in the live Blender:
    exec(open(r'.../kit_specs.py').read()); run('pool')     -> opens the source file, extracts its kits, returns sizes.
Never saves the source. Afterwards reopen SourceArt/AmenityDeck/amenity_deck.blend."""
import bpy
from mathutils import Vector

TOOLS = r'C:/Users/Admin/Documents/Unreal Projects/ArchVizExplorer-Neelam/SourceArt/AmenityDeck/tools'
SRC = r'C:/Users/Admin/Downloads/Blender Files/'
exec(open(TOOLS + '/extract_kit.py').read())


def near(anchor, radius, coll=None, keep=None):
    a = bpy.data.objects[anchor].matrix_world.translation
    pool = bpy.data.collections[coll].all_objects if coll else bpy.data.objects
    return [o.name for o in pool if o.type == 'MESH' and (Vector((o.matrix_world.translation.x - a.x, o.matrix_world.translation.y - a.y)).length < radius)
            and (keep is None or keep(o))]


def pool_kits():
    is00 = lambda o: any(m and m.name.startswith('00-') for m in o.data.materials)
    umb = ('Umbrella_Ribs', 'Umbrella_Base', 'Slider', 'Safety_Pin_With_Chain', 'Rib_Wire', 'Pulley_System', 'Pull_Rope',
           'Locking_Screw', 'Center_Pole', 'Canopy', 'Bolt_2', 'Bolt_1')
    return {
        'KIT_Lounger': near('Plane.061', 2.5, 'POOL', is00),
        'KIT_Umbrella': near('Canopy', 1.5, None, lambda o: o.name.split('.')[0] in umb),
        'KIT_GrassBig': ['garden02_017'], 'KIT_FlowerSpikes': ['garden02_012'], 'KIT_GroundFlower': ['garden02_013'],
        'KIT_BigLeaf': ['garden02_014'], 'KIT_SmallPlant': ['garden02_006'], 'KIT_Fern': ['garden02_002'],
        'KIT_LowShrub': ['garden02_001'], 'KIT_GrassTuft': ['garden02_009'], 'KIT_GrassCarpet': ['garden02_007'],
        'KIT_FlowerBush': ['Garden04plants_011'], 'KIT_Shrub01': ['flowebox01_031'], 'KIT_Shrub05': ['flowebox01_027'],
        'KIT_Shrub06': ['flowebox01_026'], 'KIT_Shrub04': ['flowebox01_021'],
        'KIT_PalmPot': near('Caraday Palm Large', 1.0, 'Caraday Palm Lrg Pot'),
        'KIT_PotBush': near('Plane.019', 1.5, 'Pot Bush'),
    }


def lawn_kits():
    return {
        'KIT_PathLight': ['Cuerpo', 'Luz'],                       # Bustan LED pillar light, 0.4 m
        'KIT_PostLight': ['Street Light.001'],                    # 3.6 m garden post lamp
        'KIT_GardenLight': near('LightScrews', 0.3, 'Garden Light Short'),
    }


FILES = {'pool': ('pool.blend', pool_kits), 'lawn': ('party lawn.blend', lawn_kits)}


def run(key, only=None):
    fn, specs = FILES[key]
    if not bpy.data.filepath.endswith(fn):
        bpy.ops.wm.open_mainfile(filepath=SRC + fn, load_ui=False)
    res = {}
    for kit, objs in specs().items():
        if only and kit not in only:
            continue
        try:
            res[kit] = extract(kit, objs)
        except Exception as e:
            res[kit] = 'ERROR ' + str(e)[:160]
    return res
