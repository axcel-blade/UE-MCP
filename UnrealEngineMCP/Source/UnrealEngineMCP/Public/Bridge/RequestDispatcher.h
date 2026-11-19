#pragma once

#include "CoreMinimal.h"
#include "Bridge/MessageProtocol.h"

class FUnrealEngineMCPRequestDispatcher
{
public:
	static FUnrealEngineMCPResponse Dispatch(const FUnrealEngineMCPRequest& Request);
};
