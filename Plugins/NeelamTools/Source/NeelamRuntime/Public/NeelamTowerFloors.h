#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "NeelamTypes.h"
#include "NeelamTowerFloors.generated.h"

class UInstancedStaticMeshComponent;
class UStaticMesh;
class UMaterialInterface;

/**
 * One tower for Floor View: a clickable translucent box per floor.
 * Place it with the same transform as the building root; footprint + floors are in actor-local space.
 * Box state (per-instance custom data 0): 0 idle, 1 hover, 2 selected, -1 hidden/disabled.
 */
UCLASS(Blueprintable, meta = (DisplayName = "Neelam Tower Floors"))
class NEELAMRUNTIME_API ANeelamTowerFloors : public AActor
{
    GENERATED_BODY()
public:
    ANeelamTowerFloors();

    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Neelam") FName TowerId;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Neelam") FText DisplayName;
    /** Order in the tower tabs. */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Neelam") int32 SortOrder = 0;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Neelam") FVector2D FootprintCenter = FVector2D::ZeroVector;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Neelam") FVector2D FootprintHalfSize = FVector2D(1500.0, 1500.0);
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Neelam") float Inflate = 200.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Neelam") float VerticalGap = 30.f;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Neelam") TArray<FNeelamFloor> Floors;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Neelam") TObjectPtr<UStaticMesh> BoxMesh;
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Neelam") TObjectPtr<UMaterialInterface> BoxMaterial;
    /** Show the boxes in the editor viewport (they are always hidden in game until Floor View opens). */
    UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Neelam") bool bPreviewInEditor = false;

    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Neelam") TObjectPtr<USceneComponent> Root;
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Neelam") TObjectPtr<UInstancedStaticMeshComponent> Boxes;

    UFUNCTION(BlueprintCallable, Category = "Neelam") void RebuildBoxes();
    UFUNCTION(BlueprintCallable, Category = "Neelam") void SetFloorState(int32 FloorIndex, float State);
    UFUNCTION(BlueprintCallable, Category = "Neelam") void ResetFloorStates();
    UFUNCTION(BlueprintCallable, Category = "Neelam") void SetBoxesActive(bool bActive);
    UFUNCTION(BlueprintPure, Category = "Neelam") bool IsBoxesActive() const { return bActive; }
    UFUNCTION(BlueprintPure, Category = "Neelam") int32 FindFloorIndexByNumber(int32 Number) const;
    UFUNCTION(BlueprintPure, Category = "Neelam") FVector GetFloorCenter(int32 FloorIndex) const;
    UFUNCTION(BlueprintPure, Category = "Neelam") FVector GetTowerCenter() const;
    UFUNCTION(BlueprintPure, Category = "Neelam") float GetTowerTopZ() const;
    /** World point on the facade of FloorIndex in direction LocalYaw (+Offset sideways), pushed Outside cm out. */
    UFUNCTION(BlueprintPure, Category = "Neelam") FVector GetFacadePoint(int32 FloorIndex, float LocalYaw, float Offset, float Outside, FVector& OutNormal) const;

    virtual void OnConstruction(const FTransform& Transform) override;
    virtual void BeginPlay() override;

private:
    bool bActive = false;
    float BaseState(int32 FloorIndex) const;
};
