#pragma once
#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "NeelamGroundClamp.generated.h"

/** Add to the explorer pawn. Two independent safety nets on top of whatever collision the floating movement
 *  already has (fast pan/fly can outrun it, or outrun Cesium tile collision still streaming in):
 *   1. Ground floor: line-traces straight down and stops the owner sinking below the real ground/terrain.
 *   2. Anti-tunnel (OFF by default - see bEnableAntiTunnelSweep): sphere-sweeps from last frame's location to this
 *      frame's and pulls the owner back if that step punched through solid geometry. Found to false-positive
 *      against small BlockAll props (trees, pool lights, etc.) during ordinary panning, causing visible camera
 *      snapping/stutter - leave off until it can be scoped to just building/amenity structural meshes. */
UCLASS(Blueprintable, ClassGroup = (Neelam), meta = (BlueprintSpawnableComponent))
class NEELAMRUNTIME_API UNeelamGroundClampComponent : public UActorComponent
{
    GENERATED_BODY()
public:
    UNeelamGroundClampComponent();

    /** Minimum height (cm) the owner is kept above whatever the ground trace hits. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neelam") float MinClearance = 60.f;
    /** See class comment - off by default, caused camera stutter against small decorative props. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neelam") bool bEnableAntiTunnelSweep = false;
    /** How far below the owner to search for ground (cm). */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neelam") float TraceDistance = 20000.f;
    /** Trace channel used for both traces (Visibility matches Cesium tile / site mesh collision). */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neelam") TEnumAsByte<ECollisionChannel> TraceChannel = ECC_Visibility;
    /** Sphere radius (cm) used for the anti-tunnel sweep; keep <= the pawn's own collision radius. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neelam") float SweepRadius = 40.f;
    /** Ignore a single-frame step shorter than this (cm) - normal movement, not worth sweeping every tick. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neelam") float MinStepToSweep = 50.f;
    /** Pause entirely whenever ANeelamFlatTour is active (Floor View / flat tours camera moves close past the
     *  tower's own structure - the ground trace can catch a floor slab and yank the camera, overshooting toward
     *  the top). Only meant for free-roam exploration outside Floor View. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neelam") bool bPauseDuringFlatTour = true;

protected:
    virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

private:
    bool bHasLastLocation = false;
    FVector LastLocation = FVector::ZeroVector;
};
