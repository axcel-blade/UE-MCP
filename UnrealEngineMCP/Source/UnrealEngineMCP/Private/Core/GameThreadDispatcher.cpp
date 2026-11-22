#include "Core/GameThreadDispatcher.h"
#include "Async/Async.h"
#include "HAL/PlatformProcess.h"
#include "Containers/Ticker.h"

void FUnrealEngineMCPGameThreadDispatcher::RunAndWait(TFunction<void()> Func, float TimeoutSeconds)
{
	TPromise<bool> Promise;
	TFuture<bool> Future = Promise.GetFuture();
	TSharedRef<TPromise<bool>, ESPMode::ThreadSafe> Shared = MakeShared<TPromise<bool>, ESPMode::ThreadSafe>(MoveTemp(Promise));

	AsyncTask(ENamedThreads::GameThread, [Shared, Func]()
	{
		Func();
		Shared->SetValue(true);
	});

	const double Start = FPlatformTime::Seconds();
	while (!Future.IsReady())
	{
		if ((FPlatformTime::Seconds() - Start) > TimeoutSeconds)
		{
			return;
		}
		FPlatformProcess::Sleep(0.001f);
	}
	Future.Get();
}

TSharedPtr<FJsonObject> FUnrealEngineMCPGameThreadDispatcher::RunJson(TFunction<TSharedPtr<FJsonObject>()> Func, float TimeoutSeconds)
{
	TPromise<TSharedPtr<FJsonObject>> Promise;
	TFuture<TSharedPtr<FJsonObject>> Future = Promise.GetFuture();
	TSharedRef<TPromise<TSharedPtr<FJsonObject>>, ESPMode::ThreadSafe> Shared =
		MakeShared<TPromise<TSharedPtr<FJsonObject>>, ESPMode::ThreadSafe>(MoveTemp(Promise));

	AsyncTask(ENamedThreads::GameThread, [Shared, Func]()
	{
		Shared->SetValue(Func());
	});

	const double Start = FPlatformTime::Seconds();
	while (!Future.IsReady())
	{
		if ((FPlatformTime::Seconds() - Start) > TimeoutSeconds)
		{
			TSharedPtr<FJsonObject> Err = MakeShared<FJsonObject>();
			Err->SetBoolField(TEXT("ok"), false);
			Err->SetStringField(TEXT("error"), TEXT("GameThread dispatch timed out"));
			return Err;
		}
		FPlatformProcess::Sleep(0.001f);
	}
	return Future.Get();
}

TSharedPtr<FJsonObject> FUnrealEngineMCPGameThreadDispatcher::RunJsonOnTicker(TFunction<TSharedPtr<FJsonObject>()> Func, float TimeoutSeconds)
{
	TPromise<TSharedPtr<FJsonObject>> Promise;
	TFuture<TSharedPtr<FJsonObject>> Future = Promise.GetFuture();
	TSharedRef<TPromise<TSharedPtr<FJsonObject>>, ESPMode::ThreadSafe> Shared =
		MakeShared<TPromise<TSharedPtr<FJsonObject>>, ESPMode::ThreadSafe>(MoveTemp(Promise));

	// Registering a ticker must happen on the game thread.
	AsyncTask(ENamedThreads::GameThread, [Shared, Func]()
	{
		FTSTicker::GetCoreTicker().AddTicker(FTickerDelegate::CreateLambda([Shared, Func](float)
		{
			Shared->SetValue(Func());
			return false; // one-shot
		}));
	});

	const double Start = FPlatformTime::Seconds();
	while (!Future.IsReady())
	{
		if ((FPlatformTime::Seconds() - Start) > TimeoutSeconds)
		{
			TSharedPtr<FJsonObject> Err = MakeShared<FJsonObject>();
			Err->SetBoolField(TEXT("ok"), false);
			Err->SetStringField(TEXT("error"), TEXT("GameThread dispatch timed out (is a modal dialog open in the editor?)"));
			return Err;
		}
		FPlatformProcess::Sleep(0.001f);
	}
	return Future.Get();
}
