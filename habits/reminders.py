# spec: 005-local-reminders
"""Lógica pura de recordatorios locales por hábito.

Valida la hora configurada, genera la etiqueta visible y el texto de la
notificación, y calcula la primera fecha desde la que puede avisar un
recordatorio. No importa Flet ni accede a SQLite (Constitución, principio 3).

Cubre RF-1.1, RF-1.2, RF-1.6, RF-2.2, RF-3.1 y RF-3.6.
"""

import re
from datetime import date, datetime, timedelta

DISABLED_LABEL = "Sin recordatorio"
ACTIVE_LABEL_TEMPLATE = "Recordatorio a las {time}"
MESSAGE_TEMPLATE = "⏰ No olvides registrar «{name}» hoy."

_TIME_PATTERN = re.compile(r"^(\d{2}):(\d{2})$")


def validate_reminder_time(value: str) -> str | None:
    """Validar una hora local en formato HH:MM.

    Args:
        value: Texto introducido por el usuario.

    Returns:
        La hora normalizada ``HH:MM`` si está entre 00:00 y 23:59, o ``None``
        si está vacía, incompleta o fuera de rango.
    """
    candidate = value.strip()
    match = _TIME_PATTERN.match(candidate)
    if match is None:
        return None

    hours, minutes = int(match.group(1)), int(match.group(2))
    if hours > 23 or minutes > 59:
        return None

    return f"{hours:02d}:{minutes:02d}"


def reminder_label(enabled: bool, reminder_time: str | None) -> str:
    """Generar la etiqueta visible del estado del recordatorio.

    Args:
        enabled: Indica si el recordatorio está activo.
        reminder_time: Hora guardada en formato HH:MM, si existe.

    Returns:
        “Sin recordatorio” cuando está desactivado o no tiene hora válida, o
        “Recordatorio a las HH:MM” cuando está activo.
    """
    if not enabled or reminder_time is None:
        return DISABLED_LABEL

    valid_time = validate_reminder_time(reminder_time)
    if valid_time is None:
        return DISABLED_LABEL

    return ACTIVE_LABEL_TEMPLATE.format(time=valid_time)


def effective_date(now: datetime, reminder_time: str) -> date:
    """Calcular la primera fecha desde la que puede avisar un recordatorio.

    Si la hora elegida todavía no ha llegado, el aviso puede producirse hoy;
    si ya pasó (o es la hora actual), el primer aviso será al día siguiente
    para no enviar avisos inmediatos ni retroactivos (RF-3.1 y RF-3.6).

    Args:
        now: Fecha y hora locales actuales.
        reminder_time: Hora elegida en formato HH:MM.

    Returns:
        La fecha local del primer aviso posible.

    Raises:
        ValueError: Si ``reminder_time`` no es una hora HH:MM válida.
    """
    valid_time = validate_reminder_time(reminder_time)
    if valid_time is None:
        raise ValueError(f"Hora de recordatorio inválida: {reminder_time!r}")

    today = now.date()
    if valid_time <= now.strftime("%H:%M"):
        return today + timedelta(days=1)

    return today


def reminder_message(habit_name: str) -> str:
    """Generar el texto de la notificación del recordatorio.

    Args:
        habit_name: Nombre visible del hábito pendiente.

    Returns:
        Texto en español que incluye el nombre del hábito.
    """
    return MESSAGE_TEMPLATE.format(name=habit_name)


def is_due(
    now: datetime,
    *,
    enabled: bool,
    reminder_time: str | None,
    effective_from: date,
    start_date: date,
    last_notified_on: date | None = None,
    completed_today: bool = False,
) -> bool:
    """Decidir si un recordatorio debe avisar en el instante indicado.

    Un recordatorio vence cuando está activo, tiene una hora válida ya
    alcanzada, su vigencia y la fecha de inicio del hábito ya comenzaron, el
    hábito sigue pendiente y no se avisó ese mismo día. Una hora pasada sigue
    vencida durante el resto del día local, pero nunca se avisa de un día
    anterior ni se repite el aviso.

    Args:
        now: Fecha y hora locales actuales.
        enabled: Indica si el recordatorio está activo.
        reminder_time: Hora configurada en formato HH:MM, si existe.
        effective_from: Fecha desde la que el recordatorio puede avisar.
        start_date: Fecha de inicio del hábito.
        last_notified_on: Fecha del último aviso entregado, si lo hubo.
        completed_today: Indica si el hábito ya se registró hoy.

    Returns:
        True si corresponde mostrar la notificación; False en caso contrario.
    """
    if not enabled or completed_today:
        return False

    valid_time = (
        validate_reminder_time(reminder_time) if reminder_time is not None else None
    )
    if valid_time is None:
        return False

    today = now.date()
    if effective_from > today:
        return False
    if start_date > today:
        return False
    if last_notified_on == today:
        return False
    if valid_time > now.strftime("%H:%M"):
        return False

    return True

