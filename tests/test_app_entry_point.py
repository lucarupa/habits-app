# spec: 006-code-organization
"""Tests del punto de entrada — Tarea 6.5.

Fijan el contrato de `habits/app.py`: solo conserva `main`, sus constantes y la
conexión entre estado, persistencia y widgets. Los componentes, diálogos y
utilidades visuales viven en `habits/ui/`, y las vistas heredadas sin uso se
eliminan (RF-2.1, RF-2.2, RF-2.4, RF-2.5 y RF-5.4).
"""

import ast
from pathlib import Path

from habits.module_size import count_content_lines

ROOT = Path(__file__).resolve().parents[1]
APP_PATH = ROOT / "habits" / "app.py"
LIMIT = 250

REMOVED_CLASSES = {
    "Sidebar",
    "HabitDetailHeader",
    "HabitStatsCards",
    "ActivityHeatmap",
    "TodayRegistrationPanel",
    "EmptyDetailPanel",
    "HabitFormDialog",
    "DeleteHabitDialog",
    "StreakRecoveryDialog",
    "ReminderDialog",
    "CreateHabitView",
    "ListHabitsView",
}
REMOVED_FUNCTIONS = {
    "icon_for_habit",
    "format_streak_label",
    "format_date_display",
    "configure_page",
    "create_main_view",
}
REMOVED_CONSTANTS = {
    "ICON_BY_KEY",
    "DEFAULT_SIDEBAR_ICON",
    "STAT_CARD_ICONS",
    "WEEKDAY_LABELS",
    "APP_ICON_PATH",
}
UI_IMPORTS = {
    "Sidebar": "habits.ui.sidebar",
    "HabitDetailHeader": "habits.ui.detail_header",
    "HabitStatsCards": "habits.ui.stats",
    "ActivityHeatmap": "habits.ui.heatmap",
    "TodayRegistrationPanel": "habits.ui.registration_panel",
    "EmptyDetailPanel": "habits.ui.empty",
    "HabitFormDialog": "habits.ui.form_dialog",
    "DeleteHabitDialog": "habits.ui.delete_dialog",
    "StreakRecoveryDialog": "habits.ui.recovery_dialog",
    "ReminderDialog": "habits.ui.reminder_dialog",
    "configure_page": "habits.ui.page",
}


def parse_app() -> ast.Module:
    """Analizar `habits/app.py` sin importar Flet."""
    return ast.parse(APP_PATH.read_text(encoding="utf-8"))


def defined_names(tree: ast.Module) -> set[str]:
    """Recoger clases, funciones y asignaciones de nivel de módulo."""
    names: set[str] = set()

    for node in tree.body:
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            names.add(node.name)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    names.add(target.id)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            names.add(node.target.id)

    return names


def imported_from(tree: ast.Module) -> dict[str, str]:
    """Mapear cada nombre importado al módulo del que procede."""
    modules: dict[str, str] = {}

    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.module:
            for alias in node.names:
                modules[alias.asname or alias.name] = node.module

    return modules


def test_app_only_defines_main_and_its_connection_constants():
    """RF-2.1, RF-2.4: `app.py` no contiene widgets ni utilidades visuales."""
    names = defined_names(parse_app())

    assert "main" in names
    assert names & REMOVED_CLASSES == set()
    assert names & REMOVED_FUNCTIONS == set()
    assert names & REMOVED_CONSTANTS == set()


def test_legacy_views_are_removed():
    """RF-2.5: las vistas heredadas sin referencias desaparecen del módulo."""
    names = defined_names(parse_app())

    assert "CreateHabitView" not in names
    assert "ListHabitsView" not in names
    assert "create_main_view" not in names


def test_app_imports_each_widget_from_its_ui_module():
    """RF-2.2: cada componente se importa del módulo de responsabilidad."""
    imports = imported_from(parse_app())

    for name, module in UI_IMPORTS.items():
        assert imports.get(name) == module, name


def test_app_respects_the_content_line_limit():
    """RF-2.1: el punto de entrada se mantiene por debajo del límite."""
    count = count_content_lines(APP_PATH.read_text(encoding="utf-8"))

    assert count <= LIMIT, f"habits/app.py tiene {count} líneas con contenido"


def test_main_remains_the_flet_entry_point():
    """RF-5.4: el arranque de la aplicación sigue llamando a `main`."""
    tree = parse_app()
    main_guard = [
        node
        for node in tree.body
        if isinstance(node, ast.If)
        and isinstance(node.test, ast.Compare)
        and ast.unparse(node.test) == "__name__ == '__main__'"
    ]

    assert len(main_guard) == 1
    assert "ft.run(main)" in ast.unparse(main_guard[0])
