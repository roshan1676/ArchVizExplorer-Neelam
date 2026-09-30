"""Post-process material that paints each pixel's WORLD position along one axis (for depth-exact massing heights):
v = dot(WorldPos - Origin, Axis) / Scale + 0.5  ->  R = v, G = frac(v * 256)  (16-bit fixed point in two 8-bit channels).
Blendable location: replacing the tonemapper (values written unmodified). /Game/Neelam/Massing/M_Neelam_PosPP."""
import unreal
mel = unreal.MaterialEditingLibrary; EAL = unreal.EditorAssetLibrary
path = "/Game/Neelam/Massing/M_Neelam_PosPP"
if EAL.does_asset_exist(path): EAL.delete_asset(path)
m = unreal.AssetToolsHelpers.get_asset_tools().create_asset("M_Neelam_PosPP", "/Game/Neelam/Massing", unreal.Material, unreal.MaterialFactoryNew())
m.set_editor_property("material_domain", unreal.MaterialDomain.MD_POST_PROCESS)
m.set_editor_property("blendable_location", unreal.BlendableLocation.BL_REPLACING_TONEMAPPER)
E = lambda cls, x, y: mel.create_material_expression(m, cls, x, y)
wp = E(unreal.MaterialExpressionWorldPosition, -900, 0)
org = E(unreal.MaterialExpressionVectorParameter, -900, 150); org.set_editor_property("parameter_name", "Origin")
ax = E(unreal.MaterialExpressionVectorParameter, -900, 300); ax.set_editor_property("parameter_name", "Axis"); ax.set_editor_property("default_value", unreal.LinearColor(0, 0, 1, 0))
sc = E(unreal.MaterialExpressionScalarParameter, -600, 400); sc.set_editor_property("parameter_name", "Scale"); sc.set_editor_property("default_value", 80000.0)
mo = E(unreal.MaterialExpressionComponentMask, -700, 150); mo.set_editor_property("r", True); mo.set_editor_property("g", True); mo.set_editor_property("b", True); mo.set_editor_property("a", False)
ma = E(unreal.MaterialExpressionComponentMask, -700, 300); ma.set_editor_property("r", True); ma.set_editor_property("g", True); ma.set_editor_property("b", True); ma.set_editor_property("a", False)
mel.connect_material_expressions(org, "", mo, ""); mel.connect_material_expressions(ax, "", ma, "")
sub = E(unreal.MaterialExpressionSubtract, -550, 50); mel.connect_material_expressions(wp, "", sub, "A"); mel.connect_material_expressions(mo, "", sub, "B")
dot = E(unreal.MaterialExpressionDotProduct, -400, 100); mel.connect_material_expressions(sub, "", dot, "A"); mel.connect_material_expressions(ma, "", dot, "B")
div = E(unreal.MaterialExpressionDivide, -250, 150); mel.connect_material_expressions(dot, "", div, "A"); mel.connect_material_expressions(sc, "", div, "B")
add = E(unreal.MaterialExpressionAdd, -120, 150); add.set_editor_property("const_b", 0.5); mel.connect_material_expressions(div, "", add, "A")
sat = E(unreal.MaterialExpressionSaturate, 0, 150); mel.connect_material_expressions(add, "", sat, "")
mul = E(unreal.MaterialExpressionMultiply, 0, 300); mul.set_editor_property("const_b", 256.0); mel.connect_material_expressions(sat, "", mul, "A")
fr = E(unreal.MaterialExpressionFrac, 120, 300); mel.connect_material_expressions(mul, "", fr, "")
# R = coarse: floor(v*256)/256 so R and G never disagree at the wrap
fl = E(unreal.MaterialExpressionFloor, 120, 150); mel.connect_material_expressions(mul, "", fl, "")
d2 = E(unreal.MaterialExpressionDivide, 240, 150); d2.set_editor_property("const_b", 255.0); mel.connect_material_expressions(fl, "", d2, "A")
ap = E(unreal.MaterialExpressionAppendVector, 360, 200); mel.connect_material_expressions(d2, "", ap, "A"); mel.connect_material_expressions(fr, "", ap, "B")
ap2 = E(unreal.MaterialExpressionAppendVector, 480, 200); mel.connect_material_expressions(ap, "", ap2, "A")
z0 = E(unreal.MaterialExpressionConstant, 360, 320); mel.connect_material_expressions(z0, "", ap2, "B")
mel.connect_material_property(ap2, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
mel.recompile_material(m); EAL.save_asset(path)
result = path
