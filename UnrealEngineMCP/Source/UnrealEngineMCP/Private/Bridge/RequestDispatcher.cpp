#include "Bridge/RequestDispatcher.h"
#include "Core/ToolRegistry.h"
#include "Core/ResultSerializer.h"
#include "UnrealEngineMCPSettings.h"
#include "HAL/PlatformTime.h"

FUnrealEngineMCPResponse FUnrealEngineMCPRequestDispatcher::Dispatch(const FUnrealEngineMCPRequest& Request)
{
	const double Start = FPlatformTime::Seconds();
	const UUnrealEngineMCPSettings* Settings = GetDefault<UUnrealEngineMCPSettings>();
	if (Settings && !Settings->AuthToken.IsEmpty())
	{
		if (Request.Auth != Settings->AuthToken)
		{
			return FUnrealEngineMCPResultSerializer::Fail(Request.Id, TEXT("auth_failed"), TEXT("Invalid auth token"));
		}
	}

	FUnrealEngineMCPResponse Response = FUnrealEngineMCPToolRegistry::Get().Execute(Request);
	Response.DurationMs = (FPlatformTime::Seconds() - Start) * 1000.0;
	if (Response.Id.IsEmpty())
	{
		Response.Id = Request.Id;
	}
	return Response;
}
