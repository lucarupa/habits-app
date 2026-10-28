# spec: 006-code-organization
"""Verificación de la conservación del comportamiento y los datos — Tarea 9.2.

Comprueba con las APIs públicas que una base existente conserva hábitos,
registros, días recuperados, rachas, estadísticas, heatmap y recordatorios;
que creación, edición, borrado, registro, aviso de duplicado y recuperación de
racha siguen funcionando igual; y que no cambian las dependencias ni el
esquema (RF-5.2, RF-5.3, RF-5.4 y RF-5.6).
"""

import sqlite3
from datetime import date, timedelta
from pathlib import Path

from habits.domain.heatmap import build_activity_heatmap
from habits.domain.models import Habit, HabitStats
from habits.domain.recovery import find_recoverable_gap, get_habit_stats
from habits.forms.models import HabitFormData
from habits.forms.service import create_habit_from_form, update_habit_from_form
from habits.persistence.completions_repo import (
    get_completions_db,
    get_recovered_dates_db,
    mark_completed_db,
    mark_recovered_days_db,
)
from habits.persistence.habits_repo import (
    create_habit_db,
    delete_habit_db,
    get_habit_db,
    list_all_habits_db,
)
from habits.persistence.reminders_repo import save_reminder_db
from habits.persistence.schema import init_db
from habits.registration import (
    REGISTRATION_DUPLICATE_MESSAGE,
    REGISTRATION_SUCCESS_MESSAGE,
    duplicate_warning,
    register_today,
)
from habits.state.loader import load_app_state

ROOT = Path(__file__).resolve().parents[1]
APPROVED_DEPENDENCIES = {"flet", "pytest", "pytest-cov"}


def days_ago(today: date, days: int) -> date:
    """Devolver una fecha anterior a la fecha de referencia."""
    return today - timedelta(days=days)


def dependency_name(requirement: str) -> str:
    """Extraer el nombre de un requisito sin versión ni extras."""
    name = requirement.split(";")[0]
    for separator in ("==", ">=", "<=", "~=", "!=", ">", "<", "["):
        name = name.split(separator)[0]
    return name.strip().lower()


def test_existing_database_preserves_habits_records_recovered_and_reminders(
    tmp_path,
):
    """RF-5.2, RF-5.3: una base existente conserva datos, estadísticas y avisos."""
    db_path = str(tmp_path / "habits.db")
    init_db(db_path)
    today = date.today()
    reading_id = create_habit_db(
        "Leer",
        days_ago(today, 30).isoformat(),
        "book",
        db_path,
    )
    python_id = create_habit_db(
        "Python",
        days_ago(today, 20).isoformat(),
        "code",
        db_path,
    )

    mark_completed_db(reading_id, today.isoformat(), db_path)
    mark_completed_db(reading_id, days_ago(today, 1).isoformat(), db_path)
    mark_recovered_days_db(
        reading_id,
        [days_ago(today, 2).isoformat()],
        db_path,
    )
    mark_completed_db(python_id, today.isoformat(), db_path)
    save_reminder_db(
        reading_id,
        True,
        "09:30",
        today.isoformat(),
        db_path,
    )

    # Volver a inicializar la base no debe borrar ni duplicar datos.
    init_db(db_path)

    state = load_app_state(db_path, today)

    assert [item.habit.name for item in state.habits] == ["Leer", "Python"]
    assert state.selected_id == reading_id
    selected = state.selected
    assert selected is not None
    assert selected.stats == HabitStats(
        current_streak=3,
        best_streak=3,
        registered_days=2,
    )
    assert selected.completed_dates == {
        today,
        days_ago(today, 1),
        days_ago(today, 2),
    }
    assert selected.recovered_dates == {days_ago(today, 2)}
    assert selected.reminder_enabled is True
    assert selected.reminder_time == "09:30"
    assert state.reminder_label == "Recordatorio a las 09:30"
    assert [card.value for card in state.stat_cards()] == [3, 3, 2]

    cells = state.heatmap_cells()
    assert len(cells) == 35
    by_date = {cell.date: cell for cell in cells}
    assert by_date[days_ago(today, 2)].completed is True
    assert by_date[days_ago(today, 2)].recovered is True
    assert by_date[today].is_today is True

    assert get_habit_db(reading_id, db_path).name == "Leer"
    assert get_completions_db(reading_id, db_path) == sorted(
        [
            today.isoformat(),
            days_ago(today, 1).isoformat(),
            days_ago(today, 2).isoformat(),
        ]
    )
    assert get_recovered_dates_db(reading_id, db_path) == [
        days_ago(today, 2).isoformat()
    ]
    assert [row.name for row in list_all_habits_db(db_path)] == [
        "Leer",
        "Python",
    ]


def test_create_and_edit_preserve_identity_texts_and_records(tmp_path):
    """RF-5.3, RF-5.4: crear y editar conservan ID, textos y registros."""
    db_path = str(tmp_path / "habits.db")
    init_db(db_path)
    today = date.today()
    start_date = days_ago(today, 30)

    created = create_habit_from_form(
        HabitFormData(
            name="  Leer  ",
            start_date=start_date.strftime("%d/%m/%Y"),
            icon="book",
        ),
        db_path,
        today,
    )

    assert created.name == "Leer"
    assert created.start_date == start_date
    assert created.icon == "book"

    mark_completed_db(created.habit_id, today.isoformat(), db_path)
    habit = Habit(
        id=created.habit_id,
        name=created.name,
        start_date=created.start_date,
        icon=created.icon,
    )
    new_start_date = days_ago(today, 20)

    updated = update_habit_from_form(
        habit,
        HabitFormData(
            name="Leer más",
            start_date=new_start_date.strftime("%d/%m/%Y"),
            icon="code",
        ),
        db_path,
        today,
    )

    assert updated.habit_id == created.habit_id
    assert updated.name == "Leer más"
    assert updated.start_date == new_start_date
    assert updated.icon == "code"

    row = get_habit_db(created.habit_id, db_path)
    assert row is not None
    assert row.name == "Leer más"
    assert row.start_date == new_start_date.isoformat()
    assert row.icon == "code"
    assert get_completions_db(created.habit_id, db_path) == [
        today.isoformat()
    ]


def test_delete_preserves_other_habits_and_removes_associated_data(tmp_path):
    """RF-5.2, RF-5.4: borrar un hábito no afecta a los demás ni deja huérfanos."""
    db_path = str(tmp_path / "habits.db")
    init_db(db_path)
    today = date.today()
    kept_id = create_habit_db(
        "Leer",
        days_ago(today, 30).isoformat(),
        "book",
        db_path,
    )
    doomed_id = create_habit_db(
        "Temporal",
        days_ago(today, 10).isoformat(),
        "code",
        db_path,
    )

    mark_completed_db(kept_id, today.isoformat(), db_path)
    mark_completed_db(doomed_id, today.isoformat(), db_path)
    mark_recovered_days_db(
        doomed_id,
        [days_ago(today, 1).isoformat()],
        db_path,
    )
    save_reminder_db(
        doomed_id,
        True,
        "08:00",
        today.isoformat(),
        db_path,
    )

    delete_habit_db(doomed_id, db_path)

    assert get_habit_db(doomed_id, db_path) is None
    assert get_completions_db(doomed_id, db_path) == []
    assert get_recovered_dates_db(doomed_id, db_path) == []
    assert get_habit_db(kept_id, db_path).name == "Leer"
    assert get_completions_db(kept_id, db_path) == [today.isoformat()]

    with sqlite3.connect(db_path) as conn:
        reminder_count = conn.execute(
            "SELECT COUNT(*) FROM reminders WHERE habit_id = ?",
            (doomed_id,),
        ).fetchone()[0]

    assert reminder_count == 0


def test_registration_duplicate_warning_and_recovery_preserve_behavior(
    tmp_path,
):
    """RF-5.3, RF-5.4: registro, aviso de duplicado y recuperación no cambian."""
    db_path = str(tmp_path / "habits.db")
    init_db(db_path)
    today = date.today()
    habit_id = create_habit_db(
        "Leer",
        days_ago(today, 30).isoformat(),
        "book",
        db_path,
    )

    first = register_today(habit_id, today, db_path)
    assert first.success is True
    assert first.message == REGISTRATION_SUCCESS_MESSAGE

    second = register_today(habit_id, today, db_path)
    assert second.success is False
    assert second.message == REGISTRATION_DUPLICATE_MESSAGE
    assert get_completions_db(habit_id, db_path) == [today.isoformat()]
    assert duplicate_warning("Leer") == "⚠️ «Leer» ya está registrado hoy."

    recovery_id = create_habit_db(
        "Python",
        days_ago(today, 20).isoformat(),
        "code",
        db_path,
    )
    mark_completed_db(recovery_id, today.isoformat(), db_path)
    mark_completed_db(
        recovery_id,
        days_ago(today, 3).isoformat(),
        db_path,
    )

    gap = find_recoverable_gap(
        {today, days_ago(today, 3)},
        today,
    )
    assert gap is not None
    assert gap.dates == (days_ago(today, 2), days_ago(today, 1))

    mark_recovered_days_db(
        recovery_id,
        [value.isoformat() for value in gap.dates],
        db_path,
    )

    stats = get_habit_stats(
        {
            today,
            days_ago(today, 3),
            days_ago(today, 2),
            days_ago(today, 1),
        },
        today,
        {days_ago(today, 2), days_ago(today, 1)},
    )
    assert stats == HabitStats(
        current_streak=4,
        best_streak=4,
        registered_days=2,
    )
    assert get_recovered_dates_db(recovery_id, db_path) == [
        days_ago(today, 2).isoformat(),
        days_ago(today, 1).isoformat(),
    ]

    with sqlite3.connect(db_path) as conn:
        normal = conn.execute(
            "SELECT recovered FROM completions "
            "WHERE habit_id = ? AND completed_date = ?",
            (recovery_id, days_ago(today, 3).isoformat()),
        ).fetchone()
        recovered = conn.execute(
            "SELECT recovered FROM completions "
            "WHERE habit_id = ? AND completed_date = ?",
            (recovery_id, days_ago(today, 1).isoformat()),
        ).fetchone()

    assert normal == (0,)
    assert recovered == (1,)

    cells = {
        cell.date: cell
        for cell in build_activity_heatmap(
            {
                today,
                days_ago(today, 3),
                days_ago(today, 2),
                days_ago(today, 1),
            },
            today,
            {days_ago(today, 2), days_ago(today, 1)},
        )
    }
    assert cells[days_ago(today, 1)].completed is True
    assert cells[days_ago(today, 1)].recovered is True
    assert cells[days_ago(today, 3)].recovered is False


def test_schema_and_dependencies_are_unchanged(tmp_path):
    """RF-5.6: no se añaden tablas, columnas ni dependencias externas."""
    db_path = str(tmp_path / "habits.db")
    init_db(db_path)

    with sqlite3.connect(db_path) as conn:
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
            if not row[0].startswith("sqlite_")
        }
        columns = {
            table: [
                row[1]
                for row in conn.execute(f"PRAGMA table_info({table})")
            ]
            for table in tables
        }

    assert tables == {"habits", "completions", "reminders"}
    assert columns == {
        "habits": ["id", "name", "start_date", "icon"],
        "completions": [
            "id",
            "habit_id",
            "completed_date",
            "recovered",
        ],
        "reminders": [
            "habit_id",
            "enabled",
            "reminder_time",
            "effective_from",
            "last_notified_on",
        ],
    }

    requirements = {
        dependency_name(line)
        for line in (ROOT / "requirements.txt")
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip() and not line.strip().startswith("#")
    }
    assert requirements == APPROVED_DEPENDENCIES
