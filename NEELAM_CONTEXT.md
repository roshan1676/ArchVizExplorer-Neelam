# NEELAM – project memory / resume context

> Read this first when resuming work (human or AI assistant).
> Last updated: 28 Sep 2026. Engine: Unreal Engine 5.5 · Template: "ArchViz Explorer" (KarlDetroit) · Blueprint-only (no C++).
> Plugins: CesiumForUnreal, SunPosition, Volumetrics. Main level: `/Game/ArchVizExplorer/Maps/Realistic_01`.

---

## 1. What this project is
Interactive real-estate presentation of the **Neelam "Wind Tunnel" development** (5 towers A–E, podium, amenities)
at **SUPREMO, V B Phadke Road, next to V.G. Vaze College, Mulund East, Mumbai**, placed on a real 3D map
(Cesium World Terrain + Google Photorealistic 3D Tiles). Cesium georeference origin 19.163755 N, 72.958977 E.

Reference videos for the target experience:
- Vinode "UE5 ArchViz Web App Template" – https://youtu.be/5VOTfkBfgCI (apartment selector, floor plan, fly-through)
- Visual Dynamics "Dynamic Immersion 2.0" – https://youtu.be/WfIEcqHoDMo (units/amenities/floor-plan menus, **flat tour with room bar + interior configurator** ← most important for the client)

## 2. Live editor link – NeelamBridge (IMPORTANT for AI-assisted work)
- `Scripts/Neelam/NeelamBridge.py` – auto-started by `Content/Python/init_unreal.py` whenever the editor opens.
- Drop `<job>.py` into `Saved/NeelamBridge/inbox/` → editor runs it inside one Undo transaction →
  result in `Saved/NeelamBridge/outbox/<job>.json` `{ok, stdout, error, result, seconds}`.
- Inside a job: `shot(name, unreal.Vector, unreal.Rotator, settle_s)` renders a screenshot through a hidden
  SceneCapture2D (works with the editor in the background) → `Saved/NeelamBridge/outbox/shots/<name>.png`.
- `env` dict persists between jobs. Heartbeat: `Saved/NeelamBridge/outbox/heartbeat.json`.
- Git with LFS must be run from **Windows** (the Cowork Linux VM has no git-lfs); a job can call `subprocess.run(["git", ...])`.
- Editor Python notes: `unreal.WidgetBlueprintLibrary` / `SlateBlueprintLibrary` are NOT available in the editor Python;
  widget templates can be edited with `unreal.load_object(None, "<BP>.<BP>:WidgetTree.<Widget>")` + compile + save.
  During PIE: `UnrealEditorSubsystem.get_game_world()`, PC variable `MasterMenu` → `Surroundings` → `BP_POI_List_*`.

## 3. Done so far
| Area | Result | Script(s) |
|---|---|---|
| Config | `WaterBodyCollision` collision profile added to `Config/DefaultEngine.ini` | – |
| Building | 81 meshes / 511 placements imported to `/Game/Neelam/Buildings/WindTunnel`, attached to `Neelam_WindTunnel_Root` | `Place_WindTunnel.py` (+ `Data/level_manifest.json`, `asset_report.json`) |
| Materials | 20 Poly Haven CC0 2K texture sets → masters `M_Neelam_Surface/Glass/Emissive` + 55 `MI_*`, tuned to the RenderEdge reference renders | `Apply_WindTunnel_Materials.py` (re-downloads textures into `SourceArt/PolyHaven` if missing) |
| Site | Real site boundary (curved) → `SM_Site_Platform` + `SM_Site_Lawn`; Cesium cut-out `Neelam_SiteCutout` 12 cm inside the boundary wall; root Z seated on ground | `make_site_outline.py`, `Build_Site_Outline.py`, `Ground_Development.py`, `Site_Finishing.py` |
| Vegetation | 70 hand-placed trees/bushes around the site (`Neelam_Vegetation`) + 3,598 map-detected trees in 3×3 km (`Neelam_Vegetation_Area`), HISM, culled, no collision | `make_tree_candidates.py`, `Plant_Vegetation.py`, `Plant_Area_Trees.py` |
| Clean-up (Surroundings Phase 1) | Removed template US sample data: 13 BP_RoadTool (+318 poles, 318 lamps), 15 BP_Skyglow | via bridge |
| Surroundings Phase 2 (MUST HAVE) | POIs: V.G. Vaze College, Mulund Railway Station, Check Naka (Mulund East toll plaza, EEH). Drive routes (OSRM, real roads). Key-road glow lines + labels: V B Phadke Rd, Eastern Express Hwy, Mulund–Airoli Link Rd. 144 pole lights (45 VB Phadke, 99 highway) | `make_connectivity.py`, `connectivity_lib.py`, `Build_Surroundings.py`, `Data/landmarks_phase2.json`, `Data/connectivity_phase2.json`, `Data/osm/*` |
| UI tweak | `BP_Entry_Widget` rows made shorter (padding 4→1 px, font 12→11) so 5 entries fit a list | via bridge |

Review / capture helper: `Capture_Review_Shots.py`.

## 4. ⚠️ OPEN ISSUE – Surroundings list entry not clickable
**Symptom (user):** in PIE → SURROUNDINGS → TRANSPORTATION list, the road entry (**Mulund–Airoli Link Road**, 5th row) cannot be clicked. Still not working after the row-height change.

**Verified so far:**
- Widget wiring is correct: all 5 entries exist, are enabled, visibility `SelfHitTestInvisible`, each linked to its POI (`Label_mar` etc.).
- Calling `Select_POI` on `Label_mar`, `Label_vb`, `Label_eeh`, `POI_station` from script works (camera flies there, `Selected?` = true). → the POI logic is fine; the problem is the **click/hit-test in the UI**.
- Row template change (padding/font) is live at runtime.
- No Blueprint runtime errors in `Saved/Logs/ArchVizExplorer.log`.

**Suspects to check next:**
1. `BP_EntryList_Widget` click handling: "Ignore double tap (which usually occurs on the first click)" logic + `RetriggerableDelay` – may swallow clicks on some entries.
2. Something overlapping the lower part of the list (bottom task bar / `Border_Shadow` / BackgroundBlur / 3D POI screen-space widget) – use the Widget Reflector (Ctrl+Shift+W → "Pick Hit-Testable Widgets") on the entry to see which widget receives the click.
3. Label POIs for roads sit mid-road; the road label's screen-space `WidgetComponent` might cover the list area on screen.
4. Text with non-ASCII "–" (en dash) in the name – unlikely but test by renaming to "Mulund-Airoli Link Road".
5. `BP_Entry_Widget` uses `OnButtonReleased` (not OnClicked) – with touch/precise-click settings a drag inside the ScrollBox may cancel the release.

## 5. Plan / next steps (approved by user)
Full plan: `claude/surroundings_plan.md` in the Claude project "neelma" (copy of decisions below).
1. ✅ Phase 1 clean-up · ✅ Phase 2 MUST HAVE (pending the click bug above)
2. Phase 3 HIGH: Healthcare (Hira Mongi 2.5 km, Fortis 4.7, Apex 5.0, Jupiter 6.6), Retail (R Mall 4.4, Viviana 4.5, D-Mart 5.0, Korum 5.6), Education (JBCN 4.2, Singhania 6.5, Billabong 6.8)
3. Phase 4 Neighbourhood (clickable): Vardhaman Nagar, Spiro Tower, Superbia, Sanskar, Neelam Nagar
4. Upcoming Metro Station (6.1 km) – SKIPPED until client confirms which station (OSM shows "Mulund Check Naka Metro" under construction at 19.18346, 72.95096).
5. Menu categories should follow the brief (Immediate, Transport, Healthcare, Retail/Lifestyle, Education, Neighbourhood) – needs a widget edit + hospital icon.
6. Card text = client distance + drive time ("1.3 km · 3 min drive (1.6 km)"). Route colour per category.
7. Later: apartment selector (Filter_DataTable + BP_POI Filter + BP_UnitSearch + section view – rebuild for towers A–E), flat tour / interiors (user will provide details), replace KarlDetroit branding + Vagon ad widget.

## 6. Known limits / notes
- Daylight: `BP_AVE_SunSky_01` (SunPosition BP) – driving it from Site_Finishing failed ("no sun actor found"); BP_Time_Widget drives it at runtime.
- Google 3D Tiles are blurry at street level (source data); Cesium cut-out hides tiles visually but their collision remains inside the site.
- Some POIs got Z = site level because the map wasn't streamed at build time (traces missed) – re-run `Build_Surroundings.py` with the area loaded to re-seat them.
- `SourceArt/PolyHaven` (≈210 MB source JPGs) is NOT in git – it is re-downloaded automatically by `Apply_WindTunnel_Materials.py`; the imported textures (uassets) ARE in git.
- Source model package lives outside the repo: `C:\Users\Admin\Downloads\wind tunnel\wind tunnel` (Unreal/, Export_v4/, reference renders, design_data.json).
