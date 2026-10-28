# spec: 002-ui-redesign
# spec: 003-edit-delete-habits
# spec: 006-code-organization
"""Datos, resultados, constantes e iconos del formulario de hábitos.

Conserva los mismos valores y textos del módulo monolítico anterior, sin
dependencias de Flet ni SQLite (RF-2.2, RF-2.3 y RF-5.3).
"""

from dataclasses import dataclass
from datetime import date

from habits.domain.models import DEFAULT_ICON

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
