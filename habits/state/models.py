# spec: 002-ui-redesign
# spec: 004-duplicate-warning-streak-recovery
# spec: 005-local-reminders
# spec: 006-code-organization
"""Modelos, textos y formatos del estado de la aplicación.

Conserva las mismas entradas, salidas y textos del módulo monolítico anterior,
sin dependencias de Flet ni SQLite (RF-2.2, RF-2.3 y RF-5.3).
"""

from dataclasses import dataclass, field
from datetime import date

from habits.domain.models import Habit, HabitStats
from habits.reminders import reminder_label as build_reminder_label

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
