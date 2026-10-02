#include "NeelamFlatTour.h"
#include "Components/TimelineComponent.h"
#include "NeelamTowerFloors.h"
#include "NeelamWidgets.h"
#include "Engine/DataTable.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "TimerManager.h"
#include "Camera/CameraActor.h"
#include "Camera/CameraComponent.h"
#include "Camera/PlayerCameraManager.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/Pawn.h"
#include "Components/StaticMeshComponent.h"
#include "Components/InstancedStaticMeshComponent.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Blueprint/UserWidget.h"
#include "Kismet/GameplayStatics.h"
#include "InputCoreTypes.h"
#include "Algo/Sort.h"
#include "Blueprint/WidgetTree.h"
#include "Components/Button.h"

ANeelamFlatTour::ANeelamFlatTour()
{
    PrimaryActorTick.bCanEverTick = true;
    PrimaryActorTick.bStartWithTickEnabled = true;
    RootComponent = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
}

ANeelamFlatTour* ANeelamFlatTour::GetFlatTour(const UObject* WorldContext)
{
    UWorld* W = WorldContext ? WorldContext->GetWorld() : nullptr;
    if (!W) return nullptr;
    for (TActorIterator<ANeelamFlatTour> It(W); It; ++It) return *It;
    return nullptr;
}

APlayerController* ANeelamFlatTour::PC() const
{
    return GetWorld() ? GetWorld()->GetFirstPlayerController() : nullptr;
}

void ANeelamFlatTour::BeginPlay()
{
    Super::BeginPlay();
    GatherTowers();
}

void ANeelamFlatTour::GatherTowers()
{
    Towers.Reset();
    for (TActorIterator<ANeelamTowerFloors> It(GetWorld()); It; ++It) Towers.Add(*It);
    Algo::Sort(Towers, [](const TObjectPtr<ANeelamTowerFloors>& A, const TObjectPtr<ANeelamTowerFloors>& B)
    { return A->SortOrder != B->SortOrder ? A->SortOrder < B->SortOrder : A->TowerId.LexicalLess(B->TowerId); });
}

// ------------------------------------------------------------------ data
ANeelamTowerFloors* ANeelamFlatTour::FindTower(FName TowerId) const
{
    for (ANeelamTowerFloors* T : Towers) if (T && T->TowerId == TowerId) return T;
    return nullptr;
}

TArray<FName> ANeelamFlatTour::GetFlatsOnFloor(FName TowerId, int32 FloorNumber) const
{
    TArray<FName> Out;
    if (!FlatsTable) return Out;
    for (const TPair<FName, uint8*>& P : FlatsTable->GetRowMap())
    {
        const FNeelamFlatRow* R = reinterpret_cast<const FNeelamFlatRow*>(P.Value);
        if (R && R->Tower == TowerId && R->Floor == FloorNumber) Out.Add(P.Key);
    }
    return Out;
}

bool ANeelamFlatTour::GetFlat(FName FlatRow, FNeelamFlatRow& Out) const
{
    const FNeelamFlatRow* R = FlatsTable ? FlatsTable->FindRow<FNeelamFlatRow>(FlatRow, TEXT("Neelam"), false) : nullptr;
    if (R) Out = *R;
    return R != nullptr;
}

bool ANeelamFlatTour::GetUnitType(FName UnitType, FNeelamUnitTypeRow& Out) const
{
    const FNeelamUnitTypeRow* R = UnitTypesTable ? UnitTypesTable->FindRow<FNeelamUnitTypeRow>(UnitType, TEXT("Neelam"), false) : nullptr;
    if (R) Out = *R;
    return R != nullptr;
}

// ------------------------------------------------------------------ template glue (reflection, no hard BP dependency)
static bool SetNumberProp(UObject* O, FName Name, double V)
{
    if (!O) return false;
    FProperty* P = O->GetClass()->FindPropertyByName(Name);
    if (FNumericProperty* N = CastField<FNumericProperty>(P))
    {
        void* Ptr = N->ContainerPtrToValuePtr<void>(O);
        if (N->IsFloatingPoint()) N->SetFloatingPointPropertyValue(Ptr, V); else N->SetIntPropertyValue(Ptr, (int64)V);
        return true;
    }
    return false;
}
static bool SetVectorProp(UObject* O, FName Name, const FVector& V)
{
    if (!O) return false;
    FStructProperty* P = CastField<FStructProperty>(O->GetClass()->FindPropertyByName(Name));
    if (P && P->Struct == TBaseStructure<FVector>::Get()) { *P->ContainerPtrToValuePtr<FVector>(O) = V; return true; }
    return false;
}
static bool SetBoolProp(UObject* O, FName Name, bool V)
{
    if (!O) return false;
    FBoolProperty* P = CastField<FBoolProperty>(O->GetClass()->FindPropertyByName(Name));
    if (P) { P->SetPropertyValue_InContainer(O, V); return true; }
    return false;
}
static bool GetBoolProp(UObject* O, FName Name, bool Default)
{
    FBoolProperty* P = O ? CastField<FBoolProperty>(O->GetClass()->FindPropertyByName(Name)) : nullptr;
    return P ? P->GetPropertyValue_InContainer(O) : Default;
}
static UObject* GetObjectProp(UObject* O, FName Name)
{
    if (!O) return nullptr;
    FObjectPropertyBase* P = CastField<FObjectPropertyBase>(O->GetClass()->FindPropertyByName(Name));
    return P ? P->GetObjectPropertyValue_InContainer(O) : nullptr;
}
static bool CallNoParams(UObject* O, FName Fn)
{
    UFunction* F = O ? O->FindFunction(Fn) : nullptr;
    if (!F || F->ParmsSize > 0) return false;
    O->ProcessEvent(F, nullptr);
    return true;
}

bool ANeelamFlatTour::CallSwitchPawn(uint8 PawnType)
{
    APlayerController* P = PC();
    UFunction* F = P ? P->FindFunction(TEXT("Switch_Pawn")) : nullptr;
    if (!F) return false;
    uint8* Parms = (uint8*)FMemory_Alloca(FMath::Max<int32>(F->ParmsSize, 1));
    FMemory::Memzero(Parms, F->ParmsSize);
    for (TFieldIterator<FProperty> It(F); It && It->HasAnyPropertyFlags(CPF_Parm); ++It) It->InitializeValue_InContainer(Parms);
    for (TFieldIterator<FProperty> It(F); It && It->HasAnyPropertyFlags(CPF_Parm); ++It)
    {
        void* Ptr = It->ContainerPtrToValuePtr<void>(Parms);
        if (FEnumProperty* E = CastField<FEnumProperty>(*It)) E->GetUnderlyingProperty()->SetIntPropertyValue(Ptr, (int64)PawnType);
        else if (FByteProperty* B = CastField<FByteProperty>(*It)) B->SetIntPropertyValue(Ptr, (int64)PawnType);
        break;
    }
    P->ProcessEvent(F, Parms);
    for (TFieldIterator<FProperty> It(F); It && It->HasAnyPropertyFlags(CPF_Parm); ++It) It->DestroyValue_InContainer(Parms);
    return true;
}

void ANeelamFlatTour::FocusPawn(const FVector& Location, float Pitch, float Yaw, float ArmLength)
{
    APawn* P = MainPawn ? MainPawn.Get() : (PC() ? PC()->GetPawn() : nullptr);
    if (!P) return;
    SetVectorProp(P, TEXT("Location_New"), Location);
    SetNumberProp(P, TEXT("Pitch_New"), Pitch);
    SetNumberProp(P, TEXT("Yaw_New"), Yaw);
    SetNumberProp(P, TEXT("TargetArmLength_New"), ArmLength);
    CallNoParams(P, TEXT("Focus"));
}

void ANeelamFlatTour::SetMasterMenuVisible(bool bVisible)
{
    if (UUserWidget* W = Cast<UUserWidget>(GetObjectProp(PC(), TEXT("MasterMenu"))))
        W->SetVisibility(bVisible ? ESlateVisibility::SelfHitTestInvisible : ESlateVisibility::Collapsed);
}

void ANeelamFlatTour::SetPoiLayerHidden(bool bHide)
{
    // surroundings pins / routes (template BP_POI + BP_Route) - hidden while Floor View is open
    for (TActorIterator<AActor> It(GetWorld()); It; ++It)
    {
        const FString CN = It->GetClass()->GetName();
        if (CN == TEXT("BP_POI_C")) CallNoParams(*It, bHide ? TEXT("Hide_POI") : TEXT("Show_POI"));
        else if (CN == TEXT("BP_Route_C")) CallNoParams(*It, bHide ? TEXT("Hide_Route") : TEXT("Show_Route"));
    }
}

void ANeelamFlatTour::SetSphereTexture(UTexture* Tex)
{
    if (!Tex) return;
    for (TActorIterator<AActor> It(GetWorld()); It; ++It)
    {
        if (It->GetClass()->GetName() != TEXT("BP_360Sphere_C")) continue;
        TArray<UStaticMeshComponent*> Comps; It->GetComponents(Comps);
        for (UStaticMeshComponent* C : Comps)
        {
            UMaterialInstanceDynamic* M = Cast<UMaterialInstanceDynamic>(C->GetMaterial(0));
            if (!M) M = C->CreateDynamicMaterialInstance(0);
            if (M) M->SetTextureParameterValue(TEXT("HDR_Texture"), Tex);
        }
    }
}

void ANeelamFlatTour::Fade(float From, float To, float Duration, bool bHold)
{
    if (APlayerController* P = PC()) if (P->PlayerCameraManager)
        P->PlayerCameraManager->StartCameraFade(From, To, Duration, FLinearColor::Black, false, bHold);
}

// ------------------------------------------------------------------ floor view
void ANeelamFlatTour::ActivateFloorView()
{
    if (State != ENeelamTourState::Off) return;
    GatherTowers();
    if (APlayerController* P = PC()) MainPawn = P->GetPawn();
    if (MainPawn && !bIdleSuppressed)
    {
        // the template pawn starts an idle auto-orbit after 15 s - it swung Tower E out of frame
        bSavedAllowIdle = GetBoolProp(MainPawn, TEXT("Allow_Idle?"), true);
        SetBoolProp(MainPawn, TEXT("Allow_Idle?"), false);
        SetNumberProp(MainPawn, TEXT("Idle_Timer"), 0.0);
        if (UTimelineComponent* TL = Cast<UTimelineComponent>(GetObjectProp(MainPawn, TEXT("Timeline_Idle")))) TL->Stop();   // an orbit already running
        bIdleSuppressed = true;
    }
    State = ENeelamTourState::FloorView;
    for (ANeelamTowerFloors* T : Towers) if (T) T->SetBoxesActive(true);
    SetPoiLayerHidden(true);
    if (!FloorViewWidget && FloorViewWidgetClass && PC()) FloorViewWidget = CreateWidget<UNeelamFloorViewWidget>(PC(), FloorViewWidgetClass);
    if (FloorViewWidget)
    {
        if (!FloorViewWidget->IsInViewport()) FloorViewWidget->AddToViewport(5);
        FloorViewWidget->SetVisibility(ESlateVisibility::SelfHitTestInvisible);
        FloorViewWidget->InitFloorView(this);
    }
    // always open on the Floor View start camera; a previously selected floor stays highlighted + in the detail panel
    if (SelectedTower && SelectedFloor != INDEX_NONE) SelectFloor(SelectedTower, SelectedFloor, false);
    FocusOverview();
}

void ANeelamFlatTour::DeactivateFloorView()
{
    if (State != ENeelamTourState::FloorView) return;
    State = ENeelamTourState::Off;
    if (bIdleSuppressed && MainPawn) { SetBoolProp(MainPawn, TEXT("Allow_Idle?"), bSavedAllowIdle); SetNumberProp(MainPawn, TEXT("Idle_Timer"), 0.0); }
    bIdleSuppressed = false;
    for (ANeelamTowerFloors* T : Towers) if (T) T->SetBoxesActive(false);
    if (FloorViewWidget) FloorViewWidget->RemoveFromParent();
    FloorViewWidget = nullptr;
    HoveredTower = nullptr; HoveredFloor = INDEX_NONE;
}

void ANeelamFlatTour::FocusOverview()
{
    if (!Towers.Num()) return;
    ANeelamTowerFloors* Focus = SelectedTower ? SelectedTower.Get() : nullptr;
    if (FloorViewWidget) if (ANeelamTowerFloors* T = FindTower(FloorViewWidget->CurrentTower)) Focus = T;
    FVector C = FVector::ZeroVector;
    if (Focus) C = Focus->GetTowerCenter() + OverviewPivotOffset;
    else { for (ANeelamTowerFloors* T : Towers) C += T->GetTowerCenter(); C /= Towers.Num(); }
    FocusPawn(C, OverviewPitch, OverviewYaw, Focus ? OverviewArmLength * 0.75f : OverviewArmLength);
}

void ANeelamFlatTour::ClearSelection()
{
    if (SelectedTower && SelectedFloor != INDEX_NONE) SelectedTower->SetFloorState(SelectedFloor, 0.f);
    SelectedTower = nullptr; SelectedFloor = INDEX_NONE;
}

void ANeelamFlatTour::HoverFloor(ANeelamTowerFloors* Tower, int32 FloorIndex)
{
    if (Tower == HoveredTower && FloorIndex == HoveredFloor) return;
    if (HoveredTower && HoveredFloor != INDEX_NONE && !(HoveredTower == SelectedTower && HoveredFloor == SelectedFloor))
        HoveredTower->SetFloorState(HoveredFloor, 0.f);
    HoveredTower = Tower; HoveredFloor = Tower ? FloorIndex : INDEX_NONE;
    if (HoveredTower && HoveredFloor != INDEX_NONE && !(HoveredTower == SelectedTower && HoveredFloor == SelectedFloor))
        HoveredTower->SetFloorState(HoveredFloor, 1.f);
    if (FloorViewWidget) FloorViewWidget->SetHoveredFloor(HoveredTower, HoveredFloor);
    OnFloorHovered.Broadcast(HoveredTower, HoveredFloor);
}

void ANeelamFlatTour::SelectFloor(ANeelamTowerFloors* Tower, int32 FloorIndex, bool bFocusCamera)
{
    if (!Tower || !Tower->Floors.IsValidIndex(FloorIndex) || !Tower->Floors[FloorIndex].bResidential) return;
    if (SelectedTower && SelectedFloor != INDEX_NONE) SelectedTower->SetFloorState(SelectedFloor, 0.f);
    SelectedTower = Tower; SelectedFloor = FloorIndex;
    Tower->SetFloorState(FloorIndex, 2.f);
    if (bFocusCamera)
    {
        // look at the floor from the side of its first flat (or the default overview side)
        float Yaw = OverviewYaw;
        const TArray<FName> Flats = GetFlatsOnFloor(Tower->TowerId, Tower->Floors[FloorIndex].Number);
        FNeelamFlatRow Row;
        if (Flats.Num() && GetFlat(Flats[0], Row))
        {
            FVector N; Tower->GetFacadePoint(FloorIndex, Row.FacadeYaw, 0.f, 0.f, N);
            Yaw = (-N).Rotation().Yaw;
        }
        FocusPawn(Tower->GetFloorCenter(FloorIndex), FloorPitch, Yaw, FloorArmLength);
    }
    if (FloorViewWidget) FloorViewWidget->ShowFloorDetail(Tower, FloorIndex);
    OnFloorSelected.Broadcast(Tower, FloorIndex);
}

void ANeelamFlatTour::UpdatePicking()
{
    APlayerController* P = PC();
    if (!P) return;
    ANeelamTowerFloors* HitTower = nullptr; int32 HitFloor = INDEX_NONE;
    FHitResult Hit;
    if (P->GetHitResultUnderCursorByChannel(UEngineTypes::ConvertToTraceType(ECC_Visibility), false, Hit))
    {
        if (ANeelamTowerFloors* T = Cast<ANeelamTowerFloors>(Hit.GetActor()))
            if (Hit.GetComponent() == T->Boxes.Get() && T->Floors.IsValidIndex(Hit.Item) && T->Floors[Hit.Item].bResidential) { HitTower = T; HitFloor = Hit.Item; }
    }
    HoverFloor(HitTower, HitFloor);

    float MX = 0, MY = 0; P->GetMousePosition(MX, MY);
    if (P->WasInputKeyJustPressed(EKeys::LeftMouseButton)) { bPressed = true; PressPos = FVector2D(MX, MY); }
    if (bPressed && P->WasInputKeyJustReleased(EKeys::LeftMouseButton))
    {
        bPressed = false;
        if (FVector2D::Distance(PressPos, FVector2D(MX, MY)) <= ClickTolerance && HitTower) SelectFloor(HitTower, HitFloor, true);
    }
}

void ANeelamFlatTour::PollMenuTab()
{
    UUserWidget* Menu = Cast<UUserWidget>(GetObjectProp(PC(), TEXT("MasterMenu")));
    if (!Menu) return;
    if (!MenuTab.IsValid() || MenuTabOwner.Get() != Menu)
    {
        MenuTab = nullptr; MenuTabOwner = Menu;
        if (Menu->WidgetTree) Menu->WidgetTree->ForEachWidget([this](UWidget* W) { if (UNeelamFloorViewTab* T = Cast<UNeelamFloorViewTab>(W)) MenuTab = T; });
    }
    UNeelamFloorViewTab* Tab = MenuTab.Get();
    if (!Tab) return;
    // make the taskbar highlight treat our button like the template ones
    if (FArrayProperty* AP = CastField<FArrayProperty>(Menu->GetClass()->FindPropertyByName(TEXT("Buttons_TaskBar"))))
        if (FObjectPropertyBase* Inner = CastField<FObjectPropertyBase>(AP->Inner))
            if (UButton* Btn = Menu->WidgetTree ? Cast<UButton>(Menu->WidgetTree->FindWidget(Tab->TaskbarButtonName)) : nullptr)
            {
                FScriptArrayHelper Arr(AP, AP->ContainerPtrToValuePtr<void>(Menu));
                bool bHas = false;
                for (int32 i = 0; i < Arr.Num() && !bHas; ++i) bHas = Inner->GetObjectPropertyValue(Arr.GetRawPtr(i)) == Btn;
                if (!bHas && Arr.Num() > 0) { const int32 N = Arr.AddValue(); Inner->SetObjectPropertyValue(Arr.GetRawPtr(N), Btn); }
            }
    const bool bNow = Tab->IsActivePage() && Menu->IsVisible();
    if (bNow && State == ENeelamTourState::Off) { Tab->bTabActive = true; ActivateFloorView(); }
    else if (!bNow && State == ENeelamTourState::FloorView && Menu->IsVisible()) { Tab->bTabActive = false; DeactivateFloorView(); }
}

void ANeelamFlatTour::Tick(float Dt)
{
    Super::Tick(Dt);
    if (State == ENeelamTourState::Off || State == ENeelamTourState::FloorView) PollMenuTab();
    if (State == ENeelamTourState::FloorView) UpdatePicking();
    else if (State == ENeelamTourState::Flying) TickFly(Dt);
}

// ------------------------------------------------------------------ tour
static FVector Bezier(const FVector& A, const FVector& B, const FVector& C, const FVector& D, float T)
{
    const float U = 1.f - T;
    return U * U * U * A + 3.f * U * U * T * B + 3.f * U * T * T * C + T * T * T * D;
}

void ANeelamFlatTour::StartTour(FName FlatRow)
{
    if (State != ENeelamTourState::FloorView) return;
    FNeelamFlatRow Flat; FNeelamUnitTypeRow Type;
    if (!GetFlat(FlatRow, Flat) || !GetUnitType(Flat.UnitType, Type)) return;
    ANeelamTowerFloors* T = FindTower(Flat.Tower);
    const int32 FI = T ? T->FindFloorIndexByNumber(Flat.Floor) : INDEX_NONE;
    APlayerController* P = PC();
    if (!T || FI == INDEX_NONE || !P || !P->PlayerCameraManager) return;

    CurrentFlat = FlatRow;
    FVector N;
    const FVector End = T->GetFacadePoint(FI, Flat.FacadeYaw, Flat.FacadeOffset, FlyEndDistance, N);
    FlyLookAt = T->GetFacadePoint(FI, Flat.FacadeYaw, Flat.FacadeOffset, -600.f, N);
    FlyP0 = P->PlayerCameraManager->GetCameraLocation();
    FlyStartRot = P->PlayerCameraManager->GetCameraRotation();
    FlyStartFov = P->PlayerCameraManager->GetFOVAngle();
    FlyP3 = End;
    FlyP2 = End + N * (FlyApproachDistance * 0.35f);
    FlyP1 = End + N * FlyApproachDistance + FVector(0, 0, 1200.f);
    // keep the first control point on the camera's side so the path does not cut through the tower
    FlyP1 = FMath::Lerp(FlyP1, FlyP0, 0.35f);

    if (!FlyCamera)
    {
        FActorSpawnParameters SP; SP.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
        FlyCamera = GetWorld()->SpawnActor<ACameraActor>(FlyP0, FlyStartRot, SP);
        if (FlyCamera && FlyCamera->GetCameraComponent()) FlyCamera->GetCameraComponent()->bConstrainAspectRatio = false;
    }
    FlyCamera->SetActorLocationAndRotation(FlyP0, FlyStartRot);
    if (FlyCamera->GetCameraComponent()) FlyCamera->GetCameraComponent()->SetFieldOfView(FlyStartFov);
    P->SetViewTarget(FlyCamera);
    FlyT = 0.f; bFadeStarted = false;
    State = ENeelamTourState::Flying;
    if (FloorViewWidget) FloorViewWidget->SetVisibility(ESlateVisibility::Collapsed);
    SetMasterMenuVisible(false);
    HoverFloor(nullptr, INDEX_NONE);
    for (ANeelamTowerFloors* TW : Towers) if (TW) TW->SetBoxesActive(false);

    // preload this flat's panoramas (we are about to go black anyway)
    LoadedTextures.Reset();
    for (const FNeelamRoom& R : Type.Rooms) if (UTexture* Tex = ResolveRoomTexture(Flat, R)) LoadedTextures.Add(Tex);
}

void ANeelamFlatTour::TickFly(float Dt)
{
    APlayerController* P = PC();
    if (!FlyCamera || !P) return;
    FlyT = FMath::Min(1.f, FlyT + Dt / FMath::Max(0.1f, FlyDuration));
    const float A = FMath::InterpEaseInOut(0.f, 1.f, FlyT, 2.2f);
    const FVector Pos = Bezier(FlyP0, FlyP1, FlyP2, FlyP3, A);
    const FQuat Look = (FlyLookAt - Pos).Rotation().Quaternion();
    const float RA = FMath::SmoothStep(0.f, 0.45f, FlyT);
    const FQuat Q = FQuat::Slerp(FlyStartRot.Quaternion(), Look, RA);
    FlyCamera->SetActorLocationAndRotation(Pos, Q);
    if (FlyCamera->GetCameraComponent()) FlyCamera->GetCameraComponent()->SetFieldOfView(FMath::Lerp(FlyStartFov, 70.f, A));
    const float FadeStart = 1.f - FadeOutDuration / FMath::Max(0.1f, FlyDuration);
    if (!bFadeStarted && FlyT >= FadeStart) { bFadeStarted = true; Fade(0.f, 1.f, FadeOutDuration, true); }
    if (FlyT >= 1.f)
    {
        State = ENeelamTourState::InTour;   // stop ticking the fly
        GetWorldTimerManager().SetTimer(TimerA, FTimerDelegate::CreateUObject(this, &ANeelamFlatTour::EnterPanorama), 0.12f, false);
    }
}

UTexture* ANeelamFlatTour::ResolveRoomTexture(const FNeelamFlatRow& Flat, const FNeelamRoom& Room) const
{
    if (Room.bUseFlatBalcony && !Flat.BalconyPanorama.IsNull())
        if (UTexture* T = Flat.BalconyPanorama.LoadSynchronous()) return T;
    return Room.Panorama.LoadSynchronous();
}

void ANeelamFlatTour::EnterPanorama()
{
    APlayerController* P = PC();
    if (!P) return;
    CallSwitchPawn(1);   // template: possess the 360 pawn inside BP_360Sphere, hide main menu
    if (UUserWidget* M = Cast<UUserWidget>(GetObjectProp(P, TEXT("360Menu")))) M->SetVisibility(ESlateVisibility::Collapsed);
    if (FlyCamera) { FlyCamera->Destroy(); FlyCamera = nullptr; }
    if (P->GetPawn()) P->SetViewTarget(P->GetPawn());

    FNeelamFlatRow Flat; FNeelamUnitTypeRow Type;
    GetFlat(CurrentFlat, Flat); GetUnitType(Flat.UnitType, Type);
    if (!TourWidget && TourWidgetClass) TourWidget = CreateWidget<UNeelamTourWidget>(P, TourWidgetClass);
    if (TourWidget)
    {
        if (!TourWidget->IsInViewport()) TourWidget->AddToViewport(10);
        TourWidget->SetVisibility(ESlateVisibility::SelfHitTestInvisible);
        TourWidget->SetupFlat(this, CurrentFlat);
    }
    ApplyRoom(Type.Rooms.IsValidIndex(Type.StartRoom) ? Type.StartRoom : 0);
    Fade(1.f, 0.f, FadeInDuration, false);
}

void ANeelamFlatTour::ApplyRoom(int32 RoomIndex)
{
    FNeelamFlatRow Flat; FNeelamUnitTypeRow Type;
    if (!GetFlat(CurrentFlat, Flat) || !GetUnitType(Flat.UnitType, Type) || !Type.Rooms.IsValidIndex(RoomIndex)) return;
    CurrentRoom = RoomIndex;
    const FNeelamRoom& R = Type.Rooms[RoomIndex];
    FNeelamBalconyView View;
    // a flat with its own balcony panorama (top floor) keeps the 360; the others get the photo gallery of the nearest floor
    const bool bGallery = R.bUseFlatBalcony && Flat.BalconyPanorama.IsNull() && FindBalconyView(Flat.Floor, View);
    if (!bGallery) SetSphereTexture(ResolveRoomTexture(Flat, R));
    if (bGallery && !Gallery) if (APlayerController* GP = PC()) Gallery = CreateWidget<UNeelamBalconyGallery>(GP, UNeelamBalconyGallery::StaticClass());
    if (Gallery)
    {
        if (bGallery) { if (!Gallery->IsInViewport()) Gallery->AddToViewport(9); Gallery->ShowView(View, Flat.Floor); }
        else Gallery->SetVisibility(ESlateVisibility::Collapsed);
    }
    if (APlayerController* P = PC()) P->SetControlRotation(FRotator(0.f, R.StartYaw, 0.f));
    if (TourWidget) TourWidget->SetActiveRoom(RoomIndex);
    OnRoomShown.Broadcast(CurrentFlat, RoomIndex);
}

void ANeelamFlatTour::ShowRoom(int32 RoomIndex)
{
    if (State != ENeelamTourState::InTour || bRoomSwitching || RoomIndex == CurrentRoom) return;
    bRoomSwitching = true;
    Fade(0.f, 1.f, RoomFadeDuration, true);
    GetWorldTimerManager().SetTimer(TimerA, FTimerDelegate::CreateLambda([this, RoomIndex]()
    {
        ApplyRoom(RoomIndex);
        Fade(1.f, 0.f, RoomFadeDuration * 1.3f, false);
        bRoomSwitching = false;
    }), RoomFadeDuration + 0.03f, false);
}

void ANeelamFlatTour::EndTour()
{
    if (State != ENeelamTourState::InTour || bRoomSwitching) return;
    State = ENeelamTourState::Leaving;
    Fade(0.f, 1.f, 0.45f, true);
    GetWorldTimerManager().SetTimer(TimerA, FTimerDelegate::CreateUObject(this, &ANeelamFlatTour::FinishEndTour), 0.5f, false);
}

void ANeelamFlatTour::FinishEndTour()
{
    if (TourWidget) TourWidget->RemoveFromParent();
    TourWidget = nullptr;
    if (Gallery) Gallery->RemoveFromParent();
    Gallery = nullptr;
    CallSwitchPawn(0);   // template: back to the main pawn, main menu + POIs restored
    if (APlayerController* P = PC()) if (P->GetPawn()) P->SetViewTarget(P->GetPawn());
    CurrentRoom = INDEX_NONE;
    LoadedTextures.Reset();
    State = ENeelamTourState::Off;
    ActivateFloorView();           // back in Floor View, same floor selected
    SetMasterMenuVisible(true);
    Fade(1.f, 0.f, FadeInDuration, false);
}

bool ANeelamFlatTour::FindBalconyView(int32 Floor, FNeelamBalconyView& OutView) const
{
    int32 Best = INDEX_NONE, BestD = MAX_int32;
    for (int32 i = 0; i < BalconyViews.Num(); ++i)
    {
        if (BalconyViews[i].Day.IsNull() && BalconyViews[i].Night.IsNull()) continue;
        const int32 D = FMath::Abs(BalconyViews[i].Floor - Floor);
        if (D < BestD) { BestD = D; Best = i; }
    }
    if (Best == INDEX_NONE) return false;
    OutView = BalconyViews[Best];
    return true;
}
