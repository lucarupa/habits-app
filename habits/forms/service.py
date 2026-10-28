# spec: 002-ui-redesign
# spec: 003-edit-delete-habits
# spec: 006-code-organization
"""Alta y actualización de hábitos desde el formulario.

Valida los datos y persiste delegando en `habits.domain` y
`habits.persistence`. No importa Flet (RF-2.2, RF-2.3 y RF-5.3).
"""

from datetime import date

from habits.domain.habits import create_habit, update_habit
from habits.domain.models import Habit
from habits.forms.models import (
    CreateHabitResult,
    HabitFormData,
    UpdateHabitResult,
)
from habits.forms.validation import validate_habit_form, validate_habit_update
from habits.persistence.habits_repo import create_habit_db, update_habit_db


def create_habit_from_form(
    data: HabitFormData,
    db_path: str = "data/habits.db",
    today: date | None = None,
) -> CreateHabitResult:
    """Validar el formulario y persistir el hábito.

    Args:
        data: Datos en bruto del formulario.
        db_path: Ruta al archivo de base de datos SQLite.
        today: Fecha actual para resolver la fecha opcional.

    Returns:
        El ID del hábito creado junto con sus datos guardados (RF-2.7).

    Raises:
        ValueError: Si el formulario no es válido; en ese caso no se persiste
            ningún hábito (RF-2.2, RF-2.3, RF-2.10).
    """
    form = validate_habit_form(data, today=today)
    habit = create_habit(form.name, form.start_date, form.icon)
    habit_id = create_habit_db(
        habit.name,
        habit.start_date.isoformat(),
        habit.icon,
        db_path,
    )

    return CreateHabitResult(
        habit_id=habit_id,
        name=habit.name,
        start_date=habit.start_date,
        icon=habit.icon,
    )


def update_habit_from_form(
    habit: Habit,
    data: HabitFormData,
    db_path: str = "data/habits.db",
    today: date | None = None,
) -> UpdateHabitResult:
    """Validar el formulario de edición y persistir los cambios.

    Delega la actualización del dominio en `update_habit` y la escritura en
    `update_habit_db`. Los registros diarios del hábito no se modifican
    (RF-2.12).

    Args:
        habit: Hábito que se está editando.
        data: Datos en bruto del formulario de edición.
        db_path: Ruta al archivo de base de datos SQLite.
        today: Fecha actual para rechazar fechas futuras.

    Returns:
        El ID del hábito editado junto con sus datos guardados (RF-2.9).

    Raises:
        ValueError: Si el formulario no es válido o el hábito ya no existe;
            en esos casos no se persiste ningún cambio.
    """
    current_day = today or date.today()
    validated = validate_habit_update(habit, data, today=current_day)
    updated = update_habit(
        habit,
        name=validated.name,
        start_date=validated.start_date,
        icon=validated.icon,
        today=current_day,
    )

    update_habit_db(
        habit_id=updated.id,
        name=updated.name,
        start_date=updated.start_date.isoformat(),
        icon=updated.icon,
        db_path=db_path,
    )

    return UpdateHabitResult(
        habit_id=updated.id,
        name=updated.name,
        start_date=updated.start_date,
        icon=updated.icon,
    )
