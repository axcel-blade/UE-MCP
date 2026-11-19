#include "Tools/BlueprintTools.h"
#include "Core/ToolRegistry.h"
#include "Core/ResultSerializer.h"
#include "Core/GameThreadDispatcher.h"
#include "Engine/Blueprint.h"
#include "Engine/BlueprintGeneratedClass.h"
#include "Factories/BlueprintFactory.h"
#include "Kismet2/KismetEditorUtilities.h"
#include "Kismet2/BlueprintEditorUtils.h"
#include "Kismet2/CompilerResultsLog.h"
#include "EdGraphSchema_K2.h"
#include "EdGraph/EdGraph.h"
#include "EdGraph/EdGraphNode.h"
#include "EdGraph/EdGraphPin.h"
#include "K2Node_Event.h"
#include "K2Node_CallFunction.h"
#include "K2Node_VariableGet.h"
#include "K2Node_VariableSet.h"
#include "Kismet/KismetSystemLibrary.h"
#include "AssetToolsModule.h"
#include "EditorAssetLibrary.h"
#include "Misc/PackageName.h"
#include "Engine/SimpleConstructionScript.h"
#include "Engine/SCS_Node.h"
#include "Components/SceneComponent.h"
#include "UObject/SavePackage.h"

namespace
{
	FUnrealEngineMCPResponse Ok(const FUnrealEngineMCPRequest& Req, TSharedPtr<FJsonObject> R) { return FUnrealEngineMCPResultSerializer::Ok(Req.Id, R); }
	FUnrealEngineMCPResponse Fail(const FUnrealEngineMCPRequest& Req, const FString& C, const FString& M) { return FUnrealEngineMCPResultSerializer::Fail(Req.Id, C, M); }

	UBlueprint* LoadBP(const FString& Path)
	{
		return LoadObject<UBlueprint>(nullptr, *Path);
	}
}

void FUnrealEngineMCPBlueprintTools::Register()
{
	auto& Reg = FUnrealEngineMCPToolRegistry::Get();

	Reg.Register(TEXT("unreal_create_blueprint"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		TSharedPtr<FJsonObject> Params = Req.Params;
		TSharedPtr<FJsonObject> Result = FUnrealEngineMCPGameThreadDispatcher::RunJson([Params]()
		{
			TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
			FString Path = Params->GetStringField(TEXT("path"));
			FString ParentName = Params->HasField(TEXT("parent_class")) ? Params->GetStringField(TEXT("parent_class")) : TEXT("Actor");
			UClass* Parent = AActor::StaticClass();
			if (!ParentName.Equals(TEXT("Actor"), ESearchCase::IgnoreCase))
			{
				UClass* Found = FindObject<UClass>(nullptr, *FString::Printf(TEXT("/Script/Engine.%s"), *ParentName));
				if (!Found) Found = LoadObject<UClass>(nullptr, *ParentName);
				if (Found) Parent = Found;
			}
			UBlueprintFactory* Factory = NewObject<UBlueprintFactory>();
			Factory->ParentClass = Parent;
			IAssetTools& AssetTools = FModuleManager::LoadModuleChecked<FAssetToolsModule>("AssetTools").Get();
			FString PackagePath = FPackageName::GetLongPackagePath(Path);
			FString AssetName = FPackageName::GetShortName(Path);
			UObject* Created = AssetTools.CreateAsset(AssetName, PackagePath, UBlueprint::StaticClass(), Factory);
			UBlueprint* BP = Cast<UBlueprint>(Created);
			if (!BP) { Obj->SetStringField(TEXT("error"), TEXT("Failed to create Blueprint")); return Obj; }
			Obj->SetStringField(TEXT("path"), BP->GetPathName());
			Obj->SetStringField(TEXT("name"), BP->GetName());
			Obj->SetStringField(TEXT("parent"), Parent->GetName());
			return Obj;
		});
		if (Result->HasField(TEXT("error"))) return Fail(Req, TEXT("engine_error"), Result->GetStringField(TEXT("error")));
		return Ok(Req, Result);
	}), TEXT("Create a Blueprint asset."));

	Reg.Register(TEXT("unreal_get_blueprint"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		TSharedPtr<FJsonObject> Params = Req.Params;
		TSharedPtr<FJsonObject> Result = FUnrealEngineMCPGameThreadDispatcher::RunJson([Params]()
		{
			TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
			UBlueprint* BP = LoadBP(Params->GetStringField(TEXT("path")));
			if (!BP) { Obj->SetStringField(TEXT("error"), TEXT("Blueprint not found")); return Obj; }
			Obj->SetStringField(TEXT("path"), BP->GetPathName());
			Obj->SetStringField(TEXT("name"), BP->GetName());
			Obj->SetStringField(TEXT("parent"), BP->ParentClass ? BP->ParentClass->GetName() : TEXT(""));
			Obj->SetNumberField(TEXT("variables"), BP->NewVariables.Num());
			Obj->SetNumberField(TEXT("graphs"), BP->FunctionGraphs.Num() + (BP->UbergraphPages.Num()));
			return Obj;
		});
		if (Result->HasField(TEXT("error"))) return Fail(Req, TEXT("engine_error"), Result->GetStringField(TEXT("error")));
		return Ok(Req, Result);
	}), TEXT("Get Blueprint asset details."));

	Reg.Register(TEXT("unreal_compile_blueprint"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		TSharedPtr<FJsonObject> Params = Req.Params;
		TSharedPtr<FJsonObject> Result = FUnrealEngineMCPGameThreadDispatcher::RunJson([Params]()
		{
			TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
			UBlueprint* BP = LoadBP(Params->GetStringField(TEXT("path")));
			if (!BP) { Obj->SetStringField(TEXT("error"), TEXT("Blueprint not found")); return Obj; }
			FCompilerResultsLog Log;
			Log.bLogDetailedResults = true;
			FKismetEditorUtilities::CompileBlueprint(BP, EBlueprintCompileOptions::None, &Log);
			Obj->SetBoolField(TEXT("compiled"), Log.NumErrors == 0);
			Obj->SetNumberField(TEXT("errors"), Log.NumErrors);
			Obj->SetNumberField(TEXT("warnings"), Log.NumWarnings);
			TArray<TSharedPtr<FJsonValue>> Messages;
			for (TSharedRef<FTokenizedMessage>& Msg : Log.Messages)
			{
				Messages.Add(MakeShared<FJsonValueString>(Msg->ToText().ToString()));
			}
			Obj->SetArrayField(TEXT("messages"), Messages);
			if (Log.NumErrors > 0) Obj->SetStringField(TEXT("error"), TEXT("Blueprint compilation reported errors"));
			return Obj;
		});
		if (Result->HasField(TEXT("error")) && Result->GetNumberField(TEXT("errors")) > 0)
		{
			return Fail(Req, TEXT("compile_error"), Result->GetStringField(TEXT("error")));
		}
		if (Result->HasField(TEXT("error")) && !Result->HasField(TEXT("compiled")))
		{
			return Fail(Req, TEXT("engine_error"), Result->GetStringField(TEXT("error")));
		}
		return Ok(Req, Result);
	}), TEXT("Compile a Blueprint and return diagnostics."));

	Reg.Register(TEXT("unreal_save_blueprint"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		TSharedPtr<FJsonObject> Params = Req.Params;
		TSharedPtr<FJsonObject> Result = FUnrealEngineMCPGameThreadDispatcher::RunJson([Params]()
		{
			TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
			FString Path = Params->GetStringField(TEXT("path"));
			const bool bOk = UEditorAssetLibrary::SaveAsset(Path);
			Obj->SetBoolField(TEXT("saved"), bOk);
			Obj->SetStringField(TEXT("path"), Path);
			if (!bOk) Obj->SetStringField(TEXT("error"), TEXT("Save failed"));
			return Obj;
		});
		if (Result->HasField(TEXT("error"))) return Fail(Req, TEXT("engine_error"), Result->GetStringField(TEXT("error")));
		return Ok(Req, Result);
	}), TEXT("Save a Blueprint asset."));

	Reg.Register(TEXT("unreal_delete_blueprint"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		TSharedPtr<FJsonObject> Params = Req.Params;
		TSharedPtr<FJsonObject> Result = FUnrealEngineMCPGameThreadDispatcher::RunJson([Params]()
		{
			TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
			FString Path = Params->GetStringField(TEXT("path"));
			const bool bOk = UEditorAssetLibrary::DeleteAsset(Path);
			Obj->SetBoolField(TEXT("deleted"), bOk);
			if (!bOk) Obj->SetStringField(TEXT("error"), TEXT("Delete failed"));
			return Obj;
		});
		if (Result->HasField(TEXT("error"))) return Fail(Req, TEXT("engine_error"), Result->GetStringField(TEXT("error")));
		return Ok(Req, Result);
	}), TEXT("Delete a Blueprint asset."));

	Reg.Register(TEXT("unreal_add_blueprint_variable"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		TSharedPtr<FJsonObject> Params = Req.Params;
		TSharedPtr<FJsonObject> Result = FUnrealEngineMCPGameThreadDispatcher::RunJson([Params]()
		{
			TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
			UBlueprint* BP = LoadBP(Params->GetStringField(TEXT("path")));
			if (!BP) { Obj->SetStringField(TEXT("error"), TEXT("Blueprint not found")); return Obj; }
			FString VarName = Params->GetStringField(TEXT("variable_name"));
			FString TypeName = Params->HasField(TEXT("type")) ? Params->GetStringField(TEXT("type")) : TEXT("bool");
			FEdGraphPinType PinType;
			PinType.PinCategory = UEdGraphSchema_K2::PC_Boolean;
			if (TypeName.Equals(TEXT("int"), ESearchCase::IgnoreCase) || TypeName.Equals(TEXT("int32"), ESearchCase::IgnoreCase))
				PinType.PinCategory = UEdGraphSchema_K2::PC_Int;
			else if (TypeName.Equals(TEXT("float"), ESearchCase::IgnoreCase) || TypeName.Equals(TEXT("double"), ESearchCase::IgnoreCase))
				PinType.PinCategory = UEdGraphSchema_K2::PC_Real;
			else if (TypeName.Equals(TEXT("string"), ESearchCase::IgnoreCase))
				PinType.PinCategory = UEdGraphSchema_K2::PC_String;
			else if (TypeName.Equals(TEXT("name"), ESearchCase::IgnoreCase))
				PinType.PinCategory = UEdGraphSchema_K2::PC_Name;
			else if (TypeName.Equals(TEXT("vector"), ESearchCase::IgnoreCase))
			{
				PinType.PinCategory = UEdGraphSchema_K2::PC_Struct;
				PinType.PinSubCategoryObject = TBaseStructure<FVector>::Get();
			}
			FBlueprintEditorUtils::AddMemberVariable(BP, FName(*VarName), PinType);
			FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(BP);
			Obj->SetStringField(TEXT("variable"), VarName);
			Obj->SetStringField(TEXT("type"), TypeName);
			return Obj;
		});
		if (Result->HasField(TEXT("error"))) return Fail(Req, TEXT("engine_error"), Result->GetStringField(TEXT("error")));
		return Ok(Req, Result);
	}), TEXT("Add a Blueprint variable."));

	Reg.Register(TEXT("unreal_remove_blueprint_variable"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		TSharedPtr<FJsonObject> Params = Req.Params;
		TSharedPtr<FJsonObject> Result = FUnrealEngineMCPGameThreadDispatcher::RunJson([Params]()
		{
			TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
			UBlueprint* BP = LoadBP(Params->GetStringField(TEXT("path")));
			if (!BP) { Obj->SetStringField(TEXT("error"), TEXT("Blueprint not found")); return Obj; }
			FString VarName = Params->GetStringField(TEXT("variable_name"));
			FBlueprintEditorUtils::RemoveMemberVariable(BP, FName(*VarName));
			FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(BP);
			Obj->SetStringField(TEXT("removed"), VarName);
			return Obj;
		});
		if (Result->HasField(TEXT("error"))) return Fail(Req, TEXT("engine_error"), Result->GetStringField(TEXT("error")));
		return Ok(Req, Result);
	}), TEXT("Remove a Blueprint variable."));

	Reg.Register(TEXT("unreal_get_blueprint_variables"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		TSharedPtr<FJsonObject> Params = Req.Params;
		TSharedPtr<FJsonObject> Result = FUnrealEngineMCPGameThreadDispatcher::RunJson([Params]()
		{
			TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
			UBlueprint* BP = LoadBP(Params->GetStringField(TEXT("path")));
			if (!BP) { Obj->SetStringField(TEXT("error"), TEXT("Blueprint not found")); return Obj; }
			TArray<TSharedPtr<FJsonValue>> Vars;
			for (const FBPVariableDescription& Var : BP->NewVariables)
			{
				TSharedPtr<FJsonObject> V = MakeShared<FJsonObject>();
				V->SetStringField(TEXT("name"), Var.VarName.ToString());
				V->SetStringField(TEXT("type"), Var.VarType.PinCategory.ToString());
				Vars.Add(MakeShared<FJsonValueObject>(V));
			}
			Obj->SetArrayField(TEXT("variables"), Vars);
			return Obj;
		});
		if (Result->HasField(TEXT("error"))) return Fail(Req, TEXT("engine_error"), Result->GetStringField(TEXT("error")));
		return Ok(Req, Result);
	}), TEXT("List Blueprint variables."));

	Reg.Register(TEXT("unreal_get_blueprint_graphs"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		TSharedPtr<FJsonObject> Params = Req.Params;
		TSharedPtr<FJsonObject> Result = FUnrealEngineMCPGameThreadDispatcher::RunJson([Params]()
		{
			TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
			UBlueprint* BP = LoadBP(Params->GetStringField(TEXT("path")));
			if (!BP) { Obj->SetStringField(TEXT("error"), TEXT("Blueprint not found")); return Obj; }
			TArray<TSharedPtr<FJsonValue>> Graphs;
			for (UEdGraph* Graph : BP->UbergraphPages)
			{
				if (!Graph) continue;
				TSharedPtr<FJsonObject> G = MakeShared<FJsonObject>();
				G->SetStringField(TEXT("name"), Graph->GetName());
				G->SetStringField(TEXT("kind"), TEXT("ubergraph"));
				G->SetNumberField(TEXT("nodes"), Graph->Nodes.Num());
				Graphs.Add(MakeShared<FJsonValueObject>(G));
			}
			for (UEdGraph* Graph : BP->FunctionGraphs)
			{
				if (!Graph) continue;
				TSharedPtr<FJsonObject> G = MakeShared<FJsonObject>();
				G->SetStringField(TEXT("name"), Graph->GetName());
				G->SetStringField(TEXT("kind"), TEXT("function"));
				G->SetNumberField(TEXT("nodes"), Graph->Nodes.Num());
				Graphs.Add(MakeShared<FJsonValueObject>(G));
			}
			Obj->SetArrayField(TEXT("graphs"), Graphs);
			return Obj;
		});
		if (Result->HasField(TEXT("error"))) return Fail(Req, TEXT("engine_error"), Result->GetStringField(TEXT("error")));
		return Ok(Req, Result);
	}), TEXT("List Blueprint graphs."));

	Reg.Register(TEXT("unreal_get_blueprint_nodes"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		TSharedPtr<FJsonObject> Params = Req.Params;
		TSharedPtr<FJsonObject> Result = FUnrealEngineMCPGameThreadDispatcher::RunJson([Params]()
		{
			TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
			UBlueprint* BP = LoadBP(Params->GetStringField(TEXT("path")));
			if (!BP) { Obj->SetStringField(TEXT("error"), TEXT("Blueprint not found")); return Obj; }
			FString GraphName = Params->HasField(TEXT("graph")) ? Params->GetStringField(TEXT("graph")) : TEXT("");
			UEdGraph* Target = nullptr;
			TArray<UEdGraph*> All; All.Append(BP->UbergraphPages); All.Append(BP->FunctionGraphs);
			for (UEdGraph* Graph : All)
			{
				if (!Graph) continue;
				if (GraphName.IsEmpty() || Graph->GetName().Equals(GraphName, ESearchCase::IgnoreCase))
				{
					Target = Graph; break;
				}
			}
			if (!Target) { Obj->SetStringField(TEXT("error"), TEXT("Graph not found")); return Obj; }
			TArray<TSharedPtr<FJsonValue>> Nodes;
			for (UEdGraphNode* Node : Target->Nodes)
			{
				if (!Node) continue;
				TSharedPtr<FJsonObject> N = MakeShared<FJsonObject>();
				N->SetStringField(TEXT("name"), Node->GetName());
				N->SetStringField(TEXT("title"), Node->GetNodeTitle(ENodeTitleType::ListView).ToString());
				N->SetStringField(TEXT("class"), Node->GetClass()->GetName());
				N->SetNumberField(TEXT("guid"), GetTypeHash(Node->NodeGuid));
				Nodes.Add(MakeShared<FJsonValueObject>(N));
			}
			Obj->SetStringField(TEXT("graph"), Target->GetName());
			Obj->SetArrayField(TEXT("nodes"), Nodes);
			return Obj;
		});
		if (Result->HasField(TEXT("error"))) return Fail(Req, TEXT("engine_error"), Result->GetStringField(TEXT("error")));
		return Ok(Req, Result);
	}), TEXT("List nodes in a Blueprint graph."));

	Reg.Register(TEXT("unreal_create_blueprint_node"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		TSharedPtr<FJsonObject> Params = Req.Params;
		TSharedPtr<FJsonObject> Result = FUnrealEngineMCPGameThreadDispatcher::RunJson([Params]()
		{
			TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
			UBlueprint* BP = LoadBP(Params->GetStringField(TEXT("path")));
			if (!BP) { Obj->SetStringField(TEXT("error"), TEXT("Blueprint not found")); return Obj; }
			UEdGraph* Graph = BP->UbergraphPages.Num() > 0 ? BP->UbergraphPages[0] : nullptr;
			if (!Graph) { Obj->SetStringField(TEXT("error"), TEXT("No ubergraph")); return Obj; }
			FString NodeType = Params->GetStringField(TEXT("node_type"));
			UEdGraphNode* NewNode = nullptr;
			if (NodeType.Equals(TEXT("EventBeginPlay"), ESearchCase::IgnoreCase) || NodeType.Equals(TEXT("BeginPlay"), ESearchCase::IgnoreCase))
			{
				UK2Node_Event* EventNode = NewObject<UK2Node_Event>(Graph);
				EventNode->EventReference.SetExternalMember(FName(TEXT("ReceiveBeginPlay")), AActor::StaticClass());
				EventNode->bOverrideFunction = true;
				Graph->AddNode(EventNode, false, false);
				EventNode->AllocateDefaultPins();
				NewNode = EventNode;
			}
			else if (NodeType.Equals(TEXT("PrintString"), ESearchCase::IgnoreCase))
			{
				UK2Node_CallFunction* Call = NewObject<UK2Node_CallFunction>(Graph);
				Call->SetFromFunction(UKismetSystemLibrary::StaticClass()->FindFunctionByName(GET_FUNCTION_NAME_CHECKED(UKismetSystemLibrary, PrintString)));
				Graph->AddNode(Call, false, false);
				Call->AllocateDefaultPins();
				NewNode = Call;
			}
			else if (NodeType.Equals(TEXT("VariableGet"), ESearchCase::IgnoreCase))
			{
				UK2Node_VariableGet* GetNode = NewObject<UK2Node_VariableGet>(Graph);
				GetNode->VariableReference.SetSelfMember(FName(*Params->GetStringField(TEXT("variable_name"))));
				Graph->AddNode(GetNode, false, false);
				GetNode->AllocateDefaultPins();
				NewNode = GetNode;
			}
			else if (NodeType.Equals(TEXT("VariableSet"), ESearchCase::IgnoreCase))
			{
				UK2Node_VariableSet* SetNode = NewObject<UK2Node_VariableSet>(Graph);
				SetNode->VariableReference.SetSelfMember(FName(*Params->GetStringField(TEXT("variable_name"))));
				Graph->AddNode(SetNode, false, false);
				SetNode->AllocateDefaultPins();
				NewNode = SetNode;
			}
			else
			{
				Obj->SetStringField(TEXT("error"), FString::Printf(TEXT("Unsupported node_type: %s"), *NodeType));
				return Obj;
			}
			if (Params->HasField(TEXT("x")) || Params->HasField(TEXT("y")))
			{
				NewNode->NodePosX = Params->HasField(TEXT("x")) ? static_cast<int32>(Params->GetNumberField(TEXT("x"))) : 0;
				NewNode->NodePosY = Params->HasField(TEXT("y")) ? static_cast<int32>(Params->GetNumberField(TEXT("y"))) : 0;
			}
			FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(BP);
			Obj->SetStringField(TEXT("node"), NewNode->GetName());
			Obj->SetStringField(TEXT("class"), NewNode->GetClass()->GetName());
			return Obj;
		});
		if (Result->HasField(TEXT("error"))) return Fail(Req, TEXT("engine_error"), Result->GetStringField(TEXT("error")));
		return Ok(Req, Result);
	}), TEXT("Create a Blueprint node."));

	Reg.Register(TEXT("unreal_connect_blueprint_nodes"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		TSharedPtr<FJsonObject> Params = Req.Params;
		TSharedPtr<FJsonObject> Result = FUnrealEngineMCPGameThreadDispatcher::RunJson([Params]()
		{
			TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
			UBlueprint* BP = LoadBP(Params->GetStringField(TEXT("path")));
			if (!BP) { Obj->SetStringField(TEXT("error"), TEXT("Blueprint not found")); return Obj; }
			UEdGraph* Graph = BP->UbergraphPages.Num() > 0 ? BP->UbergraphPages[0] : nullptr;
			if (!Graph) { Obj->SetStringField(TEXT("error"), TEXT("No ubergraph")); return Obj; }
			FString FromNodeName = Params->GetStringField(TEXT("from_node"));
			FString ToNodeName = Params->GetStringField(TEXT("to_node"));
			FString FromPinName = Params->HasField(TEXT("from_pin")) ? Params->GetStringField(TEXT("from_pin")) : TEXT("then");
			FString ToPinName = Params->HasField(TEXT("to_pin")) ? Params->GetStringField(TEXT("to_pin")) : TEXT("execute");
			UEdGraphNode* FromNode = nullptr; UEdGraphNode* ToNode = nullptr;
			for (UEdGraphNode* Node : Graph->Nodes)
			{
				if (!Node) continue;
				if (Node->GetName().Equals(FromNodeName, ESearchCase::IgnoreCase)) FromNode = Node;
				if (Node->GetName().Equals(ToNodeName, ESearchCase::IgnoreCase)) ToNode = Node;
			}
			if (!FromNode || !ToNode) { Obj->SetStringField(TEXT("error"), TEXT("Node not found")); return Obj; }
			UEdGraphPin* FromPin = FromNode->FindPin(FName(*FromPinName));
			UEdGraphPin* ToPin = ToNode->FindPin(FName(*ToPinName));
			if (!FromPin || !ToPin) { Obj->SetStringField(TEXT("error"), TEXT("Pin not found")); return Obj; }
			FromPin->MakeLinkTo(ToPin);
			FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(BP);
			Obj->SetBoolField(TEXT("connected"), true);
			return Obj;
		});
		if (Result->HasField(TEXT("error"))) return Fail(Req, TEXT("engine_error"), Result->GetStringField(TEXT("error")));
		return Ok(Req, Result);
	}), TEXT("Connect two Blueprint node pins."));

	Reg.Register(TEXT("unreal_disconnect_blueprint_nodes"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		TSharedPtr<FJsonObject> Params = Req.Params;
		TSharedPtr<FJsonObject> Result = FUnrealEngineMCPGameThreadDispatcher::RunJson([Params]()
		{
			TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
			UBlueprint* BP = LoadBP(Params->GetStringField(TEXT("path")));
			if (!BP) { Obj->SetStringField(TEXT("error"), TEXT("Blueprint not found")); return Obj; }
			UEdGraph* Graph = BP->UbergraphPages.Num() > 0 ? BP->UbergraphPages[0] : nullptr;
			UEdGraphNode* Node = nullptr;
			for (UEdGraphNode* N : Graph->Nodes)
			{
				if (N && N->GetName().Equals(Params->GetStringField(TEXT("node")), ESearchCase::IgnoreCase)) { Node = N; break; }
			}
			if (!Node) { Obj->SetStringField(TEXT("error"), TEXT("Node not found")); return Obj; }
			UEdGraphPin* Pin = Node->FindPin(FName(*Params->GetStringField(TEXT("pin"))));
			if (!Pin) { Obj->SetStringField(TEXT("error"), TEXT("Pin not found")); return Obj; }
			Pin->BreakAllPinLinks();
			FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(BP);
			Obj->SetBoolField(TEXT("disconnected"), true);
			return Obj;
		});
		if (Result->HasField(TEXT("error"))) return Fail(Req, TEXT("engine_error"), Result->GetStringField(TEXT("error")));
		return Ok(Req, Result);
	}), TEXT("Disconnect Blueprint node pins."));

	Reg.Register(TEXT("unreal_delete_blueprint_node"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		TSharedPtr<FJsonObject> Params = Req.Params;
		TSharedPtr<FJsonObject> Result = FUnrealEngineMCPGameThreadDispatcher::RunJson([Params]()
		{
			TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
			UBlueprint* BP = LoadBP(Params->GetStringField(TEXT("path")));
			if (!BP) { Obj->SetStringField(TEXT("error"), TEXT("Blueprint not found")); return Obj; }
			UEdGraph* Graph = BP->UbergraphPages.Num() > 0 ? BP->UbergraphPages[0] : nullptr;
			for (UEdGraphNode* Node : Graph->Nodes)
			{
				if (Node && Node->GetName().Equals(Params->GetStringField(TEXT("node")), ESearchCase::IgnoreCase))
				{
					FBlueprintEditorUtils::RemoveNode(BP, Node);
					Obj->SetBoolField(TEXT("deleted"), true);
					return Obj;
				}
			}
			Obj->SetStringField(TEXT("error"), TEXT("Node not found"));
			return Obj;
		});
		if (Result->HasField(TEXT("error"))) return Fail(Req, TEXT("engine_error"), Result->GetStringField(TEXT("error")));
		return Ok(Req, Result);
	}), TEXT("Delete a Blueprint node."));

	Reg.Register(TEXT("unreal_get_blueprint_node_details"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		TSharedPtr<FJsonObject> Params = Req.Params;
		TSharedPtr<FJsonObject> Result = FUnrealEngineMCPGameThreadDispatcher::RunJson([Params]()
		{
			TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
			UBlueprint* BP = LoadBP(Params->GetStringField(TEXT("path")));
			if (!BP) { Obj->SetStringField(TEXT("error"), TEXT("Blueprint not found")); return Obj; }
			UEdGraph* Graph = BP->UbergraphPages.Num() > 0 ? BP->UbergraphPages[0] : nullptr;
			for (UEdGraphNode* Node : Graph->Nodes)
			{
				if (!Node || !Node->GetName().Equals(Params->GetStringField(TEXT("node")), ESearchCase::IgnoreCase)) continue;
				Obj->SetStringField(TEXT("name"), Node->GetName());
				Obj->SetStringField(TEXT("class"), Node->GetClass()->GetName());
				Obj->SetStringField(TEXT("title"), Node->GetNodeTitle(ENodeTitleType::FullTitle).ToString());
				TArray<TSharedPtr<FJsonValue>> Pins;
				for (UEdGraphPin* Pin : Node->Pins)
				{
					TSharedPtr<FJsonObject> P = MakeShared<FJsonObject>();
					P->SetStringField(TEXT("name"), Pin->PinName.ToString());
					P->SetStringField(TEXT("direction"), Pin->Direction == EGPD_Input ? TEXT("input") : TEXT("output"));
					P->SetStringField(TEXT("category"), Pin->PinType.PinCategory.ToString());
					P->SetNumberField(TEXT("links"), Pin->LinkedTo.Num());
					Pins.Add(MakeShared<FJsonValueObject>(P));
				}
				Obj->SetArrayField(TEXT("pins"), Pins);
				return Obj;
			}
			Obj->SetStringField(TEXT("error"), TEXT("Node not found"));
			return Obj;
		});
		if (Result->HasField(TEXT("error"))) return Fail(Req, TEXT("engine_error"), Result->GetStringField(TEXT("error")));
		return Ok(Req, Result);
	}), TEXT("Get Blueprint node/pin details."));

	Reg.Register(TEXT("unreal_add_blueprint_function"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		TSharedPtr<FJsonObject> Params = Req.Params;
		TSharedPtr<FJsonObject> Result = FUnrealEngineMCPGameThreadDispatcher::RunJson([Params]()
		{
			TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
			UBlueprint* BP = LoadBP(Params->GetStringField(TEXT("path")));
			if (!BP) { Obj->SetStringField(TEXT("error"), TEXT("Blueprint not found")); return Obj; }
			FString FuncName = Params->GetStringField(TEXT("function_name"));
			UEdGraph* Graph = FBlueprintEditorUtils::CreateNewGraph(BP, FName(*FuncName), UEdGraph::StaticClass(), UEdGraphSchema_K2::StaticClass());
			FBlueprintEditorUtils::AddFunctionGraph<UFunction>(BP, Graph, false, nullptr);
			Obj->SetStringField(TEXT("function"), FuncName);
			return Obj;
		});
		if (Result->HasField(TEXT("error"))) return Fail(Req, TEXT("engine_error"), Result->GetStringField(TEXT("error")));
		return Ok(Req, Result);
	}), TEXT("Add a Blueprint function graph."));

	Reg.Register(TEXT("unreal_get_blueprint_functions"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		TSharedPtr<FJsonObject> Params = Req.Params;
		TSharedPtr<FJsonObject> Result = FUnrealEngineMCPGameThreadDispatcher::RunJson([Params]()
		{
			TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
			UBlueprint* BP = LoadBP(Params->GetStringField(TEXT("path")));
			if (!BP) { Obj->SetStringField(TEXT("error"), TEXT("Blueprint not found")); return Obj; }
			TArray<TSharedPtr<FJsonValue>> Fns;
			for (UEdGraph* Graph : BP->FunctionGraphs)
			{
				if (Graph) Fns.Add(MakeShared<FJsonValueString>(Graph->GetName()));
			}
			Obj->SetArrayField(TEXT("functions"), Fns);
			return Obj;
		});
		if (Result->HasField(TEXT("error"))) return Fail(Req, TEXT("engine_error"), Result->GetStringField(TEXT("error")));
		return Ok(Req, Result);
	}), TEXT("List Blueprint functions."));

	Reg.Register(TEXT("unreal_add_blueprint_event"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		TSharedPtr<FJsonObject> Params = Req.Params;
		Params->SetStringField(TEXT("node_type"), TEXT("EventBeginPlay"));
		// Reuse create node path by constructing synthetic request handled inline
		TSharedPtr<FJsonObject> Result = FUnrealEngineMCPGameThreadDispatcher::RunJson([Params]()
		{
			TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
			UBlueprint* BP = LoadBP(Params->GetStringField(TEXT("path")));
			if (!BP) { Obj->SetStringField(TEXT("error"), TEXT("Blueprint not found")); return Obj; }
			UEdGraph* Graph = BP->UbergraphPages.Num() > 0 ? BP->UbergraphPages[0] : nullptr;
			UK2Node_Event* EventNode = NewObject<UK2Node_Event>(Graph);
			FString EventName = Params->HasField(TEXT("event_name")) ? Params->GetStringField(TEXT("event_name")) : TEXT("ReceiveBeginPlay");
			EventNode->EventReference.SetExternalMember(FName(*EventName), AActor::StaticClass());
			EventNode->bOverrideFunction = true;
			Graph->AddNode(EventNode, false, false);
			EventNode->AllocateDefaultPins();
			FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(BP);
			Obj->SetStringField(TEXT("event"), EventName);
			Obj->SetStringField(TEXT("node"), EventNode->GetName());
			return Obj;
		});
		if (Result->HasField(TEXT("error"))) return Fail(Req, TEXT("engine_error"), Result->GetStringField(TEXT("error")));
		return Ok(Req, Result);
	}), TEXT("Add a Blueprint event node."));

	Reg.Register(TEXT("unreal_set_blueprint_node_property"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		return Fail(Req, TEXT("unsupported"), TEXT("Arbitrary node property editing is limited; use typed node creation tools."));
	}), TEXT("Set a Blueprint node property."));

	Reg.Register(TEXT("unreal_create_blueprint_macro"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		return Fail(Req, TEXT("unsupported"), TEXT("Macro graph creation is not implemented in this build."));
	}), TEXT("Create a Blueprint macro graph."));

	Reg.Register(TEXT("unreal_add_blueprint_component"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		TSharedPtr<FJsonObject> Params = Req.Params;
		TSharedPtr<FJsonObject> Result = FUnrealEngineMCPGameThreadDispatcher::RunJson([Params]()
		{
			TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
			UBlueprint* BP = LoadBP(Params->GetStringField(TEXT("path")));
			if (!BP || !BP->SimpleConstructionScript) { Obj->SetStringField(TEXT("error"), TEXT("Blueprint/SCS not found")); return Obj; }
			FString CompClassName = Params->GetStringField(TEXT("component_class"));
			UClass* CompClass = FindObject<UClass>(nullptr, *FString::Printf(TEXT("/Script/Engine.%s"), *CompClassName));
			if (!CompClass) CompClass = LoadObject<UClass>(nullptr, *CompClassName);
			if (!CompClass || !CompClass->IsChildOf(UActorComponent::StaticClass()))
			{
				Obj->SetStringField(TEXT("error"), TEXT("Invalid component class"));
				return Obj;
			}
			USCS_Node* Node = BP->SimpleConstructionScript->CreateNode(CompClass, FName(*Params->GetStringField(TEXT("component_name"))));
			BP->SimpleConstructionScript->AddNode(Node);
			FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(BP);
			Obj->SetStringField(TEXT("component"), Node->GetVariableName().ToString());
			return Obj;
		});
		if (Result->HasField(TEXT("error"))) return Fail(Req, TEXT("engine_error"), Result->GetStringField(TEXT("error")));
		return Ok(Req, Result);
	}), TEXT("Add a component to a Blueprint SCS."));

	Reg.Register(TEXT("unreal_set_blueprint_parent_class"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		TSharedPtr<FJsonObject> Params = Req.Params;
		TSharedPtr<FJsonObject> Result = FUnrealEngineMCPGameThreadDispatcher::RunJson([Params]()
		{
			TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
			UBlueprint* BP = LoadBP(Params->GetStringField(TEXT("path")));
			if (!BP) { Obj->SetStringField(TEXT("error"), TEXT("Blueprint not found")); return Obj; }
			FString ParentName = Params->GetStringField(TEXT("parent_class"));
			UClass* Parent = FindObject<UClass>(nullptr, *FString::Printf(TEXT("/Script/Engine.%s"), *ParentName));
			if (!Parent) Parent = LoadObject<UClass>(nullptr, *ParentName);
			if (!Parent) { Obj->SetStringField(TEXT("error"), TEXT("Parent class not found")); return Obj; }
			BP->ParentClass = Parent;
			FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(BP);
			Obj->SetStringField(TEXT("parent"), Parent->GetName());
			return Obj;
		});
		if (Result->HasField(TEXT("error"))) return Fail(Req, TEXT("engine_error"), Result->GetStringField(TEXT("error")));
		return Ok(Req, Result);
	}), TEXT("Set Blueprint parent class."));
}
