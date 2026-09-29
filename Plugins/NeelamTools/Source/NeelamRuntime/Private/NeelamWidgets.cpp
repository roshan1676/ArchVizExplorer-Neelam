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
        UNeelamListItem* It = CreateWidget<UNeelamListItem>(this, FloorRowClass);
        It->Id = TowerId; It->Index = i;
        const TArray<FName> Flats = Tour->GetFlatsOnFloor(TowerId, F.Number);
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
    if (Item && Tour) Tour->StartTour(Item->Id);
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
    if (FlatTitle) FlatTitle->SetText(FText::Format(LOCTEXT("TourTitle", "Flat {0}"), Flat.FlatNumber));
    if (FlatInfo)
    {
        const FText TypeT = Type.DisplayName.IsEmpty() ? FText::FromName(Flat.UnitType) : Type.DisplayName;
        FText T = FText::Format(LOCTEXT("TourInfo", "{0}  ·  Tower {1}  ·  Floor {2}"), TypeT, FText::FromName(Flat.Tower), FText::AsNumber(Flat.Floor));
        FlatInfo->SetText(T);
    }
    UTexture2D* Plan = Type.FloorPlan.LoadSynchronous();
    if (PlanImage && Plan) PlanImage->SetBrushFromTexture(Plan, false);
    if (PlanBox && Plan)
    {
        const float W = FMath::Max(1, Plan->GetSizeX()), H = FMath::Max(1, Plan->GetSizeY());
        float OutH = PlanMaxHeight, OutW = PlanMaxHeight * W / H;
        if (OutW > PlanMaxWidth) { OutW = PlanMaxWidth; OutH = PlanMaxWidth * H / W; }
        PlanBox->SetWidthOverride(OutW); PlanBox->SetHeightOverride(OutH);
    }
    if (HotspotLayer)
    {
        HotspotLayer->ClearChildren(); Hotspots.Reset();
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
    if (RoomTitle && Tour)
    {
        FNeelamFlatRow Flat; FNeelamUnitTypeRow Type;
        if (Tour->GetFlat(Tour->CurrentFlat, Flat) && Tour->GetUnitType(Flat.UnitType, Type) && Type.Rooms.IsValidIndex(RoomIndex))
            RoomTitle->SetText(Type.Rooms[RoomIndex].Name);
    }
}

void UNeelamTourWidget::HandleRoom(UNeelamListItem* Item) { if (Item && Tour) Tour->ShowRoom(Item->Index); }
void UNeelamTourWidget::HandleExit() { if (Tour) Tour->EndTour(); }

#undef LOCTEXT_NAMESPACE
