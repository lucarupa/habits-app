# spec: 002-ui-redesign
# spec: 003-edit-delete-habits
"""Tests del diálogo modal de creación y edición — Tareas 4.1 a 4.4.

Se ejecutan con el intérprete del proyecto (`.venv`), que tiene Flet instalado.
Con un Python sin Flet el módulo se omite para no romper la suite pura.
"""

import os
import tempfile
from datetime import date, datetime, timedelta

import pytest

pytest.importorskip("flet")

import flet as ft

from habits.app import HabitFormDialog
from habits.domain.models import DEFAULT_ICON, Habit
from habits.forms.models import (
    DATE_FORMAT_ERROR,
    ICON_CATALOG,
    ICON_LABELS,
    NAME_REQUIRED_ERROR,
    NAME_TOO_LONG_ERROR,
)
from habits.persistence.habits_repo import (
    create_habit_db,
    get_habit_db,
    list_all_habits_db,
)
from habits.persistence.schema import init_db

TODAY = date(2024, 10, 24)


def as_date(value: date | datetime) -> date:
    """Normalizar un valor de Flet a `date` para compararlo con TODAY."""
    return value.date() if isinstance(value, datetime) else value


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
    """Página mínima que registra los diálogos abiertos y cerrados."""

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


class TestHabitFormDialog:
    """Tests del diálogo modal — T4.1, T4.2, T4.3 y T4.4."""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_habits.db")
        init_db(self.db_path)
        self.page = FakePage()

    def teardown_method(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def make_dialog(self, on_saved=None, on_updated=None):
        return HabitFormDialog(
            self.page,
            on_saved=on_saved,
            on_updated=on_updated,
            db_path=self.db_path,
            today=TODAY,
        )

    def create_habit(
        self,
        name: str = "Leer",
        start_date: date = date(2024, 9, 1),
        icon: str = "book",
    ) -> Habit:
        """Insertar un hábito en la base de datos temporal y devolverlo."""
        habit_id = create_habit_db(
            name, start_date.isoformat(), icon, self.db_path
        )
        return Habit(habit_id, name, start_date, icon)

    def test_open_shows_dialog_with_all_fields(self):
        """RF-2.1: El modal tiene nombre, fecha opcional e icono."""
        dialog = self.make_dialog()

        dialog.open()

        assert dialog.dialog.open is True
        assert self.page.open_dialogs == [dialog.dialog]
        assert dialog.name_field.value == ""
        assert dialog.date_field.value == TODAY.strftime("%d/%m/%Y")
        assert dialog.icon_dropdown.value == DEFAULT_ICON
        assert dialog.error_text.visible is False

    def test_icon_selector_offers_the_catalog(self):
        """RF-2.1, RF-2.6: El selector muestra todos los iconos y el defecto."""
        dialog = self.make_dialog()

        keys = [option.key for option in dialog.icon_dropdown.options]

        assert keys == list(ICON_CATALOG)
        assert DEFAULT_ICON in keys
        assert dialog.icon_dropdown.value == DEFAULT_ICON
        assert all(option.text for option in dialog.icon_dropdown.options)

    def test_open_resets_previous_values(self):
        """RF-2.1: Cada apertura parte de un formulario limpio."""
        dialog = self.make_dialog()
        dialog.name_field.value = "Anterior"
        dialog.date_field.value = "01/01/2024"
        dialog.icon_dropdown.value = "code"
        dialog.error_text.value = "Error previo"
        dialog.error_text.visible = True

        dialog.open()

        assert dialog.name_field.value == ""
        assert dialog.date_field.value == TODAY.strftime("%d/%m/%Y")
        assert dialog.icon_dropdown.value == DEFAULT_ICON
        assert dialog.error_text.value == ""
        assert dialog.error_text.visible is False

    def test_open_create_prefills_today_and_read_only_date(self):
        """RF-5.1, RF-5.8: El campo muestra hoy y no se puede escribir."""
        dialog = self.make_dialog()

        dialog.open()

        assert dialog.date_field.value == TODAY.strftime("%d/%m/%Y")
        assert dialog.date_field.read_only is True
        assert as_date(dialog.date_picker.value) == TODAY

    def test_clicking_date_opens_calendar_with_future_blocked(self):
        """RF-5.3, RF-5.6: Pulsar la fecha abre el calendario sin futuro."""
        dialog = self.make_dialog()
        dialog.open()

        dialog.date_field.on_click(None)

        picker = dialog.date_picker
        assert picker.open is True
        assert self.page.open_dialogs[-1] is picker
        assert as_date(picker.current_date) == TODAY
        assert as_date(picker.last_date) == TODAY
        assert as_date(picker.value) == TODAY
        assert picker.entry_mode == ft.DatePickerEntryMode.CALENDAR_ONLY
        assert dialog.dialog.open is True

    def test_selecting_date_updates_field_and_keeps_dialog_open(self):
        """RF-5.4: Confirmar una fecha actualiza el campo sin cerrar el modal."""
        dialog = self.make_dialog()
        dialog.open()
        dialog.date_field.on_click(None)
        chosen = TODAY - timedelta(days=5)

        dialog.date_picker.value = chosen
        dialog.date_picker.on_change(None)

        assert dialog.date_field.value == chosen.strftime("%d/%m/%Y")
        assert dialog.dialog.open is True
        assert self.page.open_dialogs[0] is dialog.dialog

    def test_canceling_calendar_keeps_previous_date(self):
        """RF-5.5: Cancelar el calendario deja la fecha anterior intacta."""
        dialog = self.make_dialog()
        dialog.open()
        dialog.date_field.on_click(None)
        # El usuario toca otro día, pero cierra sin confirmar: no hay on_change.
        dialog.date_picker.value = TODAY - timedelta(days=2)

        assert dialog.date_field.value == TODAY.strftime("%d/%m/%Y")
        assert dialog.dialog.open is True

    def test_calendar_uses_spanish_locale_and_week_start(self):
        """RF-5.7: El calendario usa español (semana de lunes a domingo)."""
        dialog = self.make_dialog()
        dialog.open()

        picker = dialog.date_picker
        assert isinstance(picker, ft.DatePicker)
        assert picker.locale is not None
        assert picker.locale.language_code == "es"
        assert picker.locale.country_code == "ES"

    def test_open_edit_prefills_current_habit_values(self):
        """RF-2.2, RF-5.2: Nombre, icono y fecha actual precargados."""
        habit = self.create_habit(
            name="Leer", start_date=date(2024, 9, 1), icon="science"
        )
        dialog = self.make_dialog()

        dialog.open_edit(habit)

        assert dialog.dialog.open is True
        assert dialog.dialog.title.value == "Editar hábito"
        assert dialog.name_field.value == "Leer"
        assert dialog.icon_dropdown.value == "science"
        assert dialog.date_field.value == "01/09/2024"
        assert as_date(dialog.date_picker.value) == date(2024, 9, 1)

    def test_edit_submit_persists_and_notifies(self):
        """RF-2.9: Guardar una edición persiste, cierra y notifica el resultado."""
        habit = self.create_habit()
        updated = []
        dialog = self.make_dialog(on_updated=updated.append)
        dialog.open_edit(habit)
        dialog.name_field.value = "  Leer más  "
        dialog.date_field.value = "01/10/2024"
        dialog.icon_dropdown.value = "code"

        dialog.submit()

        assert dialog.dialog.open is False
        assert self.page.open_dialogs == []
        assert len(updated) == 1

        result = updated[0]
        assert result.habit_id == habit.id
        assert result.name == "Leer más"
        assert result.start_date == date(2024, 10, 1)
        assert result.icon == "code"

        row = get_habit_db(habit.id, self.db_path)
        assert row is not None
        assert row.name == "Leer más"
        assert row.start_date == "2024-10-01"
        assert row.icon == "code"

    def test_edit_cancel_does_not_change_the_habit(self):
        """RF-2.10: Cancelar deja intactos los datos del hábito."""
        habit = self.create_habit()
        dialog = self.make_dialog(on_updated=lambda result: None)
        dialog.open_edit(habit)
        dialog.name_field.value = "Cambiado"
        dialog.date_field.value = "01/08/2024"
        dialog.icon_dropdown.value = "art"

        dialog.close()

        assert dialog.dialog.open is False
        assert self.page.open_dialogs == []

        row = get_habit_db(habit.id, self.db_path)
        assert row is not None
        assert row.name == "Leer"
        assert row.start_date == "2024-09-01"
        assert row.icon == "book"

    def test_edit_validation_error_keeps_dialog_open(self):
        """RF-2.3, RF-2.4: Los errores mantienen el modal abierto sin persistir."""
        habit = self.create_habit()
        dialog = self.make_dialog(on_updated=lambda result: None)
        dialog.open_edit(habit)

        dialog.name_field.value = "   "
        dialog.submit()

        assert dialog.dialog.open is True
        assert dialog.error_text.visible is True
        assert dialog.error_text.value == NAME_REQUIRED_ERROR

        dialog.name_field.value = "a" * 61
        dialog.submit()

        assert dialog.dialog.open is True
        assert dialog.error_text.value == NAME_TOO_LONG_ERROR

        row = get_habit_db(habit.id, self.db_path)
        assert row is not None
        assert row.name == "Leer"

    def test_empty_name_keeps_dialog_open_and_does_not_persist(self):
        """RF-2.2: Nombre vacío muestra error y no cierra el diálogo."""
        dialog = self.make_dialog()
        dialog.open()
        dialog.name_field.value = "   "

        dialog.submit()

        assert dialog.dialog.open is True
        assert dialog.error_text.visible is True
        assert dialog.error_text.value == NAME_REQUIRED_ERROR
        assert list_all_habits_db(self.db_path) == []

    def test_too_long_name_keeps_dialog_open_and_does_not_persist(self):
        """RF-2.3: Más de 60 caracteres muestra error y no cierra el diálogo."""
        dialog = self.make_dialog()
        dialog.open()
        dialog.name_field.value = "a" * 61

        dialog.submit()

        assert dialog.dialog.open is True
        assert dialog.error_text.value == NAME_TOO_LONG_ERROR
        assert list_all_habits_db(self.db_path) == []

    def test_invalid_date_keeps_dialog_open_and_does_not_persist(self):
        """RF-2.10: Fecha inválida muestra error y no crea el hábito."""
        dialog = self.make_dialog()
        dialog.open()
        dialog.name_field.value = "Estudiar"
        dialog.date_field.value = "2024-01-05"

        dialog.submit()

        assert dialog.dialog.open is True
        assert dialog.error_text.value == DATE_FORMAT_ERROR
        assert list_all_habits_db(self.db_path) == []

    def test_future_date_is_saved_as_today(self):
        """RF-2.5: Una fecha futura se corrige a hoy al guardar."""
        dialog = self.make_dialog()
        dialog.open()
        dialog.name_field.value = "Estudiar"
        dialog.date_field.value = (TODAY + timedelta(days=5)).strftime(
            "%d/%m/%Y"
        )

        dialog.submit()

        rows = list_all_habits_db(self.db_path)
        assert len(rows) == 1
        assert rows[0].start_date == TODAY.isoformat()

    def test_success_closes_dialog_persists_and_notifies(self):
        """RF-2.7, RF-2.9: Guardar persiste, cierra y notifica el ID."""
        saved = []
        dialog = self.make_dialog(on_saved=saved.append)
        dialog.open()
        dialog.name_field.value = "  Leer  "
        dialog.date_field.value = "01/09/2024"
        dialog.icon_dropdown.value = "science"

        dialog.submit()

        assert dialog.dialog.open is False
        assert self.page.open_dialogs == []
        assert len(saved) == 1

        result = saved[0]
        row = get_habit_db(result.habit_id, self.db_path)
        assert row is not None
        assert row.name == "Leer"
        assert row.start_date == "2024-09-01"
        assert row.icon == "science"

    def test_cancel_closes_dialog(self):
        """RF-2.1: Cancelar cierra el diálogo sin crear nada."""
        dialog = self.make_dialog()
        dialog.open()

        dialog.close()

        assert dialog.dialog.open is False
        assert self.page.open_dialogs == []
        assert list_all_habits_db(self.db_path) == []

    def test_main_wires_both_ctas_and_shows_created_habit(self):
        """RF-2.1, RF-2.9, RF-6.3: Mismo modal desde ambos CTA y detalle."""
        from habits.app import main

        main(self.page, db_path=self.db_path)

        layout = self.page.views[0].controls[0].content
        sidebar = layout.controls[0]
        detail_column = layout.controls[1]
        header = detail_column.controls[0]
        stats_cards = detail_column.controls[1]
        heatmap = detail_column.controls[2]
        registration = detail_column.controls[3]
        empty_panel = detail_column.controls[4]

        assert empty_panel.visible is True
        assert stats_cards.visible is False
        assert heatmap.visible is False
        assert registration.visible is False

        sidebar.on_new()
        assert len(self.page.open_dialogs) == 1
        dialog_control = self.page.open_dialogs[0]

        self.page.pop_dialog()
        empty_panel.on_create()

        assert self.page.open_dialogs == [dialog_control]

        dialog = next(
            cell.cell_contents
            for cell in empty_panel.on_create.__closure__ or ()
            if isinstance(cell.cell_contents, HabitFormDialog)
        )
        dialog.name_field.value = "Leer"
        dialog.date_field.value = ""
        dialog.icon_dropdown.value = "book"
        dialog.submit()

        assert self.page.open_dialogs == []
        assert empty_panel.visible is False
        assert stats_cards.visible is True
        assert heatmap.visible is True
        assert registration.visible is True
        assert [card.value for card in stats_cards.cards] == [0, 0, 0]
        assert len(heatmap.rows) == 7
        assert sidebar.state.is_empty is False
        assert sidebar.state.selected_id is not None
        assert len(sidebar._items_column.controls) == 1
        assert header.state.detail_header().name == "Leer"

        name_text = header._body.controls[0].controls[1].controls[0]
        assert name_text.value == "Leer"
