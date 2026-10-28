# spec: 005-local-reminders
# spec: 006-code-organization
"""Repositorio SQLite de configuración y entrega de recordatorios.

Conserva las firmas, consultas y transacciones del módulo monolítico anterior,
sin dependencias de Flet (RF-2.2, RF-2.3, RF-5.2 y RF-5.3).
"""

import sqlite3
from dataclasses import dataclass
from datetime import date, datetime

from habits.reminders import is_due


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
