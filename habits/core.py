# spec: 001-habits-mvp
"""Lógica de dominio: modelos y cálculo de racha."""

from dataclasses import dataclass
from datetime import date, timedelta

_next_id = 1


@dataclass(frozen=True)
class Habit:
    """Modelo de un hábito de estudio.

    Atributos:
        id: Identificador único.
        name: Nombre del hábito.
        start_date: Fecha de inicio del hábito.
    """

    id: int
    name: str
    start_date: date


def create_habit(name: str, start_date: date | None = None) -> Habit:
    """Crear un nuevo hábito con validaciones.

    Args:
        name: Nombre del hábito (1–60 caracteres).
        start_date: Fecha de inicio opcional; por defecto hoy.

    Returns:
        Un nuevo objeto Habit.

    Raises:
        ValueError: Si el nombre está vacío o supera 60 caracteres.
    """
    global _next_id

    if not name or not name.strip():
        raise ValueError("El nombre del hábito es obligatorio.")
    if len(name) > 60:
        raise ValueError("El nombre del hábito no puede superar 60 caracteres.")

    today = date.today()
    if start_date is None or start_date > today:
        start_date = today

    habit = Habit(id=_next_id, name=name, start_date=start_date)
    _next_id += 1
    return habit


def reset_id_counter():
    """Reiniciar el contador de IDs para tests."""
    global _next_id
    _next_id = 1


def mark_completed(
    habit_id: int, completed_dates: set[date], today: date
) -> dict[str, object]:
    """Marcar un hábito como completado para el día actual.

    Args:
        habit_id: Identificador del hábito.
        completed_dates: Conjunto de fechas ya completadas para este hábito.
        today: La fecha actual para validar.

    Returns:
        Un diccionario con 'success' (bool) y 'message' (str).

    Raises:
        ValueError: Si la fecha proporcionada no es la fecha actual.
    """
    current_date = date.today()
    if today != current_date:
        raise ValueError("Solo se puede marcar un hábito como completado para hoy.")

    if today in completed_dates:
        return {
            "success": False,
            "message": "Este hábito ya fue registrado hoy."
        }

    completed_dates.add(today)
    return {
        "success": True,
        "message": "Hábito marcado como completado."
    }


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
