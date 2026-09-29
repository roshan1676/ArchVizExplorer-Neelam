#include "NeelamTowerFloors.h"
#include "Components/InstancedStaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Materials/MaterialInterface.h"
#include "UObject/ConstructorHelpers.h"

ANeelamTowerFloors::ANeelamTowerFloors()
{
    PrimaryActorTick.bCanEverTick = false;
    Root = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
    RootComponent = Root;
    Boxes = CreateDefaultSubobject<UInstancedStaticMeshComponent>(TEXT("FloorBoxes"));
    Boxes->SetupAttachment(Root);
    Boxes->SetMobility(EComponentMobility::Movable);
    Boxes->SetCastShadow(false);
    Boxes->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Boxes->SetCollisionResponseToAllChannels(ECR_Ignore);
    Boxes->SetCollisionResponseToChannel(ECC_Visibility, ECR_Block);
    Boxes->SetGenerateOverlapEvents(false);
    Boxes->bSelectable = true;
    Boxes->NumCustomDataFloats = 1;
    static ConstructorHelpers::FObjectFinder<UStaticMesh> Cube(TEXT("/Engine/BasicShapes/Cube.Cube"));
    if (Cube.Succeeded()) BoxMesh = Cube.Object;
}

void ANeelamTowerFloors::OnConstruction(const FTransform& Transform)
{
    Super::OnConstruction(Transform);
    RebuildBoxes();
    Boxes->SetVisibility(bPreviewInEditor, true);
}

void ANeelamTowerFloors::BeginPlay()
{
    Super::BeginPlay();
    RebuildBoxes();
    SetBoxesActive(false);
}

void ANeelamTowerFloors::RebuildBoxes()
{
    if (!Boxes) return;
    Boxes->ClearInstances();
    Boxes->SetStaticMesh(BoxMesh);
    if (BoxMaterial) Boxes->SetMaterial(0, BoxMaterial);
    Boxes->SetNumCustomDataFloats(1);
    const double SX = (FootprintHalfSize.X + Inflate) * 2.0 / 100.0;
    const double SY = (FootprintHalfSize.Y + Inflate) * 2.0 / 100.0;
    for (int32 i = 0; i < Floors.Num(); ++i)
    {
        const FNeelamFloor& F = Floors[i];
        const double H = FMath::Max(10.0, (double)F.Height - VerticalGap);
        const FVector C(FootprintCenter.X, FootprintCenter.Y, F.BottomZ + F.Height * 0.5);
        const int32 Id = Boxes->AddInstance(FTransform(FRotator::ZeroRotator, C, FVector(SX, SY, H / 100.0)), false);
        Boxes->SetCustomDataValue(Id, 0, BaseState(i), false);
    }
    Boxes->MarkRenderStateDirty();
}

float ANeelamTowerFloors::BaseState(int32 FloorIndex) const
{
    return Floors.IsValidIndex(FloorIndex) && Floors[FloorIndex].bResidential ? 0.f : -1.f;
}

void ANeelamTowerFloors::SetFloorState(int32 FloorIndex, float State)
{
    if (!Boxes || FloorIndex < 0 || FloorIndex >= Boxes->GetInstanceCount()) return;
    if (BaseState(FloorIndex) < 0.f && State > 0.f) State = -1.f;
    Boxes->SetCustomDataValue(FloorIndex, 0, State, true);
}

void ANeelamTowerFloors::ResetFloorStates()
{
    if (!Boxes) return;
    for (int32 i = 0; i < Boxes->GetInstanceCount(); ++i) Boxes->SetCustomDataValue(i, 0, BaseState(i), false);
    Boxes->MarkRenderStateDirty();
}

void ANeelamTowerFloors::SetBoxesActive(bool bNewActive)
{
    bActive = bNewActive;
    if (!Boxes) return;
    Boxes->SetVisibility(bNewActive, true);
    Boxes->SetHiddenInGame(!bNewActive, true);
    Boxes->SetCollisionEnabled(bNewActive ? ECollisionEnabled::QueryOnly : ECollisionEnabled::NoCollision);
    if (!bNewActive) ResetFloorStates();
}

int32 ANeelamTowerFloors::FindFloorIndexByNumber(int32 Number) const
{
    for (int32 i = 0; i < Floors.Num(); ++i) if (Floors[i].Number == Number) return i;
    return INDEX_NONE;
}

FVector ANeelamTowerFloors::GetFloorCenter(int32 FloorIndex) const
{
    if (!Floors.IsValidIndex(FloorIndex)) return GetTowerCenter();
    const FNeelamFloor& F = Floors[FloorIndex];
    return GetActorTransform().TransformPosition(FVector(FootprintCenter.X, FootprintCenter.Y, F.BottomZ + F.Height * 0.5));
}

FVector ANeelamTowerFloors::GetTowerCenter() const
{
    double Lo = 0, Hi = 0;
    if (Floors.Num()) { Lo = Floors[0].BottomZ; Hi = Floors.Last().BottomZ + Floors.Last().Height; }
    return GetActorTransform().TransformPosition(FVector(FootprintCenter.X, FootprintCenter.Y, (Lo + Hi) * 0.5));
}

float ANeelamTowerFloors::GetTowerTopZ() const
{
    const double Hi = Floors.Num() ? Floors.Last().BottomZ + Floors.Last().Height : 0.0;
    return GetActorTransform().TransformPosition(FVector(FootprintCenter.X, FootprintCenter.Y, Hi)).Z;
}

FVector ANeelamTowerFloors::GetFacadePoint(int32 FloorIndex, float LocalYaw, float Offset, float Outside, FVector& OutNormal) const
{
    const double HX = FootprintHalfSize.X + Inflate, HY = FootprintHalfSize.Y + Inflate;
    const double R = FMath::DegreesToRadians(LocalYaw);
    const FVector2D D(FMath::Cos(R), FMath::Sin(R));
    const double TX = FMath::Abs(D.X) > KINDA_SMALL_NUMBER ? HX / FMath::Abs(D.X) : 1e12;
    const double TY = FMath::Abs(D.Y) > KINDA_SMALL_NUMBER ? HY / FMath::Abs(D.Y) : 1e12;
    FVector2D N, Tan;
    FVector2D P;
    if (TX < TY) { N = FVector2D(FMath::Sign(D.X), 0); Tan = FVector2D(0, 1); P = D * TX; }
    else         { N = FVector2D(0, FMath::Sign(D.Y)); Tan = FVector2D(1, 0); P = D * TY; }
    P += Tan * Offset + N * Outside;
    double Z = 0;
    if (Floors.IsValidIndex(FloorIndex)) Z = Floors[FloorIndex].BottomZ + Floors[FloorIndex].Height * 0.55;
    const FTransform& T = GetActorTransform();
    OutNormal = T.TransformVectorNoScale(FVector(N.X, N.Y, 0)).GetSafeNormal();
    return T.TransformPosition(FVector(FootprintCenter.X + P.X, FootprintCenter.Y + P.Y, Z));
}
