# spec: 002-ui-redesign
# spec: 006-code-organization
"""Tarjetas de estadísticas del hábito seleccionado.

Conserva el comportamiento del componente monolítico anterior (RF-2.1, RF-2.2
y RF-5.4).
"""

import flet as ft
from flet.controls.base_control import skip_field

from habits.state.app_state import AppState
from habits.state.models import StatCard
from habits.theme import SURFACE, TEXT_PRIMARY, TEXT_SECONDARY
from habits.ui.common import STAT_CARD_ICONS


@ft.control
class HabitStatsCards(ft.Container):
    """Tarjetas de estadísticas del hábito seleccionado.

    Muestra “Racha actual”, “Mejor racha” y “Días registrados” a partir de
    `AppState.stat_cards()`; un hábito sin registros muestra 0 en las tres.
    """

    state: AppState | None = skip_field()
    cards: list[StatCard] | None = skip_field()
    _cards_row: ft.Row | None = None

    def init(self):
        self._cards_row = ft.Row(spacing=12)
        self.content = self._cards_row
        self.refresh()

    def refresh(self):
        """Reconstruir las tarjetas desde el estado actual."""
        if self._cards_row is None:
            return

        selected = self.state.selected if self.state is not None else None
        self.visible = selected is not None
        if selected is None:
            self.cards = []
            self._cards_row.controls = []
            return

        self.cards = self.state.stat_cards()
        self._cards_row.controls = [
            self._build_card(card) for card in self.cards
        ]

    def _build_card(self, card: StatCard) -> ft.Container:
        """Construir una tarjeta con su icono, título y valor."""
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Text(
                                card.label,
                                size=12,
                                color=TEXT_SECONDARY,
                                expand=True,
                            ),
                            ft.Icon(
                                STAT_CARD_ICONS.get(
                                    card.label, ft.Icons.INSIGHTS
                                ),
                                size=16,
                                color=TEXT_SECONDARY,
                            ),
                        ],
                        vertical_alignment="center",
                    ),
                    ft.Text(
                        str(card.value),
                        size=28,
                        weight="bold",
                        color=TEXT_PRIMARY,
                    ),
                ],
                spacing=4,
            ),
            padding=16,
            border_radius=12,
            bgcolor=SURFACE,
            expand=True,
        )
