# spec: 001-habits-mvp
# spec: 002-ui-redesign
# spec: 003-edit-delete-habits
# spec: 004-duplicate-warning-streak-recovery
# spec: 005-local-reminders
"""Tests para la capa de persistencia SQLite — Tarea 4.1, RFN-3."""

import os
import sqlite3
import tempfile
from contextlib import closing
from datetime import date, datetime

import pytest

from habits.persistence.completions_repo import (
    get_completions_db,
    get_recovered_dates_db,
    is_completed_today_db,
    mark_completed_db,
    mark_recovered_days_db,
)
from habits.persistence.habits_repo import (
    create_habit_db,
    delete_habit_db,
    get_habit_db,
    list_all_habits_db,
    update_habit_db,
)
from habits.persistence.reminders_repo import (
    claim_reminder_delivery_db,
    get_reminder_db,
    list_due_reminders_db,
    release_reminder_delivery_db,
    save_reminder_db,
)
from habits.persistence.schema import init_db


class TestInitDb:
    """Tests para init_db() — Tarea 4.1, RFN-3."""

    def setup_method(self):
        """Crear un directorio temporal para cada test."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_habits.db")

    def teardown_method(self):
        """Limpiar la base de datos temporal después de cada test."""
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_init_db_creates_file(self):
        """RFN-3: init_db crea el archivo de base de datos si no existe."""
        assert not os.path.exists(self.db_path)

        init_db(self.db_path)

        assert os.path.exists(self.db_path)

    def test_init_db_creates_habits_table(self):
        """RF-1: init_db crea la tabla 'habits' con las columnas esperadas."""
        init_db(self.db_path)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='habits'"
        )
        assert cursor.fetchone() is not None

        columns = {row[1] for row in conn.execute("PRAGMA table_info(habits)")}
        assert "id" in columns
        assert "name" in columns
        assert "start_date" in columns
        conn.close()

    def test_init_db_creates_completions_table(self):
        """RF-2: init_db crea la tabla 'completions' con las columnas esperadas."""
        init_db(self.db_path)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='completions'"
        )
        assert cursor.fetchone() is not None

        columns = {row[1] for row in conn.execute("PRAGMA table_info(completions)")}
        assert "id" in columns
        assert "habit_id" in columns
        assert "completed_date" in columns
        conn.close()

    def test_init_db_unique_constraint(self):
        """RF-2.2: La tabla 'completions' tiene restricción UNIQUE(habit_id, completed_date)."""
        init_db(self.db_path)

        conn = sqlite3.connect(self.db_path)
        # Insertar un registro
        conn.execute("INSERT INTO habits (name, start_date) VALUES (?, ?)", ("Test", "2024-01-01"))
        conn.execute(
            "INSERT INTO completions (habit_id, completed_date) VALUES (?, ?)",
            (1, "2024-01-01"),
        )
        conn.commit()

        # Intentar insertar duplicado debe fallar
        try:
            conn.execute(
                "INSERT INTO completions (habit_id, completed_date) VALUES (?, ?)",
                (1, "2024-01-01"),
            )
            conn.commit()
            assert False, "Se esperaba IntegrityError"
        except sqlite3.IntegrityError:
            pass  # Comportamiento esperado

        conn.close()

    def test_init_db_idempotent(self):
        """RFN-3: Llamar init_db() dos veces no causa error."""
        init_db(self.db_path)
        init_db(self.db_path)  # No debe levantar excepción

        conn = sqlite3.connect(self.db_path)
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        assert "habits" in tables
        assert "completions" in tables
        conn.close()

    def _create_legacy_db(self) -> None:
        """Crear una base con el esquema anterior, sin columna icon."""
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            """
            CREATE TABLE habits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                start_date TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE completions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                habit_id INTEGER NOT NULL,
                completed_date TEXT NOT NULL,
                UNIQUE(habit_id, completed_date),
                FOREIGN KEY (habit_id) REFERENCES habits(id)
            )
            """
        )
        conn.execute(
            "INSERT INTO habits (name, start_date) VALUES (?, ?)",
            ("Leer", "2024-01-01"),
        )
        conn.execute(
            "INSERT INTO completions (habit_id, completed_date) VALUES (?, ?)",
            (1, "2024-01-02"),
        )
        conn.commit()
        conn.close()

    def test_init_db_creates_icon_column(self):
        """RF-2.8: Una base nueva incluye la columna icon con valor por defecto."""
        init_db(self.db_path)

        with closing(sqlite3.connect(self.db_path)) as conn:
            columns = {row[1] for row in conn.execute("PRAGMA table_info(habits)")}
            assert "icon" in columns

            conn.execute(
                "INSERT INTO habits (name, start_date) VALUES (?, ?)",
                ("Leer", "2024-01-01"),
            )
            conn.commit()
            icon = conn.execute(
                "SELECT icon FROM habits WHERE id = 1"
            ).fetchone()[0]

        assert icon == "book"

    def test_init_db_migrates_existing_habits(self):
        """RF-2.9: Una base antigua recibe icon con valor por defecto."""
        self._create_legacy_db()

        init_db(self.db_path)

        with closing(sqlite3.connect(self.db_path)) as conn:
            row = conn.execute(
                "SELECT name, start_date, icon FROM habits WHERE id = 1"
            ).fetchone()

        assert row == ("Leer", "2024-01-01", "book")

    def test_init_db_migration_preserves_data(self):
        """RF-2.9, RFN-1: La migración conserva hábitos y registros."""
        self._create_legacy_db()

        init_db(self.db_path)

        with closing(sqlite3.connect(self.db_path)) as conn:
            habit = conn.execute(
                "SELECT name, start_date FROM habits WHERE id = 1"
            ).fetchone()
            completion = conn.execute(
                "SELECT habit_id, completed_date FROM completions WHERE id = 1"
            ).fetchone()

        assert habit == ("Leer", "2024-01-01")
        assert completion == (1, "2024-01-02")

    def test_init_db_migration_is_idempotent(self):
        """RF-2.9, RFN-3: Migrar dos veces no duplica ni falla."""
        self._create_legacy_db()

        init_db(self.db_path)
        init_db(self.db_path)

        with closing(sqlite3.connect(self.db_path)) as conn:
            columns = [
                row[1] for row in conn.execute("PRAGMA table_info(habits)")
            ]
            row = conn.execute(
                "SELECT name, start_date, icon FROM habits WHERE id = 1"
            ).fetchone()
            total = conn.execute("SELECT COUNT(*) FROM habits").fetchone()[0]

        assert columns.count("icon") == 1
        assert row == ("Leer", "2024-01-01", "book")
        assert total == 1


class TestInitDbRecoveredColumn:
    """Esquema y migración de la columna recovered — Tarea 2.1.

    RF-2.8, RF-2.15 y RF-2.17: una base nueva marca los registros normales con
    `recovered = 0`, una base antigua recibe la columna conservando sus filas y
    la migración se puede ejecutar varias veces sin duplicar columnas.
    """

    def setup_method(self):
        """Crear un directorio temporal para cada test."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_habits.db")

    def teardown_method(self):
        """Limpiar la base de datos temporal después de cada test."""
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def _create_legacy_db(self) -> None:
        """Crear una base con el esquema anterior, sin columna recovered."""
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            """
            CREATE TABLE habits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                start_date TEXT NOT NULL,
                icon TEXT NOT NULL DEFAULT 'book'
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE completions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                habit_id INTEGER NOT NULL,
                completed_date TEXT NOT NULL,
                UNIQUE(habit_id, completed_date),
                FOREIGN KEY (habit_id) REFERENCES habits(id)
            )
            """
        )
        conn.execute(
            "INSERT INTO habits (name, start_date) VALUES (?, ?)",
            ("Leer", "2026-10-20"),
        )
        conn.execute(
            "INSERT INTO completions (habit_id, completed_date) VALUES (?, ?)",
            (1, "2026-10-25"),
        )
        conn.commit()
        conn.close()

    def test_init_db_creates_recovered_column_with_default_zero(self):
        """RF-2.8, RF-2.17: una base nueva guarda los normales con recovered 0."""
        init_db(self.db_path)

        with closing(sqlite3.connect(self.db_path)) as conn:
            columns = {
                row[1]: row
                for row in conn.execute("PRAGMA table_info(completions)")
            }
            assert "recovered" in columns
            _, _, column_type, not_null, default, _ = columns["recovered"]
            assert column_type == "INTEGER"
            assert not_null == 1
            assert default == "0"

            conn.execute(
                "INSERT INTO habits (name, start_date) VALUES (?, ?)",
                ("Leer", "2026-10-20"),
            )
            conn.execute(
                "INSERT INTO completions (habit_id, completed_date) VALUES (?, ?)",
                (1, "2026-10-26"),
            )
            conn.commit()
            recovered = conn.execute(
                "SELECT recovered FROM completions WHERE id = 1"
            ).fetchone()[0]

        assert recovered == 0

    def test_init_db_migrates_existing_completions_without_recovered(self):
        """RF-2.15, RF-2.17: la base antigua recibe recovered sin perder filas."""
        self._create_legacy_db()

        init_db(self.db_path)

        with closing(sqlite3.connect(self.db_path)) as conn:
            habit = conn.execute(
                "SELECT name, start_date FROM habits WHERE id = 1"
            ).fetchone()
            completion = conn.execute(
                "SELECT habit_id, completed_date, recovered "
                "FROM completions WHERE id = 1"
            ).fetchone()

        assert habit == ("Leer", "2026-10-20")
        assert completion == (1, "2026-10-25", 0)

    def test_init_db_recovered_migration_is_idempotent(self):
        """RF-2.15: migrar dos veces no duplica la columna ni altera las filas."""
        self._create_legacy_db()

        init_db(self.db_path)
        init_db(self.db_path)

        with closing(sqlite3.connect(self.db_path)) as conn:
            columns = [
                row[1] for row in conn.execute("PRAGMA table_info(completions)")
            ]
            completion = conn.execute(
                "SELECT habit_id, completed_date, recovered "
                "FROM completions WHERE id = 1"
            ).fetchone()
            total = conn.execute(
                "SELECT COUNT(*) FROM completions"
            ).fetchone()[0]

        assert columns.count("recovered") == 1
        assert completion == (1, "2026-10-25", 0)
        assert total == 1


class TestCreateHabitDb:
    """Tests para create_habit_db() y get_habit_db() — Tarea 4.2, RF-1."""

    def setup_method(self):
        """Crear una base de datos temporal para cada test."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_habits.db")
        init_db(self.db_path)

    def teardown_method(self):
        """Limpiar la base de datos temporal después de cada test."""
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_create_habit_persists(self):
        """RF-1: Un hábito creado se puede leer de vuelta con los mismos datos."""
        today = date.today().isoformat()
        habit_id = create_habit_db("Estudiar Python", today, db_path=self.db_path)

        habit = get_habit_db(habit_id, db_path=self.db_path)

        assert habit is not None
        assert habit.id == habit_id
        assert habit.name == "Estudiar Python"
        assert habit.start_date == today

    def test_create_habit_returns_autoincrement_id(self):
        """RF-1: create_habit_db retorna el ID auto-generado por la base de datos."""
        today = date.today().isoformat()
        habit_id_1 = create_habit_db("Hábito A", today, db_path=self.db_path)
        habit_id_2 = create_habit_db("Hábito B", today, db_path=self.db_path)

        assert habit_id_1 == 1
        assert habit_id_2 == 2

    def test_get_habit_db_not_found(self):
        """RF-1: get_habit_db retorna None para un ID que no existe."""
        habit = get_habit_db(999, db_path=self.db_path)

        assert habit is None

    def test_create_habit_with_past_start_date(self):
        """RF-1.2: Un hábito con fecha de inicio en el pasado se almacena correctamente."""
        past_date = "2024-01-15"
        habit_id = create_habit_db("Leer", past_date, db_path=self.db_path)

        habit = get_habit_db(habit_id, db_path=self.db_path)

        assert habit.start_date == past_date

    def test_create_habit_persists_icon(self):
        """RF-2.8: El icono se guarda y se lee de vuelta."""
        today = date.today().isoformat()
        habit_id = create_habit_db(
            "Estudiar Python", today, icon="code", db_path=self.db_path
        )

        habit = get_habit_db(habit_id, db_path=self.db_path)

        assert habit is not None
        assert habit.icon == "code"

    def test_create_habit_db_default_icon(self):
        """RF-2.6: Sin icono se guarda el valor por defecto."""
        today = date.today().isoformat()
        habit_id = create_habit_db("Leer", today, db_path=self.db_path)

        habit = get_habit_db(habit_id, db_path=self.db_path)

        assert habit is not None
        assert habit.icon == "book"

    def test_get_habit_db_returns_icon(self):
        """RF-2.8: get_habit_db devuelve el icono del hábito."""
        today = date.today().isoformat()
        habit_id = create_habit_db(
            "Laboratorio", today, icon="science", db_path=self.db_path
        )

        habit = get_habit_db(habit_id, db_path=self.db_path)

        assert habit.icon == "science"


class TestUpdateHabitDb:
    """Tests para update_habit_db() — Tarea 2.1, RF-2.13, RF-2.14."""

    def setup_method(self):
        """Crear una base de datos temporal para cada test."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_habits.db")
        init_db(self.db_path)

    def teardown_method(self):
        """Limpiar la base de datos temporal después de cada test."""
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_update_habit_db_updates_existing_row(self):
        """RF-2.14: Persiste nombre, fecha e icono sin crear una fila nueva."""
        habit_id = create_habit_db(
            "Python", "2026-09-01", icon="code", db_path=self.db_path
        )

        update_habit_db(
            habit_id,
            name="Python avanzado",
            start_date="2026-10-01",
            icon="science",
            db_path=self.db_path,
        )

        habit = get_habit_db(habit_id, db_path=self.db_path)

        assert habit is not None
        assert habit.id == habit_id
        assert habit.name == "Python avanzado"
        assert habit.start_date == "2026-10-01"
        assert habit.icon == "science"
        assert len(list_all_habits_db(db_path=self.db_path)) == 1

    def test_update_habit_db_raises_for_unknown_id(self):
        """RF-2.13: Un ID inexistente lanza ValueError y no crea filas."""
        with pytest.raises(ValueError, match="no existe"):
            update_habit_db(
                999,
                name="Fantasma",
                start_date="2026-10-01",
                icon="book",
                db_path=self.db_path,
            )

        assert list_all_habits_db(db_path=self.db_path) == []


class TestDeleteHabitDb:
    """Tests para delete_habit_db() — Tarea 2.2, RF-3.4, RF-3.8."""

    def setup_method(self):
        """Crear una base de datos temporal para cada test."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_habits.db")
        init_db(self.db_path)

    def teardown_method(self):
        """Limpiar la base de datos temporal después de cada test."""
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_delete_habit_db_removes_habit_and_completions(self):
        """RF-3.4: Borra el hábito y todos sus registros diarios."""
        habit_id = create_habit_db("Python", "2026-09-01", db_path=self.db_path)
        mark_completed_db(habit_id, "2026-10-24", db_path=self.db_path)
        mark_completed_db(habit_id, "2026-10-25", db_path=self.db_path)

        delete_habit_db(habit_id, db_path=self.db_path)

        assert get_habit_db(habit_id, db_path=self.db_path) is None
        assert get_completions_db(habit_id, db_path=self.db_path) == []

    def test_delete_habit_db_keeps_other_habits(self):
        """RF-3.4: No afecta a otros hábitos ni a sus registros."""
        deleted_id = create_habit_db("Python", "2026-09-01", db_path=self.db_path)
        kept_id = create_habit_db("Lectura", "2026-09-02", db_path=self.db_path)
        mark_completed_db(deleted_id, "2026-10-24", db_path=self.db_path)
        mark_completed_db(kept_id, "2026-10-24", db_path=self.db_path)
        mark_completed_db(kept_id, "2026-10-25", db_path=self.db_path)

        delete_habit_db(deleted_id, db_path=self.db_path)

        kept = get_habit_db(kept_id, db_path=self.db_path)
        assert kept is not None
        assert kept.name == "Lectura"
        assert get_completions_db(kept_id, db_path=self.db_path) == [
            "2026-10-24",
            "2026-10-25",
        ]
        assert [habit.id for habit in list_all_habits_db(db_path=self.db_path)] == [
            kept_id
        ]

    def test_delete_habit_db_raises_for_unknown_id(self):
        """RF-3.8: Un ID inexistente lanza ValueError sin cambios parciales."""
        kept_id = create_habit_db("Lectura", "2026-09-02", db_path=self.db_path)
        mark_completed_db(kept_id, "2026-10-24", db_path=self.db_path)

        with pytest.raises(ValueError, match="no existe"):
            delete_habit_db(999, db_path=self.db_path)

        assert get_habit_db(kept_id, db_path=self.db_path) is not None
        assert get_completions_db(kept_id, db_path=self.db_path) == ["2026-10-24"]


class TestMarkCompletedDb:
    """Tests para mark_completed_db() e is_completed_today_db() — Tarea 4.3, RF-2.1, RF-2.2."""

    def setup_method(self):
        """Crear una base de datos temporal para cada test."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_habits.db")
        init_db(self.db_path)

    def teardown_method(self):
        """Limpiar la base de datos temporal después de cada test."""
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_mark_completed_db_persists(self):
        """RF-2.1: Marcar un hábito persiste la fecha en la base de datos."""
        today = date.today().isoformat()
        habit_id = create_habit_db("Estudiar", today, db_path=self.db_path)

        mark_completed_db(habit_id, today, db_path=self.db_path)

        # Verificar que el registro existe en la tabla completions
        conn = sqlite3.connect(self.db_path)
        row = conn.execute(
            "SELECT completed_date FROM completions WHERE habit_id = ?",
            (habit_id,)
        ).fetchone()
        conn.close()

        assert row is not None
        assert row[0] == today

    def test_is_completed_today_db_true(self):
        """RF-2.2: is_completed_today_db retorna True si el hábito ya está marcado hoy."""
        today = date.today().isoformat()
        habit_id = create_habit_db("Estudiar", today, db_path=self.db_path)
        mark_completed_db(habit_id, today, db_path=self.db_path)

        result = is_completed_today_db(habit_id, today, db_path=self.db_path)

        assert result is True

    def test_is_completed_today_db_false(self):
        """RF-2.1: is_completed_today_db retorna False si el hábito no está marcado hoy."""
        today = date.today().isoformat()
        habit_id = create_habit_db("Estudiar", today, db_path=self.db_path)

        result = is_completed_today_db(habit_id, today, db_path=self.db_path)

        assert result is False

    def test_is_completed_today_db_different_date(self):
        """RF-2.1: is_completed_today_db retorna False para una fecha distinta."""
        today = date.today().isoformat()
        yesterday = (date.today() - __import__('datetime').timedelta(days=1)).isoformat()
        habit_id = create_habit_db("Estudiar", today, db_path=self.db_path)
        mark_completed_db(habit_id, today, db_path=self.db_path)

        result = is_completed_today_db(habit_id, yesterday, db_path=self.db_path)

        assert result is False

    def test_mark_completed_db_multiple_habits(self):
        """RF-2.1: Diferentes hábitos pueden marcarse el mismo día."""
        today = date.today().isoformat()
        habit_id_1 = create_habit_db("Estudiar", today, db_path=self.db_path)
        habit_id_2 = create_habit_db("Leer", today, db_path=self.db_path)

        mark_completed_db(habit_id_1, today, db_path=self.db_path)
        mark_completed_db(habit_id_2, today, db_path=self.db_path)

        assert is_completed_today_db(habit_id_1, today, db_path=self.db_path) is True
        assert is_completed_today_db(habit_id_2, today, db_path=self.db_path) is True


class TestRecoveredDaysDb:
    """Tests de días recuperados — Tarea 2.3.

    RF-2.8, RF-2.15, RF-2.16 y RF-2.17: marca días con `recovered = 1`,
    conserva los registros normales, falla sin dejar filas parciales si el
    hábito no existe, devuelve las fechas recuperadas ordenadas y borra los
    recuperados junto con el hábito.
    """

    def setup_method(self):
        """Crear una base de datos temporal para cada test."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_habits.db")
        init_db(self.db_path)

    def teardown_method(self):
        """Limpiar la base de datos temporal después de cada test."""
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_mark_recovered_days_db_persists_flagged_rows(self):
        """RF-2.8: las fechas se guardan con recovered = 1."""
        habit_id = create_habit_db(
            "Estudiar", "2026-10-20", db_path=self.db_path
        )

        mark_recovered_days_db(
            habit_id,
            ["2026-10-24", "2026-10-25"],
            self.db_path,
        )

        with closing(sqlite3.connect(self.db_path)) as conn:
            rows = conn.execute(
                "SELECT completed_date, recovered FROM completions "
                "WHERE habit_id = ? ORDER BY completed_date",
                (habit_id,),
            ).fetchall()

        assert rows == [("2026-10-24", 1), ("2026-10-25", 1)]
        assert get_recovered_dates_db(
            habit_id, self.db_path
        ) == ["2026-10-24", "2026-10-25"]
        assert get_completions_db(habit_id, self.db_path) == [
            "2026-10-24",
            "2026-10-25",
        ]

    def test_mark_recovered_days_db_keeps_existing_normal_record(self):
        """RF-2.17: un registro normal previo no se convierte en recuperado."""
        habit_id = create_habit_db(
            "Estudiar", "2026-10-20", db_path=self.db_path
        )
        mark_completed_db(habit_id, "2026-10-25", db_path=self.db_path)

        mark_recovered_days_db(
            habit_id,
            ["2026-10-24", "2026-10-25"],
            self.db_path,
        )

        with closing(sqlite3.connect(self.db_path)) as conn:
            rows = conn.execute(
                "SELECT completed_date, recovered FROM completions "
                "WHERE habit_id = ? ORDER BY completed_date",
                (habit_id,),
            ).fetchall()

        assert rows == [("2026-10-24", 1), ("2026-10-25", 0)]
        assert get_recovered_dates_db(
            habit_id, self.db_path
        ) == ["2026-10-24"]

    def test_mark_recovered_days_db_raises_for_unknown_habit(self):
        """RF-2.16: un hábito inexistente no deja filas parciales."""
        with pytest.raises(ValueError, match="El hábito no existe."):
            mark_recovered_days_db(
                999,
                ["2026-10-24", "2026-10-25"],
                self.db_path,
            )

        with closing(sqlite3.connect(self.db_path)) as conn:
            total = conn.execute(
                "SELECT COUNT(*) FROM completions"
            ).fetchone()[0]

        assert total == 0

    def test_get_recovered_dates_db_returns_only_recovered_sorted(self):
        """RF-2.8: solo devuelve las fechas recuperadas, ordenadas."""
        habit_id = create_habit_db(
            "Estudiar", "2026-10-20", db_path=self.db_path
        )
        mark_completed_db(habit_id, "2026-10-20", db_path=self.db_path)

        mark_recovered_days_db(
            habit_id,
            ["2026-10-25", "2026-10-23"],
            self.db_path,
        )

        assert get_recovered_dates_db(
            habit_id, self.db_path
        ) == ["2026-10-23", "2026-10-25"]

    def test_delete_habit_db_removes_recovered_days(self):
        """RF-2.15: el borrado no deja registros recuperados huérfanos."""
        habit_id = create_habit_db(
            "Estudiar", "2026-10-20", db_path=self.db_path
        )
        mark_recovered_days_db(
            habit_id,
            ["2026-10-24", "2026-10-25"],
            self.db_path,
        )

        delete_habit_db(habit_id, self.db_path)

        with closing(sqlite3.connect(self.db_path)) as conn:
            total = conn.execute(
                "SELECT COUNT(*) FROM completions WHERE habit_id = ?",
                (habit_id,),
            ).fetchone()[0]

        assert total == 0
        assert get_recovered_dates_db(
            habit_id, self.db_path
        ) == []


class TestListAllHabitsDb:
    """Tests para list_all_habits_db() y get_completions_db() — Tarea 4.4, RF-3."""

    def setup_method(self):
        """Crear una base de datos temporal para cada test."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_habits.db")
        init_db(self.db_path)

    def teardown_method(self):
        """Limpiar la base de datos temporal después de cada test."""
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_list_all_habits_empty(self):
        """RF-3.4: Sin hábitos, list_all_habits_db retorna lista vacía."""
        result = list_all_habits_db(db_path=self.db_path)

        assert result == []

    def test_list_all_habits_returns_all(self):
        """RF-3: list_all_habits_db retorna todos los hábitos creados."""
        today = date.today().isoformat()
        create_habit_db("Estudiar Python", today, db_path=self.db_path)
        create_habit_db("Leer 30 minutos", today, db_path=self.db_path)

        result = list_all_habits_db(db_path=self.db_path)

        assert len(result) == 2
        assert result[0].name == "Estudiar Python"
        assert result[1].name == "Leer 30 minutos"

    def test_list_all_habits_order(self):
        """RF-3: list_all_habits_db retorna los hábitos ordenados por ID."""
        today = date.today().isoformat()
        id_1 = create_habit_db("Zebra", today, db_path=self.db_path)
        id_2 = create_habit_db("Alpha", today, db_path=self.db_path)

        result = list_all_habits_db(db_path=self.db_path)

        assert len(result) == 2
        assert result[0].id == id_1
        assert result[1].id == id_2

    def test_list_all_habits_db_returns_icon(self):
        """RF-2.8: El listado incluye el icono de cada hábito."""
        today = date.today().isoformat()
        create_habit_db("Estudiar Python", today, icon="code", db_path=self.db_path)
        create_habit_db("Leer 30 minutos", today, icon="book", db_path=self.db_path)

        result = list_all_habits_db(db_path=self.db_path)

        assert [habit.icon for habit in result] == ["code", "book"]

    def test_get_completions_for_habit(self):
        """RF-1, RF-2.2 (T5.1): Obtener los registros de completado de un hábito específico."""
        import datetime
        today = date.today().isoformat()
        yesterday = (date.today() - datetime.timedelta(days=1)).isoformat()
        habit_id = create_habit_db("Estudiar", today, db_path=self.db_path)

        mark_completed_db(habit_id, today, db_path=self.db_path)
        mark_completed_db(habit_id, yesterday, db_path=self.db_path)

        result = get_completions_db(habit_id, db_path=self.db_path)

        assert len(result) == 2
        assert yesterday in result
        assert today in result

    def test_get_completions_db_empty(self):
        """RF-3: get_completions_db retorna lista vacía si no hay registros."""
        today = date.today().isoformat()
        habit_id = create_habit_db("Estudiar", today, db_path=self.db_path)

        result = get_completions_db(habit_id, db_path=self.db_path)

        assert result == []

    def test_get_completions_db_returns_dates(self):
        """RF-3: get_completions_db retorna las fechas de completado ordenadas."""
        today = date.today().isoformat()
        yesterday = (date.today() - __import__("datetime").timedelta(days=1)).isoformat()
        habit_id = create_habit_db("Estudiar", today, db_path=self.db_path)

        mark_completed_db(habit_id, today, db_path=self.db_path)
        mark_completed_db(habit_id, yesterday, db_path=self.db_path)

        result = get_completions_db(habit_id, db_path=self.db_path)

        assert len(result) == 2
        assert result[0] == yesterday
        assert result[1] == today

    def test_get_completions_db_nonexistent_habit(self):
        """RF-3: get_completions_db retorna lista vacía para un ID que no existe."""
        result = get_completions_db(999, db_path=self.db_path)

        assert result == []


class TestPersistenceIntegration:
    """Tests de integración para persistencia — Tarea 5.2, RF-3, RFN-3."""

    def setup_method(self):
        """Crear un directorio temporal para cada test."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_habits.db")

    def teardown_method(self):
        """Limpiar la base de datos temporal después de cada test."""
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_list_all_habits(self):
        """RF-3 (T5.2): list_all_habits_db retorna todos los hábitos creados."""
        init_db(self.db_path)
        today = date.today().isoformat()
        create_habit_db("Estudiar Python", today, db_path=self.db_path)
        create_habit_db("Leer 30 minutos", today, db_path=self.db_path)
        create_habit_db("Meditar", today, db_path=self.db_path)

        result = list_all_habits_db(db_path=self.db_path)

        assert len(result) == 3
        names = [h.name for h in result]
        assert "Estudiar Python" in names
        assert "Leer 30 minutos" in names
        assert "Meditar" in names

    def test_database_created_on_first_use(self):
        """RFN-3 (T5.2): init_db crea la base de datos y las tablas al primer uso."""
        assert not os.path.exists(self.db_path)

        init_db(self.db_path)

        assert os.path.exists(self.db_path)
        conn = sqlite3.connect(self.db_path)
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        assert "habits" in tables
        assert "completions" in tables
        conn.close()


class TestRemindersStorage:
    """Esquema y CRUD de recordatorios — Tarea 2.1, RF-1.2 a RF-1.8 y RF-3.4."""

    def setup_method(self):
        """Crear un directorio temporal para cada test."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_reminders.db")
        init_db(self.db_path)

    def teardown_method(self):
        """Limpiar la base de datos temporal después de cada test."""
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def _table_info(self, table: str) -> dict[str, tuple]:
        """Devolver las columnas de una tabla indexadas por nombre."""
        with closing(sqlite3.connect(self.db_path)) as conn:
            return {
                row[1]: row
                for row in conn.execute(f"PRAGMA table_info({table})").fetchall()
            }

    def test_init_db_creates_reminders_table(self):
        """RF-1.8: init_db crea la tabla `reminders` con el esquema del plan."""
        columns = self._table_info("reminders")

        assert set(columns) == {
            "habit_id",
            "enabled",
            "reminder_time",
            "effective_from",
            "last_notified_on",
        }
        assert columns["habit_id"][5] == 1
        assert columns["enabled"][3] == 1
        assert columns["enabled"][4] == "0"
        assert columns["effective_from"][3] == 1
        assert columns["reminder_time"][3] == 0
        assert columns["last_notified_on"][3] == 0

    def test_init_db_is_idempotent_and_keeps_existing_data(self):
        """RF-1.8: volver a inicializar no borra hábitos ni recordatorios."""
        habit_id = create_habit_db(
            "Leer", "2024-09-01", db_path=self.db_path
        )
        save_reminder_db(
            habit_id, True, "20:00", "2024-10-20", db_path=self.db_path
        )

        init_db(self.db_path)

        assert get_habit_db(habit_id, db_path=self.db_path) is not None
        reminder = get_reminder_db(habit_id, db_path=self.db_path)
        assert reminder is not None
        assert reminder.reminder_time == "20:00"

    def test_save_and_get_reminder_db(self):
        """RF-1.2, RF-1.7: guarda y recupera la configuración activa."""
        habit_id = create_habit_db(
            "Estudiar Python", "2024-09-15", db_path=self.db_path
        )

        save_reminder_db(
            habit_id, True, "20:00", "2024-10-24", db_path=self.db_path
        )
        reminder = get_reminder_db(habit_id, db_path=self.db_path)

        assert reminder is not None
        assert reminder.habit_id == habit_id
        assert reminder.enabled is True
        assert reminder.reminder_time == "20:00"
        assert reminder.effective_from == "2024-10-24"
        assert reminder.last_notified_on is None

    def test_save_reminder_db_updates_the_existing_row(self):
        """RF-1.4: cambiar la hora actualiza la misma fila sin duplicarla."""
        habit_id = create_habit_db(
            "Leer", "2024-09-01", db_path=self.db_path
        )
        save_reminder_db(
            habit_id, True, "20:00", "2024-10-20", db_path=self.db_path
        )

        save_reminder_db(
            habit_id, True, "21:30", "2024-10-24", db_path=self.db_path
        )
        reminder = get_reminder_db(habit_id, db_path=self.db_path)

        assert reminder is not None
        assert reminder.enabled is True
        assert reminder.reminder_time == "21:30"
        assert reminder.effective_from == "2024-10-24"
        with closing(sqlite3.connect(self.db_path)) as conn:
            count = conn.execute("SELECT COUNT(*) FROM reminders").fetchone()[0]
        assert count == 1

    def test_disabled_reminder_keeps_its_time(self):
        """RF-1.5: desactivar conserva la hora pero deja de estar activo."""
        habit_id = create_habit_db(
            "Leer", "2024-09-01", db_path=self.db_path
        )
        save_reminder_db(
            habit_id, True, "20:00", "2024-10-20", db_path=self.db_path
        )

        save_reminder_db(
            habit_id, False, "20:00", "2024-10-20", db_path=self.db_path
        )
        reminder = get_reminder_db(habit_id, db_path=self.db_path)

        assert reminder is not None
        assert reminder.enabled is False
        assert reminder.reminder_time == "20:00"

    def test_reminder_without_row_is_disabled(self):
        """RF-1.3, RF-1.8: un hábito sin fila equivale a desactivado."""
        habit_id = create_habit_db(
            "Leer", "2024-09-01", db_path=self.db_path
        )

        assert get_reminder_db(habit_id, db_path=self.db_path) is None

    def test_delete_habit_db_removes_its_reminder(self):
        """RF-3.4: al borrar el hábito desaparece su recordatorio."""
        habit_id = create_habit_db(
            "Leer", "2024-09-01", db_path=self.db_path
        )
        other_id = create_habit_db(
            "Python", "2024-09-15", db_path=self.db_path
        )
        save_reminder_db(
            habit_id, True, "20:00", "2024-10-20", db_path=self.db_path
        )
        save_reminder_db(
            other_id, True, "21:00", "2024-10-20", db_path=self.db_path
        )

        delete_habit_db(habit_id, db_path=self.db_path)

        assert get_reminder_db(habit_id, db_path=self.db_path) is None
        assert get_reminder_db(other_id, db_path=self.db_path) is not None

    def test_delete_habit_without_reminder_still_works(self):
        """RF-3.4: borrar un hábito sin configuración no falla."""
        habit_id = create_habit_db(
            "Leer", "2024-09-01", db_path=self.db_path
        )

        delete_habit_db(habit_id, db_path=self.db_path)

        assert get_habit_db(habit_id, db_path=self.db_path) is None


class TestReminderDeliveryStorage:
    """Consulta de vencidos y reclamación de entregas — Tarea 2.3.

    Cubre RF-2.1, RF-2.4, RF-2.5, RF-2.7, RF-2.9 y RFN-7.
    """

    NOW = datetime(2024, 10, 24, 10, 0)
    TODAY = "2024-10-24"

    def setup_method(self):
        """Crear un directorio temporal y una base nueva para cada test."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_reminders.db")
        init_db(self.db_path)

    def teardown_method(self):
        """Limpiar la base de datos temporal después de cada test."""
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def _create_habit(
        self, name: str = "Leer", start_date: str = "2024-09-01"
    ) -> int:
        """Crear un hábito y devolver su identificador."""
        return create_habit_db(name, start_date, db_path=self.db_path)

    def _save_reminder(
        self,
        habit_id: int,
        enabled: bool = True,
        reminder_time: str | None = "09:00",
        effective_from: str = "2024-10-24",
    ) -> None:
        """Guardar una configuración de recordatorio para el hábito."""
        save_reminder_db(
            habit_id,
            enabled,
            reminder_time,
            effective_from,
            db_path=self.db_path,
        )

    def _set_last_notified(self, habit_id: int, value: str | None) -> None:
        """Fijar directamente la fecha del último aviso para preparar el caso."""
        with closing(sqlite3.connect(self.db_path)) as conn:
            conn.execute(
                "UPDATE reminders SET last_notified_on = ? WHERE habit_id = ?",
                (value, habit_id),
            )
            conn.commit()

    def test_list_due_reminders_db_returns_pending_habit(self):
        """RF-2.1: devuelve el hábito activo cuya hora ya llegó."""
        habit_id = self._create_habit("Leer")
        self._save_reminder(habit_id)

        due = list_due_reminders_db(self.NOW, db_path=self.db_path)

        assert len(due) == 1
        assert due[0].habit_id == habit_id
        assert due[0].habit_name == "Leer"
        assert due[0].reminder_time == "09:00"

    def test_list_due_reminders_db_returns_only_pending_habits(self):
        """RF-2.1, RF-2.4: incluye los pendientes y omite el ya registrado."""
        pending_id = self._create_habit("Leer")
        completed_id = self._create_habit("Python", start_date="2024-09-15")
        other_id = self._create_habit("Meditar", start_date="2024-09-20")
        for habit_id in (pending_id, completed_id, other_id):
            self._save_reminder(habit_id)
        mark_completed_db(completed_id, self.TODAY, db_path=self.db_path)

        due = list_due_reminders_db(self.NOW, db_path=self.db_path)

        assert {item.habit_id for item in due} == {pending_id, other_id}
        assert {item.habit_name for item in due} == {"Leer", "Meditar"}

    @pytest.mark.parametrize(
        ("enabled", "reminder_time", "effective_from", "start_date",
         "last_notified_on", "completed_today"),
        [
            (False, "09:00", "2024-10-24", "2024-09-01", None, False),
            (True, "11:00", "2024-10-24", "2024-09-01", None, False),
            (True, "09:00", "2024-10-25", "2024-09-01", None, False),
            (True, "09:00", "2024-10-24", "2024-10-25", None, False),
            (True, "09:00", "2024-10-24", "2024-09-01", "2024-10-24", False),
            (True, "09:00", "2024-10-24", "2024-09-01", None, True),
            (True, None, "2024-10-24", "2024-09-01", None, False),
        ],
        ids=[
            "disabled",
            "before-time",
            "future-effective-date",
            "future-start-date",
            "already-notified-today",
            "completed-today",
            "without-time",
        ],
    )
    def test_list_due_reminders_db_excludes_non_due_habits(
        self,
        enabled,
        reminder_time,
        effective_from,
        start_date,
        last_notified_on,
        completed_today,
    ):
        """RF-2.1, RF-2.4, RF-2.5, RF-2.7, RF-2.9: nada fuera de regla vence."""
        habit_id = self._create_habit("Leer", start_date=start_date)
        self._save_reminder(
            habit_id,
            enabled=enabled,
            reminder_time=reminder_time,
            effective_from=effective_from,
        )
        if last_notified_on is not None:
            self._set_last_notified(habit_id, last_notified_on)
        if completed_today:
            mark_completed_db(habit_id, self.TODAY, db_path=self.db_path)

        assert list_due_reminders_db(self.NOW, db_path=self.db_path) == []

    def test_list_due_reminders_db_keeps_overdue_reminder_same_day(self):
        """RF-2.10: una hora pasada sigue vencida durante el mismo día."""
        habit_id = self._create_habit("Leer")
        self._save_reminder(habit_id, reminder_time="07:00")

        due = list_due_reminders_db(self.NOW, db_path=self.db_path)

        assert [item.habit_id for item in due] == [habit_id]

    def test_list_due_reminders_db_is_empty_without_reminders(self):
        """RFN-7: sin recordatorios activos no hay nada que entregar."""
        self._create_habit("Leer")

        assert list_due_reminders_db(self.NOW, db_path=self.db_path) == []

    def test_claim_and_release_reminder_delivery(self):
        """RF-2.7, RFN-7: reclamar evita duplicados y liberar permite reintentar."""
        habit_id = self._create_habit("Leer")
        self._save_reminder(habit_id)

        assert claim_reminder_delivery_db(
            habit_id, self.TODAY, db_path=self.db_path
        ) is True
        reminder = get_reminder_db(habit_id, db_path=self.db_path)
        assert reminder is not None
        assert reminder.last_notified_on == self.TODAY
        assert list_due_reminders_db(self.NOW, db_path=self.db_path) == []

        assert claim_reminder_delivery_db(
            habit_id, self.TODAY, db_path=self.db_path
        ) is False

        release_reminder_delivery_db(
            habit_id, self.TODAY, db_path=self.db_path
        )
        reminder = get_reminder_db(habit_id, db_path=self.db_path)
        assert reminder is not None
        assert reminder.last_notified_on is None
        assert len(list_due_reminders_db(self.NOW, db_path=self.db_path)) == 1

    def test_claim_reminder_delivery_db_succeeds_after_previous_day(self):
        """RF-2.7: el aviso de ayer no impide reclamar el de hoy."""
        habit_id = self._create_habit("Leer")
        self._save_reminder(habit_id)
        self._set_last_notified(habit_id, "2024-10-23")

        assert claim_reminder_delivery_db(
            habit_id, self.TODAY, db_path=self.db_path
        ) is True
        reminder = get_reminder_db(habit_id, db_path=self.db_path)
        assert reminder is not None
        assert reminder.last_notified_on == self.TODAY

    def test_claim_reminder_delivery_db_returns_false_without_row(self):
        """RFN-7: reclamar un hábito sin recordatorio no crea una fila."""
        habit_id = self._create_habit("Leer")

        assert claim_reminder_delivery_db(
            habit_id, self.TODAY, db_path=self.db_path
        ) is False
        assert get_reminder_db(habit_id, db_path=self.db_path) is None

    def test_release_reminder_delivery_db_keeps_previous_day_notice(self):
        """RF-2.7: liberar solo suelta la reclamación del día actual."""
        habit_id = self._create_habit("Leer")
        self._save_reminder(habit_id)
        self._set_last_notified(habit_id, "2024-10-23")

        release_reminder_delivery_db(
            habit_id, self.TODAY, db_path=self.db_path
        )

        reminder = get_reminder_db(habit_id, db_path=self.db_path)
        assert reminder is not None
        assert reminder.last_notified_on == "2024-10-23"
