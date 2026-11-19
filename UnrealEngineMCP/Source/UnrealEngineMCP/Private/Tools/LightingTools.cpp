#include "Tools/LightingTools.h"
#include "Core/ToolRegistry.h"
#include "Core/ResultSerializer.h"
#include "Core/GameThreadDispatcher.h"
#include "Editor.h"
#include "Engine/World.h"
#include "Engine/DirectionalLight.h"
#include "Engine/PointLight.h"
#include "Engine/SpotLight.h"
#include "Engine/RectLight.h"
#include "Engine/SkyLight.h"
#include "Components/DirectionalLightComponent.h"
#include "Components/PointLightComponent.h"
#include "Components/SpotLightComponent.h"
#include "Components/RectLightComponent.h"
#include "Components/SkyLightComponent.h"
#include "Components/LightComponent.h"
#include "EngineUtils.h"
#include "GameFramework/Actor.h"

#if __has_include("AtmosphericFogComponent.h")
#endif

namespace
{
	FUnrealEngineMCPResponse Ok(const FUnrealEngineMCPRequest& R, TSharedPtr<FJsonObject> O) { return FUnrealEngineMCPResultSerializer::Ok(R.Id, O); }
	FUnrealEngineMCPResponse Fail(const FUnrealEngineMCPRequest& R, const FString& C, const FString& M) { return FUnrealEngineMCPResultSerializer::Fail(R.Id, C, M); }

	AActor* FindActor(UWorld* World, const FString& Name)
	{
		if (!World) return nullptr;
		for (TActorIterator<AActor> It(World); It; ++It)
		{
			if ((*It)->GetName().Equals(Name, ESearchCase::IgnoreCase) || (*It)->GetActorLabel().Equals(Name, ESearchCase::IgnoreCase))
				return *It;
		}
		return nullptr;
	}

	template<typename T>
	TSharedPtr<FJsonObject> SpawnLight(TSharedPtr<FJsonObject> Params)
	{
		TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
		UWorld* World = GEditor ? GEditor->GetEditorWorldContext().World() : nullptr;
		if (!World) { Obj->SetStringField(TEXT("error"), TEXT("No editor world")); return Obj; }
		FVector Loc = FVector::ZeroVector; FRotator Rot = FRotator::ZeroRotator;
		FUnrealEngineMCPResultSerializer::TryGetVector(Params, TEXT("location"), Loc);
		FUnrealEngineMCPResultSerializer::TryGetRotator(Params, TEXT("rotation"), Rot);
		FActorSpawnParameters SP;
		T* Light = World->SpawnActor<T>(Loc, Rot, SP);
		if (!Light) { Obj->SetStringField(TEXT("error"), TEXT("Failed to spawn light")); return Obj; }
		if (Params->HasField(TEXT("name"))) Light->SetActorLabel(Params->GetStringField(TEXT("name")));
		if (Params->HasField(TEXT("intensity")))
		{
			if (ULightComponent* Comp = Cast<ULightComponent>(Light->GetComponentByClass(ULightComponent::StaticClass())))
			{
				Comp->SetIntensity(Params->GetNumberField(TEXT("intensity")));
			}
		}
		Obj->SetStringField(TEXT("name"), Light->GetName());
		Obj->SetStringField(TEXT("label"), Light->GetActorLabel());
		Obj->SetStringField(TEXT("class"), Light->GetClass()->GetName());
		Obj->SetObjectField(TEXT("transform"), FUnrealEngineMCPResultSerializer::Transform(Light->GetActorTransform()));
		return Obj;
	}
}

void FUnrealEngineMCPLightingTools::Register()
{
	auto& Reg = FUnrealEngineMCPToolRegistry::Get();

	Reg.Register(TEXT("unreal_create_directional_light"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		auto Result = FUnrealEngineMCPGameThreadDispatcher::RunJson([Params = Req.Params]() { return SpawnLight<ADirectionalLight>(Params); });
		if (Result->HasField(TEXT("error"))) return Fail(Req, TEXT("engine_error"), Result->GetStringField(TEXT("error")));
		return Ok(Req, Result);
	}), TEXT("Create a directional light."));

	Reg.Register(TEXT("unreal_create_point_light"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		auto Result = FUnrealEngineMCPGameThreadDispatcher::RunJson([Params = Req.Params]() { return SpawnLight<APointLight>(Params); });
		if (Result->HasField(TEXT("error"))) return Fail(Req, TEXT("engine_error"), Result->GetStringField(TEXT("error")));
		return Ok(Req, Result);
	}), TEXT("Create a point light."));

	Reg.Register(TEXT("unreal_create_spot_light"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		auto Result = FUnrealEngineMCPGameThreadDispatcher::RunJson([Params = Req.Params]() { return SpawnLight<ASpotLight>(Params); });
		if (Result->HasField(TEXT("error"))) return Fail(Req, TEXT("engine_error"), Result->GetStringField(TEXT("error")));
		return Ok(Req, Result);
	}), TEXT("Create a spot light."));

	Reg.Register(TEXT("unreal_create_rect_light"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		auto Result = FUnrealEngineMCPGameThreadDispatcher::RunJson([Params = Req.Params]() { return SpawnLight<ARectLight>(Params); });
		if (Result->HasField(TEXT("error"))) return Fail(Req, TEXT("engine_error"), Result->GetStringField(TEXT("error")));
		return Ok(Req, Result);
	}), TEXT("Create a rect light."));

	Reg.Register(TEXT("unreal_create_sky_light"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		auto Result = FUnrealEngineMCPGameThreadDispatcher::RunJson([Params = Req.Params]() { return SpawnLight<ASkyLight>(Params); });
		if (Result->HasField(TEXT("error"))) return Fail(Req, TEXT("engine_error"), Result->GetStringField(TEXT("error")));
		return Ok(Req, Result);
	}), TEXT("Create a sky light."));

	Reg.Register(TEXT("unreal_create_sky_atmosphere"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		TSharedPtr<FJsonObject> Params = Req.Params;
		auto Result = FUnrealEngineMCPGameThreadDispatcher::RunJson([Params]()
		{
			TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
			UWorld* World = GEditor ? GEditor->GetEditorWorldContext().World() : nullptr;
			if (!World) { Obj->SetStringField(TEXT("error"), TEXT("No editor world")); return Obj; }
			UClass* Class = FindObject<UClass>(nullptr, TEXT("/Script/Engine.SkyAtmosphere"));
			if (!Class) { Obj->SetStringField(TEXT("error"), TEXT("SkyAtmosphere class unavailable")); return Obj; }
			AActor* Actor = World->SpawnActor<AActor>(Class);
			if (!Actor) { Obj->SetStringField(TEXT("error"), TEXT("Spawn failed")); return Obj; }
			if (Params->HasField(TEXT("name"))) Actor->SetActorLabel(Params->GetStringField(TEXT("name")));
			Obj->SetStringField(TEXT("name"), Actor->GetName());
			Obj->SetStringField(TEXT("label"), Actor->GetActorLabel());
			return Obj;
		});
		if (Result->HasField(TEXT("error"))) return Fail(Req, TEXT("engine_error"), Result->GetStringField(TEXT("error")));
		return Ok(Req, Result);
	}), TEXT("Create a sky atmosphere actor."));

	Reg.Register(TEXT("unreal_create_exponential_height_fog"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		TSharedPtr<FJsonObject> Params = Req.Params;
		auto Result = FUnrealEngineMCPGameThreadDispatcher::RunJson([Params]()
		{
			TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
			UWorld* World = GEditor ? GEditor->GetEditorWorldContext().World() : nullptr;
			if (!World) { Obj->SetStringField(TEXT("error"), TEXT("No editor world")); return Obj; }
			UClass* Class = FindObject<UClass>(nullptr, TEXT("/Script/Engine.ExponentialHeightFog"));
			if (!Class) { Obj->SetStringField(TEXT("error"), TEXT("ExponentialHeightFog class unavailable")); return Obj; }
			AActor* Actor = World->SpawnActor<AActor>(Class);
			if (!Actor) { Obj->SetStringField(TEXT("error"), TEXT("Spawn failed")); return Obj; }
			if (Params->HasField(TEXT("name"))) Actor->SetActorLabel(Params->GetStringField(TEXT("name")));
			Obj->SetStringField(TEXT("name"), Actor->GetName());
			return Obj;
		});
		if (Result->HasField(TEXT("error"))) return Fail(Req, TEXT("engine_error"), Result->GetStringField(TEXT("error")));
		return Ok(Req, Result);
	}), TEXT("Create exponential height fog."));

	Reg.Register(TEXT("unreal_set_light_intensity"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		TSharedPtr<FJsonObject> Params = Req.Params;
		auto Result = FUnrealEngineMCPGameThreadDispatcher::RunJson([Params]()
		{
			TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
			UWorld* World = GEditor ? GEditor->GetEditorWorldContext().World() : nullptr;
			AActor* Actor = FindActor(World, Params->GetStringField(TEXT("name")));
			if (!Actor) { Obj->SetStringField(TEXT("error"), TEXT("Light not found")); return Obj; }
			ULightComponent* Comp = Actor->FindComponentByClass<ULightComponent>();
			if (!Comp) { Obj->SetStringField(TEXT("error"), TEXT("No light component")); return Obj; }
			Comp->SetIntensity(Params->GetNumberField(TEXT("intensity")));
			Actor->MarkPackageDirty();
			Obj->SetBoolField(TEXT("updated"), true);
			return Obj;
		});
		if (Result->HasField(TEXT("error"))) return Fail(Req, TEXT("engine_error"), Result->GetStringField(TEXT("error")));
		return Ok(Req, Result);
	}), TEXT("Set light intensity."));

	Reg.Register(TEXT("unreal_set_light_color"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		TSharedPtr<FJsonObject> Params = Req.Params;
		auto Result = FUnrealEngineMCPGameThreadDispatcher::RunJson([Params]()
		{
			TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
			UWorld* World = GEditor ? GEditor->GetEditorWorldContext().World() : nullptr;
			AActor* Actor = FindActor(World, Params->GetStringField(TEXT("name")));
			if (!Actor) { Obj->SetStringField(TEXT("error"), TEXT("Light not found")); return Obj; }
			ULightComponent* Comp = Actor->FindComponentByClass<ULightComponent>();
			if (!Comp) { Obj->SetStringField(TEXT("error"), TEXT("No light component")); return Obj; }
			FLinearColor Color(1,1,1);
			if (Params->HasTypedField<EJson::Object>(TEXT("color")))
			{
				auto C = Params->GetObjectField(TEXT("color"));
				Color.R = C->GetNumberField(TEXT("r")); Color.G = C->GetNumberField(TEXT("g")); Color.B = C->GetNumberField(TEXT("b"));
			}
			Comp->SetLightColor(Color);
			Actor->MarkPackageDirty();
			Obj->SetBoolField(TEXT("updated"), true);
			return Obj;
		});
		if (Result->HasField(TEXT("error"))) return Fail(Req, TEXT("engine_error"), Result->GetStringField(TEXT("error")));
		return Ok(Req, Result);
	}), TEXT("Set light color."));

	Reg.Register(TEXT("unreal_set_light_temperature"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		TSharedPtr<FJsonObject> Params = Req.Params;
		auto Result = FUnrealEngineMCPGameThreadDispatcher::RunJson([Params]()
		{
			TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
			UWorld* World = GEditor ? GEditor->GetEditorWorldContext().World() : nullptr;
			AActor* Actor = FindActor(World, Params->GetStringField(TEXT("name")));
			ULightComponent* Comp = Actor ? Actor->FindComponentByClass<ULightComponent>() : nullptr;
			if (!Comp) { Obj->SetStringField(TEXT("error"), TEXT("Light not found")); return Obj; }
			Comp->SetTemperature(Params->GetNumberField(TEXT("temperature")));
			Comp->SetUseTemperature(true);
			Actor->MarkPackageDirty();
			Obj->SetBoolField(TEXT("updated"), true);
			return Obj;
		});
		if (Result->HasField(TEXT("error"))) return Fail(Req, TEXT("engine_error"), Result->GetStringField(TEXT("error")));
		return Ok(Req, Result);
	}), TEXT("Set light temperature."));

	Reg.Register(TEXT("unreal_set_shadow_settings"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		TSharedPtr<FJsonObject> Params = Req.Params;
		auto Result = FUnrealEngineMCPGameThreadDispatcher::RunJson([Params]()
		{
			TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
			UWorld* World = GEditor ? GEditor->GetEditorWorldContext().World() : nullptr;
			AActor* Actor = FindActor(World, Params->GetStringField(TEXT("name")));
			ULightComponent* Comp = Actor ? Actor->FindComponentByClass<ULightComponent>() : nullptr;
			if (!Comp) { Obj->SetStringField(TEXT("error"), TEXT("Light not found")); return Obj; }
			if (Params->HasField(TEXT("cast_shadows"))) Comp->SetCastShadows(Params->GetBoolField(TEXT("cast_shadows")));
			Actor->MarkPackageDirty();
			Obj->SetBoolField(TEXT("updated"), true);
			return Obj;
		});
		if (Result->HasField(TEXT("error"))) return Fail(Req, TEXT("engine_error"), Result->GetStringField(TEXT("error")));
		return Ok(Req, Result);
	}), TEXT("Set light shadow settings."));

	Reg.Register(TEXT("unreal_set_environment_settings"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		return Fail(Req, TEXT("unsupported"), TEXT("Environment settings updates are limited; use dedicated fog/sky/light tools."));
	}), TEXT("Set environment/fog/sky settings."));

	Reg.Register(TEXT("unreal_get_lighting_info"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		auto Result = FUnrealEngineMCPGameThreadDispatcher::RunJson([]()
		{
			TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
			UWorld* World = GEditor ? GEditor->GetEditorWorldContext().World() : nullptr;
			TArray<TSharedPtr<FJsonValue>> Lights;
			if (World)
			{
				for (TActorIterator<AActor> It(World); It; ++It)
				{
					if ((*It)->FindComponentByClass<ULightComponent>())
					{
						TSharedPtr<FJsonObject> L = MakeShared<FJsonObject>();
						L->SetStringField(TEXT("name"), (*It)->GetName());
						L->SetStringField(TEXT("label"), (*It)->GetActorLabel());
						L->SetStringField(TEXT("class"), (*It)->GetClass()->GetName());
						Lights.Add(MakeShared<FJsonValueObject>(L));
					}
				}
			}
			Obj->SetArrayField(TEXT("lights"), Lights);
			Obj->SetNumberField(TEXT("count"), Lights.Num());
			return Obj;
		});
		return Ok(Req, Result);
	}), TEXT("Get lighting actors info."));
}
