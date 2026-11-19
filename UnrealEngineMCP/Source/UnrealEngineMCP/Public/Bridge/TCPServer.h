#pragma once

#include "CoreMinimal.h"
#include "HAL/Runnable.h"
#include "HAL/RunnableThread.h"
#include "HAL/CriticalSection.h"
#include "Sockets.h"
#include "Bridge/MessageProtocol.h"

class FUnrealEngineMCPBridgeServer;

/**
 * Accept loop for the UnrealEngineMCP TCP bridge.
 * Each accepted client is handled on its own thread so concurrent MCP
 * clients (and persistent connections with multiple requests) work reliably.
 */
class FUnrealEngineMCPTCPServerRunnable : public FRunnable
{
public:
	FUnrealEngineMCPTCPServerRunnable(FUnrealEngineMCPBridgeServer* InOwner, TSharedPtr<FSocket> InListener);
	virtual ~FUnrealEngineMCPTCPServerRunnable() override;

	virtual bool Init() override;
	virtual uint32 Run() override;
	virtual void Stop() override;

	/** Block until in-flight client workers have finished (after Stop). */
	void WaitForClients();

	void HandleClient(TSharedPtr<FSocket> ClientSocket);

private:
	bool ReadExact(FSocket* Socket, uint8* Buffer, int32 Length) const;
	bool SendAll(FSocket* Socket, const TArray<uint8>& Data) const;

	FUnrealEngineMCPBridgeServer* Owner;
	TSharedPtr<FSocket> ListenerSocket;
	TAtomic<bool> bStopping;
	TAtomic<int32> ActiveClients;
};

class FUnrealEngineMCPBridgeServer
{
public:
	FUnrealEngineMCPBridgeServer();
	~FUnrealEngineMCPBridgeServer();

	bool Start(const FString& Host, int32 Port);
	void Stop();
	bool IsRunning() const { return bRunning; }
	FString GetHost() const { return Host; }
	int32 GetPort() const { return Port; }

	FUnrealEngineMCPResponse ProcessRequest(const FUnrealEngineMCPRequest& Request);

private:
	FString Host;
	int32 Port = 55557;
	bool bRunning = false;
	TSharedPtr<FSocket> ListenerSocket;
	FRunnableThread* Thread = nullptr;
	FUnrealEngineMCPTCPServerRunnable* Runnable = nullptr;
};
