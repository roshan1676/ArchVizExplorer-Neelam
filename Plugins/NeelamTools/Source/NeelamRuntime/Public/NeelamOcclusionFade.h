#pragma once
#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "NeelamOcclusionFade.generated.h"

class UWidgetComponent;

/** Add to a world-space/screen-space label actor (e.g. BP_Neelam_UpcomingLabel): each tick, line-traces from the
 *  player's camera to the owner and smoothly fades the owner's UWidgetComponent out when something solid (a
 *  building) is between the camera and it, back in when the view clears - so it never reads as if it belongs to
 *  whatever happens to be in front of it. Fade, not a hard show/hide, so it's never a visible pop/glitch. */
UCLASS(Blueprintable, ClassGroup = (Neelam), meta = (BlueprintSpawnableComponent))
class NEELAMRUNTIME_API UNeelamOcclusionFadeComponent : public UActorComponent
{
    GENERATED_BODY()
public:
    UNeelamOcclusionFadeComponent();

    /** Seconds to fully fade in/out. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neelam") float FadeSpeed = 3.f;
    /** Trace channel used to detect blocking geometry (Visibility matches building/site mesh collision). */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neelam") TEnumAsByte<ECollisionChannel> TraceChannel = ECC_Visibility;

protected:
    virtual void BeginPlay() override;
    virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

private:
    TWeakObjectPtr<UWidgetComponent> Target;
    float CurrentOpacity = 1.f;
};
