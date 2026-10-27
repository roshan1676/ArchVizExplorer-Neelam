#include "NeelamGroundClamp.h"
#include "NeelamFlatTour.h"
#include "GameFramework/Actor.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/SpringArmComponent.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/Controller.h"
#include "Camera/CameraComponent.h"

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

    // the template's 360 pawn lives inside BP_360Sphere (150 m under the site): "rescuing" it to the ground lifted it out of
    // the sphere -> every 360 (amenity + flat tour) was viewed from far off-centre (bent floors, wrong look direction)
    if (!SphereChecked)
    {
        SphereChecked = true;
        for (TActorIterator<AActor> It(World); It; ++It)
            if (It->GetClass()->GetName() == TEXT("BP_360Sphere_C") && FVector::Dist(It->GetActorLocation(), Owner->GetActorLocation()) < 15000.f) bInside360Sphere = true;
    }
    if (bInside360Sphere) return;

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
        if (Delta.SizeSquared() > 1.f)   // every step: the stand-off sphere must never be crossed
        {
            FHitResult SweepHit;
            if (World->SweepSingleByChannel(SweepHit, LastLocation, Loc, FQuat::Identity, TraceChannel, FCollisionShape::MakeSphere(FMath::Max(SweepRadius, PivotStandoff)), Params)
                && SweepHit.GetComponent() && SweepHit.GetComponent()->Bounds.BoxExtent.GetMax() >= MinBlockerExtent
                && !(SweepHit.GetActor() && SweepHit.GetActor()->GetClass()->GetName().Contains(TEXT("Cesium")))
                && !SweepHit.bStartPenetrating                 // already inside the stand-off: let it move away
                && SweepHit.ImpactNormal.Z < 0.7f)            // floors / decks / roofs under the pivot: ground clamp's job
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

    // 3) + 4) camera on the spring arm (client 27 Oct: "camera not smooth, goes into the property, goes under the map")
    if (!bClampCamera) return;
    USpringArmComponent* Arm = Owner->FindComponentByClass<USpringArmComponent>();
    if (!Arm || Arm->TargetArmLength < 1.f) return;
    if (!CamComp.IsValid())
    {
        TArray<USceneComponent*> Kids; Arm->GetChildrenComponents(false, Kids);
        for (USceneComponent* K : Kids)   // the CineCamera - not the proxy mesh / frustum / widget also hanging on the arm
            if (K && K->IsA<UCameraComponent>()) { CamComp = K; CamBaseRel = K->GetRelativeLocation(); break; }
        Arm->bDoCollisionTest = false;   // the engine test snaps; ours below eases
    }
    const FVector Pivot = Arm->GetComponentLocation();
    const FVector Desired = Arm->GetSocketLocation(USpringArmComponent::SocketName);   // collision test off = lagged desired spot
    const float Len = FVector::Dist(Pivot, Desired);

    // 3) never below the terrain: cap the arm pitch. Terrain only (Cesium tiles) - roofs made the cap jump. Eased.
    float GroundZ;
    float MaxPitch = 89.f;
    if (TerrainZ(World, Desired, GroundZ) && Len > 1.f)
        MaxPitch = FMath::RadiansToDegrees(FMath::Asin(FMath::Clamp((Pivot.Z - (GroundZ + CameraClearance)) / Len, -1.f, 1.f)));
    SmoothMaxPitch = FMath::FInterpTo(SmoothMaxPitch, MaxPitch, DeltaTime, 4.f);
    FRotator R = Arm->GetComponentRotation();
    if (R.Pitch > SmoothMaxPitch)
    {
        R.Pitch = SmoothMaxPitch; Arm->SetWorldRotation(R);
        if (FNumericProperty* N = CastField<FNumericProperty>(Owner->GetClass()->FindPropertyByName(TEXT("Pitch_New"))))
        {
            void* Ptr = N->ContainerPtrToValuePtr<void>(Owner);
            if (N->IsFloatingPoint() && N->GetFloatingPointPropertyValue(Ptr) > SmoothMaxPitch) N->SetFloatingPointPropertyValue(Ptr, SmoothMaxPitch);
        }
        if (APawn* Pn = Cast<APawn>(Owner))
            if (AController* C = Pn->GetController())
                if (Arm->bUsePawnControlRotation && C->GetControlRotation().GetNormalized().Pitch > SmoothMaxPitch)
                {
                    FRotator CR = C->GetControlRotation(); CR.Pitch = SmoothMaxPitch; C->SetControlRotation(CR);
                }
    }

    // 4) keep the camera out of buildings, eased: sweep pivot -> camera, slide the camera toward the pivot by an
    //    interpolated amount (fast in, slow out) instead of the spring arm's per-frame snap
    if (!CamComp.IsValid()) return;
    float Want = 0.f;
    FHitResult Near, Hit;   // wide early-warning sweep drives the easing; the tight one is the hard limit
    if (World->SweepSingleByChannel(Near, Pivot, Desired, FQuat::Identity, TraceChannel, FCollisionShape::MakeSphere(CamAnticipate), Params) && !Near.bStartPenetrating)
        Want = FMath::Max(0.f, Len - FMath::Max(Near.Distance - 100.f, 150.f));
    World->SweepSingleByChannel(Hit, Pivot, Desired, FQuat::Identity, TraceChannel, FCollisionShape::MakeSphere(CamProbeRadius), Params);
    CamPull = FMath::FInterpTo(CamPull, Want, DeltaTime, Want > CamPull ? CamPullInSpeed : CamLetOutSpeed);
    // hard limit (client: "camera shall not be able to go inside the building"): never behind the first wall, even
    // when a fast pan outruns the easing. Want keeps a 1 m buffer, so this only bites in that case.
    if (Hit.bBlockingHit && !Hit.bStartPenetrating) CamPull = FMath::Max(CamPull, Len - FMath::Max(Hit.Distance - 30.f, 100.f));
    CamComp->SetRelativeLocation(CamBaseRel + FVector(CamPull, 0.f, 0.f));   // +X = along the arm toward the pivot
}

bool UNeelamGroundClampComponent::TerrainZ(UWorld* World, const FVector& At, float& OutZ) const
{
    FCollisionQueryParams P(SCENE_QUERY_STAT(NeelamTerrainZ), false, GetOwner());
    for (int32 i = 0; i < 6; ++i)   // step through roofs / decks until the map tiles (blocking hits end a trace)
    {
        FHitResult H;
        if (!World->LineTraceSingleByChannel(H, FVector(At.X, At.Y, At.Z + 100000.f), FVector(At.X, At.Y, At.Z - TraceDistance), TraceChannel, P) || !H.GetActor()) return false;
        if (H.GetActor()->GetClass()->GetName().Contains(TEXT("Cesium3DTileset"))) { OutZ = H.ImpactPoint.Z; return true; }
        P.AddIgnoredActor(H.GetActor());
    }
    return false;
}
