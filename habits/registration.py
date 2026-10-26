# spec: 002-ui-redesign
"""Lógica pura del registro del día actual.

Persiste el completado de hoy y evita duplicados delegando en `storage.py`.
No importa Flet (Constitución, principio 3). Cubre RF-5.1 a RF-5.6.
"""

import sqlite3
from dataclasses import dataclass
from datetime import date

from habits.storage import is_completed_today_db, mark_completed_db

REGISTRATION_TITLE = "Registrar hoy"
REGISTRATION_BUTTON_LABEL = "Guardar"
REGISTRATION_DUPLICATE_MESSAGE = "Ya registrado hoy"
REGISTRATION_SUCCESS_MESSAGE = "✅ Registro guardado"


@dataclass(frozen=True)
class RegistrationResult:
    """Resultado de intentar registrar el día actual.

    Atributos:
        success: Indica si el registro se persistió.
        message: Mensaje visible para el usuario.
    """

    success: bool
    message: str


def is_registered_today(
    habit_id: int,
    today: date,
    db_path: str = "data/habits.db",
) -> bool:
    """Indicar si un hábito ya está registrado para la fecha dada.

    Args:
        habit_id: Identificador del hábito.
        today: Fecha a consultar.
        db_path: Ruta a la base de datos SQLite.

    Returns:
        True si ya existe un registro para ese hábito y fecha.
    """
    return is_completed_today_db(habit_id, today.isoformat(), db_path)


def register_today(
    habit_id: int,
    today: date,
    db_path: str = "data/habits.db",
) -> RegistrationResult:
    """Registrar el completado de un hábito para la fecha indicada.

    La interfaz solo pasa la fecha actual. Si el registro ya existe, devuelve
    el mensaje de duplicado sin insertar una segunda fila.

    Args:
        habit_id: Identificador del hábito.
        today: Fecha que se va a registrar.
        db_path: Ruta a la base de datos SQLite.

    Returns:
        Un RegistrationResult con el resultado y el mensaje para el usuario.
    """
    if is_registered_today(habit_id, today, db_path):
        return RegistrationResult(
            success=False,
            message=REGISTRATION_DUPLICATE_MESSAGE,
        )

    try:
        mark_completed_db(habit_id, today.isoformat(), db_path)
    except sqlite3.IntegrityError:
        return RegistrationResult(
            success=False,
            message=REGISTRATION_DUPLICATE_MESSAGE,
        )

    return RegistrationResult(
        success=True,
        message=REGISTRATION_SUCCESS_MESSAGE,
    )
