# spec: 002-ui-redesign
# spec: 003-edit-delete-habits
# spec: 006-code-organization
"""Encabezado del panel de detalle.

Conserva el comportamiento del componente monolítico anterior (RF-2.1, RF-2.2
y RF-5.4).
"""

from typing import Callable

import flet as ft
from flet.controls.base_control import skip_field

from habits.state.app_state import AppState
from habits.theme import (
    ACCENT_GREEN,
    SELECTED_BG,
    SURFACE,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
)
from habits.ui.common import icon_for_habit


@ft.control
class HabitDetailHeader(ft.Container):
    """Encabezado del panel de detalle del hábito seleccionado.

    Muestra el icono, el nombre, el subtítulo “Hábito de estudio”, la fecha de
    inicio en dd/mm/aaaa, el estado del recordatorio y las acciones
    “Recordatorio”, “Editar” y “Eliminar”, que solo aparecen con un hábito
    seleccionado y notifican su ID mediante callbacks.
    """

    state: AppState | None = skip_field()
    on_edit: Callable[[int], None] | None = None
    on_delete: Callable[[int], None] | None = None
    on_reminder: Callable[[int], None] | None = None
    edit_button: ft.TextButton | None = skip_field()
    delete_button: ft.TextButton | None = skip_field()
    reminder_button: ft.TextButton | None = skip_field()
    _body: ft.Column | None = None

    def init(self):
        self.padding = 16
        self.border_radius = 12
        self.bgcolor = SURFACE
        self._body = ft.Column(spacing=8)
        self.content = self._body
        self.refresh()

    def refresh(self):
        """Reconstruir el encabezado desde el estado actual."""
        if self._body is None:
            return

        header = (
            self.state.detail_header() if self.state is not None else None
        )
        self.visible = header is not None
        if header is None:
            self.edit_button = None
            self.delete_button = None
            self.reminder_button = None
            self._body.controls = []
            return

        self.reminder_button = ft.TextButton(
            content="Recordatorio",
            icon=ft.Icons.NOTIFICATIONS_OUTLINED,
            on_click=self._handle_reminder,
        )
        self.edit_button = ft.TextButton(
            content="Editar",
            icon=ft.Icons.EDIT,
            on_click=self._handle_edit,
        )
        self.delete_button = ft.TextButton(
            content="Eliminar",
            icon=ft.Icons.DELETE_OUTLINE,
            on_click=self._handle_delete,
        )

        self._body.controls = [
            ft.Row(
                controls=[
                    ft.Container(
                        content=ft.Icon(
                            icon_for_habit(header.icon),
                            size=28,
                            color=ACCENT_GREEN,
                        ),
                        padding=10,
                        border_radius=10,
                        bgcolor=SELECTED_BG,
                    ),
                    ft.Column(
                        controls=[
                            ft.Text(
                                header.name,
                                size=24,
                                weight="bold",
                                color=TEXT_PRIMARY,
                            ),
                            ft.Text(
                                header.subtitle,
                                size=14,
                                color=TEXT_SECONDARY,
                            ),
                            ft.Text(
                                value=(
                                    self.state.reminder_label
                                    if self.state is not None
                                    else ""
                                ),
                                size=12,
                                color=TEXT_SECONDARY,
                            ),
                        ],
                        spacing=2,
                        expand=True,
                    ),
                    self.reminder_button,
                    self.edit_button,
                    self.delete_button,
                ],
                spacing=12,
                vertical_alignment="center",
            ),
            ft.Text(
                value=f"Inicio: {header.start_date_label}",
                size=12,
                color=TEXT_SECONDARY,
            ),
        ]

    def _handle_reminder(self, event=None) -> None:
        """Notificar la configuración del recordatorio."""
        selected = self.state.selected if self.state is not None else None
        if selected is not None and self.on_reminder is not None:
            self.on_reminder(selected.habit.id)

    def _handle_edit(self, event=None) -> None:
        """Notificar la edición del hábito seleccionado."""
        selected = self.state.selected if self.state is not None else None
        if selected is not None and self.on_edit is not None:
            self.on_edit(selected.habit.id)

    def _handle_delete(self, event=None) -> None:
        """Notificar la eliminación del hábito seleccionado."""
        selected = self.state.selected if self.state is not None else None
        if selected is not None and self.on_delete is not None:
            self.on_delete(selected.habit.id)
