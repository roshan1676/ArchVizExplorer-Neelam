#include "NeelamSurroundingsLibrary.h"
#include "EngineUtils.h"
#include "Engine/World.h"
#include "Kismet/GameplayStatics.h"

// Route/Traffic actors carry two runtime (non-editor-only) tags set by Build_Surroundings.py / Build_Traffic.py:
//   "Neelam_Route"       - marks it as a per-landmark route/traffic actor (vs. road glows, poles, POIs)
//   "LM_<id>"            - which landmark it belongs to, e.g. "LM_fortis"
// Tags are runtime-safe (unlike GetActorLabel(), which is editor-only and stripped from packaged builds).

void UNeelamSurroundingsLibrary::IsolateSurroundingsRoute(UObject* WorldContextObject, FName LandmarkId)
{
    UWorld* World = GEngine ? GEngine->GetWorldFromContextObject(WorldContextObject, EGetWorldErrorMode::ReturnNull) : nullptr;
    if (!World) return;
    const FName WantedTag = FName(*(TEXT("LM_") + LandmarkId.ToString()));
    for (TActorIterator<AActor> It(World); It; ++It)
    {
        AActor* A = *It;
        if (!A) continue;
        // key-road glow lines (Road_vb/eeh/mar) are shared context, not a landmark path - hide them while a single
        // route is isolated so only the one path to the selected place reads, same as the per-landmark routes.
        if (A->ActorHasTag(TEXT("Neelam_RoadGlow"))) { A->SetActorHiddenInGame(true); continue; }
        if (!A->ActorHasTag(TEXT("Neelam_Route"))) continue;
        A->SetActorHiddenInGame(!A->ActorHasTag(WantedTag));
    }
}

void UNeelamSurroundingsLibrary::ShowAllSurroundingsRoutes(UObject* WorldContextObject)
{
    UWorld* World = GEngine ? GEngine->GetWorldFromContextObject(WorldContextObject, EGetWorldErrorMode::ReturnNull) : nullptr;
    if (!World) return;
    for (TActorIterator<AActor> It(World); It; ++It)
    {
        AActor* A = *It;
        if (!A || !(A->ActorHasTag(TEXT("Neelam_Route")) || A->ActorHasTag(TEXT("Neelam_RoadGlow")))) continue;
        A->SetActorHiddenInGame(false);
    }
}

void UNeelamSurroundingsLibrary::IsolateSurroundingsRouteForActor(UObject* WorldContextObject, AActor* Poi)
{
    if (!Poi) return;
    static const FString Prefix = TEXT("LM_");
    for (const FName& Tag : Poi->Tags)
    {
        const FString TagStr = Tag.ToString();
        if (TagStr.StartsWith(Prefix))
        {
            IsolateSurroundingsRoute(WorldContextObject, FName(*TagStr.RightChop(Prefix.Len())));
            return;
        }
    }
}
