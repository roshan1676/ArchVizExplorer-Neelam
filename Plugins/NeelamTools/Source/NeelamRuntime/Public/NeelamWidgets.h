#pragma once
#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "NeelamTypes.h"
#include "NeelamWidgets.generated.h"

class UButton; class UTextBlock; class UImage; class UBorder; class UPanelWidget; class UScrollBox;
class UCanvasPanel; class USizeBox; class UScaleBox; class ANeelamFlatTour; class ANeelamTowerFloors; class UNeelamListItem;

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FNeelamItemEvent, UNeelamListItem*, Item);

/** Generic clickable row / tab / card / hotspot. Style it in the Widget Blueprint; bind the named widgets. */
UCLASS(Abstract, Blueprintable)
class NEELAMRUNTIME_API UNeelamListItem : public UUserWidget
{
    GENERATED_BODY()
public:
    UPROPERTY(BlueprintReadOnly, Category = "Neelam", meta = (BindWidget)) TObjectPtr<UButton> MainButton;
    UPROPERTY(BlueprintReadOnly, Category = "Neelam", meta = (BindWidgetOptional)) TObjectPtr<UButton> ActionButton;
    UPROPERTY(BlueprintReadOnly, Category = "Neelam", meta = (BindWidgetOptional)) TObjectPtr<UTextBlock> Label;
    UPROPERTY(BlueprintReadOnly, Category = "Neelam", meta = (BindWidgetOptional)) TObjectPtr<UTextBlock> Info;
    UPROPERTY(BlueprintReadOnly, Category = "Neelam", meta = (BindWidgetOptional)) TObjectPtr<UTextBlock> Extra;
    UPROPERTY(BlueprintReadOnly, Category = "Neelam", meta = (BindWidgetOptional)) TObjectPtr<UTextBlock> Badge;
    UPROPERTY(BlueprintReadOnly, Category = "Neelam", meta = (BindWidgetOptional)) TObjectPtr<UImage> Thumb;
    UPROPERTY(BlueprintReadOnly, Category = "Neelam", meta = (BindWidgetOptional)) TObjectPtr<UBorder> Background;
    UPROPERTY(BlueprintReadOnly, Category = "Neelam", meta = (BindWidgetOptional)) TObjectPtr<UBorder> Marker;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neelam|Style") FLinearColor NormalColor = FLinearColor(0.02f, 0.03f, 0.05f, 0.55f);
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neelam|Style") FLinearColor HoverColor = FLinearColor(0.08f, 0.25f, 0.6f, 0.75f);
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neelam|Style") FLinearColor SelectedColor = FLinearColor(0.1f, 0.45f, 1.f, 0.95f);
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neelam|Style") FLinearColor DisabledColor = FLinearColor(0.02f, 0.02f, 0.02f, 0.35f);

    UPROPERTY(BlueprintReadWrite, Category = "Neelam") FName Id;
    UPROPERTY(BlueprintReadWrite, Category = "Neelam") int32 Index = INDEX_NONE;
    UPROPERTY(BlueprintReadOnly, Category = "Neelam") bool bSelected = false;
    UPROPERTY(BlueprintReadOnly, Category = "Neelam") bool bHovered = false;
    UPROPERTY(BlueprintReadOnly, Category = "Neelam") bool bDisabledItem = false;

    UPROPERTY(BlueprintAssignable, Category = "Neelam") FNeelamItemEvent OnItemClicked;
    UPROPERTY(BlueprintAssignable, Category = "Neelam") FNeelamItemEvent OnItemAction;
    UPROPERTY(BlueprintAssignable, Category = "Neelam") FNeelamItemEvent OnItemHovered;
    UPROPERTY(BlueprintAssignable, Category = "Neelam") FNeelamItemEvent OnItemUnhovered;

    UFUNCTION(BlueprintCallable, Category = "Neelam") void SetTexts(const FText& InLabel, const FText& InInfo, const FText& InExtra);
    UFUNCTION(BlueprintCallable, Category = "Neelam") void SetBadge(const FText& InBadge, FLinearColor Color);
    UFUNCTION(BlueprintCallable, Category = "Neelam") void SetSelected(bool bInSelected);
    UFUNCTION(BlueprintCallable, Category = "Neelam") void SetDisabledItem(bool bInDisabled);
    UFUNCTION(BlueprintCallable, Category = "Neelam") void SetThumb(UTexture2D* Texture);
    UFUNCTION(BlueprintImplementableEvent, Category = "Neelam") void OnVisualStateChanged(bool bIsSelected, bool bIsHovered, bool bIsDisabled);

protected:
    virtual void NativeOnInitialized() override;
    void RefreshVisual();
    UFUNCTION() void HandleClicked();
    UFUNCTION() void HandleAction();
    UFUNCTION() void HandleHovered();
    UFUNCTION() void HandleUnhovered();
};

/** Invisible page inside the MasterMenu WidgetSwitcher: when it becomes the active page, Floor View turns on. */
UCLASS(Blueprintable)
class NEELAMRUNTIME_API UNeelamFloorViewTab : public UUserWidget
{
    GENERATED_BODY()
public:
    UPROPERTY(BlueprintReadOnly, Category = "Neelam") bool bTabActive = false;
    /** Taskbar button of this tab in the MasterMenu (added to its Buttons_TaskBar list so the highlight works). */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neelam") FName TaskbarButtonName = TEXT("Button_UnitSearch_FV_0");
    /** Polled by ANeelamFlatTour every frame (works even when the UI is not being painted). */
    bool IsActivePage() const;
protected:
    virtual void NativeDestruct() override;
};

/** Floor View overlay: tower tabs + floor list (left) and floor detail with flats (right). */
UCLASS(Abstract, Blueprintable)
class NEELAMRUNTIME_API UNeelamFloorViewWidget : public UUserWidget
{
    GENERATED_BODY()
public:
    UPROPERTY(BlueprintReadOnly, Category = "Neelam", meta = (BindWidget)) TObjectPtr<UPanelWidget> TowerTabs;
    UPROPERTY(BlueprintReadOnly, Category = "Neelam", meta = (BindWidget)) TObjectPtr<UScrollBox> FloorList;
    UPROPERTY(BlueprintReadOnly, Category = "Neelam", meta = (BindWidget)) TObjectPtr<UWidget> DetailPanel;
    UPROPERTY(BlueprintReadOnly, Category = "Neelam", meta = (BindWidget)) TObjectPtr<UTextBlock> DetailTitle;
    UPROPERTY(BlueprintReadOnly, Category = "Neelam", meta = (BindWidget)) TObjectPtr<UPanelWidget> FlatList;
    UPROPERTY(BlueprintReadOnly, Category = "Neelam", meta = (BindWidgetOptional)) TObjectPtr<UTextBlock> DetailSubtitle;
    UPROPERTY(BlueprintReadOnly, Category = "Neelam", meta = (BindWidgetOptional)) TObjectPtr<UTextBlock> ListTitle;
    UPROPERTY(BlueprintReadOnly, Category = "Neelam", meta = (BindWidgetOptional)) TObjectPtr<UTextBlock> HoverHint;
    UPROPERTY(BlueprintReadOnly, Category = "Neelam", meta = (BindWidgetOptional)) TObjectPtr<UButton> CloseDetailButton;
    UPROPERTY(BlueprintReadOnly, Category = "Neelam", meta = (BindWidgetOptional)) TObjectPtr<UTextBlock> EmptyText;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Neelam") TSubclassOf<UNeelamListItem> TowerTabClass;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Neelam") TSubclassOf<UNeelamListItem> FloorRowClass;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Neelam") TSubclassOf<UNeelamListItem> FlatCardClass;

    UFUNCTION(BlueprintCallable, Category = "Neelam") void InitFloorView(ANeelamFlatTour* InTour);
    UFUNCTION(BlueprintCallable, Category = "Neelam") void ShowTower(FName TowerId);
    UFUNCTION(BlueprintCallable, Category = "Neelam") void ShowFloorDetail(ANeelamTowerFloors* Tower, int32 FloorIndex);
    UFUNCTION(BlueprintCallable, Category = "Neelam") void HideFloorDetail();
    UFUNCTION(BlueprintCallable, Category = "Neelam") void SetHoveredFloor(ANeelamTowerFloors* Tower, int32 FloorIndex);

    UPROPERTY(BlueprintReadOnly, Category = "Neelam") TObjectPtr<ANeelamFlatTour> Tour;
    UPROPERTY(BlueprintReadOnly, Category = "Neelam") FName CurrentTower;

protected:
    virtual void NativeOnInitialized() override;
    UFUNCTION() void HandleTowerTab(UNeelamListItem* Item);
    UFUNCTION() void HandleFloorRow(UNeelamListItem* Item);
    UFUNCTION() void HandleFloorHover(UNeelamListItem* Item);
    UFUNCTION() void HandleFloorUnhover(UNeelamListItem* Item);
    UFUNCTION() void HandleFlatPanorama(UNeelamListItem* Item);
    UFUNCTION() void HandleCloseDetail();
    UPROPERTY() TArray<TObjectPtr<UNeelamListItem>> TabItems;
    UPROPERTY() TArray<TObjectPtr<UNeelamListItem>> FloorItems;
};

/** In-flat overlay: floor plan with room hotspots (left), room bar, exit. */
UCLASS(Abstract, Blueprintable)
class NEELAMRUNTIME_API UNeelamTourWidget : public UUserWidget
{
    GENERATED_BODY()
public:
    UPROPERTY(BlueprintReadOnly, Category = "Neelam", meta = (BindWidget)) TObjectPtr<UImage> PlanImage;
    UPROPERTY(BlueprintReadOnly, Category = "Neelam", meta = (BindWidget)) TObjectPtr<UCanvasPanel> HotspotLayer;
    UPROPERTY(BlueprintReadOnly, Category = "Neelam", meta = (BindWidget)) TObjectPtr<USizeBox> PlanBox;
    UPROPERTY(BlueprintReadOnly, Category = "Neelam", meta = (BindWidget)) TObjectPtr<UButton> ExitButton;
    UPROPERTY(BlueprintReadOnly, Category = "Neelam", meta = (BindWidgetOptional)) TObjectPtr<UTextBlock> FlatTitle;
    UPROPERTY(BlueprintReadOnly, Category = "Neelam", meta = (BindWidgetOptional)) TObjectPtr<UTextBlock> FlatInfo;
    UPROPERTY(BlueprintReadOnly, Category = "Neelam", meta = (BindWidgetOptional)) TObjectPtr<UTextBlock> RoomTitle;
    UPROPERTY(BlueprintReadOnly, Category = "Neelam", meta = (BindWidgetOptional)) TObjectPtr<UPanelWidget> RoomBar;

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Neelam") TSubclassOf<UNeelamListItem> HotspotClass;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Neelam") TSubclassOf<UNeelamListItem> RoomButtonClass;
    /** Longest side of the floor plan on screen (px at 1080p). */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Neelam") float PlanMaxHeight = 700.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Neelam") float PlanMaxWidth = 460.f;

    UFUNCTION(BlueprintCallable, Category = "Neelam") void SetupFlat(ANeelamFlatTour* InTour, FName FlatRow);
    UFUNCTION(BlueprintCallable, Category = "Neelam") void SetActiveRoom(int32 RoomIndex);

    UPROPERTY(BlueprintReadOnly, Category = "Neelam") TObjectPtr<ANeelamFlatTour> Tour;

protected:
    virtual void NativeOnInitialized() override;
    UFUNCTION() void HandleRoom(UNeelamListItem* Item);
    UFUNCTION() void HandleExit();
    UPROPERTY() TArray<TObjectPtr<UNeelamListItem>> Hotspots;
    UPROPERTY() TArray<TObjectPtr<UNeelamListItem>> RoomButtons;
};

/** Full-screen balcony photo viewer (day / night) - built in C++, no WBP needed. Opens over the 360 pawn, under the tour overlay. */
UCLASS(Blueprintable)
class NEELAMRUNTIME_API UNeelamBalconyGallery : public UUserWidget
{
    GENERATED_BODY()
public:
    UFUNCTION(BlueprintCallable, Category = "Neelam") void ShowView(const FNeelamBalconyView& View, int32 FlatFloor);
    UFUNCTION(BlueprintCallable, Category = "Neelam") void SetNight(bool bInNight);
protected:
    virtual TSharedRef<SWidget> RebuildWidget() override;
    UFUNCTION() void HandleDay();
    UFUNCTION() void HandleNight();
    void Refresh();
    UPROPERTY() TObjectPtr<UImage> Photo;
    UPROPERTY() TObjectPtr<UButton> BtnDay;
    UPROPERTY() TObjectPtr<UButton> BtnNight;
    UPROPERTY() TObjectPtr<UTextBlock> Caption;
    UPROPERTY() TObjectPtr<UTexture2D> DayTex;
    UPROPERTY() TObjectPtr<UTexture2D> NightTex;
    int32 ViewFloor = 0, FlatFloorNum = 0;
    bool bNight = false;
};
