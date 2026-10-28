# Graph Report - ArchVizExplorer-Neelam  (2026-10-27)

## Corpus Check
- 270 files · ~10,541,383 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1305 nodes · 1865 edges · 180 communities (109 shown, 71 thin omitted)
- Extraction: 96% EXTRACTED · 4% INFERRED · 0% AMBIGUOUS · INFERRED: 74 edges (avg confidence: 0.79)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `ab80572d`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- NeelamToolsLibrary.cpp
- connectivity_lib.py
- scene_builder.py
- UI_Theme.py
- pano_lumen.py
- FloorView_UI.py
- Amenity_Lighting.py
- NeelamWidgets.cpp
- NeelamFlatTour.cpp
- mrq_render.py
- pbr_mats.py
- Apply_WindTunnel_Materials.py
- make_far_massing.py
- build_railway.py
- lux.py
- strip.py
- NeelamWidgets.h
- Context_Backdrop.py
- NeelamTowerFloors.cpp
- Camera_Test.py
- NeelamTimeWidget.cpp
- NEELAM – project memory / resume context
- FName
- make_branding.py
- Amenity_Panoramas.py
- NeelamSurroundingsLibrary.cpp
- inspect_px.py
- lux_mat.py
- Amenity_Beautify.py
- FloorView_Setup.py
- Site_Finishing.py
- int32
- build_shell.py
- NeelamBridge.py
- NeelamTypes.h
- ue_tools.py
- FLinearColor
- NeelamTimeWidget.h
- NeelamFlatTour.h
- dress.py
- props.py
- bake_mats.py
- stitch_pano.py
- Build_HoloFX.py
- Fix_Landmarks.py
- ANeelamTowerFloors
- UNeelamGroundClampComponent::TickComponent
- ANeelamFlatTour
- Build_Amenities_POI.py
- Build_Facades.py
- make_site_outline.py
- pie_util.py
- Road glow static audit (27 Oct 2026)
- int32
- Room_render (UE 5.6) — Neelam 2BHK / 3BHK archviz
- capture.py
- build_amenity_fixtures.py
- Fix_Highway_Glow.py
- make_connectivity.py
- make_routes_osrm.py
- Ribbon_Clearance.py
- Route_Loops.py
- ui_preview.py
- Neelam work handoff — 27 Oct 2026
- NeelamOcclusionFade.cpp
- blend_export.py
- Balcony_Views.py
- Fix_CheckNaka_Ribbons.py
- Flatten_Roads.py
- Glow_Smooth.py
- Landmark_PIE.py
- make_building_footprints.py
- make_footprints.py
- Place_WindTunnel.py
- Plant_Vegetation.py
- Ribbon_Heights.py
- Ribbon_Snap.py
- Codex takeover: floating buildings and amenity panoramas (2026-10-27)
- ModuleRules
- Build_Railway.py
- Ground_Development.py
- make_massing_sel.py
- Ribbon_Tidy.py
- copyset.py
- topdown_sheet.py
- make_railway.py
- Night_Materials.py
- Plant_Area_Trees.py
- NeelamOcclusionFade.h
- cams.py
- Portable Neelam amenity render project (Unreal Engine 5.6)
- backdrop2hdr.py
- bake_heavy.sh
- grade_amenity_panos.py
- hdri_export.py
- Fix_CheckNaka_Road.py
- Floor_Gallery.py
- FloorView_StartCam.py
- make_road_data.py
- Mark_Massing_Removals.py
- Massing_PIE.py
- Package_Build.py
- Rail_Heights_PIE.py
- Rebuild_Restart.py
- Ribbon_Surface_PIE.py
- UNeelamTourWidget::NativeTick
- pano_spots.py
- bk_import.sh
- bk_prep.py
- kitchen_prep.py
- look_test.sh
- make_water_normal.py
- pano_amenities.sh
- pano_amenities2.sh
- pano_amenities3.sh
- pano_contact.py
- pano_lumen_spot.sh
- pano_preview.sh
- pano_preview_all.sh
- pano_view.py
- python.sh
- render_amenities.sh
- shot.sh
- topdown_amenities.sh
- ue.sh
- view_arc.py
- Clean_PodiumAB_Parapet.py
- Depth_PIE.py
- Fix_CheckNaka_Import.py
- fix_ground_dem.py
- Import_Massing.py
- Import_Roads.py
- Make_PosPP.py
- make_view_cone.py
- Place_DeckABFill.py
- Place_PodiumAB_Parapet.py
- Place_RoadPoles.py
- PosPP_Shot.py
- pv.sh
- Road_Align_PIE.py
- Road_Surface_PIE.py
- select_textured.py
- ui_comp.py
- Verify_Ribbons.py
- ribbon_ground_check.py
- Ribbon_Rebuild_Z.py
- NeelamFont
- Ribbon_Fit.py
- Ribbon_Valleys.py
- Ribbon_Deck_Check.py
- Route_Audit.py
- Ribbon_Covered.py
- Route_Select_PIE.py
- ui_press.py
- Ribbon_Tangents.py
- Infra_Ground_PIE.py

## God Nodes (most connected - your core abstractions)
1. `build_items()` - 15 edges
2. `UBlueprint` - 14 edges
3. `B` - 14 edges
4. `build_floor_view()` - 14 edges
5. `build_tour()` - 14 edges
6. `Modified()` - 13 edges
7. `build_hotspot()` - 13 edges
8. `style_text()` - 13 edges
9. `NEELAM – project memory / resume context` - 13 edges
10. `build_surface_master()` - 12 edges

## Surprising Connections (you probably didn't know these)
- `place()` --indirect_call--> `root()`  [INFERRED]
  Scripts/Neelam/Build_Site_Outline.py → PortableRender_UE56/Content/Python/scene_builder.py
- `_faces()` --calls--> `pick()`  [INFERRED]
  Scripts/Neelam/FloorView_UI.py → PortableRender_UE56/Content/Python/inspect_px.py
- `master()` --calls--> `tex()`  [INFERRED]
  PortableRender_UE56/Content/Python/lux_mat.py → Scripts/Neelam/UI_Theme.py
- `ground()` --indirect_call--> `root()`  [INFERRED]
  Scripts/Neelam/Site_Finishing.py → PortableRender_UE56/Content/Python/scene_builder.py
- `step_materials()` --calls--> `mi()`  [INFERRED]
  Scripts/Neelam/Amenity_Lighting.py → Scripts/Neelam/Place_Roads.py

## Import Cycles
- None detected.

## Communities (180 total, 71 thin omitted)

### Community 0 - "NeelamToolsLibrary.cpp"
Cohesion: 0.08
Nodes (66): FJsonObject, FJsonValue, FString, FVector2D, CloneRec(), CopyEditableProps(), FGeometry, FName (+58 more)

### Community 1 - "connectivity_lib.py"
Cohesion: 0.06
Nodes (35): Apply Verify_Ribbons.py results: fill holes in Data/surface_dense.json (> 3 m be, build_spline(), Neelam - surroundings / connectivity builder (run INSIDE Unreal via the bridge)., set_info(), spawn_poi(), spawn_route(), txt(), cell() (+27 more)

### Community 2 - "scene_builder.py"
Cohesion: 0.07
Nodes (48): capture(), _floor(), _level(), place(), Dress amenity levels with props the same artist already modelled in OTHER amenit, index = which match to use as the prop's anchor (0 = first)., Place prop in the OPEN level at top-down grid cell coords (u, v in 0..10), stand, _arc_mesh() (+40 more)

### Community 3 - "UI_Theme.py"
Cohesion: 0.18
Nodes (30): Upcoming project' marker where Towers A and B stood (30 Sep, client: A/B removed, _divider(), _pill_button(), NEELAM premium redesign of the template UI (run step by step via NeelamBridge)., _round_icon_button(), _section_title(), step_compass(), step_info() (+22 more)

### Community 4 - "pano_lumen.py"
Cohesion: 0.08
Nodes (27): add_sun(), amenity_spot(), _bounds(), cleanup_orphans(), finish_batch(), Fast Lumen panoramas (minutes, not hours) - same 6-cube-face rig as pano.py but, # NOTE: tick_batch() must be called from SEPARATE bridge jobs (separate `bash ue, Ortho top view of the open level -> Saved/Pano/_topdown/<name>.png; returns the (+19 more)

### Community 5 - "FloorView_UI.py"
Cohesion: 0.24
Nodes (23): B, _blur_panel(), brush(), build_all(), build_floor_view(), build_hotspot(), build_items(), build_tab() (+15 more)

### Community 6 - "Amenity_Lighting.py"
Cohesion: 0.13
Nodes (19): _actors(), _clear(), _l2w(), _light(), _mesh(), _new_material(), _on_node(), Amenity deck lighting = client lighting plan "Amenities Floor design.pdf" (7th p (+11 more)

### Community 7 - "NeelamWidgets.cpp"
Cohesion: 0.10
Nodes (7): UNeelamFloorViewWidget::HandleFlatPanorama(), UNeelamFloorViewWidget::HandleFloorHover(), UNeelamFloorViewWidget::HandleFloorRow(), UNeelamFloorViewWidget::HandleFloorUnhover(), UNeelamFloorViewWidget::HandleTowerTab(), UNeelamTourWidget::HandleRoom(), UNeelamListItem

### Community 8 - "NeelamFlatTour.cpp"
Cohesion: 0.10
Nodes (11): APlayerController, ANeelamFlatTour::CallSwitchPawn(), ANeelamFlatTour::EnterPanorama(), ANeelamFlatTour::PC(), ANeelamFlatTour::PollMenuTab(), ANeelamFlatTour::SetMasterMenuVisible(), ANeelamFlatTour::TickFly(), ANeelamFlatTour::UpdatePicking() (+3 more)

### Community 9 - "mrq_render.py"
Cohesion: 0.11
Nodes (18): Claude file bridge for Unreal Editor. Watches <Project>/Saved/ClaudeBridge/inbox, _run_one(), start(), _tick(), _write_json(), make_sequences(), _pt(), Final stills through Movie Render Queue (needs the MovieRenderPipeline plugin, e (+10 more)

### Community 10 - "pbr_mats.py"
Cohesion: 0.15
Nodes (22): assign(), auto(), fix_worldgrid(), flat(), _fn(), instance(), _is_white(), master() (+14 more)

### Community 11 - "Apply_WindTunnel_Materials.py"
Cohesion: 0.24
Nodes (15): assign(), build_emissive_master(), build_glass_master(), build_instances(), build_surface_master(), download_all(), G, get_or_create_material() (+7 more)

### Community 12 - "make_far_massing.py"
Cohesion: 0.13
Nodes (19): area(), dp(), fetch(), import_far(), inside(), make_far_build(), Context buildings round the FAR landmarks (4 Oct, client: 'landmarks without sur, massing_far_sel + massing_far_heights -> massing_far_build.json (same rules as m (+11 more)

### Community 13 - "build_railway.py"
Cohesion: 0.14
Nodes (16): beam(), box(), C(), ck(), cross_offsets(), ground(), offsets(), quad() (+8 more)

### Community 14 - "lux.py"
Cohesion: 0.12
Nodes (18): depth_pass(), environment(), glass_material(), hdri_cube(), lighting(), Luxury look pass for the Neelam levels (on top of scene_builder's straight impor, Rebuild /Game/Neelam/Shared/M_Glass as Thin Translucent (correct in Lumen AND th, Warm luxury mood: interior lights to <kelvin>, emissive strips tinted warm, stro (+10 more)

### Community 15 - "strip.py"
Cohesion: 0.16
Nodes (7): detect(), detect_row(), profiles(), best_cam(), img(), sample(), strip()

### Community 16 - "NeelamWidgets.h"
Cohesion: 0.12
Nodes (14): SWidget, TSharedRef, UNeelamBalconyGallery::RebuildWidget(), ANeelamTowerFloors, UBorder, UButton, UCanvasPanel, UImage (+6 more)

### Community 17 - "Context_Backdrop.py"
Cohesion: 0.16
Nodes (15): build_mesh(), ccw(), place(), Neelam - platform, lawn and Cesium cut-out following the REAL site boundary (cur, _amenity_dressing(), arm(), export(), face() (+7 more)

### Community 18 - "NeelamTowerFloors.cpp"
Cohesion: 0.18
Nodes (12): FTransform, ANeelamTowerFloors::BaseState(), ANeelamTowerFloors::FindFloorIndexByNumber(), ANeelamTowerFloors::GetFacadePoint(), ANeelamTowerFloors::GetFloorCenter(), ANeelamTowerFloors::GetTowerCenter(), ANeelamTowerFloors::GetTowerTopZ(), ANeelamTowerFloors::OnConstruction() (+4 more)

### Community 19 - "Camera_Test.py"
Cohesion: 0.14
Nodes (10): fly(), Records the pawn while the template flies to a POI (Select_POI). fly(label, anti, arm(), Explorer-camera smoothness / wall test (PIE, through the NeelamBridge). Written, Run ~1 s after start(): anti-tunnel back on (setting it from the tick hit a stal, start(), existing(), Neelam - capture review screenshots of the Wind Tunnel development (run INSIDE U (+2 more)

### Community 21 - "NEELAM – project memory / resume context"
Cohesion: 0.14
Nodes (13): 10. Premium UI redesign (29 Sep 2026, evening – new PC C:\Users\rosha\...), 11. Branding (5 Oct 2026), 12. Client review fixes (11 Oct 2026), 1. What this project is, 2. Live editor link – NeelamBridge (IMPORTANT for AI-assisted work), 3. Done so far, 4. ⚠️ OPEN ISSUE – Surroundings list entry not clickable, 5. Plan / next steps (approved by user) (+5 more)

### Community 22 - "FName"
Cohesion: 0.29
Nodes (13): ANeelamFlatTour::ActivateFloorView(), ANeelamFlatTour::DeactivateFloorView(), ANeelamFlatTour::FocusPawn(), ANeelamFlatTour::SetPoiLayerHidden(), ANeelamFlatTour::StartTour(), CallNoParams(), FName, FVector (+5 more)

### Community 23 - "make_branding.py"
Cohesion: 0.25
Nodes (13): gold_fill(), icon_master(), main(), NEELAM branding: app icon, game + editor splash, project thumbnail (run with pla, Brushed champagne gold: light top-left -> deeper bottom-right., Letter-spaced text (UE 'spacing' look). Returns width., Line-art of the three Wind Tunnel towers on the podium (fallback backdrop)., sans() (+5 more)

### Community 24 - "Amenity_Panoramas.py"
Cohesion: 0.23
Nodes (12): assign(), audit_assignments(), export_client(), import_all(), import_ue(), Neelam - 360 panoramas for the Amenities pins (re-run safe). HOW TO ADD ONE:, Preview each amenity pin's panorama assignment without changing or saving the le, suffix "_UE" + src SourceArt/.../Panoramas/UE = the Room_render renders, importe (+4 more)

### Community 25 - "NeelamSurroundingsLibrary.cpp"
Cohesion: 0.39
Nodes (11): AActor, CallPoiEvent(), FName, TCHAR, UObject, HideAllSurroundingsRoutes(), UNeelamSurroundingsLibrary::HideTaggedPOIs(), UNeelamSurroundingsLibrary::IsolateSurroundingsRoute() (+3 more)

### Community 26 - "inspect_px.py"
Cohesion: 0.24
Nodes (10): ceiling_fixtures(), gap_up(), pick(), Debug helpers: what is under a pixel of a camera view, and how far it sits from, Distance from the actor's top to the next surface above (ceiling)., Small objects near the ceiling: report gap between their top and the ceiling sur, Raise ceiling light fittings flush to the ceiling; light actors just under each, snap_ceiling_lights() (+2 more)

### Community 27 - "lux_mat.py"
Cohesion: 0.23
Nodes (11): library(), master(), mi(), Luxury material palette (M_LuxSurface + instances) and swaps.     import lux_ma, Create/refresh /Game/Neelam/Shared/Lux/MI_<name>. Texture args are paths under S, Statuario floor slabs, Nero Marquina accent, smoked walnut, satin brass., mapping: {existing material name (or prefix + '*'): library key}. Swaps on every, World-projected versions for meshes with poor UVs (kitchen set): no grout, big t (+3 more)

### Community 28 - "Amenity_Beautify.py"
Cohesion: 0.24
Nodes (10): _import_tex(), _light(), _master(), _mi(), Amenity deck beautify (29 Sep): realistic Poly Haven CC0 trees replace the low-p, M_Neelam_Emissive: emissive x (1 + NightBoost x Effects) - fixture heads and poo, step_emissive_night(), step_grass() (+2 more)

### Community 29 - "FloorView_Setup.py"
Cohesion: 0.24
Nodes (9): _asset(), _pp(), Floor View + flat tour setup (runs inside UE via NeelamBridge). Re-runnable., _rooms(), _root(), step_material(), step_tables(), step_towers() (+1 more)

### Community 30 - "Site_Finishing.py"
Cohesion: 0.33
Nodes (10): actors_of(), by_label(), cls(), cutout(), daylight(), gp(), ground(), Neelam - site finishing for the Wind Tunnel development (run INSIDE Unreal, afte (+2 more)

### Community 31 - "int32"
Cohesion: 0.29
Nodes (11): ANeelamFlatTour::ApplyRoom(), ANeelamFlatTour::FindBalconyView(), ANeelamFlatTour::FindFloorGalleryView(), ANeelamFlatTour::GetFlatsOnFloor(), ANeelamFlatTour::OpenFloorGallery(), ANeelamFlatTour::ShowRoom(), int32, TArray (+3 more)

### Community 32 - "build_shell.py"
Cohesion: 0.24
Nodes (8): box_uv(), cuboid(), pane(), Build an apartment shell from a traced layout JSON (Tools/layouts/<unit>.json)., World-scale box projection: each face takes the two axes it doesn't face., rect(), X(), Y()

### Community 33 - "NeelamBridge.py"
Cohesion: 0.31
Nodes (9): _capture(), NeelamBridge - lets Claude work live in this editor session.  Starts automatical, Queue a viewport screenshot. location/rotation: unreal.Vector / unreal.Rotator (, Render through a hidden SceneCapture2D (works even when the editor is in the bac, _run_job(), shot(), _shots_tick(), _tick() (+1 more)

### Community 34 - "NeelamTypes.h"
Cohesion: 0.22
Nodes (8): ANeelamFlatTour::GetFlat(), ANeelamFlatTour::GetUnitType(), ANeelamFlatTour::ResolveRoomTexture(), ANeelamFlatTour::SetSphereTexture(), FNeelamFlatRow(), FNeelamRoom(), FNeelamUnitTypeRow(), UTexture

### Community 35 - "ue_tools.py"
Cohesion: 0.31
Nodes (6): cam(), find(), _r(), Helpers for bridge jobs:  import ue_tools as T   T.scene()              -> level, scene(), _v()

### Community 36 - "FLinearColor"
Cohesion: 0.33
Nodes (6): FLinearColor, FText, UNeelamBalconyGallery::Refresh(), UNeelamListItem::SetBadge(), UNeelamListItem::SetTexts(), UNeelamTimeWidget()

### Community 37 - "NeelamTimeWidget.h"
Cohesion: 0.22
Nodes (8): UNeelamListItem::SetThumb(), UButton, UImage, UMaterialParameterCollection, USkyLightComponent, USlider, UTextBlock, UTexture2D

### Community 38 - "NeelamFlatTour.h"
Cohesion: 0.22
Nodes (7): ACameraActor, ANeelamTowerFloors, APawn, UDataTable, UNeelamFloorViewWidget, UNeelamTourWidget, UWidget

### Community 39 - "dress.py"
Cohesion: 0.40
Nodes (5): classify(), Offline report on Data/infra_ground.json (Infra_Ground_PIE.py): broken / buried, merge consecutive samples of the same (id, issue): -> (kind, id, issue, start d,, runs(), selftest()

### Community 40 - "props.py"
Cohesion: 0.28
Nodes (8): import_prop(), _mesh(), picture_light(), place(), Decor props from BlenderKit (converted by Tools/bk_import.sh -> SourceArt/Props/, Interchange-import SourceArt/Props/<name>/scene.gltf as assets, then glass/emiss, rot: optional unreal.Rotator overriding yaw. Re-running with the same label move, Linear wall-wash light (rect light) grazing down a wall/artwork.

### Community 41 - "bake_mats.py"
Cohesion: 0.22
Nodes (3): needs(), Bake Blender materials that glTF can't express (colour mixes, ramps, procedural,, True when Principled <sock> is driven by something other than a lone image textu

### Community 42 - "stitch_pano.py"
Cohesion: 0.25
Nodes (4): After rendering: Saved/Final/_raw -> Saved/Final   Stills/8K/<name>_8K.png, Stil, Cube faces (Unreal cameras, 92 deg FOV) -> equirectangular panorama. python stit, stitch(), _test()

### Community 43 - "Build_HoloFX.py"
Cohesion: 0.39
Nodes (8): _build(), _material(), Neelam - premium hologram highlight materials (re-run safe).   M_Neelam_HoloFX, put MI_Neelam_HoloFX on every placed BP_POI highlight box (the BP builds its dyn, run(), step_apply_pois(), step_floor_material(), step_poi_material()

### Community 44 - "Fix_Landmarks.py"
Cohesion: 0.22
Nodes (5): frame(), Landmark corrections after the client review (11 Oct 2026). Run AFTER Place_Land, mesh-local bbox + world centre / axes / half sizes (cm), separating-axis distance between two convex quads (cm, <= 0 = overlap), sat_gap()

### Community 45 - "ANeelamTowerFloors"
Cohesion: 0.25
Nodes (7): ANeelamFlatTour::FindTower(), ANeelamFlatTour::HoverFloor(), ANeelamFlatTour::SelectFloor(), ANeelamTowerFloors(), UInstancedStaticMeshComponent, UMaterialInterface, UStaticMesh

### Community 46 - "UNeelamGroundClampComponent::TickComponent"
Cohesion: 0.29
Nodes (6): ELevelTick, FActorComponentTickFunction, FVector, UNeelamGroundClampComponent::TerrainZ(), UNeelamGroundClampComponent::TickComponent(), UWorld

### Community 47 - "ANeelamFlatTour"
Cohesion: 0.32
Nodes (8): ANeelamFlatTour::GetFlatTour(), NeighbourGalleryFloor(), UNeelamBalconyGallery::HandleClose(), UNeelamBalconyGallery::HandleNextFloor(), UNeelamBalconyGallery::HandlePrevFloor(), UNeelamFloorViewTab::NativeDestruct(), UNeelamFloorViewWidget::InitFloorView(), ANeelamFlatTour

### Community 48 - "Build_Amenities_POI.py"
Cohesion: 0.39
Nodes (7): Neelam - Amenities menu pins (BP_POI) on the CDE amenity deck + AB roof deck.  R, rename the 3rd list Transportation -> Facilities, set tags / colours, run(), set_info(), step_lists(), step_pois(), txt()

### Community 49 - "Build_Facades.py"
Cohesion: 0.43
Nodes (7): _custom(), _mat(), Neelam - realistic facades on the context buildings around the site (30 Sep, cli, run(), step_import(), step_materials(), _tex()

### Community 50 - "make_site_outline.py"
Cohesion: 0.32
Nodes (6): loc(), Builds Data/site_outline.json from the model's real site boundary (design_data.j, ring(), tris(), along(), Candidate tree/bush spots from the real site boundary (local cm of Neelam_WindTu

### Community 51 - "pie_util.py"
Cohesion: 0.36
Nodes (7): click_widget(), pc(), PIE helpers for NeelamBridge jobs., screenshot WITH UI -> Saved/Screenshots/WindowsEditor/<name>*.png (async, next f, rect(), shot(), world()

### Community 52 - "Road glow static audit (27 Oct 2026)"
Cohesion: 0.29
Nodes (6): Height values in checked-in road scripts, Likely Eastern Express Highway segment near the road label, Practical follow-up for Claude, Road glow static audit (27 Oct 2026), Static approximation of which deck IDs the key-glow alignment uses, What the existing fix actually targets

### Community 53 - "int32"
Cohesion: 0.40
Nodes (5): int32, UNeelamBalconyGallery::ShowView(), UNeelamFloorViewWidget::SetHoveredFloor(), UNeelamFloorViewWidget::ShowFloorDetail(), UNeelamTourWidget::SetActiveRoom()

### Community 54 - "Room_render (UE 5.6) — Neelam 2BHK / 3BHK archviz"
Cohesion: 0.29
Nodes (6): Editor bridge, Luxury pass (Content/Python/lux.py) — in progress, Pipeline (re-runnable per scene, name = "2BHK" / "3BHK"), Progress, Room_render (UE 5.6) — Neelam 2BHK / 3BHK archviz, Units / matching

### Community 55 - "capture.py"
Cohesion: 0.38
Nodes (6): finish(), Offscreen camera render with Lumen (works with the editor unfocused). Two bridge, One capture; call from separate bridge jobs so real frames pass in between (Lume, start(), tick(), _world()

### Community 56 - "build_amenity_fixtures.py"
Cohesion: 0.38
Nodes (4): box(), cyl(), frustum along +Z (UE cm), optional transform M (UE space), _xf()

### Community 57 - "Fix_Highway_Glow.py"
Cohesion: 0.29
Nodes (3): deck_at(), Key-road glow lines + route ribbons vs the 3D road decks (29 Sep). Problem: Roa, (deck z, centreline x, y, tangent, half width m) of the carriageway under (x, y)

### Community 58 - "make_connectivity.py"
Cohesion: 0.43
Nodes (5): length(), m(), ok(), OSM ways + OSRM routes -> clean lat/lon polylines for the Phase 2 connectivity l, simplify()

### Community 59 - "make_routes_osrm.py"
Cohesion: 0.33
Nodes (3): length(), m(), Drive routes site -> landmarks via OSRM (real roads) -> Data/connectivity_<phase

### Community 60 - "Ribbon_Clearance.py"
Cohesion: 0.48
Nodes (6): deficits(), inside(), lift(), Ribbon clearance pass (30 Sep, client): no route / road glow / traffic ribbon ma, rebuild(), run()

### Community 61 - "Route_Loops.py"
Cohesion: 0.48
Nodes (6): find_loops(), pdist(), Remove U-turn detour loops from the landmark routes (30 Sep, client: "splines cu, rebuild(), run(), segd()

### Community 62 - "ui_preview.py"
Cohesion: 0.43
Nodes (5): pc(), UI previews without the user: render the live PIE MasterMenu off-screen + a scen, scene(), viewport_widgets(), world()

### Community 63 - "Neelam work handoff — 27 Oct 2026"
Cohesion: 0.33
Nodes (5): Current task state, Neelam work handoff — 27 Oct 2026, Portable rendering at home, Render folders, Resume this project

### Community 64 - "NeelamOcclusionFade.cpp"
Cohesion: 0.33
Nodes (3): ELevelTick, FActorComponentTickFunction, UNeelamOcclusionFadeComponent::TickComponent()

### Community 65 - "blend_export.py"
Cohesion: 0.33
Nodes (3): Blender -> Unreal export.  NEVER saves the .blend. blender --background --facto, Visible in the viewport AND in renders (object + every parent collection)., rendered()

### Community 66 - "Balcony_Views.py"
Cohesion: 0.53
Nodes (5): _files(), _import(), Balcony photo galleries + top-floor panorama (client, 2 Oct 2026). Source: C:\\, step_import(), step_views()

### Community 67 - "Fix_CheckNaka_Ribbons.py"
Cohesion: 0.33
Nodes (3): deck_z(), After Fix_CheckNaka_Road.py raised the plaza deck up to 2 m, the road glow / rou, deck top under (x, y); extra widens the corridor (the EEH glow runs on the media

### Community 68 - "Flatten_Roads.py"
Cohesion: 0.33
Nodes (3): Data/road_build.json: remove the bogus dips from the carriageway profiles (29 Se, nodes within geodesic distance rad of n (along carriageways + junction links), within()

### Community 69 - "Glow_Smooth.py"
Cohesion: 0.47
Nodes (5): offsets(), Smooth the key-road glow lines Road_eeh / Road_vb / Road_mar sideways (1 Oct, cl, zig-zag only: a point off its neighbours' chord by > 0.8 m whose neighbour is of, rebuild(), run()

### Community 70 - "Landmark_PIE.py"
Cohesion: 0.33
Nodes (3): frame(), Real ground + roof heights around each landmark from the photogrammetry, plus a, centre, unit axes, half sizes (cm) of the landmark mesh footprint

### Community 73 - "Place_WindTunnel.py"
Cohesion: 0.53
Nodes (5): find_label(), main(), Neelam - place the Wind Tunnel development on the construction plot (UE 5.5).  R, rot2(), trace_z()

### Community 74 - "Plant_Vegetation.py"
Cohesion: 0.60
Nodes (5): clear_above(), down(), Neelam - optimised trees and bushes around and inside the site (run INSIDE Unrea, trace(), valid()

### Community 75 - "Ribbon_Heights.py"
Cohesion: 0.53
Nodes (5): clean(), deck(), inside(), Ribbon spline heights from Data/ribbon_surface.json (Ribbon_Surface_PIE.py) - ed, win()

### Community 76 - "Ribbon_Snap.py"
Cohesion: 0.53
Nodes (5): lift(), nearest(), Ribbon snap to the built carriageways (30 Sep, client: "splines go out of the ro, rebuild(), run()

### Community 77 - "Codex takeover: floating buildings and amenity panoramas (2026-10-27)"
Cohesion: 0.40
Nodes (4): Amenity panoramas, Codex takeover: floating buildings and amenity panoramas (2026-10-27), Floating facade chunk, Next checks

### Community 78 - "ModuleRules"
Cohesion: 0.40
Nodes (3): ModuleRules, NeelamRuntime, NeelamTools

### Community 79 - "Build_Railway.py"
Cohesion: 0.60
Nodes (4): Railway corridor in the level (4 Oct, client 'railway is a flat photo'). Pipelin, run(), step_import(), step_materials()

### Community 82 - "Ribbon_Tidy.py"
Cohesion: 0.60
Nodes (4): bad_points(), Ribbon tidy (1 Oct): remove spline points that make hooks / kinks.  - duplicate, rebuild(), run()

### Community 85 - "make_railway.py"
Cohesion: 0.67
Nodes (3): fetch(), _geo(), Central Railway line + Mulund station in 3D (4 Oct, client: 'railway is just a f

### Community 168 - "ribbon_ground_check.py"
Cohesion: 0.36
Nodes (6): deck_z(), load_roads(), Offline (plain py): every ribbon sample vs its REAL ground (27 Oct). Ground = ou, deck top under (x, y) of a carriageway the ribbon runs along (direction tx, ty),, run(), selftest()

### Community 169 - "Ribbon_Rebuild_Z.py"
Cohesion: 0.33
Nodes (4): bridge(), Rebuild every ribbon's spline heights from the measured ground in ONE determinis, ground with deck gaps (<= GAP, deck on both sides) filled linearly between the r, selftest()

### Community 170 - "NeelamFont"
Cohesion: 0.33
Nodes (6): FSlateFontInfo, FName, TCHAR, NeelamFont(), UNeelamFloorViewWidget::ShowTower(), UNeelamTourWidget::SetupFlat()

### Community 172 - "Ribbon_Valleys.py"
Cohesion: 0.50
Nodes (3): closing(), Fill short valleys in ribbon heights (27 Oct): a ribbon must not dive into a gap, selftest()

### Community 173 - "Ribbon_Deck_Check.py"
Cohesion: 0.50
Nodes (3): along(), Ribbon ground = max(photogrammetry map, our road deck MESH the ribbon runs along, direction of the carriageway centreline nearest to (x, y) parallel to (tx, ty)?

### Community 178 - "Ribbon_Tangents.py"
Cohesion: 0.40
Nodes (3): Smooth tangents on every ribbon spline (27 Oct, client: "highlight dotted / brok, P: list of (x, y, z) -> list of tangents, tangents()

## Knowledge Gaps
- **69 isolated node(s):** `ANeelamTowerFloors`, `UWidget`, `UNeelamFloorViewWidget`, `UNeelamTourWidget`, `UDataTable` (+64 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **71 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `ANeelamFlatTour` connect `ANeelamFlatTour` to `NeelamWidgets.h`, `NeelamFont`, `FLinearColor`, `UNeelamGroundClampComponent::TickComponent`?**
  _High betweenness centrality (0.007) - this node is a cross-community bridge._
- **Why does `master()` connect `lux_mat.py` to `UI_Theme.py`?**
  _High betweenness centrality (0.006) - this node is a cross-community bridge._
- **Why does `tex()` connect `UI_Theme.py` to `lux_mat.py`?**
  _High betweenness centrality (0.006) - this node is a cross-community bridge._
- **What connects `ANeelamTowerFloors`, `UWidget`, `UNeelamFloorViewWidget` to the rest of the system?**
  _69 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `NeelamToolsLibrary.cpp` be split into smaller, more focused modules?**
  _Cohesion score 0.08340649692712906 - nodes in this community are weakly interconnected._
- **Should `connectivity_lib.py` be split into smaller, more focused modules?**
  _Cohesion score 0.057971014492753624 - nodes in this community are weakly interconnected._
- **Should `scene_builder.py` be split into smaller, more focused modules?**
  _Cohesion score 0.06966618287373004 - nodes in this community are weakly interconnected._