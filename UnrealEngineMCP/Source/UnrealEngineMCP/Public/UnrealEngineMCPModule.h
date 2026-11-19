#pragma once

#include "CoreMinimal.h"
#include "Modules/ModuleManager.h"

class FUnrealEngineMCPBridgeServer;

class FUnrealEngineMCPModule : public IModuleInterface
{
public:
	virtual void StartupModule() override;
	virtual void ShutdownModule() override;

	static FUnrealEngineMCPModule& Get();
	TSharedPtr<FUnrealEngineMCPBridgeServer> GetBridge() const { return BridgeServer; }

private:
	TSharedPtr<FUnrealEngineMCPBridgeServer> BridgeServer;
};
