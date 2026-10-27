# spec: 002-ui-redesign
# spec: 004-duplicate-warning-streak-recovery
# spec: 005-local-reminders
"""Cargador de estado de la aplicación.

Orquesta la lectura de hábitos, fechas y recordatorios desde `storage.py` y
delega los cálculos en `core.py` y `reminders.py`. No importa Flet ni contiene
lógica de presentación (Constitución, principio 3; RFN-3).
"""

from dataclasses import dataclass, field
from datetime import date

from habits.core import (
    Habit,
    HabitStats,
    HeatmapDay,
    RecoverableGap,
    build_activity_heatmap,
    find_recoverable_gap,
    get_habit_stats,
)
from habits.reminders import (
    DISABLED_LABEL,
    reminder_label as build_reminder_label,
)
from habits.storage import (
    get_completions_db,
    get_recovered_dates_db,
    get_reminder_db,
    list_all_habits_db,
)

HABIT_SUBTITLE = "Hábito de estudio"
EMPTY_SIDEBAR_MESSAGE = "No hay hábitos aún"
EMPTY_TITLE = "Crea tu primer hábito para empezar tu racha"
EMPTY_BUTTON_LABEL = "+ Crear hábito"

STAT_CURRENT_STREAK_LABEL = "Racha actual"
STAT_BEST_STREAK_LABEL = "Mejor racha"
STAT_REGISTERED_DAYS_LABEL = "Días registrados"

HEATMAP_TITLE = "Actividad (últimas 5 semanas)"
HEATMAP_COMPLETED_LABEL = "Completado"
HEATMAP_NOT_COMPLETED_LABEL = "No completado"
HEATMAP_RECOVERED_LABEL = "Recuperado"


def format_date_label(value: date) -> str:
    """Formatear una fecha como dd/mm/aaaa para mostrarla al usuario.

    Args:
        value: Fecha a formatear.

    Returns:
        La fecha en formato dd/mm/aaaa (RF-7.4).
    """
    return value.strftime("%d/%m/%Y")


@dataclass
class HabitState:
    """Hábito junto con sus estadísticas, fechas y recordatorio.

    Atributos:
        habit: El hábito de dominio.
        stats: Racha actual, mejor racha y días registrados.
        completed_dates: Fechas en las que el hábito se completó, incluidas
            las recuperadas.
        recovered_dates: Subconjunto de fechas marcadas como recuperadas.
        reminder_enabled: Indica si el recordatorio está activo.
        reminder_time: Hora guardada en formato HH:MM, aunque esté desactivado.
    """

    habit: Habit
    stats: HabitStats
    completed_dates: set[date]
    recovered_dates: set[date] = field(default_factory=set)
    reminder_enabled: bool = False
    reminder_time: str | None = None

    @property
    def reminder_label(self) -> str:
        """Devolver la etiqueta visible del recordatorio.

        Returns:
            “Sin recordatorio” si está desactivado o no tiene hora válida, o
            “Recordatorio a las HH:MM” si está activo (RF-1.1).
        """
        return build_reminder_label(self.reminder_enabled, self.reminder_time)


@dataclass(frozen=True)
class SidebarItem:
    """Datos que la barra lateral necesita para pintar un hábito.

    Atributos:
        habit_id: Identificador del hábito.
        icon: Clave semántica del icono.
        name: Nombre visible del hábito.
        streak: Racha actual.
        selected: Indica si el elemento está seleccionado.
    """

    habit_id: int
    icon: str
    name: str
    streak: int
    selected: bool


@dataclass(frozen=True)
class DetailHeader:
    """Datos del encabezado del panel de detalle.

    Atributos:
        habit_id: Identificador del hábito.
        icon: Clave semántica del icono.
        name: Nombre visible del hábito.
        subtitle: Subtítulo fijo del detalle.
        start_date_label: Fecha de inicio en formato dd/mm/aaaa.
    """

    habit_id: int
    icon: str
    name: str
    subtitle: str
    start_date_label: str


@dataclass(frozen=True)
class EmptyState:
    """Textos que se muestran cuando no hay hábitos.

    Atributos:
        sidebar_message: Mensaje de la barra lateral.
        title: Título del panel principal.
        button_label: Texto del botón para crear el primer hábito.
    """

    sidebar_message: str
    title: str
    button_label: str


@dataclass(frozen=True)
class StatCard:
    """Datos de una tarjeta de estadísticas.

    Atributos:
        label: Título visible de la tarjeta.
        value: Valor numérico de la estadística.
    """

    label: str
    value: int


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


def load_app_state(
    db_path: str = "data/habits.db",
    today: date | None = None,
) -> AppState:
    """Cargar el estado de la aplicación desde la base de datos.

    Obtiene todos los hábitos y sus fechas de completado, recuperadas y su
    configuración de recordatorio desde `storage.py`, calcula las estadísticas
    con `core.py`, ordena por racha actual descendente y nombre ascendente, y
    selecciona el primer hábito de la lista.

    Args:
        db_path: Ruta al archivo de base de datos SQLite.
        today: Fecha actual; si se omite, se usa `date.today()`.

    Returns:
        Un AppState con los hábitos, sus estadísticas, sus fechas recuperadas,
        sus recordatorios y la selección inicial.
    """
    current_day = today or date.today()
    rows = list_all_habits_db(db_path)

    habits_state: list[HabitState] = []
    for row in rows:
        completed_dates = {
            date.fromisoformat(value)
            for value in get_completions_db(row.id, db_path)
        }
        recovered_dates = {
            date.fromisoformat(value)
            for value in get_recovered_dates_db(row.id, db_path)
        }
        reminder = get_reminder_db(row.id, db_path)
        habits_state.append(
            HabitState(
                habit=Habit(
                    id=row.id,
                    name=row.name,
                    start_date=date.fromisoformat(row.start_date),
                    icon=row.icon,
                ),
                stats=get_habit_stats(
                    completed_dates,
                    current_day,
                    recovered_dates,
                ),
                completed_dates=completed_dates,
                recovered_dates=recovered_dates,
                reminder_enabled=reminder.enabled if reminder else False,
                reminder_time=reminder.reminder_time if reminder else None,
            )
        )

    habits_state.sort(
        key=lambda state: (-state.stats.current_streak, state.habit.name)
    )

    selected_id = habits_state[0].habit.id if habits_state else None
    return AppState(
        habits=habits_state,
        selected_id=selected_id,
        today=current_day,
    )
