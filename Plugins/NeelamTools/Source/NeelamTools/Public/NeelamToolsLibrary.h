#pragma once
#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "NeelamToolsLibrary.generated.h"

class UBlueprint; class UWidgetBlueprint; class UWidget; class UUserWidget;

/** Editor automation exposed to Python as unreal.NeelamToolsLibrary.* (all return human/JSON-readable results). */
class UTextureRenderTarget2D;

UCLASS()
class UNeelamToolsLibrary : public UBlueprintFunctionLibrary
{
    GENERATED_BODY()
public:
    // ---------------- UMG widget trees ----------------
    /** Add a widget of WidgetClass named NewName under ParentName (a panel) at Index (-1 = end). Empty ParentName + no root -> becomes root. Returns the widget or null. */
    UFUNCTION(BlueprintCallable, Category = "NeelamTools|Widgets")
    static UWidget* AddWidget(UWidgetBlueprint* WidgetBlueprint, FName ParentName, TSubclassOf<UWidget> WidgetClass, FName NewName, int32 Index = -1, bool bIsVariable = true);
    /** Remove a widget (and its children) from the tree. */
    UFUNCTION(BlueprintCallable, Category = "NeelamTools|Widgets")
    static bool RemoveWidget(UWidgetBlueprint* WidgetBlueprint, FName WidgetName);
    /** Move a widget under another panel. */
    UFUNCTION(BlueprintCallable, Category = "NeelamTools|Widgets")
    static bool MoveWidget(UWidgetBlueprint* WidgetBlueprint, FName WidgetName, FName NewParentName, int32 Index = -1);
    /** JSON list of the widget tree: name, class, parent, index, visibility, is_variable. */
    UFUNCTION(BlueprintCallable, Category = "NeelamTools|Widgets")
    static FString DescribeWidgetTree(UWidgetBlueprint* WidgetBlueprint);
    /** Deep-copy widget SourceName (with all children, styles and slot settings) from SourceBlueprint into TargetBlueprint under
        TargetParent at Index. New names = old names + Suffix (made unique). Returns the new root widget. */
    UFUNCTION(BlueprintCallable, Category = "NeelamTools|Widgets")
    static UWidget* CloneWidget(UWidgetBlueprint* SourceBlueprint, FName SourceName, UWidgetBlueprint* TargetBlueprint, FName TargetParent, int32 Index, const FString& Suffix);
    /** Change the parent class of a Blueprint (e.g. a widget blueprint to a C++ UUserWidget subclass). */
    UFUNCTION(BlueprintCallable, Category = "NeelamTools|Widgets")
    static bool ReparentBlueprint(UBlueprint* Blueprint, UClass* NewParent);

    // ---------------- Blueprint graphs ----------------
    /** Names of all graphs (event graph, functions, macros). */
    UFUNCTION(BlueprintCallable, Category = "NeelamTools|Graphs")
    static TArray<FString> ListGraphs(UBlueprint* Blueprint);
    /** JSON: every node (name, guid, class, title, pos) with pins (name, dir, type, default, links -> node.pin). */
    UFUNCTION(BlueprintCallable, Category = "NeelamTools|Graphs")
    static FString DescribeGraph(UBlueprint* Blueprint, FName GraphName);
    /** T3D copy-text of the whole graph (or only NodeNames if given) - exactly what Ctrl+C in the graph editor produces. */
    UFUNCTION(BlueprintCallable, Category = "NeelamTools|Graphs")
    static FString ExportGraphText(UBlueprint* Blueprint, FName GraphName, const TArray<FString>& NodeNames);
    /** Paste T3D node text into a graph (like Ctrl+V), offset by Offset. Returns the new node names. */
    UFUNCTION(BlueprintCallable, Category = "NeelamTools|Graphs")
    static TArray<FString> ImportGraphText(UBlueprint* Blueprint, FName GraphName, const FString& Text, FVector2D Offset);
    /** Connect NodeA.PinA -> NodeB.PinB (schema-validated). Node = name or guid. */
    UFUNCTION(BlueprintCallable, Category = "NeelamTools|Graphs")
    static FString ConnectPins(UBlueprint* Blueprint, FName GraphName, const FString& NodeA, FName PinA, const FString& NodeB, FName PinB);
    /** Break links of NodeA.PinA (all links, or only to NodeB.PinB if given). */
    UFUNCTION(BlueprintCallable, Category = "NeelamTools|Graphs")
    static bool BreakPinLinks(UBlueprint* Blueprint, FName GraphName, const FString& Node, FName Pin, const FString& OtherNode, FName OtherPin);
    /** Set a pin's default value (as the details panel would). */
    UFUNCTION(BlueprintCallable, Category = "NeelamTools|Graphs")
    static bool SetPinDefault(UBlueprint* Blueprint, FName GraphName, const FString& Node, FName Pin, const FString& Value);
    /** Delete a node. */
    UFUNCTION(BlueprintCallable, Category = "NeelamTools|Graphs")
    static bool DeleteNode(UBlueprint* Blueprint, FName GraphName, const FString& Node);
    /** Add a member variable. Category: bool,byte,int,int64,real,string,text,name,object,class,struct,softobject. SubType = object/struct/class path for those. */
    UFUNCTION(BlueprintCallable, Category = "NeelamTools|Graphs")
    static bool AddMemberVariable(UBlueprint* Blueprint, FName VarName, const FString& Category, const FString& SubTypePath, bool bArray = false, bool bInstanceEditable = true);
    /** Add an OnClicked-style bound event node for a widget variable's delegate (e.g. Button 'Btn_Plan', delegate 'OnClicked'). Returns node name. */
    UFUNCTION(BlueprintCallable, Category = "NeelamTools|Graphs")
    static FString AddWidgetBoundEvent(UWidgetBlueprint* WidgetBlueprint, FName WidgetVariable, FName DelegateName, FVector2D Position);
    /** Compile and return the compiler log (errors/warnings) as text; "OK" if clean. */
    UFUNCTION(BlueprintCallable, Category = "NeelamTools|Graphs")
    static FString CompileAndReport(UBlueprint* Blueprint);

    // ---------------- fonts ----------------
    /** Set the default typeface entries of a composite UFont (runtime cache): Names[i] -> Faces[i]. */
    UFUNCTION(BlueprintCallable, Category = "NeelamTools|Fonts")
    static bool SetFontTypefaces(class UFont* Font, const TArray<FName>& Names, const TArray<class UFontFace*>& Faces);

    // ---------------- previews ----------------
    /** Render a live widget (e.g. the PIE MasterMenu) off-screen to a PNG with alpha. Returns "OK <path>" or an error. */
    UFUNCTION(BlueprintCallable, Category = "NeelamTools|Preview")
    static FString RenderWidgetToPng(UWidget* Widget, int32 Width, int32 Height, const FString& FilePath);

    /** Read a (float) render target on the game thread and write its R channel as raw little-endian float32:
     *  header int32 width, int32 height, then width*height floats (row-major, top row first). Returns "" or an error. */
    UFUNCTION(BlueprintCallable, Category = "Neelam|Render")
    static FString ExportRenderTargetRawR(UTextureRenderTarget2D* RenderTarget, const FString& FilePath);

    /** Create a widget of Class in the editor (or PIE if running) world, render it to PNG, destroy it. */
    UFUNCTION(BlueprintCallable, Category = "NeelamTools|Preview")
    static FString RenderWidgetClassToPng(TSubclassOf<UUserWidget> WidgetClass, int32 Width, int32 Height, const FString& FilePath);

    // ---------------- PIE input / inspection ----------------
    /** Real Slate mouse click in the PIE game viewport at normalized coords (0..1). Button: Left/Right. */
    UFUNCTION(BlueprintCallable, Category = "NeelamTools|PIE")
    static FString ClickGameViewport(float X01, float Y01, FName Button = "Left", bool bDoubleClick = false);
    /** Move the cursor (hover) in the PIE viewport. */
    UFUNCTION(BlueprintCallable, Category = "NeelamTools|PIE")
    static FString HoverGameViewport(float X01, float Y01);
    /** Widget path (top-most first) under a normalized PIE viewport point - who would receive a click there. */
    UFUNCTION(BlueprintCallable, Category = "NeelamTools|PIE")
    static FString HitTestGameViewport(float X01, float Y01);
    /** On-screen rect of a (runtime) widget, normalized to the PIE viewport: {"x","y","w","h","visible"}. */
    UFUNCTION(BlueprintCallable, Category = "NeelamTools|PIE")
    static FString GetWidgetViewportRect(UWidget* Widget);
};
