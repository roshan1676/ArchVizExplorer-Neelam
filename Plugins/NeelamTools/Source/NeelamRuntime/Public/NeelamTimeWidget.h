#pragma once
#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "NeelamTimeWidget.generated.h"

class USlider; class UTextBlock; class UImage; class UButton; class UTexture2D; class UMaterialParameterCollection; class USkyLightComponent;

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

    /** Amenity lighting switch groups (Amenity_Lighting.py): the slider hour is written to this MPC's "Hour" every frame
        (S2 timer 19-22 h, S3 security 18-06 h). Defaults to /Game/Neelam/Amenities/Lighting/MPC_Neelam_Lighting. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neelam") TObjectPtr<UMaterialParameterCollection> LightingMPC;

    /** Night ambient: the real-time sky light keeps almost day-level ambient after sunset, so auto exposure made 21:00 look like
        daylight and every night light (amenity lighting plan, street lamps, windows) disappeared. The sky light is scaled
        by Lerp(1, NightSkyLightScale, Emissive_MPC.Effects) - Effects is the template's 0 day -> 1 night factor. 1 = off. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neelam") float NightSkyLightScale = 0.003f;

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
    float LastHourSent = -100.f;
    TWeakObjectPtr<USkyLightComponent> SkyLight;
    float SkyLightDay = -1.f;
    TObjectPtr<UMaterialParameterCollection> EmissiveMPC;
    void UpdateNightAmbient();
    void PushHour(float Hour);
};
