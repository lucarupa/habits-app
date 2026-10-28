# spec: 005-local-reminders
"""Tests del flujo integrado de recordatorios — Tarea 6.5.

RF-1.2, RF-1.7, RF-3.4, RF-4.2 y RF-4.4: `main` abre el diálogo, guarda con
la persistencia, sincroniza el planificador al iniciar y tras cada cambio, conserva
la configuración anterior si el sistema falla y muestra avisos en español.

Se ejecutan con el intérprete del proyecto (`.venv`), que tiene Flet instalado.
Con un Python sin Flet el módulo se omite para no romper la suite pura.
"""

import os
import tempfile
from datetime import date

import pytest

pytest.importorskip("flet")

from habits.app import main
from habits.ui.delete_dialog import DeleteHabitDialog
from habits.ui.reminder_dialog import ReminderDialog
from habits.state.app_state import AppState
from habits.notifications.models import (
    NotificationResult,
    SchedulerResult,
)
from habits.reminders import reminder_message
from habits.persistence.habits_repo import create_habit_db
from habits.persistence.reminders_repo import get_reminder_db, save_reminder_db
from habits.persistence.schema import init_db

TODAY = date.today()


class FakeWindow:
    """Ventana mínima usada por `configure_page`."""

    width = None
    height = None
    min_width = None
    min_height = None
    icon = None


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
        self.title = ""
        self.bgcolor = None
        self.theme_mode = None
        self.theme = None
        self.padding = None

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


class FakeScheduler:
    """Planificador simulado que registra las sincronizaciones."""

    def __init__(self, results: list[SchedulerResult] | None = None) -> None:
        self.calls: list[tuple[str, bool]] = []
        self._results = list(results or [])

    def sync(
        self, db_path: str, *, has_active_reminders: bool
    ) -> SchedulerResult:
        """Registrar la llamada y devolver el siguiente resultado."""
        self.calls.append((db_path, has_active_reminders))
        if self._results:
            return self._results.pop(0)
        return SchedulerResult(ok=True)


class FakeNotifier:
    """Notificador simulado que registra los textos enviados."""

    def __init__(self, results: list[NotificationResult] | None = None) -> None:
        self.messages: list[str] = []
        self._results = list(results or [])

    def notify(self, message: str) -> NotificationResult:
        """Registrar el texto y devolver el siguiente resultado."""
        self.messages.append(message)
        if self._results:
            return self._results.pop(0)
        return NotificationResult(ok=True)


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


def find_reminder_dialog(callback) -> ReminderDialog:
    """Extraer el `ReminderDialog` capturado por un callback de `main`."""
    if callback is None:
        raise AssertionError("main no conectó el callback del recordatorio")
    for cell in callback.__closure__ or ():
        content = cell.cell_contents
        if isinstance(content, ReminderDialog):
            return content
    raise AssertionError("No se encontró el ReminderDialog en el callback")


def find_delete_dialog(callback) -> DeleteHabitDialog:
    """Extraer el `DeleteHabitDialog` capturado por un callback de `main`."""
    if callback is None:
        raise AssertionError("main no conectó el callback de eliminación")
    for cell in callback.__closure__ or ():
        content = cell.cell_contents
        if isinstance(content, DeleteHabitDialog):
            return content
    raise AssertionError("No se encontró el DeleteHabitDialog en el callback")


class TestReminderFlow:
    """Conexión del recordatorio en `main` — Tarea 6.5."""

    def setup_method(self):
        """Crear una base de datos temporal con un hábito de prueba."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_reminders.db")
        init_db(self.db_path)
        self.habit_id = create_habit_db(
            "Leer", "2024-09-01", icon="book", db_path=self.db_path
        )

    def teardown_method(self):
        """Eliminar la base de datos temporal después de cada test."""
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def _save_reminder(
        self,
        *,
        enabled: bool = True,
        reminder_time: str | None = "09:00",
    ) -> None:
        """Guardar un recordatorio activo o inactivo en la base."""
        save_reminder_db(
            self.habit_id,
            enabled,
            reminder_time,
            TODAY.isoformat(),
            db_path=self.db_path,
        )

    def _mount(
        self,
        scheduler: FakeScheduler | None = None,
        notifier: FakeNotifier | None = None,
        page: FakePage | None = None,
    ):
        """Montar `main` y devolver la página y el encabezado del detalle."""
        page = page or FakePage()
        main(
            page,
            db_path=self.db_path,
            scheduler=scheduler or FakeScheduler(),
            notifier=notifier or FakeNotifier(),
        )
        layout = page.views[0].controls[0].content
        header = layout.controls[1].controls[0]
        return page, header

    def test_main_syncs_scheduler_on_startup(self):
        """RF-3.4: al arrancar se instala la tarea si hay recordatorios."""
        self._save_reminder()
        scheduler = FakeScheduler()

        self._mount(scheduler=scheduler)

        assert scheduler.calls == [(self.db_path, True)]

    def test_main_removes_the_task_when_no_reminders(self):
        """RF-3.4: al arrancar sin recordatorios se retira la tarea."""
        scheduler = FakeScheduler()

        self._mount(scheduler=scheduler)

        assert scheduler.calls == [(self.db_path, False)]

    def test_header_action_opens_the_reminder_dialog(self):
        """RF-1.2: el botón abre el diálogo con la configuración actual."""
        self._save_reminder()
        page, header = self._mount()

        header.reminder_button.on_click(None)

        dialog = find_reminder_dialog(header.on_reminder)
        assert dialog.dialog.open is True
        assert page.open_dialogs == [dialog.dialog]
        assert dialog.enabled_switch.value is True
        assert dialog.time_field.value == "09:00"

    def test_saving_activation_persists_and_syncs(self):
        """RF-1.2: guardar activa el aviso y actualiza la tarea del sistema."""
        scheduler = FakeScheduler()
        notifier = FakeNotifier()
        page, header = self._mount(
            scheduler=scheduler, notifier=notifier
        )
        header.reminder_button.on_click(None)
        dialog = find_reminder_dialog(header.on_reminder)

        dialog.enabled_switch.value = True
        dialog.time_field.value = "07:15"
        dialog.save()

        reminder = get_reminder_db(self.habit_id, db_path=self.db_path)
        assert reminder is not None
        assert reminder.enabled is True
        assert reminder.reminder_time == "07:15"
        assert "Recordatorio a las 07:15" in collect_texts(header)
        assert scheduler.calls[-1] == (self.db_path, True)
        assert notifier.messages == [reminder_message("Leer")]
        assert page.open_dialogs == []

    def test_reminder_flow_persists_after_reload(self):
        """RF-1.7: la configuración sobrevive a reiniciar la aplicación."""
        _, header = self._mount()
        header.reminder_button.on_click(None)
        dialog = find_reminder_dialog(header.on_reminder)
        dialog.enabled_switch.value = True
        dialog.time_field.value = "07:15"
        dialog.save()

        _, reloaded_header = self._mount()

        assert "Recordatorio a las 07:15" in collect_texts(reloaded_header)

    def test_deactivating_the_last_reminder_removes_the_task(self):
        """RF-3.4: sin recordatorios activos se retira la tarea del sistema."""
        self._save_reminder()
        scheduler = FakeScheduler()
        _, header = self._mount(scheduler=scheduler)
        header.reminder_button.on_click(None)
        dialog = find_reminder_dialog(header.on_reminder)

        dialog.enabled_switch.value = False
        dialog.save()

        reminder = get_reminder_db(self.habit_id, db_path=self.db_path)
        assert reminder is not None
        assert reminder.enabled is False
        assert scheduler.calls[-1] == (self.db_path, False)
        assert "Sin recordatorio" in collect_texts(header)

    def test_activation_is_refused_when_permission_is_denied(self):
        """RF-4.2: sin permiso el recordatorio no queda activo y se avisa."""
        scheduler = FakeScheduler()
        notifier = FakeNotifier(
            results=[
                NotificationResult(
                    ok=False,
                    message=(
                        "Permiso de notificaciones denegado. "
                        "Habilítalo en los ajustes del sistema."
                    ),
                    permission_denied=True,
                )
            ]
        )
        page, header = self._mount(
            scheduler=scheduler, notifier=notifier
        )
        header.reminder_button.on_click(None)
        dialog = find_reminder_dialog(header.on_reminder)

        dialog.enabled_switch.value = True
        dialog.time_field.value = "09:00"
        dialog.save()

        assert get_reminder_db(self.habit_id, db_path=self.db_path) is None
        assert "Sin recordatorio" in collect_texts(header)
        assert all(not active for _, active in scheduler.calls)
        snackbar = page.open_dialogs[-1]
        assert any(
            "Permiso de notificaciones denegado" in text
            for text in collect_texts(snackbar)
        )

    def test_scheduler_failure_keeps_the_previous_configuration(self):
        """RF-4.4: si falla la programación se conserva la configuración."""
        self._save_reminder(reminder_time="09:00")
        scheduler = FakeScheduler(
            results=[
                SchedulerResult(ok=True),
                SchedulerResult(
                    ok=False,
                    message=(
                        "No se pudo programar el recordatorio en el sistema."
                    ),
                ),
            ]
        )
        page, header = self._mount(scheduler=scheduler)
        header.reminder_button.on_click(None)
        dialog = find_reminder_dialog(header.on_reminder)

        dialog.time_field.value = "18:00"
        dialog.save()

        reminder = get_reminder_db(self.habit_id, db_path=self.db_path)
        assert reminder is not None
        assert reminder.enabled is True
        assert reminder.reminder_time == "09:00"
        assert "Recordatorio a las 09:00" in collect_texts(header)
        snackbar = page.open_dialogs[-1]
        assert any(
            "No se pudo programar" in text
            for text in collect_texts(snackbar)
        )

    def test_deleting_a_habit_cancels_its_reminder_and_syncs(self):
        """RF-3.4: eliminar el hábito cancela sus avisos futuros."""
        self._save_reminder()
        scheduler = FakeScheduler()
        page, header = self._mount(scheduler=scheduler)
        header.delete_button.on_click(None)
        dialog = find_delete_dialog(header.on_delete)

        dialog.confirm()

        assert get_reminder_db(self.habit_id, db_path=self.db_path) is None
        assert scheduler.calls[-1] == (self.db_path, False)
        assert isinstance(header.state, AppState)
        assert page.open_dialogs == []
