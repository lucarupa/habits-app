# spec: 001-habits-mvp
# spec: 002-ui-redesign
# spec: 004-duplicate-warning-streak-recovery
# spec: 005-local-reminders
# spec: 006-code-organization
"""Esquema SQLite y migraciones de la base de datos.

Conserva las tablas, columnas, datos y migraciones del módulo monolítico
anterior, sin dependencias de Flet (RF-2.2, RF-5.2 y RF-5.6).
"""

import os
import sqlite3
from dataclasses import dataclass

from habits.domain.models import DEFAULT_ICON


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
