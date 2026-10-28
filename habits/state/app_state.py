# spec: 002-ui-redesign
# spec: 004-duplicate-warning-streak-recovery
# spec: 005-local-reminders
# spec: 006-code-organization
"""Estado derivado de la aplicación.

Construye las vistas de barra lateral, detalle, estadísticas y heatmap a partir
de los modelos de estado, sin dependencias de Flet ni SQLite (RF-2.2, RF-2.3 y
RF-5.3).
"""

from dataclasses import dataclass, field
from datetime import date

from habits.domain.heatmap import build_activity_heatmap
from habits.domain.models import HeatmapDay, RecoverableGap
from habits.domain.recovery import find_recoverable_gap
from habits.reminders import DISABLED_LABEL
from habits.state.models import (
    EMPTY_BUTTON_LABEL,
    EMPTY_SIDEBAR_MESSAGE,
    EMPTY_TITLE,
    HABIT_SUBTITLE,
    STAT_BEST_STREAK_LABEL,
    STAT_CURRENT_STREAK_LABEL,
    STAT_REGISTERED_DAYS_LABEL,
    DetailHeader,
    EmptyState,
    HabitState,
    SidebarItem,
    StatCard,
    format_date_label,
)


@dataclass
class AppState:
    """Estado completo de la aplicación en un momento dado.

    Atributos:
        habits: Hábitos ordenados por racha descendente y nombre ascendente.
        selected_id: ID del hábito seleccionado, o None si no hay hábitos.
        today: Fecha usada para calcular estadísticas y heatmap.
    """

    habits: list[HabitState] = field(default_factory=list)
    selected_id: int | None = None
    today: date = field(default_factory=date.today)

    @property
    def selected(self) -> HabitState | None:
        """Devolver el hábito seleccionado, o None si no existe."""
        for habit_state in self.habits:
            if habit_state.habit.id == self.selected_id:
                return habit_state
        return None

    @property
    def is_empty(self) -> bool:
        """Indicar si no hay ningún hábito registrado."""
        return not self.habits

    @property
    def is_completed_today(self) -> bool:
        """Indicar si el hábito seleccionado ya está completado hoy.

        Returns:
            True si hay un hábito seleccionado y su fecha actual está entre
            sus registros; False en caso contrario (RF-5.2, RF-5.4).
        """
        selected = self.selected
        if selected is None:
            return False
        return self.today in selected.completed_dates

    @property
    def reminder_label(self) -> str:
        """Devolver la etiqueta del recordatorio del hábito seleccionado.

        Returns:
            “Sin recordatorio” si no hay selección o el recordatorio está
            desactivado, o “Recordatorio a las HH:MM” si está activo
            (RF-1.1).
        """
        selected = self.selected
        if selected is None:
            return DISABLED_LABEL
        return selected.reminder_label

    @property
    def recoverable_gap(self) -> RecoverableGap | None:
        """Devolver el hueco recuperable del hábito seleccionado.

        Returns:
            El hueco más reciente de uno o dos días sin registro, o None si
            no hay hábito seleccionado o el hueco no es recuperable
            (RF-2.1, RF-2.2 y RF-2.18).
        """
        selected = self.selected
        if selected is None:
            return None
        return find_recoverable_gap(selected.completed_dates, self.today)

    def empty_state(self) -> EmptyState | None:
        """Construir el estado vacío, o None si ya existen hábitos.

        Returns:
            Un EmptyState con los textos de la barra lateral y del panel
            principal, o None cuando hay al menos un hábito.
        """
        if not self.is_empty:
            return None

        return EmptyState(
            sidebar_message=EMPTY_SIDEBAR_MESSAGE,
            title=EMPTY_TITLE,
            button_label=EMPTY_BUTTON_LABEL,
        )

    def select(self, habit_id: int) -> None:
        """Seleccionar un hábito existente.

        Args:
            habit_id: Identificador del hábito a seleccionar.

        Raises:
            ValueError: Si el hábito no existe en el estado.
        """
        if not any(habit_state.habit.id == habit_id for habit_state in self.habits):
            raise ValueError(f"El hábito {habit_id} no existe")
        self.selected_id = habit_id

    def sidebar_items(self) -> list[SidebarItem]:
        """Construir los elementos de la barra lateral en orden de visualización.

        Returns:
            Una lista de SidebarItem en el mismo orden que `habits`, marcando
            como seleccionado el hábito actual.
        """
        return [
            SidebarItem(
                habit_id=habit_state.habit.id,
                icon=habit_state.habit.icon,
                name=habit_state.habit.name,
                streak=habit_state.stats.current_streak,
                selected=habit_state.habit.id == self.selected_id,
            )
            for habit_state in self.habits
        ]

    def detail_header(self) -> DetailHeader | None:
        """Construir el encabezado del panel de detalle del hábito seleccionado.

        Returns:
            Un DetailHeader con icono, nombre, subtítulo y fecha de inicio, o
            None si no hay ningún hábito seleccionado.
        """
        selected = self.selected
        if selected is None:
            return None

        return DetailHeader(
            habit_id=selected.habit.id,
            icon=selected.habit.icon,
            name=selected.habit.name,
            subtitle=HABIT_SUBTITLE,
            start_date_label=format_date_label(selected.habit.start_date),
        )

    def stat_cards(self) -> list[StatCard]:
        """Construir las tarjetas de estadísticas del hábito seleccionado.

        Returns:
            Una lista con “Racha actual”, “Mejor racha” y “Días registrados”,
            o una lista vacía si no hay hábito seleccionado (RF-3.2 a RF-3.5).
        """
        selected = self.selected
        if selected is None:
            return []

        return [
            StatCard(
                label=STAT_CURRENT_STREAK_LABEL,
                value=selected.stats.current_streak,
            ),
            StatCard(
                label=STAT_BEST_STREAK_LABEL,
                value=selected.stats.best_streak,
            ),
            StatCard(
                label=STAT_REGISTERED_DAYS_LABEL,
                value=selected.stats.registered_days,
            ),
        ]

    def heatmap_cells(self, weeks: int = 5) -> list[HeatmapDay]:
        """Construir las celdas del heatmap del hábito seleccionado.

        Args:
            weeks: Cantidad de semanas calendario a mostrar.

        Returns:
            Las celdas del heatmap, o una lista vacía si no hay hábito
            seleccionado (RF-4.1 a RF-4.6).
        """
        selected = self.selected
        if selected is None:
            return []

        return build_activity_heatmap(
            selected.completed_dates,
            self.today,
            recovered_dates=selected.recovered_dates,
            weeks=weeks,
        )

    def heatmap_rows(self, weeks: int = 5) -> list[list[HeatmapDay]]:
        """Agrupar las celdas del heatmap en 7 filas de lunes a domingo.

        Args:
            weeks: Cantidad de semanas calendario a mostrar.

        Returns:
            Siete filas, cada una con una celda por semana en orden
            cronológico (RF-4.2).
        """
        cells = self.heatmap_cells(weeks=weeks)
        if not cells:
            return []

        rows: list[list[HeatmapDay]] = [[] for _ in range(7)]
        for cell in cells:
            rows[cell.weekday].append(cell)
        return rows
