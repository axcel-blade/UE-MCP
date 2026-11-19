#include "Tools/NiagaraTools.h"
#include "Core/ToolRegistry.h"
#include "Core/ResultSerializer.h"

void FUnrealEngineMCPNiagaraTools::Register()
{
	auto& Reg = FUnrealEngineMCPToolRegistry::Get();

	Reg.Register(TEXT("unreal_list_niagara_systems"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		return FUnrealEngineMCPResultSerializer::Fail(Req.Id, TEXT("unsupported"), TEXT("unreal_list_niagara_systems is not implemented in this build"));
	}), TEXT("List Niagara systems."));
	Reg.Register(TEXT("unreal_get_niagara_info"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		return FUnrealEngineMCPResultSerializer::Fail(Req.Id, TEXT("unsupported"), TEXT("unreal_get_niagara_info is not implemented in this build"));
	}), TEXT("Get Niagara system info."));
	Reg.Register(TEXT("unreal_create_niagara_system"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		return FUnrealEngineMCPResultSerializer::Fail(Req.Id, TEXT("unsupported"), TEXT("unreal_create_niagara_system is not implemented in this build"));
	}), TEXT("Create a Niagara system asset."));
	Reg.Register(TEXT("unreal_spawn_niagara_system"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		return FUnrealEngineMCPResultSerializer::Fail(Req.Id, TEXT("unsupported"), TEXT("unreal_spawn_niagara_system is not implemented in this build"));
	}), TEXT("Spawn a Niagara actor."));
	Reg.Register(TEXT("unreal_set_niagara_parameter"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		return FUnrealEngineMCPResultSerializer::Fail(Req.Id, TEXT("unsupported"), TEXT("unreal_set_niagara_parameter is not implemented in this build"));
	}), TEXT("Set a Niagara user parameter."));
	Reg.Register(TEXT("unreal_get_niagara_parameters"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		return FUnrealEngineMCPResultSerializer::Fail(Req.Id, TEXT("unsupported"), TEXT("unreal_get_niagara_parameters is not implemented in this build"));
	}), TEXT("Get Niagara parameters."));
	Reg.Register(TEXT("unreal_save_niagara_system"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		return FUnrealEngineMCPResultSerializer::Fail(Req.Id, TEXT("unsupported"), TEXT("unreal_save_niagara_system is not implemented in this build"));
	}), TEXT("Save a Niagara system."));
}
