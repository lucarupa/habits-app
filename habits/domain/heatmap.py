# spec: 002-ui-redesign
# spec: 004-duplicate-warning-streak-recovery
# spec: 006-code-organization
"""Construcción pura del heatmap de actividad.

Conserva las mismas entradas, salidas y resultados del dominio original, sin
dependencias de Flet ni de SQLite (RF-2.1, RF-2.2, RF-2.3 y RF-5.3).
"""

from datetime import date, timedelta

from habits.domain.models import HeatmapDay


def build_activity_heatmap(
    completed_dates: set[date],
    today: date,
    recovered_dates: set[date] | frozenset[date] = frozenset(),
    weeks: int = 5,
) -> list[HeatmapDay]:
    """Construir las celdas del heatmap de actividad.

    La cuadrícula empieza en el lunes de la primera semana y termina en el
    domingo de la semana actual. Las celdas posteriores a hoy se marcan como
    futuras. Los días recuperados se marcan como completados y como
    recuperados para que la interfaz los distinga (RF-2.11).

    Args:
        completed_dates: Conjunto de fechas completadas, incluidas las
            recuperadas.
        today: La fecha actual.
        recovered_dates: Subconjunto de fechas recuperadas que se marcan con
            el estado recuperado.
        weeks: Cantidad de semanas calendario a mostrar (5 por defecto).

    Returns:
        Una lista de celdas HeatmapDay ordenadas por fecha.
    """
    start_of_current_week = today - timedelta(days=today.weekday())
    start = start_of_current_week - timedelta(weeks=weeks - 1)

    cells: list[HeatmapDay] = []
    for offset in range(weeks * 7):
        day = start + timedelta(days=offset)
        cells.append(
            HeatmapDay(
                date=day,
                completed=day in completed_dates,
                is_today=day == today,
                is_future=day > today,
                weekday=day.weekday(),
                week=offset // 7,
                recovered=day in recovered_dates,
            )
        )

    return cells
