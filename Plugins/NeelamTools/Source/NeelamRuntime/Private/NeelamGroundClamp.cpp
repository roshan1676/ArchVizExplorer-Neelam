#include "NeelamGroundClamp.h"
#include "NeelamFlatTour.h"
#include "GameFramework/Actor.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/SpringArmComponent.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/Controller.h"

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

    // 3) the camera hangs on a long spring arm: camera z = pivot z - sin(pitch) * L, so tilting up swings it under the
    //    terrain. Cap the pitch so the camera stays CameraClearance above the ground under it.
    if (!bClampCamera) return;
    USpringArmComponent* Arm = Owner->FindComponentByClass<USpringArmComponent>();
    if (!Arm || Arm->TargetArmLength < 1.f) return;
    if (!Arm->bDoCollisionTest)   // client 27 Oct: orbit/zoom went INTO the podium/towers -> stop the camera in front of walls
    {
        Arm->bDoCollisionTest = true; Arm->ProbeSize = 40.f; Arm->ProbeChannel = TraceChannel;
    }
    const FVector Pivot = Arm->GetComponentLocation();
    const FVector Cam = Arm->GetSocketLocation(USpringArmComponent::SocketName);
    FHitResult CamHit;
    if (!World->LineTraceSingleByChannel(CamHit, FVector(Cam.X, Cam.Y, FMath::Max(Cam.Z, Pivot.Z) + 50000.f),
                                         FVector(Cam.X, Cam.Y, Cam.Z - TraceDistance), TraceChannel, Params)) return;
    const float L = Arm->TargetArmLength;
    const float MaxPitch = FMath::RadiansToDegrees(FMath::Asin(FMath::Clamp((Pivot.Z - (CamHit.ImpactPoint.Z + CameraClearance)) / L, -1.f, 1.f)));
    FRotator R = Arm->GetComponentRotation();
    if (R.Pitch <= MaxPitch) return;
    R.Pitch = MaxPitch;
    Arm->SetWorldRotation(R);
    // whoever drives the arm next frame must agree: template BP target (Pitch_New) and/or the controller
    if (FNumericProperty* N = CastField<FNumericProperty>(Owner->GetClass()->FindPropertyByName(TEXT("Pitch_New"))))
    {
        void* Ptr = N->ContainerPtrToValuePtr<void>(Owner);
        if (N->IsFloatingPoint() && N->GetFloatingPointPropertyValue(Ptr) > MaxPitch) N->SetFloatingPointPropertyValue(Ptr, MaxPitch);
    }
    if (APawn* Pn = Cast<APawn>(Owner))
        if (AController* C = Pn->GetController())
            if (Arm->bUsePawnControlRotation && C->GetControlRotation().GetNormalized().Pitch > MaxPitch)
            {
                FRotator CR = C->GetControlRotation(); CR.Pitch = MaxPitch; C->SetControlRotation(CR);
            }
}
