#include "Tools/LevelTools.h"
#include "Core/ToolRegistry.h"
#include "Core/ResultSerializer.h"
#include "Core/GameThreadDispatcher.h"
#include "Editor.h"
#include "Engine/World.h"
#include "Engine/Level.h"
#include "EngineUtils.h"
#include "FileHelpers.h"
#include "EditorLevelUtils.h"
#include "Engine/LevelStreaming.h"
#include "Engine/LevelStreamingDynamic.h"
#include "GameFramework/WorldSettings.h"
#include "AssetRegistry/AssetRegistryModule.h"
#include "AssetToolsModule.h"
#include "Factories/WorldFactory.h"
#include "Misc/PackageName.h"
#include "UObject/SavePackage.h"
#include "GameFramework/Actor.h"
#include "EditorAssetLibrary.h"

namespace
{
	FUnrealEngineMCPResponse Ok(const FUnrealEngineMCPRequest& Req, TSharedPtr<FJsonObject> Result)
	{
		return FUnrealEngineMCPResultSerializer::Ok(Req.Id, Result);
	}
	FUnrealEngineMCPResponse Fail(const FUnrealEngineMCPRequest& Req, const FString& Code, const FString& Message)
	{
		return FUnrealEngineMCPResultSerializer::Fail(Req.Id, Code, Message);
	}
}

void FUnrealEngineMCPLevelTools::Register()
{
	auto& Reg = FUnrealEngineMCPToolRegistry::Get();

	Reg.Register(TEXT("unreal_create_level"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		TSharedPtr<FJsonObject> Params = Req.Params;
		TSharedPtr<FJsonObject> Result = FUnrealEngineMCPGameThreadDispatcher::RunJson([Params]()
		{
			TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
			FString Path = Params->GetStringField(TEXT("path"));
			if (Path.IsEmpty())
			{
				Obj->SetStringField(TEXT("error"), TEXT("path is required, e.g. /Game/Maps/NewMap"));
				return Obj;
			}

			UWorldFactory* Factory = NewObject<UWorldFactory>();
			IAssetTools& AssetTools = FModuleManager::LoadModuleChecked<FAssetToolsModule>("AssetTools").Get();
			FString PackagePath = FPackageName::GetLongPackagePath(Path);
			FString AssetName = FPackageName::GetShortName(Path);
			UObject* NewAsset = AssetTools.CreateAsset(AssetName, PackagePath, UWorld::StaticClass(), Factory);
			if (!NewAsset)
			{
				Obj->SetStringField(TEXT("error"), TEXT("Failed to create level asset"));
				return Obj;
			}
			Obj->SetStringField(TEXT("path"), NewAsset->GetPathName());
			Obj->SetStringField(TEXT("name"), NewAsset->GetName());
			return Obj;
		});
		if (Result->HasField(TEXT("error"))) return Fail(Req, TEXT("engine_error"), Result->GetStringField(TEXT("error")));
		return Ok(Req, Result);
	}), TEXT("Create a new level asset."));

	Reg.Register(TEXT("unreal_open_level"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		TSharedPtr<FJsonObject> Params = Req.Params;
		TSharedPtr<FJsonObject> Result = FUnrealEngineMCPGameThreadDispatcher::RunJson([Params]()
		{
			TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
			FString Path = Params->GetStringField(TEXT("path"));
			if (!FEditorFileUtils::LoadMap(Path))
			{
				Obj->SetStringField(TEXT("error"), FString::Printf(TEXT("Failed to open level: %s"), *Path));
				return Obj;
			}
			Obj->SetStringField(TEXT("opened"), Path);
			return Obj;
		});
		if (Result->HasField(TEXT("error"))) return Fail(Req, TEXT("engine_error"), Result->GetStringField(TEXT("error")));
		return Ok(Req, Result);
	}), TEXT("Open a level."));

	Reg.Register(TEXT("unreal_save_level"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		TSharedPtr<FJsonObject> Result = FUnrealEngineMCPGameThreadDispatcher::RunJson([]()
		{
			TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
			UWorld* World = GEditor ? GEditor->GetEditorWorldContext().World() : nullptr;
			if (!World)
			{
				Obj->SetStringField(TEXT("error"), TEXT("No editor world"));
				return Obj;
			}
			const bool bSaved = FEditorFileUtils::SaveCurrentLevel();
			Obj->SetBoolField(TEXT("saved"), bSaved);
			Obj->SetStringField(TEXT("level"), World->GetMapName());
			if (!bSaved)
			{
				Obj->SetStringField(TEXT("error"), TEXT("SaveCurrentLevel returned false"));
			}
			return Obj;
		});
		if (Result->HasField(TEXT("error")) && !Result->GetBoolField(TEXT("saved")))
		{
			return Fail(Req, TEXT("engine_error"), Result->GetStringField(TEXT("error")));
		}
		return Ok(Req, Result);
	}), TEXT("Save the current level."));

	Reg.Register(TEXT("unreal_get_levels"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		TSharedPtr<FJsonObject> Params = Req.Params;
		TSharedPtr<FJsonObject> Result = FUnrealEngineMCPGameThreadDispatcher::RunJson([Params]()
		{
			TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
			FAssetRegistryModule& ARM = FModuleManager::LoadModuleChecked<FAssetRegistryModule>("AssetRegistry");
			TArray<FAssetData> Assets;
			FARFilter Filter;
			Filter.ClassPaths.Add(UWorld::StaticClass()->GetClassPathName());
			Filter.bRecursivePaths = true;
			FString Path = Params.IsValid() && Params->HasField(TEXT("path")) ? Params->GetStringField(TEXT("path")) : TEXT("/Game");
			Filter.PackagePaths.Add(*Path);
			ARM.Get().GetAssets(Filter, Assets);
			int32 Limit = Params.IsValid() && Params->HasField(TEXT("limit")) ? static_cast<int32>(Params->GetNumberField(TEXT("limit"))) : 200;
			TArray<TSharedPtr<FJsonValue>> Levels;
			for (int32 i = 0; i < Assets.Num() && i < Limit; ++i)
			{
				TSharedPtr<FJsonObject> L = MakeShared<FJsonObject>();
				L->SetStringField(TEXT("name"), Assets[i].AssetName.ToString());
				L->SetStringField(TEXT("path"), Assets[i].GetObjectPathString());
				Levels.Add(MakeShared<FJsonValueObject>(L));
			}
			Obj->SetArrayField(TEXT("levels"), Levels);
			return Obj;
		});
		return Ok(Req, Result);
	}), TEXT("List levels in the project."));

	Reg.Register(TEXT("unreal_get_world_info"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		TSharedPtr<FJsonObject> Result = FUnrealEngineMCPGameThreadDispatcher::RunJson([]()
		{
			TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
			UWorld* World = GEditor ? GEditor->GetEditorWorldContext().World() : nullptr;
			if (!World)
			{
				Obj->SetStringField(TEXT("error"), TEXT("No editor world"));
				return Obj;
			}
			Obj->SetStringField(TEXT("name"), World->GetName());
			Obj->SetStringField(TEXT("path"), World->GetPathName());
			Obj->SetNumberField(TEXT("actor_count"), World->GetActorCount());
			Obj->SetNumberField(TEXT("streaming_levels"), World->GetStreamingLevels().Num());
			return Obj;
		});
		if (Result->HasField(TEXT("error"))) return Fail(Req, TEXT("engine_error"), Result->GetStringField(TEXT("error")));
		return Ok(Req, Result);
	}), TEXT("Get world and level info."));

	Reg.Register(TEXT("unreal_set_world_settings"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		TSharedPtr<FJsonObject> Params = Req.Params;
		TSharedPtr<FJsonObject> Result = FUnrealEngineMCPGameThreadDispatcher::RunJson([Params]()
		{
			TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
			UWorld* World = GEditor ? GEditor->GetEditorWorldContext().World() : nullptr;
			if (!World || !World->GetWorldSettings())
			{
				Obj->SetStringField(TEXT("error"), TEXT("No world settings"));
				return Obj;
			}
			AWorldSettings* Settings = World->GetWorldSettings();
			if (Params->HasField(TEXT("kill_z")))
			{
				Settings->KillZ = Params->GetNumberField(TEXT("kill_z"));
			}
			if (Params->HasField(TEXT("gravity_z")))
			{
				Settings->bGlobalGravitySet = true;
				Settings->GlobalGravityZ = Params->GetNumberField(TEXT("gravity_z"));
			}
			Settings->MarkPackageDirty();
			Obj->SetBoolField(TEXT("updated"), true);
			return Obj;
		});
		if (Result->HasField(TEXT("error"))) return Fail(Req, TEXT("engine_error"), Result->GetStringField(TEXT("error")));
		return Ok(Req, Result);
	}), TEXT("Set supported world settings."));

	Reg.Register(TEXT("unreal_create_sublevel"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		TSharedPtr<FJsonObject> Params = Req.Params;
		TSharedPtr<FJsonObject> Result = FUnrealEngineMCPGameThreadDispatcher::RunJson([Params]()
		{
			TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
			UWorld* World = GEditor ? GEditor->GetEditorWorldContext().World() : nullptr;
			if (!World)
			{
				Obj->SetStringField(TEXT("error"), TEXT("No editor world"));
				return Obj;
			}
			FString Path = Params->GetStringField(TEXT("path"));
			ULevelStreaming* Streaming = EditorLevelUtils::CreateNewStreamingLevel(ULevelStreamingDynamic::StaticClass(), Path, true);
			if (!Streaming)
			{
				Obj->SetStringField(TEXT("error"), TEXT("Failed to create streaming sublevel"));
				return Obj;
			}
			Obj->SetStringField(TEXT("path"), Path);
			return Obj;
		});
		if (Result->HasField(TEXT("error"))) return Fail(Req, TEXT("engine_error"), Result->GetStringField(TEXT("error")));
		return Ok(Req, Result);
	}), TEXT("Create a streaming sublevel."));

	Reg.Register(TEXT("unreal_manage_level_visibility"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		TSharedPtr<FJsonObject> Params = Req.Params;
		TSharedPtr<FJsonObject> Result = FUnrealEngineMCPGameThreadDispatcher::RunJson([Params]()
		{
			TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
			UWorld* World = GEditor ? GEditor->GetEditorWorldContext().World() : nullptr;
			if (!World)
			{
				Obj->SetStringField(TEXT("error"), TEXT("No editor world"));
				return Obj;
			}
			FString Path = Params->GetStringField(TEXT("path"));
			const bool bVisible = Params->HasField(TEXT("visible")) ? Params->GetBoolField(TEXT("visible")) : true;
			bool bFound = false;
			for (ULevelStreaming* Streaming : World->GetStreamingLevels())
			{
				if (Streaming && Streaming->GetWorldAssetPackageName().Contains(Path))
				{
					Streaming->SetShouldBeVisible(bVisible);
					Streaming->SetShouldBeLoaded(bVisible);
					bFound = true;
					break;
				}
			}
			if (!bFound)
			{
				Obj->SetStringField(TEXT("error"), TEXT("Streaming level not found"));
				return Obj;
			}
			Obj->SetBoolField(TEXT("visible"), bVisible);
			Obj->SetStringField(TEXT("path"), Path);
			return Obj;
		});
		if (Result->HasField(TEXT("error"))) return Fail(Req, TEXT("engine_error"), Result->GetStringField(TEXT("error")));
		return Ok(Req, Result);
	}), TEXT("Show/hide a streaming level."));

	Reg.Register(TEXT("unreal_list_level_actors"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		TSharedPtr<FJsonObject> Params = Req.Params;
		TSharedPtr<FJsonObject> Result = FUnrealEngineMCPGameThreadDispatcher::RunJson([Params]()
		{
			TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
			UWorld* World = GEditor ? GEditor->GetEditorWorldContext().World() : nullptr;
			int32 Limit = Params.IsValid() && Params->HasField(TEXT("limit")) ? static_cast<int32>(Params->GetNumberField(TEXT("limit"))) : 500;
			TArray<TSharedPtr<FJsonValue>> Actors;
			int32 Count = 0;
			if (World)
			{
				for (TActorIterator<AActor> It(World); It; ++It)
				{
					if (Count >= Limit) break;
					TSharedPtr<FJsonObject> A = MakeShared<FJsonObject>();
					A->SetStringField(TEXT("name"), (*It)->GetName());
					A->SetStringField(TEXT("label"), (*It)->GetActorLabel());
					A->SetStringField(TEXT("class"), (*It)->GetClass()->GetName());
					Actors.Add(MakeShared<FJsonValueObject>(A));
					++Count;
				}
			}
			Obj->SetArrayField(TEXT("actors"), Actors);
			return Obj;
		});
		return Ok(Req, Result);
	}), TEXT("List actors for a level."));

	Reg.Register(TEXT("unreal_create_world_partition_info"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		TSharedPtr<FJsonObject> Result = FUnrealEngineMCPGameThreadDispatcher::RunJson([]()
		{
			TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
			UWorld* World = GEditor ? GEditor->GetEditorWorldContext().World() : nullptr;
			if (!World)
			{
				Obj->SetStringField(TEXT("error"), TEXT("No editor world"));
				return Obj;
			}
			Obj->SetBoolField(TEXT("is_partitioned"), World->IsPartitionedWorld());
			Obj->SetStringField(TEXT("world"), World->GetName());
			return Obj;
		});
		if (Result->HasField(TEXT("error"))) return Fail(Req, TEXT("engine_error"), Result->GetStringField(TEXT("error")));
		return Ok(Req, Result);
	}), TEXT("Inspect world partition info when available."));
}
