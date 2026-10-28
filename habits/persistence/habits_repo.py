# spec: 001-habits-mvp
# spec: 002-ui-redesign
# spec: 003-edit-delete-habits
# spec: 005-local-reminders
# spec: 006-code-organization
"""Repositorio SQLite de hábitos.

Conserva las firmas, validaciones y resultados del módulo monolítico anterior,
sin dependencias de Flet (RF-2.2, RF-2.3, RF-5.2 y RF-5.3).
"""

import sqlite3

from habits.domain.models import DEFAULT_ICON
from habits.persistence.schema import HabitRow


def create_habit_db(
    name: str,
    start_date: str,
    icon: str = DEFAULT_ICON,
    db_path: str = "data/habits.db",
) -> int:
    """Crear un hábito en la base de datos.

    Args:
        name: Nombre del hábito.
        start_date: Fecha de inicio en formato YYYY-MM-DD.
        icon: Clave semántica del icono elegido.
        db_path: Ruta al archivo de base de datos SQLite.

    Returns:
        El ID auto-generado del hábito creado.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO habits (name, start_date, icon) VALUES (?, ?, ?)",
        (name, start_date, icon)
    )
    conn.commit()
    habit_id = cursor.lastrowid
    conn.close()
    return habit_id


def get_habit_db(
    habit_id: int, db_path: str = "data/habits.db"
) -> HabitRow | None:
    """Obtener un hábito por su ID desde la base de datos.

    Args:
        habit_id: Identificador único del hábito.
        db_path: Ruta al archivo de base de datos SQLite.

    Returns:
        Un objeto HabitRow si existe, o None si no se encuentra.
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.execute(
        "SELECT id, name, start_date, icon FROM habits WHERE id = ?",
        (habit_id,)
    )
    row = cursor.fetchone()
    conn.close()

    if row is None:
        return None

    return HabitRow(
        id=row["id"],
        name=row["name"],
        start_date=row["start_date"],
        icon=row["icon"],
    )


def update_habit_db(
    habit_id: int,
    name: str,
    start_date: str,
    icon: str = DEFAULT_ICON,
    db_path: str = "data/habits.db",
) -> None:
    """Actualizar nombre, fecha de inicio e icono de un hábito existente.

    Args:
        habit_id: Identificador único del hábito.
        name: Nombre nuevo del hábito.
        start_date: Fecha de inicio nueva en formato YYYY-MM-DD.
        icon: Clave semántica del icono nuevo.
        db_path: Ruta al archivo de base de datos SQLite.

    Raises:
        ValueError: Si no existe un hábito con ese ID.
    """
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.execute(
            "UPDATE habits SET name = ?, start_date = ?, icon = ? WHERE id = ?",
            (name, start_date, icon, habit_id),
        )
        if cursor.rowcount == 0:
            conn.rollback()
            raise ValueError("El hábito no existe.")
        conn.commit()
    finally:
        conn.close()


def delete_habit_db(
    habit_id: int,
    db_path: str = "data/habits.db",
) -> None:
    """Eliminar un hábito y todos sus datos asociados.

    Borra los registros de `completions`, la configuración de `reminders` y,
    por último, la fila de `habits` dentro de una única transacción, para no
    dejar registros ni recordatorios huérfanos si algo falla.

    Args:
        habit_id: Identificador único del hábito.
        db_path: Ruta al archivo de base de datos SQLite.

    Raises:
        ValueError: Si no existe un hábito con ese ID.
    """
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("BEGIN")
        conn.execute(
            "DELETE FROM completions WHERE habit_id = ?",
            (habit_id,),
        )
        conn.execute(
            "DELETE FROM reminders WHERE habit_id = ?",
            (habit_id,),
        )
        cursor = conn.execute(
            "DELETE FROM habits WHERE id = ?",
            (habit_id,),
        )
        if cursor.rowcount == 0:
            conn.rollback()
            raise ValueError("El hábito no existe.")
        conn.commit()
    finally:
        conn.close()


def list_all_habits_db(db_path: str = "data/habits.db") -> list[HabitRow]:
    """Obtener todos los hábitos desde la base de datos.

    RF-3: Retornar la lista completa de hábitos para mostrar al usuario.

    Args:
        db_path: Ruta al archivo de base de datos SQLite.

    Returns:
        Lista de objetos HabitRow con todos los hábitos registrados.
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.execute(
        "SELECT id, name, start_date, icon FROM habits ORDER BY id"
    )
    rows = cursor.fetchall()
    conn.close()

    return [
        HabitRow(
            id=row["id"],
            name=row["name"],
            start_date=row["start_date"],
            icon=row["icon"],
        )
        for row in rows
    ]
