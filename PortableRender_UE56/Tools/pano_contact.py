"""Build a labeled contact sheet.

Usage:
  python pano_contact.py <input_dir> <out.jpg> [image.jpg ...]
  python pano_contact.py <out.jpg> AmenityName ...  # legacy 8K amenity mode
"""
import sys, os, time
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageStat

args = sys.argv[1:]
if len(args) < 2:
    raise SystemExit(__doc__)

tool_dir = Path(__file__).resolve().parent
project_dir = tool_dir.parent
if Path(args[0]).is_dir():
    source_dir, output = Path(args[0]), Path(args[1])
    requested = args[2:]
    files = [source_dir / n for n in requested] if requested else sorted(
        p for p in source_dir.glob("*.jpg") if p.name.lower() != "contact_sheet.jpg"
    )
else:
    source_dir, output = project_dir / "Saved" / "Final" / "Panoramas" / "8K", Path(args[0])
    files = [source_dir / ("Amenity_%s_360_8K.jpg" % n) for n in args[1:]]

files = [p for p in files if p.is_file()]
if not files:
    raise SystemExit("No panorama images found in %s" % source_dir)

W, H, COLS = 960, 480, 3
rows = (len(files) + COLS - 1) // COLS
sheet = Image.new("RGB", (COLS * W, rows * H), (24, 24, 24))
try:
    font = ImageFont.truetype("arialbd.ttf", 24)
except OSError:
    font = ImageFont.load_default()

for i, path in enumerate(files):
    im = Image.open(path).convert("RGB")
    im.thumbnail((W, H))
    tile = Image.new("RGB", (W, H), (24, 24, 24))
    tile.paste(im, ((W - im.width) // 2, (H - im.height) // 2))
    draw = ImageDraw.Draw(tile)
    mean = sum(ImageStat.Stat(im).mean) / 3
    label = "%s  %s  mean %.0f" % (path.stem, time.strftime("%H:%M", time.localtime(path.stat().st_mtime)), mean)
    draw.rectangle((0, 0, W, 36), fill=(0, 0, 0))
    draw.text((10, 5), label, fill="white", font=font)
    sheet.paste(tile, ((i % COLS) * W, (i // COLS) * H))

output.parent.mkdir(parents=True, exist_ok=True)
sheet.save(output, quality=88)
print("Wrote %s (%d panoramas)" % (output, len(files)))
