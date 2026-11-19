#include "Core/ErrorHandler.h"

FCriticalSection FUnrealEngineMCPErrorHandler::Mutex;
TArray<FString> FUnrealEngineMCPErrorHandler::Logs;
TArray<FString> FUnrealEngineMCPErrorHandler::Errors;

void FUnrealEngineMCPErrorHandler::LogInfo(const FString& Message)
{
	UE_LOG(LogTemp, Display, TEXT("UnrealEngineMCP: %s"), *Message);
	FScopeLock Lock(&Mutex);
	Logs.Add(FString::Printf(TEXT("[INFO] %s"), *Message));
	if (Logs.Num() > 500) { Logs.RemoveAt(0, Logs.Num() - 500); }
}

void FUnrealEngineMCPErrorHandler::LogWarning(const FString& Message)
{
	UE_LOG(LogTemp, Warning, TEXT("UnrealEngineMCP: %s"), *Message);
	FScopeLock Lock(&Mutex);
	Logs.Add(FString::Printf(TEXT("[WARN] %s"), *Message));
	if (Logs.Num() > 500) { Logs.RemoveAt(0, Logs.Num() - 500); }
}

void FUnrealEngineMCPErrorHandler::LogError(const FString& Message)
{
	UE_LOG(LogTemp, Error, TEXT("UnrealEngineMCP: %s"), *Message);
	FScopeLock Lock(&Mutex);
	Logs.Add(FString::Printf(TEXT("[ERROR] %s"), *Message));
	Errors.Add(Message);
	if (Logs.Num() > 500) { Logs.RemoveAt(0, Logs.Num() - 500); }
	if (Errors.Num() > 200) { Errors.RemoveAt(0, Errors.Num() - 200); }
}

TArray<FString> FUnrealEngineMCPErrorHandler::GetRecentLogs(int32 Limit)
{
	FScopeLock Lock(&Mutex);
	const int32 Start = FMath::Max(0, Logs.Num() - Limit);
	TArray<FString> Out;
	for (int32 i = Start; i < Logs.Num(); ++i) { Out.Add(Logs[i]); }
	return Out;
}

TArray<FString> FUnrealEngineMCPErrorHandler::GetRecentErrors(int32 Limit)
{
	FScopeLock Lock(&Mutex);
	const int32 Start = FMath::Max(0, Errors.Num() - Limit);
	TArray<FString> Out;
	for (int32 i = Start; i < Errors.Num(); ++i) { Out.Add(Errors[i]); }
	return Out;
}
