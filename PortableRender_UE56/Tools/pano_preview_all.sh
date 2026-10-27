#!/bin/bash
# Lumen 360 previews of every spot of a unit (its level must be open). bash Tools/pano_preview_all.sh 3BHK
R="$(cd "$(dirname "$0")/.." && pwd -W)"; U=$1
"C:/Users/Admin/AppData/Local/Programs/Python/Python314/python" -c "
import sys; sys.path.insert(0, r'$R/Content/Python'); from pano_spots import SPOTS
for k, (x, y) in SPOTS['$U'].items(): print(k, x, y)" | tr -d '\r' | while read k x y; do bash "$R/Tools/pano_preview.sh" "${U}_$k" $x $y 12 >/dev/null; echo "$k"; done
"C:/Users/Admin/AppData/Local/Programs/Python/Python314/python" -c "
import glob; from PIL import Image
fs=sorted(glob.glob(r'$R/Saved/Pano/preview/${U}_0*.jpg')); o=Image.new('RGB',(2048,512*len(fs)))
for i,f in enumerate(fs): o.paste(Image.open(f).resize((2048,512)),(0,i*512))
o.save(r'$R/Saved/Pano/preview/sheet_$U.jpg')"
