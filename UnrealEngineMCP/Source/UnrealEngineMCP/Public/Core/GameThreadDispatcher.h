#pragma once

#include "CoreMinimal.h"
#include "Async/Future.h"

class FUnrealEngineMCPGameThreadDispatcher
{
public:
	template <typename TResult>
	static TFuture<TResult> Run(TFunction<TResult()> Func)
	{
		TPromise<TResult> Promise;
		TFuture<TResult> Future = Promise.GetFuture();
		TSharedRef<TPromise<TResult>, ESPMode::ThreadSafe> SharedPromise =
			MakeShared<TPromise<TResult>, ESPMode::ThreadSafe>(MoveTemp(Promise));

		AsyncTask(ENamedThreads::GameThread, [SharedPromise, Func]()
		{
			try
			{
				SharedPromise->SetValue(Func());
			}
			catch (...)
			{
				// Unreal code should not throw; keep a safe fallback.
				SharedPromise->SetValue(TResult());
			}
		});

		return Future;
	}

	static void RunAndWait(TFunction<void()> Func, float TimeoutSeconds = 60.0f);
	static TSharedPtr<FJsonObject> RunJson(TFunction<TSharedPtr<FJsonObject>()> Func, float TimeoutSeconds = 60.0f);

	/**
	 * Like RunJson, but runs Func from the core ticker in the main loop instead of a
	 * task-graph game-thread task. Use for work that may flush rendering or pump the
	 * task graph itself (asset import, map loads, editor Python): doing that inside a
	 * game-thread task trips the TaskGraph RecursionGuard assertion and crashes.
	 */
	static TSharedPtr<FJsonObject> RunJsonOnTicker(TFunction<TSharedPtr<FJsonObject>()> Func, float TimeoutSeconds = 60.0f);
};
