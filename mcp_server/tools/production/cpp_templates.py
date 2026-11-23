"""Unreal C++ class scaffolding that follows engine conventions (UCLASS, GENERATED_BODY,
module API macros, Public/Private layout)."""

from __future__ import annotations

import re

# kind -> (parent class, parent include, class prefix, UCLASS specifiers)
CLASS_KINDS: dict[str, tuple[str, str, str, str]] = {
    "actor": ("AActor", "GameFramework/Actor.h", "A", ""),
    "pawn": ("APawn", "GameFramework/Pawn.h", "A", ""),
    "character": ("ACharacter", "GameFramework/Character.h", "A", ""),
    "actor_component": (
        "UActorComponent",
        "Components/ActorComponent.h",
        "U",
        "ClassGroup=(Custom), meta=(BlueprintSpawnableComponent)",
    ),
    "scene_component": (
        "USceneComponent",
        "Components/SceneComponent.h",
        "U",
        "ClassGroup=(Custom), meta=(BlueprintSpawnableComponent)",
    ),
    "game_mode": ("AGameModeBase", "GameFramework/GameModeBase.h", "A", ""),
    "game_state": ("AGameStateBase", "GameFramework/GameStateBase.h", "A", ""),
    "player_controller": ("APlayerController", "GameFramework/PlayerController.h", "A", ""),
    "player_state": ("APlayerState", "GameFramework/PlayerState.h", "A", ""),
    "hud": ("AHUD", "GameFramework/HUD.h", "A", ""),
    "ai_controller": ("AAIController", "AIController.h", "A", ""),
    "object": ("UObject", "UObject/Object.h", "U", "BlueprintType, Blueprintable"),
    "game_instance_subsystem": (
        "UGameInstanceSubsystem",
        "Subsystems/GameInstanceSubsystem.h",
        "U",
        "",
    ),
    "world_subsystem": ("UWorldSubsystem", "Subsystems/WorldSubsystem.h", "U", ""),
    "blueprint_function_library": (
        "UBlueprintFunctionLibrary",
        "Kismet/BlueprintFunctionLibrary.h",
        "U",
        "",
    ),
    "interface": ("UInterface", "UObject/Interface.h", "U", "MinimalAPI, Blueprintable"),
}

_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,63}$")


def validate_name(name: str) -> str:
    if not _NAME_RE.match(name):
        raise ValueError("Class/module names must be C++ identifiers (letters, digits, _)")
    return name


def strip_prefix(name: str, prefix: str) -> str:
    """'AMyActor' -> 'MyActor' when the user already typed the prefix."""
    if len(name) > 1 and name[0] == prefix and name[1].isupper():
        return name[1:]
    return name


def render(kind: str, name: str, module: str) -> tuple[str, str, str]:
    """Return (base_name, header, source) for a class of ``kind``."""
    if kind not in CLASS_KINDS:
        raise ValueError(f"Unknown class kind '{kind}'. Use one of: {', '.join(CLASS_KINDS)}")
    validate_name(name)
    validate_name(module)
    parent, include, prefix, specifiers = CLASS_KINDS[kind]
    base = strip_prefix(name, prefix)
    api = f"{module.upper()}_API"

    if kind == "interface":
        header = f"""#pragma once

#include "CoreMinimal.h"
#include "{include}"
#include "{base}.generated.h"

UINTERFACE({specifiers})
class U{base} : public UInterface
{{
\tGENERATED_BODY()
}};

class {api} I{base}
{{
\tGENERATED_BODY()

public:
}};
"""
        source = f'#include "{base}.h"\n'
        return base, header, source

    full = prefix + base
    spec = f"UCLASS({specifiers})" if specifiers else "UCLASS()"
    body_h = ""
    body_cpp = ""
    if kind in ("actor", "pawn", "character"):
        body_h = (
            f"public:\n\t{full}();\n\n"
            "protected:\n\tvirtual void BeginPlay() override;\n\n"
            "public:\n\tvirtual void Tick(float DeltaTime) override;\n"
        )
        body_cpp = (
            f"{full}::{full}()\n{{\n\tPrimaryActorTick.bCanEverTick = true;\n}}\n\n"
            f"void {full}::BeginPlay()\n{{\n\tSuper::BeginPlay();\n}}\n\n"
            f"void {full}::Tick(float DeltaTime)\n{{\n\tSuper::Tick(DeltaTime);\n}}\n"
        )
    elif kind in ("actor_component", "scene_component"):
        body_h = (
            f"public:\n\t{full}();\n\n"
            "protected:\n\tvirtual void BeginPlay() override;\n\n"
            "public:\n\tvirtual void TickComponent(float DeltaTime, ELevelTick TickType, "
            "FActorComponentTickFunction* ThisTickFunction) override;\n"
        )
        body_cpp = (
            f"{full}::{full}()\n{{\n\tPrimaryComponentTick.bCanEverTick = true;\n}}\n\n"
            f"void {full}::BeginPlay()\n{{\n\tSuper::BeginPlay();\n}}\n\n"
            f"void {full}::TickComponent(float DeltaTime, ELevelTick TickType, "
            "FActorComponentTickFunction* ThisTickFunction)\n"
            "{\n\tSuper::TickComponent(DeltaTime, TickType, ThisTickFunction);\n}\n"
        )
    elif kind in ("game_instance_subsystem", "world_subsystem"):
        body_h = (
            "public:\n\tvirtual void Initialize(FSubsystemCollectionBase& Collection) override;\n"
            "\tvirtual void Deinitialize() override;\n"
        )
        body_cpp = (
            f"void {full}::Initialize(FSubsystemCollectionBase& Collection)\n"
            "{\n\tSuper::Initialize(Collection);\n}\n\n"
            f"void {full}::Deinitialize()\n{{\n\tSuper::Deinitialize();\n}}\n"
        )

    header = f"""#pragma once

#include "CoreMinimal.h"
#include "{include}"
#include "{base}.generated.h"

{spec}
class {api} {full} : public {parent}
{{
\tGENERATED_BODY()

{body_h}}};
"""
    source = f'#include "{base}.h"\n\n{body_cpp}'
    return base, header, source
