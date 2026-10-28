# spec: 002-ui-redesign
# spec: 003-edit-delete-habits
# spec: 006-code-organization
"""Validación de fechas, nombre e icono del formulario de hábitos.

Conserva las reglas y los mensajes del módulo monolítico anterior. No importa
Flet ni SQLite (RF-2.2, RF-2.3 y RF-5.3).
"""

import re
from datetime import date

from habits.domain.models import ALLOWED_ICONS, DEFAULT_ICON, Habit
from habits.forms.models import (
    DATE_FORMAT_ERROR,
    DATE_FUTURE_ERROR,
    MAX_NAME_LENGTH,
    NAME_REQUIRED_ERROR,
    NAME_TOO_LONG_ERROR,
    HabitFormData,
    HabitFormResult,
)

_DATE_PATTERN = re.compile(r"^(\d{2})/(\d{2})/(\d{4})$")


def normalize_icon(icon: str | None) -> str:
    """Devolver un icono válido, usando el valor por defecto si hace falta.

    Args:
        icon: Clave semántica elegida, posiblemente vacía o inválida.

    Returns:
        La misma clave si pertenece al catálogo, o `DEFAULT_ICON` (RF-2.6).
    """
    if icon in ALLOWED_ICONS:
        return icon
    return DEFAULT_ICON


def parse_start_date(value: str, today: date | None = None) -> date:
    """Interpretar la fecha opcional del formulario.

    Args:
        value: Fecha en formato dd/mm/aaaa. Si está vacía, se usa hoy.
        today: Fecha actual; si se omite, se usa `date.today()`.

    Returns:
        La fecha indicada, o la fecha actual si el campo está vacío o la
        fecha es futura (RF-2.4, RF-2.5).

    Raises:
        ValueError: Si el texto no es una fecha real en dd/mm/aaaa (RF-2.10).
    """
    current_day = today or date.today()
    text = (value or "").strip()
    if not text:
        return current_day

    match = _DATE_PATTERN.match(text)
    if match is None:
        raise ValueError(DATE_FORMAT_ERROR)

    day, month, year = (int(part) for part in match.groups())
    try:
        parsed = date(year, month, day)
    except ValueError:
        raise ValueError(DATE_FORMAT_ERROR) from None

    if parsed > current_day:
        return current_day
    return parsed


def _parse_strict_date(value: str) -> date:
    """Interpretar una fecha dd/mm/aaaa sin normalizarla.

    A diferencia de `parse_start_date`, una fecha futura no se corrige a hoy:
    la edición la rechaza para no guardar datos incoherentes (RF-2.7).

    Args:
        value: Fecha escrita en formato dd/mm/aaaa.

    Returns:
        La fecha indicada, tal cual.

    Raises:
        ValueError: Si el texto no es una fecha real en dd/mm/aaaa.
    """
    text = (value or "").strip()
    match = _DATE_PATTERN.match(text)
    if match is None:
        raise ValueError(DATE_FORMAT_ERROR)

    day, month, year = (int(part) for part in match.groups())
    try:
        return date(year, month, day)
    except ValueError:
        raise ValueError(DATE_FORMAT_ERROR) from None


def validate_habit_form(
    data: HabitFormData,
    today: date | None = None,
) -> HabitFormResult:
    """Validar y normalizar los datos del formulario.

    Args:
        data: Datos en bruto del formulario.
        today: Fecha actual para resolver la fecha opcional.

    Returns:
        Los datos normalizados y listos para persistir.

    Raises:
        ValueError: Con un mensaje en español si el nombre o la fecha no son
            válidos (RF-2.2, RF-2.3, RF-2.10).
    """
    name = data.name.strip() if data.name else ""
    if not name:
        raise ValueError(NAME_REQUIRED_ERROR)
    if len(name) > MAX_NAME_LENGTH:
        raise ValueError(NAME_TOO_LONG_ERROR)

    return HabitFormResult(
        name=name,
        start_date=parse_start_date(data.start_date, today=today),
        icon=normalize_icon(data.icon),
    )


def validate_habit_update(
    habit: Habit,
    data: HabitFormData,
    today: date | None = None,
) -> HabitFormResult:
    """Validar y normalizar los datos de una edición.

    Reutiliza las reglas de nombre de la creación, conserva la fecha y el
    icono actuales cuando el formulario no los cambia y rechaza las fechas
    futuras en lugar de normalizarlas (RF-2.5, RF-2.7, RF-2.8).

    Args:
        habit: Hábito que se está editando.
        data: Datos en bruto del formulario de edición.
        today: Fecha actual para rechazar fechas futuras.

    Returns:
        Los datos normalizados y listos para persistir.

    Raises:
        ValueError: Con un mensaje en español si el nombre no es válido, si
            la fecha no tiene el formato dd/mm/aaaa o si es futura.
    """
    current_day = today or date.today()

    name = data.name.strip() if data.name else ""
    if not name:
        raise ValueError(NAME_REQUIRED_ERROR)
    if len(name) > MAX_NAME_LENGTH:
        raise ValueError(NAME_TOO_LONG_ERROR)

    start_date = habit.start_date
    if (data.start_date or "").strip():
        start_date = _parse_strict_date(data.start_date)
        if start_date > current_day:
            raise ValueError(DATE_FUTURE_ERROR)

    icon = data.icon if data.icon in ALLOWED_ICONS else habit.icon

    return HabitFormResult(
        name=name,
        start_date=start_date,
        icon=icon,
    )
