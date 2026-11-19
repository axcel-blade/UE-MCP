#pragma once

#include "CoreMinimal.h"
#include "Dom/JsonObject.h"
#include "Bridge/MessageProtocol.h"

class FUnrealEngineMCPResultSerializer
{
public:
	static FUnrealEngineMCPResponse Ok(const FString& Id, TSharedPtr<FJsonObject> Result = nullptr, double DurationMs = 0.0);
	static FUnrealEngineMCPResponse Fail(const FString& Id, const FString& Code, const FString& Message,
		TSharedPtr<FJsonObject> Details = nullptr, double DurationMs = 0.0);

	static TSharedPtr<FJsonObject> Vector(const FVector& V);
	static TSharedPtr<FJsonObject> Rotator(const FRotator& R);
	static TSharedPtr<FJsonObject> Transform(const FTransform& T);
	static bool TryGetVector(const TSharedPtr<FJsonObject>& Obj, const FString& Field, FVector& Out);
	static bool TryGetRotator(const TSharedPtr<FJsonObject>& Obj, const FString& Field, FRotator& Out);
};
