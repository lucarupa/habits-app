# spec: 002-ui-redesign
# spec: 003-edit-delete-habits
"""Lógica pura del formulario de creación y edición de hábitos.

Valida el nombre, la fecha opcional y el icono, y persiste el hábito delegando
en `habits.domain` y `habits.persistence`. No importa Flet (Constitución, principio 3).

Cubre RF-2.2 a RF-2.10 de la creación y RF-2.1 a RF-2.14 de la edición.
"""

import re
from dataclasses import dataclass
from datetime import date

from habits.domain.habits import create_habit, update_habit
from habits.domain.models import ALLOWED_ICONS, DEFAULT_ICON, Habit
from habits.persistence.habits_repo import create_habit_db, update_habit_db

MAX_NAME_LENGTH = 60

NAME_REQUIRED_ERROR = "⚠️ El nombre del hábito es obligatorio."
NAME_TOO_LONG_ERROR = "⚠️ El nombre no puede superar 60 caracteres."
DATE_FORMAT_ERROR = "⚠️ Formato de fecha inválido. Usa dd/mm/aaaa."
DATE_FUTURE_ERROR = "⚠️ La fecha de inicio no puede ser futura."

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


@dataclass(frozen=True)
class UpdateHabitResult:
    """Resultado de editar un hábito desde el formulario.

    Atributos:
        habit_id: ID del hábito editado.
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


def update_habit_from_form(
    habit: Habit,
    data: HabitFormData,
    db_path: str = "data/habits.db",
    today: date | None = None,
) -> UpdateHabitResult:
    """Validar el formulario de edición y persistir los cambios.

    Delega la actualización del dominio en `update_habit` y la escritura en
    `update_habit_db`. Los registros diarios del hábito no se modifican
    (RF-2.12).

    Args:
        habit: Hábito que se está editando.
        data: Datos en bruto del formulario de edición.
        db_path: Ruta al archivo de base de datos SQLite.
        today: Fecha actual para rechazar fechas futuras.

    Returns:
        El ID del hábito editado junto con sus datos guardados (RF-2.9).

    Raises:
        ValueError: Si el formulario no es válido o el hábito ya no existe;
            en esos casos no se persiste ningún cambio.
    """
    current_day = today or date.today()
    validated = validate_habit_update(habit, data, today=current_day)
    updated = update_habit(
        habit,
        name=validated.name,
        start_date=validated.start_date,
        icon=validated.icon,
        today=current_day,
    )

    update_habit_db(
        habit_id=updated.id,
        name=updated.name,
        start_date=updated.start_date.isoformat(),
        icon=updated.icon,
        db_path=db_path,
    )

    return UpdateHabitResult(
        habit_id=updated.id,
        name=updated.name,
        start_date=updated.start_date,
        icon=updated.icon,
    )
