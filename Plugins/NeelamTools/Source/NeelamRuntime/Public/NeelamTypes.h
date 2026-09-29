#pragma once
#include "CoreMinimal.h"
#include "Engine/DataTable.h"
#include "Engine/Texture.h"
#include "Engine/Texture2D.h"
#include "NeelamTypes.generated.h"

UENUM(BlueprintType)
enum class ENeelamUnitStatus : uint8
{
    Available,
    OnHold,
    Sold
};

/** One room of a unit type: a panorama + a hotspot position on the floor plan. */
USTRUCT(BlueprintType)
struct NEELAMRUNTIME_API FNeelamRoom
{
    GENERATED_BODY()
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neelam") FText Name;
    /** Equirectangular 360 image (2:1). Ignored when bUseFlatBalcony is set and the flat has its own balcony image. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neelam") TSoftObjectPtr<UTexture> Panorama;
    /** Use the flat's own balcony panorama (the view is different on every floor / flat). */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neelam") bool bUseFlatBalcony = false;
    /** Hotspot position on the floor-plan image, 0..1 (0,0 = top-left). */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neelam") FVector2D PlanPosition = FVector2D(0.5, 0.5);
    /** Initial look direction inside the panorama (degrees). */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neelam") float StartYaw = 0.f;
};

/** Row of DT_Neelam_UnitTypes (e.g. 2BHK, 3BHK). */
USTRUCT(BlueprintType)
struct NEELAMRUNTIME_API FNeelamUnitTypeRow : public FTableRowBase
{
    GENERATED_BODY()
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neelam") FText DisplayName;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neelam") FText AreaText;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neelam") TSoftObjectPtr<UTexture2D> FloorPlan;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neelam") TArray<FNeelamRoom> Rooms;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neelam") int32 StartRoom = 0;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neelam") FLinearColor Accent = FLinearColor(0.12f, 0.5f, 1.f, 1.f);
};

/** Row of DT_Neelam_Flats - one apartment. */
USTRUCT(BlueprintType)
struct NEELAMRUNTIME_API FNeelamFlatRow : public FTableRowBase
{
    GENERATED_BODY()
    /** Matches ANeelamTowerFloors::TowerId (A..E). */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neelam") FName Tower;
    /** Floor number as shown in the list (ANeelamTowerFloors::Floors[].Number). */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neelam") int32 Floor = 1;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neelam") FText FlatNumber;
    /** Row name in DT_Neelam_UnitTypes. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neelam") FName UnitType;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neelam") ENeelamUnitStatus Status = ENeelamUnitStatus::Available;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neelam") FText Facing;
    /** This flat's own balcony view (different per floor / flat). */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neelam") TSoftObjectPtr<UTexture> BalconyPanorama;
    /** Direction (tower-local yaw, degrees) from the floor centre to this flat's facade - where the camera flies in. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neelam") float FacadeYaw = 0.f;
    /** Sideways offset along that facade (cm). */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neelam") float FacadeOffset = 0.f;
};

/** One floor of a tower (actor-local heights). */
USTRUCT(BlueprintType)
struct NEELAMRUNTIME_API FNeelamFloor
{
    GENERATED_BODY()
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neelam") int32 Number = 1;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neelam") FText Label;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neelam") float BottomZ = 0.f;
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neelam") float Height = 320.f;
    /** False for refuge / service floors: shown greyed out, not selectable. */
    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Neelam") bool bResidential = true;
};
