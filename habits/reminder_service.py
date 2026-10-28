# spec: 005-local-reminders
"""Servicio de entrega de recordatorios.

Recoge los recordatorios vencidos, reclama la entrega de cada uno, envía la
notificación con el nombre actual del hábito y libera la reclamación si el
envío falla. No importa Flet ni accede a widgets (RF-2.1, RF-2.4, RF-2.6,
RF-2.7, RF-2.8, RF-3.2, RF-3.3, RF-4.5 y RFN-7).
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol

from habits.notifications import NotificationResult
from habits.reminders import reminder_message
from habits.persistence.reminders_repo import (
    claim_reminder_delivery_db,
    list_due_reminders_db,
    release_reminder_delivery_db,
)

GENERIC_DELIVERY_ERROR = (
    "No se pudo enviar la notificación del recordatorio."
)


class Notifier(Protocol):
    """Interfaz mínima que debe cumplir un notificador inyectable."""

    def notify(self, message: str) -> NotificationResult:
        """Mostrar una notificación y devolver su resultado."""
        ...


@dataclass(frozen=True)
class DeliverySummary:
    """Resumen de una comprobación de recordatorios.

    Atributos:
        sent: Identificadores de los hábitos cuyo aviso se entregó.
        errors: Mensajes en español de los envíos que fallaron.
    """

    sent: list[int] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def deliver_due_reminders(
    now: datetime,
    db_path: str,
    notifier: Notifier,
) -> DeliverySummary:
    """Entregar los recordatorios vencidos en el instante indicado.

    Para cada recordatorio vencido se reclama la entrega de forma atómica; si
    otro proceso ya la reclamó, se omite. Cuando el envío falla se libera la
    reclamación para reintentar en la siguiente comprobación y se registra el
    error, sin marcar el hábito como registrado ni alterar sus estadísticas.

    Args:
        now: Fecha y hora locales actuales.
        db_path: Ruta al archivo de base de datos SQLite.
        notifier: Notificador que entrega el texto del aviso.

    Returns:
        Un DeliverySummary con los hábitos avisados y los errores producidos.
    """
    today = now.date().isoformat()
    summary = DeliverySummary()

    for reminder in list_due_reminders_db(now, db_path):
        if not claim_reminder_delivery_db(
            reminder.habit_id, today, db_path
        ):
            continue

        result = notifier.notify(reminder_message(reminder.habit_name))
        if result.ok:
            summary.sent.append(reminder.habit_id)
            continue

        release_reminder_delivery_db(reminder.habit_id, today, db_path)
        summary.errors.append(result.message or GENERIC_DELIVERY_ERROR)

    return summary