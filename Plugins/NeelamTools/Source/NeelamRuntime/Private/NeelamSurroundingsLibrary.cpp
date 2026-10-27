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
        // road pins (Label_vb/eeh/mar) carry LM_<road>: keep ONLY that road's glow; any other selection hides them all
        if (A->ActorHasTag(TEXT("Neelam_RoadGlow"))) { A->SetActorHiddenInGame(!A->ActorHasTag(WantedTag)); continue; }
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

// every route / traffic strip / key-road glow hidden (selection without a route of its own, e.g. an amenity pin)
static void HideAllSurroundingsRoutes(UObject* WorldContextObject)
{
    UWorld* World = GEngine ? GEngine->GetWorldFromContextObject(WorldContextObject, EGetWorldErrorMode::ReturnNull) : nullptr;
    if (!World) return;
    for (TActorIterator<AActor> It(World); It; ++It)
        if (*It && (It->ActorHasTag(TEXT("Neelam_Route")) || It->ActorHasTag(TEXT("Neelam_RoadGlow")))) It->SetActorHiddenInGame(true);
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
    // BP_POI Select_POI runs ShowAllSurroundingsRoutes first: a pin without LM_<id> (amenities) used to leave ALL 35
    // routes on (client 27 Oct: "only one path shall highlight")
    HideAllSurroundingsRoutes(WorldContextObject);
}

// BP_POI's Show_POI / Hide_POI are parameterless Blueprint custom events: call them by name.
static void CallPoiEvent(AActor* A, const TCHAR* EventName)
{
    if (UFunction* F = A->FindFunction(FName(EventName)))
        if (F->ParmsSize == 0) A->ProcessEvent(F, nullptr);
}

void UNeelamSurroundingsLibrary::HideTaggedPOIs(UObject* WorldContextObject, FName Tag)
{
    UWorld* World = GEngine ? GEngine->GetWorldFromContextObject(WorldContextObject, EGetWorldErrorMode::ReturnNull) : nullptr;
    if (!World) return;
    HideAllSurroundingsRoutes(WorldContextObject);   // Amenities menu: a route left on from Surroundings stayed visible
    for (TActorIterator<AActor> It(World); It; ++It)
        if (*It && It->ActorHasTag(Tag)) CallPoiEvent(*It, TEXT("Hide_POI"));
}

void UNeelamSurroundingsLibrary::IsolateTaggedPOI(UObject* WorldContextObject, AActor* Poi, FName Tag)
{
    if (!Poi || !Poi->ActorHasTag(Tag)) return;
    UWorld* World = Poi->GetWorld();
    if (!World) return;
    for (TActorIterator<AActor> It(World); It; ++It)
        if (*It && *It != Poi && It->ActorHasTag(Tag)) CallPoiEvent(*It, TEXT("Hide_POI"));
    CallPoiEvent(Poi, TEXT("Show_POI"));
}
