# spec: 002-ui-redesign
# spec: 004-duplicate-warning-streak-recovery
# spec: 005-local-reminders
# spec: 006-code-organization
"""Carga del estado desde la persistencia.

Orquesta la lectura de hábitos, fechas y recordatorios, y delega los cálculos
en el dominio. No importa Flet ni contiene lógica de presentación (RF-2.2,
RF-2.3 y RF-5.3).
"""

from datetime import date

from habits.domain.models import Habit
from habits.domain.recovery import get_habit_stats
from habits.persistence.completions_repo import (
    get_completions_db,
    get_recovered_dates_db,
)
from habits.persistence.habits_repo import list_all_habits_db
from habits.persistence.reminders_repo import get_reminder_db
from habits.state.app_state import AppState
from habits.state.models import HabitState


def load_app_state(
    db_path: str = "data/habits.db",
    today: date | None = None,
) -> AppState:
    """Cargar el estado de la aplicación desde la base de datos.

    Obtiene todos los hábitos y sus fechas de completado, recuperadas y su
    configuración de recordatorio desde `habits.persistence`, calcula las estadísticas
    con `habits.domain`, ordena por racha actual descendente y nombre ascendente, y
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
