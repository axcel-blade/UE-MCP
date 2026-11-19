#include "Tools/MeshTools.h"
#include "Core/ToolRegistry.h"
#include "Core/ResultSerializer.h"

void FUnrealEngineMCPMeshTools::Register()
{
	auto& Reg = FUnrealEngineMCPToolRegistry::Get();

	Reg.Register(TEXT("unreal_get_mesh_info"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		return FUnrealEngineMCPResultSerializer::Fail(Req.Id, TEXT("unsupported"), TEXT("unreal_get_mesh_info is not implemented in this build"));
	}), TEXT("Get static mesh info."));
	Reg.Register(TEXT("unreal_create_static_mesh"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		return FUnrealEngineMCPResultSerializer::Fail(Req.Id, TEXT("unsupported"), TEXT("unreal_create_static_mesh is not implemented in this build"));
	}), TEXT("Create a basic static mesh asset where supported."));
	Reg.Register(TEXT("unreal_get_mesh_bounds"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		return FUnrealEngineMCPResultSerializer::Fail(Req.Id, TEXT("unsupported"), TEXT("unreal_get_mesh_bounds is not implemented in this build"));
	}), TEXT("Get mesh bounds."));
	Reg.Register(TEXT("unreal_get_mesh_sections"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		return FUnrealEngineMCPResultSerializer::Fail(Req.Id, TEXT("unsupported"), TEXT("unreal_get_mesh_sections is not implemented in this build"));
	}), TEXT("Get mesh sections."));
	Reg.Register(TEXT("unreal_get_mesh_materials"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		return FUnrealEngineMCPResultSerializer::Fail(Req.Id, TEXT("unsupported"), TEXT("unreal_get_mesh_materials is not implemented in this build"));
	}), TEXT("Get mesh materials."));
	Reg.Register(TEXT("unreal_set_mesh_material"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		return FUnrealEngineMCPResultSerializer::Fail(Req.Id, TEXT("unsupported"), TEXT("unreal_set_mesh_material is not implemented in this build"));
	}), TEXT("Set a mesh material slot."));
	Reg.Register(TEXT("unreal_generate_collision"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		return FUnrealEngineMCPResultSerializer::Fail(Req.Id, TEXT("unsupported"), TEXT("unreal_generate_collision is not implemented in this build"));
	}), TEXT("Generate mesh collision."));
	Reg.Register(TEXT("unreal_get_collision_info"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		return FUnrealEngineMCPResultSerializer::Fail(Req.Id, TEXT("unsupported"), TEXT("unreal_get_collision_info is not implemented in this build"));
	}), TEXT("Get mesh collision info."));
	Reg.Register(TEXT("unreal_set_mesh_lod"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		return FUnrealEngineMCPResultSerializer::Fail(Req.Id, TEXT("unsupported"), TEXT("unreal_set_mesh_lod is not implemented in this build"));
	}), TEXT("Configure mesh LOD settings."));
	Reg.Register(TEXT("unreal_get_skeletal_mesh_info"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		return FUnrealEngineMCPResultSerializer::Fail(Req.Id, TEXT("unsupported"), TEXT("unreal_get_skeletal_mesh_info is not implemented in this build"));
	}), TEXT("Get skeletal mesh info."));
	Reg.Register(TEXT("unreal_get_skeleton_info"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		return FUnrealEngineMCPResultSerializer::Fail(Req.Id, TEXT("unsupported"), TEXT("unreal_get_skeleton_info is not implemented in this build"));
	}), TEXT("Get skeleton info."));
	Reg.Register(TEXT("unreal_get_bone_hierarchy"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		return FUnrealEngineMCPResultSerializer::Fail(Req.Id, TEXT("unsupported"), TEXT("unreal_get_bone_hierarchy is not implemented in this build"));
	}), TEXT("Get bone hierarchy."));
	Reg.Register(TEXT("unreal_set_mesh_collision"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		return FUnrealEngineMCPResultSerializer::Fail(Req.Id, TEXT("unsupported"), TEXT("unreal_set_mesh_collision is not implemented in this build"));
	}), TEXT("Set mesh collision profile/settings."));
}
