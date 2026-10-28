# spec: 001-habits-mvp
# spec: 002-ui-redesign
# spec: 003-edit-delete-habits
# spec: 004-duplicate-warning-streak-recovery
# spec: 005-local-reminders
"""Persistencia SQLite: CRUD de hábitos, registros diarios y recordatorios."""

from dataclasses import dataclass
from datetime import date, datetime
import sqlite3
import os

from habits.domain.models import DEFAULT_ICON
from habits.reminders import is_due


@dataclass
class HabitRow:
    """Fila de hábito leída desde la base de datos.

    Atributos:
        id: Identificador único.
        name: Nombre del hábito.
        start_date: Fecha de inicio en formato YYYY-MM-DD.
        icon: Clave semántica del icono elegido.
    """
    id: int
    name: str
    start_date: str
    icon: str = DEFAULT_ICON


@dataclass
class ReminderRow:
    """Configuración de recordatorio leída desde la base de datos.

    Atributos:
        habit_id: Identificador del hábito asociado.
        enabled: Indica si el recordatorio está activo.
        reminder_time: Hora local en formato HH:MM, si existe.
        effective_from: Fecha local YYYY-MM-DD desde la que puede avisar.
        last_notified_on: Fecha local YYYY-MM-DD del último aviso, si lo hubo.
    """
    habit_id: int
    enabled: bool
    reminder_time: str | None
    effective_from: str
    last_notified_on: str | None = None


@dataclass
class DueReminder:
    """Recordatorio que debe avisarse en el instante consultado.

    Atributos:
        habit_id: Identificador del hábito pendiente.
        habit_name: Nombre actual del hábito, para el texto del aviso.
        reminder_time: Hora local configurada en formato HH:MM.
    """
    habit_id: int
    habit_name: str
    reminder_time: str


def init_db(db_path: str = "data/habits.db") -> None:
    """Inicializar la base de datos creando las tablas si no existen.

    Crea las tablas `habits`, `completions` y `reminders` según el modelo de
    datos del plan. Si la tabla `habits` ya existe sin la columna `icon`, la
    añade con el valor por defecto `book` sin modificar los datos existentes.
    Si la tabla `completions` ya existe sin la columna `recovered`, la añade
    con el valor por defecto 0 para conservar los registros como normales. La
    función es idempotenta: llamarla varias veces no causa errores ni duplica
    columnas ni tablas.

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
            start_date TEXT NOT NULL,
            icon TEXT NOT NULL DEFAULT 'book'
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS completions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            habit_id INTEGER NOT NULL,
            completed_date TEXT NOT NULL,
            recovered INTEGER NOT NULL DEFAULT 0,
            UNIQUE(habit_id, completed_date),
            FOREIGN KEY (habit_id) REFERENCES habits(id)
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS reminders (
            habit_id INTEGER PRIMARY KEY,
            enabled INTEGER NOT NULL DEFAULT 0,
            reminder_time TEXT,
            effective_from TEXT NOT NULL,
            last_notified_on TEXT
        )
        """
    )

    columns = {row[1] for row in cursor.execute("PRAGMA table_info(habits)")}
    if "icon" not in columns:
        cursor.execute(
            "ALTER TABLE habits ADD COLUMN icon TEXT NOT NULL DEFAULT 'book'"
        )

    completion_columns = {
        row[1] for row in cursor.execute("PRAGMA table_info(completions)")
    }
    if "recovered" not in completion_columns:
        cursor.execute(
            "ALTER TABLE completions "
            "ADD COLUMN recovered INTEGER NOT NULL DEFAULT 0"
        )

    conn.commit()
    conn.close()


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


def save_reminder_db(
    habit_id: int,
    enabled: bool,
    reminder_time: str | None,
    effective_from: str,
    db_path: str = "data/habits.db",
) -> None:
    """Guardar o actualizar la configuración de recordatorio de un hábito.

    Cada hábito tiene como máximo una fila en `reminders`. Al actualizar una
    configuración existente se conserva `last_notified_on`, para no repetir el
    aviso del día actual al cambiar la hora (RF-3.2).

    Args:
        habit_id: Identificador único del hábito.
        enabled: Indica si el recordatorio queda activo.
        reminder_time: Hora local en formato HH:MM, o None si no se define.
        effective_from: Fecha local YYYY-MM-DD desde la que puede avisar.
        db_path: Ruta al archivo de base de datos SQLite.

    Raises:
        ValueError: Si no existe un hábito con ese ID.
    """
    conn = sqlite3.connect(db_path)
    try:
        exists = conn.execute(
            "SELECT 1 FROM habits WHERE id = ?",
            (habit_id,),
        ).fetchone()
        if exists is None:
            raise ValueError("El hábito no existe.")

        conn.execute(
            """
            INSERT INTO reminders
                (habit_id, enabled, reminder_time, effective_from)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(habit_id) DO UPDATE SET
                enabled = excluded.enabled,
                reminder_time = excluded.reminder_time,
                effective_from = excluded.effective_from
            """,
            (habit_id, 1 if enabled else 0, reminder_time, effective_from),
        )
        conn.commit()
    finally:
        conn.close()


def get_reminder_db(
    habit_id: int, db_path: str = "data/habits.db"
) -> ReminderRow | None:
    """Obtener la configuración de recordatorio de un hábito.

    Args:
        habit_id: Identificador único del hábito.
        db_path: Ruta al archivo de base de datos SQLite.

    Returns:
        Un objeto ReminderRow si hay configuración guardada, o None si el
        hábito no tiene fila (lo que equivale a recordatorio desactivado).
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        """
        SELECT habit_id, enabled, reminder_time, effective_from, last_notified_on
        FROM reminders WHERE habit_id = ?
        """,
        (habit_id,),
    ).fetchone()
    conn.close()

    if row is None:
        return None

    return ReminderRow(
        habit_id=row["habit_id"],
        enabled=bool(row["enabled"]),
        reminder_time=row["reminder_time"],
        effective_from=row["effective_from"],
        last_notified_on=row["last_notified_on"],
    )


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


def list_due_reminders_db(
    now: datetime, db_path: str = "data/habits.db"
) -> list[DueReminder]:
    """Obtener los recordatorios que deben avisarse en el instante indicado.

    Consulta los recordatorios activos junto con el hábito y sus registros del
    día, y delega en `is_due` la decisión final para no duplicar las reglas de
    vencimiento. Un recordatorio sin fila se considera desactivado y, por
    tanto, nunca aparece en el resultado.

    Args:
        now: Fecha y hora locales actuales.
        db_path: Ruta al archivo de base de datos SQLite.

    Returns:
        Lista de recordatorios vencidos, con el nombre actual del hábito.
    """
    today = now.date().isoformat()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            """
            SELECT
                r.habit_id,
                h.name AS habit_name,
                r.enabled,
                r.reminder_time,
                r.effective_from,
                r.last_notified_on,
                h.start_date,
                EXISTS(
                    SELECT 1 FROM completions c
                    WHERE c.habit_id = r.habit_id
                      AND c.completed_date = ?
                ) AS completed_today
            FROM reminders r
            JOIN habits h ON h.id = r.habit_id
            ORDER BY r.habit_id
            """,
            (today,),
        ).fetchall()
    finally:
        conn.close()

    due: list[DueReminder] = []
    for row in rows:
        last_notified_on = (
            date.fromisoformat(row["last_notified_on"])
            if row["last_notified_on"] is not None
            else None
        )
        if not is_due(
            now,
            enabled=bool(row["enabled"]),
            reminder_time=row["reminder_time"],
            effective_from=date.fromisoformat(row["effective_from"]),
            start_date=date.fromisoformat(row["start_date"]),
            last_notified_on=last_notified_on,
            completed_today=bool(row["completed_today"]),
        ):
            continue

        due.append(
            DueReminder(
                habit_id=row["habit_id"],
                habit_name=row["habit_name"],
                reminder_time=row["reminder_time"],
            )
        )

    return due


def claim_reminder_delivery_db(
    habit_id: int,
    today: str,
    db_path: str = "data/habits.db",
) -> bool:
    """Reclamar de forma atómica la entrega del aviso de un hábito.

    El `UPDATE` condicional solo modifica la fila si no se avisó ya en la
    fecha indicada, de modo que dos ejecuciones simultáneas no dupliquen la
    notificación. Si el envío posterior falla, el llamador debe liberar la
    reclamación.

    Args:
        habit_id: Identificador único del hábito.
        today: Fecha local actual en formato YYYY-MM-DD.
        db_path: Ruta al archivo de base de datos SQLite.

    Returns:
        True si esta llamada reclamó la entrega; False si ya estaba reclamada
        o si el hábito no tiene recordatorio.
    """
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.execute(
            """
            UPDATE reminders
            SET last_notified_on = ?
            WHERE habit_id = ?
              AND (last_notified_on IS NULL OR last_notified_on != ?)
            """,
            (today, habit_id, today),
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def release_reminder_delivery_db(
    habit_id: int,
    today: str,
    db_path: str = "data/habits.db",
) -> None:
    """Liberar la reclamación de entrega del día actual.

    Solo borra `last_notified_on` si coincide con la fecha indicada, para no
    eliminar el registro de un aviso de otro día al reintentar tras un fallo.

    Args:
        habit_id: Identificador único del hábito.
        today: Fecha local actual en formato YYYY-MM-DD.
        db_path: Ruta al archivo de base de datos SQLite.
    """
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            """
            UPDATE reminders
            SET last_notified_on = NULL
            WHERE habit_id = ? AND last_notified_on = ?
            """,
            (habit_id, today),
        )
        conn.commit()
    finally:
        conn.close()
