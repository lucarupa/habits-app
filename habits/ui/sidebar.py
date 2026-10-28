# spec: 002-ui-redesign
# spec: 006-code-organization
"""Barra lateral con la lista de hábitos.

Conserva el comportamiento del componente monolítico anterior (RF-2.1, RF-2.2
y RF-5.4).
"""

from typing import Callable

import flet as ft
from flet.controls.base_control import skip_field

from habits.state.app_state import AppState
from habits.state.models import EMPTY_SIDEBAR_MESSAGE, SidebarItem
from habits.theme import (
    ACCENT_GREEN,
    SELECTED_BG,
    SIDEBAR_BG,
    SIDEBAR_WIDTH,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
)
from habits.ui.common import format_streak_label, icon_for_habit


@ft.control
class Sidebar(ft.Container):
    """Barra lateral con “Mis hábitos”, “+ Nuevo” y la lista de hábitos.

    Muestra el icono, el nombre y la racha de cada hábito; el orden proviene
    de `AppState`. El hábito seleccionado se resalta con fondo y un indicador
    lateral.
    """

    state: AppState | None = skip_field()
    on_select: Callable[[int], None] | None = None
    on_new: Callable[[], None] | None = None
    _items_column: ft.Column | None = None

    def init(self):
        self.width = SIDEBAR_WIDTH
        self.padding = 16
        self.border_radius = 12
        self.bgcolor = SIDEBAR_BG
        self._items_column = ft.Column(spacing=4)
        self.content = ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Text("Mis hábitos", size=20, weight="bold"),
                        ft.Container(expand=True),
                        ft.FilledButton(
                            content="+ Nuevo",
                            on_click=self._handle_new,
                        ),
                    ],
                    alignment="spaceBetween",
                    vertical_alignment="center",
                ),
                self._items_column,
            ],
            spacing=12,
        )
        self.refresh()

    def refresh(self):
        """Reconstruir la lista de hábitos desde el estado actual."""
        if self._items_column is None:
            return

        items = self.state.sidebar_items() if self.state is not None else []
        if not items:
            self._items_column.controls = [
                ft.Text(
                    EMPTY_SIDEBAR_MESSAGE,
                    size=12,
                    color=TEXT_SECONDARY,
                )
            ]
            return

        self._items_column.controls = [
            self._build_item(item) for item in items
        ]

    def _handle_new(self, event):
        """Notificar que el usuario pidió crear un hábito."""
        if self.on_new is not None:
            self.on_new()

    def _select_habit(self, habit_id: int):
        """Seleccionar un hábito y notificar al panel de detalle."""
        if self.state is None:
            return

        self.state.select(habit_id)
        self.refresh()
        if self.on_select is not None:
            self.on_select(habit_id)

    def _build_item(self, item: SidebarItem) -> ft.Container:
        """Construir el control de un hábito de la barra lateral."""
        selected = item.selected
        indicator_color = ACCENT_GREEN if selected else "transparent"
        text_color = ACCENT_GREEN if selected else TEXT_PRIMARY

        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Container(
                        width=4,
                        height=40,
                        bgcolor=indicator_color,
                        border_radius=2,
                    ),
                    ft.Icon(
                        icon_for_habit(item.icon),
                        size=18,
                        color=text_color,
                    ),
                    ft.Text(
                        item.name,
                        size=14,
                        weight="medium",
                        color=text_color,
                        expand=True,
                    ),
                    ft.Text(
                        format_streak_label(item.streak),
                        size=12,
                        color=TEXT_SECONDARY,
                    ),
                ],
                spacing=10,
                vertical_alignment="center",
            ),
            padding=8,
            border_radius=8,
            bgcolor=SELECTED_BG if selected else None,
            on_click=lambda event, habit_id=item.habit_id: self._select_habit(
                habit_id
            ),
        )
