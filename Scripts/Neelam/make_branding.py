"""NEELAM branding: app icon, game + editor splash, project thumbnail (run with plain Python + Pillow, NOT in UE).

    py Scripts/Neelam/make_branding.py [hero.png]

Writes Build/Windows/Application.ico, Content/Splash/Splash.bmp, Content/Splash/EdSplash.jpg (+.bmp),
ArchVizExplorer.png. Style = the in-game UI (UI_Theme.py): dark glass + champagne gold #C8A96A,
Cormorant Garamond wordmark, Inter caps line. hero.png (optional) = a render used as splash backdrop.
"""
import os, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
FONTS = os.path.join(ROOT, "SourceArt", "Fonts")
GOLD, GOLD_HI, INK, INK2, WHITE = (200, 169, 106), (232, 211, 160), (7, 8, 11), (20, 24, 32), (244, 241, 234)


def serif(px, weight=500):
    f = ImageFont.truetype(os.path.join(FONTS, "CormorantGaramond-Var.ttf"), px)
    try: f.set_variation_by_axes([weight])
    except Exception: pass
    return f


def sans(px, face="SemiBold"):
    return ImageFont.truetype(os.path.join(FONTS, f"Inter-{face}.ttf"), px)


def vgrad(size, top, bottom):
    w, h = size
    g = Image.new("RGB", (1, h))
    for y in range(h):
        t = y / max(h - 1, 1)
        g.putpixel((0, y), tuple(int(a + (b - a) * t) for a, b in zip(top, bottom)))
    return g.resize(size)


def gold_fill(size):
    """Brushed champagne gold: light top-left -> deeper bottom-right."""
    w, h = size
    g = Image.new("RGB", (w, h))
    px = g.load()
    for y in range(h):
        for x in range(0, w, 1):
            t = min(1.0, (x / w * 0.35 + y / h * 0.65))
            px[x, y] = tuple(int(a + (b - a) * t) for a, b in zip(GOLD_HI, (164, 130, 70)))
    return g


def spaced(draw, xy, text, font, fill, spacing, anchor_center=False):
    """Letter-spaced text (UE 'spacing' look). Returns width."""
    widths = [draw.textlength(c, font=font) for c in text]
    total = sum(widths) + spacing * (len(text) - 1)
    x, y = xy
    if anchor_center: x -= total / 2
    for c, w in zip(text, widths):
        draw.text((x, y), c, font=font, fill=fill)
        x += w + spacing
    return total


def towers(size, color, alpha=255):
    """Line-art of the three Wind Tunnel towers on the podium (fallback backdrop)."""
    w, h = size
    im = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    lw = max(1, w // 480)
    base = int(h * 0.86)
    pod = (int(w * 0.08), int(h * 0.72), int(w * 0.92), base)
    c = color + (alpha,)
    d.rectangle(pod, outline=c, width=lw)
    for i, (x0, x1, top) in enumerate(((0.16, 0.38, 0.10), (0.40, 0.62, 0.04), (0.64, 0.86, 0.13))):
        X0, X1, T = int(w * x0), int(w * x1), int(h * top)
        d.rectangle((X0, T, X1, pod[1]), outline=c, width=lw)
        d.rectangle((X0 + (X1 - X0) // 3, T - int(h * 0.03), X1 - (X1 - X0) // 3, T), outline=c, width=lw)
        fl = (pod[1] - T) / 34
        for k in range(1, 34):                       # floor lines
            y = int(T + k * fl)
            d.line((X0, y, X1, y), fill=color + (alpha // 3,), width=1)
        for k in range(1, 4):                        # bay lines
            x = X0 + (X1 - X0) * k // 4
            d.line((x, T, x, pod[1]), fill=color + (alpha // 4,), width=1)
    d.line((0, base, w, base), fill=c, width=lw)
    return im


def icon_master(n=1024):
    r = n // 5
    mask = Image.new("L", (n, n), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, n - 1, n - 1), r, fill=255)
    bg = vgrad((n, n), INK2, INK).convert("RGBA")
    # soft gold glow behind the monogram
    glow = Image.new("L", (n, n), 0)
    ImageDraw.Draw(glow).ellipse((n * .18, n * .14, n * .82, n * .78), fill=70)
    glow = glow.filter(ImageFilter.GaussianBlur(n // 8))
    bg = Image.composite(Image.new("RGBA", (n, n), GOLD + (255,)), bg, glow)
    # monogram N + rule, gold gradient through a text mask
    tm = Image.new("L", (n, n), 0)
    td = ImageDraw.Draw(tm)
    f = serif(int(n * 0.78), 500)
    td.text((n / 2, n * 0.47), "N", font=f, fill=255, anchor="mm")
    td.rectangle((n * .30, n * .80, n * .70, n * .80 + max(4, n // 90)), fill=255)
    bg = Image.composite(gold_fill((n, n)).convert("RGBA"), bg, tm)
    # hairline gold border
    ImageDraw.Draw(bg).rounded_rectangle((n * .035, n * .035, n * .965, n * .965), int(r * .82),
                                         outline=GOLD + (150,), width=max(3, n // 160))
    out = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    out.paste(bg, (0, 0), mask)
    return out


def splash(size, hero=None, editor=False):
    w, h = size
    if hero:
        im = Image.open(hero).convert("RGB")
        s = max(w / im.width, h / im.height)
        im = im.resize((int(im.width * s + .5), int(im.height * s + .5)), Image.LANCZOS)
        x0 = (im.width - w) // 2 + int((im.width - w) * 0.25)   # push the towers right
        im = im.crop((min(x0, im.width - w), (im.height - h) // 2, min(x0, im.width - w) + w, (im.height - h) // 2 + h))
        im = ImageChops.multiply(im, vgrad(size, (150, 150, 155), (90, 90, 96)))
        # left-to-right dark scrim so the wordmark reads
        scrim = Image.new("L", (w, 1))
        for x in range(w):
            scrim.putpixel((x, 0), int(245 * max(0.0, 1 - x / (w * 0.62)) ** 1.4))
        im = Image.composite(Image.new("RGB", size, INK), im, scrim.resize(size)).convert("RGBA")
    else:
        im = vgrad(size, INK2, INK).convert("RGBA")
        art = towers((int(w * .46), int(h * .92)), GOLD, 120)
        im.alpha_composite(art, (int(w * .56), int(h * .08)))
        fade = Image.new("L", (w, 1))
        for x in range(w):
            fade.putpixel((x, 0), int(255 * max(0.0, 1 - (x - w * .52) / (w * .18))) if x > w * .52 else 255)
        im = Image.composite(vgrad(size, INK2, INK).convert("RGBA"), im, fade.resize(size))
    d = ImageDraw.Draw(im)
    x, y = int(w * 0.075), int(h * (0.30 if editor else 0.30))
    big = serif(int(h * 0.20), 500)
    spaced(d, (x, y), "NEELAM", big, WHITE, int(h * 0.035))
    y += int(h * 0.27)
    d.rectangle((x + 2, y, x + int(w * 0.07), y + max(2, h // 240)), fill=GOLD)
    y += int(h * 0.05)
    spaced(d, (x + 2, y), "WIND TUNNEL  ·  MULUND EAST", sans(int(h * 0.036)), GOLD, int(h * 0.012))
    y += int(h * 0.075)
    spaced(d, (x + 2, y), "INTERACTIVE EXPERIENCE", sans(int(h * 0.026), "Medium"), WHITE[:3] + (150,), int(h * 0.010))
    # thin gold frame
    d.rectangle((0, 0, w - 1, h - 1), outline=GOLD + (90,), width=1)
    return im.convert("RGB")


def main():
    hero = sys.argv[1] if len(sys.argv) > 1 else None
    ico = icon_master()
    os.makedirs(os.path.join(ROOT, "Build", "Windows"), exist_ok=True)
    ico.save(os.path.join(ROOT, "Build", "Windows", "Application.ico"),
             sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    ico.resize((192, 192), Image.LANCZOS).save(os.path.join(ROOT, "ArchVizExplorer.png"))
    ico.resize((512, 512), Image.LANCZOS).save(os.path.join(ROOT, "SourceArt", "Neelam_Icon_512.png"))
    sp = os.path.join(ROOT, "Content", "Splash")
    splash((960, 480), hero).save(os.path.join(sp, "Splash.bmp"))
    ed = splash((960, 540), hero, editor=True)
    ed.save(os.path.join(sp, "EdSplash.jpg"), quality=93)
    ed.save(os.path.join(sp, "EdSplash.bmp"))
    print("branding written")


if __name__ == "__main__":
    main()
