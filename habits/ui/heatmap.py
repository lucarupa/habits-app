# spec: 002-ui-redesign
# spec: 004-duplicate-warning-streak-recovery
# spec: 006-code-organization
"""Heatmap binario de actividad de las últimas cinco semanas.

Conserva el comportamiento del componente monolítico anterior (RF-2.1, RF-2.2
y RF-5.4).
"""

import flet as ft
from flet.controls.base_control import skip_field

from habits.domain.models import HeatmapDay
from habits.state.app_state import AppState
from habits.state.models import (
    HEATMAP_COMPLETED_LABEL,
    HEATMAP_NOT_COMPLETED_LABEL,
    HEATMAP_RECOVERED_LABEL,
    HEATMAP_TITLE,
    format_date_label,
)
from habits.theme import (
    ACCENT_GREEN,
    HEATMAP_EMPTY,
    HEATMAP_FUTURE,
    HEATMAP_RECOVERED,
    HEATMAP_TODAY_BORDER,
    SURFACE,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
)
from habits.ui.common import WEEKDAY_LABELS


@ft.control
class ActivityHeatmap(ft.Container):
    """Heatmap binario de actividad de las últimas cinco semanas.

    Pinta una cuadrícula de 7 filas de lunes a domingo por 5 columnas de
    semanas. Los días completados usan el acento verde, los recuperados un
    ámbar propio, hoy lleva borde destacado y los días futuros se ven como no
    disponibles. Incluye la leyenda “No completado / Completado / Recuperado”.
    """

    state: AppState | None = skip_field()
    rows: list[list[HeatmapDay]] | None = skip_field()
    _body: ft.Column | None = None
    _grid: ft.Column | None = None
    _weekday_labels: ft.Column | None = None

    def init(self):
        self.padding = 16
        self.border_radius = 12
        self.bgcolor = SURFACE
        self._body = ft.Column(spacing=12)
        self.content = self._body
        self.refresh()

    def refresh(self):
        """Reconstruir la cuadrícula y la leyenda desde el estado actual."""
        if self._body is None:
            return

        selected = self.state.selected if self.state is not None else None
        self.visible = selected is not None
        if selected is None:
            self.rows = []
            self._body.controls = []
            return

        self.rows = self.state.heatmap_rows()
        self._grid = ft.Column(
            controls=[
                ft.Row(
                    controls=[self._build_cell(cell) for cell in row],
                    spacing=4,
                )
                for row in self.rows
            ],
            spacing=4,
        )
        self._weekday_labels = ft.Column(
            controls=[
                ft.Text(
                    label,
                    size=11,
                    color=TEXT_SECONDARY,
                    height=22,
                )
                for label in WEEKDAY_LABELS
            ],
            spacing=4,
        )
        self._body.controls = [
            ft.Text(
                HEATMAP_TITLE,
                size=16,
                weight="bold",
                color=TEXT_PRIMARY,
            ),
            ft.Row(
                controls=[self._weekday_labels, self._grid],
                spacing=8,
                vertical_alignment="start",
            ),
            self._build_legend(),
        ]

    def _build_cell(self, cell: HeatmapDay) -> ft.Container:
        """Construir una celda con el color y el borde que le corresponden."""
        if cell.is_future:
            bgcolor = HEATMAP_FUTURE
        elif cell.recovered:
            bgcolor = HEATMAP_RECOVERED
        elif cell.completed:
            bgcolor = ACCENT_GREEN
        else:
            bgcolor = HEATMAP_EMPTY

        border = (
            ft.Border.all(2, HEATMAP_TODAY_BORDER)
            if cell.is_today
            else None
        )

        return ft.Container(
            width=22,
            height=22,
            border_radius=4,
            bgcolor=bgcolor,
            border=border,
            tooltip=self._cell_tooltip(cell),
        )

    def _cell_tooltip(self, cell: HeatmapDay) -> str:
        """Describir la fecha y el estado de una celda."""
        if cell.is_future:
            status = HEATMAP_NOT_COMPLETED_LABEL
        elif cell.recovered:
            status = HEATMAP_RECOVERED_LABEL
        elif cell.completed:
            status = HEATMAP_COMPLETED_LABEL
        else:
            status = HEATMAP_NOT_COMPLETED_LABEL
        return f"{format_date_label(cell.date)} · {status}"

    def _build_legend(self) -> ft.Row:
        """Construir la leyenda “No completado / Completado / Recuperado”."""
        return ft.Row(
            controls=[
                self._legend_item(
                    HEATMAP_NOT_COMPLETED_LABEL, HEATMAP_EMPTY
                ),
                self._legend_item(HEATMAP_COMPLETED_LABEL, ACCENT_GREEN),
                self._legend_item(
                    HEATMAP_RECOVERED_LABEL, HEATMAP_RECOVERED
                ),
            ],
            spacing=16,
        )

    def _legend_item(self, label: str, color: str) -> ft.Row:
        """Construir un elemento de la leyenda con su muestra de color."""
        return ft.Row(
            controls=[
                ft.Container(
                    width=12,
                    height=12,
                    border_radius=3,
                    bgcolor=color,
                ),
                ft.Text(label, size=12, color=TEXT_SECONDARY),
            ],
            spacing=6,
            vertical_alignment="center",
        )
