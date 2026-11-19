#include "Core/ToolRegistry.h"
#include "Core/ResultSerializer.h"

FUnrealEngineMCPToolRegistry& FUnrealEngineMCPToolRegistry::Get()
{
	static FUnrealEngineMCPToolRegistry Instance;
	return Instance;
}

void FUnrealEngineMCPToolRegistry::Register(const FString& Method, FUnrealEngineMCPToolHandler Handler, const FString& Description)
{
	FEntry Entry;
	Entry.Handler = Handler;
	Entry.Description = Description;
	Tools.Add(Method, Entry);
}

bool FUnrealEngineMCPToolRegistry::IsRegistered(const FString& Method) const
{
	return Tools.Contains(Method);
}

FUnrealEngineMCPResponse FUnrealEngineMCPToolRegistry::Execute(const FUnrealEngineMCPRequest& Request) const
{
	const FEntry* Entry = Tools.Find(Request.Method);
	if (!Entry || !Entry->Handler.IsBound())
	{
		return FUnrealEngineMCPResultSerializer::Fail(Request.Id, TEXT("unsupported"), FString::Printf(TEXT("Unknown method: %s"), *Request.Method));
	}
	return Entry->Handler.Execute(Request);
}

TArray<TSharedPtr<FJsonValue>> FUnrealEngineMCPToolRegistry::ListTools() const
{
	TArray<TSharedPtr<FJsonValue>> Out;
	for (const TPair<FString, FEntry>& Pair : Tools)
	{
		TSharedPtr<FJsonObject> Obj = MakeShared<FJsonObject>();
		Obj->SetStringField(TEXT("name"), Pair.Key);
		Obj->SetStringField(TEXT("description"), Pair.Value.Description);
		Out.Add(MakeShared<FJsonValueObject>(Obj));
	}
	return Out;
}
