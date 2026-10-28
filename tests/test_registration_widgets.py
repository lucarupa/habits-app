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
from habits.persistence.completions_repo import (
    get_completions_db,
    mark_completed_db,
)
from habits.persistence.habits_repo import create_habit_db
from habits.persistence.schema import init_db
from habits.theme import ACCENT_GREEN

TODAY = date(2024, 10, 24)


def collect_texts(control) -> list[str]:
    """Recorrer un árbol de controles Flet y recoger sus textos."""
    texts: list[str] = []
    for attribute in ("value", "text"):
        value = getattr(control, attribute, None)
        if isinstance(value, str):
            texts.append(value)
    title = getattr(control, "title", None)
    if title is not None:
        texts.extend(collect_texts(title))
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


class TestRecoverStreakPanel:
    """Acción “Recuperar racha” del panel — Tarea 5.1.

    RF-2.1, RF-2.2, RF-2.3 y RF-2.4: la acción aparece solo con un hueco
    recuperable de uno o dos días y delega el clic en la vista principal.
    """

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

    def _state(self, completed_offsets: tuple[int, ...]) -> AppState:
        for offset in completed_offsets:
            mark_completed_db(
                self.habit_id,
                (TODAY - timedelta(days=offset)).isoformat(),
                db_path=self.db_path,
            )
        return load_app_state(self.db_path, today=TODAY)

    def test_panel_shows_recover_button_for_one_day_gap(self):
        """RF-2.1: un hueco de un día ofrece “Recuperar racha”."""
        panel = TodayRegistrationPanel(state=self._state((2, 0)))

        assert "Recuperar racha" in collect_texts(panel)
        assert panel._recover_button.visible is True

    def test_panel_shows_recover_button_for_two_day_gap(self):
        """RF-2.1: un hueco de dos días ofrece “Recuperar racha”."""
        panel = TodayRegistrationPanel(state=self._state((3, 0)))

        assert "Recuperar racha" in collect_texts(panel)
        assert panel._recover_button.visible is True

    def test_panel_hides_recover_button_for_three_day_gap(self):
        """RF-2.2: un hueco de tres días no ofrece la acción."""
        panel = TodayRegistrationPanel(state=self._state((4, 0)))

        assert "Recuperar racha" not in collect_texts(panel)
        assert panel._recover_button.visible is False

    def test_panel_hides_recover_button_without_records(self):
        """RF-2.3: un hábito sin registros no ofrece la acción."""
        panel = TodayRegistrationPanel(state=self._state(()))

        assert "Recuperar racha" not in collect_texts(panel)
        assert panel._recover_button.visible is False

    def test_recover_button_notifies_main(self):
        """RF-2.4: el panel delega el clic en su callback."""
        calls: list[bool] = []
        panel = TodayRegistrationPanel(state=self._state((2, 0)))
        panel.on_recover = lambda: calls.append(True)

        panel._recover_button.on_click(None)

        assert calls == [True]


class TestStreakRecoveryDialog:
    """Diálogo de confirmación de recuperación — Tarea 5.3.

    RF-2.4 a RF-2.8 y RF-2.19: muestra el hábito y los días, advierte sobre
    las estadísticas, permite cancelar sin cambios y solo notifica al
    confirmar.
    """

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
        self.dates = (
            TODAY - timedelta(days=2),
            TODAY - timedelta(days=1),
        )

    def teardown_method(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_recovery_dialog_shows_name_and_day_count(self):
        """RF-2.4: el diálogo muestra el hábito y cuántos días se recuperan."""
        from habits.app import StreakRecoveryDialog

        dialog = StreakRecoveryDialog(self.page)

        dialog.open(self.habit, self.dates)

        assert dialog.dialog.open is True
        assert dialog.dialog.modal is True
        assert self.page.open_dialogs == [dialog.dialog]
        texts = collect_texts(dialog.dialog)
        assert self.habit.name in texts
        assert any("2 días" in text for text in texts)
        assert any("Recuperar racha" in text for text in texts)

    def test_recovery_dialog_warns_about_statistics(self):
        """RF-2.5: advierte de que cuentan para la racha, no para los días."""
        from habits.app import StreakRecoveryDialog

        dialog = StreakRecoveryDialog(self.page)

        dialog.open(self.habit, self.dates)

        texts = collect_texts(dialog.dialog)
        assert any("recuperados" in text for text in texts)
        assert any("racha" in text for text in texts)
        assert any("Días registrados" in text for text in texts)

    def test_recovery_dialog_offers_cancel_and_recover_actions(self):
        """RF-2.6: el diálogo ofrece “Cancelar” y “Recuperar”."""
        from habits.app import StreakRecoveryDialog

        dialog = StreakRecoveryDialog(self.page)
        dialog.open(self.habit, self.dates)

        labels = [action.content for action in dialog.dialog.actions]

        assert labels == ["Cancelar", "Recuperar"]

    def test_recovery_dialog_cancel_keeps_state(self):
        """RF-2.7: cancelar cierra sin notificar ni marcar días."""
        from habits.app import StreakRecoveryDialog

        confirmed: list[tuple] = []
        dialog = StreakRecoveryDialog(
            self.page,
            on_confirm=lambda habit, dates: confirmed.append((habit, dates)),
        )
        dialog.open(self.habit, self.dates)

        dialog.close()

        assert dialog.dialog.open is False
        assert self.page.open_dialogs == []
        assert confirmed == []

    def test_recovery_dialog_confirm_notifies_habit_and_dates(self):
        """RF-2.8: confirmar notifica el hábito y las fechas del hueco."""
        from habits.app import StreakRecoveryDialog

        confirmed: list[tuple] = []
        dialog = StreakRecoveryDialog(
            self.page,
            on_confirm=lambda habit, dates: confirmed.append((habit, dates)),
        )
        dialog.open(self.habit, self.dates)

        assert confirmed == []

        dialog.confirm()

        assert confirmed == [(self.habit, self.dates)]
        assert dialog.dialog.open is False
        assert self.page.open_dialogs == []


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


class TestDuplicateWarningFlow:
    """Aviso emergente de registro duplicado — Tarea 4.1, RF-1.1 a RF-1.9."""

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

    def _open_page(self) -> tuple[FakePage, TodayRegistrationPanel]:
        page = FakePage()
        main(page, db_path=self.db_path)
        detail_column = page.views[0].controls[0].content.controls[1]
        return page, detail_column.controls[3]

    @staticmethod
    def _snackbars(page: FakePage) -> list[ft.SnackBar]:
        return [
            dialog
            for dialog in page.open_dialogs
            if isinstance(dialog, ft.SnackBar)
        ]

    def test_register_duplicate_shows_snackbar_with_habit_name(self):
        """RF-1.1, RF-1.2, RF-1.7: el aviso aparece y el panel conserva el texto."""
        mark_completed_db(
            self.habit_id, self.today.isoformat(), db_path=self.db_path
        )
        page, registration = self._open_page()

        registration._save_button.on_click(None)

        snackbars = self._snackbars(page)
        assert len(snackbars) == 1
        assert (
            "⚠️ «Leer» ya está registrado hoy."
            in collect_texts(snackbars[0])
        )
        assert REGISTRATION_DUPLICATE_MESSAGE in collect_texts(registration)

    def test_register_duplicate_does_not_add_rows(self):
        """RF-1.3: el aviso no crea un registro adicional."""
        mark_completed_db(
            self.habit_id, self.today.isoformat(), db_path=self.db_path
        )
        page, registration = self._open_page()

        registration._save_button.on_click(None)

        assert get_completions_db(self.habit_id, self.db_path) == [
            self.today.isoformat()
        ]

    def test_register_new_day_does_not_show_duplicate_warning(self):
        """RF-1.4: un registro normal no muestra el aviso de duplicado."""
        page, registration = self._open_page()

        registration._save_button.on_click(None)

        assert self._snackbars(page) == []
        assert get_completions_db(self.habit_id, self.db_path) == [
            self.today.isoformat()
        ]
        assert REGISTRATION_SUCCESS_MESSAGE in collect_texts(registration)

    def test_repeated_duplicate_attempts_show_the_warning_again(self):
        """RF-1.5: cada intento duplicado vuelve a mostrar el aviso."""
        mark_completed_db(
            self.habit_id, self.today.isoformat(), db_path=self.db_path
        )
        page, registration = self._open_page()

        registration._save_button.on_click(None)
        registration._save_button.on_click(None)

        assert len(self._snackbars(page)) == 2
        assert get_completions_db(self.habit_id, self.db_path) == [
            self.today.isoformat()
        ]
