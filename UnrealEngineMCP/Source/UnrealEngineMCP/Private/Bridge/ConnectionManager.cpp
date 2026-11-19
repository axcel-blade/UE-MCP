#include "Bridge/ConnectionManager.h"

void FUnrealEngineMCPConnectionManager::OnClientConnected()
{
	FScopeLock Lock(&Mutex);
	++ClientCount;
}

void FUnrealEngineMCPConnectionManager::OnClientDisconnected()
{
	FScopeLock Lock(&Mutex);
	ClientCount = FMath::Max(0, ClientCount - 1);
}

int32 FUnrealEngineMCPConnectionManager::GetClientCount() const
{
	FScopeLock Lock(&Mutex);
	return ClientCount;
}
