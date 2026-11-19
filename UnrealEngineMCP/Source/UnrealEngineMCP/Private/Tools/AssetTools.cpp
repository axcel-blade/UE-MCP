#include "Tools/AssetTools.h"
#include "Core/ToolRegistry.h"
#include "Core/ResultSerializer.h"
#include "Core/GameThreadDispatcher.h"
#include "AssetRegistry/AssetRegistryModule.h"
#include "AssetToolsModule.h"
#include "EditorAssetLibrary.h"
#include "ObjectTools.h"
#include "Misc/PackageName.h"
#include "HAL/FileManager.h"
#include "AssetImportTask.h"
#include "IAssetTools.h"

namespace
{
	FUnrealEngineMCPResponse Ok(const FUnrealEngineMCPRequest& Req, TSharedPtr<FJsonObject> R) { return FUnrealEngineMCPResultSerializer::Ok(Req.Id, R); }
	FUnrealEngineMCPResponse Fail(const FUnrealEngineMCPRequest& Req, const FString& C, const FString& M) { return FUnrealEngineMCPResultSerializer::Fail(Req.Id, C, M); }

	TSharedPtr<FJsonObject> AssetDataToJson(const FAssetData& Data)
	{
		TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
		Obj->SetStringField(TEXT("name"), Data.AssetName.ToString());
		Obj->SetStringField(TEXT("path"), Data.GetObjectPathString());
		Obj->SetStringField(TEXT("class"), Data.AssetClassPath.GetAssetName().ToString());
		Obj->SetStringField(TEXT("package"), Data.PackageName.ToString());
		return Obj;
	}
}

void FUnrealEngineMCPAssetTools::Register()
{
	auto& Reg = FUnrealEngineMCPToolRegistry::Get();

	Reg.Register(TEXT("unreal_list_assets"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		TSharedPtr<FJsonObject> Params = Req.Params;
		TSharedPtr<FJsonObject> Result = FUnrealEngineMCPGameThreadDispatcher::RunJson([Params]()
		{
			TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
			FAssetRegistryModule& ARM = FModuleManager::LoadModuleChecked<FAssetRegistryModule>("AssetRegistry");
			FString Path = Params.IsValid() && Params->HasField(TEXT("path")) ? Params->GetStringField(TEXT("path")) : TEXT("/Game");
			int32 Limit = Params.IsValid() && Params->HasField(TEXT("limit")) ? static_cast<int32>(Params->GetNumberField(TEXT("limit"))) : 100;
			TArray<FAssetData> Assets;
			ARM.Get().GetAssetsByPath(*Path, Assets, true);
			TArray<TSharedPtr<FJsonValue>> Out;
			for (int32 i = 0; i < Assets.Num() && i < Limit; ++i)
			{
				Out.Add(MakeShared<FJsonValueObject>(AssetDataToJson(Assets[i])));
			}
			Obj->SetArrayField(TEXT("assets"), Out);
			Obj->SetNumberField(TEXT("count"), Out.Num());
			return Obj;
		});
		return Ok(Req, Result);
	}), TEXT("List assets under a content path."));

	Reg.Register(TEXT("unreal_search_assets"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		TSharedPtr<FJsonObject> Params = Req.Params;
		TSharedPtr<FJsonObject> Result = FUnrealEngineMCPGameThreadDispatcher::RunJson([Params]()
		{
			TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
			FAssetRegistryModule& ARM = FModuleManager::LoadModuleChecked<FAssetRegistryModule>("AssetRegistry");
			FString Name = Params->HasField(TEXT("name")) ? Params->GetStringField(TEXT("name")) : TEXT("");
			FString ClassName = Params->HasField(TEXT("class_name")) ? Params->GetStringField(TEXT("class_name")) : TEXT("");
			int32 Limit = Params->HasField(TEXT("limit")) ? static_cast<int32>(Params->GetNumberField(TEXT("limit"))) : 100;
			FARFilter Filter;
			Filter.bRecursivePaths = true;
			Filter.PackagePaths.Add(TEXT("/Game"));
			TArray<FAssetData> Assets;
			ARM.Get().GetAssets(Filter, Assets);
			TArray<TSharedPtr<FJsonValue>> Out;
			for (const FAssetData& Data : Assets)
			{
				if (Out.Num() >= Limit) break;
				const bool bName = Name.IsEmpty() || Data.AssetName.ToString().Contains(Name);
				const bool bClass = ClassName.IsEmpty() || Data.AssetClassPath.GetAssetName().ToString().Contains(ClassName);
				if (bName && bClass)
				{
					Out.Add(MakeShared<FJsonValueObject>(AssetDataToJson(Data)));
				}
			}
			Obj->SetArrayField(TEXT("assets"), Out);
			return Obj;
		});
		return Ok(Req, Result);
	}), TEXT("Search assets by name/class."));

	Reg.Register(TEXT("unreal_get_asset_info"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		TSharedPtr<FJsonObject> Params = Req.Params;
		TSharedPtr<FJsonObject> Result = FUnrealEngineMCPGameThreadDispatcher::RunJson([Params]()
		{
			TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
			FString Path = Params->GetStringField(TEXT("path"));
			FAssetRegistryModule& ARM = FModuleManager::LoadModuleChecked<FAssetRegistryModule>("AssetRegistry");
			FAssetData Data = ARM.Get().GetAssetByObjectPath(FSoftObjectPath(Path));
			if (!Data.IsValid())
			{
				Obj->SetStringField(TEXT("error"), TEXT("Asset not found"));
				return Obj;
			}
			return AssetDataToJson(Data);
		});
		if (Result->HasField(TEXT("error"))) return Fail(Req, TEXT("engine_error"), Result->GetStringField(TEXT("error")));
		return Ok(Req, Result);
	}), TEXT("Get asset metadata."));

	Reg.Register(TEXT("unreal_import_asset"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		TSharedPtr<FJsonObject> Params = Req.Params;
		TSharedPtr<FJsonObject> Result = FUnrealEngineMCPGameThreadDispatcher::RunJson([Params]()
		{
			TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
			FString Source = Params->GetStringField(TEXT("source_path"));
			FString Dest = Params->HasField(TEXT("destination_path")) ? Params->GetStringField(TEXT("destination_path")) : TEXT("/Game/Imported");
			if (!FPaths::FileExists(Source))
			{
				Obj->SetStringField(TEXT("error"), TEXT("Source file does not exist"));
				return Obj;
			}
			UAssetImportTask* Task = NewObject<UAssetImportTask>();
			Task->Filename = Source;
			Task->DestinationPath = Dest;
			Task->bAutomated = true;
			Task->bSave = true;
			TArray<UAssetImportTask*> Tasks; Tasks.Add(Task);
			FModuleManager::LoadModuleChecked<FAssetToolsModule>("AssetTools").Get().ImportAssetTasks(Tasks);
			TArray<TSharedPtr<FJsonValue>> Imported;
			for (UObject* Asset : Task->GetObjects())
			{
				if (Asset) Imported.Add(MakeShared<FJsonValueString>(Asset->GetPathName()));
			}
			Obj->SetArrayField(TEXT("imported"), Imported);
			Obj->SetNumberField(TEXT("count"), Imported.Num());
			if (Imported.Num() == 0)
			{
				Obj->SetStringField(TEXT("error"), TEXT("Import produced no assets"));
			}
			return Obj;
		});
		if (Result->HasField(TEXT("error"))) return Fail(Req, TEXT("engine_error"), Result->GetStringField(TEXT("error")));
		return Ok(Req, Result);
	}), TEXT("Import an external asset file."));

	Reg.Register(TEXT("unreal_reimport_asset"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		TSharedPtr<FJsonObject> Params = Req.Params;
		TSharedPtr<FJsonObject> Result = FUnrealEngineMCPGameThreadDispatcher::RunJson([Params]()
		{
			TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
			FString Path = Params->GetStringField(TEXT("path"));
			const bool bOk = UEditorAssetLibrary::ReimportAsset(Path);
			Obj->SetBoolField(TEXT("reimported"), bOk);
			Obj->SetStringField(TEXT("path"), Path);
			if (!bOk) Obj->SetStringField(TEXT("error"), TEXT("Reimport failed"));
			return Obj;
		});
		if (Result->HasField(TEXT("error"))) return Fail(Req, TEXT("engine_error"), Result->GetStringField(TEXT("error")));
		return Ok(Req, Result);
	}), TEXT("Reimport an asset."));

	Reg.Register(TEXT("unreal_duplicate_asset"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		TSharedPtr<FJsonObject> Params = Req.Params;
		TSharedPtr<FJsonObject> Result = FUnrealEngineMCPGameThreadDispatcher::RunJson([Params]()
		{
			TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
			FString Source = Params->GetStringField(TEXT("source_path"));
			FString Dest = Params->GetStringField(TEXT("destination_path"));
			UObject* Dup = UEditorAssetLibrary::DuplicateAsset(Source, Dest);
			if (!Dup) { Obj->SetStringField(TEXT("error"), TEXT("Duplicate failed")); return Obj; }
			Obj->SetStringField(TEXT("path"), Dup->GetPathName());
			return Obj;
		});
		if (Result->HasField(TEXT("error"))) return Fail(Req, TEXT("engine_error"), Result->GetStringField(TEXT("error")));
		return Ok(Req, Result);
	}), TEXT("Duplicate an asset."));

	Reg.Register(TEXT("unreal_rename_asset"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		TSharedPtr<FJsonObject> Params = Req.Params;
		TSharedPtr<FJsonObject> Result = FUnrealEngineMCPGameThreadDispatcher::RunJson([Params]()
		{
			TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
			FString Source = Params->GetStringField(TEXT("source_path"));
			FString NewName = Params->GetStringField(TEXT("new_name"));
			FString DestPath = FPackageName::GetLongPackagePath(Source) / NewName;
			const bool bOk = UEditorAssetLibrary::RenameAsset(Source, DestPath);
			Obj->SetBoolField(TEXT("renamed"), bOk);
			Obj->SetStringField(TEXT("path"), DestPath);
			if (!bOk) Obj->SetStringField(TEXT("error"), TEXT("Rename failed"));
			return Obj;
		});
		if (Result->HasField(TEXT("error"))) return Fail(Req, TEXT("engine_error"), Result->GetStringField(TEXT("error")));
		return Ok(Req, Result);
	}), TEXT("Rename an asset."));

	Reg.Register(TEXT("unreal_move_asset"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		TSharedPtr<FJsonObject> Params = Req.Params;
		TSharedPtr<FJsonObject> Result = FUnrealEngineMCPGameThreadDispatcher::RunJson([Params]()
		{
			TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
			FString Source = Params->GetStringField(TEXT("source_path"));
			FString Dest = Params->GetStringField(TEXT("destination_path"));
			const bool bOk = UEditorAssetLibrary::RenameAsset(Source, Dest);
			Obj->SetBoolField(TEXT("moved"), bOk);
			Obj->SetStringField(TEXT("path"), Dest);
			if (!bOk) Obj->SetStringField(TEXT("error"), TEXT("Move failed"));
			return Obj;
		});
		if (Result->HasField(TEXT("error"))) return Fail(Req, TEXT("engine_error"), Result->GetStringField(TEXT("error")));
		return Ok(Req, Result);
	}), TEXT("Move an asset."));

	Reg.Register(TEXT("unreal_delete_asset"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		TSharedPtr<FJsonObject> Params = Req.Params;
		TSharedPtr<FJsonObject> Result = FUnrealEngineMCPGameThreadDispatcher::RunJson([Params]()
		{
			TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
			FString Path = Params->GetStringField(TEXT("path"));
			const bool bOk = UEditorAssetLibrary::DeleteAsset(Path);
			Obj->SetBoolField(TEXT("deleted"), bOk);
			Obj->SetStringField(TEXT("path"), Path);
			if (!bOk) Obj->SetStringField(TEXT("error"), TEXT("Delete failed"));
			return Obj;
		});
		if (Result->HasField(TEXT("error"))) return Fail(Req, TEXT("engine_error"), Result->GetStringField(TEXT("error")));
		return Ok(Req, Result);
	}), TEXT("Delete an asset."));

	Reg.Register(TEXT("unreal_save_asset"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
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
	}), TEXT("Save an asset."));

	Reg.Register(TEXT("unreal_get_asset_references"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		TSharedPtr<FJsonObject> Params = Req.Params;
		TSharedPtr<FJsonObject> Result = FUnrealEngineMCPGameThreadDispatcher::RunJson([Params]()
		{
			TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
			FString Path = Params->GetStringField(TEXT("path"));
			TArray<FString> Refs = UEditorAssetLibrary::FindPackageReferencersForAsset(Path);
			TArray<TSharedPtr<FJsonValue>> Arr;
			for (const FString& R : Refs) Arr.Add(MakeShared<FJsonValueString>(R));
			Obj->SetArrayField(TEXT("references"), Arr);
			return Obj;
		});
		return Ok(Req, Result);
	}), TEXT("Get asset referencers."));

	Reg.Register(TEXT("unreal_get_asset_dependencies"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		TSharedPtr<FJsonObject> Params = Req.Params;
		TSharedPtr<FJsonObject> Result = FUnrealEngineMCPGameThreadDispatcher::RunJson([Params]()
		{
			TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
			FString Path = Params->GetStringField(TEXT("path"));
			FAssetRegistryModule& ARM = FModuleManager::LoadModuleChecked<FAssetRegistryModule>("AssetRegistry");
			TArray<FName> Deps;
			ARM.Get().GetDependencies(FName(*FPackageName::ObjectPathToPackageName(Path)), Deps);
			TArray<TSharedPtr<FJsonValue>> Arr;
			for (const FName& D : Deps) Arr.Add(MakeShared<FJsonValueString>(D.ToString()));
			Obj->SetArrayField(TEXT("dependencies"), Arr);
			return Obj;
		});
		return Ok(Req, Result);
	}), TEXT("Get asset dependencies."));

	Reg.Register(TEXT("unreal_get_asset_thumbnail"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		return Fail(Req, TEXT("unsupported"), TEXT("Thumbnail export is not implemented in this build; use unreal_capture_viewport for visual verification."));
	}), TEXT("Export asset thumbnail path when available."));

	Reg.Register(TEXT("unreal_import_blender_fbx"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		TSharedPtr<FJsonObject> Params = Req.Params;
		if (!Params.IsValid()) Params = MakeShared<FJsonObject>();
		if (!Params->HasField(TEXT("destination_path")))
		{
			Params->SetStringField(TEXT("destination_path"), TEXT("/Game/Imported/Blender"));
		}
		// Reuse import pipeline
		TSharedPtr<FJsonObject> Result = FUnrealEngineMCPGameThreadDispatcher::RunJson([Params]()
		{
			TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
			FString Source = Params->GetStringField(TEXT("source_path"));
			FString Dest = Params->GetStringField(TEXT("destination_path"));
			if (!FPaths::FileExists(Source))
			{
				Obj->SetStringField(TEXT("error"), TEXT("Source FBX does not exist"));
				return Obj;
			}
			if (!Source.EndsWith(TEXT(".fbx"), ESearchCase::IgnoreCase))
			{
				Obj->SetStringField(TEXT("warning"), TEXT("File does not end with .fbx"));
			}
			UAssetImportTask* Task = NewObject<UAssetImportTask>();
			Task->Filename = Source;
			Task->DestinationPath = Dest;
			Task->bAutomated = true;
			Task->bSave = true;
			TArray<UAssetImportTask*> Tasks; Tasks.Add(Task);
			FModuleManager::LoadModuleChecked<FAssetToolsModule>("AssetTools").Get().ImportAssetTasks(Tasks);
			TArray<TSharedPtr<FJsonValue>> Imported;
			for (UObject* Asset : Task->GetObjects())
			{
				if (Asset) Imported.Add(MakeShared<FJsonValueString>(Asset->GetPathName()));
			}
			Obj->SetArrayField(TEXT("imported"), Imported);
			Obj->SetStringField(TEXT("units_note"), TEXT("Unreal uses centimeters. Validate Blender FBX export scale."));
			Obj->SetStringField(TEXT("axis_note"), TEXT("Unreal is left-handed Z-up; Blender is right-handed Z-up. Check forward/up axes on export."));
			if (Imported.Num() == 0) Obj->SetStringField(TEXT("error"), TEXT("Import produced no assets"));
			return Obj;
		});
		if (Result->HasField(TEXT("error"))) return Fail(Req, TEXT("engine_error"), Result->GetStringField(TEXT("error")));
		return Ok(Req, Result);
	}), TEXT("Import an FBX exported from Blender with validation."));

	Reg.Register(TEXT("unreal_validate_blender_import"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
		TArray<TSharedPtr<FJsonValue>> Checks;
		auto Add = [&](const FString& Name, const FString& Status, const FString& Detail)
		{
			TSharedPtr<FJsonObject> C = MakeShared<FJsonObject>();
			C->SetStringField(TEXT("check"), Name);
			C->SetStringField(TEXT("status"), Status);
			C->SetStringField(TEXT("detail"), Detail);
			Checks.Add(MakeShared<FJsonValueObject>(C));
		};
		Add(TEXT("units"), TEXT("info"), TEXT("Unreal world units are centimeters."));
		Add(TEXT("axes"), TEXT("info"), TEXT("Prefer Blender FBX forward -Y / up Z for Unreal."));
		Add(TEXT("scale"), TEXT("info"), TEXT("Apply scale in Blender before export; expect ~1.0 object scale after import."));
		Add(TEXT("materials"), TEXT("info"), TEXT("Complex Blender materials will not auto-convert; assign Unreal materials after import."));
		Result->SetArrayField(TEXT("checks"), Checks);
		return Ok(Req, Result);
	}), TEXT("Validate Blender export conventions for Unreal."));

	Reg.Register(TEXT("unreal_reimport_blender_asset"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		TSharedPtr<FJsonObject> Params = Req.Params;
		TSharedPtr<FJsonObject> Result = FUnrealEngineMCPGameThreadDispatcher::RunJson([Params]()
		{
			TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
			FString Path = Params->GetStringField(TEXT("path"));
			const bool bOk = UEditorAssetLibrary::ReimportAsset(Path);
			Obj->SetBoolField(TEXT("reimported"), bOk);
			Obj->SetStringField(TEXT("path"), Path);
			if (!bOk) Obj->SetStringField(TEXT("error"), TEXT("Reimport failed"));
			return Obj;
		});
		if (Result->HasField(TEXT("error"))) return Fail(Req, TEXT("engine_error"), Result->GetStringField(TEXT("error")));
		return Ok(Req, Result);
	}), TEXT("Reimport a previously imported Blender asset."));

	Reg.Register(TEXT("unreal_create_folder"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		TSharedPtr<FJsonObject> Params = Req.Params;
		TSharedPtr<FJsonObject> Result = FUnrealEngineMCPGameThreadDispatcher::RunJson([Params]()
		{
			TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
			FString Path = Params->GetStringField(TEXT("path"));
			const bool bOk = UEditorAssetLibrary::MakeDirectory(Path);
			Obj->SetBoolField(TEXT("created"), bOk);
			Obj->SetStringField(TEXT("path"), Path);
			if (!bOk && !UEditorAssetLibrary::DoesDirectoryExist(Path))
			{
				Obj->SetStringField(TEXT("error"), TEXT("Failed to create folder"));
			}
			return Obj;
		});
		if (Result->HasField(TEXT("error"))) return Fail(Req, TEXT("engine_error"), Result->GetStringField(TEXT("error")));
		return Ok(Req, Result);
	}), TEXT("Create a content browser folder."));
}
