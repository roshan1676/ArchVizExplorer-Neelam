# Portable Neelam amenity render project (Unreal Engine 5.6)

This is a standalone render project beside the main Neelam UE 5.5 project. It contains the 17 amenity levels and their Unreal asset dependencies (about 7.0 GB), plus the Python render pipeline and helper scripts. It is intentionally separate to avoid loading UE 5.6 assets into the UE 5.5 project.

## Open at home

1. Install Unreal Engine 5.6, Git for Windows (for Git Bash), Python 3, and Pillow (`python -m pip install pillow`).
2. Open `PortableRender_UE56/Room_render.uproject` in Unreal Editor 5.6 and let shaders build on first open.
3. The Unreal Python plugin starts the local render bridge when the editor opens.
4. To rerender the shared outdoor panoramas, run `Tools/render_shared_outdoor.ps1` from PowerShell. Outputs go under `Saved/Final/Panoramas/SharedOutdoor_8K`.

The `.uproject` enables the same built-in editor plugins as the original renderer. `Saved`, `Intermediate`, and `DerivedDataCache` are regenerated locally and are not part of this portable copy. New renders remain review outputs until they pass visual QA and are assigned to the live amenity pins.