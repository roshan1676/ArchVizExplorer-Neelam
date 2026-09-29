"""NEELAM premium UI theme (dark glass + champagne gold). Shared by all UI build scripts."""
import unreal
L = unreal.NeelamToolsLibrary
EAL = unreal.EditorAssetLibrary
SANS = "/Game/Neelam/UI/Fonts/F_Neelam_Sans"
SERIF = "/Game/Neelam/UI/Fonts/F_Neelam_Serif"
TEX = "/Game/Neelam/UI/Textures/"

# colours are linear
GOLD = (0.578, 0.397, 0.144, 1.0)          # #C8A96A
GOLD_SOFT = (0.578, 0.397, 0.144, 0.22)
GLASS = (0.008, 0.010, 0.016, 0.58)        # panel tint over blur
GLASS_DEEP = (0.004, 0.005, 0.009, 0.78)
ROW = (1, 1, 1, 0.035)
ROW_HOVER = (1, 1, 1, 0.08)
LINE = (1, 1, 1, 0.10)
WHITE = (1, 1, 1, 0.96)
DIM = (0.86, 0.88, 0.92, 0.62)
FAINT = (0.86, 0.88, 0.92, 0.38)
BLUR = 22.0
R_PANEL = 18.0
R_PILL = 30.0

def LC(c): return unreal.LinearColor(*c)
def SC(c): return unreal.SlateColor(specified_color=LC(c))
def V2(x, y): return unreal.Vector2D(x, y)
def M(l, t=None, r=None, b=None):
    if t is None: t = r = b = l
    return unreal.Margin(l, t, r, b)
def tex(name): return unreal.load_asset(TEX + name)

def font(size, face="Regular", serif=False, spacing=0):
    fi = unreal.SlateFontInfo()
    fi.set_editor_property("font_object", unreal.load_asset(SERIF if serif else SANS))
    fi.set_editor_property("typeface_font_name", "Regular" if serif else face)
    fi.set_editor_property("size", size)
    fi.set_editor_property("letter_spacing", spacing)
    return fi

def brush(color=(1, 1, 1, 1), radius=0.0, outline=None, texture=None, size=None, draw="ROUNDED_BOX"):
    b = unreal.SlateBrush()
    b.set_editor_property("draw_as", getattr(unreal.SlateBrushDrawType, draw))
    b.set_editor_property("tint_color", SC(color))
    if texture: b.set_editor_property("resource_object", texture)
    if size:
        v = unreal.DeprecateSlateVector2D(); v.import_text("(X=%f,Y=%f)" % (size[0], size[1]))
        b.set_editor_property("image_size", v)
    if draw == "ROUNDED_BOX":
        o = unreal.SlateBrushOutlineSettings()
        o.set_editor_property("corner_radii", unreal.Vector4(radius, radius, radius, radius))
        o.set_editor_property("rounding_type", unreal.SlateBrushRoundingType.FIXED_RADIUS)
        if outline: o.set_editor_property("color", SC(outline[0])); o.set_editor_property("width", outline[1])
        else: o.set_editor_property("width", 0.0)
        b.set_editor_property("outline_settings", o)
    return b

def image_brush(texture, size, color=WHITE):
    return brush(color, texture=texture, size=size, draw="IMAGE")

def no_brush(): return brush((1, 1, 1, 0), draw="NO_DRAW_TYPE")

def button_style(normal=None, hover=None, pressed=None, pad=M(0), radius=R_PILL):
    st = unreal.ButtonStyle()
    st.set_editor_property("normal", normal or no_brush())
    st.set_editor_property("hovered", hover or brush(ROW_HOVER, radius))
    st.set_editor_property("pressed", pressed or brush(GOLD_SOFT, radius, (GOLD, 1.0)))
    st.set_editor_property("disabled", no_brush())
    st.set_editor_property("normal_padding", pad); st.set_editor_property("pressed_padding", pad)
    return st

def W(wbp, name):
    return unreal.find_object(None, wbp.get_path_name() + ":WidgetTree." + name)

def style_text(t, text=None, size=13, face="Regular", color=WHITE, serif=False, spacing=0, shadow=False, just=None):
    if text is not None: t.set_editor_property("text", text)
    t.set_editor_property("font", font(size, face, serif, spacing))
    t.set_editor_property("color_and_opacity", SC(color))
    if shadow:
        t.set_editor_property("shadow_offset", V2(0, 1)); t.set_editor_property("shadow_color_and_opacity", LC((0, 0, 0, 0.45)))
    else:
        t.set_editor_property("shadow_color_and_opacity", LC((0, 0, 0, 0)))
    if just: t.set_editor_property("justification", getattr(unreal.TextJustify, just))
    return t

def glass_border(b, radius=R_PANEL, color=GLASS, pad=None, outline=True):
    b.set_editor_property("background", brush((1, 1, 1, 1), radius, ((1, 1, 1, 0.10), 1.0) if outline else None))
    b.set_editor_property("brush_color", LC(color))
    if pad is not None: b.set_editor_property("padding", pad)
    return b

def blur(bb, radius=R_PANEL, strength=BLUR):
    bb.set_editor_property("blur_strength", strength)
    try: bb.set_editor_property("corner_radius", unreal.Vector4(radius, radius, radius, radius))
    except Exception: pass
    return bb

def canvas(w, anchors, offsets, align=(0, 0), auto=False, z=None):
    s = w.get_editor_property("slot")
    a = unreal.Anchors(); a.set_editor_property("minimum", V2(anchors[0], anchors[1])); a.set_editor_property("maximum", V2(anchors[2], anchors[3]))
    s.set_anchors(a); s.set_offsets(M(*offsets)); s.set_alignment(V2(*align)); s.set_auto_size(auto)
    if z is not None: s.set_z_order(z)
    return s

def box(w, pad=None, fill=None, h=None, v=None):
    s = w.get_editor_property("slot")
    if pad is not None and hasattr(s, "set_padding"): s.set_padding(pad if isinstance(pad, unreal.Margin) else M(pad))
    if fill is not None and hasattr(s, "set_size"):
        cs = unreal.SlateChildSize(); cs.set_editor_property("value", fill if fill else 1.0)
        cs.set_editor_property("size_rule", unreal.SlateSizeRule.FILL if fill else unreal.SlateSizeRule.AUTOMATIC); s.set_size(cs)
    if h and hasattr(s, "set_horizontal_alignment"): s.set_horizontal_alignment(getattr(unreal.HorizontalAlignment, h))
    if v and hasattr(s, "set_vertical_alignment"): s.set_vertical_alignment(getattr(unreal.VerticalAlignment, v))
    return s

def add(wbp, parent, cls, name, index=-1, var=False):
    ex = W(wbp, name)
    if ex: return ex
    w = L.add_widget(wbp, parent or "None", cls, name, index, var)
    if w is None: raise RuntimeError("add failed %s/%s" % (parent, name))
    return w

VIS = unreal.SlateVisibility
