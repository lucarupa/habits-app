# spec: 002-ui-redesign
"""Lógica pura del formulario de creación de hábitos.

Valida el nombre, la fecha opcional y el icono, y persiste el hábito delegando
en `core.py` y `storage.py`. No importa Flet (Constitución, principio 3).

Cubre RF-2.2 a RF-2.7, RF-2.9 y RF-2.10.
"""

import re
from dataclasses import dataclass
from datetime import date

from habits.core import ALLOWED_ICONS, DEFAULT_ICON, create_habit
from habits.storage import create_habit_db

MAX_NAME_LENGTH = 60

NAME_REQUIRED_ERROR = "⚠️ El nombre del hábito es obligatorio."
NAME_TOO_LONG_ERROR = "⚠️ El nombre no puede superar 60 caracteres."
DATE_FORMAT_ERROR = "⚠️ Formato de fecha inválido. Usa dd/mm/aaaa."

ICON_LABELS: dict[str, str] = {
    "book": "Libro",
    "code": "Código",
    "science": "Ciencia",
    "language": "Idioma",
    "music": "Música",
    "art": "Arte",
    "math": "Matemáticas",
    "fitness": "Ejercicio",
}

ICON_CATALOG: tuple[str, ...] = tuple(ICON_LABELS)

_DATE_PATTERN = re.compile(r"^(\d{2})/(\d{2})/(\d{4})$")


@dataclass(frozen=True)
class HabitFormData:
    """Datos en bruto introducidos en el formulario.

    Atributos:
        name: Texto del campo de nombre.
        start_date: Texto del campo de fecha en dd/mm/aaaa; vacío si se omite.
        icon: Clave semántica del icono seleccionado.
    """

    name: str
    start_date: str = ""
    icon: str | None = DEFAULT_ICON


@dataclass(frozen=True)
class HabitFormResult:
    """Datos normalizados y validados del formulario.

    Atributos:
        name: Nombre sin espacios sobrantes.
        start_date: Fecha de inicio resuelta.
        icon: Icono válido, con el valor por defecto si no se eligió ninguno.
    """

    name: str
    start_date: date
    icon: str


@dataclass(frozen=True)
class CreateHabitResult:
    """Resultado de crear un hábito desde el formulario.

    Atributos:
        habit_id: ID auto-generado en la base de datos.
        name: Nombre guardado.
        start_date: Fecha de inicio guardada.
        icon: Icono guardado.
    """

    habit_id: int
    name: str
    start_date: date
    icon: str


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


def create_habit_from_form(
    data: HabitFormData,
    db_path: str = "data/habits.db",
    today: date | None = None,
) -> CreateHabitResult:
    """Validar el formulario y persistir el hábito.

    Args:
        data: Datos en bruto del formulario.
        db_path: Ruta al archivo de base de datos SQLite.
        today: Fecha actual para resolver la fecha opcional.

    Returns:
        El ID del hábito creado junto con sus datos guardados (RF-2.7).

    Raises:
        ValueError: Si el formulario no es válido; en ese caso no se persiste
            ningún hábito (RF-2.2, RF-2.3, RF-2.10).
    """
    form = validate_habit_form(data, today=today)
    habit = create_habit(form.name, form.start_date, form.icon)
    habit_id = create_habit_db(
        habit.name,
        habit.start_date.isoformat(),
        habit.icon,
        db_path,
    )

    return CreateHabitResult(
        habit_id=habit_id,
        name=habit.name,
        start_date=habit.start_date,
        icon=habit.icon,
    )
