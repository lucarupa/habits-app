# spec: 005-local-reminders
"""Ejecución periódica de los recordatorios.

Punto de entrada que el planificador del sistema lanza cada minuto. Usa la hora
local, entrega los recordatorios vencidos de la base de datos indicada y
devuelve un código de salida controlado (RF-2.1, RF-2.3 y RF-2.10).
"""

import argparse
import sys
from collections.abc import Sequence
from datetime import datetime

from habits.notifications.notifier import SystemNotifier
from habits.reminder_service import (
    DeliverySummary,
    Notifier,
    deliver_due_reminders,
)

DEFAULT_DB_PATH = "data/habits.db"
SENT_MESSAGE = "Recordatorios enviados: {count}"
RUNNER_FAILURE_MESSAGE = "No se pudieron comprobar los recordatorios: {error}"


def run_check(
    db_path: str,
    now: datetime | None = None,
    notifier: Notifier | None = None,
) -> DeliverySummary:
    """Comprobar y entregar los recordatorios vencidos.

    Args:
        db_path: Ruta al archivo de base de datos SQLite.
        now: Fecha y hora locales; por defecto, el instante actual.
        notifier: Notificador a usar; por defecto, `SystemNotifier`.

    Returns:
        El resumen de envíos y errores del servicio de entrega.
    """
    return deliver_due_reminders(
        now if now is not None else datetime.now(),
        db_path,
        notifier if notifier is not None else SystemNotifier(),
    )


def build_parser() -> argparse.ArgumentParser:
    """Construir el analizador de argumentos del runner."""
    parser = argparse.ArgumentParser(
        prog="habits.reminder_runner",
        description="Comprueba y envía los recordatorios pendientes.",
    )
    parser.add_argument(
        "--db",
        default=DEFAULT_DB_PATH,
        help=(
            "Ruta de la base de datos SQLite "
            f"(por defecto: {DEFAULT_DB_PATH})."
        ),
    )
    return parser


def main(
    argv: Sequence[str] | None = None,
    *,
    now: datetime | None = None,
    notifier: Notifier | None = None,
) -> int:
    """Ejecutar una comprobación de recordatorios desde la línea de comandos.

    Args:
        argv: Argumentos de la línea de comandos; por defecto, `sys.argv`.
        now: Fecha y hora locales; por defecto, el instante actual.
        notifier: Notificador a usar; por defecto, `SystemNotifier`.

    Returns:
        0 si no hubo errores; 1 si algún envío falló o la comprobación no pudo
        completarse (RF-2.3 y RF-2.10).
    """
    args = build_parser().parse_args(argv)

    try:
        summary = run_check(args.db, now=now, notifier=notifier)
    except Exception as error:  # noqa: BLE001 - el runner nunca debe romperse
        print(RUNNER_FAILURE_MESSAGE.format(error=error), file=sys.stderr)
        return 1

    print(SENT_MESSAGE.format(count=len(summary.sent)))
    for message in summary.errors:
        print(message, file=sys.stderr)
    return 1 if summary.errors else 0


if __name__ == "__main__":
    sys.exit(main())
