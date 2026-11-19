#include "Tools/SequencerTools.h"
#include "Core/ToolRegistry.h"
#include "Core/ResultSerializer.h"

void FUnrealEngineMCPSequencerTools::Register()
{
	auto& Reg = FUnrealEngineMCPToolRegistry::Get();

	Reg.Register(TEXT("unreal_create_level_sequence"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		return FUnrealEngineMCPResultSerializer::Fail(Req.Id, TEXT("unsupported"), TEXT("unreal_create_level_sequence is not implemented in this build"));
	}), TEXT("Create a Level Sequence."));
	Reg.Register(TEXT("unreal_get_level_sequences"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		return FUnrealEngineMCPResultSerializer::Fail(Req.Id, TEXT("unsupported"), TEXT("unreal_get_level_sequences is not implemented in this build"));
	}), TEXT("List Level Sequences."));
	Reg.Register(TEXT("unreal_add_sequence_track"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		return FUnrealEngineMCPResultSerializer::Fail(Req.Id, TEXT("unsupported"), TEXT("unreal_add_sequence_track is not implemented in this build"));
	}), TEXT("Add a sequence track."));
	Reg.Register(TEXT("unreal_add_sequence_section"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		return FUnrealEngineMCPResultSerializer::Fail(Req.Id, TEXT("unsupported"), TEXT("unreal_add_sequence_section is not implemented in this build"));
	}), TEXT("Add a sequence section."));
	Reg.Register(TEXT("unreal_add_camera"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		return FUnrealEngineMCPResultSerializer::Fail(Req.Id, TEXT("unsupported"), TEXT("unreal_add_camera is not implemented in this build"));
	}), TEXT("Add a camera to the level/sequence."));
	Reg.Register(TEXT("unreal_add_camera_cut"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		return FUnrealEngineMCPResultSerializer::Fail(Req.Id, TEXT("unsupported"), TEXT("unreal_add_camera_cut is not implemented in this build"));
	}), TEXT("Add a camera cut."));
	Reg.Register(TEXT("unreal_set_sequence_duration"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		return FUnrealEngineMCPResultSerializer::Fail(Req.Id, TEXT("unsupported"), TEXT("unreal_set_sequence_duration is not implemented in this build"));
	}), TEXT("Set sequence duration."));
	Reg.Register(TEXT("unreal_set_keyframe"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		return FUnrealEngineMCPResultSerializer::Fail(Req.Id, TEXT("unsupported"), TEXT("unreal_set_keyframe is not implemented in this build"));
	}), TEXT("Set a transform/property keyframe."));
	Reg.Register(TEXT("unreal_get_sequence_info"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		return FUnrealEngineMCPResultSerializer::Fail(Req.Id, TEXT("unsupported"), TEXT("unreal_get_sequence_info is not implemented in this build"));
	}), TEXT("Get sequence info."));
	Reg.Register(TEXT("unreal_render_sequence"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		return FUnrealEngineMCPResultSerializer::Fail(Req.Id, TEXT("unsupported"), TEXT("unreal_render_sequence is not implemented in this build"));
	}), TEXT("Queue a sequence render/export."));
}
