# spec: 004-duplicate-warning-streak-recovery
# spec: 006-code-organization
"""Huecos recuperables y estadísticas con días recuperados.

Conserva las mismas entradas, salidas y resultados del dominio original, sin
dependencias de Flet ni de SQLite (RF-2.1, RF-2.2, RF-2.3 y RF-5.3).
"""

from datetime import date, timedelta

from habits.domain.models import HabitStats, RecoverableGap
from habits.domain.streaks import (
    calculate_best_streak,
    calculate_streak,
    count_registered_days,
)


def find_recoverable_gap(
    completed_dates: set[date],
    today: date,
) -> RecoverableGap | None:
    """Encontrar el hueco más reciente que se puede recuperar.

    Un hueco recuperable son uno o dos días consecutivos sin registro. Solo
    se considera el hueco más reciente: primero el que separa el último
    registro de hoy (sin incluir hoy) y, si no existe, el que separa los dos
    registros más recientes. Un hueco de tres o más días no es recuperable.

    Args:
        completed_dates: Fechas con registro normal o recuperado.
        today: Fecha actual. Nunca forma parte del hueco.

    Returns:
        Un `RecoverableGap` con las fechas del hueco, o None si no hay un
        hueco recuperable.
    """
    if not completed_dates:
        return None

    dates = sorted(completed_dates)
    last_date = dates[-1]

    tail_length = max(0, (today - last_date).days - 1)
    if tail_length >= 3:
        return None
    if tail_length in (1, 2):
        return RecoverableGap(
            tuple(
                last_date + timedelta(days=offset)
                for offset in range(1, tail_length + 1)
            )
        )

    for previous, current_date in reversed(list(zip(dates, dates[1:]))):
        gap_length = (current_date - previous).days - 1
        if gap_length >= 3:
            return None
        if gap_length in (1, 2):
            return RecoverableGap(
                tuple(
                    previous + timedelta(days=offset)
                    for offset in range(1, gap_length + 1)
                )
            )

    return None


def get_habit_stats(
    completed_dates: set[date],
    today: date,
    recovered_dates: set[date] | frozenset[date] = frozenset(),
) -> HabitStats:
    """Obtener las estadísticas de un hábito.

    Reutiliza las funciones de racha actual, mejor racha y días registrados
    para no duplicar la lógica de cálculo. Las fechas recuperadas suman a las
    rachas, pero no a los días registrados (RF-2.9 y RF-2.10).

    Args:
        completed_dates: Conjunto de fechas completadas, incluidas las
            recuperadas.
        today: La fecha actual.
        recovered_dates: Subconjunto de fechas recuperadas.

    Returns:
        Un objeto HabitStats con las tres estadísticas del hábito.
    """
    return HabitStats(
        current_streak=calculate_streak(completed_dates, today),
        best_streak=calculate_best_streak(completed_dates),
        registered_days=count_registered_days(
            completed_dates,
            recovered_dates,
        ),
    )
