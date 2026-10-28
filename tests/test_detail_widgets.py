# spec: 002-ui-redesign
# spec: 003-edit-delete-habits
"""Tests de los widgets de estadísticas y heatmap — Tareas 5.1 a 5.3.

Se ejecutan con el intérprete del proyecto (`.venv`), que tiene Flet instalado.
"""

import os
import tempfile
from datetime import date, timedelta

import pytest

pytest.importorskip("flet")

import flet as ft

from habits.ui.detail_header import HabitDetailHeader
from habits.ui.heatmap import ActivityHeatmap
from habits.ui.sidebar import Sidebar
from habits.ui.stats import HabitStatsCards
from habits.state.app_state import AppState
from habits.state.loader import load_app_state
from habits.state.models import (
    HEATMAP_COMPLETED_LABEL,
    HEATMAP_NOT_COMPLETED_LABEL,
    HEATMAP_RECOVERED_LABEL,
    HEATMAP_TITLE,
    STAT_BEST_STREAK_LABEL,
    STAT_CURRENT_STREAK_LABEL,
    STAT_REGISTERED_DAYS_LABEL,
)
from habits.persistence.completions_repo import (
    mark_completed_db,
    mark_recovered_days_db,
)
from habits.persistence.habits_repo import create_habit_db, get_habit_db
from habits.persistence.schema import init_db
from habits.theme import (
    ACCENT_GREEN,
    HEATMAP_EMPTY,
    HEATMAP_FUTURE,
    HEATMAP_RECOVERED,
)

TODAY = date(2024, 10, 24)


def collect_texts(control) -> list[str]:
    """Recorrer un árbol de controles Flet y recoger sus textos."""
    texts: list[str] = []
    value = getattr(control, "value", None)
    if isinstance(value, str):
        texts.append(value)
    title = getattr(control, "title", None)
    if title is not None:
        texts.extend(collect_texts(title))
    for child in getattr(control, "controls", None) or []:
        texts.extend(collect_texts(child))
    content = getattr(control, "content", None)
    if content is not None:
        texts.extend(collect_texts(content))
    return texts


def collect_buttons(control) -> list[ft.Button]:
    """Recorrer un árbol de controles Flet y recoger sus botones."""
    buttons: list[ft.Button] = []
    if isinstance(control, (ft.Button, ft.TextButton)):
        buttons.append(control)
    for child in getattr(control, "controls", None) or []:
        buttons.extend(collect_buttons(child))
    for child in getattr(control, "actions", None) or []:
        buttons.extend(collect_buttons(child))
    content = getattr(control, "content", None)
    if content is not None and not isinstance(content, str):
        buttons.extend(collect_buttons(content))
    return buttons


def button_label(button: ft.Button) -> str | None:
    """Obtener el texto visible de un botón de Flet."""
    content = button.content
    if isinstance(content, str):
        return content
    return getattr(content, "value", None)


class FakePage:
    """Página mínima que registra los diálogos abiertos y cerrados."""

    def __init__(self):
        self.open_dialogs = []

    def show_dialog(self, dialog):
        dialog.open = True
        self.open_dialogs.append(dialog)

    def pop_dialog(self):
        if not self.open_dialogs:
            return None
        dialog = self.open_dialogs.pop()
        dialog.open = False
        return dialog

    def update(self):
        pass


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

        for control, card, expected_icon in zip(
            cards._cards_row.controls,
            cards.cards,
            [
                ft.Icons.LOCAL_FIRE_DEPARTMENT,
                ft.Icons.STAR,
                ft.Icons.CALENDAR_MONTH,
            ],
        ):
            label_row, value = control.content.controls
            assert label_row.controls[0].value == card.label
            icon = label_row.controls[-1]
            assert isinstance(icon, ft.Icon)
            assert icon.icon == expected_icon
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

    def _load_state(
        self,
        completed_days: tuple[date, ...] = (),
        recovered_days: tuple[date, ...] = (),
    ) -> AppState:
        habit_id = create_habit_db(
            "Leer", "2024-09-01", icon="book", db_path=self.db_path
        )
        for day in completed_days:
            mark_completed_db(habit_id, day.isoformat(), db_path=self.db_path)
        if recovered_days:
            mark_recovered_days_db(
                habit_id,
                [day.isoformat() for day in recovered_days],
                db_path=self.db_path,
            )
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

    def test_shows_weekday_labels(self):
        """RF-4.1: cada fila del heatmap lleva su día de la semana."""
        state = self._load_state()
        heatmap = ActivityHeatmap(state=state)

        labels = [
            control.value for control in heatmap._weekday_labels.controls
        ]

        assert labels == ["L", "M", "X", "J", "V", "S", "D"]

    def test_shows_title_and_legend(self):
        """RF-4.1, RF-4.5: Título y leyenda visibles."""
        state = self._load_state()
        heatmap = ActivityHeatmap(state=state)

        texts = collect_texts(heatmap)

        assert HEATMAP_TITLE in texts
        assert HEATMAP_NOT_COMPLETED_LABEL in texts
        assert HEATMAP_COMPLETED_LABEL in texts

    def test_heatmap_legend_includes_recovered(self):
        """RF-2.11: la leyenda del heatmap distingue los días recuperados."""
        state = self._load_state(
            completed_days=(TODAY,),
            recovered_days=(TODAY - timedelta(days=1),),
        )
        heatmap = ActivityHeatmap(state=state)

        assert HEATMAP_RECOVERED_LABEL in collect_texts(heatmap)

    def test_recovered_cell_has_own_color_and_tooltip(self):
        """RF-2.11: la celda recuperada se distingue del resto de estados."""
        recovered_day = TODAY - timedelta(days=1)
        state = self._load_state(
            completed_days=(TODAY, TODAY - timedelta(days=2)),
            recovered_days=(recovered_day,),
        )
        heatmap = ActivityHeatmap(state=state)

        recovered_cell = self._cell_control(heatmap, recovered_day)
        completed_cell = self._cell_control(
            heatmap, TODAY - timedelta(days=2)
        )

        assert recovered_cell.bgcolor == HEATMAP_RECOVERED
        assert recovered_cell.bgcolor not in (
            ACCENT_GREEN,
            HEATMAP_EMPTY,
            HEATMAP_FUTURE,
        )
        assert recovered_cell.bgcolor != completed_cell.bgcolor
        assert recovered_cell.border is None
        assert HEATMAP_RECOVERED_LABEL in recovered_cell.tooltip

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
        assert isinstance(button, ft.FilledButton)

    def test_empty_panel_button_does_not_repeat_the_plus(self):
        """RF-6.3: el botón muestra “+ Crear hábito” una sola vez."""
        from habits.ui.empty import EmptyDetailPanel

        panel = EmptyDetailPanel(state=AppState(today=TODAY))

        button = panel.content.controls[-1]

        assert button.content == "+ Crear hábito"
        assert button.icon is None
        assert isinstance(button, ft.FilledButton)


class TestSidebarItemLayout:
    """La racha se muestra a la derecha del nombre, como en el mockup."""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_habits.db")
        init_db(self.db_path)
        habit_id = create_habit_db(
            "Leer", "2024-10-01", icon="book", db_path=self.db_path
        )
        mark_completed_db(
            habit_id, TODAY.isoformat(), db_path=self.db_path
        )
        self.state = load_app_state(self.db_path, today=TODAY)

    def teardown_method(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_streak_is_shown_next_to_the_name(self):
        """RF-1.2: icono y nombre a la izquierda; racha a la derecha."""
        sidebar = Sidebar(state=self.state)

        row = sidebar._items_column.controls[0].content

        assert isinstance(row.controls[1], ft.Icon)
        assert row.controls[2].value == "Leer"
        assert row.controls[3].value == "🔥 1 día"


class TestHabitDetailHeaderActions:
    """Tests de las acciones del detalle — Tarea 5.1."""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_habits.db")
        init_db(self.db_path)
        self.habit_id = create_habit_db(
            "Leer", "2024-09-01", icon="book", db_path=self.db_path
        )
        self.state = load_app_state(self.db_path, today=TODAY)

    def teardown_method(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_detail_header_shows_edit_and_delete_actions(self):
        """RF-1.1: con hábito seleccionado aparecen ambas acciones."""
        header = HabitDetailHeader(state=self.state)

        assert header.visible is True
        assert header.edit_button is not None
        assert header.delete_button is not None
        assert header.edit_button.content == "Editar"
        assert header.delete_button.content == "Eliminar"
        assert header.edit_button.visible is True
        assert header.delete_button.visible is True

    def test_empty_detail_hides_edit_and_delete_actions(self):
        """RF-1.2: sin hábitos no aparecen las acciones."""
        header = HabitDetailHeader(state=AppState(today=TODAY))

        assert header.visible is False
        assert header.edit_button is None
        assert header.delete_button is None
        assert "Editar" not in collect_texts(header)
        assert "Eliminar" not in collect_texts(header)

    def test_detail_actions_invoke_callbacks_with_habit_id(self):
        """RF-1.3, RF-1.4: cada botón notifica el ID del hábito."""
        edited: list[int] = []
        deleted: list[int] = []
        header = HabitDetailHeader(
            state=self.state,
            on_edit=edited.append,
            on_delete=deleted.append,
        )

        header.edit_button.on_click(None)
        header.delete_button.on_click(None)

        assert edited == [self.habit_id]
        assert deleted == [self.habit_id]

    def test_sidebar_does_not_show_edit_or_delete_actions(self):
        """RF-1.5: las acciones solo están en el panel de detalle."""
        sidebar = Sidebar(state=self.state)

        texts = collect_texts(sidebar)

        assert "Editar" not in texts
        assert "Eliminar" not in texts


class TestDeleteHabitDialog:
    """Tests del diálogo de confirmación de borrado — Tarea 5.3."""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_habits.db")
        init_db(self.db_path)
        create_habit_db(
            "Leer", "2024-09-01", icon="book", db_path=self.db_path
        )
        self.state = load_app_state(self.db_path, today=TODAY)
        self.habit = self.state.selected.habit
        self.page = FakePage()

    def teardown_method(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_delete_dialog_shows_name_and_warning(self):
        """RF-3.1: El diálogo muestra el nombre y advierte del borrado."""
        from habits.ui.delete_dialog import DELETE_WARNING, DeleteHabitDialog

        dialog = DeleteHabitDialog(self.page)

        dialog.open(self.habit)

        assert dialog.dialog.open is True
        assert self.page.open_dialogs == [dialog.dialog]
        texts = collect_texts(dialog.dialog)
        assert self.habit.name in texts
        assert DELETE_WARNING in texts

    def test_delete_dialog_offers_cancel_and_delete_actions(self):
        """RF-3.2: El diálogo ofrece “Cancelar” y “Eliminar”."""
        from habits.ui.delete_dialog import DeleteHabitDialog

        dialog = DeleteHabitDialog(self.page)

        dialog.open(self.habit)

        labels = [button_label(button) for button in collect_buttons(dialog.dialog)]
        assert labels == ["Cancelar", "Eliminar"]

    def test_delete_cancel_keeps_habit_and_selection(self):
        """RF-3.3: Cancelar cierra sin borrar ni notificar."""
        from habits.ui.delete_dialog import DeleteHabitDialog

        confirmed: list[int] = []
        dialog = DeleteHabitDialog(self.page, on_confirm=confirmed.append)
        dialog.open(self.habit)

        dialog.close()

        assert dialog.dialog.open is False
        assert self.page.open_dialogs == []
        assert confirmed == []
        assert get_habit_db(self.habit.id, self.db_path) is not None

    def test_delete_confirm_notifies_the_habit_id(self):
        """RF-3.4, RF-3.5: Solo se notifica al confirmar, con el ID."""
        from habits.ui.delete_dialog import DeleteHabitDialog

        confirmed: list[int] = []
        dialog = DeleteHabitDialog(self.page, on_confirm=confirmed.append)
        dialog.open(self.habit)

        assert confirmed == []
        assert get_habit_db(self.habit.id, self.db_path) is not None

        dialog.confirm()

        assert confirmed == [self.habit.id]
        assert dialog.dialog.open is False
        assert self.page.open_dialogs == []
