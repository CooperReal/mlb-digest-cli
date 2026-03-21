"""
Structural tests that enforce architectural boundaries and taste invariants.

Every test failure is written as a remediation instruction so humans and AI
agents can self-correct. These tests run in pre-commit and CI.
"""
import ast
from pathlib import Path

import pytest

SRC_DIR = Path(__file__).resolve().parent.parent / "src" / "mlb_digest"
TEST_DIR = Path(__file__).resolve().parent
MODULES = [p.stem for p in SRC_DIR.glob("*.py") if p.stem != "__init__"]


# ---------------------------------------------------------------------------
# DEPENDENCY LAYERING
#
#   config      (layer 0 — depends on nothing internal)
#   mlb_api, feeds  (layer 1 — data fetching)
#   narrator    (layer 2 — transforms data, may use types from layer 1)
#   templates   (layer 3 — rendering)
#   emailer     (layer 4 — delivery)
#   cli         (layer 5 — orchestrator, may import anything)
# ---------------------------------------------------------------------------

LAYER: dict[str, int] = {
    "config": 0,
    "mlb_api": 1,
    "feeds": 1,
    "narrator": 2,
    "templates": 3,
    "emailer": 4,
    "cli": 5,
}

# Explicit cross-layer allowances (module -> set of modules it may import)
ALLOWED_IMPORTS: dict[str, set[str]] = {
    "narrator": {"feeds", "mlb_api"},
}


def _get_internal_imports(filepath: Path) -> list[str]:
    """Parse a module's AST and return all mlb_digest sub-module names it imports."""
    tree = ast.parse(filepath.read_text())
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith(
            "mlb_digest."
        ):
            imports.append(node.module.split(".")[-1])
    return imports


@pytest.mark.parametrize("module", sorted(LAYER.keys()))
def test_dependency_direction(module: str) -> None:
    """Modules may only import from their own layer or higher (lower index)."""
    filepath = SRC_DIR / f"{module}.py"
    my_layer = LAYER[module]
    allowed = ALLOWED_IMPORTS.get(module, set())

    for imported in _get_internal_imports(filepath):
        if imported not in LAYER:
            continue
        imported_layer = LAYER[imported]
        if imported_layer > my_layer and imported not in allowed:
            pytest.fail(
                f"ARCHITECTURE VIOLATION: '{module}' (layer {my_layer}) imports "
                f"'{imported}' (layer {imported_layer}).\n"
                f"Layer order: config(0) → mlb_api/feeds(1) → narrator(2) "
                f"→ templates(3) → emailer(4) → cli(5).\n"
                f"FIX: Move shared code to a higher layer, or add a type "
                f"definition to config.py or a shared types module."
            )


# ---------------------------------------------------------------------------
# MODULE SIZE
# ---------------------------------------------------------------------------

MAX_MODULE_LINES = 300


@pytest.mark.parametrize("module", MODULES)
def test_module_size_limit(module: str) -> None:
    """No single module may exceed 300 lines."""
    filepath = SRC_DIR / f"{module}.py"
    line_count = len(filepath.read_text().splitlines())

    assert line_count <= MAX_MODULE_LINES, (
        f"TASTE VIOLATION: '{module}.py' is {line_count} lines "
        f"(max {MAX_MODULE_LINES}).\n"
        f"FIX: Split into focused modules. Each module should do one thing. "
        f"For example, extract roster functions from mlb_api.py into mlb_roster.py."
    )


# ---------------------------------------------------------------------------
# TEST COVERAGE MAPPING
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("module", MODULES)
def test_every_module_has_tests(module: str) -> None:
    """Every source module must have a corresponding test file."""
    test_file = TEST_DIR / f"test_{module}.py"

    assert test_file.exists(), (
        f"COVERAGE VIOLATION: 'src/mlb_digest/{module}.py' has no test file.\n"
        f"FIX: Create 'tests/test_{module}.py' with at least one test for "
        f"the module's public interface."
    )


# ---------------------------------------------------------------------------
# NO RAW DICT AT MODULE BOUNDARIES
# ---------------------------------------------------------------------------


@pytest.mark.xfail(reason="Task 3 will replace with SelectedArticles dataclass")
def test_no_raw_dict_returns_at_boundaries() -> None:
    """Public functions in data modules must return dataclasses, not raw dicts."""
    boundary_modules = ["mlb_api", "feeds", "config"]

    for mod_name in boundary_modules:
        filepath = SRC_DIR / f"{mod_name}.py"
        tree = ast.parse(filepath.read_text())

        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if node.name.startswith("_"):
                continue
            if node.returns is None:
                continue

            # Flag bare `dict` return
            if isinstance(node.returns, ast.Name) and node.returns.id == "dict":
                pytest.fail(
                    f"TASTE VIOLATION: '{mod_name}.{node.name}()' returns bare 'dict'.\n"
                    f"FIX: Define a @dataclass for this return type. Dataclasses are "
                    f"self-documenting, type-safe, and readable across module boundaries."
                )
            # Flag dict[...] return
            if (
                isinstance(node.returns, ast.Subscript)
                and isinstance(node.returns.value, ast.Name)
                and node.returns.value.id == "dict"
            ):
                pytest.fail(
                    f"TASTE VIOLATION: '{mod_name}.{node.name}()' returns 'dict[...]'.\n"
                    f"FIX: Define a @dataclass for this return type. If this is a "
                    f"lookup table (e.g. dict[str, list[Article]]), consider a "
                    f"dedicated dataclass like 'SelectedArticles' with named fields."
                )


# ---------------------------------------------------------------------------
# RETURN TYPE ANNOTATIONS
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("module", MODULES)
def test_public_functions_have_return_types(module: str) -> None:
    """Every public function must declare a return type."""
    filepath = SRC_DIR / f"{module}.py"
    tree = ast.parse(filepath.read_text())

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if node.name.startswith("_"):
            continue
        # Skip Click-decorated functions (Click infers return types)
        decorator_names: list[str] = []
        for dec in node.decorator_list:
            if isinstance(dec, ast.Attribute):
                decorator_names.append(dec.attr)
            elif isinstance(dec, ast.Name):
                decorator_names.append(dec.id)
            elif isinstance(dec, ast.Call):
                if isinstance(dec.func, ast.Attribute):
                    decorator_names.append(dec.func.attr)
                elif isinstance(dec.func, ast.Name):
                    decorator_names.append(dec.func.id)
        click_decorators = {"command", "group", "option", "pass_context", "argument"}
        if any(d in click_decorators for d in decorator_names):
            continue

        if node.returns is None:
            pytest.fail(
                f"TASTE VIOLATION: '{module}.{node.name}()' at line {node.lineno} "
                f"has no return type annotation.\n"
                f"FIX: Add '-> ReturnType' to the function signature. "
                f"Use '-> None' for functions that don't return a value."
            )


# ---------------------------------------------------------------------------
# EXCEPTION NAMING
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("module", MODULES)
def test_exception_classes_end_with_error(module: str) -> None:
    """Custom exception classes must be named *Error, not *Exception."""
    filepath = SRC_DIR / f"{module}.py"
    tree = ast.parse(filepath.read_text())

    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        is_exception = False
        for base in node.bases:
            base_name = ""
            if isinstance(base, ast.Name):
                base_name = base.id
            elif isinstance(base, ast.Attribute):
                base_name = base.attr
            if base_name in ("Exception", "BaseException") or base_name.endswith(
                ("Error", "Exception")
            ):
                is_exception = True
                break

        if is_exception and not node.name.endswith("Error"):
            pytest.fail(
                f"TASTE VIOLATION: Exception class '{module}.{node.name}' "
                f"does not end with 'Error'.\n"
                f"FIX: Rename to '{node.name.replace('Exception', '')}Error'. "
                f"We use the *Error suffix consistently (e.g. NarratorError)."
            )


# ---------------------------------------------------------------------------
# NO WILDCARD IMPORTS
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("module", MODULES)
def test_no_wildcard_imports(module: str) -> None:
    """Wildcard imports are banned — explicit imports only."""
    filepath = SRC_DIR / f"{module}.py"
    tree = ast.parse(filepath.read_text())

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.names:
            for alias in node.names:
                if alias.name == "*":
                    pytest.fail(
                        f"TASTE VIOLATION: '{module}.py' line {node.lineno} uses "
                        f"'from {node.module} import *'.\n"
                        f"FIX: Import specific names explicitly. Wildcard imports "
                        f"make dependencies opaque and break static analysis."
                    )


# ---------------------------------------------------------------------------
# NO F-STRINGS IN LOGGING (supplements Ruff G004 with better remediation)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("module", MODULES)
def test_no_fstrings_in_logging(module: str) -> None:
    """Log calls must use %-formatting, not f-strings."""
    filepath = SRC_DIR / f"{module}.py"
    tree = ast.parse(filepath.read_text())

    log_methods = {"debug", "info", "warning", "error", "exception", "critical"}

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Attribute):
            continue
        if node.func.attr not in log_methods:
            continue

        if node.args and isinstance(node.args[0], ast.JoinedStr):
            pytest.fail(
                f"TASTE VIOLATION: '{module}.py' line {node.lineno} uses "
                f"f-string in logger.{node.func.attr}() call.\n"
                f"FIX: Use %-formatting instead:\n"
                f'  logger.{node.func.attr}("message: %s", value)\n'
                f"Why: %-formatting is lazy (string not built if level is disabled) "
                f"and structured logging tools can parse the template."
            )
