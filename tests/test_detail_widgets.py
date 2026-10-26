# spec: 002-ui-redesign
"""Tests de los widgets de estadísticas y heatmap — Tareas 5.1 a 5.3.

Se ejecutan con el intérprete del proyecto (`.venv`), que tiene Flet instalado.
"""

import os
import tempfile
from datetime import date, timedelta

import pytest

pytest.importorskip("flet")

from habits.app import ActivityHeatmap, HabitStatsCards, Sidebar
from habits.app_state import (
    HEATMAP_COMPLETED_LABEL,
    HEATMAP_NOT_COMPLETED_LABEL,
    HEATMAP_TITLE,
    STAT_BEST_STREAK_LABEL,
    STAT_CURRENT_STREAK_LABEL,
    STAT_REGISTERED_DAYS_LABEL,
    AppState,
    load_app_state,
)
from habits.storage import create_habit_db, init_db, mark_completed_db
from habits.theme import ACCENT_GREEN, HEATMAP_EMPTY, HEATMAP_FUTURE

TODAY = date(2024, 10, 24)


def collect_texts(control) -> list[str]:
    """Recorrer un árbol de controles Flet y recoger sus textos."""
    texts: list[str] = []
    value = getattr(control, "value", None)
    if isinstance(value, str):
        texts.append(value)
    for child in getattr(control, "controls", None) or []:
        texts.extend(collect_texts(child))
    content = getattr(control, "content", None)
    if content is not None:
        texts.extend(collect_texts(content))
    return texts


class TestHabitStatsCards:
    """Tests de las tarjetas de estadísticas — Tarea 5.1."""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_habits.db")
        init_db(self.db_path)

    def teardown_method(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def _load_state(self, completed_days: tuple[date, ...] = ()) -> AppState:
        habit_id = create_habit_db(
            "Leer", "2024-10-01", icon="book", db_path=self.db_path
        )
        for day in completed_days:
            mark_completed_db(habit_id, day.isoformat(), db_path=self.db_path)
        return load_app_state(self.db_path, today=TODAY)

    def test_shows_three_cards_with_labels_and_values(self):
        """RF-3.2, RF-3.3, RF-3.4: Tres tarjetas con sus valores."""
        state = self._load_state(
            (TODAY, TODAY - timedelta(days=1))
        )

        cards = HabitStatsCards(state=state)

        assert cards.visible is True
        assert [card.label for card in cards.cards] == [
            STAT_CURRENT_STREAK_LABEL,
            STAT_BEST_STREAK_LABEL,
            STAT_REGISTERED_DAYS_LABEL,
        ]
        assert [card.value for card in cards.cards] == [2, 2, 2]
        assert len(cards._cards_row.controls) == 3

        for control, card in zip(cards._cards_row.controls, cards.cards):
            label, value = control.content.controls
            assert label.value == card.label
            assert value.value == str(card.value)

    def test_shows_zeros_without_records(self):
        """RF-3.5: Sin registros las tres tarjetas muestran 0."""
        state = self._load_state()

        cards = HabitStatsCards(state=state)

        assert [card.value for card in cards.cards] == [0, 0, 0]

    def test_hides_without_selected_habit(self):
        """RF-3.2: Sin hábito seleccionado no se muestran tarjetas."""
        cards = HabitStatsCards(state=AppState())

        assert cards.visible is False
        assert cards.cards == []
        assert cards._cards_row.controls == []


class TestActivityHeatmap:
    """Tests del heatmap — Tarea 5.2."""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_habits.db")
        init_db(self.db_path)

    def teardown_method(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def _load_state(self, completed_days: tuple[date, ...] = ()) -> AppState:
        habit_id = create_habit_db(
            "Leer", "2024-09-01", icon="book", db_path=self.db_path
        )
        for day in completed_days:
            mark_completed_db(habit_id, day.isoformat(), db_path=self.db_path)
        return load_app_state(self.db_path, today=TODAY)

    def _cell_control(self, heatmap: ActivityHeatmap, day: date):
        for row_index, row in enumerate(heatmap.rows):
            for column_index, cell in enumerate(row):
                if cell.date == day:
                    return heatmap._grid.controls[row_index].controls[
                        column_index
                    ]
        raise AssertionError(f"No se encontró la celda {day}")

    def test_draws_seven_rows_by_five_columns(self):
        """RF-4.1, RF-4.2: Cuadrícula de 7 filas por 5 columnas."""
        state = self._load_state()
        heatmap = ActivityHeatmap(state=state)

        assert heatmap.visible is True
        assert len(heatmap.rows) == 7
        assert all(len(row) == 5 for row in heatmap.rows)
        assert len(heatmap._grid.controls) == 7
        assert all(len(row.controls) == 5 for row in heatmap._grid.controls)

    def test_shows_title_and_legend(self):
        """RF-4.1, RF-4.5: Título y leyenda visibles."""
        state = self._load_state()
        heatmap = ActivityHeatmap(state=state)

        texts = collect_texts(heatmap)

        assert HEATMAP_TITLE in texts
        assert HEATMAP_NOT_COMPLETED_LABEL in texts
        assert HEATMAP_COMPLETED_LABEL in texts

    def test_distinguishes_completed_empty_today_and_future(self):
        """RF-4.3, RF-4.4: Estados visuales de las celdas."""
        state = self._load_state(
            (TODAY, TODAY - timedelta(days=1))
        )
        heatmap = ActivityHeatmap(state=state)

        today_cell = self._cell_control(heatmap, TODAY)
        completed_cell = self._cell_control(
            heatmap, TODAY - timedelta(days=1)
        )
        empty_cell = self._cell_control(heatmap, TODAY - timedelta(days=7))
        future_cell = self._cell_control(heatmap, TODAY + timedelta(days=1))

        assert today_cell.bgcolor == ACCENT_GREEN
        assert today_cell.border is not None
        assert completed_cell.bgcolor == ACCENT_GREEN
        assert completed_cell.border is None
        assert empty_cell.bgcolor == HEATMAP_EMPTY
        assert future_cell.bgcolor == HEATMAP_FUTURE

    def test_hides_without_selected_habit(self):
        """RF-4.1: Sin hábito seleccionado no se pinta el heatmap."""
        heatmap = ActivityHeatmap(state=AppState())

        assert heatmap.visible is False
        assert heatmap.rows == []
        assert heatmap._body.controls == []


class TestRefreshAfterRegistration:
    """Tests del refresco sin reiniciar — Tarea 5.3, RF-3.6, RF-4.7."""

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

    def _today_cell(self, heatmap: ActivityHeatmap):
        for row_index, row in enumerate(heatmap.rows):
            for column_index, cell in enumerate(row):
                if cell.date == TODAY:
                    return heatmap._grid.controls[row_index].controls[
                        column_index
                    ]
        raise AssertionError("No se encontró la celda de hoy")

    def test_refresh_updates_cards_heatmap_and_sidebar(self):
        """RF-3.6, RF-4.7: Al registrar hoy se refrescan las tres zonas."""
        before = load_app_state(self.db_path, today=TODAY)
        cards = HabitStatsCards(state=before)
        heatmap = ActivityHeatmap(state=before)
        sidebar = Sidebar(state=before)

        assert [card.value for card in cards.cards] == [0, 0, 0]
        assert self._today_cell(heatmap).bgcolor != ACCENT_GREEN

        mark_completed_db(
            self.habit_id, TODAY.isoformat(), db_path=self.db_path
        )
        after = load_app_state(self.db_path, today=TODAY)

        cards.state = after
        cards.refresh()
        heatmap.state = after
        heatmap.refresh()
        sidebar.state = after
        sidebar.refresh()

        assert [card.value for card in cards.cards] == [1, 1, 1]
        assert self._today_cell(heatmap).bgcolor == ACCENT_GREEN
        assert HEATMAP_COMPLETED_LABEL in collect_texts(heatmap)
        assert "🔥 1 día" in collect_texts(sidebar)


class TestCreateButtonLabels:
    """Los CTA no duplican el “+” del texto con un icono adicional."""

    def test_sidebar_new_button_does_not_repeat_the_plus(self):
        """RF-1.6: el botón muestra “+ Nuevo” una sola vez."""
        sidebar = Sidebar(state=AppState(today=TODAY))

        button = sidebar.content.controls[0].controls[2]

        assert button.content == "+ Nuevo"
        assert button.icon is None

    def test_empty_panel_button_does_not_repeat_the_plus(self):
        """RF-6.3: el botón muestra “+ Crear hábito” una sola vez."""
        from habits.app import EmptyDetailPanel

        panel = EmptyDetailPanel(state=AppState(today=TODAY))

        button = panel.content.controls[-1]

        assert button.content == "+ Crear hábito"
        assert button.icon is None
