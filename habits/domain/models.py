# spec: 001-habits-mvp
# spec: 002-ui-redesign
# spec: 003-edit-delete-habits
# spec: 004-duplicate-warning-streak-recovery
# spec: 006-code-organization
"""Modelos y valores constantes del dominio de hábitos.

Conserva las mismas entradas, salidas y textos del dominio original, sin
dependencias de Flet ni de SQLite (RF-2.2, RF-2.3 y RF-5.3).
"""

from dataclasses import dataclass
from datetime import date

DEFAULT_ICON = "book"
ALLOWED_ICONS: frozenset[str] = frozenset(
    {"book", "code", "science", "language", "music", "art", "math", "fitness"}
)


@dataclass(frozen=True)
class Habit:
    """Modelo de un hábito de estudio.

    Atributos:
        id: Identificador único.
        name: Nombre del hábito.
        start_date: Fecha de inicio del hábito.
        icon: Clave semántica del icono del hábito.
    """

    id: int
    name: str
    start_date: date
    icon: str = DEFAULT_ICON


@dataclass(frozen=True)
class HabitStats:
    """Estadísticas de un hábito.

    Atributos:
        current_streak: Días consecutivos que terminan hoy.
        best_streak: Mayor cantidad de días consecutivos registrados.
        registered_days: Cantidad de fechas distintas con al menos un registro.
    """

    current_streak: int
    best_streak: int
    registered_days: int


@dataclass(frozen=True)
class HeatmapDay:
    """Celda del heatmap de actividad.

    Atributos:
        date: Fecha representada por la celda.
        completed: Indica si el hábito se completó esa fecha.
        is_today: Indica si la celda corresponde a hoy.
        is_future: Indica si la fecha es posterior a hoy.
        weekday: Día de la semana (0 = lunes, 6 = domingo).
        week: Índice de la semana dentro del heatmap (0–4).
        recovered: Indica si el día se recuperó para conservar la racha.
    """

    date: date
    completed: bool
    is_today: bool
    is_future: bool
    weekday: int
    week: int
    recovered: bool = False


@dataclass(frozen=True)
class RecoverableGap:
    """Días consecutivos sin registro que se pueden recuperar.

    Atributos:
        dates: Fechas del hueco, en orden cronológico. Siempre contiene uno
            o dos días y nunca incluye la fecha actual.
    """

    dates: tuple[date, ...]
