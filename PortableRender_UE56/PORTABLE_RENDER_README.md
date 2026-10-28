# Portable Neelam amenity render project (Unreal Engine 5.6)

This is a standalone render project beside the main Neelam UE 5.5 project. It contains the 17 amenity levels and their Unreal asset dependencies (about 7.0 GB), plus the Python render pipeline and helper scripts. It is intentionally separate to avoid loading UE 5.6 assets into the UE 5.5 project.

## Open at home

1. Clone or pull branch `codex/amenity-render-handoff-2026-10-27` with Git LFS enabled; the render assets are about 6.5 GiB. The 8K review images already in the Neelam repo are under `SourceArt/Amenities/Panoramas/SharedReview_8K`.
2. Install Unreal Engine 5.6, Git for Windows (Git Bash), Python 3, and Pillow (`python -m pip install pillow`).
3. Run `Tools/setup_portable_render.ps1` once from PowerShell to create the local render bridge runner.
4. Open `Room_render.uproject` in Unreal Editor 5.6 and let shaders build on first open. Keep the editor open while rendering.
5. Render per-level amenity panoramas with `bash Tools/pano_amenities3.sh 20 Building Cabin CarPark Court FireRoom Gym JoggingTrack Lightings PartyLawn Path Pavilion PickleBall Pool Senior STP Washroom` from Git Bash. Outputs go under `Saved/Final/Panoramas/{8K,16K}`.
6. For the consistent outdoor set—with outdoor amenities shown together under the shared environment—run `Tools/render_shared_outdoor.ps1` from PowerShell. Outputs go under `Saved/Final/Panoramas/SharedOutdoor_8K`.

The `.uproject` enables the same built-in editor plugins as the original renderer. The shell scripts find Python 3 from `PATH` (including the Windows `py -3` launcher), so they do not depend on the original workstation's install path. `Saved`, `Intermediate`, and `DerivedDataCache` are regenerated locally and are not part of this portable copy. New renders remain review outputs until they pass visual QA and are assigned to the live amenity pins.
