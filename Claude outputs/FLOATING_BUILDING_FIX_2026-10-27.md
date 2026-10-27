# Codex takeover: floating buildings and amenity panoramas (2026-10-27)

## Floating facade chunk

The Neelam editor was already focused on the loaded terrain view with actor `Facade_-6_-3` selected. A live editor-world trace against `Google Photorealistic 3D Tiles` showed six buildings in that chunk had ground values near 16,000 cm while terrain under their footprints is about 3,035-3,330 cm. Their old bases were therefore roughly 123-130 m above the local terrain.

Corrected only these six records in `Scripts/Neelam/Data/massing_build.json`, preserving each building's height:

| OSM ID | New sampled ground (cm) | New base (cm) | New top (cm) |
|---|---:|---:|---:|
| 353810104 | 3150.2 | 2850.2 | 5257.3 |
| 353810108 | 3329.8 | 3029.8 | 6406.7 |
| 359160883 | 3151.6 | 2851.6 | 6154.9 |
| 359160885 | 3148.8 | 2848.8 | 5673.2 |
| 1330126873 | 3080.5 | 2780.5 | 4680.5 |
| 1330126874 | 3035.8 | 2735.8 | 24795.8 |

Rebuilt the single `facade_-6_-3.fbx` geometry chunk with Blender 5.2 in background mode; no render was run. Reimported it over `/Game/Neelam/Massing/Facades/Meshes/facade_-6_-3` and saved that asset only. The level actor remains in place; level was not saved because its tab was already dirty. The actor bounds now end at Z 24,795.8 cm (previously 38,169.9 cm), matching the corrected top. All other 3,299 building rows in `massing_build.json` match their pre-fix values.

**Important pipeline warning:** Do not run `Scripts/Neelam/make_massing.py` as a generic rebuild. It changed 1,506 unrelated building rows when run against the current source set, so that output was discarded and the saved pre-run build was restored before applying the six-row correction. The raw `massing_heights.json` remains unchanged. Backups are in `Saved/NeelamBridge/codex_backups/float_fix_20261027/`.

## Amenity panoramas

`batch_pro3.log` confirms all eight 8K renders completed. Made a before/after contact sheet at `Claude outputs/amenity_batch_pro3_before_after.jpg`; row legend is `Claude outputs/amenity_batch_pro3_before_after_legend.txt` (old/previous on the left, fresh render on the right).

Copied the eight fresh renders into `SourceArt/Amenities/Panoramas/UE/` and imported them into their existing `/Game/Neelam/Amenities/Panoramas/T_Pano_Amenity_<id>_UE` assets: `track`, `stp`, `toilets`, `gym`, `cabin`, `fire`, `parking`, `clubhouse`. Texture settings are Skybox, no mipmaps, never streamed, max 8192. No POI pin assignment was run, no client texture was replaced, and the level was not saved. Previous UE source JPGs are backed up in `Saved/NeelamBridge/codex_backups/pano_previous_20261027/`.

## Next checks

- Have the user confirm that the corrected `Facade_-6_-3` buildings match the corner in their screenshot. The active editor view had terrain loaded and the matching chunk selected; live trace results confirm the new bases sit 3 m below the lowest sampled terrain around each footprint.
- Let the user compare the panorama contact sheet before assigning any `_UE` textures to POI pins.
- Continue any other backlog items from the memory section `FLOOR PLAN AGENT STATUS` and the current handoff. Do not start a GPU render batch while Room_render is active without warning the user.