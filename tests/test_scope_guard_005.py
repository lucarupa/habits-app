# spec: 005-local-reminders
"""Guardia de alcance de la spec 005 — Tarea 8.1.

Comprueba que los recordatorios se limitan a una tarea periódica del sistema
que consulta la base de datos: se permite la tabla `reminders` y el runner,
pero se rechazan posponer, agrupar, programar por días, enviar por red y
modificar registros o estadísticas desde la notificación. Los criterios
funcionales se validan con la suite de dominio, servicio, runner y flujos.
"""

import ast
import sqlite3
import tempfile
from pathlib import Path

from habits.persistence.schema import init_db

ROOT = Path(__file__).resolve().parents[1]
HABITS_DIR = ROOT / "habits"
REMINDERS_PATH = HABITS_DIR / "reminders.py"
SERVICE_PATH = HABITS_DIR / "reminder_service.py"
RUNNER_PATH = HABITS_DIR / "reminder_runner.py"
NOTIFICATIONS_DIR = HABITS_DIR / "notifications"

ALLOWED_TABLES = {"habits", "completions", "reminders"}
FORBIDDEN_TABLES = {
    "notifications",
    "notification_queue",
    "deliveries",
    "delivery_log",
    "schedules",
    "reminder_groups",
    "groups",
    "snoozes",
}
FORBIDDEN_SOURCE_TERMS = (
    "posponer",
    "postpone",
    "snooze",
    "agrupar recordatorios",
    "recordatorio grupal",
    "recordatorios grupales",
    "repetir por días",
    "programar por días",
    "días de la semana",
)
FORBIDDEN_FEATURE_NAMES = (
    "snooze",
    "postpone",
    "pospone",
    "group_reminder",
    "reminder_group",
    "repeat_days",
    "days_of_week",
)
FORBIDDEN_NETWORK_MODULES = {
    "http",
    "smtplib",
    "socket",
    "urllib",
    "requests",
    "websocket",
    "websockets",
    "aiohttp",
}
FORBIDDEN_WRITE_FUNCTIONS = {
    "mark_completed_db",
    "mark_recovered_days_db",
    "save_reminder_db",
    "update_habit_db",
    "delete_habit_db",
    "create_habit_db",
}
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


def imported_names(path: Path) -> set[str]:
    """Recoger los módulos y nombres importados por un archivo."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.name.split(".")[0])
                names.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module is not None:
                names.add(node.module.split(".")[0])
                names.add(node.module)
            for alias in node.names:
                names.add(alias.name)

    return names


def test_scope_guard_allows_reminders_table_and_runner():
    """RF-2.1: el esquema y el runner periódico pertenecen a la spec 005."""
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
            reminder_columns = {
                row[1].lower()
                for row in connection.execute("PRAGMA table_info(reminders)")
            }
        finally:
            connection.close()

    assert tables == ALLOWED_TABLES
    assert tables.isdisjoint(FORBIDDEN_TABLES)
    assert reminder_columns == {
        "habit_id",
        "enabled",
        "reminder_time",
        "effective_from",
        "last_notified_on",
    }

    assert RUNNER_PATH.exists()
    module = ast.parse(RUNNER_PATH.read_text(encoding="utf-8"))
    functions = {
        node.name
        for node in module.body
        if isinstance(node, ast.FunctionDef)
    }
    assert {"run_check", "main"} <= functions


def test_scope_guard_rejects_snooze_groups_and_per_day_schedules():
    """Fuera de alcance: sin posponer, agrupar ni programar por días."""
    offenders: list[str] = []

    for path in sorted(HABITS_DIR.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(
                node,
                (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef),
            ):
                name = node.name.lower()
                if any(term in name for term in FORBIDDEN_FEATURE_NAMES):
                    offenders.append(f"{path.name}: {node.name}")

        for text in ui_strings(path):
            normalized = text.strip().lower()
            if any(term in normalized for term in FORBIDDEN_SOURCE_TERMS):
                offenders.append(f"{path.name}: {text}")

    assert offenders == []


def test_scope_guard_rejects_network_delivery():
    """RFN-5: los avisos son locales; no se envía nada por red."""
    offenders: list[str] = []

    for path in sorted(HABITS_DIR.rglob("*.py")):
        for name in imported_names(path):
            if name in FORBIDDEN_NETWORK_MODULES:
                offenders.append(f"{path.name}: {name}")

    assert offenders == []


def test_scope_guard_does_not_modify_records_from_notifications():
    """RF-2.8, RF-3.4: avisar no toca registros, estadísticas ni hábitos."""
    offenders: list[str] = []
    notification_paths = sorted(NOTIFICATIONS_DIR.glob("*.py"))

    for path in (REMINDERS_PATH, SERVICE_PATH, RUNNER_PATH, *notification_paths):
        for name in imported_names(path):
            if name in FORBIDDEN_WRITE_FUNCTIONS:
                offenders.append(f"{path.name}: {name}")

    assert offenders == []
