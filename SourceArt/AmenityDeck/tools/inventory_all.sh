#!/bin/bash
D="C:/Users/Admin/Documents/Unreal Projects/ArchVizExplorer-Neelam/SourceArt/AmenityDeck"
B="/c/Program Files/Blender Foundation/Blender 5.2/blender.exe"
for f in /c/Users/Admin/Downloads/Blender\ Files/*.blend; do
  n=$(basename "$f" .blend); n=${n// /_}
  [ -f "$D/inventory/$n.json" ] && continue
  "$B" -b "$f" --factory-startup --python "$D/tools/inventory_blend.py" -- "$D/inventory/$n.json" > "$D/inventory/$n.log" 2>&1
  echo "$n $(ls -la "$D/inventory/$n.json" 2>/dev/null | awk '{print $5}')"
done
