#include "Tools/RenderingTools.h"
#include "Core/ToolRegistry.h"
#include "Core/ResultSerializer.h"
#include "Core/GameThreadDispatcher.h"
#include "UnrealEngineMCPSettings.h"
#include "Editor.h"
#include "LevelEditorViewport.h"
#include "EditorViewportClient.h"
#include "IImageWrapper.h"
#include "IImageWrapperModule.h"
#include "Modules/ModuleManager.h"
#include "Misc/FileHelper.h"
#include "HAL/PlatformFileManager.h"
#include "HighResScreenshot.h"
#include "UnrealClient.h"

namespace
{
	FUnrealEngineMCPResponse Ok(const FUnrealEngineMCPRequest& R, TSharedPtr<FJsonObject> O) { return FUnrealEngineMCPResultSerializer::Ok(R.Id, O); }
	FUnrealEngineMCPResponse Fail(const FUnrealEngineMCPRequest& R, const FString& C, const FString& M) { return FUnrealEngineMCPResultSerializer::Fail(R.Id, C, M); }

	FEditorViewportClient* GetActiveViewportClient()
	{
		if (!GEditor) return nullptr;
		return static_cast<FEditorViewportClient*>(GEditor->GetActiveViewport() ? GEditor->GetActiveViewport()->GetClient() : nullptr);
	}
}

void FUnrealEngineMCPRenderingTools::Register()
{
	auto& Reg = FUnrealEngineMCPToolRegistry::Get();

	Reg.Register(TEXT("unreal_capture_viewport"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		TSharedPtr<FJsonObject> Params = Req.Params;
		auto Result = FUnrealEngineMCPGameThreadDispatcher::RunJson([Params]()
		{
			TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
			FViewport* Viewport = GEditor ? GEditor->GetActiveViewport() : nullptr;
			if (!Viewport) { Obj->SetStringField(TEXT("error"), TEXT("No active viewport")); return Obj; }

			const UUnrealEngineMCPSettings* Settings = GetDefault<UUnrealEngineMCPSettings>();
			FString Dir = Settings && !Settings->ScreenshotDirectory.IsEmpty()
				? Settings->ScreenshotDirectory
				: FPaths::ProjectSavedDir() / TEXT("Screenshots/UnrealEngineMCP");
			IFileManager::Get().MakeDirectory(*Dir, true);
			FString Filename = Params.IsValid() && Params->HasField(TEXT("filename"))
				? Params->GetStringField(TEXT("filename"))
				: FString::Printf(TEXT("viewport_%s.png"), *FDateTime::Now().ToString(TEXT("%Y%m%d_%H%M%S")));
			FString FullPath = FPaths::ConvertRelativePathToFull(Dir / Filename);

			FScreenshotRequest::RequestScreenshot(FullPath, false, false);
			Obj->SetStringField(TEXT("path"), FullPath);
			Obj->SetBoolField(TEXT("requested"), true);
			Obj->SetStringField(TEXT("note"), TEXT("Screenshot requested asynchronously; file appears after next viewport draw."));
			return Obj;
		});
		if (Result->HasField(TEXT("error"))) return Fail(Req, TEXT("engine_error"), Result->GetStringField(TEXT("error")));
		return Ok(Req, Result);
	}), TEXT("Capture the active editor viewport."));

	Reg.Register(TEXT("unreal_capture_screenshot"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		// Same path for now; higher quality can use HighResShot console later.
		TSharedPtr<FJsonObject> Params = Req.Params;
		auto Result = FUnrealEngineMCPGameThreadDispatcher::RunJson([Params]()
		{
			TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
			const UUnrealEngineMCPSettings* Settings = GetDefault<UUnrealEngineMCPSettings>();
			FString Dir = Settings && !Settings->ScreenshotDirectory.IsEmpty()
				? Settings->ScreenshotDirectory
				: FPaths::ProjectSavedDir() / TEXT("Screenshots/UnrealEngineMCP");
			IFileManager::Get().MakeDirectory(*Dir, true);
			FString Filename = Params.IsValid() && Params->HasField(TEXT("filename"))
				? Params->GetStringField(TEXT("filename"))
				: FString::Printf(TEXT("screenshot_%s.png"), *FDateTime::Now().ToString(TEXT("%Y%m%d_%H%M%S")));
			FString FullPath = FPaths::ConvertRelativePathToFull(Dir / Filename);
			FScreenshotRequest::RequestScreenshot(FullPath, false, false);
			Obj->SetStringField(TEXT("path"), FullPath);
			Obj->SetBoolField(TEXT("requested"), true);
			return Obj;
		});
		return Ok(Req, Result);
	}), TEXT("Capture a high-quality screenshot."));

	Reg.Register(TEXT("unreal_get_viewport_info"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		auto Result = FUnrealEngineMCPGameThreadDispatcher::RunJson([]()
		{
			TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
			FEditorViewportClient* Client = GetActiveViewportClient();
			if (!Client) { Obj->SetStringField(TEXT("error"), TEXT("No active viewport client")); return Obj; }
			Obj->SetObjectField(TEXT("location"), FUnrealEngineMCPResultSerializer::Vector(Client->GetViewLocation()));
			Obj->SetObjectField(TEXT("rotation"), FUnrealEngineMCPResultSerializer::Rotator(Client->GetViewRotation()));
			Obj->SetNumberField(TEXT("fov"), Client->ViewFOV);
			return Obj;
		});
		if (Result->HasField(TEXT("error"))) return Fail(Req, TEXT("engine_error"), Result->GetStringField(TEXT("error")));
		return Ok(Req, Result);
	}), TEXT("Get viewport camera info."));

	Reg.Register(TEXT("unreal_set_viewport_location"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		TSharedPtr<FJsonObject> Params = Req.Params;
		auto Result = FUnrealEngineMCPGameThreadDispatcher::RunJson([Params]()
		{
			TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
			FEditorViewportClient* Client = GetActiveViewportClient();
			if (!Client) { Obj->SetStringField(TEXT("error"), TEXT("No active viewport client")); return Obj; }
			FVector Loc = Client->GetViewLocation();
			if (Params->HasField(TEXT("x"))) Loc.X = Params->GetNumberField(TEXT("x"));
			if (Params->HasField(TEXT("y"))) Loc.Y = Params->GetNumberField(TEXT("y"));
			if (Params->HasField(TEXT("z"))) Loc.Z = Params->GetNumberField(TEXT("z"));
			FUnrealEngineMCPResultSerializer::TryGetVector(Params, TEXT("location"), Loc);
			Client->SetViewLocation(Loc);
			Obj->SetObjectField(TEXT("location"), FUnrealEngineMCPResultSerializer::Vector(Loc));
			return Obj;
		});
		if (Result->HasField(TEXT("error"))) return Fail(Req, TEXT("engine_error"), Result->GetStringField(TEXT("error")));
		return Ok(Req, Result);
	}), TEXT("Set viewport camera location."));

	Reg.Register(TEXT("unreal_set_viewport_rotation"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		TSharedPtr<FJsonObject> Params = Req.Params;
		auto Result = FUnrealEngineMCPGameThreadDispatcher::RunJson([Params]()
		{
			TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
			FEditorViewportClient* Client = GetActiveViewportClient();
			if (!Client) { Obj->SetStringField(TEXT("error"), TEXT("No active viewport client")); return Obj; }
			FRotator Rot = Client->GetViewRotation();
			if (Params->HasField(TEXT("pitch"))) Rot.Pitch = Params->GetNumberField(TEXT("pitch"));
			if (Params->HasField(TEXT("yaw"))) Rot.Yaw = Params->GetNumberField(TEXT("yaw"));
			if (Params->HasField(TEXT("roll"))) Rot.Roll = Params->GetNumberField(TEXT("roll"));
			FUnrealEngineMCPResultSerializer::TryGetRotator(Params, TEXT("rotation"), Rot);
			Client->SetViewRotation(Rot);
			Obj->SetObjectField(TEXT("rotation"), FUnrealEngineMCPResultSerializer::Rotator(Rot));
			return Obj;
		});
		if (Result->HasField(TEXT("error"))) return Fail(Req, TEXT("engine_error"), Result->GetStringField(TEXT("error")));
		return Ok(Req, Result);
	}), TEXT("Set viewport camera rotation."));

	Reg.Register(TEXT("unreal_set_viewport_camera"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		TSharedPtr<FJsonObject> Params = Req.Params;
		auto Result = FUnrealEngineMCPGameThreadDispatcher::RunJson([Params]()
		{
			TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
			FEditorViewportClient* Client = GetActiveViewportClient();
			if (!Client) { Obj->SetStringField(TEXT("error"), TEXT("No active viewport client")); return Obj; }
			FVector Loc = Client->GetViewLocation();
			FRotator Rot = Client->GetViewRotation();
			FUnrealEngineMCPResultSerializer::TryGetVector(Params, TEXT("location"), Loc);
			FUnrealEngineMCPResultSerializer::TryGetRotator(Params, TEXT("rotation"), Rot);
			Client->SetViewLocation(Loc);
			Client->SetViewRotation(Rot);
			Obj->SetObjectField(TEXT("location"), FUnrealEngineMCPResultSerializer::Vector(Loc));
			Obj->SetObjectField(TEXT("rotation"), FUnrealEngineMCPResultSerializer::Rotator(Rot));
			return Obj;
		});
		if (Result->HasField(TEXT("error"))) return Fail(Req, TEXT("engine_error"), Result->GetStringField(TEXT("error")));
		return Ok(Req, Result);
	}), TEXT("Set viewport camera actor/view."));

	Reg.Register(TEXT("unreal_set_viewport_mode"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		return Fail(Req, TEXT("unsupported"), TEXT("Viewport mode switching is not implemented in this build."));
	}), TEXT("Set viewport mode/show flags where supported."));

	Reg.Register(TEXT("unreal_render_image"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		return Fail(Req, TEXT("unsupported"), TEXT("Offline render_image is not implemented; use unreal_capture_screenshot."));
	}), TEXT("Render an image from the current view."));

	Reg.Register(TEXT("unreal_get_render_settings"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		auto Result = FUnrealEngineMCPGameThreadDispatcher::RunJson([]()
		{
			TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
			Obj->SetStringField(TEXT("note"), TEXT("Subset only"));
			Obj->SetStringField(TEXT("rhi"), GDynamicRHI ? GDynamicRHI->GetName() : TEXT("unknown"));
			return Obj;
		});
		return Ok(Req, Result);
	}), TEXT("Get project render settings."));

	Reg.Register(TEXT("unreal_set_render_settings"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		return Fail(Req, TEXT("unsupported"), TEXT("Render settings mutation requires validated setting keys; not enabled yet."));
	}), TEXT("Set supported render settings."));
}
