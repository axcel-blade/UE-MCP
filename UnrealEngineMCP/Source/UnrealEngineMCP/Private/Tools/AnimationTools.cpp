#include "Tools/AnimationTools.h"
#include "Core/ToolRegistry.h"
#include "Core/ResultSerializer.h"

void FUnrealEngineMCPAnimationTools::Register()
{
	auto& Reg = FUnrealEngineMCPToolRegistry::Get();

	Reg.Register(TEXT("unreal_list_animations"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		return FUnrealEngineMCPResultSerializer::Fail(Req.Id, TEXT("unsupported"), TEXT("unreal_list_animations is not implemented in this build"));
	}), TEXT("List animation sequences."));
	Reg.Register(TEXT("unreal_get_animation_info"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		return FUnrealEngineMCPResultSerializer::Fail(Req.Id, TEXT("unsupported"), TEXT("unreal_get_animation_info is not implemented in this build"));
	}), TEXT("Get animation sequence info."));
	Reg.Register(TEXT("unreal_create_animation_blueprint"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		return FUnrealEngineMCPResultSerializer::Fail(Req.Id, TEXT("unsupported"), TEXT("unreal_create_animation_blueprint is not implemented in this build"));
	}), TEXT("Create an Animation Blueprint."));
	Reg.Register(TEXT("unreal_get_animation_blueprint"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		return FUnrealEngineMCPResultSerializer::Fail(Req.Id, TEXT("unsupported"), TEXT("unreal_get_animation_blueprint is not implemented in this build"));
	}), TEXT("Get Animation Blueprint info."));
	Reg.Register(TEXT("unreal_create_animation_montage"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		return FUnrealEngineMCPResultSerializer::Fail(Req.Id, TEXT("unsupported"), TEXT("unreal_create_animation_montage is not implemented in this build"));
	}), TEXT("Create an animation montage."));
	Reg.Register(TEXT("unreal_set_animation_sequence"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		return FUnrealEngineMCPResultSerializer::Fail(Req.Id, TEXT("unsupported"), TEXT("unreal_set_animation_sequence is not implemented in this build"));
	}), TEXT("Set montage/sequence references."));
	Reg.Register(TEXT("unreal_get_animation_notifies"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		return FUnrealEngineMCPResultSerializer::Fail(Req.Id, TEXT("unsupported"), TEXT("unreal_get_animation_notifies is not implemented in this build"));
	}), TEXT("Get animation notifies."));
	Reg.Register(TEXT("unreal_add_animation_notify"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		return FUnrealEngineMCPResultSerializer::Fail(Req.Id, TEXT("unsupported"), TEXT("unreal_add_animation_notify is not implemented in this build"));
	}), TEXT("Add an animation notify."));
	Reg.Register(TEXT("unreal_get_skeleton_assets"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		return FUnrealEngineMCPResultSerializer::Fail(Req.Id, TEXT("unsupported"), TEXT("unreal_get_skeleton_assets is not implemented in this build"));
	}), TEXT("List skeleton assets."));
	Reg.Register(TEXT("unreal_get_animation_graph"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		return FUnrealEngineMCPResultSerializer::Fail(Req.Id, TEXT("unsupported"), TEXT("unreal_get_animation_graph is not implemented in this build"));
	}), TEXT("Inspect animation graph nodes."));
}
