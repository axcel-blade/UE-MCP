#pragma once

#include "CoreMinimal.h"
#include "HAL/Runnable.h"
#include "HAL/RunnableThread.h"
#include "Sockets.h"
#include "Bridge/MessageProtocol.h"

class FUnrealEngineMCPBridgeServer;

class FUnrealEngineMCPTCPServerRunnable : public FRunnable
{
public:
	FUnrealEngineMCPTCPServerRunnable(FUnrealEngineMCPBridgeServer* InOwner, TSharedPtr<FSocket> InListener);
	virtual ~FUnrealEngineMCPTCPServerRunnable() override;

	virtual bool Init() override;
	virtual uint32 Run() override;
	virtual void Stop() override;

private:
	void HandleClient(TSharedPtr<FSocket> ClientSocket);
	bool ReadExact(FSocket* Socket, uint8* Buffer, int32 Length);
	bool SendAll(FSocket* Socket, const TArray<uint8>& Data);

	FUnrealEngineMCPBridgeServer* Owner;
	TSharedPtr<FSocket> ListenerSocket;
	TAtomic<bool> bStopping;
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
