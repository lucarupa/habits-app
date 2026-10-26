# spec: 002-ui-redesign
"""Guardia de alcance de la spec 002 — Tarea 7.5, RF-5.5.

Comprueba que la aplicación no incorpora minutos, sesiones, “Quitar
registro”, Ajustes ni Progreso. La suite verde se valida ejecutando pytest.
"""

import ast
import sqlite3
import tempfile
from pathlib import Path

from habits.storage import init_db

ROOT = Path(__file__).resolve().parents[1]
HABITS_DIR = ROOT / "habits"

FORBIDDEN_TABLES = {"sessions", "minutes", "time_entries", "settings"}
FORBIDDEN_COLUMNS = {"minutes", "duration", "session_id"}
FORBIDDEN_NAME_PARTS = ("minute", "session", "settings", "progress")
FORBIDDEN_UI_TERMS = (
    "minutos",
    "sesiones",
    "quitar registro",
    "ajustes",
    "progreso",
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


def production_files() -> list[Path]:
    """Listar los módulos de producción."""
    return sorted(HABITS_DIR.glob("*.py"))


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


def test_database_schema_stays_within_scope():
    """RF-5.5: solo existen hábitos y registros diarios."""
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
            assert tables == {"habits", "completions"}
            assert tables.isdisjoint(FORBIDDEN_TABLES)

            for table in tables:
                columns = {
                    row[1].lower()
                    for row in connection.execute(
                        f"PRAGMA table_info({table})"
                    )
                }
                assert columns.isdisjoint(FORBIDDEN_COLUMNS)
        finally:
            connection.close()


def test_production_code_defines_no_out_of_scope_components():
    """RF-5.5: no hay funciones ni clases de minutos, sesiones o pantallas."""
    offenders: list[str] = []

    for path in production_files():
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(
                node,
                (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef),
            ):
                continue
            name = node.name.lower()
            if any(part in name for part in FORBIDDEN_NAME_PARTS):
                offenders.append(f"{path.name}: {node.name}")

    assert offenders == []


def test_ui_does_not_show_out_of_scope_labels():
    """RF-5.5: la interfaz no muestra minutos, sesiones ni pantallas extra."""
    offenders: list[str] = []

    for path in production_files():
        for text in ui_strings(path):
            normalized = text.strip().lower()
            if any(term in normalized for term in FORBIDDEN_UI_TERMS):
                offenders.append(f"{path.name}: {text}")

    assert offenders == []
