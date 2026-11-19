#include "Tools/SystemTools.h"
#include "Core/ToolRegistry.h"
#include "Core/ResultSerializer.h"
#include "Core/GameThreadDispatcher.h"
#include "Core/ErrorHandler.h"
#include "Bridge/TCPServer.h"
#include "UnrealEngineMCPModule.h"
#include "UnrealEngineMCPSettings.h"
#include "Editor.h"
#include "Engine/World.h"
#include "Engine/Selection.h"
#include "Misc/EngineVersion.h"
#include "Interfaces/IPluginManager.h"
#include "GameFramework/Actor.h"

namespace
{
	FUnrealEngineMCPResponse MakeOk(const FUnrealEngineMCPRequest& Req, TSharedPtr<FJsonObject> Result)
	{
		return FUnrealEngineMCPResultSerializer::Ok(Req.Id, Result);
	}

	FUnrealEngineMCPResponse MakeFail(const FUnrealEngineMCPRequest& Req, const FString& Code, const FString& Message)
	{
		return FUnrealEngineMCPResultSerializer::Fail(Req.Id, Code, Message);
	}
}

void FUnrealEngineMCPSystemTools::Register()
{
	auto& Reg = FUnrealEngineMCPToolRegistry::Get();

	Reg.Register(TEXT("unreal_ping"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
		Result->SetStringField(TEXT("message"), TEXT("pong"));
		Result->SetBoolField(TEXT("editor"), GEditor != nullptr);
		return MakeOk(Req, Result);
	}), TEXT("Ping the Unreal Editor bridge."));

	Reg.Register(TEXT("unreal_get_status"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		TSharedPtr<FJsonObject> Result = FUnrealEngineMCPGameThreadDispatcher::RunJson([]()
		{
			TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
			const UUnrealEngineMCPSettings* Settings = GetDefault<UUnrealEngineMCPSettings>();
			FUnrealEngineMCPModule& Module = FUnrealEngineMCPModule::Get();
			TSharedPtr<FUnrealEngineMCPBridgeServer> Bridge = Module.GetBridge();
			Obj->SetBoolField(TEXT("bridge_running"), Bridge.IsValid() && Bridge->IsRunning());
			Obj->SetStringField(TEXT("host"), Settings ? Settings->BindAddress : TEXT("127.0.0.1"));
			Obj->SetNumberField(TEXT("port"), Settings ? Settings->Port : 55557);
			Obj->SetBoolField(TEXT("editor_valid"), GEditor != nullptr);
			Obj->SetBoolField(TEXT("pie"), GEditor && GEditor->PlayWorld != nullptr);
			return Obj;
		});
		return MakeOk(Req, Result);
	}), TEXT("Get bridge and editor connection status."));

	Reg.Register(TEXT("unreal_get_version"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
		Result->SetStringField(TEXT("engine"), FEngineVersion::Current().ToString());
		TSharedPtr<IPlugin> Plugin = IPluginManager::Get().FindPlugin(TEXT("UnrealEngineMCP"));
		Result->SetStringField(TEXT("plugin"), Plugin.IsValid() ? Plugin->GetDescriptor().VersionName : TEXT("0.1.0"));
		Result->SetStringField(TEXT("protocol"), TEXT("1.0"));
		return MakeOk(Req, Result);
	}), TEXT("Get Unreal Engine and plugin version info."));

	Reg.Register(TEXT("unreal_get_project_info"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		TSharedPtr<FJsonObject> Result = FUnrealEngineMCPGameThreadDispatcher::RunJson([]()
		{
			TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
			Obj->SetStringField(TEXT("project_name"), FApp::GetProjectName());
			Obj->SetStringField(TEXT("project_dir"), FPaths::ConvertRelativePathToFull(FPaths::ProjectDir()));
			Obj->SetStringField(TEXT("content_dir"), FPaths::ConvertRelativePathToFull(FPaths::ProjectContentDir()));
			Obj->SetStringField(TEXT("engine_dir"), FPaths::ConvertRelativePathToFull(FPaths::EngineDir()));
			return Obj;
		});
		return MakeOk(Req, Result);
	}), TEXT("Get current Unreal project information."));

	Reg.Register(TEXT("unreal_get_editor_status"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		TSharedPtr<FJsonObject> Result = FUnrealEngineMCPGameThreadDispatcher::RunJson([]()
		{
			TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
			Obj->SetBoolField(TEXT("has_editor"), GEditor != nullptr);
			Obj->SetBoolField(TEXT("is_playing"), GEditor && GEditor->PlayWorld != nullptr);
			int32 Selected = 0;
			if (GEditor)
			{
				Selected = GEditor->GetSelectedActors()->Num();
			}
			Obj->SetNumberField(TEXT("selected_actors"), Selected);
			return Obj;
		});
		return MakeOk(Req, Result);
	}), TEXT("Get editor play/pie and selection status."));

	Reg.Register(TEXT("unreal_get_current_level"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		TSharedPtr<FJsonObject> Result = FUnrealEngineMCPGameThreadDispatcher::RunJson([]()
		{
			TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
			UWorld* World = GEditor ? GEditor->GetEditorWorldContext().World() : nullptr;
			if (!World)
			{
				Obj->SetBoolField(TEXT("ok"), false);
				Obj->SetStringField(TEXT("error"), TEXT("No editor world"));
				return Obj;
			}
			Obj->SetStringField(TEXT("world"), World->GetMapName());
			if (ULevel* Level = World->PersistentLevel)
			{
				Obj->SetStringField(TEXT("level_package"), Level->GetOutermost()->GetName());
				Obj->SetStringField(TEXT("level_path"), Level->GetPathName());
			}
			return Obj;
		});
		if (Result->HasField(TEXT("error")))
		{
			return MakeFail(Req, TEXT("engine_error"), Result->GetStringField(TEXT("error")));
		}
		return MakeOk(Req, Result);
	}), TEXT("Get the currently loaded level."));

	Reg.Register(TEXT("unreal_get_active_world"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		TSharedPtr<FJsonObject> Result = FUnrealEngineMCPGameThreadDispatcher::RunJson([]()
		{
			TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
			UWorld* World = GEditor ? GEditor->GetEditorWorldContext().World() : nullptr;
			if (!World)
			{
				Obj->SetStringField(TEXT("error"), TEXT("No active world"));
				return Obj;
			}
			Obj->SetStringField(TEXT("name"), World->GetName());
			Obj->SetStringField(TEXT("path"), World->GetPathName());
			Obj->SetNumberField(TEXT("actor_count"), World->GetActorCount());
			return Obj;
		});
		if (Result->HasField(TEXT("error")))
		{
			return MakeFail(Req, TEXT("engine_error"), Result->GetStringField(TEXT("error")));
		}
		return MakeOk(Req, Result);
	}), TEXT("Get the active editor world."));

	Reg.Register(TEXT("unreal_get_selected_actors"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		TSharedPtr<FJsonObject> Result = FUnrealEngineMCPGameThreadDispatcher::RunJson([]()
		{
			TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
			TArray<TSharedPtr<FJsonValue>> Actors;
			if (GEditor)
			{
				for (FSelectionIterator It(GEditor->GetSelectedActorIterator()); It; ++It)
				{
					if (AActor* Actor = Cast<AActor>(*It))
					{
						TSharedPtr<FJsonObject> A = MakeShared<FJsonObject>();
						A->SetStringField(TEXT("name"), Actor->GetName());
						A->SetStringField(TEXT("label"), Actor->GetActorLabel());
						A->SetStringField(TEXT("class"), Actor->GetClass()->GetName());
						A->SetObjectField(TEXT("transform"), FUnrealEngineMCPResultSerializer::Transform(Actor->GetActorTransform()));
						Actors.Add(MakeShared<FJsonValueObject>(A));
					}
				}
			}
			Obj->SetArrayField(TEXT("actors"), Actors);
			return Obj;
		});
		return MakeOk(Req, Result);
	}), TEXT("List currently selected actors."));

	Reg.Register(TEXT("unreal_list_tools"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
		Result->SetArrayField(TEXT("tools"), FUnrealEngineMCPToolRegistry::Get().ListTools());
		return MakeOk(Req, Result);
	}), TEXT("List tools registered in the Unreal plugin."));

	Reg.Register(TEXT("unreal_get_logs"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		int32 Limit = Req.Params.IsValid() ? static_cast<int32>(Req.Params->GetNumberField(TEXT("limit"))) : 100;
		if (Limit <= 0) Limit = 100;
		TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
		TArray<TSharedPtr<FJsonValue>> Arr;
		for (const FString& Line : FUnrealEngineMCPErrorHandler::GetRecentLogs(Limit))
		{
			Arr.Add(MakeShared<FJsonValueString>(Line));
		}
		Result->SetArrayField(TEXT("logs"), Arr);
		return MakeOk(Req, Result);
	}), TEXT("Get recent UnrealEngineMCP plugin logs."));

	Reg.Register(TEXT("unreal_get_errors"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		int32 Limit = Req.Params.IsValid() ? static_cast<int32>(Req.Params->GetNumberField(TEXT("limit"))) : 50;
		if (Limit <= 0) Limit = 50;
		TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
		TArray<TSharedPtr<FJsonValue>> Arr;
		for (const FString& Line : FUnrealEngineMCPErrorHandler::GetRecentErrors(Limit))
		{
			Arr.Add(MakeShared<FJsonValueString>(Line));
		}
		Result->SetArrayField(TEXT("errors"), Arr);
		return MakeOk(Req, Result);
	}), TEXT("Get recent engine/plugin errors."));
}
