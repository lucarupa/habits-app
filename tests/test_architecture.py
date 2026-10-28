# spec: 006-code-organization
"""Tests de arquitectura — Tarea 7.1.

Comprueban que la lógica no depende de Flet, que la interfaz no accede a
SQLite ni a los repositorios, que no existen ciclos entre módulos, que los
módulos monolíticos desaparecieron y que los paquetes nuevos son importables
(RF-2.2, RF-2.5, RF-2.6 y RFN-6).
"""

import ast
import importlib
from pathlib import Path

import pytest

from habits.notifications.models import SCHEDULER_INSTALL_FAILED_MESSAGE

ROOT = Path(__file__).resolve().parents[1]
HABITS_DIR = ROOT / "habits"
UI_DIR = HABITS_DIR / "ui"
NOTIFICATIONS_DIR = HABITS_DIR / "notifications"
NOTIFICATION_MODULES = ("models", "common", "notifier", "scheduler")
LEGACY_MODULES = ("core.py", "storage.py", "app_state.py", "habit_form.py")
LOGIC_PACKAGES = ("domain", "persistence", "state", "forms")
IMPORTABLE_PACKAGES = (
    "habits.domain",
    "habits.persistence",
    "habits.state",
    "habits.forms",
)


def python_files(directory: Path) -> list[Path]:
    """Listar los módulos Python de un directorio, sin cachés."""
    return [
        path
        for path in sorted(directory.rglob("*.py"))
        if "__pycache__" not in path.parts
    ]


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


def flet_imports(path: Path) -> list[str]:
    """Devolver los imports de Flet de un archivo."""
    return sorted(
        module
        for module in imported_modules(path)
        if module == "flet" or module.startswith("flet.")
    )


def data_access_imports(path: Path) -> list[str]:
    """Devolver los imports de SQLite o de repositorios de un archivo."""
    return sorted(
        module
        for module in imported_modules(path)
        if module == "sqlite3" or module.startswith("habits.persistence")
    )


def module_name(path: Path) -> str:
    """Convertir la ruta de un módulo de producción en su nombre importable."""
    parts = list(path.relative_to(HABITS_DIR).with_suffix("").parts)
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(["habits", *parts]) if parts else "habits"


def production_modules() -> dict[str, Path]:
    """Mapear cada módulo de producción a su archivo."""
    return {module_name(path): path for path in python_files(HABITS_DIR)}


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


def test_domain_persistence_and_state_do_not_import_flet():
    """RF-2.2, RFN-6: la lógica no depende de widgets."""
    offenders: list[str] = []

    for package in LOGIC_PACKAGES:
        for path in python_files(HABITS_DIR / package):
            for module in flet_imports(path):
                offenders.append(f"{path.relative_to(ROOT)}: {module}")

    assert offenders == []


def test_ui_does_not_import_sqlite_or_repositories():
    """RF-2.2, RFN-6: la interfaz no accede directamente a datos."""
    offenders: list[str] = []

    for path in python_files(UI_DIR):
        for module in data_access_imports(path):
            offenders.append(f"{path.relative_to(ROOT)}: {module}")

    assert offenders == []


def test_production_modules_have_no_import_cycles():
    """RF-2.6: ningún módulo de producción depende circularmente de otro."""
    cycles = find_cycles(import_graph())

    assert cycles == [], "\n".join(" -> ".join(cycle) for cycle in cycles)


def test_cycle_detector_reports_a_cycle():
    """RF-2.6: el detector distingue un ciclo real de un grafo acíclico."""
    assert find_cycles({"a": {"b"}, "b": {"a"}}) == [("a", "b", "a")]
    assert find_cycles({"a": {"b"}, "b": {"c"}, "c": set()}) == []


def test_shared_scheduler_error_message_is_not_duplicated():
    """RF-2.7: el aviso de fallo del planificador vive en un solo módulo."""
    occurrences: list[str] = []

    for path in python_files(HABITS_DIR):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Constant)
                and node.value == SCHEDULER_INSTALL_FAILED_MESSAGE
            ):
                occurrences.append(
                    f"{path.relative_to(ROOT).as_posix()}:{node.lineno}"
                )

    assert len(occurrences) == 1
    assert occurrences[0].startswith("habits/notifications/models.py:")


def test_notification_adapters_are_split_by_responsibility():
    """RF-1.8, RF-2.1: el módulo sobredimensionado se divide por responsabilidad."""
    assert not (HABITS_DIR / "notifications.py").exists()
    assert NOTIFICATIONS_DIR.is_dir()

    for name in NOTIFICATION_MODULES:
        assert (NOTIFICATIONS_DIR / f"{name}.py").exists()


def test_notification_classes_live_in_their_responsibility_module():
    """RF-2.1, RF-2.2: cada adaptador vive en el módulo de su responsabilidad."""
    from habits.notifications.notifier import SystemNotifier
    from habits.notifications.scheduler import SystemScheduler

    assert SystemNotifier.__module__ == "habits.notifications.notifier"
    assert SystemScheduler.__module__ == "habits.notifications.scheduler"


def test_old_monolithic_modules_are_removed():
    """RF-2.5: no quedan archivos monolíticos ni fachadas de compatibilidad."""
    remaining = [name for name in LEGACY_MODULES if (HABITS_DIR / name).exists()]

    assert remaining == []


def test_old_module_imports_are_gone():
    """RF-2.5: ningún módulo importa las rutas antiguas."""
    old_prefixes = tuple(
        f"habits.{name.removesuffix('.py')}" for name in LEGACY_MODULES
    )
    offenders: list[str] = []

    for path in python_files(HABITS_DIR):
        for module in imported_modules(path):
            if module.startswith(old_prefixes):
                offenders.append(f"{path.relative_to(ROOT)}: {module}")

    assert offenders == []


@pytest.mark.parametrize("package", IMPORTABLE_PACKAGES)
def test_logic_packages_are_importable(package):
    """RF-2.2: los paquetes de lógica se pueden importar sin Flet."""
    assert importlib.import_module(package) is not None


def test_notifications_package_is_importable():
    """RF-2.2: el paquete de adaptadores se puede importar sin Flet."""
    assert importlib.import_module("habits.notifications") is not None

    for name in NOTIFICATION_MODULES:
        module = f"habits.notifications.{name}"
        assert importlib.import_module(module) is not None


def test_ui_package_is_importable():
    """RF-2.2: el paquete de interfaz existe y se puede importar."""
    pytest.importorskip("flet")

    assert importlib.import_module("habits.ui") is not None


def test_ui_modules_are_importable():
    """RF-2.2: cada componente de la interfaz se puede importar."""
    pytest.importorskip("flet")

    for path in python_files(UI_DIR):
        assert importlib.import_module(module_name(path)) is not None


def test_entry_point_is_importable():
    """RF-2.2, RF-5.4: el punto de entrada de la aplicación se puede importar."""
    pytest.importorskip("flet")

    assert importlib.import_module("habits.app") is not None
