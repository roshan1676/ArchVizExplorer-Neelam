"""Builds the Floor View / flat-tour Widget Blueprints (runs inside UE via NeelamBridge). Re-runnable.
All widgets are normal UMG Blueprints - restyle them freely in the designer; C++ only needs the bound names."""
import unreal

L = unreal.NeelamToolsLibrary
EAL = unreal.EditorAssetLibrary
AT = unreal.AssetToolsHelpers.get_asset_tools()
UI = "/Game/Neelam/FloorView/UI"
FONT_PATH = "/Game/Neelam/UI/Fonts/F_Neelam_Sans"
SERIF_PATH = "/Game/Neelam/UI/Fonts/F_Neelam_Serif"
FACES = {}   # filled by _faces()

C_PANEL = (0.008, 0.010, 0.016, 0.62)     # dark glass (over a BackgroundBlur)
C_ROW = (1, 1, 1, 0.035)
C_HOVER = (1, 1, 1, 0.09)
C_SEL = (0.578, 0.397, 0.144, 0.30)      # champagne gold
C_TEXT = (1, 1, 1, 0.96)
C_DIM = (0.86, 0.88, 0.92, 0.62)
C_ACCENT = (0.578, 0.397, 0.144, 1)
C_GOLD = (0.578, 0.397, 0.144, 1)

def LC(c): return unreal.LinearColor(*c)
def SC(c): return unreal.SlateColor(specified_color=LC(c))
def V2(x, y): return unreal.Vector2D(x, y)
def M(l, t=None, r=None, b=None):
    if t is None: t = r = b = l
    return unreal.Margin(l, t, r, b)

def _faces():
    FACES.update({"all": ["Light", "Regular", "Medium", "SemiBold", "Bold"], "regular": "Regular", "bold": "SemiBold", "light": "Light", "medium": "Medium"})
    return FACES["all"]
    f = unreal.load_asset(FONT_PATH)
    names = []
    try:
        cf = f.get_editor_property("composite_font")
        for e in cf.get_editor_property("default_typeface").get_editor_property("fonts"):
            names.append(str(e.get_editor_property("name")))
    except Exception as ex:
        names = []
    if not names: names = ["Default", "Bold", "Medium"]   # FiraSansCondensed_Font typefaces
    FACES["all"] = names
    def pick(*cands):
        for c in cands:
            for n in names:
                if n.lower() == c.lower(): return n
        return names[0] if names else "Regular"
    FACES["regular"] = pick("Default", "Regular", "Book")
    FACES["bold"] = pick("Bold", "SemiBold", "Medium")
    FACES["light"] = pick("Light", "Default")
    return names

def brush(color=(1, 1, 1, 1), radius=0.0, outline=None, tex=None, size=None, draw="ROUNDED_BOX"):
    b = unreal.SlateBrush()
    b.set_editor_property("draw_as", getattr(unreal.SlateBrushDrawType, draw))
    b.set_editor_property("tint_color", SC(color))
    if tex: b.set_editor_property("resource_object", tex)
    if size:
        v = unreal.DeprecateSlateVector2D(); v.import_text("(X=%f,Y=%f)" % (size[0], size[1])); b.set_editor_property("image_size", v)
    if draw == "ROUNDED_BOX":
        o = unreal.SlateBrushOutlineSettings()
        o.set_editor_property("corner_radii", unreal.Vector4(radius, radius, radius, radius))
        o.set_editor_property("rounding_type", unreal.SlateBrushRoundingType.FIXED_RADIUS)
        if outline:
            o.set_editor_property("color", SC(outline[0])); o.set_editor_property("width", outline[1])
        else:
            o.set_editor_property("width", 0.0)
        b.set_editor_property("outline_settings", o)
    return b

def font(size, face="regular", spacing=0):
    fi = unreal.SlateFontInfo()
    serif = face == "serif"
    fi.set_editor_property("font_object", unreal.load_asset(SERIF_PATH if serif else FONT_PATH))
    fi.set_editor_property("typeface_font_name", "Regular" if serif else FACES.get(face, face))
    fi.set_editor_property("size", size)
    fi.set_editor_property("letter_spacing", spacing)
    return fi

class B:
    """tiny builder around NeelamToolsLibrary.add_widget"""
    def __init__(self, path, parent_cls):
        self.path = path
        if EAL.does_asset_exist(path):
            self.wbp = unreal.load_asset(path)
            import json
            tree = json.loads(L.describe_widget_tree(self.wbp))
            roots = [w["name"] for w in tree if not w["parent"]]
            for r in roots: L.remove_widget(self.wbp, r)
            if parent_cls: L.reparent_blueprint(self.wbp, parent_cls)
        else:
            f = unreal.WidgetBlueprintFactory(); f.set_editor_property("parent_class", parent_cls or unreal.UserWidget)
            folder, name = path.rsplit("/", 1)
            self.wbp = AT.create_asset(name, folder, unreal.WidgetBlueprint, f)
    def add(self, parent, cls, name, var=False):
        w = L.add_widget(self.wbp, parent or "None", cls, name, -1, var)
        if w is None: raise RuntimeError("add_widget failed: %s under %s in %s" % (name, parent, self.path))
        return w
    def text(self, parent, name, s, size, face="regular", color=C_TEXT, var=False, shadow=False, wrap=0, just=None, spacing=0):
        t = self.add(parent, unreal.TextBlock, name, var)
        t.set_editor_property("text", s)
        t.set_editor_property("font", font(size, face, spacing))
        t.set_editor_property("color_and_opacity", SC(color))
        if shadow:
            t.set_editor_property("shadow_offset", V2(1.5, 1.5)); t.set_editor_property("shadow_color_and_opacity", LC((0, 0, 0, 0.75)))
        if wrap:
            t.set_editor_property("auto_wrap_text", True)
        if just:
            t.set_editor_property("justification", getattr(unreal.TextJustify, just))
        t.set_editor_property("visibility", unreal.SlateVisibility.HIT_TEST_INVISIBLE)
        return t
    def border(self, parent, name, color=C_PANEL, radius=10, pad=12, var=False, outline=None):
        b = self.add(parent, unreal.Border, name, var)
        b.set_editor_property("background", brush((1, 1, 1, 1), radius, outline))
        b.set_editor_property("brush_color", LC(color))
        b.set_editor_property("padding", M(pad) if not isinstance(pad, unreal.Margin) else pad)
        return b
    def clear_button(self, parent, name, var=True):
        btn = self.add(parent, unreal.Button, name, var)
        st = unreal.ButtonStyle()
        for k in ("normal", "hovered", "pressed", "disabled"):
            st.set_editor_property(k, brush((1, 1, 1, 0), 0, draw="NO_DRAW_TYPE"))
        st.set_editor_property("normal_padding", M(0)); st.set_editor_property("pressed_padding", M(0))
        btn.set_editor_property("widget_style", st)
        return btn
    def pill_button(self, parent, name, var=True, radius=8):
        btn = self.add(parent, unreal.Button, name, var)
        st = unreal.ButtonStyle()
        st.set_editor_property("normal", brush((1, 1, 1, 0.0), radius, ((0.578, 0.397, 0.144, 0.75), 1.0)))
        st.set_editor_property("hovered", brush((0.578, 0.397, 0.144, 0.22), radius, ((0.578, 0.397, 0.144, 1.0), 1.0)))
        st.set_editor_property("pressed", brush((0.578, 0.397, 0.144, 0.4), radius, ((0.578, 0.397, 0.144, 1.0), 1.0)))
        st.set_editor_property("disabled", brush((0.02, 0.02, 0.02, 0.4), radius))
        st.set_editor_property("normal_padding", M(14, 8, 14, 8)); st.set_editor_property("pressed_padding", M(14, 9, 14, 7))
        btn.set_editor_property("widget_style", st)
        return btn
    def done(self, cdo_props=None):
        r = L.compile_and_report(self.wbp)
        if cdo_props:
            cdo = unreal.get_default_object(self.wbp.generated_class())
            for k, v in cdo_props.items(): cdo.set_editor_property(k, v)
            r = L.compile_and_report(self.wbp)
        EAL.save_asset(self.path)
        return r

def slot_box(w, pad=None, fill=None, h=None, v=None):
    s = w.get_editor_property("slot")
    if pad is not None: s.set_padding(pad if isinstance(pad, unreal.Margin) else M(pad))
    if fill is not None:
        cs = unreal.SlateChildSize(); cs.set_editor_property("value", fill if fill else 1.0)
        cs.set_editor_property("size_rule", unreal.SlateSizeRule.FILL if fill else unreal.SlateSizeRule.AUTOMATIC)
        s.set_size(cs)
    if h: s.set_horizontal_alignment(getattr(unreal.HorizontalAlignment, h))
    if v: s.set_vertical_alignment(getattr(unreal.VerticalAlignment, v))
    return s

def slot_canvas(w, anchors=(0, 0, 0, 0), offsets=(0, 0, 100, 30), align=(0, 0), auto=False, z=0):
    s = w.get_editor_property("slot")
    a = unreal.Anchors(); a.set_editor_property("minimum", V2(anchors[0], anchors[1])); a.set_editor_property("maximum", V2(anchors[2], anchors[3]))
    s.set_anchors(a); s.set_offsets(M(*offsets)); s.set_alignment(V2(*align)); s.set_auto_size(auto); s.set_z_order(z)
    return s

def item_colors(normal=C_ROW, hover=C_HOVER, sel=C_SEL):
    return {"normal_color": LC(normal), "hover_color": LC(hover), "selected_color": LC(sel)}

# ------------------------------------------------------------------ list items
def build_items():
    res = {}
    LI = unreal.NeelamListItem
    # tower tab
    b = B(UI + "/WBP_FV_TowerTab", LI)
    b.border(None, "Background", C_ROW, 8, M(0), var=True)
    btn = b.clear_button("Background", "MainButton")
    t = b.text("MainButton", "Label", "Tower A", 14, "bold", just="CENTER", var=True)
    slot_box(t, pad=M(12, 7, 12, 7), h="H_ALIGN_CENTER", v="V_ALIGN_CENTER")
    res["tab"] = b.done(item_colors())
    # floor row
    b = B(UI + "/WBP_FV_FloorRow", LI)
    b.border(None, "Background", C_ROW, 6, M(0), var=True)
    b.clear_button("Background", "MainButton")
    hb = b.add("MainButton", unreal.HorizontalBox, "Row")
    mk = b.border("Row", "Marker", C_ROW, 2, M(0), var=True)
    slot_box(mk, pad=M(0, 0, 10, 0), v="V_ALIGN_FILL")
    ms = b.add("Marker", unreal.SizeBox, "MarkerSize"); ms.set_width_override(4)
    vb = b.add("Row", unreal.VerticalBox, "Texts"); slot_box(vb, pad=M(0, 7, 0, 7), fill=1.0, v="V_ALIGN_CENTER")
    b.text("Texts", "Label", "Floor 20", 16, "bold", var=True)
    b.text("Texts", "Info", "2 units · 2 available", 12, "regular", C_DIM, var=True)
    bd = b.text("Row", "Badge", "2", 14, "bold", C_ACCENT, var=True)
    slot_box(bd, pad=M(8, 0, 12, 0), v="V_ALIGN_CENTER")
    res["floor"] = b.done(item_colors())
    # flat card
    b = B(UI + "/WBP_FV_FlatCard", LI)
    b.border(None, "Background", (0.03, 0.05, 0.09, 0.75), 10, M(10), var=True)
    b.clear_button("Background", "MainButton")
    hb = b.add("MainButton", unreal.HorizontalBox, "Card")
    tb = b.border("Card", "ThumbBg", (0.95, 0.96, 0.98, 1), 6, M(3))
    slot_box(tb, pad=M(0, 0, 12, 0), v="V_ALIGN_CENTER")
    ts = b.add("ThumbBg", unreal.SizeBox, "ThumbSize"); ts.set_width_override(78); ts.set_height_override(118)
    th = b.add("ThumbSize", unreal.Image, "Thumb", True)
    vb = b.add("Card", unreal.VerticalBox, "CardTexts"); slot_box(vb, fill=1.0, v="V_ALIGN_CENTER")
    b.text("CardTexts", "Label", "Flat C-2001", 18, "bold", var=True)
    b.text("CardTexts", "Info", "2 BHK", 15, "bold", C_ACCENT, var=True)
    b.text("CardTexts", "Extra", "RERA 652 sq.ft", 12, "regular", C_DIM, var=True, wrap=1)
    bdg = b.text("CardTexts", "Badge", "AVAILABLE", 11, "bold", (0.2, 0.9, 0.45, 1), var=True)
    slot_box(bdg, pad=M(0, 4, 0, 6))
    ab = b.pill_button("CardTexts", "ActionButton"); slot_box(ab, h="H_ALIGN_LEFT")
    b.text("ActionButton", "ActionText", "360° PANORAMA", 13, "bold")
    res["card"] = b.done(item_colors((0.03, 0.05, 0.09, 0.75), (0.05, 0.16, 0.38, 0.9), (0.07, 0.3, 0.7, 0.95)))
    # plan hotspot
    b = B(UI + "/WBP_FV_Hotspot", LI)
    b.border(None, "Background", (0.01, 0.02, 0.05, 0.82), 14, M(0), var=True)
    b.clear_button("Background", "MainButton")
    hb = b.add("MainButton", unreal.HorizontalBox, "Pill")
    mk = b.border("Pill", "Marker", C_ACCENT, 7, M(0), var=True); slot_box(mk, pad=M(8, 0, 6, 0), v="V_ALIGN_CENTER")
    ms = b.add("Marker", unreal.SizeBox, "Dot"); ms.set_width_override(12); ms.set_height_override(12)
    lb = b.text("Pill", "Label", "Living", 13, "bold", var=True); slot_box(lb, pad=M(0, 5, 10, 5), v="V_ALIGN_CENTER")
    res["hotspot"] = b.done({"normal_color": LC((0.01, 0.02, 0.05, 0.82)), "hover_color": LC((0.07, 0.25, 0.6, 0.95)), "selected_color": LC((0.1, 0.45, 1.0, 1.0))})
    # room bar button
    b = B(UI + "/WBP_FV_RoomButton", LI)
    b.border(None, "Background", (0.02, 0.03, 0.06, 0.7), 8, M(0), var=True)
    b.clear_button("Background", "MainButton")
    t = b.text("MainButton", "Label", "Living", 14, "bold", var=True)
    slot_box(t, pad=M(16, 9, 16, 9))
    res["room"] = b.done({"normal_color": LC((0.02, 0.03, 0.06, 0.7)), "hover_color": LC((0.07, 0.25, 0.6, 0.9)), "selected_color": LC((0.1, 0.45, 1.0, 1.0))})
    return res

# ------------------------------------------------------------------ floor view overlay
def build_floor_view():
    b = B(UI + "/WBP_Neelam_FloorView", unreal.NeelamFloorViewWidget)
    b.add(None, unreal.CanvasPanel, "Root")
    # left list
    lp = b.border("Root", "LeftPanel", C_PANEL, 14, M(16))
    slot_canvas(lp, (0, 0, 0, 1), (24, 96, 350, 150))
    vb = b.add("LeftPanel", unreal.VerticalBox, "LeftVBox")
    b.text("LeftVBox", "Header", "FLOOR VIEW", 24, "bold")
    lt = b.text("LeftVBox", "ListTitle", "Tower A · 58 floors", 13, "regular", C_DIM, var=True); slot_box(lt, pad=M(0, 0, 0, 10))
    tabs = b.add("LeftVBox", unreal.WrapBox, "TowerTabs", True); slot_box(tabs, pad=M(0, 0, 0, 12))
    tabs.set_editor_property("inner_slot_padding", V2(6, 6))
    sc = b.add("LeftVBox", unreal.ScrollBox, "FloorList", True); slot_box(sc, fill=1.0)
    tip = b.text("LeftVBox", "Tip", "Tip: click a floor on the tower or pick it here", 12, "regular", C_DIM, wrap=1)
    slot_box(tip, pad=M(0, 10, 0, 0))
    # hover hint
    hh = b.text("Root", "HoverHint", "Tower C · Floor 20", 22, "bold", var=True, shadow=True)
    slot_canvas(hh, (0.5, 0, 0.5, 0), (0, 100, 0, 0), (0.5, 0), auto=True)
    hh.set_editor_property("visibility", unreal.SlateVisibility.COLLAPSED)
    # detail panel
    dp = b.border("Root", "DetailPanel", C_PANEL, 14, M(16), var=True)
    slot_canvas(dp, (1, 0, 1, 0), (-24, 96, 0, 0), (1, 0), auto=True)
    ds = b.add("DetailPanel", unreal.SizeBox, "DetailSize")
    ds.set_width_override(400); ds.set_max_desired_height(760)
    dv = b.add("DetailSize", unreal.VerticalBox, "DetailVBox")
    hb = b.add("DetailVBox", unreal.HorizontalBox, "DetailHeader")
    t = b.text("DetailHeader", "DetailTitle", "Tower C · Floor 20", 22, "bold", var=True); slot_box(t, fill=1.0, v="V_ALIGN_CENTER")
    cb = b.pill_button("DetailHeader", "CloseDetailButton"); slot_box(cb, v="V_ALIGN_CENTER")
    b.text("CloseDetailButton", "CloseX", "CLOSE", 12, "bold")
    st = b.text("DetailVBox", "DetailSubtitle", "2 apartments on this floor", 13, "regular", C_DIM, var=True); slot_box(st, pad=M(0, 2, 0, 12))
    et = b.text("DetailVBox", "EmptyText", "Demo flats are on Tower C · Floor 20 (2BHK + 3BHK).", 13, "regular", C_DIM, var=True, wrap=1)
    et.set_editor_property("visibility", unreal.SlateVisibility.COLLAPSED)
    fs = b.add("DetailVBox", unreal.ScrollBox, "FlatScroll"); slot_box(fs, fill=1.0)
    fl = b.add("FlatScroll", unreal.VerticalBox, "FlatList", True)
    return b.done({
        "tower_tab_class": unreal.load_asset(UI + "/WBP_FV_TowerTab").generated_class(),
        "floor_row_class": unreal.load_asset(UI + "/WBP_FV_FloorRow").generated_class(),
        "flat_card_class": unreal.load_asset(UI + "/WBP_FV_FlatCard").generated_class()})

# ------------------------------------------------------------------ tour overlay
def build_tour():
    b = B(UI + "/WBP_Neelam_Tour", unreal.NeelamTourWidget)
    b.add(None, unreal.CanvasPanel, "Root")
    pp = b.border("Root", "PlanPanel", C_PANEL, 14, M(16))
    slot_canvas(pp, (0, 0.5, 0, 0.5), (24, 0, 0, 0), (0, 0.5), auto=True)
    pv = b.add("PlanPanel", unreal.VerticalBox, "PlanVBox")
    b.text("PlanVBox", "FlatTitle", "Flat C-2001", 24, "bold", var=True)
    fi = b.text("PlanVBox", "FlatInfo", "2 BHK · Tower C · Floor 20", 13, "regular", C_DIM, var=True); slot_box(fi, pad=M(0, 0, 0, 12))
    pbg = b.border("PlanVBox", "PlanBg", (0.96, 0.97, 0.99, 1), 8, M(0))
    pb = b.add("PlanBg", unreal.SizeBox, "PlanBox", True)
    pb.set_width_override(330); pb.set_height_override(620)
    ov = b.add("PlanBox", unreal.Overlay, "PlanOverlay")
    im = b.add("PlanOverlay", unreal.Image, "PlanImage", True); slot_box(im, h="H_ALIGN_FILL", v="V_ALIGN_FILL")
    hl = b.add("PlanOverlay", unreal.CanvasPanel, "HotspotLayer", True); slot_box(hl, h="H_ALIGN_FILL", v="V_ALIGN_FILL")
    hint = b.text("PlanVBox", "PlanHint", "Click a room on the plan to step inside", 12, "regular", C_DIM); slot_box(hint, pad=M(0, 10, 0, 0))
    rt = b.text("Root", "RoomTitle", "Living", 34, "bold", var=True, shadow=True)
    slot_canvas(rt, (0.5, 0, 0.5, 0), (0, 26, 0, 0), (0.5, 0), auto=True)
    rbb = b.border("Root", "RoomBarBg", (0.006, 0.009, 0.018, 0.6), 12, M(8))
    slot_canvas(rbb, (0.5, 1, 0.5, 1), (0, -24, 0, 0), (0.5, 1), auto=True)
    rb = b.add("RoomBarBg", unreal.WrapBox, "RoomBar", True); rb.set_editor_property("inner_slot_padding", V2(6, 6))
    ex = b.pill_button("Root", "ExitButton"); slot_canvas(ex, (1, 0, 1, 0), (-24, 24, 0, 0), (1, 0), auto=True)
    b.text("ExitButton", "ExitText", "EXIT TOUR", 15, "bold")
    lk = b.text("Root", "LookHint", "Drag to look around", 12, "regular", (1, 1, 1, 0.7), shadow=True)
    slot_canvas(lk, (1, 1, 1, 1), (-24, -30, 0, 0), (1, 1), auto=True)
    return b.done({
        "hotspot_class": unreal.load_asset(UI + "/WBP_FV_Hotspot").generated_class(),
        "room_button_class": unreal.load_asset(UI + "/WBP_FV_RoomButton").generated_class(),
        "plan_max_height": 620.0, "plan_max_width": 440.0})

def build_tab():
    b = B(UI + "/WBP_FV_Tab", unreal.NeelamFloorViewTab)
    s = b.add(None, unreal.SizeBox, "Empty")
    s.set_editor_property("visibility", unreal.SlateVisibility.SELF_HIT_TEST_INVISIBLE)
    return b.done()

def build_all():
    _faces()
    r = {"faces": FACES}
    r["items"] = build_items()
    r["floor_view"] = build_floor_view()
    r["tour"] = build_tour()
    r["tab"] = build_tab()
    return r


# ====================================================================== premium versions (override the first drafts above)
def _blur_panel(b, parent, name, anchors, offsets, align=(0, 0), auto=False, var=False, radius=18, pad=M(18)):
    """BackgroundBlur (canvas slot) > Border glass. Returns (blur, border)."""
    bl = b.add(parent, unreal.BackgroundBlur, name, var)
    bl.set_editor_property("blur_strength", 22.0)
    try: bl.set_editor_property("corner_radius", unreal.Vector4(radius, radius, radius, radius))
    except Exception: pass
    bl.set_editor_property("padding", M(0))
    slot_canvas(bl, anchors, offsets, align, auto)
    g = b.border(name, name + "_Glass", C_PANEL, radius, pad, outline=((1, 1, 1, 0.10), 1.0))
    s = g.get_editor_property("slot"); s.set_horizontal_alignment(unreal.HorizontalAlignment.H_ALIGN_FILL); s.set_vertical_alignment(unreal.VerticalAlignment.V_ALIGN_FILL)
    return bl, g

def _caps(t):
    for prop in ("text_transform_policy", "text_transformation_policy"):
        try: t.set_editor_property(prop, unreal.TextTransformPolicy.TO_UPPER); return
        except Exception: pass

def build_items():
    res = {}
    LI = unreal.NeelamListItem
    b = B(UI + "/WBP_FV_TowerTab", LI)
    b.border(None, "Background", C_ROW, 16, M(0), var=True)
    b.clear_button("Background", "MainButton")
    t = b.text("MainButton", "Label", "Tower A", 10, "bold", just="CENTER", var=True, spacing=160); _caps(t)
    slot_box(t, pad=M(14, 8, 14, 8), h="H_ALIGN_CENTER", v="V_ALIGN_CENTER")
    res["tab"] = b.done(item_colors(C_ROW, C_HOVER, (0.578, 0.397, 0.144, 0.55)))
    b = B(UI + "/WBP_FV_FloorRow", LI)
    b.border(None, "Background", C_ROW, 10, M(0), var=True)
    b.clear_button("Background", "MainButton")
    rw = b.add("MainButton", unreal.HorizontalBox, "Row"); slot_box(rw, h="H_ALIGN_FILL", v="V_ALIGN_FILL")
    mk = b.border("Row", "Marker", C_ROW, 2, M(0), var=True); slot_box(mk, pad=M(0, 10, 12, 10), v="V_ALIGN_FILL")
    ms = b.add("Marker", unreal.SizeBox, "MarkerSize"); ms.set_width_override(3)
    b.add("Row", unreal.VerticalBox, "Texts"); slot_box(b.wbp and b.add("Row", unreal.VerticalBox, "Texts") if False else unreal.find_object(None, b.wbp.get_path_name() + ":WidgetTree.Texts"), pad=M(0, 8, 0, 8), fill=1.0, v="V_ALIGN_CENTER")
    b.text("Texts", "Label", "Floor 20", 15, "medium", var=True)
    b.text("Texts", "Info", "2 units · 2 available", 10.5, "regular", C_DIM, var=True)
    bd = b.text("Row", "Badge", "2", 12, "bold", C_GOLD, var=True); slot_box(bd, pad=M(8, 0, 14, 0), v="V_ALIGN_CENTER")
    res["floor"] = b.done(item_colors(C_ROW, C_HOVER, C_SEL))
    b = B(UI + "/WBP_FV_FlatCard", LI)
    b.border(None, "Background", (1, 1, 1, 0.04), 14, M(12), var=True)
    b.clear_button("Background", "MainButton")
    cw = b.add("MainButton", unreal.HorizontalBox, "Card"); slot_box(cw, h="H_ALIGN_FILL", v="V_ALIGN_FILL")
    tb = b.border("Card", "ThumbBg", (0.97, 0.97, 0.98, 1), 8, M(4)); slot_box(tb, pad=M(0, 0, 14, 0), v="V_ALIGN_CENTER")
    ts = b.add("ThumbBg", unreal.SizeBox, "ThumbSize"); ts.set_width_override(80); ts.set_height_override(120)
    b.add("ThumbSize", unreal.Image, "Thumb", True)
    vb = b.add("Card", unreal.VerticalBox, "CardTexts"); slot_box(vb, fill=1.0, v="V_ALIGN_CENTER")
    b.text("CardTexts", "Label", "Flat C-2001", 24, "serif", var=True)
    b.text("CardTexts", "Info", "2 BHK", 10.5, "bold", C_GOLD, var=True, spacing=200)
    b.text("CardTexts", "Extra", "RERA 652 sq.ft", 11, "regular", C_DIM, var=True, wrap=1)
    bdg = b.text("CardTexts", "Badge", "AVAILABLE", 8.5, "bold", (0.2, 0.9, 0.45, 1), var=True, spacing=220); slot_box(bdg, pad=M(0, 6, 0, 8))
    ab = b.pill_button("CardTexts", "ActionButton", radius=16); slot_box(ab, h="H_ALIGN_LEFT")
    b.text("ActionButton", "ActionText", "360°  PANORAMA", 9.5, "bold", spacing=200)
    res["card"] = b.done(item_colors((1, 1, 1, 0.04), (1, 1, 1, 0.08), (0.578, 0.397, 0.144, 0.22)))
    b = B(UI + "/WBP_FV_Hotspot", LI)
    b.border(None, "Background", (0.008, 0.010, 0.016, 0.85), 14, M(0), var=True)
    b.clear_button("Background", "MainButton")
    pw = b.add("MainButton", unreal.HorizontalBox, "Pill"); slot_box(pw, h="H_ALIGN_FILL", v="V_ALIGN_FILL")
    mk = b.border("Pill", "GoldDot", C_GOLD, 5, M(0)); slot_box(mk, pad=M(9, 0, 7, 0), v="V_ALIGN_CENTER")
    ms = b.add("GoldDot", unreal.SizeBox, "Dot"); ms.set_width_override(9); ms.set_height_override(9)
    lb = b.text("Pill", "Label", "Living", 10, "bold", var=True, spacing=120); _caps(lb); slot_box(lb, pad=M(0, 6, 11, 6), v="V_ALIGN_CENTER")
    res["hotspot"] = b.done({"normal_color": LC((0.008, 0.010, 0.016, 0.85)), "hover_color": LC((0.12, 0.09, 0.05, 0.95)), "selected_color": LC((0.578, 0.397, 0.144, 1.0))})
    b = B(UI + "/WBP_FV_RoomButton", LI)
    b.border(None, "Background", (1, 1, 1, 0.0), 18, M(0), var=True)
    b.clear_button("Background", "MainButton")
    t = b.text("MainButton", "Label", "Living", 10, "bold", var=True, spacing=180); _caps(t)
    slot_box(t, pad=M(16, 9, 16, 9))
    res["room"] = b.done({"normal_color": LC((1, 1, 1, 0.0)), "hover_color": LC((1, 1, 1, 0.09)), "selected_color": LC((0.578, 0.397, 0.144, 0.55))})
    return res

def build_floor_view():
    b = B(UI + "/WBP_Neelam_FloorView", unreal.NeelamFloorViewWidget)
    b.add(None, unreal.CanvasPanel, "Root")
    bl, lp = _blur_panel(b, "Root", "LeftPanel", (0, 0, 0, 1), (40, 128, 360, 132), pad=M(22, 22, 20, 18))
    b.add("LeftPanel_Glass", unreal.VerticalBox, "LeftVBox")
    b.text("LeftVBox", "Overline", "RESIDENCES", 8.5, "bold", C_GOLD, spacing=320)
    b.text("LeftVBox", "Header", "Floor View", 38, "serif")
    lt = b.text("LeftVBox", "ListTitle", "Tower A · 58 floors", 10.5, "regular", C_DIM, var=True); slot_box(lt, pad=M(0, 0, 0, 14))
    tabs = b.add("LeftVBox", unreal.WrapBox, "TowerTabs", True); slot_box(tabs, pad=M(0, 0, 0, 14)); tabs.set_editor_property("inner_slot_padding", V2(6, 6))
    sep = b.add("LeftVBox", unreal.Image, "Sep1"); sep.set_editor_property("brush", brush((1, 1, 1, 0.10), 0, size=(8, 1), draw="IMAGE")); slot_box(sep, pad=M(0, 0, 0, 8))
    sc = b.add("LeftVBox", unreal.ScrollBox, "FloorList", True); slot_box(sc, fill=1.0)
    sc.set_editor_property("scroll_bar_visibility", unreal.SlateVisibility.COLLAPSED)
    tip = b.text("LeftVBox", "Tip", "Select a floor on the tower or from the list", 10, "regular", (1, 1, 1, 0.4), wrap=1); slot_box(tip, pad=M(0, 12, 0, 0))
    hh = b.text("Root", "HoverHint", "Tower C · Floor 20", 30, "serif", var=True, shadow=True)
    slot_canvas(hh, (0.5, 0, 0.5, 0), (0, 124, 0, 0), (0.5, 0), auto=True)
    hh.set_editor_property("visibility", unreal.SlateVisibility.COLLAPSED)
    dp, dg = _blur_panel(b, "Root", "DetailPanel", (1, 0, 1, 0), (-40, 128, 0, 0), (1, 0), auto=True, var=True, pad=M(22, 20, 22, 20))
    ds = b.add("DetailPanel_Glass", unreal.SizeBox, "DetailSize"); ds.set_width_override(420); ds.set_max_desired_height(740)
    b.add("DetailSize", unreal.VerticalBox, "DetailVBox")
    b.add("DetailVBox", unreal.HorizontalBox, "DetailHeader")
    b.add("DetailHeader", unreal.VerticalBox, "DetailHeadTexts"); slot_box(unreal.find_object(None, b.wbp.get_path_name() + ":WidgetTree.DetailHeadTexts"), fill=1.0, v="V_ALIGN_CENTER")
    b.text("DetailHeadTexts", "DetailOverline", "SELECTED FLOOR", 8.5, "bold", C_GOLD, spacing=320)
    b.text("DetailHeadTexts", "DetailTitle", "Tower C · Floor 20", 30, "serif", var=True)
    cb = b.pill_button("DetailHeader", "CloseDetailButton", radius=16); slot_box(cb, v="V_ALIGN_TOP")
    b.text("CloseDetailButton", "CloseX", "CLOSE", 9, "bold", spacing=200)
    st = b.text("DetailVBox", "DetailSubtitle", "2 apartments on this floor", 11, "regular", C_DIM, var=True); slot_box(st, pad=M(0, 2, 0, 16))
    et = b.text("DetailVBox", "EmptyText", "Demo flats are on Tower C · Floor 20 (2BHK + 3BHK).", 11, "regular", C_DIM, var=True, wrap=1)
    et.set_editor_property("visibility", unreal.SlateVisibility.COLLAPSED)
    fs = b.add("DetailVBox", unreal.ScrollBox, "FlatScroll"); slot_box(fs, fill=1.0); fs.set_editor_property("scroll_bar_visibility", unreal.SlateVisibility.COLLAPSED)
    fl = b.add("FlatScroll", unreal.VerticalBox, "FlatList", True)
    return b.done({
        "tower_tab_class": unreal.load_asset(UI + "/WBP_FV_TowerTab").generated_class(),
        "floor_row_class": unreal.load_asset(UI + "/WBP_FV_FloorRow").generated_class(),
        "flat_card_class": unreal.load_asset(UI + "/WBP_FV_FlatCard").generated_class()})

def build_tour():
    b = B(UI + "/WBP_Neelam_Tour", unreal.NeelamTourWidget)
    b.add(None, unreal.CanvasPanel, "Root")
    bl, pp = _blur_panel(b, "Root", "PlanPanel", (0, 0.5, 0, 0.5), (40, 0, 0, 0), (0, 0.5), auto=True, pad=M(22, 20, 22, 20))
    b.add("PlanPanel_Glass", unreal.VerticalBox, "PlanVBox")
    b.text("PlanVBox", "PlanOverline", "YOUR RESIDENCE", 8.5, "bold", C_GOLD, spacing=320)
    b.text("PlanVBox", "FlatTitle", "Flat C-2001", 32, "serif", var=True)
    fi = b.text("PlanVBox", "FlatInfo", "2 BHK · Tower C · Floor 20", 10.5, "regular", C_DIM, var=True); slot_box(fi, pad=M(0, 0, 0, 14))
    pbg = b.border("PlanVBox", "PlanBg", (0.97, 0.97, 0.98, 1), 10, M(6))
    pb = b.add("PlanBg", unreal.SizeBox, "PlanBox", True); pb.set_width_override(330); pb.set_height_override(620)
    ov = b.add("PlanBox", unreal.Overlay, "PlanOverlay")
    im = b.add("PlanOverlay", unreal.Image, "PlanImage", True); slot_box(im, h="H_ALIGN_FILL", v="V_ALIGN_FILL")
    hl = b.add("PlanOverlay", unreal.CanvasPanel, "HotspotLayer", True); slot_box(hl, h="H_ALIGN_FILL", v="V_ALIGN_FILL")
    hint = b.text("PlanVBox", "PlanHint", "Tap a room on the plan to step inside", 10, "regular", (1, 1, 1, 0.45)); slot_box(hint, pad=M(0, 12, 0, 0))
    ro = b.text("Root", "RoomOverline", "NOW VIEWING", 8.5, "bold", C_GOLD, spacing=360, shadow=True)
    slot_canvas(ro, (0.5, 0, 0.5, 0), (0, 30, 0, 0), (0.5, 0), auto=True)
    rt = b.text("Root", "RoomTitle", "Living", 46, "serif", var=True, shadow=True)
    slot_canvas(rt, (0.5, 0, 0.5, 0), (0, 44, 0, 0), (0.5, 0), auto=True)
    rbb, rbg = _blur_panel(b, "Root", "RoomBarBg", (0.5, 1, 0.5, 1), (0, -32, 0, 0), (0.5, 1), auto=True, radius=28, pad=M(8, 7, 8, 7))
    rb = b.add("RoomBarBg_Glass", unreal.HorizontalBox, "RoomBar", True)
    scr = b.add("Root", unreal.Image, "TopScrim"); slot_canvas(scr, (0, 0, 1, 0), (0, 0, 0, 240), (0, 0), z=-1)
    scr.set_editor_property("brush", brush((1, 1, 1, 0.5), 0, tex=unreal.load_asset("/Game/Neelam/UI/Textures/T_UI_ScrimV"), size=(8, 256), draw="IMAGE"))
    scr.set_render_transform_angle(180.0); scr.set_editor_property("visibility", unreal.SlateVisibility.HIT_TEST_INVISIBLE)
    ex = b.pill_button("Root", "ExitButton", radius=20); slot_canvas(ex, (1, 0, 1, 0), (-40, 32, 0, 0), (1, 0), auto=True)
    est = ex.get_editor_property("widget_style"); est.set_editor_property("normal", brush((0.008, 0.010, 0.016, 0.7), 20, ((0.578, 0.397, 0.144, 0.8), 1.0))); ex.set_editor_property("widget_style", est)
    b.text("ExitButton", "ExitText", "EXIT TOUR", 10, "bold", spacing=220)
    lk = b.text("Root", "LookHint", "Drag to look around", 10, "regular", (1, 1, 1, 0.6), shadow=True)
    slot_canvas(lk, (1, 1, 1, 1), (-40, -40, 0, 0), (1, 1), auto=True)
    return b.done({
        "hotspot_class": unreal.load_asset(UI + "/WBP_FV_Hotspot").generated_class(),
        "room_button_class": unreal.load_asset(UI + "/WBP_FV_RoomButton").generated_class(),
        "plan_max_height": 600.0, "plan_max_width": 420.0})
