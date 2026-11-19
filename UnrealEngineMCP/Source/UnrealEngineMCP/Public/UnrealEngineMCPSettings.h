#pragma once

#include "CoreMinimal.h"
#include "Engine/DeveloperSettings.h"
#include "UnrealEngineMCPSettings.generated.h"

UCLASS(config = EditorPerProjectUserSettings, defaultconfig, meta = (DisplayName = "Unreal MCP"))
class UNREALENGINEMCP_API UUnrealEngineMCPSettings : public UDeveloperSettings
{
	GENERATED_BODY()

public:
	UUnrealEngineMCPSettings();

	virtual FName GetCategoryName() const override { return TEXT("Plugins"); }

	UPROPERTY(EditAnywhere, config, Category = "Bridge")
	FString BindAddress = TEXT("127.0.0.1");

	UPROPERTY(EditAnywhere, config, Category = "Bridge", meta = (ClampMin = "1024", ClampMax = "65535"))
	int32 Port = 55557;

	UPROPERTY(EditAnywhere, config, Category = "Bridge")
	bool bAutoStart = true;

	UPROPERTY(EditAnywhere, config, Category = "Security")
	FString AuthToken;

	UPROPERTY(EditAnywhere, config, Category = "Paths")
	FString ScreenshotDirectory;

	UPROPERTY(EditAnywhere, config, Category = "Bridge", meta = (ClampMin = "1.0"))
	float RequestTimeoutSeconds = 60.0f;
};
