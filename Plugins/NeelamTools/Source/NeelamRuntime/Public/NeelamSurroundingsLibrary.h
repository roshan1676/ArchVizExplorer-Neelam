#pragma once
#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "NeelamSurroundingsLibrary.generated.h"

/** Runtime helpers for the Surroundings panel: isolate a single landmark's route instead of showing every route at once. */
UCLASS()
class NEELAMRUNTIME_API UNeelamSurroundingsLibrary : public UBlueprintFunctionLibrary
{
    GENERATED_BODY()
public:
    /** Hides every Surroundings route/traffic actor (tag "Neelam_Route") except the one tagged "LM_<LandmarkId>"
     *  (e.g. "fortis" -> "LM_fortis", set by Build_Surroundings.py / Build_Traffic.py), and also hides the shared
     *  key-road glow lines (tag "Neelam_RoadGlow": Road_vb/eeh/mar) so only the one path to the selected place
     *  reads on screen. Poles and POI pins are left alone. */
    UFUNCTION(BlueprintCallable, Category = "Neelam|Surroundings", meta = (WorldContext = "WorldContextObject"))
    static void IsolateSurroundingsRoute(UObject* WorldContextObject, FName LandmarkId);

    /** Restores every Surroundings route/traffic actor to visible (call on deselect / closing the detail panel). */
    UFUNCTION(BlueprintCallable, Category = "Neelam|Surroundings", meta = (WorldContext = "WorldContextObject"))
    static void ShowAllSurroundingsRoutes(UObject* WorldContextObject);

    /** Convenience for BP_POI::Select_POI - reads the POI actor's own "LM_<id>" tag and isolates that route,
     *  so the Blueprint doesn't need to parse its own tags. No-op (does nothing, not an error) if the actor has
     *  no "LM_" tag - e.g. the IMMEDIATE/landmark category pins. */
    UFUNCTION(BlueprintCallable, Category = "Neelam|Surroundings", meta = (WorldContext = "WorldContextObject"))
    static void IsolateSurroundingsRouteForActor(UObject* WorldContextObject, AActor* Poi);
};
