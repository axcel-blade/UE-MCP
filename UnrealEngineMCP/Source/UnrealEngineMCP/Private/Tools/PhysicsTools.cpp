#include "Tools/PhysicsTools.h"
#include "Core/ToolRegistry.h"
#include "Core/ResultSerializer.h"
#include "Core/GameThreadDispatcher.h"
#include "Editor.h"
#include "EngineUtils.h"
#include "GameFramework/Actor.h"
#include "Components/PrimitiveComponent.h"
#include "Engine/EngineTypes.h"

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

	UPrimitiveComponent* GetPrim(AActor* Actor)
	{
		return Actor ? Actor->FindComponentByClass<UPrimitiveComponent>() : nullptr;
	}
}

void FUnrealEngineMCPPhysicsTools::Register()
{
	auto& Reg = FUnrealEngineMCPToolRegistry::Get();

	Reg.Register(TEXT("unreal_set_simulate_physics"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		TSharedPtr<FJsonObject> Params = Req.Params;
		auto Result = FUnrealEngineMCPGameThreadDispatcher::RunJson([Params]()
		{
			TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
			UWorld* World = GEditor ? GEditor->GetEditorWorldContext().World() : nullptr;
			AActor* Actor = FindActor(World, Params->GetStringField(TEXT("name")));
			UPrimitiveComponent* Prim = GetPrim(Actor);
			if (!Prim) { Obj->SetStringField(TEXT("error"), TEXT("Primitive component not found")); return Obj; }
			const bool bEnable = Params->HasField(TEXT("enabled")) ? Params->GetBoolField(TEXT("enabled")) : true;
			Prim->SetSimulatePhysics(bEnable);
			Actor->MarkPackageDirty();
			Obj->SetBoolField(TEXT("simulate_physics"), bEnable);
			return Obj;
		});
		if (Result->HasField(TEXT("error"))) return Fail(Req, TEXT("engine_error"), Result->GetStringField(TEXT("error")));
		return Ok(Req, Result);
	}), TEXT("Toggle simulate physics."));

	Reg.Register(TEXT("unreal_set_physics_enabled"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		// Alias behavior
		TSharedPtr<FJsonObject> Params = Req.Params;
		auto Result = FUnrealEngineMCPGameThreadDispatcher::RunJson([Params]()
		{
			TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
			UWorld* World = GEditor ? GEditor->GetEditorWorldContext().World() : nullptr;
			AActor* Actor = FindActor(World, Params->GetStringField(TEXT("name")));
			UPrimitiveComponent* Prim = GetPrim(Actor);
			if (!Prim) { Obj->SetStringField(TEXT("error"), TEXT("Primitive component not found")); return Obj; }
			const bool bEnable = Params->HasField(TEXT("enabled")) ? Params->GetBoolField(TEXT("enabled")) : true;
			Prim->SetSimulatePhysics(bEnable);
			Obj->SetBoolField(TEXT("enabled"), bEnable);
			return Obj;
		});
		if (Result->HasField(TEXT("error"))) return Fail(Req, TEXT("engine_error"), Result->GetStringField(TEXT("error")));
		return Ok(Req, Result);
	}), TEXT("Enable/disable physics on an actor/component."));

	Reg.Register(TEXT("unreal_set_collision_profile"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		TSharedPtr<FJsonObject> Params = Req.Params;
		auto Result = FUnrealEngineMCPGameThreadDispatcher::RunJson([Params]()
		{
			TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
			UWorld* World = GEditor ? GEditor->GetEditorWorldContext().World() : nullptr;
			AActor* Actor = FindActor(World, Params->GetStringField(TEXT("name")));
			UPrimitiveComponent* Prim = GetPrim(Actor);
			if (!Prim) { Obj->SetStringField(TEXT("error"), TEXT("Primitive component not found")); return Obj; }
			Prim->SetCollisionProfileName(FName(*Params->GetStringField(TEXT("profile"))));
			Actor->MarkPackageDirty();
			Obj->SetStringField(TEXT("profile"), Params->GetStringField(TEXT("profile")));
			return Obj;
		});
		if (Result->HasField(TEXT("error"))) return Fail(Req, TEXT("engine_error"), Result->GetStringField(TEXT("error")));
		return Ok(Req, Result);
	}), TEXT("Set collision profile name."));

	Reg.Register(TEXT("unreal_get_physics_info"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		TSharedPtr<FJsonObject> Params = Req.Params;
		auto Result = FUnrealEngineMCPGameThreadDispatcher::RunJson([Params]()
		{
			TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
			UWorld* World = GEditor ? GEditor->GetEditorWorldContext().World() : nullptr;
			AActor* Actor = FindActor(World, Params->GetStringField(TEXT("name")));
			UPrimitiveComponent* Prim = GetPrim(Actor);
			if (!Prim) { Obj->SetStringField(TEXT("error"), TEXT("Primitive component not found")); return Obj; }
			Obj->SetBoolField(TEXT("simulate_physics"), Prim->IsSimulatingPhysics());
			Obj->SetStringField(TEXT("collision_profile"), Prim->GetCollisionProfileName().ToString());
			Obj->SetNumberField(TEXT("mass"), Prim->GetMass());
			return Obj;
		});
		if (Result->HasField(TEXT("error"))) return Fail(Req, TEXT("engine_error"), Result->GetStringField(TEXT("error")));
		return Ok(Req, Result);
	}), TEXT("Get physics info for an actor."));

	Reg.Register(TEXT("unreal_set_gravity"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		TSharedPtr<FJsonObject> Params = Req.Params;
		auto Result = FUnrealEngineMCPGameThreadDispatcher::RunJson([Params]()
		{
			TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
			UWorld* World = GEditor ? GEditor->GetEditorWorldContext().World() : nullptr;
			AActor* Actor = FindActor(World, Params->GetStringField(TEXT("name")));
			UPrimitiveComponent* Prim = GetPrim(Actor);
			if (!Prim) { Obj->SetStringField(TEXT("error"), TEXT("Primitive component not found")); return Obj; }
			const bool bEnable = Params->HasField(TEXT("enabled")) ? Params->GetBoolField(TEXT("enabled")) : true;
			Prim->SetEnableGravity(bEnable);
			Obj->SetBoolField(TEXT("gravity"), bEnable);
			return Obj;
		});
		if (Result->HasField(TEXT("error"))) return Fail(Req, TEXT("engine_error"), Result->GetStringField(TEXT("error")));
		return Ok(Req, Result);
	}), TEXT("Set gravity enabled/scale."));

	Reg.Register(TEXT("unreal_set_mass"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		TSharedPtr<FJsonObject> Params = Req.Params;
		auto Result = FUnrealEngineMCPGameThreadDispatcher::RunJson([Params]()
		{
			TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
			UWorld* World = GEditor ? GEditor->GetEditorWorldContext().World() : nullptr;
			AActor* Actor = FindActor(World, Params->GetStringField(TEXT("name")));
			UPrimitiveComponent* Prim = GetPrim(Actor);
			if (!Prim) { Obj->SetStringField(TEXT("error"), TEXT("Primitive component not found")); return Obj; }
			Prim->SetMassOverrideInKg(NAME_None, Params->GetNumberField(TEXT("mass")), true);
			Obj->SetNumberField(TEXT("mass"), Params->GetNumberField(TEXT("mass")));
			return Obj;
		});
		if (Result->HasField(TEXT("error"))) return Fail(Req, TEXT("engine_error"), Result->GetStringField(TEXT("error")));
		return Ok(Req, Result);
	}), TEXT("Set mass override."));

	Reg.Register(TEXT("unreal_set_linear_velocity"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		return Fail(Req, TEXT("unsupported"), TEXT("Linear velocity is runtime/PIE oriented; not applied in editor world by default."));
	}), TEXT("Set linear velocity."));

	Reg.Register(TEXT("unreal_set_angular_velocity"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		return Fail(Req, TEXT("unsupported"), TEXT("Angular velocity is runtime/PIE oriented; not applied in editor world by default."));
	}), TEXT("Set angular velocity."));

	Reg.Register(TEXT("unreal_get_collision_channels"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		TSharedPtr<FJsonObject> Result = MakeShared<FJsonObject>();
		TArray<TSharedPtr<FJsonValue>> Channels;
		for (int32 i = 0; i < 32; ++i)
		{
			Channels.Add(MakeShared<FJsonValueString>(FString::Printf(TEXT("Channel_%d"), i)));
		}
		Result->SetArrayField(TEXT("channels"), Channels);
		Result->SetStringField(TEXT("note"), TEXT("Named project channels require CollisionProfile config parsing."));
		return Ok(Req, Result);
	}), TEXT("Get collision channel names."));
}
