# spec: 001-habits-mvp
"""Persistencia SQLite: CRUD de hábitos y registros diarios."""

from dataclasses import dataclass
import sqlite3
import os


@dataclass
class HabitRow:
    """Fila de hábito leída desde la base de datos.

    Atributos:
        id: Identificador único.
        name: Nombre del hábito.
        start_date: Fecha de inicio en formato YYYY-MM-DD.
    """
    id: int
    name: str
    start_date: str


def init_db(db_path: str = "data/habits.db") -> None:
    """Inicializar la base de datos creando las tablas si no existen.

    Crea las tablas `habits` y `completions` según el modelo de datos del plan.
    La función es idempotenta: llamarla varias veces no causa errores.

    Args:
        db_path: Ruta al archivo de base de datos SQLite.
    """
    os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS habits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            start_date TEXT NOT NULL
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS completions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            habit_id INTEGER NOT NULL,
            completed_date TEXT NOT NULL,
            UNIQUE(habit_id, completed_date),
            FOREIGN KEY (habit_id) REFERENCES habits(id)
        )
        """
    )

    conn.commit()
    conn.close()


def create_habit_db(
    name: str, start_date: str, db_path: str = "data/habits.db"
) -> int:
    """Crear un hábito en la base de datos.

    Args:
        name: Nombre del hábito.
        start_date: Fecha de inicio en formato YYYY-MM-DD.
        db_path: Ruta al archivo de base de datos SQLite.

    Returns:
        El ID auto-generado del hábito creado.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO habits (name, start_date) VALUES (?, ?)",
        (name, start_date)
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
        "SELECT id, name, start_date FROM habits WHERE id = ?",
        (habit_id,)
    )
    row = cursor.fetchone()
    conn.close()

    if row is None:
        return None

    return HabitRow(id=row["id"], name=row["name"], start_date=row["start_date"])


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
        "SELECT id, name, start_date FROM habits ORDER BY id"
    )
    rows = cursor.fetchall()
    conn.close()

    return [
        HabitRow(id=row["id"], name=row["name"], start_date=row["start_date"])
        for row in rows
    ]


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
