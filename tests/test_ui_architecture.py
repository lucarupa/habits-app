# spec: 006-code-organization
"""Verificación de la interfaz — Tarea 6.6.

Comprueba que los módulos de `habits/ui/` no acceden a SQLite ni a los
repositorios, que la reorganización no introduce dependencias circulares, que
cada módulo respeta el límite de 250 líneas con contenido y que no se duplican
definiciones entre componentes (RF-2.6, RF-2.7, RF-5.1 y RF-5.4).
"""

import ast
from pathlib import Path

from habits.module_size import find_oversized_modules

ROOT = Path(__file__).resolve().parents[1]
HABITS_DIR = ROOT / "habits"
UI_DIR = HABITS_DIR / "ui"
FORBIDDEN_MODULES = {"sqlite3"}
FORBIDDEN_PREFIXES = ("habits.persistence",)


def production_modules() -> dict[str, Path]:
    """Mapear cada módulo de producción a su archivo."""
    modules: dict[str, Path] = {}

    for path in sorted(HABITS_DIR.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue

        parts = list(path.relative_to(HABITS_DIR).with_suffix("").parts)
        if parts[-1] == "__init__":
            parts.pop()
        name = ".".join(["habits", *parts]) if parts else "habits"
        modules[name] = path

    return modules


def imported_modules(path: Path) -> set[str]:
    """Recoger los módulos importados por un archivo."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    modules: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
            for alias in node.names:
                modules.add(f"{node.module}.{alias.name}")

    return modules


def import_graph() -> dict[str, set[str]]:
    """Construir el grafo de imports entre módulos de producción."""
    modules = production_modules()
    graph = {name: set() for name in modules}

    for name, path in modules.items():
        for target in imported_modules(path):
            if target in modules:
                graph[name].add(target)

    return graph


def find_cycles(graph: dict[str, set[str]]) -> list[tuple[str, ...]]:
    """Devolver los ciclos encontrados en el grafo de imports."""
    visiting: set[str] = set()
    visited: set[str] = set()
    cycles: list[tuple[str, ...]] = []

    def visit(node: str, stack: list[str]) -> None:
        visiting.add(node)
        stack.append(node)

        for neighbour in sorted(graph[node]):
            if neighbour in visiting:
                start = stack.index(neighbour)
                cycles.append(tuple(stack[start:] + [neighbour]))
            elif neighbour not in visited:
                visit(neighbour, stack)

        stack.pop()
        visiting.remove(node)
        visited.add(node)

    for node in sorted(graph):
        if node not in visited:
            visit(node, [])

    return cycles


def module_level_names(path: Path) -> list[str]:
    """Recoger clases, funciones y asignaciones de nivel de módulo."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: list[str] = []

    for node in tree.body:
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            names.append(node.name)
        elif isinstance(node, ast.Assign):
            names.extend(
                target.id
                for target in node.targets
                if isinstance(target, ast.Name)
            )
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            names.append(node.target.id)

    return names


def test_ui_does_not_import_sqlite_or_repositories():
    """RF-2.2, RF-2.6: la interfaz no accede directamente a datos."""
    offenders: list[str] = []

    for path in sorted(UI_DIR.glob("*.py")):
        for module in imported_modules(path):
            if module in FORBIDDEN_MODULES or module.startswith(
                FORBIDDEN_PREFIXES
            ):
                offenders.append(f"{path.name}: {module}")

    assert offenders == []


def test_production_modules_have_no_import_cycles():
    """RF-2.6: ningún módulo de producción depende circularmente de otro."""
    cycles = find_cycles(import_graph())

    assert cycles == [], "\n".join(" -> ".join(cycle) for cycle in cycles)


def test_ui_modules_respect_the_content_line_limit():
    """RF-2.1, RF-2.8: todos los módulos de la interfaz caben en 250 líneas."""
    modules = sorted(UI_DIR.glob("*.py"))

    assert modules
    assert find_oversized_modules(UI_DIR) == []


def test_ui_does_not_duplicate_module_level_definitions():
    """RF-2.7: cada componente y constante de la interfaz vive en un solo módulo."""
    seen: dict[str, str] = {}
    duplicates: list[str] = []

    for path in sorted(UI_DIR.glob("*.py")):
        for name in module_level_names(path):
            if name in seen:
                duplicates.append(f"{name}: {seen[name]}, {path.name}")
            seen[name] = path.name

    assert duplicates == []
