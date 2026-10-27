"""Build a separate, shared rooftop recreation level from the individual amenity maps.
Original amenity maps and source textures are not modified."""
import unreal, json, os, math
import scene_builder as SB
import pano_lumen as PL

PROJ=unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
DATA=os.path.join(PROJ,"Saved","ClaudeBridge","outbox","_shared_amenity_sources.json")
NAME="Amenity_Shared_Outdoor"
LAYOUT={
 "Pool":(0,0,178.5), "Court":(5500,0,173.9), "PickleBall":(-5500,0,180.0),
 "JoggingTrack":(0,6500,165.5), "PartyLawn":(0,-6500,165.8),
 "Pavilion":(5500,5500,183.0), "Senior":(-5500,5500,181.8),
 "Path":(5500,-5500,176.6),
 "Lightings":(0,-3000,178.0)
}

def build():
    data=json.load(open(DATA,encoding="utf-8"))
    SB.new_level(NAME)
    act=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    eal=unreal.EditorAssetLibrary
    totals={}
    for unit,target in LAYOUT.items():
        src=data[unit]; s=src["spot"]; tx,ty,tz=target
        count=0
        for it in src["actors"]:
            mesh=eal.load_asset(it["mesh"])
            if not mesh: continue
            lx,ly,lz=it["loc"]
            loc=unreal.Vector(tx+(lx-s[0]),ty+(ly-s[1]),tz+(lz-s[2]))
            rr=it["rot"]
            rot=unreal.Rotator(roll=rr[0],pitch=rr[1],yaw=rr[2])
            a=act.spawn_actor_from_class(unreal.StaticMeshActor,loc,rot)
            if not a: continue
            comp=a.static_mesh_component; comp.set_static_mesh(mesh)
            for i,mp in enumerate(it.get("mats",[])):
                if mp:
                    mat=eal.load_asset(mp)
                    if mat: comp.set_material(i,mat)
            a.set_actor_scale3d(unreal.Vector(*it["scale"]))
            try: a.set_actor_label((unit+"_"+it["label"])[:96])
            except: pass
            try: a.set_folder_path("SharedOutdoor/"+unit)
            except: pass
            count+=1
        totals[unit]=count
    env=SB.environment(NAME)
    sun=PL.add_sun(4.2,82.2,-55.5,(1.0,0.96,0.90))
    for a in act.get_all_level_actors():
        if isinstance(a,unreal.DirectionalLight) and "pano_sun" in [str(t) for t in a.tags]:
            a.light_component.set_editor_property("light_source_angle",2.0)
        if isinstance(a,unreal.SkyLight):
            c=a.light_component
            c.set_editor_property("intensity",float(c.get_editor_property("intensity"))*1.25)
            c.recapture_sky()
        if isinstance(a,unreal.PostProcessVolume):
            s=a.get_editor_property("settings"); s.set_editor_property("override_auto_exposure_bias",True); s.set_editor_property("auto_exposure_bias",0.35); a.set_editor_property("settings",s)
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    return {"level":"/Game/Neelam/"+NAME+"/L_"+NAME,"actors":totals,"total":sum(totals.values()),"environment":env,"sun":sun,"layout":LAYOUT}