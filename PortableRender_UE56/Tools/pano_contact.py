"""py contact.py out.jpg Name ...  -> 2-col sheet of Room_render 8K amenity panos with mtime + mean brightness"""
import sys, os, time
from PIL import Image, ImageDraw, ImageFont, ImageStat
D = r"C:/Users/Admin/Documents/Unreal Projects/Room_render/Saved/Final/Panoramas/8K"
names = sys.argv[2:]; W, H = 1000, 500
sheet = Image.new("RGB", (2 * W, H * ((len(names) + 1) // 2)), (30, 30, 30)); f = ImageFont.truetype("arialbd.ttf", 26)
for i, n in enumerate(names):
    p = os.path.join(D, "Amenity_%s_360_8K.jpg" % n)
    if not os.path.exists(p): continue
    im = Image.open(p).convert("RGB"); im.draft("RGB", (2000, 1000)); im = im.resize((W, H))
    d = ImageDraw.Draw(im); m = sum(ImageStat.Stat(im).mean) / 3
    d.text((10, 8), "%s  %s  mean %.0f" % (n, time.strftime("%H:%M", time.localtime(os.path.getmtime(p))), m), fill="white", font=f, stroke_width=3, stroke_fill="black")
    sheet.paste(im, ((i % 2) * W, (i // 2) * H))
sheet.save(sys.argv[1], quality=85)
