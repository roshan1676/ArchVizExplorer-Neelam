#!/bin/bash
# Bake materials for the 5 heavy amenity files that skipped it. 2 Blender processes at a time.
R="$(cd "$(dirname "$0")/.." && pwd)"; B="/c/Program Files/Blender Foundation/Blender 5.2/blender.exe"; S="/c/Users/Admin/Downloads/Blender Files"
bake() { "$B" --background --factory-startup "$S/$2.blend" --python "$R/Tools/bake_mats.py" -- "$(cygpath -w "$R/SourceArt/Amenity_$1")" > "$R/Saved/bake_$1.log" 2>&1; echo "$(date +%H:%M) baked $1 rc=$? n=$(ls "$R/SourceArt/Amenity_$1/baked" 2>/dev/null | wc -l)"; }
( bake Court "multipurpose court"; bake STP "smtp plant"; bake Building building ) &
( bake Pool pool; bake Senior "senior citizen" ) &
wait
