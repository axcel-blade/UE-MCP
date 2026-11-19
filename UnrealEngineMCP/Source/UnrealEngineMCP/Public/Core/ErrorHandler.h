#pragma once

#include "CoreMinimal.h"

class FUnrealEngineMCPErrorHandler
{
public:
	static void LogInfo(const FString& Message);
	static void LogWarning(const FString& Message);
	static void LogError(const FString& Message);

	static TArray<FString> GetRecentLogs(int32 Limit = 100);
	static TArray<FString> GetRecentErrors(int32 Limit = 50);

private:
	static FCriticalSection Mutex;
	static TArray<FString> Logs;
	static TArray<FString> Errors;
};
