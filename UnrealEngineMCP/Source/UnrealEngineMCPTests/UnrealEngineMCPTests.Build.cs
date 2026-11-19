using UnrealBuildTool;

public class UnrealEngineMCPTests : ModuleRules
{
	public UnrealEngineMCPTests(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;
		PrivateDependencyModuleNames.AddRange(new string[] {
			"Core",
			"CoreUObject",
			"Engine",
			"UnrealEd",
			"UnrealEngineMCP"
		});
	}
}
