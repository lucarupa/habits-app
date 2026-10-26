# spec: 002-ui-redesign
"""Tests del panel “Registrar hoy” y del flujo completo — Fase 6, RF-5.

Se ejecutan con el intérprete del proyecto (`.venv`), que tiene Flet instalado.
"""

import os
import tempfile
from datetime import date, timedelta

import pytest

pytest.importorskip("flet")

import flet as ft

from habits.app import ActivityHeatmap, Sidebar, TodayRegistrationPanel, main
from habits.app_state import AppState, load_app_state
from habits.registration import (
    REGISTRATION_BUTTON_LABEL,
    REGISTRATION_DUPLICATE_MESSAGE,
    REGISTRATION_SUCCESS_MESSAGE,
    REGISTRATION_TITLE,
)
from habits.storage import (
    create_habit_db,
    get_completions_db,
    init_db,
    mark_completed_db,
)
from habits.theme import ACCENT_GREEN

TODAY = date(2024, 10, 24)


def collect_texts(control) -> list[str]:
    """Recorrer un árbol de controles Flet y recoger sus textos."""
    texts: list[str] = []
    for attribute in ("value", "text"):
        value = getattr(control, attribute, None)
        if isinstance(value, str):
            texts.append(value)
    content = getattr(control, "content", None)
    if isinstance(content, str):
        texts.append(content)
    elif content is not None and hasattr(content, "_i"):
        texts.extend(collect_texts(content))
    for child in getattr(control, "controls", None) or []:
        texts.extend(collect_texts(child))
    return texts


def iter_controls(control):
    """Recorrer todos los controles de un árbol Flet."""
    yield control
    content = getattr(control, "content", None)
    if content is not None and hasattr(content, "_i"):
        yield from iter_controls(content)
    for child in getattr(control, "controls", None) or []:
        yield from iter_controls(child)


class FakeWindow:
    """Ventana mínima usada por `configure_page`."""

    width = None
    height = None
    min_width = None
    min_height = None


class FakeView:
    """Vista raíz mínima que contiene los controles añadidos a la página."""

    def __init__(self):
        self.controls = []


class FakePage:
    """Página mínima para ejecutar `main()` sin una sesión Flet."""

    def __init__(self):
        self.open_dialogs = []
        self.updates = 0
        self.views = [FakeView()]
        self.window = FakeWindow()

    def add(self, *controls):
        """Añadir controles a la vista raíz, como `flet.Page.add`."""
        self.views[0].controls.extend(controls)

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
        self.updates += 1


class TestTodayRegistrationPanel:
    """Panel “Registrar hoy” — Tarea 6.1, RF-5.1, RF-5.2, RF-5.5, RF-5.6."""

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

    def _load_state(self, completed_today: bool = False) -> AppState:
        if completed_today:
            mark_completed_db(
                self.habit_id, TODAY.isoformat(), db_path=self.db_path
            )
        return load_app_state(self.db_path, today=TODAY)

    def test_shows_title_today_and_save_button(self):
        """RF-5.1, RF-5.2: Título, fecha dd/mm/aaaa y Guardar habilitado."""
        panel = TodayRegistrationPanel(state=self._load_state())

        texts = collect_texts(panel)

        assert panel.visible is True
        assert REGISTRATION_TITLE in texts
        assert TODAY.strftime("%d/%m/%Y") in texts
        assert panel._save_button.content == REGISTRATION_BUTTON_LABEL
        assert panel._save_button.disabled is False

    def test_has_no_date_selector_minutes_or_remove_option(self):
        """RF-5.5: Sin selector de fecha, minutos ni “Quitar registro”."""
        panel = TodayRegistrationPanel(state=self._load_state())

        texts = collect_texts(panel)
        controls = list(iter_controls(panel))

        assert not any(isinstance(c, ft.TextField) for c in controls)
        assert not any(isinstance(c, ft.DatePicker) for c in controls)
        assert "Minutos" not in texts
        assert "Quitar registro" not in texts

    def test_hides_without_selected_habit(self):
        """RF-5.1: Sin hábito seleccionado no se muestra el panel."""
        panel = TodayRegistrationPanel(state=AppState(today=TODAY))

        assert panel.visible is False
        assert panel.message == ""
        assert panel._message_text.visible is False

    def test_shows_already_registered_message(self):
        """RF-5.4: Si ya está completado hoy, muestra “Ya registrado hoy”."""
        panel = TodayRegistrationPanel(
            state=self._load_state(completed_today=True)
        )

        assert REGISTRATION_DUPLICATE_MESSAGE in collect_texts(panel)
        assert panel._message_text.visible is True

    def test_save_button_calls_the_callback(self):
        """RF-5.3: Guardar delega la acción en el callback de la vista."""
        calls: list[bool] = []
        panel = TodayRegistrationPanel(state=self._load_state())
        panel.on_save = lambda: calls.append(True)

        panel._save_button.on_click(None)

        assert calls == [True]

    def test_refresh_updates_the_displayed_date(self):
        """RF-5.6: La fecha mostrada se actualiza al refrescar."""
        state = self._load_state()
        panel = TodayRegistrationPanel(state=state)
        next_day = TODAY + timedelta(days=1)

        state.today = next_day
        panel.refresh()

        assert next_day.strftime("%d/%m/%Y") in collect_texts(panel)


class TestRegistrationFlow:
    """Flujo completo desde `main()` — Tarea 6.2 y 6.3, RF-5.3, RF-5.4."""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_habits.db")
        init_db(self.db_path)
        self.today = date.today()
        self.habit_id = create_habit_db(
            "Leer",
            self.today.isoformat(),
            icon="book",
            db_path=self.db_path,
        )

    def teardown_method(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def _today_cell(self, heatmap: ActivityHeatmap):
        for row_index, row in enumerate(heatmap.rows):
            for column_index, cell in enumerate(row):
                if cell.date == self.today:
                    return heatmap._grid.controls[row_index].controls[
                        column_index
                    ]
        raise AssertionError("No se encontró la celda de hoy")

    def test_registering_today_updates_every_view_and_prevents_duplicates(self):
        """RF-5.3, RF-5.4: Guardar actualiza todo y el duplicado se rechaza."""
        page = FakePage()
        main(page, db_path=self.db_path)

        detail_column = page.views[0].controls[0].content.controls[1]
        sidebar = page.views[0].controls[0].content.controls[0]
        stats_cards = detail_column.controls[1]
        heatmap = detail_column.controls[2]
        registration = detail_column.controls[3]
        empty_panel = detail_column.controls[4]

        assert registration.visible is True
        assert empty_panel.visible is False
        assert [card.value for card in stats_cards.cards] == [0, 0, 0]

        registration._save_button.on_click(None)

        assert get_completions_db(self.habit_id, self.db_path) == [
            self.today.isoformat()
        ]
        assert [card.value for card in stats_cards.cards] == [1, 1, 1]
        assert "🔥 1 día" in collect_texts(sidebar)
        assert self._today_cell(heatmap).bgcolor == ACCENT_GREEN
        assert REGISTRATION_SUCCESS_MESSAGE in collect_texts(registration)

        registration._save_button.on_click(None)

        assert get_completions_db(self.habit_id, self.db_path) == [
            self.today.isoformat()
        ]
        assert REGISTRATION_DUPLICATE_MESSAGE in collect_texts(registration)

        reloaded = load_app_state(self.db_path, today=self.today)
        assert reloaded.is_completed_today is True
        assert reloaded.selected.stats.current_streak == 1
