# spec: 004-duplicate-warning-streak-recovery
# spec: 006-code-organization
"""Diálogo modal para confirmar la recuperación de una racha.

Conserva el comportamiento del diálogo monolítico anterior (RF-2.1, RF-2.2 y
RF-5.4). No accede a datos: la persistencia queda en `main`.
"""

from datetime import date
from typing import Callable

import flet as ft

from habits.domain.models import Habit
from habits.theme import TEXT_PRIMARY, TEXT_SECONDARY
from habits.ui.common import (
    STREAK_RECOVERY_CANCEL_LABEL,
    STREAK_RECOVERY_CONFIRM_LABEL,
    STREAK_RECOVERY_DIALOG_TITLE,
    STREAK_RECOVERY_WARNING,
)


class StreakRecoveryDialog:
    """Diálogo modal para confirmar la recuperación de una racha.

    Muestra el hábito y cuántos días se recuperarán, advierte de que contarán
    para la racha pero no para “Días registrados”, y solo notifica el hábito y
    las fechas al confirmar.
    """

    def __init__(
        self,
        page: ft.Page,
        on_confirm: (
            Callable[[Habit, tuple[date, ...]], None] | None
        ) = None,
    ) -> None:
        """Construir el diálogo de confirmación.

        Args:
            page: Página Flet sobre la que se muestra el diálogo.
            on_confirm: Callback invocado con el hábito y las fechas del hueco.
        """
        self.page = page
        self.on_confirm = on_confirm
        self.habit: Habit | None = None
        self.dates: tuple[date, ...] = ()

        self.name_text = ft.Text(
            value="",
            size=16,
            weight="bold",
            color=TEXT_PRIMARY,
        )
        self.detail_text = ft.Text(
            value="",
            size=14,
            color=TEXT_PRIMARY,
        )
        self.warning_text = ft.Text(
            value=STREAK_RECOVERY_WARNING,
            size=14,
            color=TEXT_SECONDARY,
        )
        self.dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(
                STREAK_RECOVERY_DIALOG_TITLE,
                size=20,
                weight="bold",
            ),
            content=ft.Column(
                controls=[
                    self.name_text,
                    self.detail_text,
                    self.warning_text,
                ],
                spacing=12,
                tight=True,
                width=420,
            ),
            actions=[
                ft.TextButton(
                    content=STREAK_RECOVERY_CANCEL_LABEL,
                    on_click=self.close,
                ),
                ft.Button(
                    content=STREAK_RECOVERY_CONFIRM_LABEL,
                    icon=ft.Icons.AUTORENEW,
                    on_click=self.confirm,
                ),
            ],
            actions_alignment="end",
        )

    def open(self, habit: Habit, dates: tuple[date, ...]) -> None:
        """Abrir el diálogo con el hábito y las fechas a recuperar."""
        self.habit = habit
        self.dates = tuple(dates)
        self.name_text.value = habit.name
        day_count = len(self.dates)
        self.detail_text.value = (
            f"Se recuperará {day_count} día del hábito seleccionado."
            if day_count == 1
            else f"Se recuperarán {day_count} días del hábito seleccionado."
        )
        self.page.show_dialog(self.dialog)

    def close(self, event=None) -> None:
        """Cerrar el diálogo sin recuperar nada."""
        self.habit = None
        self.dates = ()
        self.page.pop_dialog()

    def confirm(self, event=None) -> None:
        """Cerrar el diálogo y notificar la recuperación."""
        habit = self.habit
        dates = self.dates
        if habit is None or not dates:
            return
        self.close()
        if self.on_confirm is not None:
            self.on_confirm(habit, dates)
