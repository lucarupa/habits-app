# spec: 002-ui-redesign
"""Cargador de estado de la aplicación.

Orquesta la lectura de hábitos y fechas desde `storage.py` y delega los
cálculos en `core.py`. No importa Flet ni contiene lógica de presentación
(Constitución, principio 3; RFN-3).
"""

from dataclasses import dataclass, field
from datetime import date

from habits.core import Habit, HabitStats, get_habit_stats
from habits.storage import get_completions_db, list_all_habits_db

HABIT_SUBTITLE = "Hábito de estudio"
EMPTY_SIDEBAR_MESSAGE = "No hay hábitos aún"
EMPTY_TITLE = "Crea tu primer hábito para empezar tu racha"
EMPTY_BUTTON_LABEL = "+ Crear hábito"


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
    """Hábito junto con sus estadísticas y fechas completadas.

    Atributos:
        habit: El hábito de dominio.
        stats: Racha actual, mejor racha y días registrados.
        completed_dates: Fechas en las que el hábito se completó.
    """

    habit: Habit
    stats: HabitStats
    completed_dates: set[date]


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


@dataclass
class AppState:
    """Estado completo de la aplicación en un momento dado.

    Atributos:
        habits: Hábitos ordenados por racha descendente y nombre ascendente.
        selected_id: ID del hábito seleccionado, o None si no hay hábitos.
    """

    habits: list[HabitState] = field(default_factory=list)
    selected_id: int | None = None

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


def load_app_state(
    db_path: str = "data/habits.db",
    today: date | None = None,
) -> AppState:
    """Cargar el estado de la aplicación desde la base de datos.

    Obtiene todos los hábitos y sus fechas de completado desde `storage.py`,
    calcula las estadísticas con `core.py`, ordena por racha actual descendente
    y nombre ascendente, y selecciona el primer hábito de la lista.

    Args:
        db_path: Ruta al archivo de base de datos SQLite.
        today: Fecha actual; si se omite, se usa `date.today()`.

    Returns:
        Un AppState con los hábitos, sus estadísticas y la selección inicial.
    """
    current_day = today or date.today()
    rows = list_all_habits_db(db_path)

    habits_state: list[HabitState] = []
    for row in rows:
        completed_dates = {
            date.fromisoformat(value)
            for value in get_completions_db(row.id, db_path)
        }
        habits_state.append(
            HabitState(
                habit=Habit(
                    id=row.id,
                    name=row.name,
                    start_date=date.fromisoformat(row.start_date),
                    icon=row.icon,
                ),
                stats=get_habit_stats(completed_dates, current_day),
                completed_dates=completed_dates,
            )
        )

    habits_state.sort(
        key=lambda state: (-state.stats.current_streak, state.habit.name)
    )

    selected_id = habits_state[0].habit.id if habits_state else None
    return AppState(habits=habits_state, selected_id=selected_id)
