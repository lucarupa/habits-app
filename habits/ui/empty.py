# spec: 002-ui-redesign
# spec: 006-code-organization
"""Estado vacío del panel principal.

Conserva el comportamiento del componente monolítico anterior (RF-2.1, RF-2.2
y RF-5.4).
"""

from typing import Callable

import flet as ft
from flet.controls.base_control import skip_field

from habits.state.app_state import AppState
from habits.state.models import EMPTY_BUTTON_LABEL, EMPTY_TITLE
from habits.theme import ACCENT_GREEN, TEXT_PRIMARY


@ft.control
class EmptyDetailPanel(ft.Container):
    """Estado vacío del panel principal cuando no hay hábitos.

    Muestra una ilustración, el título de bienvenida y el botón
    “+ Crear hábito”. Se oculta en cuanto existe al menos un hábito.
    """

    state: AppState | None = skip_field()
    on_create: Callable[[], None] | None = None

    def init(self):
        self.expand = True
        self.padding = 32
        self.alignment = ft.Alignment.CENTER
        self.content = ft.Column(
            controls=[
                ft.Icon(
                    ft.Icons.SELF_IMPROVEMENT,
                    size=64,
                    color=ACCENT_GREEN,
                ),
                ft.Text(
                    EMPTY_TITLE,
                    size=20,
                    weight="bold",
                    text_align="center",
                    color=TEXT_PRIMARY,
                ),
                ft.FilledButton(
                    content=EMPTY_BUTTON_LABEL,
                    on_click=self._handle_create,
                ),
            ],
            horizontal_alignment="center",
            alignment="center",
            spacing=16,
        )
        self.refresh()

    def refresh(self):
        """Mostrar el estado vacío solo cuando no hay hábitos."""
        empty = (
            self.state.empty_state() if self.state is not None else None
        )
        self.visible = empty is not None

    def _handle_create(self, event):
        """Abrir el diálogo de creación desde el estado vacío."""
        if self.on_create is not None:
            self.on_create()
