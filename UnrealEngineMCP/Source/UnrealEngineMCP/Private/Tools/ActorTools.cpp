#include "Tools/ActorTools.h"
#include "Core/ToolRegistry.h"
#include "Core/ResultSerializer.h"
#include "Core/GameThreadDispatcher.h"
#include "Editor.h"
#include "Engine/World.h"
#include "Engine/StaticMeshActor.h"
#include "Engine/StaticMesh.h"
#include "Components/StaticMeshComponent.h"
#include "Components/SceneComponent.h"
#include "GameFramework/Actor.h"
#include "Subsystems/EditorActorSubsystem.h"
#include "UObject/ConstructorHelpers.h"
#include "EngineUtils.h"
#include "EditorAssetLibrary.h"

namespace ActorToolsPrivate
{
	FUnrealEngineMCPResponse Ok(const FUnrealEngineMCPRequest& Req, TSharedPtr<FJsonObject> Result)
	{
		return FUnrealEngineMCPResultSerializer::Ok(Req.Id, Result);
	}

	FUnrealEngineMCPResponse Fail(const FUnrealEngineMCPRequest& Req, const FString& Code, const FString& Message)
	{
		return FUnrealEngineMCPResultSerializer::Fail(Req.Id, Code, Message);
	}

	AActor* FindActorByNameOrLabel(UWorld* World, const FString& Name)
	{
		if (!World) return nullptr;
		for (TActorIterator<AActor> It(World); It; ++It)
		{
			AActor* Actor = *It;
			if (Actor->GetName().Equals(Name, ESearchCase::IgnoreCase) ||
				Actor->GetActorLabel().Equals(Name, ESearchCase::IgnoreCase) ||
				Actor->GetPathName().Equals(Name, ESearchCase::IgnoreCase))
			{
				return Actor;
			}
		}
		return nullptr;
	}

	TSharedPtr<FJsonObject> ActorToJson(AActor* Actor)
	{
		TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
		if (!Actor) return Obj;
		Obj->SetStringField(TEXT("name"), Actor->GetName());
		Obj->SetStringField(TEXT("label"), Actor->GetActorLabel());
		Obj->SetStringField(TEXT("class"), Actor->GetClass()->GetName());
		Obj->SetStringField(TEXT("path"), Actor->GetPathName());
		Obj->SetBoolField(TEXT("hidden"), Actor->IsHidden());
		Obj->SetObjectField(TEXT("transform"), FUnrealEngineMCPResultSerializer::Transform(Actor->GetActorTransform()));
		return Obj;
	}
}

void FUnrealEngineMCPActorTools::Register()
{
	using namespace ActorToolsPrivate;
	auto& Reg = FUnrealEngineMCPToolRegistry::Get();

	Reg.Register(TEXT("unreal_spawn_actor"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
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

			FString ClassName = Params->HasField(TEXT("class_name")) ? Params->GetStringField(TEXT("class_name")) : TEXT("StaticMeshActor");
			FString Name = Params->HasField(TEXT("name")) ? Params->GetStringField(TEXT("name")) : TEXT("");
			FVector Location = FVector::ZeroVector;
			FRotator Rotation = FRotator::ZeroRotator;
			FVector Scale = FVector::OneVector;
			FUnrealEngineMCPResultSerializer::TryGetVector(Params, TEXT("location"), Location);
			FUnrealEngineMCPResultSerializer::TryGetRotator(Params, TEXT("rotation"), Rotation);
			FUnrealEngineMCPResultSerializer::TryGetVector(Params, TEXT("scale"), Scale);

			UClass* ActorClass = AStaticMeshActor::StaticClass();
			if (ClassName.Equals(TEXT("CameraActor"), ESearchCase::IgnoreCase))
			{
				ActorClass = FindObject<UClass>(nullptr, TEXT("/Script/Engine.CameraActor"));
			}
			else if (!ClassName.Equals(TEXT("StaticMeshActor"), ESearchCase::IgnoreCase))
			{
				UClass* Found = FindObject<UClass>(nullptr, *FString::Printf(TEXT("/Script/Engine.%s"), *ClassName));
				if (!Found)
				{
					Found = LoadObject<UClass>(nullptr, *ClassName);
				}
				if (!Found || !Found->IsChildOf(AActor::StaticClass()))
				{
					Obj->SetStringField(TEXT("error"), FString::Printf(TEXT("Actor class '%s' not found or not an Actor"), *ClassName));
					return Obj;
				}
				ActorClass = Found;
			}

			FActorSpawnParameters SpawnParams;
			SpawnParams.Name = Name.IsEmpty() ? NAME_None : FName(*Name);
			// A forced name that is still in use (an existing actor, or one just deleted
			// and held by the undo buffer) is a fatal error in SpawnActor. Treat it as a
			// request so the engine picks a unique object name; the label stays exact.
			SpawnParams.NameMode = FActorSpawnParameters::ESpawnActorNameMode::Requested;
			SpawnParams.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
			AActor* Actor = World->SpawnActor<AActor>(ActorClass, Location, Rotation, SpawnParams);
			if (!Actor)
			{
				Obj->SetStringField(TEXT("error"), TEXT("SpawnActor failed"));
				return Obj;
			}
			Actor->SetActorScale3D(Scale);
			if (!Name.IsEmpty())
			{
				Actor->SetActorLabel(Name);
			}

			if (AStaticMeshActor* MeshActor = Cast<AStaticMeshActor>(Actor))
			{
				FString MeshPath = Params->HasField(TEXT("mesh"))
					? Params->GetStringField(TEXT("mesh"))
					: TEXT("/Engine/BasicShapes/Cube.Cube");
				if (UStaticMesh* Mesh = LoadObject<UStaticMesh>(nullptr, *MeshPath))
				{
					MeshActor->GetStaticMeshComponent()->SetStaticMesh(Mesh);
				}
			}

			Actor->MarkPackageDirty();
			Obj = ActorToJson(Actor);
			return Obj;
		});

		if (Result->HasField(TEXT("error")))
		{
			return Fail(Req, TEXT("engine_error"), Result->GetStringField(TEXT("error")));
		}
		return Ok(Req, Result);
	}), TEXT("Spawn an actor in the current level."));

	Reg.Register(TEXT("unreal_delete_actor"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		TSharedPtr<FJsonObject> Params = Req.Params;
		TSharedPtr<FJsonObject> Result = FUnrealEngineMCPGameThreadDispatcher::RunJson([Params]()
		{
			TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
			UWorld* World = GEditor ? GEditor->GetEditorWorldContext().World() : nullptr;
			FString Name = Params->GetStringField(TEXT("name"));
			AActor* Actor = FindActorByNameOrLabel(World, Name);
			if (!Actor)
			{
				Obj->SetStringField(TEXT("error"), TEXT("Actor not found"));
				return Obj;
			}
			const FString Deleted = Actor->GetActorLabel();
			bool bOk = false;
			if (UEditorActorSubsystem* Sub = GEditor->GetEditorSubsystem<UEditorActorSubsystem>())
			{
				bOk = Sub->DestroyActor(Actor);
			}
			else
			{
				bOk = World->DestroyActor(Actor);
			}
			if (!bOk)
			{
				Obj->SetStringField(TEXT("error"), TEXT("Failed to destroy actor"));
				return Obj;
			}
			Obj->SetStringField(TEXT("deleted"), Deleted);
			return Obj;
		});
		if (Result->HasField(TEXT("error"))) return Fail(Req, TEXT("engine_error"), Result->GetStringField(TEXT("error")));
		return Ok(Req, Result);
	}), TEXT("Delete an actor by name or path."));

	Reg.Register(TEXT("unreal_duplicate_actor"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		TSharedPtr<FJsonObject> Params = Req.Params;
		TSharedPtr<FJsonObject> Result = FUnrealEngineMCPGameThreadDispatcher::RunJson([Params]()
		{
			TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
			UWorld* World = GEditor ? GEditor->GetEditorWorldContext().World() : nullptr;
			AActor* Actor = FindActorByNameOrLabel(World, Params->GetStringField(TEXT("name")));
			if (!Actor)
			{
				Obj->SetStringField(TEXT("error"), TEXT("Actor not found"));
				return Obj;
			}
			UEditorActorSubsystem* Sub = GEditor->GetEditorSubsystem<UEditorActorSubsystem>();
			AActor* Dup = Sub ? Sub->DuplicateActor(Actor) : nullptr;
			if (!Dup)
			{
				Obj->SetStringField(TEXT("error"), TEXT("Duplicate failed"));
				return Obj;
			}
			if (Params->HasField(TEXT("new_name")))
			{
				Dup->SetActorLabel(Params->GetStringField(TEXT("new_name")));
			}
			return ActorToJson(Dup);
		});
		if (Result->HasField(TEXT("error"))) return Fail(Req, TEXT("engine_error"), Result->GetStringField(TEXT("error")));
		return Ok(Req, Result);
	}), TEXT("Duplicate an actor."));

	Reg.Register(TEXT("unreal_find_actor"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		TSharedPtr<FJsonObject> Params = Req.Params;
		TSharedPtr<FJsonObject> Result = FUnrealEngineMCPGameThreadDispatcher::RunJson([Params]()
		{
			TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
			UWorld* World = GEditor ? GEditor->GetEditorWorldContext().World() : nullptr;
			TArray<TSharedPtr<FJsonValue>> Matches;
			FString Query = Params->HasField(TEXT("query")) ? Params->GetStringField(TEXT("query")) : Params->GetStringField(TEXT("name"));
			FString ClassFilter = Params->HasField(TEXT("class_name")) ? Params->GetStringField(TEXT("class_name")) : TEXT("");
			if (World)
			{
				for (TActorIterator<AActor> It(World); It; ++It)
				{
					AActor* Actor = *It;
					const bool bNameMatch = Query.IsEmpty() || Actor->GetName().Contains(Query) || Actor->GetActorLabel().Contains(Query);
					const bool bClassMatch = ClassFilter.IsEmpty() || Actor->GetClass()->GetName().Contains(ClassFilter);
					if (bNameMatch && bClassMatch)
					{
						Matches.Add(MakeShared<FJsonValueObject>(ActorToJson(Actor)));
					}
				}
			}
			Obj->SetArrayField(TEXT("actors"), Matches);
			return Obj;
		});
		return Ok(Req, Result);
	}), TEXT("Find actors by name/label/class."));

	Reg.Register(TEXT("unreal_get_actor_details"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		TSharedPtr<FJsonObject> Params = Req.Params;
		TSharedPtr<FJsonObject> Result = FUnrealEngineMCPGameThreadDispatcher::RunJson([Params]()
		{
			UWorld* World = GEditor ? GEditor->GetEditorWorldContext().World() : nullptr;
			AActor* Actor = FindActorByNameOrLabel(World, Params->GetStringField(TEXT("name")));
			if (!Actor)
			{
				TSharedPtr<FJsonObject> Err = MakeShared<FJsonObject>();
				Err->SetStringField(TEXT("error"), TEXT("Actor not found"));
				return Err;
			}
			TSharedPtr<FJsonObject> Obj = ActorToJson(Actor);
			TArray<TSharedPtr<FJsonValue>> Components;
			TArray<UActorComponent*> Comps;
			Actor->GetComponents(Comps);
			for (UActorComponent* Comp : Comps)
			{
				TSharedPtr<FJsonObject> C = MakeShared<FJsonObject>();
				C->SetStringField(TEXT("name"), Comp->GetName());
				C->SetStringField(TEXT("class"), Comp->GetClass()->GetName());
				Components.Add(MakeShared<FJsonValueObject>(C));
			}
			Obj->SetArrayField(TEXT("components"), Components);
			return Obj;
		});
		if (Result->HasField(TEXT("error"))) return Fail(Req, TEXT("engine_error"), Result->GetStringField(TEXT("error")));
		return Ok(Req, Result);
	}), TEXT("Get detailed actor information."));

	Reg.Register(TEXT("unreal_get_all_actors"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
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
					Actors.Add(MakeShared<FJsonValueObject>(ActorToJson(*It)));
					++Count;
				}
			}
			Obj->SetArrayField(TEXT("actors"), Actors);
			Obj->SetNumberField(TEXT("count"), Actors.Num());
			return Obj;
		});
		return Ok(Req, Result);
	}), TEXT("List actors in the current world."));

	Reg.Register(TEXT("unreal_set_actor_transform"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		TSharedPtr<FJsonObject> Params = Req.Params;
		TSharedPtr<FJsonObject> Result = FUnrealEngineMCPGameThreadDispatcher::RunJson([Params]()
		{
			TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
			UWorld* World = GEditor ? GEditor->GetEditorWorldContext().World() : nullptr;
			AActor* Actor = FindActorByNameOrLabel(World, Params->GetStringField(TEXT("name")));
			if (!Actor)
			{
				Obj->SetStringField(TEXT("error"), TEXT("Actor not found"));
				return Obj;
			}
			FVector Loc = Actor->GetActorLocation();
			FRotator Rot = Actor->GetActorRotation();
			FVector Scale = Actor->GetActorScale3D();
			FUnrealEngineMCPResultSerializer::TryGetVector(Params, TEXT("location"), Loc);
			FUnrealEngineMCPResultSerializer::TryGetRotator(Params, TEXT("rotation"), Rot);
			FUnrealEngineMCPResultSerializer::TryGetVector(Params, TEXT("scale"), Scale);
			Actor->SetActorTransform(FTransform(Rot, Loc, Scale));
			Actor->MarkPackageDirty();
			return ActorToJson(Actor);
		});
		if (Result->HasField(TEXT("error"))) return Fail(Req, TEXT("engine_error"), Result->GetStringField(TEXT("error")));
		return Ok(Req, Result);
	}), TEXT("Set actor location/rotation/scale."));

	Reg.Register(TEXT("unreal_get_actor_transform"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		TSharedPtr<FJsonObject> Params = Req.Params;
		TSharedPtr<FJsonObject> Result = FUnrealEngineMCPGameThreadDispatcher::RunJson([Params]()
		{
			TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
			UWorld* World = GEditor ? GEditor->GetEditorWorldContext().World() : nullptr;
			AActor* Actor = FindActorByNameOrLabel(World, Params->GetStringField(TEXT("name")));
			if (!Actor)
			{
				Obj->SetStringField(TEXT("error"), TEXT("Actor not found"));
				return Obj;
			}
			return FUnrealEngineMCPResultSerializer::Transform(Actor->GetActorTransform());
		});
		if (Result->HasField(TEXT("error"))) return Fail(Req, TEXT("engine_error"), Result->GetStringField(TEXT("error")));
		return Ok(Req, Result);
	}), TEXT("Get actor transform."));

	Reg.Register(TEXT("unreal_set_actor_location"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		TSharedPtr<FJsonObject> Params = Req.Params;
		TSharedPtr<FJsonObject> Result = FUnrealEngineMCPGameThreadDispatcher::RunJson([Params]()
		{
			TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
			UWorld* World = GEditor ? GEditor->GetEditorWorldContext().World() : nullptr;
			AActor* Actor = FindActorByNameOrLabel(World, Params->GetStringField(TEXT("name")));
			if (!Actor) { Obj->SetStringField(TEXT("error"), TEXT("Actor not found")); return Obj; }
			FVector Loc = Actor->GetActorLocation();
			if (Params->HasField(TEXT("x"))) Loc.X = Params->GetNumberField(TEXT("x"));
			if (Params->HasField(TEXT("y"))) Loc.Y = Params->GetNumberField(TEXT("y"));
			if (Params->HasField(TEXT("z"))) Loc.Z = Params->GetNumberField(TEXT("z"));
			FUnrealEngineMCPResultSerializer::TryGetVector(Params, TEXT("location"), Loc);
			Actor->SetActorLocation(Loc);
			Actor->MarkPackageDirty();
			return ActorToJson(Actor);
		});
		if (Result->HasField(TEXT("error"))) return Fail(Req, TEXT("engine_error"), Result->GetStringField(TEXT("error")));
		return Ok(Req, Result);
	}), TEXT("Set actor location."));

	Reg.Register(TEXT("unreal_set_actor_rotation"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		TSharedPtr<FJsonObject> Params = Req.Params;
		TSharedPtr<FJsonObject> Result = FUnrealEngineMCPGameThreadDispatcher::RunJson([Params]()
		{
			TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
			UWorld* World = GEditor ? GEditor->GetEditorWorldContext().World() : nullptr;
			AActor* Actor = FindActorByNameOrLabel(World, Params->GetStringField(TEXT("name")));
			if (!Actor) { Obj->SetStringField(TEXT("error"), TEXT("Actor not found")); return Obj; }
			FRotator Rot = Actor->GetActorRotation();
			if (Params->HasField(TEXT("pitch"))) Rot.Pitch = Params->GetNumberField(TEXT("pitch"));
			if (Params->HasField(TEXT("yaw"))) Rot.Yaw = Params->GetNumberField(TEXT("yaw"));
			if (Params->HasField(TEXT("roll"))) Rot.Roll = Params->GetNumberField(TEXT("roll"));
			FUnrealEngineMCPResultSerializer::TryGetRotator(Params, TEXT("rotation"), Rot);
			Actor->SetActorRotation(Rot);
			Actor->MarkPackageDirty();
			return ActorToJson(Actor);
		});
		if (Result->HasField(TEXT("error"))) return Fail(Req, TEXT("engine_error"), Result->GetStringField(TEXT("error")));
		return Ok(Req, Result);
	}), TEXT("Set actor rotation."));

	Reg.Register(TEXT("unreal_set_actor_scale"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		TSharedPtr<FJsonObject> Params = Req.Params;
		TSharedPtr<FJsonObject> Result = FUnrealEngineMCPGameThreadDispatcher::RunJson([Params]()
		{
			TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
			UWorld* World = GEditor ? GEditor->GetEditorWorldContext().World() : nullptr;
			AActor* Actor = FindActorByNameOrLabel(World, Params->GetStringField(TEXT("name")));
			if (!Actor) { Obj->SetStringField(TEXT("error"), TEXT("Actor not found")); return Obj; }
			FVector Scale = Actor->GetActorScale3D();
			if (Params->HasField(TEXT("x"))) Scale.X = Params->GetNumberField(TEXT("x"));
			if (Params->HasField(TEXT("y"))) Scale.Y = Params->GetNumberField(TEXT("y"));
			if (Params->HasField(TEXT("z"))) Scale.Z = Params->GetNumberField(TEXT("z"));
			FUnrealEngineMCPResultSerializer::TryGetVector(Params, TEXT("scale"), Scale);
			Actor->SetActorScale3D(Scale);
			Actor->MarkPackageDirty();
			return ActorToJson(Actor);
		});
		if (Result->HasField(TEXT("error"))) return Fail(Req, TEXT("engine_error"), Result->GetStringField(TEXT("error")));
		return Ok(Req, Result);
	}), TEXT("Set actor scale."));

	Reg.Register(TEXT("unreal_rename_actor"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		TSharedPtr<FJsonObject> Params = Req.Params;
		TSharedPtr<FJsonObject> Result = FUnrealEngineMCPGameThreadDispatcher::RunJson([Params]()
		{
			TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
			UWorld* World = GEditor ? GEditor->GetEditorWorldContext().World() : nullptr;
			AActor* Actor = FindActorByNameOrLabel(World, Params->GetStringField(TEXT("name")));
			if (!Actor) { Obj->SetStringField(TEXT("error"), TEXT("Actor not found")); return Obj; }
			Actor->SetActorLabel(Params->GetStringField(TEXT("new_name")));
			Actor->MarkPackageDirty();
			return ActorToJson(Actor);
		});
		if (Result->HasField(TEXT("error"))) return Fail(Req, TEXT("engine_error"), Result->GetStringField(TEXT("error")));
		return Ok(Req, Result);
	}), TEXT("Rename an actor label."));

	Reg.Register(TEXT("unreal_set_actor_visibility"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		TSharedPtr<FJsonObject> Params = Req.Params;
		TSharedPtr<FJsonObject> Result = FUnrealEngineMCPGameThreadDispatcher::RunJson([Params]()
		{
			TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
			UWorld* World = GEditor ? GEditor->GetEditorWorldContext().World() : nullptr;
			AActor* Actor = FindActorByNameOrLabel(World, Params->GetStringField(TEXT("name")));
			if (!Actor) { Obj->SetStringField(TEXT("error"), TEXT("Actor not found")); return Obj; }
			const bool bVisible = Params->HasField(TEXT("visible")) ? Params->GetBoolField(TEXT("visible")) : true;
			Actor->SetIsTemporarilyHiddenInEditor(!bVisible);
			Actor->SetActorHiddenInGame(!bVisible);
			Actor->MarkPackageDirty();
			return ActorToJson(Actor);
		});
		if (Result->HasField(TEXT("error"))) return Fail(Req, TEXT("engine_error"), Result->GetStringField(TEXT("error")));
		return Ok(Req, Result);
	}), TEXT("Set actor visibility."));

	Reg.Register(TEXT("unreal_set_actor_mobility"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		TSharedPtr<FJsonObject> Params = Req.Params;
		TSharedPtr<FJsonObject> Result = FUnrealEngineMCPGameThreadDispatcher::RunJson([Params]()
		{
			TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
			UWorld* World = GEditor ? GEditor->GetEditorWorldContext().World() : nullptr;
			AActor* Actor = FindActorByNameOrLabel(World, Params->GetStringField(TEXT("name")));
			if (!Actor) { Obj->SetStringField(TEXT("error"), TEXT("Actor not found")); return Obj; }
			USceneComponent* Root = Actor->GetRootComponent();
			if (!Root) { Obj->SetStringField(TEXT("error"), TEXT("No root component")); return Obj; }
			FString Mobility = Params->GetStringField(TEXT("mobility"));
			if (Mobility.Equals(TEXT("Static"), ESearchCase::IgnoreCase)) Root->SetMobility(EComponentMobility::Static);
			else if (Mobility.Equals(TEXT("Stationary"), ESearchCase::IgnoreCase)) Root->SetMobility(EComponentMobility::Stationary);
			else Root->SetMobility(EComponentMobility::Movable);
			Actor->MarkPackageDirty();
			Obj = ActorToJson(Actor);
			Obj->SetStringField(TEXT("mobility"), Mobility);
			return Obj;
		});
		if (Result->HasField(TEXT("error"))) return Fail(Req, TEXT("engine_error"), Result->GetStringField(TEXT("error")));
		return Ok(Req, Result);
	}), TEXT("Set actor mobility."));

	Reg.Register(TEXT("unreal_attach_actor"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		TSharedPtr<FJsonObject> Params = Req.Params;
		TSharedPtr<FJsonObject> Result = FUnrealEngineMCPGameThreadDispatcher::RunJson([Params]()
		{
			TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
			UWorld* World = GEditor ? GEditor->GetEditorWorldContext().World() : nullptr;
			AActor* Child = FindActorByNameOrLabel(World, Params->GetStringField(TEXT("name")));
			AActor* Parent = FindActorByNameOrLabel(World, Params->GetStringField(TEXT("parent")));
			if (!Child || !Parent) { Obj->SetStringField(TEXT("error"), TEXT("Child or parent not found")); return Obj; }
			Child->AttachToActor(Parent, FAttachmentTransformRules::KeepWorldTransform);
			Child->MarkPackageDirty();
			return ActorToJson(Child);
		});
		if (Result->HasField(TEXT("error"))) return Fail(Req, TEXT("engine_error"), Result->GetStringField(TEXT("error")));
		return Ok(Req, Result);
	}), TEXT("Attach an actor to another."));

	Reg.Register(TEXT("unreal_detach_actor"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		TSharedPtr<FJsonObject> Params = Req.Params;
		TSharedPtr<FJsonObject> Result = FUnrealEngineMCPGameThreadDispatcher::RunJson([Params]()
		{
			TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
			UWorld* World = GEditor ? GEditor->GetEditorWorldContext().World() : nullptr;
			AActor* Actor = FindActorByNameOrLabel(World, Params->GetStringField(TEXT("name")));
			if (!Actor) { Obj->SetStringField(TEXT("error"), TEXT("Actor not found")); return Obj; }
			Actor->DetachFromActor(FDetachmentTransformRules::KeepWorldTransform);
			Actor->MarkPackageDirty();
			return ActorToJson(Actor);
		});
		if (Result->HasField(TEXT("error"))) return Fail(Req, TEXT("engine_error"), Result->GetStringField(TEXT("error")));
		return Ok(Req, Result);
	}), TEXT("Detach an actor from its parent."));

	Reg.Register(TEXT("unreal_get_actor_components"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		TSharedPtr<FJsonObject> Params = Req.Params;
		TSharedPtr<FJsonObject> Result = FUnrealEngineMCPGameThreadDispatcher::RunJson([Params]()
		{
			TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
			UWorld* World = GEditor ? GEditor->GetEditorWorldContext().World() : nullptr;
			AActor* Actor = FindActorByNameOrLabel(World, Params->GetStringField(TEXT("name")));
			if (!Actor) { Obj->SetStringField(TEXT("error"), TEXT("Actor not found")); return Obj; }
			TArray<TSharedPtr<FJsonValue>> Components;
			TArray<UActorComponent*> Comps;
			Actor->GetComponents(Comps);
			for (UActorComponent* Comp : Comps)
			{
				TSharedPtr<FJsonObject> C = MakeShared<FJsonObject>();
				C->SetStringField(TEXT("name"), Comp->GetName());
				C->SetStringField(TEXT("class"), Comp->GetClass()->GetName());
				Components.Add(MakeShared<FJsonValueObject>(C));
			}
			Obj->SetArrayField(TEXT("components"), Components);
			return Obj;
		});
		if (Result->HasField(TEXT("error"))) return Fail(Req, TEXT("engine_error"), Result->GetStringField(TEXT("error")));
		return Ok(Req, Result);
	}), TEXT("List actor components."));

	Reg.Register(TEXT("unreal_add_component"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		TSharedPtr<FJsonObject> Params = Req.Params;
		TSharedPtr<FJsonObject> Result = FUnrealEngineMCPGameThreadDispatcher::RunJson([Params]()
		{
			TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
			UWorld* World = GEditor ? GEditor->GetEditorWorldContext().World() : nullptr;
			AActor* Actor = FindActorByNameOrLabel(World, Params->GetStringField(TEXT("name")));
			if (!Actor) { Obj->SetStringField(TEXT("error"), TEXT("Actor not found")); return Obj; }
			FString CompClassName = Params->GetStringField(TEXT("component_class"));
			UClass* CompClass = FindObject<UClass>(nullptr, *FString::Printf(TEXT("/Script/Engine.%s"), *CompClassName));
			if (!CompClass) CompClass = LoadObject<UClass>(nullptr, *CompClassName);
			if (!CompClass || !CompClass->IsChildOf(UActorComponent::StaticClass()))
			{
				Obj->SetStringField(TEXT("error"), TEXT("Invalid component class"));
				return Obj;
			}
			FString CompName = Params->HasField(TEXT("component_name")) ? Params->GetStringField(TEXT("component_name")) : CompClassName;
			UActorComponent* Comp = NewObject<UActorComponent>(Actor, CompClass, *CompName);
			if (USceneComponent* Scene = Cast<USceneComponent>(Comp))
			{
				Scene->SetupAttachment(Actor->GetRootComponent());
			}
			Actor->AddInstanceComponent(Comp);
			Comp->RegisterComponent();
			Actor->MarkPackageDirty();
			Obj->SetStringField(TEXT("component"), Comp->GetName());
			Obj->SetStringField(TEXT("class"), Comp->GetClass()->GetName());
			return Obj;
		});
		if (Result->HasField(TEXT("error"))) return Fail(Req, TEXT("engine_error"), Result->GetStringField(TEXT("error")));
		return Ok(Req, Result);
	}), TEXT("Add a component to an actor."));

	Reg.Register(TEXT("unreal_remove_component"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		TSharedPtr<FJsonObject> Params = Req.Params;
		TSharedPtr<FJsonObject> Result = FUnrealEngineMCPGameThreadDispatcher::RunJson([Params]()
		{
			TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
			UWorld* World = GEditor ? GEditor->GetEditorWorldContext().World() : nullptr;
			AActor* Actor = FindActorByNameOrLabel(World, Params->GetStringField(TEXT("name")));
			if (!Actor) { Obj->SetStringField(TEXT("error"), TEXT("Actor not found")); return Obj; }
			FString CompName = Params->GetStringField(TEXT("component_name"));
			TArray<UActorComponent*> Comps;
			Actor->GetComponents(Comps);
			for (UActorComponent* Comp : Comps)
			{
				if (Comp->GetName().Equals(CompName, ESearchCase::IgnoreCase))
				{
					Comp->DestroyComponent();
					Actor->MarkPackageDirty();
					Obj->SetStringField(TEXT("removed"), CompName);
					return Obj;
				}
			}
			Obj->SetStringField(TEXT("error"), TEXT("Component not found"));
			return Obj;
		});
		if (Result->HasField(TEXT("error"))) return Fail(Req, TEXT("engine_error"), Result->GetStringField(TEXT("error")));
		return Ok(Req, Result);
	}), TEXT("Remove a component from an actor."));
}
