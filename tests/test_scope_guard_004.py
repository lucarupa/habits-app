# spec: 004-duplicate-warning-streak-recovery
# spec: 005-local-reminders
"""Guardia de alcance de la spec 004 — Tarea 6.3.

Comprueba que la recuperación no incorpora selección manual de días, deshacer,
recuperación de huecos largos ni tablas ajenas. La tabla `reminders` y los
conceptos de recordatorio y notificación pertenecen a la spec 005 y están
permitidos. Los criterios funcionales se validan con la suite de dominio,
widgets y flujos integrados.
"""

import ast
import sqlite3
import tempfile
from pathlib import Path

from habits.storage import init_db

ROOT = Path(__file__).resolve().parents[1]
HABITS_DIR = ROOT / "habits"
APP_PATH = HABITS_DIR / "app.py"

FORBIDDEN_TABLES = {
    "recovered_days",
    "recoveries",
    "recovery_history",
    "notifications",
    "undo_history",
    "settings",
}
FORBIDDEN_COLUMNS = {
    "manual",
    "selected_days",
    "notification_id",
    "gap_length",
    "undo",
}
FORBIDDEN_UI_TERMS = (
    "elegir días",
    "seleccionar días",
    "selección manual",
    "días manuales",
    "recuperar todos",
    "huecos anteriores",
    "hueco largo",
    "deshacer",
)
FORBIDDEN_FEATURE_NAMES = (
    "undo",
    "archive",
)
UI_CONTROLS = {
    "Text",
    "TextField",
    "Button",
    "FilledButton",
    "TextButton",
    "DropdownOption",
    "SnackBar",
    "Tab",
}


def ui_strings(path: Path) -> list[str]:
    """Extraer los textos que se pasan a controles visibles de Flet."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    texts: list[str] = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        function = node.func
        name = (
            function.attr
            if isinstance(function, ast.Attribute)
            else getattr(function, "id", "")
        )
        if name not in UI_CONTROLS:
            continue

        for argument in node.args:
            if isinstance(argument, ast.Constant) and isinstance(
                argument.value, str
            ):
                texts.append(argument.value)
        for keyword in node.keywords:
            if keyword.arg not in {
                "value",
                "content",
                "label",
                "hint_text",
                "title",
            }:
                continue
            if isinstance(keyword.value, ast.Constant) and isinstance(
                keyword.value.value, str
            ):
                texts.append(keyword.value.value)

    return texts


def class_source(source: str, name: str) -> str:
    """Devolver el código fuente de una clase de nivel superior."""
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == name:
            segment = ast.get_source_segment(source, node)
            if segment is not None:
                return segment
    raise AssertionError(f"No se encontró la clase {name}")


def test_scope_guard_allows_recovered_column():
    """RF-2.15: el esquema añade `recovered` y la tabla de la spec 005."""
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = str(Path(temp_dir) / "scope.db")
        init_db(db_path)

        connection = sqlite3.connect(db_path)
        try:
            tables = {
                row[0]
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                )
                if not row[0].startswith("sqlite_")
            }
            assert tables == {"habits", "completions", "reminders"}
            assert tables.isdisjoint(FORBIDDEN_TABLES)

            columns = {
                table: {
                    row[1].lower()
                    for row in connection.execute(
                        f"PRAGMA table_info({table})"
                    )
                }
                for table in tables
            }
        finally:
            connection.close()

    assert columns["habits"] == {"id", "name", "start_date", "icon"}
    assert columns["completions"] == {
        "id",
        "habit_id",
        "completed_date",
        "recovered",
    }
    assert columns["completions"].isdisjoint(FORBIDDEN_COLUMNS)


def test_scope_guard_rejects_manual_gap_selection():
    """RF-2.18: no se eligen días concretos ni se recuperan huecos largos."""
    offenders: list[str] = []

    for path in sorted(HABITS_DIR.glob("*.py")):
        for text in ui_strings(path):
            normalized = text.strip().lower()
            if any(term in normalized for term in FORBIDDEN_UI_TERMS):
                offenders.append(f"{path.name}: {text}")

    assert offenders == []

    source = APP_PATH.read_text(encoding="utf-8")
    dialog = class_source(source, "StreakRecoveryDialog")

    assert "Checkbox" not in dialog
    assert "DatePicker" not in dialog
    assert "Calendar" not in dialog


def test_scope_guard_rejects_undo_and_archive_features():
    """Fuera de alcance: sin deshacer ni archivar; los avisos son de la spec 005."""
    offenders: list[str] = []

    for path in sorted(HABITS_DIR.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(
                node,
                (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef),
            ):
                continue
            name = node.name.lower()
            if any(part in name for part in FORBIDDEN_FEATURE_NAMES):
                offenders.append(f"{path.name}: {node.name}")

    assert offenders == []
