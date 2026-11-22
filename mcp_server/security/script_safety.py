"""Static checks that refuse clearly dangerous editor-Python scripts before they run.

Ported from Blender-MCP and applied to ``unreal_execute_python`` while
``security.safe_python_execution`` is on (the default). The script is parsed (never
run) and refused if it would run other programs, delete files or assets, use the
network, keep callbacks running or change editor-wide defaults, quit the editor, or
reach around these checks (eval/exec/compile/__import__, importlib, dunder
attributes, nested Python execution, raw console commands).

A guard against accidents and against an AI being talked into something harmful,
not a sandbox: Python is too dynamic to make airtight by inspection.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass

PROCESS = "runs other programs"
DELETE = "deletes files or folders"
NETWORK = "uses the network"
PERSIST = "changes the editor beyond this session (keeps running or survives a restart)"
SESSION = "throws away the user's editor session"
ESCAPE = "can bypass these safety checks"

# Importing any of these (or a submodule) is refused outright.
BLOCKED_MODULES: dict[str, str] = {
    "subprocess": PROCESS,
    "pty": PROCESS,
    "multiprocessing": PROCESS,
    "socket": NETWORK,
    "ssl": NETWORK,
    "urllib": NETWORK,
    "http": NETWORK,
    "ftplib": NETWORK,
    "smtplib": NETWORK,
    "telnetlib": NETWORK,
    "requests": NETWORK,
    "httpx": NETWORK,
    "aiohttp": NETWORK,
    "webbrowser": NETWORK,
    "importlib": ESCAPE,
    "ctypes": ESCAPE,
    "builtins": ESCAPE,
}

# Fully-qualified call/attribute paths, after resolving import aliases.
BLOCKED_PATHS: dict[str, str] = {
    "os.system": PROCESS,
    "os.popen": PROCESS,
    "os.fork": PROCESS,
    "os.kill": PROCESS,
    "os.startfile": PROCESS,
    "os.remove": DELETE,
    "os.unlink": DELETE,
    "os.rmdir": DELETE,
    "os.removedirs": DELETE,
    "shutil.rmtree": DELETE,
    "unreal.SystemLibrary.quit_editor": SESSION,
    "unreal.SystemLibrary.launch_url": NETWORK,
    "unreal.SystemLibrary.execute_console_command": ESCAPE
    + " (console commands have their own setting)",
    "unreal.PythonScriptLibrary.execute_python_command": ESCAPE,
    "unreal.PythonScriptLibrary.execute_python_command_ex": ESCAPE,
    "unreal.EditorAssetLibrary.delete_asset": DELETE + " (use unreal_delete_asset)",
    "unreal.EditorAssetLibrary.delete_directory": DELETE + " (use unreal_delete_asset)",
    "unreal.EditorAssetLibrary.delete_loaded_asset": DELETE + " (use unreal_delete_asset)",
    "unreal.EditorAssetLibrary.delete_loaded_assets": DELETE + " (use unreal_delete_asset)",
}

# Any path starting with one of these.
BLOCKED_PREFIXES: dict[str, str] = {
    "os.exec": PROCESS,
    "os.spawn": PROCESS,
    "os.posix_spawn": PROCESS,
    "unreal.register_slate_": PERSIST,
    "unreal.register_python_shutdown_callback": PERSIST,
}

# pathlib-style deletes: refused when called with no positional argument.
BLOCKED_METHODS: dict[str, str] = {
    "unlink": DELETE,
    "rmdir": DELETE,
}

BLOCKED_BUILTINS: dict[str, str] = {
    "eval": ESCAPE,
    "exec": ESCAPE,
    "compile": ESCAPE,
    "__import__": ESCAPE,
    "globals": ESCAPE,
    "breakpoint": ESCAPE,
}

# Dunder attributes that lead out of normal code. Others (__name__, __class__) are fine.
BLOCKED_DUNDERS = frozenset(
    {
        "__globals__",
        "__builtins__",
        "__subclasses__",
        "__code__",
        "__closure__",
        "__bases__",
        "__mro__",
        "__base__",
        "__loader__",
        "__spec__",
        "__getattribute__",
        "__reduce__",
        "__reduce_ex__",
        "__func__",
        "__self__",
        "__dict__",
        "__import__",
    }
)

# Writes under these roots are refused (editor-wide settings that persist).
_PREFS_ROOTS = ("unreal.get_default_object",)


@dataclass(frozen=True)
class Violation:
    line: int
    what: str
    reason: str

    def describe(self) -> str:
        return f"line {self.line}: {self.what} ({self.reason})"


class UnsafeScriptError(PermissionError):
    def __init__(self, violations: list[Violation]) -> None:
        self.violations = violations
        lines = "; ".join(v.describe() for v in violations[:10])
        more = f" (+{len(violations) - 10} more)" if len(violations) > 10 else ""
        super().__init__(
            f"Script refused by safe Python execution: {lines}{more}. Do the work without "
            "these operations (or with the dedicated MCP tool), or ask the user to set "
            "security.safe_python_execution=false if they really want it."
        )


def _dotted(node: ast.AST) -> list[str] | None:
    """['unreal', 'SystemLibrary', 'quit_editor'] for unreal.SystemLibrary.quit_editor."""
    parts: list[str] = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
        return parts[::-1]
    return None


class _Checker(ast.NodeVisitor):
    def __init__(self) -> None:
        self.violations: list[Violation] = []
        # Local name -> the module path it stands for ("o" -> "os").
        self.aliases: dict[str, str] = {}

    def _flag(self, node: ast.AST, what: str, reason: str) -> None:
        self.violations.append(Violation(getattr(node, "lineno", 0), what, reason))

    def _resolve(self, parts: list[str]) -> str:
        head = self.aliases.get(parts[0], parts[0])
        return ".".join([head, *parts[1:]])

    def _check_path(self, node: ast.AST, path: str) -> None:
        if path in BLOCKED_PATHS:
            self._flag(node, path, BLOCKED_PATHS[path])
            return
        for prefix, reason in BLOCKED_PREFIXES.items():
            if path.startswith(prefix):
                self._flag(node, path, reason)
                return
        top = path.split(".", 1)[0]
        if top in BLOCKED_MODULES and top in self.aliases.values():
            self._flag(node, path, BLOCKED_MODULES[top])

    # imports ---------------------------------------------------------------------

    def _check_module(self, node: ast.AST, module: str) -> None:
        top = module.split(".", 1)[0]
        if top in BLOCKED_MODULES:
            self._flag(node, f"import {module}", BLOCKED_MODULES[top])

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            self._check_module(node, alias.name)
            local = alias.asname or alias.name.split(".", 1)[0]
            self.aliases[local] = alias.name if alias.asname else local

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        module = node.module or ""
        self._check_module(node, module)
        for alias in node.names:
            full = f"{module}.{alias.name}" if module else alias.name
            self._check_path(node, full)
            if alias.name in BLOCKED_BUILTINS and module == "builtins":
                self._flag(node, full, BLOCKED_BUILTINS[alias.name])
            self.aliases[alias.asname or alias.name] = full

    # names, attributes, calls -----------------------------------------------------

    def visit_Assign(self, node: ast.Assign) -> None:
        # x = os / x = unreal.SystemLibrary : keep following the alias.
        parts = _dotted(node.value)
        if parts is not None:
            for target in node.targets:
                if isinstance(target, ast.Name):
                    self.aliases[target.id] = self._resolve(parts)
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name) -> None:
        if node.id in BLOCKED_BUILTINS and node.id not in self.aliases:
            self._flag(node, node.id, BLOCKED_BUILTINS[node.id])
        elif node.id in BLOCKED_DUNDERS:
            self._flag(node, node.id, ESCAPE)
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        if node.attr in BLOCKED_DUNDERS:
            self._flag(node, node.attr, ESCAPE)
        parts = _dotted(node)
        if parts is not None:
            path = self._resolve(parts)
            self._check_path(node, path)
        # Visit only the innermost value: checking every prefix of a.b.c.d would
        # report the same chain several times.
        inner = node.value
        while isinstance(inner, ast.Attribute):
            if inner.attr in BLOCKED_DUNDERS:
                self._flag(inner, inner.attr, ESCAPE)
            inner = inner.value
        self.visit(inner)

    def visit_Call(self, node: ast.Call) -> None:
        func = node.func
        if isinstance(func, ast.Attribute) and func.attr in BLOCKED_METHODS and not node.args:
            self._flag(node, f".{func.attr}()", BLOCKED_METHODS[func.attr])
        # getattr(obj, "__globals__") / getattr(os, "system")
        if (
            isinstance(func, ast.Name)
            and func.id in ("getattr", "setattr", "delattr")
            and len(node.args) >= 2
            and isinstance(node.args[1], ast.Constant)
            and isinstance(node.args[1].value, str)
        ):
            attr = node.args[1].value
            if attr in BLOCKED_DUNDERS:
                self._flag(node, f"{func.id}(..., {attr!r})", ESCAPE)
            base = _dotted(node.args[0])
            if base is not None:
                self._check_path(node, f"{self._resolve(base)}.{attr}")
        self.generic_visit(node)

    # writes to preferences -------------------------------------------------------

    def _check_store(self, target: ast.AST) -> None:
        if isinstance(target, ast.Subscript):
            target = target.value
        if not isinstance(target, ast.Attribute):
            return  # plain reads are fine
        parts = _dotted(target)
        if parts is not None:
            path = self._resolve(parts)
            if any(path == r or path.startswith(r + ".") for r in _PREFS_ROOTS):
                self._flag(target, path, PERSIST + "; preferences")

    def visit_AugAssign(self, node: ast.AugAssign) -> None:
        self._check_store(node.target)
        self.generic_visit(node)


def _visit_stores(checker: _Checker, tree: ast.AST) -> None:
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                checker._check_store(target)


def check(code: str) -> list[Violation]:
    """Every refused operation in ``code``, in line order. Syntax errors are not
    reported here; the script then fails normally with Python's own message."""
    try:
        tree = ast.parse(code, filename="<unreal_mcp>", mode="exec")
    except SyntaxError:
        return []
    checker = _Checker()
    checker.visit(tree)
    _visit_stores(checker, tree)
    seen: set[tuple[int, str]] = set()
    unique: list[Violation] = []
    for v in sorted(checker.violations, key=lambda v: v.line):
        if (v.line, v.what) not in seen:
            seen.add((v.line, v.what))
            unique.append(v)
    return unique


def enforce(code: str) -> None:
    violations = check(code)
    if violations:
        raise UnsafeScriptError(violations)
