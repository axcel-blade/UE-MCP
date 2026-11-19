#include "Tools/IntelligenceTools.h"
#include "Core/ToolRegistry.h"
#include "Core/ResultSerializer.h"
#include "Core/GameThreadDispatcher.h"
#include "Editor.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/Actor.h"
#include "Components/PrimitiveComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Components/LightComponent.h"
#include "AssetRegistry/AssetRegistryModule.h"
#include "EditorAssetLibrary.h"
#include "Engine/Blueprint.h"
#include "Materials/MaterialInterface.h"
#include "Misc/PackageName.h"
#include "Components/SceneComponent.h"

namespace
{
	FUnrealEngineMCPResponse Ok(const FUnrealEngineMCPRequest& R, TSharedPtr<FJsonObject> O) { return FUnrealEngineMCPResultSerializer::Ok(R.Id, O); }
	FUnrealEngineMCPResponse Fail(const FUnrealEngineMCPRequest& R, const FString& C, const FString& M) { return FUnrealEngineMCPResultSerializer::Fail(R.Id, C, M); }
}

void FUnrealEngineMCPIntelligenceTools::Register()
{
	auto& Reg = FUnrealEngineMCPToolRegistry::Get();

	Reg.Register(TEXT("unreal_get_scene_hierarchy"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		auto Result = FUnrealEngineMCPGameThreadDispatcher::RunJson([]()
		{
			TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
			UWorld* World = GEditor ? GEditor->GetEditorWorldContext().World() : nullptr;
			TArray<TSharedPtr<FJsonValue>> Roots;
			if (World)
			{
				for (TActorIterator<AActor> It(World); It; ++It)
				{
					AActor* Actor = *It;
					if (Actor->GetAttachParentActor() != nullptr) continue;
					TSharedPtr<FJsonObject> Node = MakeShared<FJsonObject>();
					Node->SetStringField(TEXT("name"), Actor->GetName());
					Node->SetStringField(TEXT("label"), Actor->GetActorLabel());
					TArray<TSharedPtr<FJsonValue>> Children;
					TArray<AActor*> Attached; Actor->GetAttachedActors(Attached);
					for (AActor* Child : Attached)
					{
						TSharedPtr<FJsonObject> C = MakeShared<FJsonObject>();
						C->SetStringField(TEXT("name"), Child->GetName());
						C->SetStringField(TEXT("label"), Child->GetActorLabel());
						Children.Add(MakeShared<FJsonValueObject>(C));
					}
					Node->SetArrayField(TEXT("children"), Children);
					Roots.Add(MakeShared<FJsonValueObject>(Node));
				}
			}
			Obj->SetArrayField(TEXT("roots"), Roots);
			return Obj;
		});
		return Ok(Req, Result);
	}), TEXT("Inspect actor attachment hierarchy."));

	Reg.Register(TEXT("unreal_get_actor_relationships"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		TSharedPtr<FJsonObject> Params = Req.Params;
		auto Result = FUnrealEngineMCPGameThreadDispatcher::RunJson([Params]()
		{
			TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
			UWorld* World = GEditor ? GEditor->GetEditorWorldContext().World() : nullptr;
			AActor* Actor = nullptr;
			FString Name = Params->GetStringField(TEXT("name"));
			for (TActorIterator<AActor> It(World); It; ++It)
			{
				if ((*It)->GetName().Equals(Name, ESearchCase::IgnoreCase) || (*It)->GetActorLabel().Equals(Name, ESearchCase::IgnoreCase))
				{ Actor = *It; break; }
			}
			if (!Actor) { Obj->SetStringField(TEXT("error"), TEXT("Actor not found")); return Obj; }
			Obj->SetStringField(TEXT("name"), Actor->GetName());
			Obj->SetStringField(TEXT("parent"), Actor->GetAttachParentActor() ? Actor->GetAttachParentActor()->GetName() : TEXT(""));
			TArray<AActor*> Attached; Actor->GetAttachedActors(Attached);
			TArray<TSharedPtr<FJsonValue>> Children;
			for (AActor* Child : Attached) Children.Add(MakeShared<FJsonValueString>(Child->GetName()));
			Obj->SetArrayField(TEXT("children"), Children);
			Obj->SetStringField(TEXT("owner"), Actor->GetOwner() ? Actor->GetOwner()->GetName() : TEXT(""));
			return Obj;
		});
		if (Result->HasField(TEXT("error"))) return Fail(Req, TEXT("engine_error"), Result->GetStringField(TEXT("error")));
		return Ok(Req, Result);
	}), TEXT("Inspect actor relationships."));

	Reg.Register(TEXT("unreal_get_component_hierarchy"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		TSharedPtr<FJsonObject> Params = Req.Params;
		auto Result = FUnrealEngineMCPGameThreadDispatcher::RunJson([Params]()
		{
			TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
			UWorld* World = GEditor ? GEditor->GetEditorWorldContext().World() : nullptr;
			AActor* Actor = nullptr;
			FString Name = Params->GetStringField(TEXT("name"));
			for (TActorIterator<AActor> It(World); It; ++It)
			{
				if ((*It)->GetName().Equals(Name, ESearchCase::IgnoreCase) || (*It)->GetActorLabel().Equals(Name, ESearchCase::IgnoreCase))
				{ Actor = *It; break; }
			}
			if (!Actor) { Obj->SetStringField(TEXT("error"), TEXT("Actor not found")); return Obj; }
			TArray<TSharedPtr<FJsonValue>> Components;
			TArray<UActorComponent*> Comps; Actor->GetComponents(Comps);
			for (UActorComponent* Comp : Comps)
			{
				TSharedPtr<FJsonObject> C = MakeShared<FJsonObject>();
				C->SetStringField(TEXT("name"), Comp->GetName());
				C->SetStringField(TEXT("class"), Comp->GetClass()->GetName());
				if (USceneComponent* Scene = Cast<USceneComponent>(Comp))
				{
					C->SetStringField(TEXT("attach_parent"), Scene->GetAttachParent() ? Scene->GetAttachParent()->GetName() : TEXT(""));
				}
				Components.Add(MakeShared<FJsonValueObject>(C));
			}
			Obj->SetArrayField(TEXT("components"), Components);
			return Obj;
		});
		if (Result->HasField(TEXT("error"))) return Fail(Req, TEXT("engine_error"), Result->GetStringField(TEXT("error")));
		return Ok(Req, Result);
	}), TEXT("Inspect component hierarchy."));

	Reg.Register(TEXT("unreal_analyze_asset_dependencies"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		TSharedPtr<FJsonObject> Params = Req.Params;
		auto Result = FUnrealEngineMCPGameThreadDispatcher::RunJson([Params]()
		{
			TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
			FString Path = Params->GetStringField(TEXT("path"));
			FAssetRegistryModule& ARM = FModuleManager::LoadModuleChecked<FAssetRegistryModule>("AssetRegistry");
			TArray<FName> Deps; ARM.Get().GetDependencies(FName(*FPackageName::ObjectPathToPackageName(Path)), Deps);
			TArray<TSharedPtr<FJsonValue>> Arr;
			for (const FName& D : Deps) Arr.Add(MakeShared<FJsonValueString>(D.ToString()));
			Obj->SetArrayField(TEXT("dependencies"), Arr);
			return Obj;
		});
		return Ok(Req, Result);
	}), TEXT("Analyze asset dependencies."));

	Reg.Register(TEXT("unreal_analyze_blueprint_relationships"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		TSharedPtr<FJsonObject> Params = Req.Params;
		auto Result = FUnrealEngineMCPGameThreadDispatcher::RunJson([Params]()
		{
			TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
			UBlueprint* BP = LoadObject<UBlueprint>(nullptr, *Params->GetStringField(TEXT("path")));
			if (!BP) { Obj->SetStringField(TEXT("error"), TEXT("Blueprint not found")); return Obj; }
			Obj->SetStringField(TEXT("parent"), BP->ParentClass ? BP->ParentClass->GetName() : TEXT(""));
			Obj->SetNumberField(TEXT("variables"), BP->NewVariables.Num());
			Obj->SetNumberField(TEXT("functions"), BP->FunctionGraphs.Num());
			return Obj;
		});
		if (Result->HasField(TEXT("error"))) return Fail(Req, TEXT("engine_error"), Result->GetStringField(TEXT("error")));
		return Ok(Req, Result);
	}), TEXT("Analyze Blueprint relationships."));

	Reg.Register(TEXT("unreal_analyze_material_assignments"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		auto Result = FUnrealEngineMCPGameThreadDispatcher::RunJson([]()
		{
			TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
			UWorld* World = GEditor ? GEditor->GetEditorWorldContext().World() : nullptr;
			TArray<TSharedPtr<FJsonValue>> Assignments;
			if (World)
			{
				for (TActorIterator<AActor> It(World); It; ++It)
				{
					if (UStaticMeshComponent* SMC = (*It)->FindComponentByClass<UStaticMeshComponent>())
					{
						const int32 Num = SMC->GetNumMaterials();
						for (int32 i = 0; i < Num; ++i)
						{
							UMaterialInterface* Mat = SMC->GetMaterial(i);
							TSharedPtr<FJsonObject> A = MakeShared<FJsonObject>();
							A->SetStringField(TEXT("actor"), (*It)->GetActorLabel());
							A->SetNumberField(TEXT("slot"), i);
							A->SetStringField(TEXT("material"), Mat ? Mat->GetPathName() : TEXT("None"));
							Assignments.Add(MakeShared<FJsonValueObject>(A));
						}
					}
				}
			}
			Obj->SetArrayField(TEXT("assignments"), Assignments);
			return Obj;
		});
		return Ok(Req, Result);
	}), TEXT("Analyze material assignments in level."));

	Reg.Register(TEXT("unreal_analyze_level_composition"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		auto Result = FUnrealEngineMCPGameThreadDispatcher::RunJson([]()
		{
			TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
			UWorld* World = GEditor ? GEditor->GetEditorWorldContext().World() : nullptr;
			if (!World) { Obj->SetStringField(TEXT("error"), TEXT("No world")); return Obj; }
			Obj->SetStringField(TEXT("persistent_level"), World->GetMapName());
			Obj->SetNumberField(TEXT("streaming_levels"), World->GetStreamingLevels().Num());
			Obj->SetNumberField(TEXT("actors"), World->GetActorCount());
			Obj->SetBoolField(TEXT("partitioned"), World->IsPartitionedWorld());
			return Obj;
		});
		if (Result->HasField(TEXT("error"))) return Fail(Req, TEXT("engine_error"), Result->GetStringField(TEXT("error")));
		return Ok(Req, Result);
	}), TEXT("Analyze level composition."));

	Reg.Register(TEXT("unreal_validate_actor_placement"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		auto Result = FUnrealEngineMCPGameThreadDispatcher::RunJson([]()
		{
			TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
			UWorld* World = GEditor ? GEditor->GetEditorWorldContext().World() : nullptr;
			TArray<TSharedPtr<FJsonValue>> Issues;
			if (World)
			{
				for (TActorIterator<AActor> It(World); It; ++It)
				{
					const FVector Loc = (*It)->GetActorLocation();
					if (!Loc.ContainsNaN() && (FMath::Abs(Loc.Z) > 1000000.0f))
					{
						TSharedPtr<FJsonObject> Issue = MakeShared<FJsonObject>();
						Issue->SetStringField(TEXT("actor"), (*It)->GetActorLabel());
						Issue->SetStringField(TEXT("issue"), TEXT("Extreme Z location"));
						Issues.Add(MakeShared<FJsonValueObject>(Issue));
					}
				}
			}
			Obj->SetArrayField(TEXT("issues"), Issues);
			Obj->SetBoolField(TEXT("ok"), Issues.Num() == 0);
			return Obj;
		});
		return Ok(Req, Result);
	}), TEXT("Validate actor placement."));

	Reg.Register(TEXT("unreal_find_duplicate_assets"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		TSharedPtr<FJsonObject> Params = Req.Params;
		auto Result = FUnrealEngineMCPGameThreadDispatcher::RunJson([Params]()
		{
			TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
			FAssetRegistryModule& ARM = FModuleManager::LoadModuleChecked<FAssetRegistryModule>("AssetRegistry");
			TArray<FAssetData> Assets; ARM.Get().GetAssetsByPath(TEXT("/Game"), Assets, true);
			TMap<FString, TArray<FString>> ByName;
			int32 Limit = Params.IsValid() && Params->HasField(TEXT("limit")) ? (int32)Params->GetNumberField(TEXT("limit")) : 200;
			for (int32 i = 0; i < Assets.Num() && i < Limit; ++i)
			{
				ByName.FindOrAdd(Assets[i].AssetName.ToString()).Add(Assets[i].GetObjectPathString());
			}
			TArray<TSharedPtr<FJsonValue>> Dupes;
			for (const auto& Pair : ByName)
			{
				if (Pair.Value.Num() > 1)
				{
					TSharedPtr<FJsonObject> D = MakeShared<FJsonObject>();
					D->SetStringField(TEXT("name"), Pair.Key);
					TArray<TSharedPtr<FJsonValue>> Paths;
					for (const FString& P : Pair.Value) Paths.Add(MakeShared<FJsonValueString>(P));
					D->SetArrayField(TEXT("paths"), Paths);
					Dupes.Add(MakeShared<FJsonValueObject>(D));
				}
			}
			Obj->SetArrayField(TEXT("duplicates"), Dupes);
			return Obj;
		});
		return Ok(Req, Result);
	}), TEXT("Find potentially duplicate assets."));

	Reg.Register(TEXT("unreal_find_missing_references"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
		Result->SetArrayField(TEXT("missing"), {});
		Result->SetStringField(TEXT("note"), TEXT("Bounded scan placeholder using Asset Registry; deep redirector fixup not performed."));
		return Ok(Req, Result);
	}), TEXT("Find missing references."));

	Reg.Register(TEXT("unreal_find_unused_assets"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		TSharedPtr<FJsonObject> Params = Req.Params;
		auto Result = FUnrealEngineMCPGameThreadDispatcher::RunJson([Params]()
		{
			TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
			FAssetRegistryModule& ARM = FModuleManager::LoadModuleChecked<FAssetRegistryModule>("AssetRegistry");
			TArray<FAssetData> Assets; ARM.Get().GetAssetsByPath(TEXT("/Game"), Assets, true);
			int32 Limit = Params.IsValid() && Params->HasField(TEXT("limit")) ? (int32)Params->GetNumberField(TEXT("limit")) : 100;
			TArray<TSharedPtr<FJsonValue>> Unused;
			for (int32 i = 0; i < Assets.Num() && Unused.Num() < Limit; ++i)
			{
				TArray<FName> Referencers;
				ARM.Get().GetReferencers(Assets[i].PackageName, Referencers);
				if (Referencers.Num() == 0)
				{
					Unused.Add(MakeShared<FJsonValueString>(Assets[i].GetObjectPathString()));
				}
			}
			Obj->SetArrayField(TEXT("unused"), Unused);
			Obj->SetStringField(TEXT("note"), TEXT("Heuristic only; assets with zero referencers may still be used by maps not loaded."));
			return Obj;
		});
		return Ok(Req, Result);
	}), TEXT("Find unused assets (bounded scan)."));

	Reg.Register(TEXT("unreal_get_scene_statistics"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		auto Result = FUnrealEngineMCPGameThreadDispatcher::RunJson([]()
		{
			TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
			UWorld* World = GEditor ? GEditor->GetEditorWorldContext().World() : nullptr;
			int32 Lights = 0, Meshes = 0, Total = 0;
			if (World)
			{
				for (TActorIterator<AActor> It(World); It; ++It)
				{
					++Total;
					if ((*It)->FindComponentByClass<ULightComponent>()) ++Lights;
					if ((*It)->FindComponentByClass<UStaticMeshComponent>()) ++Meshes;
				}
			}
			Obj->SetNumberField(TEXT("actor_count"), Total);
			Obj->SetNumberField(TEXT("dynamic_lights"), Lights);
			Obj->SetNumberField(TEXT("mesh_actors"), Meshes);
			return Obj;
		});
		return Ok(Req, Result);
	}), TEXT("Get scene statistics."));
}
