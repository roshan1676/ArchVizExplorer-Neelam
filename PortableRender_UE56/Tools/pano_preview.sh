#!/bin/bash
# Lumen 360 preview of a spot in the open level.  bash Tools/pano_preview.sh <name> <x> <y> [ticks=15]
# -> Saved/Pano/preview/<name>.jpg (2048x1024 equirect)
R="$(cd "$(dirname "$0")/.." && pwd)"; UE="$R/Saved/ClaudeBridge/ue.sh"; N=${4:-15}
echo "import pano, importlib; importlib.reload(pano); result = pano.preview_start('$1', $2, $3)" | bash "$UE" - 60 >/dev/null
for i in $(seq 1 "$N"); do echo "import pano; result = pano.preview_tick('$1')" | bash "$UE" - 60 >/dev/null; done
echo "import pano; result = pano.preview_finish('$1')" | bash "$UE" - 60 >/dev/null
"C:/Users/Admin/AppData/Local/Programs/Python/Python314/python" "$R/Tools/stitch_pano.py" "$R/Saved/Pano/preview/$1" "$R/Saved/Pano/preview/$1" 2048
