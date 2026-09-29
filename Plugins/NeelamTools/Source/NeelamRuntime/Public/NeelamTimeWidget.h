#pragma once
#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "NeelamTimeWidget.generated.h"

class USlider; class UTextBlock; class UImage; class UButton; class UTexture2D;

/** Parent class for BP_Time_Widget: preset buttons (smooth time glide), sun/moon icon and period label.
    The Blueprint keeps its own logic (OnValueChanged -> sun, night lights); we only drive the slider. */
UCLASS(Blueprintable)
class NEELAMRUNTIME_API UNeelamTimeWidget : public UUserWidget
{
    GENERATED_BODY()
public:
    UPROPERTY(BlueprintReadOnly, Category = "Neelam", meta = (BindWidgetOptional)) TObjectPtr<USlider> Slider_01;
    UPROPERTY(BlueprintReadOnly, Category = "Neelam", meta = (BindWidgetOptional)) TObjectPtr<UImage> Image_TimeIcon;
    UPROPERTY(BlueprintReadOnly, Category = "Neelam", meta = (BindWidgetOptional)) TObjectPtr<UTextBlock> Text_Period;
    UPROPERTY(BlueprintReadOnly, Category = "Neelam", meta = (BindWidgetOptional)) TObjectPtr<UButton> Btn_Morning;
    UPROPERTY(BlueprintReadOnly, Category = "Neelam", meta = (BindWidgetOptional)) TObjectPtr<UButton> Btn_Noon;
    UPROPERTY(BlueprintReadOnly, Category = "Neelam", meta = (BindWidgetOptional)) TObjectPtr<UButton> Btn_Sunset;
    UPROPERTY(BlueprintReadOnly, Category = "Neelam", meta = (BindWidgetOptional)) TObjectPtr<UButton> Btn_Night;
    UPROPERTY(BlueprintReadOnly, Category = "Neelam", meta = (BindWidgetOptional)) TObjectPtr<UTextBlock> Txt_Morning;
    UPROPERTY(BlueprintReadOnly, Category = "Neelam", meta = (BindWidgetOptional)) TObjectPtr<UTextBlock> Txt_Noon;
    UPROPERTY(BlueprintReadOnly, Category = "Neelam", meta = (BindWidgetOptional)) TObjectPtr<UTextBlock> Txt_Sunset;
    UPROPERTY(BlueprintReadOnly, Category = "Neelam", meta = (BindWidgetOptional)) TObjectPtr<UTextBlock> Txt_Night;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neelam") float MorningHour = 8.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neelam") float NoonHour = 12.5f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neelam") float SunsetHour = 18.25f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neelam") float NightHour = 21.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neelam") float GlideSeconds = 1.4f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neelam") TObjectPtr<UTexture2D> IconDay;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neelam") TObjectPtr<UTexture2D> IconTwilight;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neelam") TObjectPtr<UTexture2D> IconNight;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neelam") FLinearColor ActiveColor = FLinearColor(0.578f, 0.397f, 0.144f, 1.f);
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neelam") FLinearColor InactiveColor = FLinearColor(1.f, 1.f, 1.f, 0.55f);

    /** Glide the time of day to Hour (the Blueprint's slider handler updates sun + lights every frame). */
    UFUNCTION(BlueprintCallable, Category = "Neelam") void GlideTo(float Hour);

protected:
    virtual void NativeOnInitialized() override;
    virtual void NativeTick(const FGeometry& MyGeometry, float InDeltaTime) override;
    UFUNCTION() void OnMorning();
    UFUNCTION() void OnNoon();
    UFUNCTION() void OnSunset();
    UFUNCTION() void OnNight();
    void ApplyValue(float V);
    void RefreshLook(float Hour);
private:
    bool bGliding = false;
    float GlideFrom = 0.f, GlideTarget = 0.f, GlideT = 0.f;
    int32 LastPeriod = -1;
};
