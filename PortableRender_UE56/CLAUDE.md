# Room_render (UE 5.6) — Neelam 2BHK / 3BHK archviz

Blender sources: `C:\Users\Admin\Desktop\archviz - neelam\2bhk\2BHK (1).blend`, `...\3bhk\Untitled.blend` (Cycles, AgX).
Levels: `/Game/Neelam/2BHK/L_2BHK`, `/Game/Neelam/3BHK/L_3BHK`. The older `/Game/2BHK` map is the user's — don't touch.

## Editor bridge
`Content/Python/init_unreal.py` starts `claude_bridge.py` on editor launch (if the editor was already open:
Output Log → Cmd → `py "C:/Users/Admin/Documents/Unreal Projects/Room_render/Content/Python/init_unreal.py"`).
Run Python in the open editor: `bash Saved/ClaudeBridge/ue.sh file.py [timeout]` or `echo '...' | bash ue.sh - 60`; set `result = ...`.
Heartbeat: `Saved/ClaudeBridge/heartbeat.json` (every 3 s). Long jobs (imports) block the editor — use a big timeout.

## Pipeline (re-runnable per scene, name = "2BHK" / "3BHK")
1. `Tools/blend_export.py` (Blender) → `SourceArt/<NAME>/scene.gltf` + `scene.json` (lights, cameras, material kinds). Skips render-hidden objects.
2. `Tools/bake_mats.py` (Blender) → `SourceArt/<NAME>/baked/` base colour + roughness for materials glTF can't express (mixes, ramps, procedural).
3. `Tools/hdri_export.py` (Blender) → `SourceArt/<NAME>/sky.hdr` + `world.json` (Easy HDRI sky strength).
4. In editor: `import scene_builder as SB` → `SB.new_level`, `import_meshes`, `fix_materials` (glass/emissive → `/Game/Neelam/Shared/M_Glass|M_Emissive`),
   `apply_bakes`, `nanite_off_for_translucent`, `place_lights`, `place_cameras`, `environment`; or `SB.build(name)` for all.
Blender CLI: `"/c/Program Files/Blender Foundation/Blender 5.2/blender.exe" --background --factory-startup <blend> --python <script> -- <out_dir>`.
Blender crashes on exit after big exports — harmless if `@@DONE` is in the log.
UE's glTF importer silently imports NOTHING if the file requires `EXT_texture_webp`: convert `tex/*.webp` to PNG and drop the
extension from scene.gltf (done once for 3BHK by hand — redo after any 3BHK re-export).

## Units / matching
- Blender (x,y,z) m → UE (x, -y, z)·100 cm (verified against imported actors).
- Cycles value 1.0 = UE 1.2 nits at EV100 0, manual exposure (`K = 1.2` in scene_builder): area W → rect nits K·W/(π·A), point/spot cd K·W/4π, sun lux K·W, emissive ×K, sky light K·strength.
- Camera renders: `bash Tools/shot.sh <camera label> <name> [ticks]` → `Saved/ClaudeBridge/shots/<name>.png`. SceneCapture with Lumen,
  one capture per bridge job so Lumen accumulates over real frames (works with the editor unfocused). A single-frame capture has no
  bounce light (black ceilings). Shadows look slightly blocky in these captures only (VSM).
  HighResShot does NOT work while the editor window is in the background.
- Blender reference: Cycles CPU render (GPU is full while the editor runs). 2BHK works; 3BHK crashed (access violation) on CPU render.
- Final 4K stills: Movie Render Queue (plugin enabled). `import mrq_render as R`; `R.make_sequences(name)` with that level open
  (one-frame SEQ_ per BL_ camera in /Game/Neelam/<NAME>/Shots), then `R.render_all()` -> Saved/MovieRenders/<NAME>/<cam>.png.
  All 5 cameras take ~2 min. Background CPU throttling is off via Config/DefaultEditorPerProjectUserSettings.ini.

## Progress
`powershell -File Tools/progress.ps1` — live export / bake / bridge status.

## Luxury pass (Content/Python/lux.py) — in progress
- `lux.environment(unit, hdri, ...)`: Poly Haven sky HDRI (SourceArt/HDRI) as sky light + sky sphere, spun so its sun sits at sun_yaw
  (3BHK living window faces yaw 180), matching warm directional sun. `lux.sky_probe` checks where the HDRI sun lands.
- `lux.glass_material()`: M_Glass is Thin Translucent — the old refractive glass went black/blocked sun in the path tracer.
- `lux.lighting(unit)`: lights 3200 K, LED strips warm, sun 4500 K / 12 lux, white balance 4800, light grade.
- Finals: `mrq_render.render([("3BHK","SEQ_Camera")], path_tracer=True, spp=128, tag="_x")` (~20 s at 1080p).
- Unreal Python Rotator positional order is (roll, pitch, yaw) — always use keywords.
- Path tracer: sky sphere must stay visible_in_ray_tracing (PT doesn't draw the sky light as background).
- Materials: `Content/Python/lux_mat.py` — M_LuxSurface (+ MI_Statuario / MI_NeroMarquina / MI_Walnut / MI_Brass in /Game/Neelam/Shared/Lux).
  WorldTiles mode = 120 cm slabs at true scale, per-tile random offset, grout; projection picked from the surface normal (floors and walls).
  `LM.swap(unit, {"old material name" or "prefix*": "Statuario"|...})`; the swap tables used are in Saved/ClaudeBridge/_swap3.py and _lux2.py.
  Gotchas: ComponentMask nodes default to R+G on (set all four channels); sampler type must match texture (roughness = sRGB colour here).
  `lux.warm_emissives()` warms near-white glTF emissives (white balance turns them blue otherwise).
- Both levels have the full pass (sky, lighting, materials). 2BHK bathroom walls are Statuario slabs.
- Props: local BlenderKit library C:/Users/Admin/blenderkit_data/models (184 assets). `bash Tools/bk_import.sh <folder> <PropName>`
  (bk_prep.py joins to one mesh, pivot bottom-centre, then blend_export + bake_mats) -> `props.import_prop(name)` / `props.place(...)`
  / `props.picture_light(...)` in Content/Python/props.py. Placed so far (3BHK): corridor console, 2 art + wash lights, plant,
  6 walnut fluted panels (Saved/ClaudeBridge/_corridor*.py), balcony glass railing (parapet `Cube` hidden, _rail.py),
  balcony lounge: 2 Qubba chairs, rattan table, palm (_balcony.py). Corridor cam BL_Camera.002 has its own exposure bias -0.8.
- SAVE GOTCHA: save_dirty_packages() did not always persist level actor overrides; also call
  LevelEditorSubsystem.save_current_level() and verify by reloading the level (MRQ renders load maps from disk).
- Window view (real Mulund): client DJI drone photos at floors 5/10/15/20/30/40 in
  ArchVizExplorer-Neelam/SourceArt/FloorView/FloorGallery. floor_20 -> SourceArt/View/view_floor20.png (crop left tower,
  warm grade, top fades to alpha, PRE-MIRRORED because the arc maps U right-to-left). Tools/view_arc.py builds the 120 deg arc
  (UVs from vertex direction). `lux_view.place("LUX_View_Living", center_xy, facing_yaw=180)` in both levels, 300 m radius,
  MI_ViewBackdrop Strength 3. GOTCHA: Interchange turned Nanite ON for the arc -> translucent fallback mesh = zigzag photo; keep it OFF.
- 2BHK room cameras (2026-10-19): `cams.make()` (Content/Python/cams.py) -> LUX_Cam_Living, Living2, Dining, Bed1, Bed2 (+ BL_Camera bathroom);
  sequences SEQ_<name> via mrq_render.make_sequences (now includes LUX_Cam_*). 2BHK staging is an open 11x22 m showcase, NOT the plan,
  and has NO kitchen. Extra view arc LUX_View_FacadeX (facing +X) for the living balcony doors; balcony lounge set placed.
  Black glass fix: Blender glass with linked colour came in black (opaque in thin translucent) -> clear tint; MI_diamond was pure green.
- 2BHK kitchen (added, not in Blender): ceiling-less room x -100..498, y -477..-101 (window on east wall). BlenderKit kitchen-set via
  Tools/kitchen_prep.py (drop hood, cut at 2.6 m, clear custom normals, smooth by angle) -> LUX_Kitchen at (490,-474,0) yaw 90
  (Interchange flips mesh Y). Materials: MI_WalnutWorld + MI_StatuarioSlab (world-projected, lux_mat.world_variants), brass pendants/tap.
  LUX_KitchenCeiling slab, 4 downlights 160 cd, 2 pendant points, LED rect; LUX_Cam_Kitchen EV -1.6 -> SEQ_Kitchen.
  GOTCHA: path tracer renders Nanite meshes from the coarse fallback -> faceted triangles. Nanite is OFF on all /Game/Neelam/Props meshes.
- QA pass (user-flagged issues, 2026-10-19): `inspect_px.py` = pick(cam, px, py), gap_up(label), ceiling_fixtures() scan,
  snap_ceiling_lights(), invisible_material(). Fixed: 20 floating disc lights (3BHK), 2BHK window_cut boxes Cube_039/057 (Blender
  camera-invisible -> exporter now skips visible_camera=False / WIRE objects), sheer Voilage -> M_Sheer, curtains -> MI_Linen,
  toilet paper holder onto wall (roll is attached to holder: move only the parent!), bedroom sconces 1 cm off wall,
  corridor art flush + glass slot -> M_Invisible, walnut column -> WalnutWorld, M_LuxSurface two-sided (thin folds went black in PT).
  Finals: Saved/MovieRenders/*/*_FINAL_4K.png + FINAL_contact_sheet.png.
- 360 panoramas: pano.py (6 cube cams PANO_<spot>_<F|R|B|L|U|D>, eye 163 cm, 92 deg), pano_spots.py (15 spots), Tools/pano_preview.sh,
  mrq_render.render_panos -> Saved/Pano/faces, Tools/stitch_pano.py / stitch_all.py -> Saved/Pano/final *_16K.jpg/_8K.jpg.
  RENDER_PANOS.bat = one click (run_all_panos.py renders only missing spots, then stitches). NOT yet tested end to end (2026-10-19).
  3BHK bedrooms got the 2BHK bed sets (copyset.py). 3BHK area x 500-1000 (3rd bedroom + 2 baths) is EMPTY in the source - no panos there.
- ONE CLICK: RENDER_ALL.bat -> run_all.py (rebuild pano rigs, mrq_render.render_everything: 11 stills 8K/256spp + 15 panos 6x4K/192spp, skips done) -> Tools/finalize.py -> Saved/Final (README.txt there). Pano spot ~15 min, 8K still ~7 min.
- RENDER_ALL launch (fixed 2026-10-21): bat writes Saved/ClaudeBridge/RENDER_ALL.flag and opens the project; init_unreal.py sees the flag -> import run_all.
  NEVER use -ExecutePythonScript for long jobs (editor QUITs after the script; also '\r' in the path got escaped). Executor-finished
  callable needs 2 args (executor, success). Bridge does NOT run while MRQ renders. First full run started 2026-10-21 12:00 IST (26 jobs).
- 2026-10-21 texture pass: Statuario/StatuarioSlab now Marble021 (clean white, Tint 1.0); all MI_Walnut -> MI_WalnutWorld in both levels
  (stretched grain on fluted panels); 2BHK blotchy velvet sofa (bed_01_body_001) -> MI_Taupe_Velvet. Old raw renders deleted.
- 2026-10-21 depth/lighting pass: lux.depth_pass (walls Vert -> MI_WallPlaster warm Marble021 tint .70/.63/.55, sky 0.3, sun 22,
  area-light barn doors 40, EV -0.65, contrast 1.16, vignette .45; params Saved/ClaudeBridge/dp_params.json, run _dp.py), lux.track_spots
  (3BHK track fixtures -> 37 real 135 cd wall-grazing spots). Per-camera EV: 2BHK BL_Camera +0.5, LUX_Cam_Kitchen -2.1, 3BHK BL_Camera.003 +0.4.
