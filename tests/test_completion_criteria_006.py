# spec: 006-code-organization
"""Verificación de los criterios de finalización — Tarea 9.3.

Comprueba los ocho criterios de finalización de la spec 006 y que `tasks.md`
quede completamente marcado. La suite y la cobertura se midieron en la Tarea
9.1; aquí se verifica que las cifras documentadas siguen superando el mínimo
del 80 % y que el resto de criterios se cumplen sobre el código real.
"""

import ast
import re
import sqlite3
from datetime import date, timedelta
from pathlib import Path

import pytest

import habits.notifications as notifications_package
from habits.domain.models import HabitStats
from habits.forms.models import NAME_REQUIRED_ERROR, HabitFormData
from habits.forms.validation import validate_habit_form
from habits.module_size import (
    CONTENT_LINE_LIMIT,
    count_content_lines,
    ensure_modules_within_limit,
    find_oversized_modules,
    format_oversized_modules_message,
)
from habits.persistence.completions_repo import mark_completed_db
from habits.persistence.habits_repo import create_habit_db
from habits.persistence.schema import init_db
from habits.registration import (
    REGISTRATION_DUPLICATE_MESSAGE,
    REGISTRATION_SUCCESS_MESSAGE,
    duplicate_warning,
    register_today,
)
from habits.state.loader import load_app_state

ROOT = Path(__file__).resolve().parents[1]
HABITS_DIR = ROOT / "habits"
TESTS_DIR = ROOT / "tests"
README_PATH = ROOT / "README.md"
TASKS_PATH = ROOT / "specs" / "006-code-organization" / "tasks.md"

APPROVED_DEPENDENCIES = {"flet", "pytest", "pytest-cov"}
LEGACY_MODULES = (
    "core.py",
    "storage.py",
    "app_state.py",
    "habit_form.py",
    "notifications.py",
)
LEGACY_IMPORTS = (
    "habits.core",
    "habits.storage",
    "habits.app_state",
    "habits.habit_form",
)
EXPECTED_MODULES = (
    "domain/models.py",
    "domain/habits.py",
    "domain/streaks.py",
    "domain/recovery.py",
    "domain/heatmap.py",
    "persistence/schema.py",
    "persistence/habits_repo.py",
    "persistence/completions_repo.py",
    "persistence/reminders_repo.py",
    "state/models.py",
    "state/app_state.py",
    "state/loader.py",
    "forms/models.py",
    "forms/validation.py",
    "forms/service.py",
    "ui/common.py",
    "ui/page.py",
    "ui/sidebar.py",
    "ui/detail_header.py",
    "ui/stats.py",
    "ui/heatmap.py",
    "ui/registration_panel.py",
    "ui/empty.py",
    "ui/form_dialog.py",
    "ui/delete_dialog.py",
    "ui/recovery_dialog.py",
    "ui/reminder_dialog.py",
    "notifications/models.py",
    "notifications/common.py",
    "notifications/notifier.py",
    "notifications/scheduler.py",
)
EXPECTED_TASKS = (
    "1.1", "1.2", "1.3", "1.4", "1.5",
    "2.1", "2.2", "2.3", "2.4", "2.5",
    "3.1", "3.2", "3.3", "3.4", "3.5",
    "4.1", "4.2", "4.3", "4.4",
    "5.1", "5.2", "5.3", "5.4",
    "6.1", "6.2", "6.3", "6.4", "6.5", "6.6",
    "7.1", "7.2", "7.3", "7.4",
    "8.1", "8.2", "8.3",
    "9.1", "9.2", "9.3",
)
COVERAGE_PATTERN = re.compile(
    r"`(domain/|persistence/|state/|forms/|module_size\.py)` (\d+) %"
)
TOTAL_COVERAGE_PATTERN = re.compile(r"total del conjunto (\d+) %")
TASK_PATTERN = re.compile(r"^- \[( |x)\] \*\*Tarea ([\d.]+):\*\*", re.MULTILINE)


def production_files() -> list[Path]:
    """Listar los módulos de producción sin cachés."""
    return [
        path
        for path in sorted(HABITS_DIR.rglob("*.py"))
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


def dependency_name(requirement: str) -> str:
    """Extraer el nombre de un requisito sin versión ni extras."""
    name = requirement.split(";")[0]
    for separator in ("==", ">=", "<=", "~=", "!=", ">", "<", "["):
        name = name.split(separator)[0]
    return name.strip().lower()


class TestCompletionCriteria:
    """Criterios de finalización de la spec 006 — Tarea 9.3."""

    def test_criterion_1_all_production_modules_respect_the_limit(self):
        """Criterio 1: ningún módulo supera las 250 líneas con contenido."""
        files = production_files()

        assert files
        assert find_oversized_modules(HABITS_DIR) == []
        counts = {
            path.relative_to(HABITS_DIR).as_posix(): count_content_lines(
                path.read_text(encoding="utf-8")
            )
            for path in files
        }
        assert counts
        assert max(counts.values()) <= CONTENT_LINE_LIMIT
        ensure_modules_within_limit(HABITS_DIR)

    def test_criterion_2_monoliths_were_split_by_responsibility(self):
        """Criterio 2: los monolíticos se sustituyeron por módulos por capa."""
        for legacy in LEGACY_MODULES:
            assert not (HABITS_DIR / legacy).exists()

        for relative_path in EXPECTED_MODULES:
            path = HABITS_DIR / relative_path
            assert path.exists(), relative_path
            assert count_content_lines(
                path.read_text(encoding="utf-8")
            ) > 0, relative_path

    def test_criterion_3_internal_imports_use_the_new_locations(self):
        """Criterio 3: no quedan imports antiguos ni fachadas de compatibilidad."""
        modules: set[str] = set()
        for path in production_files() + [
            path
            for path in sorted(TESTS_DIR.rglob("*.py"))
            if "__pycache__" not in path.parts
        ]:
            modules.update(imported_modules(path))

        stale = sorted(
            module
            for module in modules
            if any(
                module == legacy or module.startswith(f"{legacy}.")
                for legacy in LEGACY_IMPORTS
            )
        )

        assert stale == []
        assert not hasattr(notifications_package, "SystemNotifier")
        assert not hasattr(notifications_package, "SystemScheduler")

    def test_criterion_4_size_guard_lists_every_offender(self, tmp_path):
        """Criterio 4: la guardia recorre el paquete y lista todos los infractores."""
        assert (TESTS_DIR / "test_module_size.py").exists()
        assert find_oversized_modules(HABITS_DIR) == []
        assert format_oversized_modules_message([]) == ""

        for name in ("alpha.py", "beta.py"):
            (tmp_path / name).write_text(
                "\n".join(["value = 1"] * (CONTENT_LINE_LIMIT + 1)),
                encoding="utf-8",
            )

        offenders = find_oversized_modules(tmp_path)

        assert [path for path, _ in offenders] == ["alpha.py", "beta.py"]
        with pytest.raises(AssertionError) as error:
            ensure_modules_within_limit(tmp_path)

        message = str(error.value)
        assert "alpha.py" in message
        assert "beta.py" in message
        assert f"{CONTENT_LINE_LIMIT + 1} líneas" in message

    def test_criterion_5_suite_and_coverage_meet_the_minimum(self):
        """Criterio 5: la cobertura documentada de la lógica supera el 80 %."""
        readme = README_PATH.read_text(encoding="utf-8")
        coverage = {
            module: int(percentage)
            for module, percentage in COVERAGE_PATTERN.findall(readme)
        }

        assert set(coverage) == {
            "domain/",
            "persistence/",
            "state/",
            "forms/",
            "module_size.py",
        }
        assert all(percentage >= 80 for percentage in coverage.values())
        total = TOTAL_COVERAGE_PATTERN.search(readme)
        assert total is not None
        assert int(total.group(1)) >= 80
        assert ".venv\\Scripts\\python.exe -m pytest -q" in readme

    def test_criterion_6_behavior_texts_and_data_are_preserved(self, tmp_path):
        """Criterio 6: flujos, textos públicos, rachas y heatmap no cambian."""
        db_path = str(tmp_path / "habits.db")
        init_db(db_path)
        today = date.today()
        habit_id = create_habit_db(
            "Leer",
            (today - timedelta(days=1)).isoformat(),
            "book",
            db_path,
        )

        first = register_today(habit_id, today, db_path)
        second = register_today(habit_id, today, db_path)

        assert first.success is True
        assert first.message == REGISTRATION_SUCCESS_MESSAGE
        assert second.success is False
        assert second.message == REGISTRATION_DUPLICATE_MESSAGE
        assert duplicate_warning("Leer") == "⚠️ «Leer» ya está registrado hoy."

        state = load_app_state(db_path, today)
        assert state.selected is not None
        assert state.selected.habit.name == "Leer"
        assert state.selected.stats == HabitStats(
            current_streak=1,
            best_streak=1,
            registered_days=1,
        )
        assert [card.value for card in state.stat_cards()] == [1, 1, 1]
        assert len(state.heatmap_cells()) == 35

        with pytest.raises(ValueError) as error:
            validate_habit_form(HabitFormData(name="   "), today)

        assert str(error.value) == NAME_REQUIRED_ERROR

    def test_criterion_7_readme_documents_the_rule_and_structure(self):
        """Criterio 7: la documentación describe límite, conteo, exclusiones y capas."""
        readme = README_PATH.read_text(encoding="utf-8")
        lowered = readme.lower()

        assert "250" in readme
        assert "líneas con contenido" in lowered
        for term in (
            "vacías",
            "comentarios",
            "docstring",
            "cadenas multilínea",
            "al final",
        ):
            assert term in lowered
        for excluded in (
            "__pycache__",
            ".venv",
            "venv",
            "build",
            "dist",
            "node_modules",
            ".pytest_cache",
            ".mypy_cache",
            ".ruff_cache",
            ".git",
        ):
            assert excluded in readme
        for package in (
            "habits/domain/",
            "habits/persistence/",
            "habits/state/",
            "habits/forms/",
            "habits/ui/",
            "habits/notifications/",
        ):
            assert package in readme
        assert "## Estructura del proyecto" in readme

    def test_criterion_8_no_new_dependencies_or_schema_changes(self, tmp_path):
        """Criterio 8: dependencias y esquema SQLite sin cambios."""
        db_path = str(tmp_path / "habits.db")
        init_db(db_path)

        with sqlite3.connect(db_path) as conn:
            tables = {
                row[0]
                for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                )
                if not row[0].startswith("sqlite_")
            }
            columns = {
                table: [
                    row[1]
                    for row in conn.execute(f"PRAGMA table_info({table})")
                ]
                for table in tables
            }

        assert tables == {"habits", "completions", "reminders"}
        assert columns == {
            "habits": ["id", "name", "start_date", "icon"],
            "completions": [
                "id",
                "habit_id",
                "completed_date",
                "recovered",
            ],
            "reminders": [
                "habit_id",
                "enabled",
                "reminder_time",
                "effective_from",
                "last_notified_on",
            ],
        }

        requirements = {
            dependency_name(line)
            for line in (ROOT / "requirements.txt")
            .read_text(encoding="utf-8")
            .splitlines()
            if line.strip() and not line.strip().startswith("#")
        }
        assert requirements == APPROVED_DEPENDENCIES

    def test_all_tasks_are_marked_complete(self):
        """Cierre: `tasks.md` no deja ninguna tarea pendiente."""
        tasks = TASKS_PATH.read_text(encoding="utf-8")
        matches = TASK_PATTERN.findall(tasks)

        assert matches
        assert [task for mark, task in matches if mark != "x"] == []
        assert {task for _, task in matches} == set(EXPECTED_TASKS)
        assert "- [ ]" not in tasks
