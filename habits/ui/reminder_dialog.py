# spec: 005-local-reminders
# spec: 006-code-organization
"""Diálogo modal para configurar el recordatorio de un hábito.

Conserva el comportamiento del diálogo monolítico anterior (RF-2.1, RF-2.2 y
RF-5.4). No accede a datos: la persistencia queda en `main`.
"""

from typing import Callable

import flet as ft

from habits.domain.models import Habit
from habits.reminders import validate_reminder_time
from habits.theme import TEXT_PRIMARY

REMINDER_DIALOG_TITLE = "Recordatorio"
REMINDER_SWITCH_LABEL = "Activar recordatorio"
REMINDER_TIME_LABEL = "Hora (HH:MM)"
INVALID_REMINDER_TIME_MESSAGE = (
    "Introduce una hora válida en formato HH:MM (de 00:00 a 23:59)."
)


class ReminderDialog:
    """Diálogo modal para configurar el recordatorio de un hábito.

    Activa o desactiva el aviso, permite cambiar su hora y valida el formato
    antes de guardar. Solo notifica el hábito y la configuración al confirmar;
    la persistencia queda en `main`.
    """

    def __init__(
        self,
        page: ft.Page,
        on_save: Callable[[int, bool, str | None], None] | None = None,
    ) -> None:
        """Construir el diálogo de configuración del recordatorio.

        Args:
            page: Página Flet sobre la que se muestra el diálogo.
            on_save: Callback invocado con el ID del hábito, si el recordatorio
                queda activo y la hora normalizada o None.
        """
        self.page = page
        self.on_save = on_save
        self.habit: Habit | None = None

        self.habit_name_text = ft.Text(
            value="",
            size=16,
            weight="bold",
            color=TEXT_PRIMARY,
        )
        self.enabled_switch = ft.Switch(
            label=REMINDER_SWITCH_LABEL,
            value=False,
        )
        self.time_field = ft.TextField(
            label=REMINDER_TIME_LABEL,
            value="",
            hint_text="HH:MM",
        )
        self.error_text = ft.Text(
            value="",
            size=14,
            color="red",
            visible=False,
        )
        self.dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(REMINDER_DIALOG_TITLE, size=20, weight="bold"),
            content=ft.Column(
                controls=[
                    self.habit_name_text,
                    self.enabled_switch,
                    self.time_field,
                    self.error_text,
                ],
                spacing=12,
                tight=True,
                width=420,
            ),
            actions=[
                ft.TextButton(
                    content="Cancelar",
                    on_click=self.close,
                ),
                ft.Button(
                    content="Guardar",
                    icon=ft.Icons.SAVE,
                    on_click=self.save,
                ),
            ],
            actions_alignment="end",
        )

    def open(
        self,
        habit: Habit,
        *,
        enabled: bool = False,
        reminder_time: str | None = None,
    ) -> None:
        """Abrir el diálogo con la configuración actual del hábito."""
        self.habit = habit
        self.habit_name_text.value = habit.name
        self.enabled_switch.value = enabled
        self.time_field.value = reminder_time or ""
        self._show_error("")
        self.page.show_dialog(self.dialog)

    def close(self, event=None) -> None:
        """Cerrar el diálogo sin guardar cambios."""
        self.habit = None
        self.page.pop_dialog()

    def save(self, event=None) -> None:
        """Validar y notificar la configuración elegida.

        Con el recordatorio activo, una hora vacía, incompleta o fuera de
        rango muestra un mensaje en español y mantiene el diálogo abierto sin
        guardar. Al desactivar no se exige hora y se conserva la que hubiera.
        """
        habit = self.habit
        if habit is None:
            return

        enabled = bool(self.enabled_switch.value)
        valid_time = validate_reminder_time(self.time_field.value or "")
        if enabled and valid_time is None:
            self._show_error(INVALID_REMINDER_TIME_MESSAGE)
            return

        self._show_error("")
        self.close()
        if self.on_save is not None:
            self.on_save(habit.id, enabled, valid_time)

    def _show_error(self, message: str) -> None:
        """Mostrar u ocultar el mensaje de error sin cerrar el diálogo."""
        self.error_text.value = message
        self.error_text.visible = bool(message)
        if self.dialog.open:
            self.page.update()
