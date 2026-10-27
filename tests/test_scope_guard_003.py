# spec: 003-edit-delete-habits
# spec: 005-local-reminders
"""Guardia de alcance de la spec 003 — Tarea 7.3.

Comprueba que la edición y la eliminación no incorporan funciones fuera de
alcance: deshacer, archivar, borrado masivo, edición de registros diarios,
historial, importación/exportación ni acciones desde la barra lateral. Los
recordatorios y sus notificaciones pertenecen a la spec 005. Los criterios
funcionales se validan con la suite de widgets y de flujos integrados.
"""

import ast
import sqlite3
import tempfile
from pathlib import Path

from habits.storage import init_db

ROOT = Path(__file__).resolve().parents[1]
HABITS_DIR = ROOT / "habits"
APP_PATH = HABITS_DIR / "app.py"
STORAGE_PATH = HABITS_DIR / "storage.py"

FORBIDDEN_FUNCTION_PARTS = (
    "undo",
    "archive",
    "restore",
    "history",
    "audit",
    "export",
    "import",
)
RECORD_MUTATION_VERBS = (
    "update",
    "delete",
    "edit",
    "remove",
    "change",
)
FORBIDDEN_UI_TERMS = (
    "deshacer",
    "restaurar",
    "archivar",
    "archivado",
    "borrado masivo",
    "eliminación masiva",
    "eliminar todos",
    "historial",
    "auditoría",
    "importar",
    "exportar",
    "tema oscuro",
    "minutos",
    "sesiones",
    "quitar registro",
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


def test_database_schema_has_no_undo_archive_or_history_tables():
    """Fuera de alcance: sin estado extra, pero se admite `reminders` (spec 005)."""
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


def test_storage_has_no_record_level_mutation_or_history_api():
    """Fuera de alcance: no se editan registros ni se guarda historial."""
    tree = ast.parse(STORAGE_PATH.read_text(encoding="utf-8"))
    offenders: list[str] = []

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        name = node.name.lower()

        if any(part in name for part in FORBIDDEN_FUNCTION_PARTS):
            offenders.append(node.name)
            continue
        if "completion" in name and any(
            verb in name for verb in RECORD_MUTATION_VERBS
        ):
            offenders.append(node.name)

    assert offenders == []


def test_ui_does_not_show_out_of_scope_actions():
    """Fuera de alcance: sin deshacer, archivar, masivo, historial ni avisos."""
    offenders: list[str] = []

    for path in sorted(HABITS_DIR.glob("*.py")):
        for text in ui_strings(path):
            normalized = text.strip().lower()
            if any(term in normalized for term in FORBIDDEN_UI_TERMS):
                offenders.append(f"{path.name}: {text}")

    assert offenders == []


def test_edit_and_delete_actions_live_only_in_the_detail_header():
    """RF-1.3, RF-1.4: la barra lateral solo selecciona hábitos."""
    source = APP_PATH.read_text(encoding="utf-8")
    header = class_source(source, "HabitDetailHeader")
    sidebar = class_source(source, "Sidebar")

    assert "Editar" in header
    assert "Eliminar" in header
    assert "on_edit" in header
    assert "on_delete" in header

    assert "Editar" not in sidebar
    assert "Eliminar" not in sidebar
    assert "on_edit" not in sidebar
    assert "on_delete" not in sidebar
