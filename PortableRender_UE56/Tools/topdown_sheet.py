"""Grid-labelled contact sheets of Saved/Pano/_topdown/<name>.png (10x10 cells A-J x 0-9, 2x2 per sheet).
Cell -> world: cell_to_world(name, 'C4'). Usage: python topdown_sheet.py <out_prefix> Name1 Name2 ..."""
import sys, json, os
from PIL import Image, ImageDraw, ImageFont
D = os.path.join(os.path.dirname(__file__), "..", "Saved", "Pano", "_topdown")

def cell_to_world(name, cell, sub=(0.5, 0.5)):
    j = json.load(open(os.path.join(D, name + ".json")))
    col, row = "ABCDEFGHIJ".index(cell[0].upper()), int(cell[1:])
    u, v = (col + sub[0]) / 10, (row + sub[1]) / 10
    return j["cx"] + (u - 0.5) * j["w"], j["cy"] + (v - 0.5) * j["w"]   # image x = +X, image y = +Y

def tile(name, s=800):
    im = Image.open(os.path.join(D, name + ".png")).convert("RGB").resize((s, s)); d = ImageDraw.Draw(im)
    f = ImageFont.truetype("arialbd.ttf", 15)
    for i in range(1, 10):
        d.line([(i * s / 10, 0), (i * s / 10, s)], fill=(255, 255, 0), width=1); d.line([(0, i * s / 10), (s, i * s / 10)], fill=(255, 255, 0), width=1)
    for c in range(10):
        for r in range(10):
            d.text((c * s / 10 + 3, r * s / 10 + 2), "ABCDEFGHIJ"[c] + str(r), fill=(255, 255, 0), font=f, stroke_width=2, stroke_fill=(0, 0, 0))
    j = json.load(open(os.path.join(D, name + ".json")))
    d.text((s / 2 - 150, s - 30), "%s  %.0f m wide" % (name, j["w"] / 100), fill=(255, 255, 255), font=ImageFont.truetype("arialbd.ttf", 22), stroke_width=3, stroke_fill=(0, 0, 0))
    return im

if __name__ == "__main__":
    names = sys.argv[2:]
    for k in range(0, len(names), 4):
        sheet = Image.new("RGB", (1600, 1600))
        for i, n in enumerate(names[k:k + 4]): sheet.paste(tile(n), ((i % 2) * 800, (i // 2) * 800))
        sheet.save("%s_%d.jpg" % (sys.argv[1], k // 4), quality=88)
