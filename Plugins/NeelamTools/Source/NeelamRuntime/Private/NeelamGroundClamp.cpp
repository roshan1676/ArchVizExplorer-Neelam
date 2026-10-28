#include "NeelamGroundClamp.h"
#include "NeelamFlatTour.h"
#include "GameFramework/Actor.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/SpringArmComponent.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/Controller.h"
#include "Camera/CameraComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Components/TimelineComponent.h"

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
    // the template's pin flight (BP timeline "Timeline_Focus_Animation") must pass: gym / toilets / STP / fire / parking
    // pins sit INSIDE the podium - blocking it left the camera parked outside and the pin click did nothing
    bool bFocusFlight = false;
    TInlineComponentArray<UTimelineComponent*> Timelines(Owner);
    for (const UTimelineComponent* T : Timelines)
        if (T->IsPlaying() && T->GetName().Contains(TEXT("Focus"))) bFocusFlight = true;
    if (bEnableAntiTunnelSweep && bHasLastLocation && !bFocusFlight)
    {
        const FVector Delta = Loc - LastLocation;
        if (Delta.SizeSquared() > 1.f)   // every step: the stand-off sphere must never be crossed
        {
            FCollisionQueryParams SweepParams = Params;
            for (int32 i = 0; i < 6; ++i)   // skip non-blockers and look behind them (a tower can sit behind a fence)
            {
                FHitResult SweepHit;
                if (!World->SweepSingleByChannel(SweepHit, LastLocation, Loc, FQuat::Identity, TraceChannel, FCollisionShape::MakeSphere(FMath::Max(SweepRadius, PivotStandoff)), SweepParams)
                    || !SweepHit.GetActor()) break;
                const UPrimitiveComponent* C = SweepHit.GetComponent();
                const UStaticMeshComponent* S = Cast<UStaticMeshComponent>(C);
                const bool bBlocks = S && C->Bounds.BoxExtent.GetMax() >= MinBlockerExtent   // meshes only: pin (BP_POI) boxes are not walls
                    && !SweepHit.GetActor()->GetClass()->GetName().Contains(TEXT("Cesium"))
                    // amenity dressing is merged per type (fences / trees / climbing wall = 20-28 m bounds): pan over it
                    && !(S && S->GetStaticMesh() && S->GetStaticMesh()->GetName().StartsWith(TEXT("SM_Amenity_")))
                    && !SweepHit.bStartPenetrating                 // already inside the stand-off: let it move away
                    && SweepHit.ImpactNormal.Z < 0.7f;            // floors / decks / roofs under the pivot: ground clamp's job
                if (bBlocks)
                {
                    // pull back to just outside the hit, keeping the attempted height so it still reads as "blocked", not "teleported down"
                    Loc = SweepHit.Location + SweepHit.ImpactNormal * 2.f;
                    Owner->SetActorLocation(Loc, false, nullptr, ETeleportType::TeleportPhysics);
                    break;
                }
                SweepParams.AddIgnoredActor(SweepHit.GetActor());
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
    // where the camera really sits unpulled: the CineCamera hangs 12 m BEHIND the arm end (relative X -1216) - sweeping
    // only to the socket left those 12 m unchecked and the camera ended up behind Tower C (test 27 Oct)
    const FVector Desired = Arm->GetSocketTransform(USpringArmComponent::SocketName).TransformPosition(CamBaseRel);
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
    // 28 Oct (client: "Home / camera broken - inside buildings, under the map"): no camera collision while
    //  - the template flies the camera (pin focus / Home): its end views are designed, and
    //  - the pivot itself is covered (Home pivot sits at 2 m INSIDE the podium, some pins are under the map /
    //    inside the podium): every sweep from there hits the cover -> camera was dragged in to the pivot.
    FHitResult Cover;
    bool bPivotCovered = World->LineTraceSingleByChannel(Cover, Pivot + FVector(0, 0, 50.f), Pivot + FVector(0, 0, 15000.f), TraceChannel, Params);
    // enclosed: walls within 150 m in 7+ of 8 directions (Home's pivot is INSIDE the podium, whose ceiling has no
    // collision, so the up-trace sees sky). Re-checked only when the pivot has moved > 1 m.
    static TWeakObjectPtr<const UNeelamGroundClampComponent> EncFor; static FVector EncAt(1e30); static bool bEnc = false;
    if (EncFor.Get() != this || FVector::DistSquared(EncAt, Pivot) > 10000.f)
    {
        EncFor = this; EncAt = Pivot; int32 Walls = 0;
        for (int32 d = 0; d < 8; ++d)
        {
            const FVector Dir = FRotator(0.f, d * 45.f, 0.f).Vector(); FHitResult W;
            if (World->LineTraceSingleByChannel(W, Pivot, Pivot + Dir * 15000.f, TraceChannel, Params) && W.GetActor()
                && !W.GetActor()->GetClass()->GetName().Contains(TEXT("Cesium"))) ++Walls;
        }
        bEnc = Walls >= 7;
    }
    bPivotCovered = bPivotCovered || bEnc;
    const bool bCollide = !bFocusFlight && !bPivotCovered;
    // the wall sweeps react to buildings only: the photo map is the terrain (pitch cap above handles it). Home's 450 m arm
    // at -4..-8 deg skims the map ground ~17 m out -> it was "a wall" and the camera got dragged in to the pivot.
    static TWeakObjectPtr<UWorld> MapWorld; static TArray<TWeakObjectPtr<AActor>> MapActors;   // found once per world
    if (MapWorld.Get() != World)
    {
        MapWorld = World; MapActors.Reset();
        for (TActorIterator<AActor> It(World); It; ++It)
            if (It->GetClass()->GetName().Contains(TEXT("Cesium3DTileset"))) MapActors.Add(*It);
    }
    FCollisionQueryParams CamParams = Params;
    for (const TWeakObjectPtr<AActor>& M : MapActors) if (M.IsValid()) CamParams.AddIgnoredActor(M.Get());
    float Want = 0.f;
    FHitResult Near, Hit;   // wide early-warning sweep drives the easing; the tight one is the hard limit
    if (bCollide && World->SweepSingleByChannel(Near, Pivot, Desired, FQuat::Identity, TraceChannel, FCollisionShape::MakeSphere(CamAnticipate), CamParams) && !Near.bStartPenetrating)
        Want = FMath::Max(0.f, Len - FMath::Max(Near.Distance - 100.f, 150.f));
    // look ahead along the orbit: where the arm will point CamLookAheadTime from now
    const float ArmYaw = Arm->GetComponentRotation().Yaw;
    if (DeltaTime > KINDA_SMALL_NUMBER)
        SmoothYawRate = FMath::FInterpTo(SmoothYawRate, FMath::FindDeltaAngleDegrees(LastArmYaw, ArmYaw) / DeltaTime, DeltaTime, 5.f);
    LastArmYaw = ArmYaw;
    const float AheadYaw = FMath::Clamp(SmoothYawRate * CamLookAheadTime, -45.f, 45.f);
    FHitResult Ahead;
    if (bCollide && FMath::Abs(AheadYaw) > 2.f
        && World->SweepSingleByChannel(Ahead, Pivot, Pivot + FRotator(0.f, AheadYaw, 0.f).RotateVector(Desired - Pivot), FQuat::Identity, TraceChannel, FCollisionShape::MakeSphere(CamProbeRadius), CamParams)
        && !Ahead.bStartPenetrating)
        Want = FMath::Max(Want, Len - FMath::Max(Ahead.Distance - 100.f, 150.f));
    if (bCollide) World->SweepSingleByChannel(Hit, Pivot, Desired, FQuat::Identity, TraceChannel, FCollisionShape::MakeSphere(CamProbeRadius), CamParams);
    const bool bIn = Want > CamPull;
    // let-out scales with the arm: Home sets a 450 m arm, a fixed 6 m/s let-out left the camera pulled ~360 m for a minute
    const float MaxStep = (bIn ? CamMaxPullInRate : FMath::Max(CamMaxLetOutRate, 0.25f * Len)) * DeltaTime;
    CamPull = FMath::Clamp(FMath::FInterpTo(CamPull, Want, DeltaTime, bIn ? CamPullInSpeed : CamLetOutSpeed), CamPull - MaxStep, CamPull + MaxStep);
    // hard limit (client: "camera shall not be able to go inside the building"): never behind the first wall, even
    // when a fast pan outruns the easing. Want keeps a 1 m buffer, so this only bites in that case.
    if (bCollide && Hit.bBlockingHit && !Hit.bStartPenetrating) CamPull = FMath::Max(CamPull, Len - FMath::Max(Hit.Distance - 30.f, 100.f));
    // never past the pivot: the arm can shrink in one frame (450 m Home -> 97 m Amenities) while CamPull was large ->
    // the camera went through the pivot and out the far side, under the map
    CamPull = FMath::Clamp(CamPull, 0.f, FMath::Max(0.f, Len - 300.f));
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
