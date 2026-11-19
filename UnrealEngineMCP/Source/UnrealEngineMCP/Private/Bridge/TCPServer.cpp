#include "Bridge/TCPServer.h"
#include "Bridge/RequestDispatcher.h"
#include "Core/ErrorHandler.h"
#include "Sockets.h"
#include "SocketSubsystem.h"
#include "Interfaces/IPv4/IPv4Address.h"
#include "Interfaces/IPv4/IPv4Endpoint.h"
#include "HAL/RunnableThread.h"
#include "HAL/PlatformProcess.h"
#include "Async/Async.h"

FUnrealEngineMCPTCPServerRunnable::FUnrealEngineMCPTCPServerRunnable(FUnrealEngineMCPBridgeServer* InOwner, TSharedPtr<FSocket> InListener)
	: Owner(InOwner)
	, ListenerSocket(InListener)
	, bStopping(false)
	, ActiveClients(0)
{
}

FUnrealEngineMCPTCPServerRunnable::~FUnrealEngineMCPTCPServerRunnable() = default;

bool FUnrealEngineMCPTCPServerRunnable::Init()
{
	return ListenerSocket.IsValid();
}

uint32 FUnrealEngineMCPTCPServerRunnable::Run()
{
	while (!bStopping)
	{
		bool bPending = false;
		if (ListenerSocket.IsValid() && ListenerSocket->HasPendingConnection(bPending) && bPending)
		{
			TSharedPtr<FSocket> Client = MakeShareable(ListenerSocket->Accept(TEXT("UnrealEngineMCPClient")));
			if (Client.IsValid())
			{
				// Blocking I/O so ReadExact/SendAll wait for the peer instead of
				// treating "no data yet" as a disconnect between requests.
				Client->SetNonBlocking(false);
				Client->SetNoDelay(true);

				++ActiveClients;
				Async(EAsyncExecution::Thread, [this, Client]()
				{
					HandleClient(Client);
					--ActiveClients;
				});
			}
		}
		else
		{
			FPlatformProcess::Sleep(0.01f);
		}
	}
	return 0;
}

void FUnrealEngineMCPTCPServerRunnable::Stop()
{
	bStopping = true;
}

void FUnrealEngineMCPTCPServerRunnable::WaitForClients()
{
	const double Start = FPlatformTime::Seconds();
	while (ActiveClients.Load(EMemoryOrder::SequentiallyConsistent) > 0 && (FPlatformTime::Seconds() - Start) < 5.0)
	{
		FPlatformProcess::Sleep(0.01f);
	}
}

bool FUnrealEngineMCPTCPServerRunnable::ReadExact(FSocket* Socket, uint8* Buffer, int32 Length) const
{
	int32 Total = 0;
	while (Total < Length && !bStopping)
	{
		// Wait up to 100ms for readability so idle persistent connections stay open.
		if (!Socket->Wait(ESocketWaitConditions::WaitForRead, FTimespan::FromMilliseconds(100)))
		{
			continue;
		}

		int32 Read = 0;
		if (!Socket->Recv(Buffer + Total, Length - Total, Read) || Read <= 0)
		{
			return false;
		}
		Total += Read;
	}
	return Total == Length;
}

bool FUnrealEngineMCPTCPServerRunnable::SendAll(FSocket* Socket, const TArray<uint8>& Data) const
{
	int32 SentTotal = 0;
	while (SentTotal < Data.Num() && !bStopping)
	{
		int32 Sent = 0;
		if (!Socket->Send(Data.GetData() + SentTotal, Data.Num() - SentTotal, Sent) || Sent <= 0)
		{
			return false;
		}
		SentTotal += Sent;
	}
	return SentTotal == Data.Num();
}

void FUnrealEngineMCPTCPServerRunnable::HandleClient(TSharedPtr<FSocket> ClientSocket)
{
	FUnrealEngineMCPErrorHandler::LogInfo(TEXT("MCP client connected"));
	while (!bStopping && ClientSocket.IsValid())
	{
		uint8 LengthBytes[4];
		if (!ReadExact(ClientSocket.Get(), LengthBytes, 4))
		{
			break;
		}

		uint32 BodyLength = 0;
		if (!FUnrealEngineMCPMessageProtocol::TryReadLength(LengthBytes, 4, BodyLength))
		{
			FUnrealEngineMCPErrorHandler::LogError(TEXT("Invalid frame length"));
			break;
		}

		TArray<uint8> Body;
		Body.SetNumUninitialized(static_cast<int32>(BodyLength));
		if (!ReadExact(ClientSocket.Get(), Body.GetData(), static_cast<int32>(BodyLength)))
		{
			break;
		}

		FUnrealEngineMCPRequest Request;
		FString ParseError;
		FUnrealEngineMCPResponse Response;
		if (!FUnrealEngineMCPMessageProtocol::TryParseRequest(Body, Request, ParseError))
		{
			Response.Id = TEXT("");
			Response.bOk = false;
			Response.ErrorCode = TEXT("protocol_error");
			Response.ErrorMessage = ParseError;
		}
		else
		{
			Response = Owner->ProcessRequest(Request);
		}

		const TArray<uint8> Frame = FUnrealEngineMCPMessageProtocol::EncodeResponse(Response);
		if (!SendAll(ClientSocket.Get(), Frame))
		{
			break;
		}
	}

	if (ClientSocket.IsValid())
	{
		ClientSocket->Close();
	}
	FUnrealEngineMCPErrorHandler::LogInfo(TEXT("MCP client disconnected"));
}

FUnrealEngineMCPBridgeServer::FUnrealEngineMCPBridgeServer() = default;

FUnrealEngineMCPBridgeServer::~FUnrealEngineMCPBridgeServer()
{
	Stop();
}

bool FUnrealEngineMCPBridgeServer::Start(const FString& InHost, int32 InPort)
{
	if (bRunning)
	{
		return true;
	}

	Host = InHost;
	Port = InPort;

	ISocketSubsystem* Sockets = ISocketSubsystem::Get(PLATFORM_SOCKETSUBSYSTEM);
	if (!Sockets)
	{
		return false;
	}

	FIPv4Address Address;
	if (!FIPv4Address::Parse(Host, Address))
	{
		Address = FIPv4Address::InternalLoopback;
	}

	TSharedRef<FInternetAddr> Addr = Sockets->CreateInternetAddr();
	Addr->SetIp(Address.Value);
	Addr->SetPort(Port);

	ListenerSocket = MakeShareable(Sockets->CreateSocket(NAME_Stream, TEXT("UnrealEngineMCPListener"), false));
	if (!ListenerSocket.IsValid())
	{
		return false;
	}

	ListenerSocket->SetReuseAddr(true);
	ListenerSocket->SetNonBlocking(true);
	if (!ListenerSocket->Bind(*Addr) || !ListenerSocket->Listen(16))
	{
		ListenerSocket->Close();
		ListenerSocket.Reset();
		return false;
	}

	Runnable = new FUnrealEngineMCPTCPServerRunnable(this, ListenerSocket);
	Thread = FRunnableThread::Create(Runnable, TEXT("UnrealEngineMCPBridge"), 0, TPri_Normal);
	bRunning = Thread != nullptr;
	return bRunning;
}

void FUnrealEngineMCPBridgeServer::Stop()
{
	if (Runnable)
	{
		Runnable->Stop();
	}
	if (ListenerSocket.IsValid())
	{
		ListenerSocket->Close();
		ListenerSocket.Reset();
	}
	if (Runnable)
	{
		Runnable->WaitForClients();
	}
	if (Thread)
	{
		Thread->WaitForCompletion();
		delete Thread;
		Thread = nullptr;
	}
	if (Runnable)
	{
		delete Runnable;
		Runnable = nullptr;
	}
	bRunning = false;
}

FUnrealEngineMCPResponse FUnrealEngineMCPBridgeServer::ProcessRequest(const FUnrealEngineMCPRequest& Request)
{
	return FUnrealEngineMCPRequestDispatcher::Dispatch(Request);
}
