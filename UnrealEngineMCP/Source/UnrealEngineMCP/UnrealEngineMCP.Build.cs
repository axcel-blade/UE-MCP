using UnrealBuildTool;

public class UnrealEngineMCP : ModuleRules
{
	public UnrealEngineMCP(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = ModuleRules.PCHUsageMode.UseExplicitOrSharedPCHs;

		PublicIncludePaths.AddRange(new string[] {
			System.IO.Path.Combine(ModuleDirectory, "Public")
		});

		PrivateIncludePaths.AddRange(new string[] {
			System.IO.Path.Combine(ModuleDirectory, "Private")
		});

		PublicDependencyModuleNames.AddRange(new string[] {
			"Core",
			"CoreUObject",
			"Engine",
			"InputCore",
			"Json",
			"JsonUtilities",
			"Networking",
			"Sockets",
			"DeveloperSettings"
		});

		PrivateDependencyModuleNames.AddRange(new string[] {
			"UnrealEd",
			"EditorSubsystem",
			"EditorScriptingUtilities",
			"Slate",
			"SlateCore",
			"AssetRegistry",
			"AssetTools",
			"Kismet",
			"KismetCompiler",
			"BlueprintGraph",
			"Projects",
			"LevelEditor",
			"ToolMenus",
			"ImageWrapper",
			"RenderCore",
			"RHI"
		});

		if (Target.bBuildEditor)
		{
			PrivateDependencyModuleNames.AddRange(new string[] {
				"PropertyEditor",
				"BlueprintEditorLibrary",
				"MaterialEditor"
			});
		}
	}
}
