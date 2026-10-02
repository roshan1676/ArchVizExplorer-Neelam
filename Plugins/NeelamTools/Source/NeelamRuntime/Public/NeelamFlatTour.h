#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "NeelamTypes.h"
#include "NeelamFlatTour.generated.h"

class ANeelamTowerFloors;
class UNeelamFloorViewWidget;
class UNeelamTourWidget; class UNeelamBalconyGallery;
class UDataTable;
class ACameraActor;
class APawn;

UENUM(BlueprintType)
enum class ENeelamTourState : uint8
{
    Off,
    FloorView,
    Flying,
    InTour,
    Leaving
};

DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FNeelamFloorEvent, ANeelamTowerFloors*, Tower, int32, FloorIndex);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FNeelamRoomEvent, FName, Flat, int32, RoomIndex);

/**
 * Drives Floor View + flat tours. Put ONE in the level.
 *  Floor View tab -> ActivateFloorView(): tower floor boxes + floor list widget.
 *  Floor selected -> camera focuses the floor, detail panel lists the flats (DT_Neelam_Flats).
 *  "360 Panorama" -> StartTour(flat): camera flies to the flat facade, fades to black, the template 360 pawn/sphere
 *  shows the room panoramas (DT_Neelam_UnitTypes), floor plan with room hotspots on the left.
 */
UCLASS(Blueprintable, meta = (DisplayName = "Neelam Flat Tour"))
class NEELAMRUNTIME_API ANeelamFlatTour : public AActor
{
    GENERATED_BODY()
public:
    ANeelamFlatTour();

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Neelam|Data") TObjectPtr<UDataTable> FlatsTable;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Neelam|Data") TObjectPtr<UDataTable> UnitTypesTable;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Neelam|UI") TSubclassOf<UNeelamFloorViewWidget> FloorViewWidgetClass;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Neelam|UI") TSubclassOf<UNeelamTourWidget> TourWidgetClass;
    /** Balcony photo sets per floor (day / night). When set, a flat's Balcony room shows these as a gallery instead of a panorama. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Neelam") TArray<FNeelamBalconyView> BalconyViews;
    UFUNCTION(BlueprintPure, Category = "Neelam") bool FindBalconyView(int32 Floor, FNeelamBalconyView& OutView) const;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neelam|Camera") float OverviewArmLength = 45000.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neelam|Camera") float OverviewPitch = -8.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neelam|Camera") float OverviewYaw = 47.f;
    /** added to the focused tower centre for the Floor View start camera (world cm) (0 = tower centred on screen) */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neelam|Camera") FVector OverviewPivotOffset = FVector::ZeroVector;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neelam|Camera") float FloorArmLength = 17000.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neelam|Camera") float FloorPitch = -6.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neelam|Camera") float FlyDuration = 3.2f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neelam|Camera") float FlyEndDistance = 350.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neelam|Camera") float FlyApproachDistance = 5000.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neelam|Camera") float FadeOutDuration = 0.7f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neelam|Camera") float FadeInDuration = 0.9f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neelam|Camera") float RoomFadeDuration = 0.35f;
    /** Mouse movement (px) allowed between press and release for a click on a floor box. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neelam|Input") float ClickTolerance = 8.f;

    UPROPERTY(BlueprintReadOnly, Category = "Neelam") ENeelamTourState State = ENeelamTourState::Off;
    UPROPERTY(BlueprintReadOnly, Category = "Neelam") TArray<TObjectPtr<ANeelamTowerFloors>> Towers;
    UPROPERTY(BlueprintReadOnly, Category = "Neelam") TObjectPtr<ANeelamTowerFloors> SelectedTower;
    UPROPERTY(BlueprintReadOnly, Category = "Neelam") int32 SelectedFloor = INDEX_NONE;
    UPROPERTY(BlueprintReadOnly, Category = "Neelam") TObjectPtr<ANeelamTowerFloors> HoveredTower;
    UPROPERTY(BlueprintReadOnly, Category = "Neelam") int32 HoveredFloor = INDEX_NONE;
    UPROPERTY(BlueprintReadOnly, Category = "Neelam") FName CurrentFlat;
    UPROPERTY(BlueprintReadOnly, Category = "Neelam") int32 CurrentRoom = INDEX_NONE;
    UPROPERTY(BlueprintReadOnly, Category = "Neelam") TObjectPtr<UNeelamFloorViewWidget> FloorViewWidget;
    UPROPERTY(BlueprintReadOnly, Category = "Neelam") TObjectPtr<UNeelamTourWidget> TourWidget;
    UPROPERTY(BlueprintReadOnly, Category = "Neelam") TObjectPtr<UNeelamBalconyGallery> Gallery;

    UPROPERTY(BlueprintAssignable, Category = "Neelam") FNeelamFloorEvent OnFloorSelected;
    UPROPERTY(BlueprintAssignable, Category = "Neelam") FNeelamFloorEvent OnFloorHovered;
    UPROPERTY(BlueprintAssignable, Category = "Neelam") FNeelamRoomEvent OnRoomShown;

    UFUNCTION(BlueprintPure, Category = "Neelam", meta = (WorldContext = "WorldContext")) static ANeelamFlatTour* GetFlatTour(const UObject* WorldContext);

    UFUNCTION(BlueprintCallable, Category = "Neelam") void ActivateFloorView();
    UFUNCTION(BlueprintCallable, Category = "Neelam") void DeactivateFloorView();
    UFUNCTION(BlueprintCallable, Category = "Neelam") void FocusOverview();
    UFUNCTION(BlueprintCallable, Category = "Neelam") void SelectFloor(ANeelamTowerFloors* Tower, int32 FloorIndex, bool bFocusCamera = true);
    UFUNCTION(BlueprintCallable, Category = "Neelam") void HoverFloor(ANeelamTowerFloors* Tower, int32 FloorIndex);
    UFUNCTION(BlueprintCallable, Category = "Neelam") void ClearSelection();
    UFUNCTION(BlueprintCallable, Category = "Neelam") void StartTour(FName FlatRow);
    UFUNCTION(BlueprintCallable, Category = "Neelam") void ShowRoom(int32 RoomIndex);
    UFUNCTION(BlueprintCallable, Category = "Neelam") void EndTour();

    UFUNCTION(BlueprintPure, Category = "Neelam") ANeelamTowerFloors* FindTower(FName TowerId) const;
    UFUNCTION(BlueprintPure, Category = "Neelam") TArray<FName> GetFlatsOnFloor(FName TowerId, int32 FloorNumber) const;
    UFUNCTION(BlueprintPure, Category = "Neelam") bool GetFlat(FName FlatRow, FNeelamFlatRow& OutFlat) const;
    UFUNCTION(BlueprintPure, Category = "Neelam") bool GetUnitType(FName UnitType, FNeelamUnitTypeRow& OutType) const;
    UFUNCTION(BlueprintPure, Category = "Neelam") bool IsBusy() const { return State == ENeelamTourState::Flying || State == ENeelamTourState::Leaving || bRoomSwitching; }

    virtual void BeginPlay() override;
    virtual void Tick(float DeltaSeconds) override;

private:
    APlayerController* PC() const;
    void GatherTowers();
    void UpdatePicking();
    void PollMenuTab();
    void TickFly(float Dt);
    void EnterPanorama();
    void ApplyRoom(int32 RoomIndex);
    void FinishEndTour();
    void FocusPawn(const FVector& Location, float Pitch, float Yaw, float ArmLength);
    void SetMasterMenuVisible(bool bVisible);
    void SetPoiLayerHidden(bool bHide);
    bool CallSwitchPawn(uint8 PawnType);
    UTexture* ResolveRoomTexture(const FNeelamFlatRow& Flat, const FNeelamRoom& Room) const;
    void SetSphereTexture(UTexture* Tex);
    void Fade(float From, float To, float Duration, bool bHold);

    UPROPERTY() TObjectPtr<ACameraActor> FlyCamera;
    TWeakObjectPtr<class UNeelamFloorViewTab> MenuTab;
    TWeakObjectPtr<UUserWidget> MenuTabOwner;
    UPROPERTY() TObjectPtr<APawn> MainPawn;
    UPROPERTY() TArray<TObjectPtr<UTexture>> LoadedTextures;
    FVector FlyP0, FlyP1, FlyP2, FlyP3, FlyLookAt;
    FRotator FlyStartRot;
    float FlyT = 0.f;
    float FlyStartFov = 90.f;
    bool bFadeStarted = false;
    bool bRoomSwitching = false;
    FVector2D PressPos = FVector2D::ZeroVector;
    bool bPressed = false;
    bool bSavedAllowIdle = true;   // template pawn "Allow_Idle?" (auto-orbit after 15 s) - off while Floor View is open
    bool bIdleSuppressed = false;
    FTimerHandle TimerA;
};
