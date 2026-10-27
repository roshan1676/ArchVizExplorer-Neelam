#include "NeelamWidgets.h"
#include "NeelamFlatTour.h"
#include "NeelamTowerFloors.h"
#include "Components/Button.h"
#include "Components/TextBlock.h"
#include "Components/Image.h"
#include "Components/Border.h"
#include "Components/PanelWidget.h"
#include "Components/ScrollBox.h"
#include "Components/CanvasPanel.h"
#include "Components/CanvasPanelSlot.h"
#include "Components/SizeBox.h"
#include "Components/WidgetSwitcher.h"
#include "Engine/Texture2D.h"
#include "Components/ScaleBox.h"
#include "Components/ScaleBoxSlot.h"
#include "Components/HorizontalBox.h"
#include "Components/HorizontalBoxSlot.h"
#include "Components/ButtonSlot.h"
#include "Blueprint/WidgetTree.h"
#include "Brushes/SlateRoundedBoxBrush.h"
#include "Kismet/KismetMaterialLibrary.h"
#include "Materials/MaterialParameterCollection.h"
#include "Engine/Font.h"
#include "Camera/PlayerCameraManager.h"
#include "GameFramework/PlayerController.h"

#define LOCTEXT_NAMESPACE "Neelam"

// ============================================================ UNeelamListItem
void UNeelamListItem::NativeOnInitialized()
{
    Super::NativeOnInitialized();
    if (MainButton)
    {
        MainButton->OnClicked.AddDynamic(this, &UNeelamListItem::HandleClicked);
        MainButton->OnHovered.AddDynamic(this, &UNeelamListItem::HandleHovered);
        MainButton->OnUnhovered.AddDynamic(this, &UNeelamListItem::HandleUnhovered);
    }
    if (ActionButton) ActionButton->OnClicked.AddDynamic(this, &UNeelamListItem::HandleAction);
    RefreshVisual();
}

void UNeelamListItem::SetTexts(const FText& InLabel, const FText& InInfo, const FText& InExtra)
{
    if (Label) Label->SetText(InLabel);
    if (Info) { Info->SetText(InInfo); Info->SetVisibility(InInfo.IsEmpty() ? ESlateVisibility::Collapsed : ESlateVisibility::HitTestInvisible); }
    if (Extra) { Extra->SetText(InExtra); Extra->SetVisibility(InExtra.IsEmpty() ? ESlateVisibility::Collapsed : ESlateVisibility::HitTestInvisible); }
}

void UNeelamListItem::SetBadge(const FText& InBadge, FLinearColor Color)
{
    if (!Badge) return;
    Badge->SetText(InBadge);
    Badge->SetColorAndOpacity(FSlateColor(Color));
    Badge->SetVisibility(InBadge.IsEmpty() ? ESlateVisibility::Collapsed : ESlateVisibility::HitTestInvisible);
}

void UNeelamListItem::SetSelected(bool bIn) { bSelected = bIn; RefreshVisual(); }
void UNeelamListItem::SetDisabledItem(bool bIn) { bDisabledItem = bIn; if (MainButton) MainButton->SetIsEnabled(!bIn); RefreshVisual(); }

void UNeelamListItem::SetThumb(UTexture2D* Texture)
{
    if (!Thumb) return;
    if (Texture) { Thumb->SetBrushFromTexture(Texture, false); Thumb->SetVisibility(ESlateVisibility::HitTestInvisible); }
    else Thumb->SetVisibility(ESlateVisibility::Collapsed);
}

void UNeelamListItem::RefreshVisual()
{
    const FLinearColor C = bDisabledItem ? DisabledColor : bSelected ? SelectedColor : bHovered ? HoverColor : NormalColor;
    if (Background) Background->SetBrushColor(C);
    if (Marker) Marker->SetBrushColor(bSelected ? SelectedColor : bHovered ? HoverColor : NormalColor);
    OnVisualStateChanged(bSelected, bHovered, bDisabledItem);
}

void UNeelamListItem::HandleClicked() { if (!bDisabledItem) OnItemClicked.Broadcast(this); }
void UNeelamListItem::HandleAction() { if (!bDisabledItem) OnItemAction.Broadcast(this); }
void UNeelamListItem::HandleHovered() { bHovered = true; RefreshVisual(); OnItemHovered.Broadcast(this); }
void UNeelamListItem::HandleUnhovered() { bHovered = false; RefreshVisual(); OnItemUnhovered.Broadcast(this); }

// ============================================================ UNeelamFloorViewTab
bool UNeelamFloorViewTab::IsActivePage() const
{
    for (UWidget* P = GetParent(); P; P = P->GetParent())
        if (UWidgetSwitcher* S = Cast<UWidgetSwitcher>(P)) return S->GetActiveWidget() == this;
    return IsVisible();
}

void UNeelamFloorViewTab::NativeDestruct()
{
    if (bTabActive) if (ANeelamFlatTour* T = ANeelamFlatTour::GetFlatTour(this)) T->DeactivateFloorView();
    bTabActive = false;
    Super::NativeDestruct();
}

// ============================================================ UNeelamFloorViewWidget
static const FName NeelamGalleryId(TEXT("__FloorGallery"));
void UNeelamFloorViewWidget::NativeOnInitialized()
{
    Super::NativeOnInitialized();
    if (CloseDetailButton) CloseDetailButton->OnClicked.AddDynamic(this, &UNeelamFloorViewWidget::HandleCloseDetail);
    if (DetailPanel) DetailPanel->SetVisibility(ESlateVisibility::Collapsed);
}

void UNeelamFloorViewWidget::InitFloorView(ANeelamFlatTour* InTour)
{
    Tour = InTour;
    if (!Tour || !TowerTabs) return;
    TowerTabs->ClearChildren(); TabItems.Reset();
    for (ANeelamTowerFloors* T : Tour->Towers)
    {
        if (!T || !TowerTabClass) continue;
        UNeelamListItem* It = CreateWidget<UNeelamListItem>(this, TowerTabClass);
        It->Id = T->TowerId;
        It->SetTexts(T->DisplayName, FText::GetEmpty(), FText::GetEmpty());
        It->OnItemClicked.AddDynamic(this, &UNeelamFloorViewWidget::HandleTowerTab);
        TowerTabs->AddChild(It);
        TabItems.Add(It);
    }
    if (Tour->SelectedTower) ShowTower(Tour->SelectedTower->TowerId);
    else if (Tour->Towers.Num()) ShowTower(Tour->Towers[0]->TowerId);
}

void UNeelamFloorViewWidget::ShowTower(FName TowerId)
{
    CurrentTower = TowerId;
    for (UNeelamListItem* It : TabItems) if (It) It->SetSelected(It->Id == TowerId);
    if (!FloorList || !Tour) return;
    FloorList->ClearChildren(); FloorItems.Reset();
    ANeelamTowerFloors* T = Tour->FindTower(TowerId);
    if (!T || !FloorRowClass) return;
    if (ListTitle) ListTitle->SetText(FText::Format(LOCTEXT("SelectFloor", "{0}  ·  {1} floors"), T->DisplayName, FText::AsNumber(T->Floors.Num())));
    for (int32 i = T->Floors.Num() - 1; i >= 0; --i)
    {
        const FNeelamFloor& F = T->Floors[i];
        const TArray<FName> Flats = Tour->GetFlatsOnFloor(TowerId, F.Number);
        // Keep only floors that actually have content to show - a FloorGallery photo, real flats, ground floor,
        // or the very top floor (so "till the top" always has an entry) - instead of listing every single floor.
        // NOTE: FindFloorGalleryView/FindBalconyView do a NEAREST-floor lookup (by design, for the floors in
        // between), so they return true for every floor and can't be used here - check for an exact match instead.
        const bool bHasGallery = Tour->FloorGallery.ContainsByPredicate([&F](const FNeelamBalconyView& V) { return V.Floor == F.Number; });
        const bool bIsTop = (i == T->Floors.Num() - 1);
        if (!bHasGallery && Flats.Num() == 0 && F.Number != 0 && !bIsTop) continue;
        UNeelamListItem* It = CreateWidget<UNeelamListItem>(this, FloorRowClass);
        It->Id = TowerId; It->Index = i;
        int32 Avail = 0;
        for (const FName& R : Flats) { FNeelamFlatRow Row; if (Tour->GetFlat(R, Row) && Row.Status == ENeelamUnitStatus::Available) ++Avail; }
        FText InfoT;
        if (!F.bResidential) InfoT = LOCTEXT("Refuge", "Refuge / services");
        else if (Flats.Num()) InfoT = FText::Format(LOCTEXT("Units", "{0} units · {1} available"), FText::AsNumber(Flats.Num()), FText::AsNumber(Avail));
        else InfoT = LOCTEXT("NoUnits", "Residential");
        const FText LabelT = F.Label.IsEmpty() ? FText::Format(LOCTEXT("FloorN", "Floor {0}"), FText::AsNumber(F.Number)) : F.Label;
        It->SetTexts(LabelT, InfoT, FText::GetEmpty());
        if (Flats.Num()) It->SetBadge(FText::AsNumber(Flats.Num()), FLinearColor(0.35f, 0.75f, 1.f)); else It->SetBadge(FText::GetEmpty(), FLinearColor::White);
        It->SetDisabledItem(!F.bResidential);
        It->SetSelected(Tour->SelectedTower == T && Tour->SelectedFloor == i);
        It->OnItemClicked.AddDynamic(this, &UNeelamFloorViewWidget::HandleFloorRow);
        It->OnItemHovered.AddDynamic(this, &UNeelamFloorViewWidget::HandleFloorHover);
        It->OnItemUnhovered.AddDynamic(this, &UNeelamFloorViewWidget::HandleFloorUnhover);
        FloorList->AddChild(It);
        FloorItems.Add(It);
    }
}

void UNeelamFloorViewWidget::ShowFloorDetail(ANeelamTowerFloors* T, int32 FloorIndex)
{
    if (!Tour || !T || !T->Floors.IsValidIndex(FloorIndex)) { HideFloorDetail(); return; }
    if (CurrentTower != T->TowerId) ShowTower(T->TowerId);
    UNeelamListItem* SelectedItem = nullptr;
    for (UNeelamListItem* It : FloorItems) if (It) { const bool b = It->Index == FloorIndex; It->SetSelected(b); if (b) SelectedItem = It; }
    if (SelectedItem && FloorList) FloorList->ScrollWidgetIntoView(SelectedItem, true, EDescendantScrollDestination::Center);
    const FNeelamFloor& F = T->Floors[FloorIndex];
    if (DetailTitle) DetailTitle->SetText(FText::Format(LOCTEXT("DetTitle", "{0}  ·  Floor {1}"), T->DisplayName, FText::AsNumber(F.Number)));
    const TArray<FName> Flats = Tour->GetFlatsOnFloor(T->TowerId, F.Number);
    if (DetailSubtitle) DetailSubtitle->SetText(Flats.Num() ? FText::Format(LOCTEXT("DetSub", "{0} apartments on this floor"), FText::AsNumber(Flats.Num()))
                                                         : LOCTEXT("DetSubNone", "Apartment details for this floor coming soon"));
    if (EmptyText) EmptyText->SetVisibility(Flats.Num() ? ESlateVisibility::Collapsed : ESlateVisibility::HitTestInvisible);
    if (FlatList)
    {
        FlatList->ClearChildren();
        FNeelamBalconyView GView;
        if (FlatCardClass && Tour->FindFloorGalleryView(F.Number, GView))
        {
            UNeelamListItem* It = CreateWidget<UNeelamListItem>(this, FlatCardClass);
            It->Id = NeelamGalleryId; It->Index = F.Number;
            It->SetTexts(LOCTEXT("GalT", "Floor Gallery"), FText::Format(LOCTEXT("GalInfo", "View from floor {0}"), FText::AsNumber(F.Number)),
                         LOCTEXT("GalExtra", "Tap to open the photo"));
            It->SetBadge(LOCTEXT("GalBadge", "GALLERY"), FLinearColor(0.85f, 0.68f, 0.38f));
            // the flat card's action button reads "360° PANORAMA" - relabel it for the gallery card
            if (It->WidgetTree) It->WidgetTree->ForEachWidget([](UWidget* W)
            {
                if (UTextBlock* T = Cast<UTextBlock>(W)) if (T->GetText().ToString().Contains(TEXT("PANORAMA"))) T->SetText(LOCTEXT("GalOpen", "OPEN GALLERY"));
            });
            UTexture2D* Tex = GView.Day.LoadSynchronous();
            if (!Tex) Tex = GView.Night.LoadSynchronous();
            It->SetThumb(Tex);
            if (Tex && It->Thumb)
            {
                // centre crop of the wide photo to the thumbnail's aspect (no stretching)
                const FVector2D Sz = It->Thumb->GetDesiredSize().IsNearlyZero() ? FVector2D(80, 120) : It->Thumb->GetDesiredSize();
                const float Img = Tex->GetSizeX() / FMath::Max(1.f, (float)Tex->GetSizeY());
                const float W = FMath::Clamp((Sz.X / FMath::Max(1.0, Sz.Y)) / Img, 0.05f, 1.f);
                FSlateBrush B = It->Thumb->GetBrush();
                B.SetUVRegion(FBox2f(FVector2f(0.5f - W * 0.5f, 0.f), FVector2f(0.5f + W * 0.5f, 1.f)));
                It->Thumb->SetBrush(B);
            }
            It->OnItemClicked.AddDynamic(this, &UNeelamFloorViewWidget::HandleFlatPanorama);
            It->OnItemAction.AddDynamic(this, &UNeelamFloorViewWidget::HandleFlatPanorama);
            FlatList->AddChild(It);
        }
        for (const FName& R : Flats)
        {
            FNeelamFlatRow Row; if (!Tour->GetFlat(R, Row) || !FlatCardClass) continue;
            FNeelamUnitTypeRow Type; Tour->GetUnitType(Row.UnitType, Type);
            UNeelamListItem* It = CreateWidget<UNeelamListItem>(this, FlatCardClass);
            It->Id = R;
            const FText TypeT = Type.DisplayName.IsEmpty() ? FText::FromName(Row.UnitType) : Type.DisplayName;
            FText InfoT = Type.AreaText;
            if (!Row.Facing.IsEmpty()) InfoT = FText::Format(LOCTEXT("InfoFacing", "{0}  ·  {1} facing"), Type.AreaText, Row.Facing);
            It->SetTexts(FText::Format(LOCTEXT("FlatT", "Flat {0}"), Row.FlatNumber), TypeT, InfoT);
            static const FText StatusT[] = { LOCTEXT("Avail", "AVAILABLE"), LOCTEXT("Hold", "ON HOLD"), LOCTEXT("Sold", "SOLD") };
            static const FLinearColor StatusC[] = { FLinearColor(0.2f, 0.9f, 0.45f), FLinearColor(1.f, 0.65f, 0.1f), FLinearColor(1.f, 0.25f, 0.25f) };
            const int32 S = FMath::Clamp((int32)Row.Status, 0, 2);
            It->SetBadge(StatusT[S], StatusC[S]);
            It->SetThumb(Type.FloorPlan.LoadSynchronous());
            It->OnItemClicked.AddDynamic(this, &UNeelamFloorViewWidget::HandleFlatPanorama);
            It->OnItemAction.AddDynamic(this, &UNeelamFloorViewWidget::HandleFlatPanorama);
            FlatList->AddChild(It);
        }
    }
    if (DetailPanel) DetailPanel->SetVisibility(ESlateVisibility::SelfHitTestInvisible);
}

void UNeelamFloorViewWidget::HideFloorDetail()
{
    if (DetailPanel) DetailPanel->SetVisibility(ESlateVisibility::Collapsed);
    for (UNeelamListItem* It : FloorItems) if (It) It->SetSelected(false);
}

void UNeelamFloorViewWidget::SetHoveredFloor(ANeelamTowerFloors* T, int32 FloorIndex)
{
    if (HoverHint)
    {
        if (T && T->Floors.IsValidIndex(FloorIndex))
        {
            HoverHint->SetText(FText::Format(LOCTEXT("Hover", "{0}  ·  Floor {1}"), T->DisplayName, FText::AsNumber(T->Floors[FloorIndex].Number)));
            HoverHint->SetVisibility(ESlateVisibility::HitTestInvisible);
        }
        else HoverHint->SetVisibility(ESlateVisibility::Collapsed);
    }
}

void UNeelamFloorViewWidget::HandleTowerTab(UNeelamListItem* Item)
{
    if (!Item || !Tour) return;
    ShowTower(Item->Id);
    HideFloorDetail();
    Tour->ClearSelection();
    Tour->FocusOverview();
}
void UNeelamFloorViewWidget::HandleFloorRow(UNeelamListItem* Item)
{
    if (Item && Tour) Tour->SelectFloor(Tour->FindTower(Item->Id), Item->Index, true);
}
void UNeelamFloorViewWidget::HandleFloorHover(UNeelamListItem* Item)
{
    if (Item && Tour) Tour->HoverFloor(Tour->FindTower(Item->Id), Item->Index);
}
void UNeelamFloorViewWidget::HandleFloorUnhover(UNeelamListItem* Item)
{
    if (Tour) Tour->HoverFloor(nullptr, INDEX_NONE);
}
void UNeelamFloorViewWidget::HandleFlatPanorama(UNeelamListItem* Item)
{
    if (!Item || !Tour) return;
    if (Item->Id == NeelamGalleryId) Tour->OpenFloorGallery(Item->Index);
    else Tour->StartTour(Item->Id);
}
void UNeelamFloorViewWidget::HandleCloseDetail()
{
    HideFloorDetail();
    if (Tour) { Tour->ClearSelection(); Tour->FocusOverview(); }
}

// ============================================================ UNeelamTourWidget
void UNeelamTourWidget::NativeOnInitialized()
{
    Super::NativeOnInitialized();
    if (ExitButton) ExitButton->OnClicked.AddDynamic(this, &UNeelamTourWidget::HandleExit);
}

void UNeelamTourWidget::SetupFlat(ANeelamFlatTour* InTour, FName FlatRow)
{
    Tour = InTour;
    if (!Tour) return;
    FNeelamFlatRow Flat; FNeelamUnitTypeRow Type;
    if (!Tour->GetFlat(FlatRow, Flat) || !Tour->GetUnitType(Flat.UnitType, Type)) return;
    if (FlatTitle) FlatTitle->SetText(Type.FloorPlan.IsNull() ? Flat.FlatNumber : FText::Format(LOCTEXT("TourTitle", "Flat {0}"), Flat.FlatNumber));
    if (FlatInfo)
    {
        const FText TypeT = Type.DisplayName.IsEmpty() ? FText::FromName(Flat.UnitType) : Type.DisplayName;
        FText T = FText::Format(LOCTEXT("TourInfo", "{0}  ·  Tower {1}  ·  Floor {2}"), TypeT, FText::FromName(Flat.Tower), FText::AsNumber(Flat.Floor));
        FlatInfo->SetText(T);
    }
    UTexture2D* Plan = Type.FloorPlan.LoadSynchronous();
    if (PlanImage && Plan) PlanImage->SetBrushFromTexture(Plan, false);
    if (PlanBox) PlanBox->SetVisibility(Plan ? ESlateVisibility::SelfHitTestInvisible : ESlateVisibility::Collapsed);
    if (PlanBox && Plan)
    {
        const float W = FMath::Max(1, Plan->GetSizeX()), H = FMath::Max(1, Plan->GetSizeY());
        float OutH = PlanMaxHeight, OutW = PlanMaxHeight * W / H;
        if (OutW > PlanMaxWidth) { OutW = PlanMaxWidth; OutH = PlanMaxWidth * H / W; }
        PlanBox->SetWidthOverride(OutW); PlanBox->SetHeightOverride(OutH);
    }
    if (HotspotLayer)
    {
        HotspotLayer->ClearChildren(); Hotspots.Reset(); ViewCone = nullptr;
        if (ViewConeTexture)   // added first so it renders behind the room hotspot buttons
        {
            ViewCone = WidgetTree->ConstructWidget<UImage>(UImage::StaticClass(), TEXT("ViewCone"));
            FSlateBrush ConeBrush; ConeBrush.SetResourceObject(ViewConeTexture);
            ConeBrush.ImageSize = ViewConeSize;   // SetDesiredSizeOverride was ignored -> cone drew at the 32 px default
            ViewCone->SetBrush(ConeBrush);
            ViewCone->SetVisibility(ESlateVisibility::HitTestInvisible);
            ViewCone->SetRenderTransformPivot(FVector2D(0.5f, 1.f));   // rotate around the dot (texture's bottom-centre), not the image centre
            if (UCanvasPanelSlot* S = HotspotLayer->AddChildToCanvas(ViewCone))
            {
                S->SetAlignment(FVector2D(0.5f, 1.f));   // pivot = the dot, baked at the texture's bottom-centre
                S->SetAutoSize(true);
            }
        }
        for (int32 i = 0; i < Type.Rooms.Num(); ++i)
        {
            if (!HotspotClass) break;
            const FNeelamRoom& R = Type.Rooms[i];
            UNeelamListItem* It = CreateWidget<UNeelamListItem>(this, HotspotClass);
            It->Index = i;
            It->SetTexts(R.Name, FText::GetEmpty(), FText::GetEmpty());
            It->OnItemClicked.AddDynamic(this, &UNeelamTourWidget::HandleRoom);
            if (UCanvasPanelSlot* S = HotspotLayer->AddChildToCanvas(It))
            {
                S->SetAnchors(FAnchors((float)R.PlanPosition.X, (float)R.PlanPosition.Y));
                S->SetAlignment(FVector2D(0.5f, 0.5f));
                S->SetPosition(FVector2D::ZeroVector);
                S->SetAutoSize(true);
            }
            Hotspots.Add(It);
        }
    }
    if (RoomBar)
    {
        RoomBar->ClearChildren(); RoomButtons.Reset();
        for (int32 i = 0; i < Type.Rooms.Num(); ++i)
        {
            if (!RoomButtonClass) break;
            UNeelamListItem* It = CreateWidget<UNeelamListItem>(this, RoomButtonClass);
            It->Index = i;
            It->SetTexts(Type.Rooms[i].Name, FText::GetEmpty(), FText::GetEmpty());
            It->OnItemClicked.AddDynamic(this, &UNeelamTourWidget::HandleRoom);
            RoomBar->AddChild(It);
            RoomButtons.Add(It);
        }
    }
}

void UNeelamTourWidget::SetActiveRoom(int32 RoomIndex)
{
    for (UNeelamListItem* It : Hotspots) if (It) It->SetSelected(It->Index == RoomIndex);
    for (UNeelamListItem* It : RoomButtons) if (It) It->SetSelected(It->Index == RoomIndex);
    if (Tour)
    {
        FNeelamFlatRow Flat; FNeelamUnitTypeRow Type;
        if (Tour->GetFlat(Tour->CurrentFlat, Flat) && Tour->GetUnitType(Flat.UnitType, Type) && Type.Rooms.IsValidIndex(RoomIndex))
        {
            const FNeelamRoom& R = Type.Rooms[RoomIndex];
            if (RoomTitle) RoomTitle->SetText(R.Name);
            if (ViewCone)
            {
                if (UCanvasPanelSlot* S = Cast<UCanvasPanelSlot>(ViewCone->Slot))
                    S->SetAnchors(FAnchors((float)R.PlanPosition.X, (float)R.PlanPosition.Y));
                ViewCone->SetRenderTransformAngle(R.StartYaw + 90.f);   // texture points up at 0; plan yaw 0 = right
            }
        }
    }
}

void UNeelamTourWidget::NativeTick(const FGeometry& MyGeometry, float InDeltaTime)
{
    Super::NativeTick(MyGeometry, InDeltaTime);
    if (!ViewCone || !Tour || Tour->CurrentRoom == INDEX_NONE) return;
    // balcony photo gallery has no look direction: keep the cone at the room's StartYaw (set in SetActiveRoom)
    if (Tour->Gallery && Tour->Gallery->IsInViewport() && Tour->Gallery->GetVisibility() != ESlateVisibility::Collapsed) return;
    APlayerController* PC = GetOwningPlayer();
    if (!PC) return;
    const float CamYaw = PC->PlayerCameraManager ? PC->PlayerCameraManager->GetCameraRotation().Yaw : PC->GetControlRotation().Yaw;
    ViewCone->SetRenderTransformAngle(Tour->ControlYawToPlanYaw(CamYaw) + 90.f);   // UMG angle: 0 = up, clockwise
}

void UNeelamTourWidget::HandleRoom(UNeelamListItem* Item) { if (Item && Tour) Tour->ShowRoom(Item->Index); }
void UNeelamTourWidget::HandleExit() { if (Tour) Tour->EndTour(); }


// ------------------------------------------------------------------ balcony gallery
static FSlateFontInfo NeelamFont(int32 Size, const TCHAR* Face)
{
    if (UObject* F = LoadObject<UObject>(nullptr, TEXT("/Game/Neelam/UI/Fonts/F_Neelam_Sans.F_Neelam_Sans")))
        return FSlateFontInfo(F, Size, FName(Face));
    return FCoreStyle::GetDefaultFontStyle("Bold", Size);
}

TSharedRef<SWidget> UNeelamBalconyGallery::RebuildWidget()
{
    if (WidgetTree && !WidgetTree->RootWidget)
    {
        UCanvasPanel* Root = WidgetTree->ConstructWidget<UCanvasPanel>(UCanvasPanel::StaticClass(), TEXT("Root"));
        WidgetTree->RootWidget = Root;
        auto Full = [](UCanvasPanelSlot* S) { S->SetAnchors(FAnchors(0, 0, 1, 1)); S->SetOffsets(FMargin(0)); };
        UImage* Bg = WidgetTree->ConstructWidget<UImage>(UImage::StaticClass(), TEXT("Bg"));
        Bg->SetColorAndOpacity(FLinearColor(0.01f, 0.01f, 0.012f, 1.f));
        Full(Root->AddChildToCanvas(Bg));
        UScaleBox* SB = WidgetTree->ConstructWidget<UScaleBox>(UScaleBox::StaticClass(), TEXT("Fit"));
        SB->SetStretch(EStretch::ScaleToFit);
        Full(Root->AddChildToCanvas(SB));
        Photo = WidgetTree->ConstructWidget<UImage>(UImage::StaticClass(), TEXT("Photo"));
        SB->AddChild(Photo);

        // top-centre pill: caption + DAY / NIGHT
        UBorder* Pill = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass(), TEXT("Pill"));
        Pill->SetBrush(FSlateRoundedBoxBrush(FLinearColor(0.f, 0.f, 0.f, 0.55f), 22.f, FLinearColor(1, 1, 1, 0.12f), 1.f));
        Pill->SetPadding(FMargin(18, 6, 6, 6));
        if (UCanvasPanelSlot* S = Root->AddChildToCanvas(Pill))
        { S->SetAnchors(FAnchors(0.5f, 0.f)); S->SetAlignment(FVector2D(0.5f, 0.f)); S->SetPosition(FVector2D(0, 28)); S->SetAutoSize(true); }
        UHorizontalBox* HB = WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass(), TEXT("Row"));
        Pill->SetContent(HB);
        auto MakeBtn = [&](const TCHAR* Name, const FText& Label) -> UButton*
        {
            UButton* B = WidgetTree->ConstructWidget<UButton>(UButton::StaticClass(), FName(Name));
            UTextBlock* T = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
            T->SetText(Label); T->SetFont(NeelamFont(12, TEXT("SemiBold"))); T->SetColorAndOpacity(FSlateColor(FLinearColor::White));
            B->SetContent(T);
            if (UButtonSlot* BS = Cast<UButtonSlot>(T->Slot)) BS->SetPadding(FMargin(16, 6));
            if (UHorizontalBoxSlot* S = HB->AddChildToHorizontalBox(B)) S->SetPadding(FMargin(2, 0));
            return B;
        };
        // floor-step buttons, either side of the caption (Floor View gallery only - see Refresh)
        BtnPrevFloor = MakeBtn(TEXT("BtnPrevFloor"), NSLOCTEXT("Neelam", "GalPrev", "−"));
        Caption = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("Caption"));
        Caption->SetFont(NeelamFont(13, TEXT("Medium"))); Caption->SetColorAndOpacity(FSlateColor(FLinearColor(1, 1, 1, 0.85f)));
        if (UHorizontalBoxSlot* S = HB->AddChildToHorizontalBox(Caption)) { S->SetVerticalAlignment(VAlign_Center); S->SetPadding(FMargin(8, 0, 16, 0)); }
        BtnNextFloor = MakeBtn(TEXT("BtnNextFloor"), NSLOCTEXT("Neelam", "GalNext", "+"));
        BtnPrevFloor->OnClicked.AddDynamic(this, &UNeelamBalconyGallery::HandlePrevFloor);
        BtnNextFloor->OnClicked.AddDynamic(this, &UNeelamBalconyGallery::HandleNextFloor);
        BtnDay = MakeBtn(TEXT("BtnDay"), NSLOCTEXT("Neelam", "BalDay", "DAY"));
        BtnNight = MakeBtn(TEXT("BtnNight"), NSLOCTEXT("Neelam", "BalNight", "NIGHT"));
        BtnDay->OnClicked.AddDynamic(this, &UNeelamBalconyGallery::HandleDay);
        BtnNight->OnClicked.AddDynamic(this, &UNeelamBalconyGallery::HandleNight);

        // top-right CLOSE (Floor View gallery only)
        BtnClose = WidgetTree->ConstructWidget<UButton>(UButton::StaticClass(), TEXT("BtnClose"));
        UTextBlock* CT = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
        CT->SetText(NSLOCTEXT("Neelam", "GalClose", "×  CLOSE")); CT->SetFont(NeelamFont(12, TEXT("SemiBold"))); CT->SetColorAndOpacity(FSlateColor(FLinearColor::White));
        BtnClose->SetContent(CT);
        if (UButtonSlot* BS = Cast<UButtonSlot>(CT->Slot)) BS->SetPadding(FMargin(18, 8));
        FButtonStyle St = BtnClose->GetStyle();
        St.SetNormal(FSlateRoundedBoxBrush(FLinearColor(0.f, 0.f, 0.f, 0.55f), 20.f, FLinearColor(1, 1, 1, 0.18f), 1.f));
        St.SetHovered(FSlateRoundedBoxBrush(FLinearColor(0.578f, 0.397f, 0.144f, 1.f), 20.f));
        St.SetPressed(FSlateRoundedBoxBrush(FLinearColor(0.578f, 0.397f, 0.144f, 1.f), 20.f));
        St.SetNormalPadding(FMargin(0)); St.SetPressedPadding(FMargin(0));
        BtnClose->SetStyle(St);
        if (UCanvasPanelSlot* S = Root->AddChildToCanvas(BtnClose))
        { S->SetAnchors(FAnchors(1.f, 0.f)); S->SetAlignment(FVector2D(1.f, 0.f)); S->SetPosition(FVector2D(-32, 28)); S->SetAutoSize(true); }
        BtnClose->OnClicked.AddDynamic(this, &UNeelamBalconyGallery::HandleClose);
    }
    return Super::RebuildWidget();
}

void UNeelamBalconyGallery::ShowView(const FNeelamBalconyView& View, int32 FlatFloor)
{
    DayTex = View.Day.LoadSynchronous(); NightTex = View.Night.LoadSynchronous();
    ViewFloor = View.Floor; FlatFloorNum = FlatFloor;
    // follow the app's time of day (Emissive_MPC.Effects: 0 day -> 1 night)
    float Eff = 0.f;
    if (UMaterialParameterCollection* M = LoadObject<UMaterialParameterCollection>(nullptr, TEXT("/Game/ArchVizExplorer/Materials/MPC/Emissive_MPC.Emissive_MPC")))
        Eff = UKismetMaterialLibrary::GetScalarParameterValue(this, M, TEXT("Effects"));
    bNight = NightTex && (Eff > 0.5f || !DayTex);
    SetVisibility(ESlateVisibility::Visible);
    Refresh();
}

void UNeelamBalconyGallery::SetNight(bool bInNight) { bNight = bInNight && NightTex; Refresh(); }
void UNeelamBalconyGallery::HandleDay() { if (DayTex) SetNight(false); }
void UNeelamBalconyGallery::HandleNight() { if (NightTex) SetNight(true); }
void UNeelamBalconyGallery::HandleClose()
{
    if (ANeelamFlatTour* T = ANeelamFlatTour::GetFlatTour(this)) T->CloseFloorGallery();
    else RemoveFromParent();
}
// nearest Floor Gallery photo floor below (Dir -1) / above (Dir +1) Floor; INDEX_NONE if none.
// -/+ step through the floors that HAVE a photo (5, 10, 15, 20 ...), not every floor number (client 27 Oct)
static int32 NeighbourGalleryFloor(const ANeelamFlatTour* T, int32 Floor, int32 Dir)
{
    int32 Best = INDEX_NONE;
    for (const FNeelamBalconyView& V : T->FloorGallery)
        if ((V.Floor - Floor) * Dir > 0 && (Best == INDEX_NONE || (V.Floor - Best) * Dir < 0)) Best = V.Floor;
    return Best;
}
void UNeelamBalconyGallery::HandlePrevFloor()
{
    if (ANeelamFlatTour* T = ANeelamFlatTour::GetFlatTour(this)) { const int32 F = NeighbourGalleryFloor(T, FlatFloorNum, -1); if (F != INDEX_NONE) T->OpenFloorGallery(F); }
}
void UNeelamBalconyGallery::HandleNextFloor()
{
    if (ANeelamFlatTour* T = ANeelamFlatTour::GetFlatTour(this)) { const int32 F = NeighbourGalleryFloor(T, FlatFloorNum, +1); if (F != INDEX_NONE) T->OpenFloorGallery(F); }
}

void UNeelamBalconyGallery::Refresh()
{
    if (!Photo) return;
    UTexture2D* T = bNight ? NightTex.Get() : DayTex.Get();
    if (T) { Photo->SetBrushFromTexture(T, true); }
    const FLinearColor Gold(0.578f, 0.397f, 0.144f, 1.f), Off(1.f, 1.f, 1.f, 0.08f);
    auto Style = [&](UButton* B, bool bOn, bool bHas)
    {
        if (!B) return;
        FButtonStyle St = B->GetStyle();
        const FLinearColor C = bOn ? Gold : Off;
        St.SetNormal(FSlateRoundedBoxBrush(C, 16.f)); St.SetHovered(FSlateRoundedBoxBrush(bOn ? Gold : FLinearColor(1, 1, 1, 0.18f), 16.f));
        St.SetPressed(FSlateRoundedBoxBrush(Gold, 16.f));
        St.SetNormalPadding(FMargin(0)); St.SetPressedPadding(FMargin(0));
        B->SetStyle(St);
        B->SetVisibility(bHas ? ESlateVisibility::Visible : ESlateVisibility::Collapsed);
    };
    // DAY / NIGHT only when both photos exist (the Floor View gallery has day photos only)
    Style(BtnDay, !bNight, DayTex != nullptr && NightTex != nullptr);
    Style(BtnNight, bNight, DayTex != nullptr && NightTex != nullptr);
    if (Caption)
        Caption->SetText(FText::Format(CaptionFormat, FText::AsNumber(FlatFloorNum)));
    if (BtnClose) BtnClose->SetVisibility(bShowClose ? ESlateVisibility::Visible : ESlateVisibility::Collapsed);
    // floor-step arrows: only in the Floor View gallery (bShowClose), hidden when there is no lower / higher photo floor
    bool bCanPrev = false, bCanNext = false;
    if (bShowClose)
        if (ANeelamFlatTour* GalTour = ANeelamFlatTour::GetFlatTour(this))
        {
            bCanPrev = NeighbourGalleryFloor(GalTour, FlatFloorNum, -1) != INDEX_NONE;
            bCanNext = NeighbourGalleryFloor(GalTour, FlatFloorNum, +1) != INDEX_NONE;
        }
    if (BtnPrevFloor) BtnPrevFloor->SetVisibility(bCanPrev ? ESlateVisibility::Visible : ESlateVisibility::Collapsed);
    if (BtnNextFloor) BtnNextFloor->SetVisibility(bCanNext ? ESlateVisibility::Visible : ESlateVisibility::Collapsed);
}

#undef LOCTEXT_NAMESPACE
