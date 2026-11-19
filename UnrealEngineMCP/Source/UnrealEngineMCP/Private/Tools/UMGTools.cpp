#include "Tools/UMGTools.h"
#include "Core/ToolRegistry.h"
#include "Core/ResultSerializer.h"

void FUnrealEngineMCPUMGTools::Register()
{
	auto& Reg = FUnrealEngineMCPToolRegistry::Get();

	Reg.Register(TEXT("unreal_create_widget_blueprint"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		return FUnrealEngineMCPResultSerializer::Fail(Req.Id, TEXT("unsupported"), TEXT("unreal_create_widget_blueprint is not implemented in this build"));
	}), TEXT("Create a UMG Widget Blueprint."));
	Reg.Register(TEXT("unreal_get_widget_tree"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		return FUnrealEngineMCPResultSerializer::Fail(Req.Id, TEXT("unsupported"), TEXT("unreal_get_widget_tree is not implemented in this build"));
	}), TEXT("Get widget tree hierarchy."));
	Reg.Register(TEXT("unreal_add_widget"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		return FUnrealEngineMCPResultSerializer::Fail(Req.Id, TEXT("unsupported"), TEXT("unreal_add_widget is not implemented in this build"));
	}), TEXT("Add a widget to a Widget Blueprint."));
	Reg.Register(TEXT("unreal_remove_widget"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		return FUnrealEngineMCPResultSerializer::Fail(Req.Id, TEXT("unsupported"), TEXT("unreal_remove_widget is not implemented in this build"));
	}), TEXT("Remove a widget."));
	Reg.Register(TEXT("unreal_set_widget_property"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		return FUnrealEngineMCPResultSerializer::Fail(Req.Id, TEXT("unsupported"), TEXT("unreal_set_widget_property is not implemented in this build"));
	}), TEXT("Set a widget property."));
	Reg.Register(TEXT("unreal_set_widget_position"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		return FUnrealEngineMCPResultSerializer::Fail(Req.Id, TEXT("unsupported"), TEXT("unreal_set_widget_position is not implemented in this build"));
	}), TEXT("Set widget position."));
	Reg.Register(TEXT("unreal_set_widget_size"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		return FUnrealEngineMCPResultSerializer::Fail(Req.Id, TEXT("unsupported"), TEXT("unreal_set_widget_size is not implemented in this build"));
	}), TEXT("Set widget size."));
	Reg.Register(TEXT("unreal_set_widget_text"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		return FUnrealEngineMCPResultSerializer::Fail(Req.Id, TEXT("unsupported"), TEXT("unreal_set_widget_text is not implemented in this build"));
	}), TEXT("Set widget text."));
	Reg.Register(TEXT("unreal_set_widget_color"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		return FUnrealEngineMCPResultSerializer::Fail(Req.Id, TEXT("unsupported"), TEXT("unreal_set_widget_color is not implemented in this build"));
	}), TEXT("Set widget color."));
	Reg.Register(TEXT("unreal_add_widget_to_viewport"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		return FUnrealEngineMCPResultSerializer::Fail(Req.Id, TEXT("unsupported"), TEXT("unreal_add_widget_to_viewport is not implemented in this build"));
	}), TEXT("Add a widget instance to the viewport."));
	Reg.Register(TEXT("unreal_get_widget_details"), FUnrealEngineMCPToolHandler::CreateLambda([](const FUnrealEngineMCPRequest& Req)
	{
		return FUnrealEngineMCPResultSerializer::Fail(Req.Id, TEXT("unsupported"), TEXT("unreal_get_widget_details is not implemented in this build"));
	}), TEXT("Get widget details."));
}
