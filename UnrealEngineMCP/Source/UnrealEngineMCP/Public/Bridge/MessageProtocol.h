#pragma once

#include "CoreMinimal.h"
#include "Dom/JsonObject.h"

struct FUnrealEngineMCPRequest
{
	FString Id;
	FString Version;
	FString Method;
	TSharedPtr<FJsonObject> Params;
	FString Auth;
};

struct FUnrealEngineMCPResponse
{
	FString Id;
	bool bOk = true;
	TSharedPtr<FJsonObject> Result;
	FString ErrorCode;
	FString ErrorMessage;
	TSharedPtr<FJsonObject> ErrorDetails;
	double DurationMs = 0.0;
	FString AsyncJobId;
};

class FUnrealEngineMCPMessageProtocol
{
public:
	static constexpr uint32 MaxMessageBytes = 16u * 1024u * 1024u;
	static constexpr TCHAR ProtocolVersion[] = TEXT("1.0");

	static bool TryParseRequest(const TArray<uint8>& Body, FUnrealEngineMCPRequest& OutRequest, FString& OutError);
	static TArray<uint8> EncodeResponse(const FUnrealEngineMCPResponse& Response);
	static TArray<uint8> EncodeFrame(const TArray<uint8>& JsonBody);
	static bool TryReadLength(const uint8* Data, int32 Len, uint32& OutLength);
};
