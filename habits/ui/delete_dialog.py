# spec: 002-ui-redesign
# spec: 003-edit-delete-habits
# spec: 006-code-organization
"""Diálogo modal de confirmación para eliminar un hábito.

Conserva el comportamiento del diálogo monolítico anterior (RF-2.1, RF-2.2 y
RF-5.4). No accede a datos: la persistencia queda en `main`.
"""

from typing import Callable

import flet as ft

from habits.domain.models import Habit
from habits.theme import TEXT_PRIMARY, TEXT_SECONDARY

DELETE_DIALOG_TITLE = "Eliminar hábito"
DELETE_WARNING = (
    "⚠️ Esta acción es permanente y eliminará el hábito junto con todos "
    "sus registros diarios."
)


class DeleteHabitDialog:
    """Diálogo modal de confirmación para eliminar un hábito.

    Muestra el nombre del hábito y advierte de que el borrado es permanente e
    incluye sus registros, ofrece “Cancelar” y “Eliminar”, y solo notifica el
    ID al confirmar.
    """

    def __init__(
        self,
        page: ft.Page,
        on_confirm: Callable[[int], None] | None = None,
    ) -> None:
        """Construir el diálogo de confirmación.

        Args:
            page: Página Flet sobre la que se muestra el diálogo.
            on_confirm: Callback invocado con el ID del hábito confirmado.
        """
        self.page = page
        self.on_confirm = on_confirm
        self.habit: Habit | None = None

        self.name_text = ft.Text(
            value="",
            size=16,
            weight="bold",
            color=TEXT_PRIMARY,
        )
        self.warning_text = ft.Text(
            value=DELETE_WARNING,
            size=14,
            color=TEXT_SECONDARY,
        )
        self.dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(DELETE_DIALOG_TITLE, size=20, weight="bold"),
            content=ft.Column(
                controls=[self.name_text, self.warning_text],
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
                    content="Eliminar",
                    icon=ft.Icons.DELETE,
                    on_click=self.confirm,
                ),
            ],
            actions_alignment="end",
        )

    def open(self, habit: Habit) -> None:
        """Abrir el diálogo con el nombre del hábito a eliminar."""
        self.habit = habit
        self.name_text.value = habit.name
        self.page.show_dialog(self.dialog)

    def close(self, event=None) -> None:
        """Cerrar el diálogo sin eliminar nada."""
        self.habit = None
        self.page.pop_dialog()

    def confirm(self, event=None) -> None:
        """Cerrar el diálogo y notificar la confirmación."""
        habit = self.habit
        if habit is None:
            return
        self.close()
        if self.on_confirm is not None:
            self.on_confirm(habit.id)
