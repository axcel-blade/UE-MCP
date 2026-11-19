#include "Tools/ToolRegistration.h"
#include "Tools/SystemTools.h"
#include "Tools/ActorTools.h"
#include "Tools/LevelTools.h"
#include "Tools/AssetTools.h"
#include "Tools/BlueprintTools.h"
#include "Tools/MaterialTools.h"
#include "Tools/LightingTools.h"
#include "Tools/RenderingTools.h"
#include "Tools/ProjectTools.h"
#include "Tools/IntelligenceTools.h"
#include "Tools/MeshTools.h"
#include "Tools/AnimationTools.h"
#include "Tools/NiagaraTools.h"
#include "Tools/UMGTools.h"
#include "Tools/SequencerTools.h"
#include "Tools/PhysicsTools.h"

void RegisterUnrealEngineMCPTools()
{
	FUnrealEngineMCPSystemTools::Register();
	FUnrealEngineMCPActorTools::Register();
	FUnrealEngineMCPLevelTools::Register();
	FUnrealEngineMCPAssetTools::Register();
	FUnrealEngineMCPBlueprintTools::Register();
	FUnrealEngineMCPMaterialTools::Register();
	FUnrealEngineMCPLightingTools::Register();
	FUnrealEngineMCPRenderingTools::Register();
	FUnrealEngineMCPProjectTools::Register();
	FUnrealEngineMCPIntelligenceTools::Register();
	FUnrealEngineMCPMeshTools::Register();
	FUnrealEngineMCPAnimationTools::Register();
	FUnrealEngineMCPNiagaraTools::Register();
	FUnrealEngineMCPUMGTools::Register();
	FUnrealEngineMCPSequencerTools::Register();
	FUnrealEngineMCPPhysicsTools::Register();
}
