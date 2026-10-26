# spec: 002-ui-redesign
"""Tests de estadísticas y heatmap — Fase 5, RF-3 y RF-4.

Verifican los modelos puros que consume la interfaz, sin depender de Flet.
"""

import os
import tempfile
from datetime import date, timedelta

from habits.app_state import (
    HEATMAP_COMPLETED_LABEL,
    HEATMAP_NOT_COMPLETED_LABEL,
    HEATMAP_TITLE,
    STAT_BEST_STREAK_LABEL,
    STAT_CURRENT_STREAK_LABEL,
    STAT_REGISTERED_DAYS_LABEL,
    AppState,
    StatCard,
    load_app_state,
)
from habits.storage import create_habit_db, init_db, mark_completed_db

TODAY = date(2024, 10, 24)


class TestStatCards:
    """Tests de las tarjetas de estadísticas — Tarea 5.1, RF-3.2 a RF-3.6."""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_habits.db")
        init_db(self.db_path)

    def teardown_method(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def _create_habit(self, completed_days: tuple[date, ...] = ()) -> int:
        habit_id = create_habit_db(
            "Leer", "2024-10-01", icon="book", db_path=self.db_path
        )
        for day in completed_days:
            mark_completed_db(habit_id, day.isoformat(), db_path=self.db_path)
        return habit_id

    def test_without_habits_there_are_no_cards(self):
        """RF-3.2: Sin hábito seleccionado no se muestran tarjetas."""
        state = load_app_state(self.db_path, today=TODAY)

        assert state.stat_cards() == []

    def test_habit_without_records_shows_three_zeros(self):
        """RF-3.5: Un hábito sin registros muestra 0 en las tres tarjetas."""
        self._create_habit()
        state = load_app_state(self.db_path, today=TODAY)

        assert state.stat_cards() == [
            StatCard(label=STAT_CURRENT_STREAK_LABEL, value=0),
            StatCard(label=STAT_BEST_STREAK_LABEL, value=0),
            StatCard(label=STAT_REGISTERED_DAYS_LABEL, value=0),
        ]

    def test_cards_reflect_habit_stats(self):
        """RF-3.2, RF-3.3, RF-3.4: Las tarjetas usan las estadísticas reales."""
        self._create_habit(
            (
                TODAY,
                TODAY - timedelta(days=1),
                TODAY - timedelta(days=3),
            )
        )
        state = load_app_state(self.db_path, today=TODAY)

        assert state.stat_cards() == [
            StatCard(label=STAT_CURRENT_STREAK_LABEL, value=2),
            StatCard(label=STAT_BEST_STREAK_LABEL, value=2),
            StatCard(label=STAT_REGISTERED_DAYS_LABEL, value=3),
        ]

    def test_cards_follow_the_selected_habit(self):
        """RF-3.2: Las tarjetas corresponden al hábito seleccionado."""
        active_id = self._create_habit(
            (TODAY, TODAY - timedelta(days=1))
        )
        idle_id = create_habit_db(
            "Dormir", "2024-10-01", db_path=self.db_path
        )
        state = load_app_state(self.db_path, today=TODAY)

        state.select(idle_id)

        assert state.stat_cards() == [
            StatCard(label=STAT_CURRENT_STREAK_LABEL, value=0),
            StatCard(label=STAT_BEST_STREAK_LABEL, value=0),
            StatCard(label=STAT_REGISTERED_DAYS_LABEL, value=0),
        ]

        state.select(active_id)
        assert state.stat_cards()[0].value == 2


class TestHeatmapModel:
    """Tests del modelo del heatmap — Tarea 5.2, RF-4.1 a RF-4.6."""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_habits.db")
        init_db(self.db_path)

    def teardown_method(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def _create_habit(self, completed_days: tuple[date, ...] = ()) -> int:
        habit_id = create_habit_db(
            "Leer", "2024-09-01", icon="book", db_path=self.db_path
        )
        for day in completed_days:
            mark_completed_db(habit_id, day.isoformat(), db_path=self.db_path)
        return habit_id

    def test_without_habits_heatmap_is_empty(self):
        """RF-4.1: Sin hábito seleccionado no hay celdas que pintar."""
        state = load_app_state(self.db_path, today=TODAY)

        assert state.heatmap_cells() == []
        assert state.heatmap_rows() == []

    def test_state_keeps_today_for_heatmap(self):
        """RF-4.1: El estado conserva la fecha usada para construir el heatmap."""
        self._create_habit()
        state = load_app_state(self.db_path, today=TODAY)

        assert state.today == TODAY

    def test_heatmap_has_five_weeks_including_today(self):
        """RF-4.1: 35 celdas que incluyen la fecha actual."""
        self._create_habit()
        state = load_app_state(self.db_path, today=TODAY)

        cells = state.heatmap_cells()

        assert len(cells) == 35
        assert cells[0].date == TODAY - timedelta(days=TODAY.weekday() + 28)
        assert cells[-1].date == TODAY + timedelta(days=6 - TODAY.weekday())
        assert any(cell.date == TODAY for cell in cells)

    def test_heatmap_rows_are_monday_to_sunday_by_week(self):
        """RF-4.2: 7 filas de lunes a domingo y 5 columnas de semanas."""
        self._create_habit()
        state = load_app_state(self.db_path, today=TODAY)

        rows = state.heatmap_rows()

        assert len(rows) == 7
        assert all(len(row) == 5 for row in rows)
        assert [row[0].weekday for row in rows] == list(range(7))
        assert all([cell.week for cell in row] == list(range(5)) for row in rows)
        assert rows[0][0].date.weekday() == 0
        assert rows[6][4].date.weekday() == 6

    def test_heatmap_marks_completed_and_future_days(self):
        """RF-4.3, RF-4.4: Completado, futuro y hoy quedan identificados."""
        self._create_habit((TODAY, TODAY - timedelta(days=1)))
        state = load_app_state(self.db_path, today=TODAY)

        cells = state.heatmap_cells()
        today_cell = next(cell for cell in cells if cell.date == TODAY)
        yesterday_cell = next(
            cell for cell in cells if cell.date == TODAY - timedelta(days=1)
        )
        future_cell = next(
            cell
            for cell in cells
            if cell.date == TODAY + timedelta(days=1)
        )
        old_cell = next(
            cell
            for cell in cells
            if cell.date == TODAY - timedelta(days=7)
        )

        assert today_cell.completed is True
        assert today_cell.is_today is True
        assert today_cell.is_future is False
        assert yesterday_cell.completed is True
        assert future_cell.completed is False
        assert future_cell.is_future is True
        assert old_cell.completed is False
        assert old_cell.is_future is False

    def test_heatmap_without_records_has_no_completed_days(self):
        """RF-4.6: Sin registros, los días disponibles no están completados."""
        self._create_habit()
        state = load_app_state(self.db_path, today=TODAY)

        cells = state.heatmap_cells()

        assert not any(cell.completed for cell in cells)
        assert all(not cell.completed for cell in cells if not cell.is_future)

    def test_labels_are_defined_in_spanish(self):
        """RF-4.1, RF-4.5: Título y leyenda visibles en español."""
        assert HEATMAP_TITLE == "Actividad (últimas 5 semanas)"
        assert HEATMAP_COMPLETED_LABEL == "Completado"
        assert HEATMAP_NOT_COMPLETED_LABEL == "No completado"


class TestRefreshAfterRegistration:
    """Tests del refresco de estadísticas y heatmap — Tarea 5.3, RF-3.6, RF-4.7."""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_habits.db")
        init_db(self.db_path)
        self.habit_id = create_habit_db(
            "Leer", "2024-10-01", icon="book", db_path=self.db_path
        )

    def teardown_method(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def _today_cell(self, state: AppState):
        return next(
            cell for cell in state.heatmap_cells() if cell.date == TODAY
        )

    def test_reloading_state_updates_cards_and_today_cell(self):
        """RF-3.6, RF-4.7: Tras registrar hoy, el nuevo estado lo refleja."""
        before = load_app_state(self.db_path, today=TODAY)
        assert [card.value for card in before.stat_cards()] == [0, 0, 0]
        assert self._today_cell(before).completed is False

        mark_completed_db(
            self.habit_id, TODAY.isoformat(), db_path=self.db_path
        )
        after = load_app_state(self.db_path, today=TODAY)

        assert [card.value for card in after.stat_cards()] == [1, 1, 1]
        assert self._today_cell(after).completed is True
        assert after.sidebar_items()[0].streak == 1
