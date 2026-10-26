#include "NeelamGroundClamp.h"
#include "NeelamFlatTour.h"
#include "GameFramework/Actor.h"
#include "Engine/World.h"

UNeelamGroundClampComponent::UNeelamGroundClampComponent()
{
    PrimaryComponentTick.bCanEverTick = true;
    PrimaryComponentTick.TickGroup = TG_PostPhysics;   // after movement has been applied this frame
}

void UNeelamGroundClampComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
    Super::TickComponent(DeltaTime, TickType, ThisTickFunction);
    AActor* Owner = GetOwner();
    UWorld* World = GetWorld();
    if (!Owner || !World) return;

    if (bPauseDuringFlatTour)
    {
        if (ANeelamFlatTour* Tour = ANeelamFlatTour::GetFlatTour(this))
        {
            if (Tour->State != ENeelamTourState::Off)
            {
                bHasLastLocation = false;   // don't let a stale LastLocation trigger an anti-tunnel correction on return
                return;
            }
        }
    }

    FCollisionQueryParams Params(SCENE_QUERY_STAT(NeelamGroundClamp), false, Owner);
    Params.AddIgnoredActor(Owner);

    // 1) anti-tunnel: did this frame's step skip clean through a wall/building/amenity mesh?
    FVector Loc = Owner->GetActorLocation();
    if (bEnableAntiTunnelSweep && bHasLastLocation)
    {
        const FVector Delta = Loc - LastLocation;
        if (Delta.SizeSquared() > MinStepToSweep * MinStepToSweep)
        {
            FHitResult SweepHit;
            if (World->SweepSingleByChannel(SweepHit, LastLocation, Loc, FQuat::Identity, TraceChannel, FCollisionShape::MakeSphere(SweepRadius), Params))
            {
                // pull back to just outside the hit, keeping the attempted height so it still reads as "blocked", not "teleported down"
                Loc = SweepHit.Location + SweepHit.ImpactNormal * 2.f;
                Owner->SetActorLocation(Loc, false, nullptr, ETeleportType::TeleportPhysics);
            }
        }
    }
    LastLocation = Loc;
    bHasLastLocation = true;

    // 2) ground floor: never let the owner end up below the real ground/terrain under it
    const FVector Start = Loc + FVector(0, 0, MinClearance);
    const FVector End = Loc - FVector(0, 0, TraceDistance);
    FHitResult GroundHit;
    if (World->LineTraceSingleByChannel(GroundHit, Start, End, TraceChannel, Params))
    {
        const float FloorZ = GroundHit.ImpactPoint.Z + MinClearance;
        if (Loc.Z < FloorZ)
        {
            Loc.Z = FloorZ;
            Owner->SetActorLocation(Loc, false, nullptr, ETeleportType::TeleportPhysics);
            LastLocation = Loc;
        }
    }
}
