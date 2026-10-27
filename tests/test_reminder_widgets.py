# spec: 005-local-reminders
"""Tests de los widgets del recordatorio — Tareas 6.1 y 6.3.

RF-1.1 y RF-3.5: el encabezado del detalle muestra “Sin recordatorio” o la
hora activa junto al nombre actualizado del hábito, y ofrece el botón
“Recordatorio” que notifica el clic con el ID del hábito.

RF-1.2, RF-1.4, RF-1.5 y RF-1.6: el diálogo activa, cambia la hora, desactiva
y rechaza horas inválidas sin guardar.
"""

import os
import tempfile
from datetime import date

import pytest

pytest.importorskip("flet")

import flet as ft

from habits.app import HabitDetailHeader
from habits.app_state import AppState, load_app_state
from habits.storage import (
    create_habit_db,
    init_db,
    save_reminder_db,
    update_habit_db,
)

TODAY = date(2024, 10, 24)


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


class TestHabitDetailHeaderReminder:
    """Estado y acción del recordatorio en el detalle — Tarea 6.1."""

    def setup_method(self):
        """Crear una base de datos temporal para cada test."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_reminders.db")
        init_db(self.db_path)

    def teardown_method(self):
        """Eliminar la base de datos temporal después de cada test."""
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def _create_habit(self, name: str = "Leer") -> int:
        """Crear un hábito de prueba y devolver su identificador."""
        return create_habit_db(
            name, "2024-09-01", icon="book", db_path=self.db_path
        )

    def _load_state(self) -> AppState:
        """Cargar el estado de la aplicación para la fecha de prueba."""
        return load_app_state(self.db_path, today=TODAY)

    def test_header_shows_disabled_reminder_state(self):
        """RF-1.1: un hábito sin recordatorio muestra “Sin recordatorio”."""
        self._create_habit()

        header = HabitDetailHeader(state=self._load_state())

        assert "Sin recordatorio" in collect_texts(header)

    def test_header_shows_active_reminder_time(self):
        """RF-1.1: un recordatorio activo muestra su hora."""
        habit_id = self._create_habit()
        save_reminder_db(
            habit_id,
            True,
            "09:00",
            TODAY.isoformat(),
            db_path=self.db_path,
        )

        header = HabitDetailHeader(state=self._load_state())

        assert "Recordatorio a las 09:00" in collect_texts(header)

    def test_header_shows_updated_habit_name_with_reminder(self):
        """RF-3.5: el encabezado usa el nombre actualizado del hábito."""
        habit_id = self._create_habit()
        save_reminder_db(
            habit_id,
            True,
            "07:30",
            TODAY.isoformat(),
            db_path=self.db_path,
        )
        update_habit_db(
            habit_id,
            "Leer filosofía",
            "2024-09-01",
            db_path=self.db_path,
        )

        header = HabitDetailHeader(state=self._load_state())
        texts = collect_texts(header)

        assert "Leer filosofía" in texts
        assert "Recordatorio a las 07:30" in texts

    def test_header_offers_reminder_action(self):
        """RF-1.1: el detalle ofrece el botón “Recordatorio”."""
        self._create_habit()

        header = HabitDetailHeader(state=self._load_state())

        assert header.reminder_button is not None
        assert header.reminder_button.content == "Recordatorio"
        assert header.reminder_button.visible is True

    def test_empty_detail_hides_reminder_action(self):
        """RF-1.1: sin hábitos no se muestra estado ni botón."""
        header = HabitDetailHeader(state=AppState(today=TODAY))
        texts = collect_texts(header)

        assert header.visible is False
        assert header.reminder_button is None
        assert "Recordatorio" not in texts
        assert "Sin recordatorio" not in texts

    def test_reminder_action_invokes_callback_with_habit_id(self):
        """RF-1.1: el botón notifica el ID del hábito seleccionado."""
        habit_id = self._create_habit()
        opened: list[int] = []
        header = HabitDetailHeader(
            state=self._load_state(),
            on_reminder=opened.append,
        )

        header.reminder_button.on_click(None)

        assert opened == [habit_id]


class TestReminderDialog:
    """Diálogo de configuración del recordatorio — Tarea 6.3.

    RF-1.2, RF-1.4, RF-1.5 y RF-1.6: activa con una hora válida, cambia la
    hora, desactiva sin avisos futuros y rechaza horas inválidas sin guardar.
    """

    INVALID_TIMES = ["", "9:00", "24:00", "12:60", "abc"]

    def setup_method(self):
        """Crear una base de datos temporal para cada test."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_reminders.db")
        init_db(self.db_path)
        self.page = FakePage()

    def teardown_method(self):
        """Eliminar la base de datos temporal después de cada test."""
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def _create_habit(self, name: str = "Leer") -> int:
        """Crear un hábito de prueba y devolver su identificador."""
        return create_habit_db(
            name, "2024-09-01", icon="book", db_path=self.db_path
        )

    def _open_dialog(
        self,
        *,
        enabled: bool = False,
        reminder_time: str | None = None,
        on_save=None,
    ):
        """Abrir el diálogo para el hábito de prueba."""
        from habits.app import ReminderDialog

        state = load_app_state(self.db_path, today=TODAY)
        dialog = ReminderDialog(self.page, on_save=on_save)
        dialog.open(
            state.selected.habit,
            enabled=enabled,
            reminder_time=reminder_time,
        )
        return dialog

    def test_dialog_opens_with_current_configuration(self):
        """RF-1.2: el diálogo muestra el hábito, su estado y su hora."""
        self._create_habit()

        dialog = self._open_dialog(enabled=True, reminder_time="09:00")

        assert dialog.dialog.open is True
        assert self.page.open_dialogs == [dialog.dialog]
        texts = collect_texts(dialog.dialog)
        assert "Leer" in texts
        assert dialog.enabled_switch.value is True
        assert dialog.time_field.value == "09:00"
        labels = [
            button_label(button)
            for button in collect_buttons(dialog.dialog)
        ]
        assert labels == ["Cancelar", "Guardar"]

    def test_dialog_activates_with_a_valid_time(self):
        """RF-1.2: activar con una hora válida guarda y cierra."""
        habit_id = self._create_habit()
        saved: list[tuple[int, bool, str | None]] = []
        dialog = self._open_dialog(on_save=lambda *args: saved.append(args))

        dialog.enabled_switch.value = True
        dialog.time_field.value = "07:15"
        dialog.save()

        assert saved == [(habit_id, True, "07:15")]
        assert dialog.dialog.open is False
        assert self.page.open_dialogs == []

    def test_dialog_updates_the_existing_time(self):
        """RF-1.4: cambiar la hora conserva la nueva y descarta la anterior."""
        habit_id = self._create_habit()
        saved: list[tuple[int, bool, str | None]] = []
        dialog = self._open_dialog(
            enabled=True,
            reminder_time="09:00",
            on_save=lambda *args: saved.append(args),
        )

        dialog.time_field.value = "18:45"
        dialog.save()

        assert saved == [(habit_id, True, "18:45")]

    def test_dialog_saves_deactivation(self):
        """RF-1.5: desactivar guarda el recordatorio como inactivo."""
        habit_id = self._create_habit()
        saved: list[tuple[int, bool, str | None]] = []
        dialog = self._open_dialog(
            enabled=True,
            reminder_time="09:00",
            on_save=lambda *args: saved.append(args),
        )

        dialog.enabled_switch.value = False
        dialog.save()

        assert saved == [(habit_id, False, "09:00")]
        assert dialog.dialog.open is False

    def test_dialog_allows_deactivation_without_time(self):
        """RF-1.5: desactivar no exige una hora válida."""
        habit_id = self._create_habit()
        saved: list[tuple[int, bool, str | None]] = []
        dialog = self._open_dialog(
            enabled=True,
            reminder_time="09:00",
            on_save=lambda *args: saved.append(args),
        )

        dialog.enabled_switch.value = False
        dialog.time_field.value = ""
        dialog.save()

        assert saved == [(habit_id, False, None)]

    @pytest.mark.parametrize("invalid_time", INVALID_TIMES)
    def test_dialog_rejects_invalid_time(self, invalid_time):
        """RF-1.6: una hora vacía, incompleta o fuera de rango no guarda."""
        self._create_habit()
        saved: list[tuple[int, bool, str | None]] = []
        dialog = self._open_dialog(on_save=lambda *args: saved.append(args))

        dialog.enabled_switch.value = True
        dialog.time_field.value = invalid_time
        dialog.save()

        assert saved == []
        assert dialog.dialog.open is True
        assert dialog.error_text.visible is True
        assert "hora válida" in dialog.error_text.value.lower()
        assert "HH:MM" in dialog.error_text.value

    def test_dialog_keeps_open_until_time_is_corrected(self):
        """RF-1.6: corregir la hora después del error permite guardar."""
        habit_id = self._create_habit()
        saved: list[tuple[int, bool, str | None]] = []
        dialog = self._open_dialog(on_save=lambda *args: saved.append(args))

        dialog.enabled_switch.value = True
        dialog.time_field.value = "25:00"
        dialog.save()

        assert saved == []
        assert dialog.error_text.visible is True

        dialog.time_field.value = "10:00"
        dialog.save()

        assert saved == [(habit_id, True, "10:00")]
        assert dialog.error_text.visible is False
        assert dialog.dialog.open is False

    def test_dialog_cancel_does_not_save(self):
        """RF-1.2: cancelar cierra sin notificar ni guardar."""
        self._create_habit()
        saved: list[tuple[int, bool, str | None]] = []
        dialog = self._open_dialog(on_save=lambda *args: saved.append(args))

        dialog.enabled_switch.value = True
        dialog.time_field.value = "07:15"
        dialog.close()

        assert saved == []
        assert dialog.dialog.open is False
        assert self.page.open_dialogs == []

