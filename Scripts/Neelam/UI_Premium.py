"""NEELAM premium redesign of the template UI (run step by step via NeelamBridge). Re-runnable."""
import unreal, importlib, sys
import UI_Theme as T
importlib.reload(T)
from UI_Theme import *

WB = "/Game/ArchVizExplorer/Blueprints/Widgets/"
TABS = [  # sizebox, button, icon image, label, icon texture, text
    ("SizeBox_0", "Button_Home", "Image_3", "TextBlock_48", "T_UI_Icon_Home", "HOME", "HorizontalBox_0"),
    ("SizeBox_1", "Button_Gallery", "Image_4", "TextBlock_1", "T_UI_Icon_Gallery", "GALLERY", "HorizontalBox_2"),
    ("SizeBox_11", "Button_Surroundings", "Image_1", "TextBlock_3", "T_UI_Icon_Surroundings", "SURROUNDINGS", "HorizontalBox_43"),
    ("SizeBox_3", "Button_Amenities", "Image_0", "TextBlock_2", "T_UI_Icon_Amenities", "AMENITIES", "HorizontalBox_42"),
    ("SizeBox_4_FV_0", "Button_UnitSearch_FV_0", "Image_2_FV_1", "TextBlock_0_FV_0", "T_UI_Icon_FloorView", "FLOOR VIEW", "HorizontalBox_1_FV_0"),
]
HIDDEN = ["Image_6", "Image_7", "Image_8", "Image_9", "Image_10", "Image_10_FV_0", "Image_5", "SizeBox_4"]   # separators + template Unit Search
TAB_W, TAB_H, PILL_H = 168, 44, 58

def step_taskbar():
    mm = unreal.load_asset(WB + "BP_MasterMenu_Widget")
    r = {}
    n_tabs = len(TABS)
    pill_w = n_tabs * (TAB_W + 4) + 48 + 28
    canvas(W(mm, "Taskbar"), (0.5, 1, 0.5, 1), (0, -22, pill_w, PILL_H), (0.5, 1), z=1)
    blur(W(mm, "BackgroundBlur_3"), PILL_H / 2)
    canvas(W(mm, "BackgroundBlur_3"), (0, 0, 1, 1), (0, 0, 0, 0))
    glass_border(W(mm, "Border_1"), PILL_H / 2, GLASS_DEEP)
    canvas(W(mm, "Border_1"), (0, 0, 1, 1), (0, 0, 0, 0))
    canvas(W(mm, "HorizontalBox_3"), (0, 0, 1, 1), (10, 7, 10, 7))
    for n in HIDDEN:
        w = W(mm, n)
        if w: w.set_editor_property("visibility", VIS.COLLAPSED)
    sel = button_style(no_brush(), brush(ROW_HOVER, TAB_H / 2), brush(GOLD_SOFT, TAB_H / 2, ((GOLD[0], GOLD[1], GOLD[2], 0.75), 1.0)))
    for sb, bt, im, tx, icon, label, hbn in TABS:
        s = W(mm, sb); s.set_width_override(TAB_W); s.set_height_override(TAB_H)
        box(s, pad=M(2, 0, 2, 0), v="V_ALIGN_CENTER")
        b = W(mm, bt); b.set_editor_property("widget_style", sel)
        b.set_editor_property("background_color", LC((1, 1, 1, 1)))
        i = W(mm, im); i.set_editor_property("brush", image_brush(tex(icon), (21, 21)))
        box(i, pad=M(0, 0, 10, 0), fill=0, v="V_ALIGN_CENTER")
        t = W(mm, tx); style_text(t, label, 10.5, "Medium", WHITE, spacing=140)
        box(t, fill=0, v="V_ALIGN_CENTER")
        t.set_editor_property("justification", unreal.TextJustify.LEFT)
        hs = W(mm, hbn).get_editor_property("slot")
        if hasattr(hs, "set_horizontal_alignment"): hs.set_horizontal_alignment(unreal.HorizontalAlignment.H_ALIGN_CENTER); hs.set_vertical_alignment(unreal.VerticalAlignment.V_ALIGN_CENTER)
    # settings button -> round icon button at the right end of the pill
    st = W(mm, "Button_Settings")
    st.set_editor_property("widget_style", button_style(no_brush(), brush(ROW_HOVER, 22), brush(GOLD_SOFT, 22), M(12, 10, 12, 10), 22))
    box(st, pad=M(12, 0, 0, 0), v="V_ALIGN_CENTER")
    lg = W(mm, "Logo"); lg.set_editor_property("brush", image_brush(tex("T_UI_Icon_Settings"), (18, 18), DIM))
    # class defaults used by Update_TaskbarButton_Style
    cdo = unreal.get_default_object(mm.generated_class())
    try:
        cdo.set_editor_property("ButtonStyle_TaskBar", sel); r["style_var"] = "ok"
    except Exception as e: r["style_var"] = str(e)
    try:
        cdo.set_editor_property("Button_Text_Opacity_Unchecked", 0.62); r["opacity_var"] = "ok"
    except Exception as e: r["opacity_var"] = str(e)
    # bottom menu area sits above the floating pill
    canvas(W(mm, "WidgetSwitcher_01"), (0, 0, 1, 1), (40, 12, 40, 100))
    canvas(W(mm, "CanvasPanel_2"), (0, 0.64, 1, 1), (0, 0, 0, 0))
    b4 = W(mm, "Border_4")
    b4.set_editor_property("background", image_brush(tex("T_UI_ScrimV"), (8, 256), (1, 1, 1, 0.85)))
    b4.set_editor_property("brush_color", LC((1, 1, 1, 1)))
    # brand wordmark bottom-left
    add(mm, "CanvasPanel_0", unreal.VerticalBox, "Brand")
    canvas(W(mm, "Brand"), (0, 1, 0, 1), (44, -26, 0, 0), (0, 1), auto=True, z=2)
    W(mm, "Brand").set_editor_property("visibility", VIS.HIT_TEST_INVISIBLE)
    t1 = add(mm, "Brand", unreal.TextBlock, "Brand_Name"); style_text(t1, "NEELAM", 30, serif=True, spacing=520, color=WHITE)
    t2 = add(mm, "Brand", unreal.TextBlock, "Brand_Line"); style_text(t2, "WIND TUNNEL  ·  MULUND EAST", 8.5, "SemiBold", GOLD, spacing=360)
    box(t2, pad=M(3, 0, 0, 0))
    # time + compass placement
    canvas(W(mm, "BP_Time_Widget"), (0.5, 0, 0.5, 0), (0, 22, 0, 0), (0.5, 0), auto=True, z=1)
    canvas(W(mm, "BP_Compass"), (1, 0, 1, 0), (-32, 22, 76, 76), (1, 0), z=1)
    canvas(W(mm, "Popup_Settings_SizeBox"), (0.5, 1, 0.5, 1), (pill_w / 2 - 60, -92, 200, 124), (0.5, 1), z=3)
    r["compile"] = L.compile_and_report(mm)
    EAL.save_asset(mm.get_path_name())
    return r

def _divider(wbp, parent, name):
    d = add(wbp, parent, unreal.Image, name)
    d.set_editor_property("brush", brush(LINE, 0, size=(1, 30), draw="IMAGE"))
    box(d, pad=M(18, 0, 18, 0), v="V_ALIGN_CENTER")
    return d

def step_time():
    tw = unreal.load_asset(WB + "BP_Time_Widget")
    r = {}
    if not isinstance(unreal.get_default_object(tw.generated_class()), unreal.NeelamTimeWidget):
        r["reparent"] = L.reparent_blueprint(tw, unreal.NeelamTimeWidget)
    add(tw, "VerticalBox_0", unreal.Overlay, "TimePill", 0)
    bl = add(tw, "TimePill", unreal.BackgroundBlur, "TimeBlur"); blur(bl, 28); box(bl, h="H_ALIGN_FILL", v="V_ALIGN_FILL")
    gl = add(tw, "TimePill", unreal.Border, "TimeGlass"); glass_border(gl, 28, GLASS_DEEP, M(22, 8, 20, 8)); box(gl, h="H_ALIGN_FILL", v="V_ALIGN_FILL")
    add(tw, "TimeGlass", unreal.HorizontalBox, "TimeRow")
    ic = add(tw, "TimeRow", unreal.Image, "Image_TimeIcon", -1, True)
    ic.set_editor_property("brush", image_brush(tex("T_UI_Icon_Sun"), (22, 22), GOLD)); box(ic, pad=M(0, 0, 14, 0), v="V_ALIGN_CENTER")
    add(tw, "TimeRow", unreal.VerticalBox, "TimeTexts"); box(W(tw, "TimeTexts"), v="V_ALIGN_CENTER")
    L.move_widget(tw, "TextBlock_Time", "TimeTexts", 0)
    style_text(W(tw, "TextBlock_Time"), None, 22, "Light", WHITE, spacing=60)
    pr = add(tw, "TimeTexts", unreal.TextBlock, "Text_Period", -1, True); style_text(pr, "EVENING", 7.5, "SemiBold", GOLD, spacing=320)
    box(pr, pad=M(1, -2, 0, 0))
    _divider(tw, "TimeRow", "TimeDiv1")
    sb = add(tw, "TimeRow", unreal.SizeBox, "SliderBox"); sb.set_width_override(300); box(sb, v="V_ALIGN_CENTER")
    L.move_widget(tw, "Slider_01", "SliderBox", 0)
    s = W(tw, "Slider_01")
    ss = s.get_editor_property("widget_style")
    ss.set_editor_property("normal_bar_image", brush((1, 1, 1, 1), 1, size=(8, 2)))
    ss.set_editor_property("hovered_bar_image", brush((1, 1, 1, 1), 1, size=(8, 2)))
    ss.set_editor_property("disabled_bar_image", brush((1, 1, 1, 1), 1, size=(8, 2)))
    ss.set_editor_property("normal_thumb_image", image_brush(tex("T_UI_Dot"), (14, 14), (1, 1, 1, 1)))
    ss.set_editor_property("hovered_thumb_image", image_brush(tex("T_UI_Dot"), (17, 17), (1, 1, 1, 1)))
    ss.set_editor_property("disabled_thumb_image", image_brush(tex("T_UI_Dot"), (14, 14), (1, 1, 1, 1)))
    try: ss.set_editor_property("bar_thickness", 2.0)
    except Exception: pass
    s.set_editor_property("widget_style", ss)
    s.set_editor_property("slider_bar_color", LC((1, 1, 1, 0.28)))
    s.set_editor_property("slider_handle_color", LC(GOLD))
    _divider(tw, "TimeRow", "TimeDiv2")
    add(tw, "TimeRow", unreal.HorizontalBox, "Presets"); box(W(tw, "Presets"), v="V_ALIGN_CENTER")
    for key, label in (("Morning", "MORNING"), ("Noon", "NOON"), ("Sunset", "SUNSET"), ("Night", "NIGHT")):
        b = add(tw, "Presets", unreal.Button, "Btn_" + key, -1, True)
        b.set_editor_property("widget_style", button_style(no_brush(), brush(ROW_HOVER, 14), brush(GOLD_SOFT, 14), M(10, 6, 10, 6), 14))
        box(b, pad=M(1, 0, 1, 0), v="V_ALIGN_CENTER")
        t = add(tw, "Btn_" + key, unreal.TextBlock, "Txt_" + key, -1, True); style_text(t, label, 8.5, "SemiBold", (1, 1, 1, 0.55), spacing=220)
    old = W(tw, "Border_182")
    if old: L.remove_widget(tw, "Border_182")
    r["compile"] = L.compile_and_report(tw)
    cdo = unreal.get_default_object(tw.generated_class())
    cdo.set_editor_property("icon_day", tex("T_UI_Icon_Sun")); cdo.set_editor_property("icon_twilight", tex("T_UI_Icon_Sunrise")); cdo.set_editor_property("icon_night", tex("T_UI_Icon_Moon"))
    r["compile2"] = L.compile_and_report(tw)
    EAL.save_asset(tw.get_path_name())
    import json
    r["tree"] = [w["name"] + "<" + w["parent"] for w in json.loads(L.describe_widget_tree(tw))]
    return r

def step_compass():
    cp = unreal.load_asset(WB + "BP_Compass_Widget")
    canvas(W(cp, "Overlay_2"), (0, 0, 0, 0), (0, 0, 76, 76))
    bg = W(cp, "Image_BG"); bg.set_editor_property("brush", brush((1, 1, 1, 1), 38, ((1, 1, 1, 0.12), 1.0), size=(76, 76)))
    bg.set_editor_property("color_and_opacity", LC(GLASS_DEEP))
    i1 = W(cp, "Image_1"); i1.set_editor_property("visibility", VIS.COLLAPSED)
    bc = W(cp, "Border_Circle")
    bc.set_editor_property("background", image_brush(tex("T_UI_CompassRing"), (76, 76), (1, 1, 1, 1.0)))
    bc.set_editor_property("brush_color", LC((1, 1, 1, 1))); bc.set_editor_property("padding", M(0))
    ar = W(cp, "Image_Arrow"); ar.set_editor_property("brush", image_brush(tex("T_UI_CompassNeedle"), (76, 76), GOLD))
    try:
        bs = ar.get_editor_property("slot"); bs.set_horizontal_alignment(unreal.HorizontalAlignment.H_ALIGN_FILL); bs.set_vertical_alignment(unreal.VerticalAlignment.V_ALIGN_FILL)
    except Exception: pass
    style_text(W(cp, "TextBlock_Direction"), None, 13, "SemiBold", WHITE, spacing=120, just="CENTER")
    for n in ("Image_BG", "Border_Circle", "TextBlock_Direction"):
        box(W(cp, n), h="H_ALIGN_FILL" if n != "TextBlock_Direction" else "H_ALIGN_CENTER", v="V_ALIGN_FILL" if n != "TextBlock_Direction" else "V_ALIGN_CENTER")
    r = L.compile_and_report(cp); EAL.save_asset(cp.get_path_name())
    return r

def _section_title(wbp, title_name, spacer_name, text):
    style_text(W(wbp, title_name), text, 44, serif=True, color=WHITE, spacing=20, shadow=True)
    sp = W(wbp, spacer_name)
    sp.set_editor_property("brush", brush(GOLD, 0, size=(64, 1.5), draw="IMAGE"))
    box(sp, pad=M(3, 2, 0, 16), h="H_ALIGN_LEFT")

def step_lists():
    r = {}
    el = unreal.load_asset(WB + "BP_EntryList_Widget")
    blur(W(el, "BackgroundBlur_0"), R_PANEL, 18)
    g = add(el, "BackgroundBlur_0", unreal.Border, "CardGlass")
    glass_border(g, R_PANEL, GLASS)
    try: W(el, "BackgroundBlur_0").set_editor_property("padding", M(0))
    except Exception: pass
    gs = g.get_editor_property("slot")
    for f in ("set_horizontal_alignment", "set_vertical_alignment"):
        if hasattr(gs, f): getattr(gs, f)(unreal.HorizontalAlignment.H_ALIGN_FILL if "horiz" in f else unreal.VerticalAlignment.V_ALIGN_FILL)
    b0 = W(el, "Border_0"); b0.set_editor_property("background", no_brush()); b0.set_editor_property("brush_color", LC((1, 1, 1, 0))); b0.set_editor_property("padding", M(16, 13, 12, 9))
    b1 = W(el, "Border_1"); b1.set_editor_property("background", brush((1, 1, 1, 1), 4)); b1.set_editor_property("padding", M(4))
    box(b1, pad=M(0, 0, 10, 0), v="V_ALIGN_CENTER")
    style_text(W(el, "TextBlock_Title"), None, 10.5, "SemiBold", WHITE, spacing=200)
    box(W(el, "TextBlock_Title"), fill=1.0, v="V_ALIGN_CENTER")
    tb = W(el, "ToggleButton_01")
    tb.set_editor_property("widget_style", button_style(image_brush(tex("T_UI_ThumbRing"), (15, 15), GOLD), image_brush(tex("T_UI_ThumbRing"), (15, 15), (1, 1, 1, 0.9)),
                                                           image_brush(tex("T_UI_ThumbRing"), (15, 15), (1, 1, 1, 0.3)), M(0)))
    tb.set_editor_property("tool_tip_text", "Show / hide on the map")
    b2 = W(el, "Border_2"); b2.set_editor_property("background", no_brush()); b2.set_editor_property("brush_color", LC((1, 1, 1, 0))); b2.set_editor_property("padding", M(6, 0, 6, 10))
    sc = W(el, "ScrollBox")
    bs = sc.get_editor_property("widget_bar_style")
    for k in ("normal_thumb_image", "hovered_thumb_image", "dragged_thumb_image"):
        bs.set_editor_property(k, brush((1, 1, 1, 0.22 if k == "normal_thumb_image" else 0.4), 2))
    for k in ("horizontal_background_image", "vertical_background_image", "vertical_top_slot_image", "vertical_bottom_slot_image", "horizontal_top_slot_image", "horizontal_bottom_slot_image"):
        try: bs.set_editor_property(k, no_brush())
        except Exception: pass
    sc.set_editor_property("widget_bar_style", bs)
    t = unreal.Vector2D(3, 3)
    try: sc.set_editor_property("scrollbar_thickness", t)
    except Exception:
        try:
            v = unreal.DeprecateSlateVector2D(); v.import_text("(X=3,Y=3)"); sc.set_editor_property("scrollbar_thickness", v)
        except Exception as e: r["sb"] = str(e)
    sc.set_editor_property("scrollbar_padding", M(2, 0, 0, 0))
    sc.set_editor_property("scroll_bar_visibility", VIS.COLLAPSED)
    r["entrylist"] = L.compile_and_report(el); EAL.save_asset(el.get_path_name())
    en = unreal.load_asset(WB + "BP_Entry_Widget")
    b = W(en, "Button_01")
    b.set_editor_property("widget_style", button_style(no_brush(), brush(ROW_HOVER, 9), brush(GOLD_SOFT, 9), M(10, 6, 10, 6), 9))
    style_text(W(en, "Text_Name"), None, 12, "Regular", (1, 1, 1, 0.86), spacing=0)
    W(en, "Text_Name").set_editor_property("auto_wrap_text", False)
    W(en, "Text_Name").set_editor_property("wrap_text_at", 230.0)
    W(en, "Border_01").set_editor_property("visibility", VIS.COLLAPSED)
    r["entry"] = L.compile_and_report(en); EAL.save_asset(en.get_path_name())
    for n, title in (("BP_Surroundings_Widget", "Surroundings"), ("BP_Amenities_Widget", "Amenities")):
        wb = unreal.load_asset(WB + n)
        _section_title(wb, "Text_Title", "Image_Spacer_01", title)
        if n == "BP_Surroundings_Widget":
            ug = W(wb, "UniformGridPanel_0"); ug.set_editor_property("slot_padding", M(0, 0, 12, 0))
            ug.set_editor_property("clipping", unreal.WidgetClipping.CLIP_TO_BOUNDS)
        else:
            for sb in ("SizeBox_2", "SizeBox_0", "SizeBox_1"):
                box(W(wb, sb), pad=M(0, 0, 14, 0))
        r[n] = L.compile_and_report(wb); EAL.save_asset(wb.get_path_name())
    return r

def step_richtext():
    dt = unreal.load_asset("/Game/ArchVizExplorer/Fonts/RichText_DataTable")
    js = dt.export_to_json_string()
    import json
    rows = json.loads(js)
    for row in rows:
        ts = row["TextStyle"]
        ts = ts.replace("/Script/Engine.Font'/Game/ArchVizExplorer/Fonts/FIRASANSCONDENSED_Font.FiraSansCondensed_Font'", "/Script/Engine.Font'/Game/Neelam/UI/Fonts/F_Neelam_Sans.F_Neelam_Sans'")
        import re
        if row["Name"] == "Default":
            ts = re.sub(r'TypefaceFontName="[^"]*"', 'TypefaceFontName="Regular"', ts)
            ts = re.sub(r"Size=[0-9.]+,LetterSpacing=-?\d+", "Size=12.500000,LetterSpacing=10", ts, count=1)
            ts = re.sub(r"ColorAndOpacity=\(SpecifiedColor=\(R=[0-9.]+,G=[0-9.]+,B=[0-9.]+,A=[0-9.]+\)", "ColorAndOpacity=(SpecifiedColor=(R=0.860000,G=0.880000,B=0.920000,A=0.780000)", ts, count=1)
        else:
            ts = re.sub(r'TypefaceFontName="[^"]*"', 'TypefaceFontName="SemiBold"', ts)
            ts = re.sub(r"Size=[0-9.]+,LetterSpacing=-?\d+", "Size=10.500000,LetterSpacing=220", ts, count=1)
            ts = re.sub(r"ColorAndOpacity=\(SpecifiedColor=\(R=[0-9.]+,G=[0-9.]+,B=[0-9.]+,A=[0-9.]+\)", "ColorAndOpacity=(SpecifiedColor=(R=0.578000,G=0.397000,B=0.144000,A=1.000000)", ts, count=1)
        row["TextStyle"] = ts
    ok = unreal.DataTableFunctionLibrary.fill_data_table_from_json_string(dt, json.dumps(rows))
    EAL.save_asset(dt.get_path_name())
    return ok

def _pill_button(btn, text_w, label=None):
    btn.set_editor_property("widget_style", button_style(brush((1, 1, 1, 0.0), 18, ((GOLD[0], GOLD[1], GOLD[2], 0.7), 1.0)),
                                                         brush(GOLD_SOFT, 18, (GOLD, 1.0)), brush((GOLD[0], GOLD[1], GOLD[2], 0.35), 18, (GOLD, 1.0)), M(16, 9, 16, 9), 18))
    style_text(text_w, label, 10, "SemiBold", WHITE, spacing=200, just="CENTER")

def step_info():
    w = unreal.load_asset(WB + "BP_Info_Widget")
    blur(W(w, "BackgroundBlur_0"), 14, 20)
    W(w, "BackgroundBlur_0").set_editor_property("padding", M(0))
    sh = W(w, "Border_Shadow"); sh.set_editor_property("brush_color", LC((0, 0, 0, 0.35)))
    sb = W(w, "SizeBox_5"); sb.set_width_override(360); sb.set_height_override(210)
    bt = W(w, "Border_Title"); glass_border(bt, 0, GLASS_DEEP, M(0), outline=False)
    W(w, "Border_3").set_editor_property("padding", M(0, 0, 0, 2))
    tt = W(w, "TextBlock_Title"); style_text(tt, None, 28, serif=True, color=WHITE, spacing=10)
    box(tt, pad=M(22, 14, 22, 8))
    b9 = W(w, "Border_9"); glass_border(b9, 0, GLASS_DEEP, M(22, 4, 22, 20), outline=False)
    for bn, tn in (("Border_MediaGallery", "Text_MediaButton"), ("Border_360", "Text_360"), ("Border_Level", "Text_Level")):
        bd = W(w, bn); bd.set_editor_property("background", no_brush()); bd.set_editor_property("brush_color", LC((1, 1, 1, 0))); bd.set_editor_property("padding", M(0, 10, 0, 0))
        _pill_button(W(w, bn.replace("Border_", "Button_")), W(w, tn))
    sp = W(w, "Image_Spacer"); sp.set_editor_property("brush", brush(LINE, 0, size=(8, 1), draw="IMAGE")); box(sp, pad=M(0, 16, 0, 10))
    style_text(W(w, "Text_Footer"), None, 10, "Regular", FAINT, spacing=40)
    r = L.compile_and_report(w); EAL.save_asset(w.get_path_name())
    return r

def _round_icon_button(btn, icon_img, icon, size=18, radius=22, pad=M(12)):
    btn.set_editor_property("widget_style", button_style(brush((0.008, 0.010, 0.016, 0.62), radius, ((1, 1, 1, 0.14), 1.0)),
                                                         brush((0.02, 0.02, 0.03, 0.8), radius, (GOLD, 1.0)), brush(GOLD_SOFT, radius, (GOLD, 1.0)), pad, radius))
    if icon_img: icon_img.set_editor_property("brush", image_brush(tex(icon), (size, size), WHITE))

def step_misc():
    r = {}
    # POI labels on the map (world-space widgets)
    w = unreal.load_asset(WB + "BP_3D_Widget")
    blur(W(w, "BackgroundBlur_2"), 18, 14)
    W(w, "Button_01").set_editor_property("widget_style", button_style(no_brush(), no_brush(), no_brush(), M(0)))
    ib = W(w, "Border_Icon_BG"); ib.set_editor_property("background", brush((1, 1, 1, 1), 16)); ib.set_editor_property("padding", M(7))
    b2 = W(w, "Border_2"); glass_border(b2, 16, GLASS_DEEP, M(12, 7, 16, 7)); box(b2, pad=M(-10, 0, 0, 0), v="V_ALIGN_CENTER")
    style_text(W(w, "Text_Name"), None, 12, "Medium", WHITE, spacing=20)
    r["3d"] = L.compile_and_report(w); EAL.save_asset(w.get_path_name())
    # gallery
    g = unreal.load_asset(WB + "BP_Gallery_Widget")
    blur(W(g, "BackgroundBlur_0"), 0, 28)
    bd = W(g, "Border"); bd.set_editor_property("background", no_brush()); bd.set_editor_property("brush_color", LC((0, 0, 0, 0))); bd.set_editor_property("padding", M(48, 36, 48, 12))
    style_text(W(g, "Text_MediaTitle"), None, 38, serif=True, color=WHITE, spacing=10, shadow=True)
    for bn, im in (("Button_Arrow_Left", "Img_ArrowLeft"), ("Button_Arrow_Right", "Img_ArrowRight"), ("Button_Exit", "Img_GalleryExit")):
        i = add(g, bn, unreal.Image, im)
        _round_icon_button(W(g, bn), i, "T_UI_Icon_Close" if bn == "Button_Exit" else "T_UI_Icon_Chevron", 18 if bn == "Button_Exit" else 24, 28, M(14))
        if bn == "Button_Arrow_Left": i.set_render_transform_angle(180.0)
    box(W(g, "Button_Exit"), pad=M(0, 116, 40, 0), h="H_ALIGN_RIGHT", v="V_ALIGN_TOP")
    b2 = W(g, "Border_2"); b2.set_editor_property("background", no_brush()); b2.set_editor_property("brush_color", LC((0, 0, 0, 0)))
    r["gallery"] = L.compile_and_report(g); EAL.save_asset(g.get_path_name())
    # master menu: settings popup + hide template notification
    mm = unreal.load_asset(WB + "BP_MasterMenu_Widget")
    blur(W(mm, "BackgroundBlur"), R_PANEL, BLUR)
    glass_border(W(mm, "Border"), R_PANEL, GLASS_DEEP)
    _round_icon_button(W(mm, "Button_Exit_Popup_Settings"), W(mm, "Image_Exit"), "T_UI_Icon_Close", 14, 16, M(8))
    eg = W(mm, "Button_Exit_Game")
    eg.set_editor_property("widget_style", button_style(brush((1, 1, 1, 0.04), 12), brush(ROW_HOVER, 12, (GOLD, 1.0)), brush(GOLD_SOFT, 12), M(16, 12, 16, 12), 12))
    style_text(W(mm, "Text_Exit_Game"), "EXIT EXPERIENCE", 10, "SemiBold", WHITE, spacing=220, just="CENTER")
    W(mm, "Border_01").set_editor_property("visibility", VIS.COLLAPSED)
    r["mm"] = L.compile_and_report(mm); EAL.save_asset(mm.get_path_name())
    # 360 menu (template panoramas)
    m3 = unreal.load_asset(WB + "BP_360Menu_Widget")
    _round_icon_button(W(m3, "Button_Close"), W(m3, "Image_1"), "T_UI_Icon_Close", 16, 24, M(14))
    r["360"] = L.compile_and_report(m3); EAL.save_asset(m3.get_path_name())
    return r
