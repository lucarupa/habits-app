# spec: 002-ui-redesign
# spec: 004-duplicate-warning-streak-recovery
# spec: 005-local-reminders
"""Tests para el cargador de estado — Tarea 3.1, RF-1.1, RF-1.3, RF-1.5, RFN-3."""

import ast
import os
import tempfile
from datetime import date, timedelta
from pathlib import Path

import pytest

from habits.state.app_state import AppState
from habits.state.loader import load_app_state
from habits.state.models import DetailHeader, EmptyState, HabitState, SidebarItem
from habits.domain.models import HabitStats
from habits.persistence.completions_repo import (
    mark_completed_db,
    mark_recovered_days_db,
)
from habits.persistence.habits_repo import create_habit_db, update_habit_db
from habits.persistence.reminders_repo import save_reminder_db
from habits.persistence.schema import init_db

ROOT = Path(__file__).resolve().parents[1]
HABITS_DIR = ROOT / "habits"
LEGACY_MODULE = "habits.app_state"
FORBIDDEN_STATE_IMPORTS = {"flet", "sqlite3"}


def imported_modules(path: Path) -> list[str]:
    """Extraer los módulos importados por un archivo Python."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    modules: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.append(node.module)

    return modules


class TestStatePackage:
    """Verificación del paquete de estado — Tarea 4.4."""

    def test_legacy_app_state_module_is_gone(self):
        """RF-2.5, RF-5.1: el módulo monolítico y sus imports desaparecen."""
        assert not (HABITS_DIR / "app_state.py").exists()

        offenders = [
            path.relative_to(ROOT).as_posix()
            for directory in ("habits", "scripts", "tests")
            for path in sorted((ROOT / directory).rglob("*.py"))
            if LEGACY_MODULE in imported_modules(path)
        ]

        assert offenders == []

    def test_state_package_does_not_import_flet_or_sqlite(self):
        """RF-2.6, RF-2.7: el estado no depende de la interfaz ni de SQLite."""
        offenders = [
            f"{path.name}: {module}"
            for path in sorted((HABITS_DIR / "state").glob("*.py"))
            for module in imported_modules(path)
            if module.split(".")[0] in FORBIDDEN_STATE_IMPORTS
        ]

        assert offenders == []


class TestLoadAppState:
    """Tests para load_app_state() y AppState — Tarea 3.1."""

    def setup_method(self):
        """Crear una base de datos temporal para cada test."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_habits.db")
        init_db(self.db_path)
        self.today = date(2024, 10, 24)

    def teardown_method(self):
        """Limpiar la base de datos temporal después de cada test."""
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_load_app_state_empty(self):
        """RF-1.1, RF-1.5: Sin hábitos no hay selección."""
        state = load_app_state(self.db_path, today=self.today)

        assert isinstance(state, AppState)
        assert state.habits == []
        assert state.selected_id is None
        assert state.selected is None

    def test_load_app_state_builds_habits_from_storage(self):
        """RF-1.1, RFN-3: Obtiene hábitos y fechas desde persistencia."""
        habit_id = create_habit_db(
            "Estudiar Python",
            "2024-10-01",
            icon="code",
            db_path=self.db_path,
        )
        yesterday = self.today - timedelta(days=1)
        mark_completed_db(habit_id, self.today.isoformat(), db_path=self.db_path)
        mark_completed_db(habit_id, yesterday.isoformat(), db_path=self.db_path)

        state = load_app_state(self.db_path, today=self.today)

        assert len(state.habits) == 1
        habit_state = state.habits[0]
        assert isinstance(habit_state, HabitState)
        assert habit_state.habit.id == habit_id
        assert habit_state.habit.name == "Estudiar Python"
        assert habit_state.habit.start_date == date(2024, 10, 1)
        assert habit_state.habit.icon == "code"
        assert habit_state.completed_dates == {self.today, yesterday}

    def test_load_app_state_computes_stats_with_domain(self):
        """RF-1.1, RFN-3: Las estadísticas se calculan con dominio, no en la UI."""
        habit_id = create_habit_db(
            "Leer", "2024-10-20", db_path=self.db_path
        )
        for day in (
            self.today - timedelta(days=1),
            self.today - timedelta(days=2),
            self.today - timedelta(days=3),
        ):
            mark_completed_db(habit_id, day.isoformat(), db_path=self.db_path)

        state = load_app_state(self.db_path, today=self.today)

        assert state.habits[0].stats == HabitStats(
            current_streak=0,
            best_streak=3,
            registered_days=3,
        )

    def test_load_app_state_sorts_by_streak_then_name(self):
        """RF-1.3: Orden por racha descendente y desempate alfabético."""
        zebra_id = create_habit_db("Zebra", "2024-10-01", db_path=self.db_path)
        beta_id = create_habit_db("Beta", "2024-10-01", db_path=self.db_path)
        alpha_id = create_habit_db("Alpha", "2024-10-01", db_path=self.db_path)

        mark_completed_db(zebra_id, self.today.isoformat(), db_path=self.db_path)
        mark_completed_db(
            zebra_id,
            (self.today - timedelta(days=1)).isoformat(),
            db_path=self.db_path,
        )
        mark_completed_db(beta_id, self.today.isoformat(), db_path=self.db_path)
        mark_completed_db(alpha_id, self.today.isoformat(), db_path=self.db_path)

        state = load_app_state(self.db_path, today=self.today)

        assert [habit_state.habit.name for habit_state in state.habits] == [
            "Zebra",
            "Alpha",
            "Beta",
        ]
        assert [habit_state.habit.id for habit_state in state.habits] == [
            zebra_id,
            alpha_id,
            beta_id,
        ]

    def test_load_app_state_selects_first_habit(self):
        """RF-1.5: Se selecciona automáticamente el primero de la lista ordenada."""
        low_id = create_habit_db("Alpha", "2024-10-01", db_path=self.db_path)
        high_id = create_habit_db("Zebra", "2024-10-01", db_path=self.db_path)
        mark_completed_db(low_id, self.today.isoformat(), db_path=self.db_path)
        mark_completed_db(high_id, self.today.isoformat(), db_path=self.db_path)
        mark_completed_db(
            high_id,
            (self.today - timedelta(days=1)).isoformat(),
            db_path=self.db_path,
        )

        state = load_app_state(self.db_path, today=self.today)

        assert state.selected_id == high_id
        assert state.selected is not None
        assert state.selected.habit.id == high_id


class TestRecoveredDaysState:
    """Estado con días recuperados — Tarea 3.1.

    RF-2.1, RF-2.2, RF-2.9, RF-2.10, RF-2.11, RF-2.12 y RF-2.15: el estado
    carga las fechas recuperadas, calcula el hueco del hábito seleccionado,
    excluye los recuperados de “Días registrados” y los marca en el heatmap.
    """

    def setup_method(self):
        """Crear una base de datos temporal para cada test."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_habits.db")
        init_db(self.db_path)
        self.today = date(2026, 10, 26)

    def teardown_method(self):
        """Limpiar la base de datos temporal después de cada test."""
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def _days_ago(self, count: int) -> date:
        """Devolver la fecha situada `count` días antes de hoy."""
        return self.today - timedelta(days=count)

    def test_load_app_state_reads_recovered_dates(self):
        """RF-2.15: el estado conserva el subconjunto recuperado de la base."""
        habit_id = create_habit_db(
            "Estudiar", "2026-10-01", db_path=self.db_path
        )
        mark_completed_db(
            habit_id, self.today.isoformat(), db_path=self.db_path
        )
        mark_recovered_days_db(
            habit_id,
            [self._days_ago(1).isoformat()],
            self.db_path,
        )

        state = load_app_state(self.db_path, today=self.today)

        habit_state = state.habits[0]
        assert habit_state.completed_dates == {
            self._days_ago(1),
            self.today,
        }
        assert habit_state.recovered_dates == {self._days_ago(1)}

    def test_recoverable_gap_follows_selected_habit(self):
        """RF-2.1, RF-2.12: el hueco corresponde al hábito seleccionado."""
        gap_id = create_habit_db(
            "Con hueco", "2026-10-01", db_path=self.db_path
        )
        full_id = create_habit_db(
            "Sin hueco", "2026-10-01", db_path=self.db_path
        )
        for day in (self._days_ago(3), self.today):
            mark_completed_db(gap_id, day.isoformat(), db_path=self.db_path)
        for day in (self._days_ago(2), self._days_ago(1), self.today):
            mark_completed_db(full_id, day.isoformat(), db_path=self.db_path)

        state = load_app_state(self.db_path, today=self.today)

        assert state.selected is not None
        assert state.selected.habit.id == full_id
        assert state.recoverable_gap is None

        state.select(gap_id)

        assert state.recoverable_gap is not None
        assert state.recoverable_gap.dates == (
            self._days_ago(2),
            self._days_ago(1),
        )

    def test_recoverable_gap_is_none_for_three_days(self):
        """RF-2.2: un hueco de tres días no ofrece recuperación."""
        habit_id = create_habit_db(
            "Con hueco largo", "2026-10-01", db_path=self.db_path
        )
        for day in (self._days_ago(4), self.today):
            mark_completed_db(habit_id, day.isoformat(), db_path=self.db_path)

        state = load_app_state(self.db_path, today=self.today)

        assert state.selected is not None
        assert state.selected.habit.id == habit_id
        assert state.recoverable_gap is None

    def test_stats_cards_exclude_recovered_from_registered_days(self):
        """RF-2.9, RF-2.10: los recuperados suman a la racha, no a los días."""
        habit_id = create_habit_db(
            "Estudiar", "2026-10-01", db_path=self.db_path
        )
        mark_completed_db(
            habit_id, self._days_ago(3).isoformat(), db_path=self.db_path
        )
        mark_completed_db(
            habit_id, self.today.isoformat(), db_path=self.db_path
        )
        mark_recovered_days_db(
            habit_id,
            [
                self._days_ago(2).isoformat(),
                self._days_ago(1).isoformat(),
            ],
            self.db_path,
        )

        state = load_app_state(self.db_path, today=self.today)

        assert [card.value for card in state.stat_cards()] == [4, 4, 2]

    def test_heatmap_cells_flag_recovered_days(self):
        """RF-2.11: el heatmap recibe las fechas recuperadas."""
        habit_id = create_habit_db(
            "Estudiar", "2026-10-01", db_path=self.db_path
        )
        mark_completed_db(
            habit_id, self.today.isoformat(), db_path=self.db_path
        )
        mark_recovered_days_db(
            habit_id,
            [self._days_ago(1).isoformat()],
            self.db_path,
        )

        state = load_app_state(self.db_path, today=self.today)
        cells = {cell.date: cell for cell in state.heatmap_cells()}

        assert cells[self._days_ago(1)].completed is True
        assert cells[self._days_ago(1)].recovered is True
        assert cells[self.today].completed is True
        assert cells[self.today].recovered is False
        assert cells[self._days_ago(2)].completed is False
        assert cells[self._days_ago(2)].recovered is False


class TestSidebarItems:
    """Tests del modelo de la barra lateral — Tarea 3.2, RF-1.2, RF-1.4, RF-7.2."""

    def setup_method(self):
        """Crear una base de datos temporal para cada test."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_habits.db")
        init_db(self.db_path)
        self.today = date(2024, 10, 24)

    def teardown_method(self):
        """Limpiar la base de datos temporal después de cada test."""
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def _create_habit(
        self,
        name: str,
        icon: str = "book",
        completed_days: tuple[date, ...] = (),
    ) -> int:
        """Crear un hábito con sus fechas completadas."""
        habit_id = create_habit_db(
            name, "2024-10-01", icon=icon, db_path=self.db_path
        )
        for day in completed_days:
            mark_completed_db(habit_id, day.isoformat(), db_path=self.db_path)
        return habit_id

    def test_sidebar_items_include_icon_name_and_streak(self):
        """RF-1.2: Cada elemento expone icono, nombre y racha actual."""
        habit_id = self._create_habit(
            "Estudiar Python",
            icon="code",
            completed_days=(
                self.today,
                self.today - timedelta(days=1),
            ),
        )

        state = load_app_state(self.db_path, today=self.today)

        assert state.sidebar_items() == [
            SidebarItem(
                habit_id=habit_id,
                icon="code",
                name="Estudiar Python",
                streak=2,
                selected=True,
            )
        ]

    def test_sidebar_items_preserve_ordered_habits(self):
        """RF-1.2, RF-1.3: El orden de la barra es el del estado cargado."""
        self._create_habit(
            "Zebra",
            completed_days=(
                self.today,
                self.today - timedelta(days=1),
            ),
        )
        self._create_habit("Beta", completed_days=(self.today,))
        self._create_habit("Alpha", completed_days=(self.today,))

        state = load_app_state(self.db_path, today=self.today)

        assert [item.name for item in state.sidebar_items()] == [
            "Zebra",
            "Alpha",
            "Beta",
        ]
        assert [item.selected for item in state.sidebar_items()] == [
            True,
            False,
            False,
        ]

    def test_select_changes_highlighted_item(self):
        """RF-1.4, RF-7.2: Seleccionar otro hábito mueve el resaltado."""
        first_id = self._create_habit("Alpha", completed_days=(self.today,))
        second_id = self._create_habit(
            "Zebra",
            completed_days=(
                self.today,
                self.today - timedelta(days=1),
            ),
        )
        state = load_app_state(self.db_path, today=self.today)

        state.select(second_id)

        assert state.selected_id == second_id
        assert [item.habit_id for item in state.sidebar_items()] == [
            second_id,
            first_id,
        ]
        assert [item.selected for item in state.sidebar_items()] == [
            True,
            False,
        ]

    def test_select_unknown_habit_raises(self):
        """RF-1.4: No se puede seleccionar un hábito inexistente."""
        self._create_habit("Alpha", completed_days=(self.today,))
        state = load_app_state(self.db_path, today=self.today)

        with pytest.raises(ValueError):
            state.select(999)


class TestDetailHeader:
    """Tests del encabezado de detalle — Tarea 3.3, RF-3.1, RF-7.4."""

    def setup_method(self):
        """Crear una base de datos temporal para cada test."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_habits.db")
        init_db(self.db_path)
        self.today = date(2024, 10, 24)

    def teardown_method(self):
        """Limpiar la base de datos temporal después de cada test."""
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_detail_header_without_habits_is_none(self):
        """RF-3.1: Sin hábitos no hay encabezado de detalle."""
        state = load_app_state(self.db_path, today=self.today)

        assert state.detail_header() is None

    def test_detail_header_contains_icon_name_subtitle_and_date(self):
        """RF-3.1, RF-7.4: Icono, nombre, subtítulo y fecha dd/mm/aaaa."""
        habit_id = create_habit_db(
            "Leer",
            "2024-01-05",
            icon="book",
            db_path=self.db_path,
        )

        state = load_app_state(self.db_path, today=self.today)

        assert state.detail_header() == DetailHeader(
            habit_id=habit_id,
            icon="book",
            name="Leer",
            subtitle="Hábito de estudio",
            start_date_label="05/01/2024",
        )

    def test_detail_header_follows_selection(self):
        """RF-3.1: El encabezado corresponde al hábito seleccionado."""
        first_id = create_habit_db(
            "Alpha", "2024-10-01", icon="code", db_path=self.db_path
        )
        second_id = create_habit_db(
            "Zebra", "2024-03-09", icon="science", db_path=self.db_path
        )
        state = load_app_state(self.db_path, today=self.today)

        state.select(second_id)

        header = state.detail_header()
        assert header is not None
        assert header.habit_id == second_id
        assert header.name == "Zebra"
        assert header.icon == "science"
        assert header.start_date_label == "09/03/2024"
        assert header.habit_id != first_id


class TestEmptyState:
    """Tests del estado vacío — Tarea 3.4, RF-6.1, RF-6.2, RF-6.4."""

    def setup_method(self):
        """Crear una base de datos temporal para cada test."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_habits.db")
        init_db(self.db_path)
        self.today = date(2024, 10, 24)

    def teardown_method(self):
        """Limpiar la base de datos temporal después de cada test."""
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_empty_state_without_habits(self):
        """RF-6.1, RF-6.2: Sin hábitos se expone el estado vacío."""
        state = load_app_state(self.db_path, today=self.today)

        assert state.is_empty is True
        assert state.empty_state() == EmptyState(
            sidebar_message="No hay hábitos aún",
            title="Crea tu primer hábito para empezar tu racha",
            button_label="+ Crear hábito",
        )

    def test_empty_state_with_habits_is_none(self):
        """RF-6.4: Con un hábito creado el estado vacío desaparece."""
        create_habit_db(
            "Leer", "2024-10-01", icon="book", db_path=self.db_path
        )

        state = load_app_state(self.db_path, today=self.today)

        assert state.is_empty is False
        assert state.empty_state() is None
        assert state.detail_header() is not None

    def test_empty_state_disappears_after_first_habit(self):
        """RF-6.4: Al crear el primer hábito se selecciona y se muestra su detalle."""
        empty = load_app_state(self.db_path, today=self.today)
        assert empty.empty_state() is not None

        habit_id = create_habit_db(
            "Estudiar Python",
            "2024-10-01",
            icon="code",
            db_path=self.db_path,
        )
        state = load_app_state(self.db_path, today=self.today)

        assert state.empty_state() is None
        assert state.selected_id == habit_id
        assert state.detail_header().habit_id == habit_id


class TestReminderState:
    """Estado con recordatorios — Tarea 3.1.

    RF-1.1, RF-1.3, RF-1.7 y RF-3.5: el estado expone la configuración del
    recordatorio del hábito seleccionado, los hábitos sin fila aparecen
    desactivados y el nombre actualizado del hábito se refleja al recargar.
    """

    def setup_method(self):
        """Crear una base de datos temporal para cada test."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_habits.db")
        init_db(self.db_path)
        self.today = date(2024, 10, 24)

    def teardown_method(self):
        """Limpiar la base de datos temporal después de cada test."""
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def _create_habit(self, name: str = "Leer") -> int:
        """Crear un hábito de prueba y devolver su identificador."""
        return create_habit_db(
            name, "2024-10-01", db_path=self.db_path
        )

    def _save_reminder(
        self,
        habit_id: int,
        enabled: bool = True,
        reminder_time: str | None = "20:00",
    ) -> None:
        """Guardar un recordatorio con fecha efectiva ya vigente."""
        save_reminder_db(
            habit_id,
            enabled,
            reminder_time,
            self.today.isoformat(),
            db_path=self.db_path,
        )

    def test_load_app_state_includes_reminder_configuration(self):
        """RF-1.1, RF-1.7: el estado expone activación, hora y etiqueta."""
        habit_id = self._create_habit()
        self._save_reminder(habit_id, enabled=True, reminder_time="20:00")

        state = load_app_state(self.db_path, today=self.today)

        assert state.selected is not None
        assert state.selected.reminder_enabled is True
        assert state.selected.reminder_time == "20:00"
        assert state.selected.reminder_label == "Recordatorio a las 20:00"
        assert state.reminder_label == "Recordatorio a las 20:00"

    def test_habit_without_reminder_is_disabled(self):
        """RF-1.3: un hábito sin fila aparece con el recordatorio desactivado."""
        self._create_habit()

        state = load_app_state(self.db_path, today=self.today)

        assert state.selected is not None
        assert state.selected.reminder_enabled is False
        assert state.selected.reminder_time is None
        assert state.selected.reminder_label == "Sin recordatorio"
        assert state.reminder_label == "Sin recordatorio"

    def test_disabled_reminder_keeps_time_but_shows_disabled(self):
        """RF-1.1: desactivado conserva la hora guardada pero no la muestra."""
        habit_id = self._create_habit()
        self._save_reminder(habit_id, enabled=False, reminder_time="20:00")

        state = load_app_state(self.db_path, today=self.today)

        assert state.selected is not None
        assert state.selected.reminder_enabled is False
        assert state.selected.reminder_time == "20:00"
        assert state.reminder_label == "Sin recordatorio"

    def test_reminder_label_follows_selected_habit(self):
        """RF-1.1: la etiqueta corresponde al hábito seleccionado."""
        first_id = self._create_habit("Alpha")
        second_id = self._create_habit("Zebra")
        self._save_reminder(first_id, reminder_time="07:30")
        self._save_reminder(second_id, reminder_time="21:15")

        state = load_app_state(self.db_path, today=self.today)

        assert state.selected is not None
        assert state.selected.habit.id == first_id
        assert state.reminder_label == "Recordatorio a las 07:30"

        state.select(second_id)

        assert state.reminder_label == "Recordatorio a las 21:15"

    def test_reminder_label_without_habits_is_disabled(self):
        """RF-1.1: sin hábito seleccionado no hay recordatorio activo."""
        state = load_app_state(self.db_path, today=self.today)

        assert state.selected is None
        assert state.reminder_label == "Sin recordatorio"

    def test_reminder_configuration_survives_reload(self):
        """RF-1.7: cerrar y volver a abrir conserva activación y hora."""
        habit_id = self._create_habit()
        self._save_reminder(habit_id, enabled=True, reminder_time="18:45")

        first_state = load_app_state(self.db_path, today=self.today)
        second_state = load_app_state(self.db_path, today=self.today)

        assert first_state.selected is not None
        assert second_state.selected is not None
        assert second_state.selected.reminder_enabled is True
        assert second_state.selected.reminder_time == "18:45"

    def test_renamed_habit_keeps_reminder_and_uses_new_name(self):
        """RF-3.5: el nombre actualizado se refleja y el recordatorio se conserva."""
        habit_id = self._create_habit("Leer")
        self._save_reminder(habit_id, enabled=True, reminder_time="20:00")

        update_habit_db(
            habit_id,
            "Leer filosofía",
            "2024-10-01",
            db_path=self.db_path,
        )
        state = load_app_state(self.db_path, today=self.today)

        assert state.selected is not None
        assert state.selected.habit.name == "Leer filosofía"
        assert state.selected.reminder_enabled is True
        assert state.selected.reminder_time == "20:00"
        assert state.reminder_label == "Recordatorio a las 20:00"
