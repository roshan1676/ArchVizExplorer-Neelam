#!/bin/bash
# Lumen-converged offscreen render of a camera in the open level.
# Usage: bash Tools/shot.sh <camera_label> <name> [ticks=30]  -> Saved/ClaudeBridge/shots/<name>.png
UE="$(dirname "$0")/../Saved/ClaudeBridge/ue.sh"; N=${3:-30}
echo "import capture, importlib; importlib.reload(capture); result = capture.start('$1', '$2')" | bash "$UE" - 60 >/dev/null
for i in $(seq 1 "$N"); do echo "import capture; result = capture.tick('$2')" | bash "$UE" - 60 >/dev/null; done
echo "import capture; result = capture.finish('$2')" | bash "$UE" - 60 | grep '"result"'
