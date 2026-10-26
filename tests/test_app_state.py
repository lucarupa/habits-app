# spec: 002-ui-redesign
"""Tests para el cargador de estado — Tarea 3.1, RF-1.1, RF-1.3, RF-1.5, RFN-3."""

import os
import tempfile
from datetime import date, timedelta

import pytest

from habits.app_state import (
    AppState,
    DetailHeader,
    EmptyState,
    HabitState,
    SidebarItem,
    load_app_state,
)
from habits.core import HabitStats
from habits.storage import create_habit_db, init_db, mark_completed_db


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
        """RF-1.1, RFN-3: Obtiene hábitos y fechas desde storage."""
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

    def test_load_app_state_computes_stats_with_core(self):
        """RF-1.1, RFN-3: Las estadísticas se calculan con core, no en la UI."""
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
