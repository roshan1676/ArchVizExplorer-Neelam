#include "NeelamToolsLibrary.h"
#include "WidgetBlueprint.h"
#include "Blueprint/WidgetTree.h"
#include "Components/PanelWidget.h"
#include "Components/Widget.h"
#include "Kismet2/BlueprintEditorUtils.h"
#include "Kismet2/KismetEditorUtilities.h"
#include "Kismet2/CompilerResultsLog.h"
#include "EdGraphUtilities.h"
#include "EdGraph/EdGraph.h"
#include "EdGraph/EdGraphNode.h"
#include "EdGraph/EdGraphPin.h"
#include "EdGraphSchema_K2.h"
#include "K2Node_ComponentBoundEvent.h"
#include "Framework/Application/SlateApplication.h"
#include "Widgets/SViewport.h"
#include "Widgets/SWindow.h"
#include "Engine/GameViewportClient.h"
#include "Editor.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonWriter.h"
#include "Serialization/JsonSerializer.h"
#include "ScopedTransaction.h"
#include "Engine/World.h"
#include "Slate/WidgetRenderer.h"
#include "Engine/TextureRenderTarget2D.h"
#include "ImageUtils.h"
#include "Misc/FileHelper.h"
#include "RenderingThread.h"
#include "TextureResource.h"
#include "Blueprint/UserWidget.h"
#include "Engine/Font.h"
#include "Engine/FontFace.h"

// ---------------------------------------------------------------- helpers
static FString ToJson(const TSharedRef<FJsonObject>& O)
{
    FString S; TSharedRef<TJsonWriter<>> W = TJsonWriterFactory<>::Create(&S); FJsonSerializer::Serialize(O, W); return S;
}
static FString ToJsonArr(const TArray<TSharedPtr<FJsonValue>>& A)
{
    FString S; TSharedRef<TJsonWriter<>> W = TJsonWriterFactory<>::Create(&S); FJsonSerializer::Serialize(A, W); return S;
}
static UEdGraph* FindGraph(UBlueprint* BP, FName Name)
{
    if (!BP) return nullptr;
    TArray<UEdGraph*> Graphs; BP->GetAllGraphs(Graphs);
    for (UEdGraph* G : Graphs) if (G && G->GetFName() == Name) return G;
    return nullptr;
}
static UEdGraphNode* FindNode(UEdGraph* G, const FString& Id)
{
    if (!G) return nullptr;
    for (UEdGraphNode* N : G->Nodes)
        if (N && (N->GetName() == Id || N->NodeGuid.ToString() == Id || N->NodeGuid.ToString(EGuidFormats::DigitsWithHyphens) == Id)) return N;
    return nullptr;
}
static void Modified(UBlueprint* BP) { FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(BP); }

// ---------------------------------------------------------------- widgets
UWidget* UNeelamToolsLibrary::AddWidget(UWidgetBlueprint* WBP, FName ParentName, TSubclassOf<UWidget> WidgetClass, FName NewName, int32 Index, bool bIsVariable)
{
    if (!WBP || !WBP->WidgetTree || !*WidgetClass) return nullptr;
    const FScopedTransaction T(NSLOCTEXT("NeelamTools", "AddWidget", "Add Widget"));
    WBP->Modify(); WBP->WidgetTree->Modify();
    if (WBP->WidgetTree->FindWidget(NewName)) return nullptr;             // name must be unique
    UWidget* W = WBP->WidgetTree->ConstructWidget<UWidget>(*WidgetClass, NewName);
    if (!W) return nullptr;
    W->bIsVariable = bIsVariable;
    if (ParentName.IsNone())
    {
        if (WBP->WidgetTree->RootWidget) return nullptr;
        WBP->WidgetTree->RootWidget = W;
    }
    else
    {
        UPanelWidget* P = Cast<UPanelWidget>(WBP->WidgetTree->FindWidget(ParentName));
        if (!P) return nullptr;
        P->Modify();
        if (Index < 0 || Index >= P->GetChildrenCount()) P->AddChild(W); else P->InsertChildAt(Index, W);
    }
    Modified(WBP);
    return W;
}

bool UNeelamToolsLibrary::RemoveWidget(UWidgetBlueprint* WBP, FName WidgetName)
{
    if (!WBP || !WBP->WidgetTree) return false;
    UWidget* W = WBP->WidgetTree->FindWidget(WidgetName);
    if (!W) return false;
    const FScopedTransaction T(NSLOCTEXT("NeelamTools", "RemoveWidget", "Remove Widget"));
    WBP->Modify(); WBP->WidgetTree->Modify();
    TArray<UWidget*> Children; UWidgetTree::GetChildWidgets(W, Children);
    bool bOk = WBP->WidgetTree->RemoveWidget(W);
    if (bOk)
    {
        Modified(WBP);
    }
    return bOk;
}

bool UNeelamToolsLibrary::MoveWidget(UWidgetBlueprint* WBP, FName WidgetName, FName NewParentName, int32 Index)
{
    if (!WBP || !WBP->WidgetTree) return false;
    UWidget* W = WBP->WidgetTree->FindWidget(WidgetName);
    UPanelWidget* P = Cast<UPanelWidget>(WBP->WidgetTree->FindWidget(NewParentName));
    if (!W || !P) return false;
    const FScopedTransaction T(NSLOCTEXT("NeelamTools", "MoveWidget", "Move Widget"));
    WBP->Modify(); P->Modify();
    if (UPanelWidget* Old = W->GetParent()) { Old->Modify(); Old->RemoveChild(W); }
    if (Index < 0 || Index >= P->GetChildrenCount()) P->AddChild(W); else P->InsertChildAt(Index, W);
    Modified(WBP);
    return true;
}

FString UNeelamToolsLibrary::DescribeWidgetTree(UWidgetBlueprint* WBP)
{
    TArray<TSharedPtr<FJsonValue>> Arr;
    if (!WBP || !WBP->WidgetTree) return TEXT("[]");
    WBP->WidgetTree->ForEachWidget([&](UWidget* W)
    {
        TSharedRef<FJsonObject> O = MakeShared<FJsonObject>();
        O->SetStringField("name", W->GetName());
        O->SetStringField("class", W->GetClass()->GetName());
        UPanelWidget* P = W->GetParent();
        O->SetStringField("parent", P ? P->GetName() : TEXT(""));
        O->SetNumberField("index", P ? P->GetChildIndex(W) : -1);
        O->SetStringField("visibility", StaticEnum<ESlateVisibility>()->GetNameStringByValue((int64)W->GetVisibility()));
        O->SetBoolField("is_variable", W->bIsVariable);
        O->SetStringField("slot", W->Slot ? W->Slot->GetClass()->GetName() : TEXT(""));
        Arr.Add(MakeShared<FJsonValueObject>(O));
    });
    return ToJsonArr(Arr);
}


// ---------------------------------------------------------------- clone
static void CopyEditableProps(UObject* Dst, const UObject* Src, const TSet<FName>& Skip)
{
    for (TFieldIterator<FProperty> It(Src->GetClass()); It; ++It)
    {
        FProperty* P = *It;
        if (Skip.Contains(P->GetFName())) continue;
        if (P->HasAnyPropertyFlags(CPF_Transient | CPF_DuplicateTransient | CPF_Deprecated)) continue;
        if (!Dst->GetClass()->IsChildOf(P->GetOwnerClass())) continue;
        if (CastField<FObjectPropertyBase>(P) && P->HasAnyPropertyFlags(CPF_InstancedReference)) continue;
        P->CopyCompleteValue_InContainer(Dst, Src);
    }
}
static UWidget* CloneRec(UWidgetTree* Tree, UWidget* Src, const FString& Suffix)
{
    static const TSet<FName> SkipW = { "Slot", "Slots", "WidgetGeneratedBy", "WidgetGeneratedByClass", "DisplayLabel" };
    static const TSet<FName> SkipS = { "Parent", "Content" };
    const FName NewName = MakeUniqueObjectName(Tree, Src->GetClass(), FName(*(Src->GetName() + Suffix)));
    UWidget* N = Tree->ConstructWidget<UWidget>(Src->GetClass(), NewName);
    CopyEditableProps(N, Src, SkipW);
    if (UPanelWidget* SP = Cast<UPanelWidget>(Src))
    {
        UPanelWidget* NP = CastChecked<UPanelWidget>(N);
        for (int32 i = 0; i < SP->GetChildrenCount(); ++i)
        {
            UWidget* SC = SP->GetChildAt(i); if (!SC) continue;
            UWidget* NC = CloneRec(Tree, SC, Suffix);
            UPanelSlot* NS = NP->AddChild(NC);
            if (NS && SC->Slot && NS->GetClass() == SC->Slot->GetClass()) { CopyEditableProps(NS, SC->Slot, SkipS); NS->SynchronizeProperties(); }
        }
    }
    return N;
}

UWidget* UNeelamToolsLibrary::CloneWidget(UWidgetBlueprint* SrcBP, FName SourceName, UWidgetBlueprint* DstBP, FName TargetParent, int32 Index, const FString& Suffix)
{
    if (!SrcBP || !DstBP || !SrcBP->WidgetTree || !DstBP->WidgetTree) return nullptr;
    UWidget* Src = SrcBP->WidgetTree->FindWidget(SourceName); if (!Src) return nullptr;
    const FScopedTransaction T(NSLOCTEXT("NeelamTools", "CloneWidget", "Clone Widget"));
    DstBP->Modify(); DstBP->WidgetTree->Modify();
    UWidget* N = CloneRec(DstBP->WidgetTree, Src, Suffix);
    if (TargetParent.IsNone())
    {
        if (DstBP->WidgetTree->RootWidget) return nullptr;
        DstBP->WidgetTree->RootWidget = N;
    }
    else
    {
        UPanelWidget* P = Cast<UPanelWidget>(DstBP->WidgetTree->FindWidget(TargetParent)); if (!P) return nullptr;
        P->Modify();
        UPanelSlot* S = (Index < 0 || Index >= P->GetChildrenCount()) ? P->AddChild(N) : P->InsertChildAt(Index, N);
        if (S && Src->Slot && S->GetClass() == Src->Slot->GetClass())
        { static const TSet<FName> SkipS = { "Parent", "Content" }; CopyEditableProps(S, Src->Slot, SkipS); S->SynchronizeProperties(); }
    }
    Modified(DstBP);
    return N;
}

bool UNeelamToolsLibrary::ReparentBlueprint(UBlueprint* BP, UClass* NewParent)
{
    if (!BP || !NewParent) return false;
    BP->Modify();
    BP->ParentClass = NewParent;
    FBlueprintEditorUtils::RefreshAllNodes(BP);
    FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(BP);
    FKismetEditorUtilities::CompileBlueprint(BP);
    return BP->ParentClass == NewParent;
}

// ---------------------------------------------------------------- graphs
TArray<FString> UNeelamToolsLibrary::ListGraphs(UBlueprint* BP)
{
    TArray<FString> Out; if (!BP) return Out;
    TArray<UEdGraph*> Graphs; BP->GetAllGraphs(Graphs);
    for (UEdGraph* G : Graphs) if (G) Out.Add(G->GetName());
    return Out;
}

FString UNeelamToolsLibrary::DescribeGraph(UBlueprint* BP, FName GraphName)
{
    UEdGraph* G = FindGraph(BP, GraphName);
    if (!G) return TEXT("{\"error\":\"graph not found\"}");
    TArray<TSharedPtr<FJsonValue>> Nodes;
    for (UEdGraphNode* N : G->Nodes)
    {
        if (!N) continue;
        TSharedRef<FJsonObject> O = MakeShared<FJsonObject>();
        O->SetStringField("name", N->GetName());
        O->SetStringField("guid", N->NodeGuid.ToString());
        O->SetStringField("class", N->GetClass()->GetName());
        O->SetStringField("title", N->GetNodeTitle(ENodeTitleType::ListView).ToString());
        O->SetStringField("comment", N->NodeComment);
        O->SetNumberField("x", N->NodePosX); O->SetNumberField("y", N->NodePosY);
        TArray<TSharedPtr<FJsonValue>> Pins;
        for (UEdGraphPin* Pin : N->Pins)
        {
            if (!Pin || Pin->bHidden) continue;
            TSharedRef<FJsonObject> PO = MakeShared<FJsonObject>();
            PO->SetStringField("name", Pin->PinName.ToString());
            PO->SetStringField("dir", Pin->Direction == EGPD_Input ? TEXT("in") : TEXT("out"));
            FString Type = Pin->PinType.PinCategory.ToString();
            if (Pin->PinType.PinSubCategoryObject.IsValid()) Type += TEXT(":") + Pin->PinType.PinSubCategoryObject->GetName();
            if (Pin->PinType.IsArray()) Type += TEXT("[]");
            PO->SetStringField("type", Type);
            if (!Pin->DefaultValue.IsEmpty()) PO->SetStringField("default", Pin->DefaultValue);
            if (Pin->DefaultObject) PO->SetStringField("default_object", Pin->DefaultObject->GetPathName());
            TArray<TSharedPtr<FJsonValue>> Links;
            for (UEdGraphPin* L : Pin->LinkedTo)
                if (L && L->GetOwningNode()) Links.Add(MakeShared<FJsonValueString>(L->GetOwningNode()->GetName() + TEXT(".") + L->PinName.ToString()));
            if (Links.Num()) PO->SetArrayField("links", Links);
            Pins.Add(MakeShared<FJsonValueObject>(PO));
        }
        O->SetArrayField("pins", Pins);
        Nodes.Add(MakeShared<FJsonValueObject>(O));
    }
    return ToJsonArr(Nodes);
}

FString UNeelamToolsLibrary::ExportGraphText(UBlueprint* BP, FName GraphName, const TArray<FString>& NodeNames)
{
    UEdGraph* G = FindGraph(BP, GraphName);
    if (!G) return FString();
    TSet<UObject*> Sel;
    for (UEdGraphNode* N : G->Nodes)
        if (N && (NodeNames.Num() == 0 || NodeNames.Contains(N->GetName()) || NodeNames.Contains(N->NodeGuid.ToString())))
        { N->PrepareForCopying(); Sel.Add(N); }
    FString Text; FEdGraphUtilities::ExportNodesToText(Sel, Text);
    return Text;
}

TArray<FString> UNeelamToolsLibrary::ImportGraphText(UBlueprint* BP, FName GraphName, const FString& Text, FVector2D Offset)
{
    TArray<FString> Out;
    UEdGraph* G = FindGraph(BP, GraphName);
    if (!G || !FEdGraphUtilities::CanImportNodesFromText(G, Text)) return Out;
    const FScopedTransaction T(NSLOCTEXT("NeelamTools", "Paste", "Paste Nodes"));
    G->Modify();
    TSet<UEdGraphNode*> Nodes; FEdGraphUtilities::ImportNodesFromText(G, Text, Nodes);
    for (UEdGraphNode* N : Nodes)
    {
        if (!N) continue;
        N->CreateNewGuid(); N->PostPasteNode();
        N->NodePosX += (int32)Offset.X; N->NodePosY += (int32)Offset.Y;
        N->SnapToGrid(16);
        Out.Add(N->GetName());
    }
    Modified(BP);
    return Out;
}

FString UNeelamToolsLibrary::ConnectPins(UBlueprint* BP, FName GraphName, const FString& NodeA, FName PinA, const FString& NodeB, FName PinB)
{
    UEdGraph* G = FindGraph(BP, GraphName);
    UEdGraphNode* A = FindNode(G, NodeA); UEdGraphNode* B = FindNode(G, NodeB);
    if (!A || !B) return TEXT("node not found");
    UEdGraphPin* PA = A->FindPin(PinA); UEdGraphPin* PB = B->FindPin(PinB);
    if (!PA || !PB) return TEXT("pin not found");
    const FScopedTransaction T(NSLOCTEXT("NeelamTools", "Connect", "Connect Pins"));
    G->Modify(); A->Modify(); B->Modify();
    const UEdGraphSchema* S = G->GetSchema();
    const FPinConnectionResponse R = S->CanCreateConnection(PA, PB);
    bool bOk = S->TryCreateConnection(PA, PB);
    if (bOk) Modified(BP);
    return bOk ? TEXT("OK") : (TEXT("refused: ") + R.Message.ToString());
}

bool UNeelamToolsLibrary::BreakPinLinks(UBlueprint* BP, FName GraphName, const FString& Node, FName Pin, const FString& OtherNode, FName OtherPin)
{
    UEdGraph* G = FindGraph(BP, GraphName);
    UEdGraphNode* N = FindNode(G, Node); if (!N) return false;
    UEdGraphPin* P = N->FindPin(Pin); if (!P) return false;
    const FScopedTransaction T(NSLOCTEXT("NeelamTools", "Break", "Break Pin Links"));
    N->Modify();
    if (OtherNode.IsEmpty()) { G->GetSchema()->BreakPinLinks(*P, true); }
    else
    {
        UEdGraphNode* O = FindNode(G, OtherNode); UEdGraphPin* OP = O ? O->FindPin(OtherPin) : nullptr;
        if (!OP) return false;
        G->GetSchema()->BreakSinglePinLink(P, OP);
    }
    Modified(BP);
    return true;
}

bool UNeelamToolsLibrary::SetPinDefault(UBlueprint* BP, FName GraphName, const FString& Node, FName Pin, const FString& Value)
{
    UEdGraph* G = FindGraph(BP, GraphName);
    UEdGraphNode* N = FindNode(G, Node); if (!N) return false;
    UEdGraphPin* P = N->FindPin(Pin); if (!P) return false;
    N->Modify();
    if (P->PinType.PinCategory == UEdGraphSchema_K2::PC_Object || P->PinType.PinCategory == UEdGraphSchema_K2::PC_Class ||
        P->PinType.PinCategory == UEdGraphSchema_K2::PC_SoftObject)
    {
        UObject* Obj = StaticLoadObject(UObject::StaticClass(), nullptr, *Value);
        G->GetSchema()->TrySetDefaultObject(*P, Obj);
    }
    else G->GetSchema()->TrySetDefaultValue(*P, Value);
    Modified(BP);
    return true;
}

bool UNeelamToolsLibrary::DeleteNode(UBlueprint* BP, FName GraphName, const FString& Node)
{
    UEdGraph* G = FindGraph(BP, GraphName);
    UEdGraphNode* N = FindNode(G, Node); if (!N) return false;
    const FScopedTransaction T(NSLOCTEXT("NeelamTools", "Delete", "Delete Node"));
    FBlueprintEditorUtils::RemoveNode(BP, N, true);
    Modified(BP);
    return true;
}

bool UNeelamToolsLibrary::AddMemberVariable(UBlueprint* BP, FName VarName, const FString& Category, const FString& SubTypePath, bool bArray, bool bInstanceEditable)
{
    if (!BP) return false;
    FEdGraphPinType T;
    const FString C = Category.ToLower();
    if (C == "bool") T.PinCategory = UEdGraphSchema_K2::PC_Boolean;
    else if (C == "byte") T.PinCategory = UEdGraphSchema_K2::PC_Byte;
    else if (C == "int") T.PinCategory = UEdGraphSchema_K2::PC_Int;
    else if (C == "int64") T.PinCategory = UEdGraphSchema_K2::PC_Int64;
    else if (C == "real" || C == "float" || C == "double") { T.PinCategory = UEdGraphSchema_K2::PC_Real; T.PinSubCategory = UEdGraphSchema_K2::PC_Double; }
    else if (C == "string") T.PinCategory = UEdGraphSchema_K2::PC_String;
    else if (C == "text") T.PinCategory = UEdGraphSchema_K2::PC_Text;
    else if (C == "name") T.PinCategory = UEdGraphSchema_K2::PC_Name;
    else if (C == "object" || C == "class" || C == "softobject" || C == "struct")
    {
        T.PinCategory = C == "object" ? UEdGraphSchema_K2::PC_Object : C == "class" ? UEdGraphSchema_K2::PC_Class :
                        C == "softobject" ? UEdGraphSchema_K2::PC_SoftObject : UEdGraphSchema_K2::PC_Struct;
        UObject* Sub = StaticLoadObject(UObject::StaticClass(), nullptr, *SubTypePath);
        if (!Sub) return false;
        T.PinSubCategoryObject = Sub;
    }
    else return false;
    if (bArray) T.ContainerType = EPinContainerType::Array;
    const bool bOk = FBlueprintEditorUtils::AddMemberVariable(BP, VarName, T);
    if (bOk && bInstanceEditable) FBlueprintEditorUtils::SetBlueprintOnlyEditableFlag(BP, VarName, false);
    if (bOk) Modified(BP);
    return bOk;
}

FString UNeelamToolsLibrary::AddWidgetBoundEvent(UWidgetBlueprint* WBP, FName WidgetVariable, FName DelegateName, FVector2D Position)
{
    if (!WBP) return TEXT("no blueprint");
    UEdGraph* G = FBlueprintEditorUtils::FindEventGraph(WBP);
    if (!G) return TEXT("no event graph");
    // make sure the generated class has the widget property
    FKismetEditorUtilities::CompileBlueprint(WBP, EBlueprintCompileOptions::SkipGarbageCollection);
    UClass* Cls = WBP->SkeletonGeneratedClass ? WBP->SkeletonGeneratedClass : WBP->GeneratedClass;
    FObjectProperty* Prop = Cls ? FindFProperty<FObjectProperty>(Cls, WidgetVariable) : nullptr;
    if (!Prop) return TEXT("widget variable not found (is it marked Is Variable?)");
    UClass* WidgetCls = Prop->PropertyClass;
    FMulticastDelegateProperty* Del = WidgetCls ? FindFProperty<FMulticastDelegateProperty>(WidgetCls, DelegateName) : nullptr;
    if (!Del) return TEXT("delegate not found on widget class");
    if (const UK2Node_ComponentBoundEvent* Existing = FKismetEditorUtilities::FindBoundEventForComponent(WBP, DelegateName, WidgetVariable))
        return Existing->GetName();
    const FScopedTransaction T(NSLOCTEXT("NeelamTools", "BoundEvent", "Add Bound Event"));
    G->Modify();
    UK2Node_ComponentBoundEvent* N = NewObject<UK2Node_ComponentBoundEvent>(G);
    N->InitializeComponentBoundEventParams(Prop, Del);
    N->CreateNewGuid(); N->PostPlacedNewNode(); N->AllocateDefaultPins();
    N->NodePosX = (int32)Position.X; N->NodePosY = (int32)Position.Y;
    G->AddNode(N, true, false);
    Modified(WBP);
    return N->GetName();
}

FString UNeelamToolsLibrary::CompileAndReport(UBlueprint* BP)
{
    if (!BP) return TEXT("no blueprint");
    FCompilerResultsLog Log; Log.SetSourcePath(BP->GetPathName()); Log.bSilentMode = true;
    FKismetEditorUtilities::CompileBlueprint(BP, EBlueprintCompileOptions::None, &Log);
    FString Out;
    for (const TSharedRef<FTokenizedMessage>& M : Log.Messages)
        if (M->GetSeverity() <= EMessageSeverity::Warning) Out += M->ToText().ToString() + TEXT("\n");
    return Out.IsEmpty() ? (BP->Status == BS_Error ? TEXT("ERROR (no message)") : TEXT("OK")) : Out;
}

// ---------------------------------------------------------------- PIE input
static UGameViewportClient* PieViewport()
{
    if (!GEditor || !GEditor->PlayWorld) return nullptr;
    return GEditor->PlayWorld->GetGameViewport();
}
static bool PieGeometry(FGeometry& OutGeo, TSharedPtr<SWindow>& OutWin)
{
    UGameViewportClient* V = PieViewport(); if (!V) return false;
    TSharedPtr<SViewport> VW = V->GetGameViewportWidget(); if (!VW.IsValid()) return false;
    OutGeo = VW->GetTickSpaceGeometry();
    OutWin = FSlateApplication::Get().FindWidgetWindow(VW.ToSharedRef());
    return OutWin.IsValid();
}
static FVector2D ToAbs(const FGeometry& G, float X01, float Y01)
{
    return G.LocalToAbsolute(FVector2D(X01 * G.GetLocalSize().X, Y01 * G.GetLocalSize().Y));
}

FString UNeelamToolsLibrary::HoverGameViewport(float X01, float Y01)
{
    FGeometry G; TSharedPtr<SWindow> Win; if (!PieGeometry(G, Win)) return TEXT("no PIE viewport");
    FSlateApplication& App = FSlateApplication::Get();
    const FVector2D P = ToAbs(G, X01, Y01);
    FPointerEvent Move(App.GetUserIndexForMouse(), FSlateApplication::CursorPointerIndex, P, App.GetCursorPos(), TSet<FKey>(), EKeys::Invalid, 0, App.GetModifierKeys());
    App.SetCursorPos(P);
    App.ProcessMouseMoveEvent(Move);
    return FString::Printf(TEXT("hover %.0f,%.0f"), P.X, P.Y);
}

FString UNeelamToolsLibrary::ClickGameViewport(float X01, float Y01, FName Button, bool bDoubleClick)
{
    FGeometry G; TSharedPtr<SWindow> Win; if (!PieGeometry(G, Win)) return TEXT("no PIE viewport");
    FSlateApplication& App = FSlateApplication::Get();
    const FVector2D P = ToAbs(G, X01, Y01);
    const FKey Key = Button == "Right" ? EKeys::RightMouseButton : EKeys::LeftMouseButton;
    HoverGameViewport(X01, Y01);
    TSharedPtr<FGenericWindow> Native = Win->GetNativeWindow();
    TSet<FKey> Pressed; Pressed.Add(Key);
    FPointerEvent Down(App.GetUserIndexForMouse(), FSlateApplication::CursorPointerIndex, P, P, Pressed, Key, 0, App.GetModifierKeys());
    const bool bD = bDoubleClick ? App.ProcessMouseButtonDoubleClickEvent(Native, Down) : App.ProcessMouseButtonDownEvent(Native, Down);
    FPointerEvent Up(App.GetUserIndexForMouse(), FSlateApplication::CursorPointerIndex, P, P, TSet<FKey>(), Key, 0, App.GetModifierKeys());
    const bool bU = App.ProcessMouseButtonUpEvent(Up);
    return FString::Printf(TEXT("click %.0f,%.0f down=%d up=%d"), P.X, P.Y, bD ? 1 : 0, bU ? 1 : 0);
}

FString UNeelamToolsLibrary::HitTestGameViewport(float X01, float Y01)
{
    FGeometry G; TSharedPtr<SWindow> Win; if (!PieGeometry(G, Win)) return TEXT("[]");
    FSlateApplication& App = FSlateApplication::Get();
    const FVector2D P = ToAbs(G, X01, Y01);
    TArray<TSharedRef<SWindow>> Wins; Wins.Add(Win.ToSharedRef());
    FWidgetPath Path = App.LocateWindowUnderMouse(P, Wins, true);
    TArray<TSharedPtr<FJsonValue>> Arr;
    for (int32 i = Path.Widgets.Num() - 1; i >= 0; --i)
    {
        const TSharedRef<SWidget>& W = Path.Widgets[i].Widget;
        TSharedRef<FJsonObject> O = MakeShared<FJsonObject>();
        O->SetStringField("type", W->GetTypeAsString());
        O->SetStringField("tag", W->GetTag().ToString());
        O->SetStringField("readable", W->GetReadableLocation());
        Arr.Add(MakeShared<FJsonValueObject>(O));
        if (Arr.Num() >= 25) break;
    }
    return ToJsonArr(Arr);
}

FString UNeelamToolsLibrary::GetWidgetViewportRect(UWidget* Widget)
{
    TSharedRef<FJsonObject> O = MakeShared<FJsonObject>();
    FGeometry VG; TSharedPtr<SWindow> Win;
    if (!Widget || !PieGeometry(VG, Win)) { O->SetStringField("error", "no widget or PIE"); return ToJson(O); }
    const FGeometry& WG = Widget->GetCachedGeometry();
    const FVector2D A = WG.GetAbsolutePosition(), S = WG.GetAbsoluteSize();
    const FVector2D V = VG.GetAbsolutePosition(), VS = VG.GetAbsoluteSize();
    O->SetNumberField("x", VS.X > 0 ? (A.X - V.X) / VS.X : 0); O->SetNumberField("y", VS.Y > 0 ? (A.Y - V.Y) / VS.Y : 0);
    O->SetNumberField("w", VS.X > 0 ? S.X / VS.X : 0);           O->SetNumberField("h", VS.Y > 0 ? S.Y / VS.Y : 0);
    O->SetBoolField("visible", Widget->IsVisible());
    return ToJson(O);
}


// ---------------------------------------------------------------- previews
static FString RenderSlate(TSharedRef<SWidget> S, int32 W, int32 H, const FString& Path)
{
    W = FMath::Clamp(W, 16, 8192); H = FMath::Clamp(H, 16, 8192);
    FWidgetRenderer* R = new FWidgetRenderer(true, false);
    UTextureRenderTarget2D* RT = FWidgetRenderer::CreateTargetFor(FVector2D(W, H), TF_Bilinear, true);
    if (!RT) { delete R; return TEXT("no render target"); }
    RT->ClearColor = FLinearColor::Transparent;
    RT->UpdateResourceImmediate(true);
    for (int32 i = 0; i < 3; ++i) R->DrawWidget(RT, S, FVector2D(W, H), 0.016f);
    FlushRenderingCommands();
    TArray<FColor> Px;
    FTextureRenderTargetResource* Res = RT->GameThread_GetRenderTargetResource();
    FReadSurfaceDataFlags Flags(RCM_UNorm); Flags.SetLinearToGamma(false);
    if (!Res || !Res->ReadPixels(Px, Flags) || Px.Num() != W * H) { delete R; return TEXT("read pixels failed"); }
    TArray64<uint8> Png;
    FImageUtils::PNGCompressImageArray(W, H, TArrayView64<const FColor>(Px.GetData(), Px.Num()), Png);
    const bool bOk = FFileHelper::SaveArrayToFile(Png, *Path);
    delete R;
    RT->MarkAsGarbage();
    return bOk ? (TEXT("OK ") + Path) : TEXT("save failed");
}

FString UNeelamToolsLibrary::RenderWidgetToPng(UWidget* Widget, int32 Width, int32 Height, const FString& FilePath)
{
    if (!Widget) return TEXT("no widget");
    return RenderSlate(Widget->TakeWidget(), Width, Height, FilePath);
}

FString UNeelamToolsLibrary::RenderWidgetClassToPng(TSubclassOf<UUserWidget> WidgetClass, int32 Width, int32 Height, const FString& FilePath)
{
    if (!*WidgetClass || !GEditor) return TEXT("no class");
    UWorld* PW = GEditor->PlayWorld;
    UWorld* World = PW ? PW : GEditor->GetEditorWorldContext().World();
    if (!World) return TEXT("no world");
    UUserWidget* W = CreateWidget<UUserWidget>(World, WidgetClass);
    if (!W) return TEXT("create failed");
    const FString R = RenderSlate(W->TakeWidget(), Width, Height, FilePath);
    W->RemoveFromParent();
    return R;
}

bool UNeelamToolsLibrary::SetFontTypefaces(UFont* Font, const TArray<FName>& Names, const TArray<UFontFace*>& Faces)
{
    if (!Font || Names.Num() != Faces.Num()) return false;
    Font->Modify();
    Font->FontCacheType = EFontCacheType::Runtime;
    FTypeface& T = Font->CompositeFont.DefaultTypeface;
    T.Fonts.Reset();
    for (int32 i = 0; i < Names.Num(); ++i)
        if (Faces[i]) { FTypefaceEntry& E = T.Fonts.AddDefaulted_GetRef(); E.Name = Names[i]; E.Font = FFontData(Faces[i]); }
    Font->PostEditChange();
    Font->MarkPackageDirty();
    return T.Fonts.Num() == Names.Num();
}


FString UNeelamToolsLibrary::ExportRenderTargetRawR(UTextureRenderTarget2D* RenderTarget, const FString& FilePath)
{
    if (!RenderTarget) return TEXT("no render target");
    FTextureRenderTargetResource* Res = RenderTarget->GameThread_GetRenderTargetResource();
    if (!Res) return TEXT("no resource");
    TArray<FLinearColor> Px;
    FReadSurfaceDataFlags Flags(RCM_MinMax);
    Flags.SetLinearToGamma(false);
    if (!Res->ReadLinearColorPixels(Px, Flags)) return TEXT("read failed");
    const int32 W = RenderTarget->SizeX, H = RenderTarget->SizeY;
    if (Px.Num() != W * H) return FString::Printf(TEXT("size mismatch %d vs %d"), Px.Num(), W * H);
    TArray<uint8> Out; Out.SetNumUninitialized(8 + W * H * 4);
    FMemory::Memcpy(Out.GetData(), &W, 4); FMemory::Memcpy(Out.GetData() + 4, &H, 4);
    float* F = reinterpret_cast<float*>(Out.GetData() + 8);
    for (int32 i = 0; i < W * H; ++i) F[i] = Px[i].R;
    return FFileHelper::SaveArrayToFile(Out, *FilePath) ? FString() : TEXT("write failed");
}
