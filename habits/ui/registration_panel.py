# spec: 002-ui-redesign
# spec: 004-duplicate-warning-streak-recovery
# spec: 006-code-organization
"""Panel “Registrar hoy” del hábito seleccionado.

Conserva el comportamiento del componente monolítico anterior (RF-2.1, RF-2.2
y RF-5.4).
"""

from typing import Callable

import flet as ft
from flet.controls.base_control import skip_field

from habits.registration import (
    REGISTRATION_BUTTON_LABEL,
    REGISTRATION_DUPLICATE_MESSAGE,
    REGISTRATION_TITLE,
)
from habits.state.app_state import AppState
from habits.state.models import format_date_label
from habits.theme import SURFACE, TEXT_PRIMARY, TEXT_SECONDARY
from habits.ui.common import RECOVER_STREAK_BUTTON_LABEL


@ft.control
class TodayRegistrationPanel(ft.Container):
    """Panel “Registrar hoy” del hábito seleccionado.

    Muestra la fecha actual en dd/mm/aaaa y un botón “Guardar”; no incluye
    selector de fecha, minutos ni “Quitar registro”. Si el hábito ya está
    completado hoy muestra el mensaje “Ya registrado hoy”. También ofrece
    “Recuperar racha” cuando el hueco más reciente es de uno o dos días.
    """

    state: AppState | None = skip_field()
    on_save: Callable[[], None] | None = None
    on_recover: Callable[[], None] | None = None
    message: str = ""
    _date_text: ft.Text | None = None
    _save_button: ft.Button | None = None
    _recover_button: ft.Button | None = None
    _message_text: ft.Text | None = None
    _body: ft.Column | None = None

    def init(self):
        self.padding = 16
        self.border_radius = 12
        self.bgcolor = SURFACE
        self._date_text = ft.Text(size=14, color=TEXT_PRIMARY)
        self._save_button = ft.Button(
            content=REGISTRATION_BUTTON_LABEL,
            on_click=self._handle_save,
        )
        self._recover_button = ft.Button(
            content="",
            on_click=self._handle_recover,
            visible=False,
        )
        self._message_text = ft.Text(
            value="",
            size=14,
            color=TEXT_SECONDARY,
            visible=False,
        )
        self._body = ft.Column(
            controls=[
                ft.Text(
                    REGISTRATION_TITLE,
                    size=16,
                    weight="bold",
                    color=TEXT_PRIMARY,
                ),
                ft.Row(
                    controls=[
                        ft.Text(
                            "Fecha",
                            size=12,
                            color=TEXT_SECONDARY,
                        ),
                        self._date_text,
                        self._save_button,
                    ],
                    spacing=12,
                    vertical_alignment="center",
                ),
                self._message_text,
                self._recover_button,
            ],
            spacing=8,
        )
        self.content = self._body
        self.refresh()

    def refresh(self):
        """Actualizar fecha, botones y mensaje desde el estado actual."""
        if self._body is None:
            return

        selected = self.state.selected if self.state is not None else None
        self.visible = selected is not None
        if selected is None:
            self.message = ""
            self._message_text.value = ""
            self._message_text.visible = False
            self._recover_button.content = ""
            self._recover_button.visible = False
            return

        self._date_text.value = format_date_label(self.state.today)
        if not self.state.is_completed_today:
            self.message = ""
        elif not self.message:
            self.message = REGISTRATION_DUPLICATE_MESSAGE

        self._message_text.value = self.message
        self._message_text.visible = bool(self.message)

        can_recover = self.state.recoverable_gap is not None
        self._recover_button.content = (
            RECOVER_STREAK_BUTTON_LABEL if can_recover else ""
        )
        self._recover_button.visible = can_recover

    def _handle_save(self, event):
        """Delegar el guardado en la vista principal."""
        if self.on_save is not None:
            self.on_save()

    def _handle_recover(self, event):
        """Delegar la recuperación de racha en la vista principal."""
        if self.on_recover is not None:
            self.on_recover()
