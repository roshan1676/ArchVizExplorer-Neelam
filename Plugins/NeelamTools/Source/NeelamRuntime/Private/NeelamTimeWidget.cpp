#include "NeelamTimeWidget.h"
#include "Components/Slider.h"
#include "Components/TextBlock.h"
#include "Components/Image.h"
#include "Components/Button.h"
#include "Engine/Texture2D.h"

#define LOCTEXT_NAMESPACE "NeelamTime"

void UNeelamTimeWidget::NativeOnInitialized()
{
    Super::NativeOnInitialized();
    if (Btn_Morning) Btn_Morning->OnClicked.AddDynamic(this, &UNeelamTimeWidget::OnMorning);
    if (Btn_Noon) Btn_Noon->OnClicked.AddDynamic(this, &UNeelamTimeWidget::OnNoon);
    if (Btn_Sunset) Btn_Sunset->OnClicked.AddDynamic(this, &UNeelamTimeWidget::OnSunset);
    if (Btn_Night) Btn_Night->OnClicked.AddDynamic(this, &UNeelamTimeWidget::OnNight);
}

void UNeelamTimeWidget::OnMorning() { GlideTo(MorningHour); }
void UNeelamTimeWidget::OnNoon() { GlideTo(NoonHour); }
void UNeelamTimeWidget::OnSunset() { GlideTo(SunsetHour); }
void UNeelamTimeWidget::OnNight() { GlideTo(NightHour); }

void UNeelamTimeWidget::GlideTo(float Hour)
{
    if (!Slider_01) return;
    GlideFrom = Slider_01->GetValue();
    GlideTarget = FMath::Clamp(Hour, Slider_01->GetMinValue(), Slider_01->GetMaxValue());
    GlideT = 0.f; bGliding = true;
}

void UNeelamTimeWidget::ApplyValue(float V)
{
    if (!Slider_01) return;
    Slider_01->SetValue(V);
    Slider_01->OnValueChanged.Broadcast(V);   // the Blueprint handler moves the sun + night lights
}

void UNeelamTimeWidget::NativeTick(const FGeometry& MyGeometry, float InDeltaTime)
{
    Super::NativeTick(MyGeometry, InDeltaTime);
    if (!Slider_01) return;
    if (bGliding)
    {
        GlideT = FMath::Min(1.f, GlideT + InDeltaTime / FMath::Max(0.1f, GlideSeconds));
        ApplyValue(FMath::Lerp(GlideFrom, GlideTarget, FMath::InterpEaseInOut(0.f, 1.f, GlideT, 2.5f)));
        if (GlideT >= 1.f) bGliding = false;
    }
    RefreshLook(Slider_01->GetValue());
}

void UNeelamTimeWidget::RefreshLook(float H)
{
    // 0 morning, 1 afternoon, 2 evening, 3 night
    const int32 P = (H >= 5.5f && H < 11.5f) ? 0 : (H >= 11.5f && H < 16.75f) ? 1 : (H >= 16.75f && H < 19.5f) ? 2 : 3;
    if (P == LastPeriod) return;
    LastPeriod = P;
    static const FText Names[] = { LOCTEXT("M", "MORNING"), LOCTEXT("A", "AFTERNOON"), LOCTEXT("E", "EVENING"), LOCTEXT("N", "NIGHT") };
    if (Text_Period) Text_Period->SetText(Names[P]);
    UTexture2D* Ic = P == 3 ? IconNight.Get() : P == 2 ? IconTwilight.Get() : IconDay.Get();
    if (Image_TimeIcon && Ic) Image_TimeIcon->SetBrushFromTexture(Ic, false);
    UTextBlock* Tx[] = { Txt_Morning, Txt_Noon, Txt_Sunset, Txt_Night };
    for (int32 i = 0; i < 4; ++i) if (Tx[i]) Tx[i]->SetColorAndOpacity(FSlateColor(i == P ? ActiveColor : InactiveColor));
}

#undef LOCTEXT_NAMESPACE
