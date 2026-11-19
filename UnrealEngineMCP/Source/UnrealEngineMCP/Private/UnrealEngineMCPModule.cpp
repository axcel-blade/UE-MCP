#include "UnrealEngineMCPModule.h"
#include "UnrealEngineMCPSettings.h"
#include "Bridge/TCPServer.h"
#include "Tools/ToolRegistration.h"
#include "Core/ErrorHandler.h"
#include "Modules/ModuleManager.h"

#define LOCTEXT_NAMESPACE "FUnrealEngineMCPModule"

void FUnrealEngineMCPModule::StartupModule()
{
	FUnrealEngineMCPErrorHandler::LogInfo(TEXT("UnrealEngineMCP module starting"));
	RegisterUnrealEngineMCPTools();

	const UUnrealEngineMCPSettings* Settings = GetDefault<UUnrealEngineMCPSettings>();
	BridgeServer = MakeShared<FUnrealEngineMCPBridgeServer>();
	if (Settings && Settings->bAutoStart)
	{
		if (!BridgeServer->Start(Settings->BindAddress, Settings->Port))
		{
			FUnrealEngineMCPErrorHandler::LogError(TEXT("Failed to start UnrealEngineMCP TCP bridge"));
		}
		else
		{
			FUnrealEngineMCPErrorHandler::LogInfo(FString::Printf(TEXT("UnrealEngineMCP bridge listening on %s:%d"), *Settings->BindAddress, Settings->Port));
		}
	}
}

void FUnrealEngineMCPModule::ShutdownModule()
{
	if (BridgeServer.IsValid())
	{
		BridgeServer->Stop();
		BridgeServer.Reset();
	}
	FUnrealEngineMCPErrorHandler::LogInfo(TEXT("UnrealEngineMCP module shut down"));
}

FUnrealEngineMCPModule& FUnrealEngineMCPModule::Get()
{
	return FModuleManager::LoadModuleChecked<FUnrealEngineMCPModule>("UnrealEngineMCP");
}

IMPLEMENT_MODULE(FUnrealEngineMCPModule, UnrealEngineMCP)
#undef LOCTEXT_NAMESPACE
