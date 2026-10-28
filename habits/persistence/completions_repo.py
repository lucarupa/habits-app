# spec: 001-habits-mvp
# spec: 002-ui-redesign
# spec: 004-duplicate-warning-streak-recovery
# spec: 006-code-organization
"""Repositorio SQLite de registros diarios y días recuperados.

Conserva las firmas, transacciones y resultados del módulo monolítico anterior,
sin dependencias de Flet (RF-2.2, RF-2.3, RF-5.2 y RF-5.3).
"""

import sqlite3


def mark_completed_db(
    habit_id: int, completed_date: str, db_path: str = "data/habits.db"
) -> None:
    """Registrar un hábito como completado para una fecha dada.

    Inserta un registro en la tabla `completions`. Si ya existe un registro
    para ese hábito y fecha, se levanta un `IntegrityError` debido a la
    restricción UNIQUE.

    Args:
        habit_id: Identificador único del hábito.
        completed_date: Fecha del registro en formato YYYY-MM-DD.
        db_path: Ruta al archivo de base de datos SQLite.

    Raises:
        sqlite3.IntegrityError: Si ya existe un registro para ese hábito y fecha.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO completions (habit_id, completed_date) VALUES (?, ?)",
        (habit_id, completed_date)
    )
    conn.commit()
    conn.close()


def mark_recovered_days_db(
    habit_id: int,
    dates: list[str] | tuple[str, ...] | set[str],
    db_path: str = "data/habits.db",
) -> None:
    """Marcar varios días como recuperados para conservar la racha.

    Inserta las fechas en una única transacción con `INSERT OR IGNORE`, de
    modo que un registro normal ya existente para esa fecha se conserva sin
    cambios. Si el hábito no existe, revierte la transacción y no deja días
    recuperados parciales (RF-2.16 y RF-2.17).

    Args:
        habit_id: Identificador único del hábito.
        dates: Fechas en formato YYYY-MM-DD que se marcan como recuperadas.
        db_path: Ruta al archivo de base de datos SQLite.

    Raises:
        ValueError: Si no existe un hábito con ese ID.
    """
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("BEGIN")
        exists = conn.execute(
            "SELECT 1 FROM habits WHERE id = ?",
            (habit_id,),
        ).fetchone()
        if exists is None:
            raise ValueError("El hábito no existe.")

        conn.executemany(
            "INSERT OR IGNORE INTO completions "
            "(habit_id, completed_date, recovered) VALUES (?, ?, 1)",
            [(habit_id, value) for value in dates],
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def is_completed_today_db(
    habit_id: int, today: str, db_path: str = "data/habits.db"
) -> bool:
    """Verificar si un hábito ya está marcado como completado para una fecha.

    Args:
        habit_id: Identificador único del hábito.
        today: Fecha a verificar en formato YYYY-MM-DD.
        db_path: Ruta al archivo de base de datos SQLite.

    Returns:
        True si el hábito ya tiene un registro para la fecha, False en caso contrario.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.execute(
        "SELECT 1 FROM completions WHERE habit_id = ? AND completed_date = ?",
        (habit_id, today)
    )
    row = cursor.fetchone()
    conn.close()

    return row is not None


def get_completions_db(
    habit_id: int, db_path: str = "data/habits.db"
) -> list[str]:
    """Obtener todas las fechas de completado de un hábito.

    RF-3: Necesario para calcular la racha de cada hábito.

    Args:
        habit_id: Identificador único del hábito.
        db_path: Ruta al archivo de base de datos SQLite.

    Returns:
        Lista de fechas en formato YYYY-MM-DD, ordenadas ascendente.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.execute(
        "SELECT completed_date FROM completions WHERE habit_id = ? ORDER BY completed_date",
        (habit_id,)
    )
    rows = cursor.fetchall()
    conn.close()

    return [row[0] for row in rows]


def get_recovered_dates_db(
    habit_id: int, db_path: str = "data/habits.db"
) -> list[str]:
    """Obtener las fechas recuperadas de un hábito.

    Args:
        habit_id: Identificador único del hábito.
        db_path: Ruta al archivo de base de datos SQLite.

    Returns:
        Lista de fechas recuperadas en formato YYYY-MM-DD, ordenadas de forma
        ascendente.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.execute(
        "SELECT completed_date FROM completions "
        "WHERE habit_id = ? AND recovered = 1 "
        "ORDER BY completed_date",
        (habit_id,),
    )
    rows = cursor.fetchall()
    conn.close()

    return [row[0] for row in rows]
