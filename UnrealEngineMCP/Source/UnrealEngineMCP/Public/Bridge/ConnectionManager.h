#pragma once

#include "CoreMinimal.h"

class FUnrealEngineMCPConnectionManager
{
public:
	void OnClientConnected();
	void OnClientDisconnected();
	int32 GetClientCount() const;

private:
	mutable FCriticalSection Mutex;
	int32 ClientCount = 0;
};
