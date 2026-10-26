#include "NeelamOcclusionFade.h"
#include "Components/WidgetComponent.h"
#include "Blueprint/UserWidget.h"
#include "GameFramework/Actor.h"
#include "GameFramework/PlayerController.h"
#include "Camera/PlayerCameraManager.h"
#include "Engine/World.h"

UNeelamOcclusionFadeComponent::UNeelamOcclusionFadeComponent()
{
    PrimaryComponentTick.bCanEverTick = true;
}

void UNeelamOcclusionFadeComponent::BeginPlay()
{
    Super::BeginPlay();
    if (AActor* Owner = GetOwner())
    {
        Target = Owner->FindComponentByClass<UWidgetComponent>();
    }
}

void UNeelamOcclusionFadeComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
    Super::TickComponent(DeltaTime, TickType, ThisTickFunction);
    AActor* Owner = GetOwner();
    UWorld* World = GetWorld();
    if (!Owner || !World || !Target.IsValid()) return;

    APlayerController* PC = World->GetFirstPlayerController();
    APlayerCameraManager* CamMgr = PC ? PC->PlayerCameraManager : nullptr;
    if (!CamMgr) return;

    const FVector CamLoc = CamMgr->GetCameraLocation();
    const FVector OwnerLoc = Owner->GetActorLocation();

    FCollisionQueryParams Params(SCENE_QUERY_STAT(NeelamOcclusionFade), false, Owner);
    Params.AddIgnoredActor(Owner);
    FHitResult Hit;
    const bool bBlocked = World->LineTraceSingleByChannel(Hit, CamLoc, OwnerLoc, TraceChannel, Params);

    const float TargetOpacity = bBlocked ? 0.f : 1.f;
    CurrentOpacity = FMath::FInterpTo(CurrentOpacity, TargetOpacity, DeltaTime, FadeSpeed);

    if (UUserWidget* Widget = Target->GetUserWidgetObject())
    {
        Widget->SetRenderOpacity(CurrentOpacity);
    }
}
