"""'Upcoming project' marker where Towers A and B stood (30 Sep, client: A/B removed, amenity deck kept).
WBP_Neelam_UpcomingLabel (premium dark glass + gold, same theme as the UI) shown by BP_Neelam_UpcomingLabel's
WidgetComponent in SCREEN space -> always faces the camera, constant pixel size, floats above the AB amenity deck.
Re-run safe (rebuilds both assets, replaces the actor)."""
import sys, os, importlib
import unreal
sys.path.insert(0, os.path.join(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()), "Scripts", "Neelam"))
import UI_Theme as T; importlib.reload(T)
from UI_Theme import *
AT = unreal.AssetToolsHelpers.get_asset_tools()
DIR = "/Game/Neelam/UI/World"
WP, BP = DIR + "/WBP_Neelam_UpcomingLabel", DIR + "/BP_Neelam_UpcomingLabel"
LOC = unreal.Vector(-2350.0, -1700.0, 4250.0)      # between the old A / B footprints, ~5 m above the AB roof deck (3767.5)
# ---------------- widget
for p in (BP, WP):
    if EAL.does_asset_exist(p): EAL.delete_asset(p)
f = unreal.WidgetBlueprintFactory(); f.set_editor_property("parent_class", unreal.UserWidget)
wbp = AT.create_asset("WBP_Neelam_UpcomingLabel", DIR, unreal.WidgetBlueprint, f)
add(wbp, None, unreal.VerticalBox, "Root")
W(wbp, "Root").set_editor_property("visibility", VIS.HIT_TEST_INVISIBLE)
ov = add(wbp, "Root", unreal.Overlay, "Pill"); box(ov, h="H_ALIGN_CENTER")
bl = add(wbp, "Pill", unreal.BackgroundBlur, "PillBlur"); blur(bl, 16, 18); box(bl, h="H_ALIGN_FILL", v="V_ALIGN_FILL")
gl = add(wbp, "Pill", unreal.Border, "PillGlass"); glass_border(gl, 16, GLASS_DEEP, M(34, 16, 34, 16)); box(gl, h="H_ALIGN_FILL", v="V_ALIGN_FILL")
col = add(wbp, "PillGlass", unreal.VerticalBox, "Col")
t0 = add(wbp, "Col", unreal.TextBlock, "Kicker"); style_text(t0, "COMING SOON", 8, "SemiBold", GOLD, spacing=420, just="CENTER"); box(t0, h="H_ALIGN_CENTER")
t1 = add(wbp, "Col", unreal.TextBlock, "Title"); style_text(t1, "Upcoming Project", 26, serif=True, color=WHITE, spacing=40, just="CENTER"); box(t1, pad=M(0, 2, 0, 6), h="H_ALIGN_CENTER")
ln = add(wbp, "Col", unreal.Image, "Rule"); ln.set_editor_property("brush", brush(GOLD, 0, size=(56, 1), draw="IMAGE")); box(ln, pad=M(0, 0, 0, 7), h="H_ALIGN_CENTER")
t2 = add(wbp, "Col", unreal.TextBlock, "Sub"); style_text(t2, "TOWERS  A  &  B", 8, "Medium", DIM, spacing=360, just="CENTER"); box(t2, h="H_ALIGN_CENTER")
st = add(wbp, "Root", unreal.Image, "Stem"); st.set_editor_property("brush", brush((0.578, 0.397, 0.144, 0.85), 0, size=(1.5, 70), draw="IMAGE")); box(st, h="H_ALIGN_CENTER")
dot = add(wbp, "Root", unreal.Image, "Dot"); dot.set_editor_property("brush", brush(GOLD, 4, size=(8, 8))); box(dot, h="H_ALIGN_CENTER")
r = {"widget": L.compile_and_report(wbp)}
EAL.save_asset(WP)
# ---------------- actor blueprint with a screen-space WidgetComponent
bf = unreal.BlueprintFactory(); bf.set_editor_property("parent_class", unreal.Actor)
bp = AT.create_asset("BP_Neelam_UpcomingLabel", DIR, unreal.Blueprint, bf)
SDS = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
handles = SDS.k2_gather_subobject_data_for_blueprint(bp)
root = handles[0]
p = unreal.AddNewSubobjectParams(parent_handle=root, new_class=unreal.WidgetComponent, blueprint_context=bp)
h, fail = SDS.add_new_subobject(p)
SDS.rename_subobject(h, "Label")
wc = unreal.SubobjectDataBlueprintFunctionLibrary.get_object(unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h))
wc.set_editor_property("widget_class", wbp.generated_class())
wc.set_editor_property("space", unreal.WidgetSpace.SCREEN)
wc.set_editor_property("draw_at_desired_size", True)
wc.set_editor_property("pivot", unreal.Vector2D(0.5, 1.0))          # the stem's dot sits on the anchor point
wc.set_collision_profile_name("NoCollision")
unreal.BlueprintEditorLibrary.compile_blueprint(bp)
EAL.save_asset(BP)
# ---------------- place
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for a in EAS.get_all_level_actors():
    if a.get_actor_label() == "Neelam_UpcomingLabel_AB": EAS.destroy_actor(a)
a = EAS.spawn_actor_from_class(bp.generated_class(), LOC)
a.set_actor_label("Neelam_UpcomingLabel_AB"); a.set_folder_path("Neelam/WindTunnel/Upcoming")
unreal.EditorLevelLibrary.save_current_level()
r["actor"] = a.get_actor_label(); r["fail"] = str(fail)
result = r
