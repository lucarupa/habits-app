# spec: 001-habits-mvp
# spec: 002-ui-redesign
# spec: 003-edit-delete-habits
"""Lógica de dominio: modelos y cálculo de racha."""

from dataclasses import dataclass
from datetime import date, timedelta

DEFAULT_ICON = "book"
ALLOWED_ICONS: frozenset[str] = frozenset(
    {"book", "code", "science", "language", "music", "art", "math", "fitness"}
)

_next_id = 1


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
    """

    date: date
    completed: bool
    is_today: bool
    is_future: bool
    weekday: int
    week: int


def create_habit(
    name: str,
    start_date: date | None = None,
    icon: str = DEFAULT_ICON,
) -> Habit:
    """Crear un nuevo hábito con validaciones.

    Args:
        name: Nombre del hábito (1–60 caracteres).
        start_date: Fecha de inicio opcional; por defecto hoy.
        icon: Clave semántica del icono; si no es válida, se usa el icono por defecto.

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
    if icon not in ALLOWED_ICONS:
        icon = DEFAULT_ICON

    today = date.today()
    if start_date is None or start_date > today:
        start_date = today

    habit = Habit(id=_next_id, name=name, start_date=start_date, icon=icon)
    _next_id += 1
    return habit


def update_habit(
    habit: Habit,
    name: str,
    start_date: date | None,
    icon: str,
    today: date,
) -> Habit:
    """Actualizar los datos editables de un hábito.

    Conserva el identificador del hábito original y sus registros diarios,
    que no forman parte de este modelo.

    Args:
        habit: Hábito que se quiere actualizar.
        name: Nombre nuevo; se recortan los espacios sobrantes.
        start_date: Fecha de inicio nueva; si es None se conserva la actual.
        icon: Clave semántica del icono; si no es válida se conserva la actual.
        today: Fecha actual para rechazar fechas futuras.

    Returns:
        Un nuevo Habit con el mismo id y los datos actualizados.

    Raises:
        ValueError: Si el nombre está vacío o supera 60 caracteres, o si la
            fecha de inicio es posterior a today.
    """
    name = name.strip() if name else ""

    if not name:
        raise ValueError("El nombre del hábito es obligatorio.")
    if len(name) > 60:
        raise ValueError("El nombre del hábito no puede superar 60 caracteres.")

    if start_date is None:
        start_date = habit.start_date
    if start_date > today:
        raise ValueError("La fecha de inicio no puede ser futura.")

    if icon not in ALLOWED_ICONS:
        icon = habit.icon

    return Habit(
        id=habit.id,
        name=name,
        start_date=start_date,
        icon=icon,
    )


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


def count_registered_days(completed_dates: set[date]) -> int:
    """Contar las fechas distintas con al menos un registro.

    Args:
        completed_dates: Conjunto de fechas completadas para un hábito.

    Returns:
        La cantidad de fechas distintas registradas.
    """
    return len(set(completed_dates))


def get_habit_stats(completed_dates: set[date], today: date) -> HabitStats:
    """Obtener las estadísticas de un hábito.

    Reutiliza las funciones de racha actual, mejor racha y días registrados
    para no duplicar la lógica de cálculo.

    Args:
        completed_dates: Conjunto de fechas completadas para un hábito.
        today: La fecha actual.

    Returns:
        Un objeto HabitStats con las tres estadísticas del hábito.
    """
    return HabitStats(
        current_streak=calculate_streak(completed_dates, today),
        best_streak=calculate_best_streak(completed_dates),
        registered_days=count_registered_days(completed_dates),
    )


def build_activity_heatmap(
    completed_dates: set[date],
    today: date,
    weeks: int = 5,
) -> list[HeatmapDay]:
    """Construir las celdas del heatmap de actividad.

    La cuadrícula empieza en el lunes de la primera semana y termina en el
    domingo de la semana actual. Las celdas posteriores a hoy se marcan como
    futuras.

    Args:
        completed_dates: Conjunto de fechas completadas para un hábito.
        today: La fecha actual.
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
            )
        )

    return cells


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
