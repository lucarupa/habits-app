# spec: 001-habits-mvp
# spec: 003-edit-delete-habits
# spec: 006-code-organization
"""Operaciones puras de alta, edición y marcado de hábitos.

Conserva las mismas validaciones, mensajes y resultados del dominio original,
sin dependencias de Flet ni de SQLite (RF-2.2, RF-2.3 y RF-5.3).
"""

from datetime import date

from habits.domain.models import ALLOWED_ICONS, DEFAULT_ICON, Habit

_next_id = 1


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


def reset_id_counter() -> None:
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
