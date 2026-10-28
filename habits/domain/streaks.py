# spec: 001-habits-mvp
# spec: 004-duplicate-warning-streak-recovery
# spec: 006-code-organization
"""Cálculo de rachas, días registrados y orden de hábitos.

Conserva las mismas entradas, salidas y resultados del dominio original, sin
dependencias de Flet ni de SQLite (RF-2.1, RF-2.2, RF-2.3 y RF-5.3).
"""

from datetime import date, timedelta

from habits.domain.models import Habit


def calculate_streak(completed_dates: set[date], today: date) -> int:
    """Calcular la racha de días consecutivos de un hábito.

    Cuenta hacia atrás desde hoy mientras los días sean consecutivos.
    Si el último día registrado no es hoy, la racha activa es cero.

    Args:
        completed_dates: Conjunto de fechas completadas para un hábito.
        today: La fecha actual.

    Returns:
        Número de días consecutivos terminando en hoy.
    """
    if not completed_dates:
        return 0

    # Ordenar fechas descendente para empezar desde la más reciente
    sorted_dates = sorted(completed_dates, reverse=True)
    last_date = sorted_dates[0]

    # RF-4.2: Si el último día no es hoy, la racha es 0
    if last_date != today:
        return 0

    # RF-4.3: Un solo día hoy, racha es 1
    streak = 1
    expected_date = today - timedelta(days=1)

    # RF-4.1 y RF-4.4: contar hacia atrás hasta encontrar un hueco
    for d in sorted_dates[1:]:
        if d == expected_date:
            streak += 1
            expected_date -= timedelta(days=1)
        elif d < expected_date:
            # RF-4.4: hueco encontrado, detener conteo
            break

    return streak


def calculate_best_streak(completed_dates: set[date]) -> int:
    """Calcular la mejor racha histórica de un hábito.

    Recorre las fechas ordenadas y encuentra el bloque de días consecutivos
    más largo, sin importar si termina hoy.

    Args:
        completed_dates: Conjunto de fechas completadas para un hábito.

    Returns:
        La cantidad de días del bloque consecutivo más largo, o 0 si no hay
        registros.
    """
    if not completed_dates:
        return 0

    sorted_dates = sorted(completed_dates)
    best = 1
    current = 1
    previous = sorted_dates[0]

    for current_date in sorted_dates[1:]:
        if current_date == previous + timedelta(days=1):
            current += 1
        else:
            if current > best:
                best = current
            current = 1
        previous = current_date

    return max(best, current)


def count_registered_days(
    completed_dates: set[date],
    recovered_dates: set[date] | frozenset[date] = frozenset(),
) -> int:
    """Contar las fechas distintas con un registro normal.

    Los días recuperados cuentan para la racha, pero no para “Días
    registrados” (RF-2.10).

    Args:
        completed_dates: Conjunto de fechas completadas, incluidas las
            recuperadas.
        recovered_dates: Subconjunto de fechas recuperadas que no deben
            contarse como registros normales.

    Returns:
        La cantidad de fechas registradas que no son recuperadas.
    """
    return len(set(completed_dates) - set(recovered_dates))


def list_habits_with_streak(
    habits: list[Habit],
    completions_by_habit: dict[int, set[date]],
    today: date
) -> list[tuple[Habit, int]]:
    """Retornar una lista de hábitos con su racha, ordenada por racha descendente.

    RF-3.1: Cada hábito aparece con su nombre y racha actual.
    RF-3.2: Orden principal por racha de mayor a menor.
    RF-3.3: Desempate alfabético por nombre.
    RF-3.4: Si no hay hábitos, retorna lista vacía.

    Args:
        habits: Lista de objetos Habit.
        completions_by_habit: Diccionario que mapea habit_id a sus fechas completadas.
        today: La fecha actual.

    Returns:
        Lista de tuplas (Habit, streak) ordenada por racha descendente
        y nombre alfabético como desempate.
    """
    result = []
    for habit in habits:
        completed_dates = completions_by_habit.get(habit.id, set())
        streak = calculate_streak(completed_dates, today)
        result.append((habit, streak))

    # RF-3.2: orden por racha descendente; RF-3.3: desempate alfabético
    result.sort(key=lambda item: (-item[1], item[0].name))
    return result
