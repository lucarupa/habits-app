"""Genera datos de demostración para ver la aplicación con contenido.

Crea un hábito por cada icono disponible y registros de las dos últimas
semanas, con rachas y patrones distintos para que la barra lateral, las
tarjetas de estadísticas y el heatmap muestren variedad.

Antes de reemplazar los datos existentes guarda una copia de la base de datos
junto al original: `data/habits.before-seed-AAAAMMDD-HHMMSS.db`.

Uso:
    .venv\\Scripts\\python.exe scripts/seed_demo_data.py
    .venv\\Scripts\\python.exe scripts/seed_demo_data.py --today 2026-10-26
"""

from __future__ import annotations

import argparse
import shutil
import sqlite3
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from habits.domain.models import ALLOWED_ICONS  # noqa: E402
from habits.domain.recovery import get_habit_stats  # noqa: E402
from habits.persistence.completions_repo import mark_completed_db  # noqa: E402
from habits.persistence.habits_repo import (  # noqa: E402
    create_habit_db,
    list_all_habits_db,
)
from habits.persistence.schema import init_db  # noqa: E402

DEFAULT_DB_PATH = "data/habits.db"
DEMO_DAYS = 14

# (nombre, icono, fecha de inicio relativa en días, offsets de días completados)
# El offset 0 es hoy y el 13 es hace trece días. Cada offset es un día
# completado; los huecos generan rachas distintas.
DEMO_HABITS: tuple[tuple[str, str, int, tuple[int, ...]], ...] = (
    ("Practicar Python", "code", 67, tuple(range(14))),
    ("Entrenar", "fitness", 44, (0, 1, 2, 3, 4, 7, 8)),
    ("Leer 30 minutos", "book", 55, (0, 1, 2, 3, 5, 6, 8, 9, 10, 12, 13)),
    ("Practicar guitarra", "music", 34, (0, 1, 4, 8)),
    ("Repasar anatomía", "science", 41, (0, 2, 3, 6, 9, 12)),
    ("Dibujar", "art", 12, (0, 5, 11)),
    ("Estudiar inglés", "language", 51, (1, 2, 4, 7, 10, 13)),
    ("Resolver problemas", "math", 25, (2, 4, 6, 8, 10, 12)),
)


def backup_database(db_path: Path) -> Path | None:
    """Copiar la base de datos actual antes de reemplazarla.

    Args:
        db_path: Ruta de la base de datos existente.

    Returns:
        La ruta de la copia creada, o None si no había nada que copiar.
    """
    if not db_path.exists():
        return None

    conn = sqlite3.connect(db_path)
    try:
        has_rows = conn.execute("SELECT COUNT(*) FROM habits").fetchone()[0] > 0
    except sqlite3.OperationalError:
        has_rows = False
    finally:
        conn.close()

    if not has_rows:
        return None

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_path = db_path.with_name(f"{db_path.stem}.before-seed-{stamp}.db")
    shutil.copy2(db_path, backup_path)
    return backup_path


def clear_database(db_path: Path) -> None:
    """Vaciar hábitos y registros, reiniciando los identificadores.

    Args:
        db_path: Ruta de la base de datos a vaciar.
    """
    conn = sqlite3.connect(db_path)
    try:
        with conn:
            conn.execute("DELETE FROM completions")
            conn.execute("DELETE FROM habits")
            conn.execute(
                "DELETE FROM sqlite_sequence WHERE name IN ('habits', 'completions')"
            )
    finally:
        conn.close()


def seed(db_path: Path, today: date) -> None:
    """Insertar los hábitos y registros de demostración.

    Args:
        db_path: Ruta de la base de datos destino.
        today: Fecha que se considera hoy al generar los registros.
    """
    init_db(str(db_path))
    clear_database(db_path)

    for name, icon, start_days_ago, offsets in DEMO_HABITS:
        if icon not in ALLOWED_ICONS:
            raise ValueError(f"Icono no permitido: {icon}")

        start_date = today - timedelta(days=start_days_ago)
        habit_id = create_habit_db(
            name,
            start_date.isoformat(),
            icon=icon,
            db_path=str(db_path),
        )

        for offset in offsets:
            mark_completed_db(
                habit_id,
                (today - timedelta(days=offset)).isoformat(),
                db_path=str(db_path),
            )


def print_summary(db_path: Path, today: date) -> None:
    """Mostrar un resumen de los datos generados.

    Args:
        db_path: Ruta de la base de datos sembrada.
        today: Fecha usada como hoy.
    """
    conn = sqlite3.connect(db_path)
    try:
        rows = list_all_habits_db(str(db_path))
        print(f"Hábitos: {len(rows)} | Ventana: {DEMO_DAYS} días hasta {today:%d/%m/%Y}")
        print()
        print(f"{'ID':<4}{'Icono':<11}{'Hábito':<24}{'Racha':>6}{'Mejor':>7}{'Días':>6}")
        for row in rows:
            dates = conn.execute(
                "SELECT completed_date FROM completions WHERE habit_id = ?",
                (row.id,),
            ).fetchall()
            completed = {date.fromisoformat(value[0]) for value in dates}
            stats = get_habit_stats(completed, today)
            print(
                f"{row.id:<4}{row.icon:<11}{row.name:<24}"
                f"{stats.current_streak:>6}{stats.best_streak:>7}"
                f"{stats.registered_days:>6}"
            )
        total = conn.execute("SELECT COUNT(*) FROM completions").fetchone()[0]
        print()
        print(f"Registros totales: {total}")
    finally:
        conn.close()


def main() -> None:
    """Punto de entrada del generador de datos de demostración."""
    parser = argparse.ArgumentParser(description="Rellena la base con datos de demo.")
    parser.add_argument("--db", default=DEFAULT_DB_PATH, help="Ruta de la base SQLite.")
    parser.add_argument(
        "--today",
        default=date.today().isoformat(),
        help="Fecha actual en formato YYYY-MM-DD (por defecto, hoy).",
    )
    args = parser.parse_args()

    db_path = (ROOT / args.db).resolve() if not Path(args.db).is_absolute() else Path(args.db)
    today = date.fromisoformat(args.today)

    backup_path = backup_database(db_path)
    if backup_path is not None:
        print(f"Copia de seguridad: {backup_path}")

    seed(db_path, today)
    print_summary(db_path, today)


if __name__ == "__main__":
    main()
