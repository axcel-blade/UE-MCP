#pragma once

#include "CoreMinimal.h"
#include "Bridge/MessageProtocol.h"

DECLARE_DELEGATE_RetVal_OneParam(FUnrealEngineMCPResponse, FUnrealEngineMCPToolHandler, const FUnrealEngineMCPRequest&);

class FUnrealEngineMCPToolRegistry
{
public:
	static FUnrealEngineMCPToolRegistry& Get();

	void Register(const FString& Method, FUnrealEngineMCPToolHandler Handler, const FString& Description);
	bool IsRegistered(const FString& Method) const;
	FUnrealEngineMCPResponse Execute(const FUnrealEngineMCPRequest& Request) const;
	TArray<TSharedPtr<FJsonValue>> ListTools() const;

private:
	struct FEntry
	{
		FUnrealEngineMCPToolHandler Handler;
		FString Description;
	};

	TMap<FString, FEntry> Tools;
};
