#!/usr/bin/env bash
# Prefer the Windows launcher and only use an interpreter that has Pillow,
# which the panorama stitchers require. Windows app-execution aliases can
# appear on PATH without a usable Python installation.
if command -v py >/dev/null 2>&1 && py -3 -c 'import PIL' >/dev/null 2>&1; then
  exec py -3 "$@"
fi
for candidate in python3 python; do
  if command -v "$candidate" >/dev/null 2>&1 && "$candidate" -c 'import PIL' >/dev/null 2>&1; then
    exec "$candidate" "$@"
  fi
done
echo "Python 3 with Pillow was not found. Install Python 3 and Pillow, then add them to PATH." >&2
exit 127
