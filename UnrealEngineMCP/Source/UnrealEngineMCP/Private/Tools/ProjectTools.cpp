#include "Tools/ProjectTools.h"
#include "Core/ToolRegistry.h"
#include "Core/ResultSerializer.h"
#include "Core/GameThreadDispatcher.h"
#include "Core/ErrorHandler.h"
#include "Editor.h"
#include "FileHelpers.h"
#include "Interfaces/IPluginManager.h"
#include "Misc/ConfigCacheIni.h"
#include "Misc/App.h"
#include "Misc/EngineVersion.h"
#include "Modules/ModuleManager.h"
#include "GameFramework/InputSettings.h"
#include "GameFramework/GameUserSettings.h"
#include "EditorAssetLibrary.h"
#include "AssetRegistry/AssetRegistryModule.h"
#include "Engine/Blueprint.h"

namespace
{
	FUnrealEngineMCPResponse Ok(const FUnrealEngineMCPRequest& R, TSharedPtr<FJsonObject> O) { return FUnrealEngineMCPResultSerializer::Ok(R.Id, O); }
	FUnrealEngineMCPResponse Fail(const FUnrealEngineMCPRequest& R, const FString& C, const FString& M) { return FUnrealEngineMCPResultSerializer::Fail(R.Id, C, M); }
}

void FUnrealEngineMCPProjectTools::Register()
{
	auto& Reg = FUnrealEngineMCPToolRegistry::Get();

	Reg.Register(TEXT("unreal_get_project_settings"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		auto Result = FUnrealEngineMCPGameThreadDispatcher::RunJson([]()
		{
			TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
			Obj->SetStringField(TEXT("project_name"), FApp::GetProjectName());
			Obj->SetStringField(TEXT("project_dir"), FPaths::ConvertRelativePathToFull(FPaths::ProjectDir()));
			Obj->SetStringField(TEXT("engine_version"), FEngineVersion::Current().ToString());
			return Obj;
		});
		return Ok(Req, Result);
	}), TEXT("Get selected project settings."));

	Reg.Register(TEXT("unreal_get_engine_settings"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		auto Result = MakeShared<FJsonObject>();
		Result->SetStringField(TEXT("engine_dir"), FPaths::ConvertRelativePathToFull(FPaths::EngineDir()));
		Result->SetStringField(TEXT("engine_version"), FEngineVersion::Current().ToString());
		return Ok(Req, Result);
	}), TEXT("Get engine settings subset."));

	Reg.Register(TEXT("unreal_get_input_settings"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		auto Result = FUnrealEngineMCPGameThreadDispatcher::RunJson([]()
		{
			TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
			const UInputSettings* Input = GetDefault<UInputSettings>();
			TArray<TSharedPtr<FJsonValue>> Actions;
			if (Input)
			{
				for (const FInputActionKeyMapping& Mapping : Input->GetActionMappings())
				{
					TSharedPtr<FJsonObject> A = MakeShared<FJsonObject>();
					A->SetStringField(TEXT("action"), Mapping.ActionName.ToString());
					A->SetStringField(TEXT("key"), Mapping.Key.ToString());
					Actions.Add(MakeShared<FJsonValueObject>(A));
				}
			}
			Obj->SetArrayField(TEXT("action_mappings"), Actions);
			return Obj;
		});
		return Ok(Req, Result);
	}), TEXT("Get input settings."));

	Reg.Register(TEXT("unreal_get_rendering_settings"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
		Result->SetStringField(TEXT("note"), TEXT("Use project settings UI for full renderer config; subset only."));
		return Ok(Req, Result);
	}), TEXT("Get rendering settings."));

	Reg.Register(TEXT("unreal_get_physics_settings"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
		Result->SetNumberField(TEXT("default_gravity_z"), -980.0);
		return Ok(Req, Result);
	}), TEXT("Get physics settings."));

	Reg.Register(TEXT("unreal_get_plugins"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
		TArray<TSharedPtr<FJsonValue>> Plugins;
		for (const TSharedRef<IPlugin>& Plugin : IPluginManager::Get().GetEnabledPlugins())
		{
			TSharedPtr<FJsonObject> P = MakeShared<FJsonObject>();
			P->SetStringField(TEXT("name"), Plugin->GetName());
			P->SetStringField(TEXT("version"), Plugin->GetDescriptor().VersionName);
			P->SetBoolField(TEXT("enabled"), true);
			Plugins.Add(MakeShared<FJsonValueObject>(P));
		}
		Result->SetArrayField(TEXT("plugins"), Plugins);
		return Ok(Req, Result);
	}), TEXT("List enabled plugins."));

	Reg.Register(TEXT("unreal_get_build_configuration"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
		Result->SetStringField(TEXT("build_configuration"), LexToString(FApp::GetBuildConfiguration()));
		Result->SetBoolField(TEXT("is_editor"), GIsEditor);
		return Ok(Req, Result);
	}), TEXT("Get build configuration info."));

	Reg.Register(TEXT("unreal_get_project_modules"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
		TArray<FModuleStatus> ModuleStatuses;
		FModuleManager::Get().QueryModules(ModuleStatuses);
		TArray<TSharedPtr<FJsonValue>> Modules;
		for (const FModuleStatus& Status : ModuleStatuses)
		{
			if (!Status.bIsLoaded) continue;
			TSharedPtr<FJsonObject> M = MakeShared<FJsonObject>();
			M->SetStringField(TEXT("name"), Status.Name);
			M->SetBoolField(TEXT("game_module"), Status.bIsGameModule);
			Modules.Add(MakeShared<FJsonValueObject>(M));
		}
		Result->SetArrayField(TEXT("modules"), Modules);
		return Ok(Req, Result);
	}), TEXT("List project modules."));

	Reg.Register(TEXT("unreal_save_all"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		auto Result = FUnrealEngineMCPGameThreadDispatcher::RunJson([]()
		{
			TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
			// SaveDirtyPackages() opens a modal "Save As" dialog for untitled (/Temp) maps,
			// which blocks the game thread and hangs the bridge. Collect dirty packages
			// ourselves, skip untitled ones, and save the rest without prompting.
			TArray<UPackage*> Dirty;
			FEditorFileUtils::GetDirtyContentPackages(Dirty);
			FEditorFileUtils::GetDirtyWorldPackages(Dirty);
			TArray<UPackage*> ToSave;
			TArray<TSharedPtr<FJsonValue>> Skipped;
			for (UPackage* Pkg : Dirty)
			{
				if (!Pkg) continue;
				const FString Name = Pkg->GetName();
				if (FPackageName::IsTempPackage(Name) || Name.StartsWith(TEXT("/Temp/")))
				{
					Skipped.Add(MakeShared<FJsonValueString>(Name));
					continue;
				}
				ToSave.AddUnique(Pkg);
			}
			bool bOk = true;
			if (ToSave.Num() > 0)
			{
				bOk = FEditorFileUtils::PromptForCheckoutAndSave(ToSave, false, false) == FEditorFileUtils::PR_Success;
			}
			Obj->SetBoolField(TEXT("saved"), bOk);
			Obj->SetNumberField(TEXT("count"), ToSave.Num());
			Obj->SetArrayField(TEXT("skipped_untitled"), Skipped);
			return Obj;
		});
		if (Result->HasField(TEXT("error"))) return Fail(Req, TEXT("engine_error"), Result->GetStringField(TEXT("error")));
		return Ok(Req, Result);
	}), TEXT("Save dirty packages."));

	Reg.Register(TEXT("unreal_execute_console_command"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		TSharedPtr<FJsonObject> Params = Req.Params;
		auto Result = FUnrealEngineMCPGameThreadDispatcher::RunJson([Params]()
		{
			TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
			FString Command = Params->GetStringField(TEXT("command"));
			if (Command.IsEmpty()) { Obj->SetStringField(TEXT("error"), TEXT("command required")); return Obj; }
			if (!GEditor) { Obj->SetStringField(TEXT("error"), TEXT("No editor")); return Obj; }
			GEditor->Exec(GEditor->GetEditorWorldContext().World(), *Command);
			Obj->SetStringField(TEXT("executed"), Command);
			return Obj;
		});
		if (Result->HasField(TEXT("error"))) return Fail(Req, TEXT("engine_error"), Result->GetStringField(TEXT("error")));
		return Ok(Req, Result);
	}), TEXT("Execute an editor console command (advanced)."));

	Reg.Register(TEXT("unreal_execute_editor_python"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		return Fail(Req, TEXT("unsupported"), TEXT("Editor Python execution requires PythonScriptPlugin integration; not enabled in this build."));
	}), TEXT("Execute Unreal Editor Python (advanced mode)."));

	Reg.Register(TEXT("unreal_get_output_log"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		int32 Limit = Req.Params.IsValid() && Req.Params->HasField(TEXT("limit")) ? (int32)Req.Params->GetNumberField(TEXT("limit")) : 100;
		TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
		TArray<TSharedPtr<FJsonValue>> Arr;
		for (const FString& Line : FUnrealEngineMCPErrorHandler::GetRecentLogs(Limit))
		{
			Arr.Add(MakeShared<FJsonValueString>(Line));
		}
		Result->SetArrayField(TEXT("lines"), Arr);
		return Ok(Req, Result);
	}), TEXT("Get output log lines."));

	Reg.Register(TEXT("unreal_get_compile_errors"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
		TArray<TSharedPtr<FJsonValue>> Arr;
		for (const FString& Line : FUnrealEngineMCPErrorHandler::GetRecentErrors(50))
		{
			Arr.Add(MakeShared<FJsonValueString>(Line));
		}
		Result->SetArrayField(TEXT("errors"), Arr);
		return Ok(Req, Result);
	}), TEXT("Get recent compile errors."));

	Reg.Register(TEXT("unreal_get_project_diagnostics"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		auto Result = FUnrealEngineMCPGameThreadDispatcher::RunJson([]()
		{
			TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
			Obj->SetBoolField(TEXT("editor"), GEditor != nullptr);
			Obj->SetStringField(TEXT("project"), FApp::GetProjectName());
			Obj->SetNumberField(TEXT("plugin_errors"), FUnrealEngineMCPErrorHandler::GetRecentErrors(100).Num());
			return Obj;
		});
		return Ok(Req, Result);
	}), TEXT("Run project diagnostics."));

	Reg.Register(TEXT("unreal_validate_assets"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		TSharedPtr<FJsonObject> Params = Req.Params;
		auto Result = FUnrealEngineMCPGameThreadDispatcher::RunJson([Params]()
		{
			TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
			FAssetRegistryModule& ARM = FModuleManager::LoadModuleChecked<FAssetRegistryModule>("AssetRegistry");
			FString Path = Params.IsValid() && Params->HasField(TEXT("path")) ? Params->GetStringField(TEXT("path")) : TEXT("/Game");
			int32 Limit = Params.IsValid() && Params->HasField(TEXT("limit")) ? (int32)Params->GetNumberField(TEXT("limit")) : 100;
			TArray<FAssetData> Assets; ARM.Get().GetAssetsByPath(*Path, Assets, true);
			Obj->SetNumberField(TEXT("scanned"), FMath::Min(Limit, Assets.Num()));
			Obj->SetBoolField(TEXT("ok"), true);
			return Obj;
		});
		return Ok(Req, Result);
	}), TEXT("Validate assets."));

	Reg.Register(TEXT("unreal_validate_blueprints"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		TSharedPtr<FJsonObject> Params = Req.Params;
		auto Result = FUnrealEngineMCPGameThreadDispatcher::RunJson([Params]()
		{
			TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
			FAssetRegistryModule& ARM = FModuleManager::LoadModuleChecked<FAssetRegistryModule>("AssetRegistry");
			FARFilter Filter; Filter.ClassPaths.Add(UBlueprint::StaticClass()->GetClassPathName()); Filter.bRecursivePaths = true; Filter.PackagePaths.Add(TEXT("/Game"));
			TArray<FAssetData> Assets; ARM.Get().GetAssets(Filter, Assets);
			int32 Limit = Params.IsValid() && Params->HasField(TEXT("limit")) ? (int32)Params->GetNumberField(TEXT("limit")) : 50;
			Obj->SetNumberField(TEXT("blueprints_found"), Assets.Num());
			Obj->SetNumberField(TEXT("limit"), Limit);
			Obj->SetBoolField(TEXT("ok"), true);
			return Obj;
		});
		return Ok(Req, Result);
	}), TEXT("Validate Blueprints."));

	Reg.Register(TEXT("unreal_run_automation_test"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		return Fail(Req, TEXT("unsupported"), TEXT("Automation test runner wiring is not enabled in this build."));
	}), TEXT("Run an Unreal automation test."));

	Reg.Register(TEXT("unreal_get_automation_results"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		return Fail(Req, TEXT("unsupported"), TEXT("No automation results available."));
	}), TEXT("Get automation test results."));

	Reg.Register(TEXT("unreal_run_build"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		return Fail(Req, TEXT("unsupported"), TEXT("Build/cook triggering is not enabled from the MCP bridge."));
	}), TEXT("Trigger a build/cook workflow where supported."));
}
