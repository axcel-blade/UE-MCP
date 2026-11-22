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
#include "ImageUtils.h"
#include "Misc/Base64.h"

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
			FEditorViewportClient* Client = Viewport ? static_cast<FEditorViewportClient*>(Viewport->GetClient()) : nullptr;
			// After a level load no viewport may have focus; fall back to the level
			// viewport the user is most likely looking at.
			if (!Viewport && GEditor)
			{
				FLevelEditorViewportClient* LevelClient = GCurrentLevelEditingViewportClient;
				if (!LevelClient)
				{
					for (FLevelEditorViewportClient* C : GEditor->GetLevelViewportClients())
					{
						if (C && C->Viewport && C->IsPerspective()) { LevelClient = C; break; }
					}
				}
				if (LevelClient) { Viewport = LevelClient->Viewport; Client = LevelClient; }
			}
			if (!Viewport) { Obj->SetStringField(TEXT("error"), TEXT("No editor viewport is open")); return Obj; }

			const UUnrealEngineMCPSettings* Settings = GetDefault<UUnrealEngineMCPSettings>();
			FString Dir = Settings && !Settings->ScreenshotDirectory.IsEmpty()
				? Settings->ScreenshotDirectory
				: FPaths::ProjectSavedDir() / TEXT("Screenshots/UnrealEngineMCP");
			// A relative setting (the default "Saved/Screenshots/UnrealEngineMCP") must be
			// anchored to the project, not the process cwd (Engine/Binaries/Win64).
			if (FPaths::IsRelative(Dir))
			{
				Dir = FPaths::ProjectDir() / Dir;
			}
			IFileManager::Get().MakeDirectory(*Dir, true);
			FString Filename = Params.IsValid() && Params->HasField(TEXT("filename"))
				? Params->GetStringField(TEXT("filename"))
				: FString::Printf(TEXT("viewport_%s.png"), *FDateTime::Now().ToString(TEXT("%Y%m%d_%H%M%S")));
			if (FPaths::GetExtension(Filename).IsEmpty())
			{
				Filename += TEXT(".png");
			}
			FString FullPath = FPaths::ConvertRelativePathToFull(Dir / Filename);

			// Optional view mode for this capture only (lit, unlit, wireframe, ...).
			FString ViewModeName;
			const bool bSwapMode = Client && Params.IsValid() && Params->TryGetStringField(TEXT("view_mode"), ViewModeName) && !ViewModeName.IsEmpty();
			const EViewModeIndex OldMode = Client ? Client->GetViewMode() : VMI_Lit;
			if (bSwapMode)
			{
				static const TMap<FString, EViewModeIndex> Modes = {
					{TEXT("lit"), VMI_Lit}, {TEXT("unlit"), VMI_Unlit}, {TEXT("wireframe"), VMI_BrushWireframe},
					{TEXT("detail_lighting"), VMI_Lit_DetailLighting}, {TEXT("lighting_only"), VMI_LightingOnly},
					{TEXT("collision"), VMI_CollisionVisibility}};
				const EViewModeIndex* Mode = Modes.Find(ViewModeName.ToLower());
				if (!Mode) { Obj->SetStringField(TEXT("error"), FString::Printf(TEXT("Unknown view_mode '%s'"), *ViewModeName)); return Obj; }
				Client->SetViewMode(*Mode);
			}
			FScreenshotRequest::RequestScreenshot(FullPath, false, false);
			// The request is only serviced on the next viewport draw. A backgrounded
			// editor throttles redraws, so the file may never appear; draw now.
			Viewport->Invalidate();
			Viewport->Draw();
			if (bSwapMode)
			{
				Client->SetViewMode(OldMode);
				Viewport->Invalidate();
			}
			Obj->SetStringField(TEXT("path"), FullPath);
			Obj->SetBoolField(TEXT("requested"), true);
			const bool bWritten = IFileManager::Get().FileExists(*FullPath);
			Obj->SetBoolField(TEXT("file_written"), bWritten);
			// Optional: return a downscaled PNG inline so MCP clients can see the result.
			double MaxSize = 0;
			if (bWritten && Params.IsValid() && Params->TryGetNumberField(TEXT("max_size"), MaxSize) && MaxSize >= 64)
			{
				TArray<uint8> Png;
				IImageWrapperModule& IWM = FModuleManager::LoadModuleChecked<IImageWrapperModule>(TEXT("ImageWrapper"));
				TSharedPtr<IImageWrapper> Reader = IWM.CreateImageWrapper(EImageFormat::PNG);
				TArray<uint8> Raw;
				if (FFileHelper::LoadFileToArray(Png, *FullPath) && Reader.IsValid()
					&& Reader->SetCompressed(Png.GetData(), Png.Num())
					&& Reader->GetRaw(ERGBFormat::BGRA, 8, Raw))
				{
					const int32 W = Reader->GetWidth(), H = Reader->GetHeight();
					const float Scale = FMath::Min(1.f, static_cast<float>(MaxSize) / FMath::Max(W, H));
					const int32 NW = FMath::Max(1, FMath::RoundToInt(W * Scale)), NH = FMath::Max(1, FMath::RoundToInt(H * Scale));
					TArray<FColor> Src; Src.SetNumUninitialized(W * H);
					FMemory::Memcpy(Src.GetData(), Raw.GetData(), W * H * sizeof(FColor));
					TArray<FColor> Dst;
					if (NW != W || NH != H) { Dst.SetNumUninitialized(NW * NH); FImageUtils::ImageResize(W, H, Src, NW, NH, Dst, false); }
					else { Dst = MoveTemp(Src); }
					TSharedPtr<IImageWrapper> Writer = IWM.CreateImageWrapper(EImageFormat::PNG);
					if (Writer.IsValid() && Writer->SetRaw(Dst.GetData(), Dst.Num() * sizeof(FColor), NW, NH, ERGBFormat::BGRA, 8))
					{
						const TArray64<uint8>& Out = Writer->GetCompressed();
						Obj->SetStringField(TEXT("image_base64"), FBase64::Encode(Out.GetData(), static_cast<uint32>(Out.Num())));
						Obj->SetStringField(TEXT("mime_type"), TEXT("image/png"));
						Obj->SetNumberField(TEXT("width"), NW);
						Obj->SetNumberField(TEXT("height"), NH);
					}
				}
			}
			Obj->SetStringField(TEXT("note"), TEXT("If file_written is false, the file appears after the next viewport draw."));
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
			// A relative setting (the default "Saved/Screenshots/UnrealEngineMCP") must be
			// anchored to the project, not the process cwd (Engine/Binaries/Win64).
			if (FPaths::IsRelative(Dir))
			{
				Dir = FPaths::ProjectDir() / Dir;
			}
			IFileManager::Get().MakeDirectory(*Dir, true);
			FString Filename = Params.IsValid() && Params->HasField(TEXT("filename"))
				? Params->GetStringField(TEXT("filename"))
				: FString::Printf(TEXT("screenshot_%s.png"), *FDateTime::Now().ToString(TEXT("%Y%m%d_%H%M%S")));
			if (FPaths::GetExtension(Filename).IsEmpty())
			{
				Filename += TEXT(".png");
			}
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
