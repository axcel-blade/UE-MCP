#include "Tools/MaterialTools.h"
#include "Core/ToolRegistry.h"
#include "Core/ResultSerializer.h"
#include "Core/GameThreadDispatcher.h"
#include "Materials/Material.h"
#include "Materials/MaterialInstanceConstant.h"
#include "Factories/MaterialFactoryNew.h"
#include "Factories/MaterialInstanceConstantFactoryNew.h"
#include "AssetToolsModule.h"
#include "EditorAssetLibrary.h"
#include "Misc/PackageName.h"
#include "Engine/StaticMeshActor.h"
#include "Components/StaticMeshComponent.h"
#include "EngineUtils.h"
#include "Editor.h"

namespace {
FUnrealEngineMCPResponse Ok(const FUnrealEngineMCPRequest& R, TSharedPtr<FJsonObject> O){return FUnrealEngineMCPResultSerializer::Ok(R.Id,O);} 
FUnrealEngineMCPResponse Fail(const FUnrealEngineMCPRequest& R,const FString& C,const FString& M){return FUnrealEngineMCPResultSerializer::Fail(R.Id,C,M);} 
}

void FUnrealEngineMCPMaterialTools::Register()
{
	auto& Reg = FUnrealEngineMCPToolRegistry::Get();
	Reg.Register(TEXT("unreal_create_material"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req){
		TSharedPtr<FJsonObject> Params=Req.Params;
		auto Result=FUnrealEngineMCPGameThreadDispatcher::RunJson([Params](){
			TSharedPtr<FJsonObject> Obj=MakeShared<FJsonObject>();
			FString Path=Params->GetStringField(TEXT("path"));
			UMaterialFactoryNew* Factory=NewObject<UMaterialFactoryNew>();
			IAssetTools& AT=FModuleManager::LoadModuleChecked<FAssetToolsModule>("AssetTools").Get();
			UObject* Created=AT.CreateAsset(FPackageName::GetShortName(Path), FPackageName::GetLongPackagePath(Path), UMaterial::StaticClass(), Factory);
			if(!Created){Obj->SetStringField(TEXT("error"),TEXT("Failed to create material")); return Obj;}
			Obj->SetStringField(TEXT("path"), Created->GetPathName());
			return Obj;
		});
		if(Result->HasField(TEXT("error"))) return Fail(Req,TEXT("engine_error"),Result->GetStringField(TEXT("error")));
		return Ok(Req,Result);
	}), TEXT("Create a material asset."));

	Reg.Register(TEXT("unreal_create_material_instance"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req){
		TSharedPtr<FJsonObject> Params=Req.Params;
		auto Result=FUnrealEngineMCPGameThreadDispatcher::RunJson([Params](){
			TSharedPtr<FJsonObject> Obj=MakeShared<FJsonObject>();
			FString Path=Params->GetStringField(TEXT("path"));
			FString Parent=Params->GetStringField(TEXT("parent"));
			UMaterialInterface* ParentMat=LoadObject<UMaterialInterface>(nullptr,*Parent);
			if(!ParentMat){Obj->SetStringField(TEXT("error"),TEXT("Parent material not found")); return Obj;}
			UMaterialInstanceConstantFactoryNew* Factory=NewObject<UMaterialInstanceConstantFactoryNew>();
			Factory->InitialParent=ParentMat;
			IAssetTools& AT=FModuleManager::LoadModuleChecked<FAssetToolsModule>("AssetTools").Get();
			UObject* Created=AT.CreateAsset(FPackageName::GetShortName(Path), FPackageName::GetLongPackagePath(Path), UMaterialInstanceConstant::StaticClass(), Factory);
			if(!Created){Obj->SetStringField(TEXT("error"),TEXT("Failed to create material instance")); return Obj;}
			Obj->SetStringField(TEXT("path"), Created->GetPathName());
			return Obj;
		});
		if(Result->HasField(TEXT("error"))) return Fail(Req,TEXT("engine_error"),Result->GetStringField(TEXT("error")));
		return Ok(Req,Result);
	}), TEXT("Create a material instance."));

	Reg.Register(TEXT("unreal_get_material"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req){
		TSharedPtr<FJsonObject> Params=Req.Params;
		auto Result=FUnrealEngineMCPGameThreadDispatcher::RunJson([Params](){
			TSharedPtr<FJsonObject> Obj=MakeShared<FJsonObject>();
			UMaterialInterface* Mat=LoadObject<UMaterialInterface>(nullptr,*Params->GetStringField(TEXT("path")));
			if(!Mat){Obj->SetStringField(TEXT("error"),TEXT("Material not found")); return Obj;}
			Obj->SetStringField(TEXT("path"), Mat->GetPathName());
			Obj->SetStringField(TEXT("name"), Mat->GetName());
			Obj->SetStringField(TEXT("class"), Mat->GetClass()->GetName());
			return Obj;
		});
		if(Result->HasField(TEXT("error"))) return Fail(Req,TEXT("engine_error"),Result->GetStringField(TEXT("error")));
		return Ok(Req,Result);
	}), TEXT("Get material details."));

	Reg.Register(TEXT("unreal_get_material_parameters"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req){
		TSharedPtr<FJsonObject> Params=Req.Params;
		auto Result=FUnrealEngineMCPGameThreadDispatcher::RunJson([Params](){
			TSharedPtr<FJsonObject> Obj=MakeShared<FJsonObject>();
			UMaterialInterface* Mat=LoadObject<UMaterialInterface>(nullptr,*Params->GetStringField(TEXT("path")));
			if(!Mat){Obj->SetStringField(TEXT("error"),TEXT("Material not found")); return Obj;}
			TArray<FMaterialParameterInfo> Infos; TArray<FGuid> Ids;
			TArray<TSharedPtr<FJsonValue>> ParamsOut;
			Mat->GetAllScalarParameterInfo(Infos, Ids);
			for(const FMaterialParameterInfo& Info: Infos){ TSharedPtr<FJsonObject> P=MakeShared<FJsonObject>(); P->SetStringField(TEXT("name"), Info.Name.ToString()); P->SetStringField(TEXT("type"), TEXT("scalar")); ParamsOut.Add(MakeShared<FJsonValueObject>(P)); }
			Infos.Reset(); Ids.Reset(); Mat->GetAllVectorParameterInfo(Infos, Ids);
			for(const FMaterialParameterInfo& Info: Infos){ TSharedPtr<FJsonObject> P=MakeShared<FJsonObject>(); P->SetStringField(TEXT("name"), Info.Name.ToString()); P->SetStringField(TEXT("type"), TEXT("vector")); ParamsOut.Add(MakeShared<FJsonValueObject>(P)); }
			Obj->SetArrayField(TEXT("parameters"), ParamsOut);
			return Obj;
		});
		if(Result->HasField(TEXT("error"))) return Fail(Req,TEXT("engine_error"),Result->GetStringField(TEXT("error")));
		return Ok(Req,Result);
	}), TEXT("List material parameters."));

	Reg.Register(TEXT("unreal_set_material_parameter"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req){
		TSharedPtr<FJsonObject> Params=Req.Params;
		auto Result=FUnrealEngineMCPGameThreadDispatcher::RunJson([Params](){
			TSharedPtr<FJsonObject> Obj=MakeShared<FJsonObject>();
			UMaterialInstanceConstant* MIC=LoadObject<UMaterialInstanceConstant>(nullptr,*Params->GetStringField(TEXT("path")));
			if(!MIC){Obj->SetStringField(TEXT("error"),TEXT("Material instance not found")); return Obj;}
			FString Name=Params->GetStringField(TEXT("name"));
			FString Type=Params->HasField(TEXT("type"))?Params->GetStringField(TEXT("type")):TEXT("scalar");
			if(Type.Equals(TEXT("scalar"), ESearchCase::IgnoreCase))
			{
				MIC->SetScalarParameterValueEditorOnly(FName(*Name), Params->GetNumberField(TEXT("value")));
			}
			else
			{
				FLinearColor Color(1,1,1,1);
				if(Params->HasTypedField<EJson::Object>(TEXT("value")))
				{
					auto V=Params->GetObjectField(TEXT("value"));
					Color.R=V->GetNumberField(TEXT("r")); Color.G=V->GetNumberField(TEXT("g")); Color.B=V->GetNumberField(TEXT("b"));
					if(V->HasField(TEXT("a"))) Color.A=V->GetNumberField(TEXT("a"));
				}
				MIC->SetVectorParameterValueEditorOnly(FName(*Name), Color);
			}
			MIC->MarkPackageDirty();
			Obj->SetBoolField(TEXT("updated"), true);
			return Obj;
		});
		if(Result->HasField(TEXT("error"))) return Fail(Req,TEXT("engine_error"),Result->GetStringField(TEXT("error")));
		return Ok(Req,Result);
	}), TEXT("Set a material instance parameter."));

	Reg.Register(TEXT("unreal_assign_material"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req){
		TSharedPtr<FJsonObject> Params=Req.Params;
		auto Result=FUnrealEngineMCPGameThreadDispatcher::RunJson([Params](){
			TSharedPtr<FJsonObject> Obj=MakeShared<FJsonObject>();
			UWorld* World=GEditor?GEditor->GetEditorWorldContext().World():nullptr;
			AActor* Actor=nullptr;
			FString Name=Params->GetStringField(TEXT("actor"));
			for(TActorIterator<AActor> It(World); It; ++It){ if((*It)->GetName().Equals(Name,ESearchCase::IgnoreCase)||(*It)->GetActorLabel().Equals(Name,ESearchCase::IgnoreCase)){Actor=*It; break;}}
			if(!Actor){Obj->SetStringField(TEXT("error"),TEXT("Actor not found")); return Obj;}
			UMaterialInterface* Mat=LoadObject<UMaterialInterface>(nullptr,*Params->GetStringField(TEXT("material")));
			if(!Mat){Obj->SetStringField(TEXT("error"),TEXT("Material not found")); return Obj;}
			int32 Slot=Params->HasField(TEXT("slot"))? (int32)Params->GetNumberField(TEXT("slot")):0;
			if(UStaticMeshComponent* SMC=Actor->FindComponentByClass<UStaticMeshComponent>())
			{
				SMC->SetMaterial(Slot, Mat);
				Actor->MarkPackageDirty();
				Obj->SetBoolField(TEXT("assigned"), true);
				return Obj;
			}
			Obj->SetStringField(TEXT("error"),TEXT("No StaticMeshComponent"));
			return Obj;
		});
		if(Result->HasField(TEXT("error"))) return Fail(Req,TEXT("engine_error"),Result->GetStringField(TEXT("error")));
		return Ok(Req,Result);
	}), TEXT("Assign a material to a mesh component."));

	Reg.Register(TEXT("unreal_compile_material"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req){
		TSharedPtr<FJsonObject> Params=Req.Params;
		auto Result=FUnrealEngineMCPGameThreadDispatcher::RunJson([Params](){
			TSharedPtr<FJsonObject> Obj=MakeShared<FJsonObject>();
			UMaterial* Mat=LoadObject<UMaterial>(nullptr,*Params->GetStringField(TEXT("path")));
			if(!Mat){Obj->SetStringField(TEXT("error"),TEXT("Material not found")); return Obj;}
			Mat->PreEditChange(nullptr); Mat->PostEditChange();
			Obj->SetBoolField(TEXT("compiled"), true);
			return Obj;
		});
		if(Result->HasField(TEXT("error"))) return Fail(Req,TEXT("engine_error"),Result->GetStringField(TEXT("error")));
		return Ok(Req,Result);
	}), TEXT("Compile a material."));

	Reg.Register(TEXT("unreal_save_material"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req){
		TSharedPtr<FJsonObject> Params=Req.Params;
		auto Result=FUnrealEngineMCPGameThreadDispatcher::RunJson([Params](){
			TSharedPtr<FJsonObject> Obj=MakeShared<FJsonObject>();
			bool bOk=UEditorAssetLibrary::SaveAsset(Params->GetStringField(TEXT("path")));
			Obj->SetBoolField(TEXT("saved"), bOk);
			if(!bOk) Obj->SetStringField(TEXT("error"),TEXT("Save failed"));
			return Obj;
		});
		if(Result->HasField(TEXT("error"))) return Fail(Req,TEXT("engine_error"),Result->GetStringField(TEXT("error")));
		return Ok(Req,Result);
	}), TEXT("Save a material asset."));

	Reg.Register(TEXT("unreal_add_material_expression"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req){
		return Fail(Req, TEXT("unsupported"), TEXT("unreal_add_material_expression requires Material Editor graph APIs not fully exposed in this build"));
	}), TEXT("Add a material expression."));
	Reg.Register(TEXT("unreal_connect_material_nodes"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req){
		return Fail(Req, TEXT("unsupported"), TEXT("unreal_connect_material_nodes requires Material Editor graph APIs not fully exposed in this build"));
	}), TEXT("Connect material expressions."));
	Reg.Register(TEXT("unreal_disconnect_material_nodes"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req){
		return Fail(Req, TEXT("unsupported"), TEXT("unreal_disconnect_material_nodes requires Material Editor graph APIs not fully exposed in this build"));
	}), TEXT("Disconnect material expressions."));
	Reg.Register(TEXT("unreal_delete_material_expression"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req){
		return Fail(Req, TEXT("unsupported"), TEXT("unreal_delete_material_expression requires Material Editor graph APIs not fully exposed in this build"));
	}), TEXT("Delete a material expression."));
}
