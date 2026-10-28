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
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neelam") bool bEnableAntiTunnelSweep = true;
    /** Anti-tunnel only blocks on structures at least this big (half-extent, cm): towers / podium / landmarks, not trees,
     *  bollards or pool lights (those caused the old stutter). Map tiles never block (ground clamp handles them). */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neelam") float MinBlockerExtent = 1500.f;
    /** The pivot stays this far (cm) from big structures, so the orbiting camera always has room in front of a wall
     *  (pivot glued to a facade = camera behind the wall for half the orbit). */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neelam") float PivotStandoff = 800.f;
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
    /** Keep the spring-arm CAMERA above the terrain too: limits how far the orbit can tilt up (camera swinging below
     *  the pivot went under the map). Client 27 Oct. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neelam") bool bClampCamera = true;
    /** Minimum height (cm) of the camera above the ground under it. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neelam") float CameraClearance = 400.f;
    /** Smoothed camera collision (replaces USpringArmComponent::bDoCollisionTest, which snapped the camera 6 m in one
     *  frame every time a tower passed between camera and pivot = jerky panning). Pull-in / let-out speeds (1/s). */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neelam") float CamPullInSpeed = 5.f;
    /** Early-warning sweep radius (cm): the camera starts easing in this far before it would touch a wall. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neelam") float CamAnticipate = 600.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neelam") float CamLetOutSpeed = 2.5f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neelam") float CamProbeRadius = 60.f;
    /** Speed caps (cm/s) on the eased pull-in / let-out: FInterpTo alone moved 40+ m/s on a big gap (test 27 Oct). */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neelam") float CamMaxPullInRate = 1500.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neelam") float CamMaxLetOutRate = 600.f;
    /** While orbiting, also probe where the camera will be this many seconds ahead, so it eases in before the wall. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neelam") float CamLookAheadTime = 0.8f;

protected:
    virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

private:
    bool SphereChecked = false;
    TWeakObjectPtr<class USceneComponent> CamComp;
    FVector CamBaseRel = FVector::ZeroVector;
    float CamPull = 0.f;
    float SmoothMaxPitch = 90.f;
    float LastArmYaw = 0.f;
    float SmoothYawRate = 0.f;
    bool TerrainZ(UWorld* World, const FVector& At, float& OutZ) const;
    bool bInside360Sphere = false;
    bool bHasLastLocation = false;
    FVector LastLocation = FVector::ZeroVector;
};
