using UnrealBuildTool;
public class NeelamTools : ModuleRules
{
    public NeelamTools(ReadOnlyTargetRules Target) : base(Target)
    {
        PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;
        PublicDependencyModuleNames.AddRange(new string[] { "Core", "CoreUObject", "Engine" });
        PrivateDependencyModuleNames.AddRange(new string[] {
            "UnrealEd", "UMG", "UMGEditor", "Slate", "SlateCore", "InputCore", "BlueprintGraph", "Kismet", "KismetCompiler",
            "GraphEditor", "Json", "JsonUtilities", "ApplicationCore", "RenderCore", "RHI" });
    }
}
