# spec: 002-ui-redesign
# spec: 006-code-organization
"""Iconos, etiquetas y formatos visuales compartidos por la interfaz.

Conserva los mismos valores y el mismo comportamiento observable del módulo
monolítico anterior (RF-2.2 y RF-5.4).
"""

from datetime import date

import flet as ft

from habits.state.models import (
    STAT_BEST_STREAK_LABEL,
    STAT_CURRENT_STREAK_LABEL,
    STAT_REGISTERED_DAYS_LABEL,
    format_date_label,
)

ICON_BY_KEY = {
    "book": ft.Icons.MENU_BOOK,
    "code": ft.Icons.CODE,
    "science": ft.Icons.SCIENCE,
    "language": ft.Icons.TRANSLATE,
    "music": ft.Icons.MUSIC_NOTE,
    "art": ft.Icons.PALETTE,
    "math": ft.Icons.CALCULATE,
    "fitness": ft.Icons.FITNESS_CENTER,
}
DEFAULT_SIDEBAR_ICON = ft.Icons.MENU_BOOK

STAT_CARD_ICONS = {
    STAT_CURRENT_STREAK_LABEL: ft.Icons.LOCAL_FIRE_DEPARTMENT,
    STAT_BEST_STREAK_LABEL: ft.Icons.STAR,
    STAT_REGISTERED_DAYS_LABEL: ft.Icons.CALENDAR_MONTH,
}

WEEKDAY_LABELS = ("L", "M", "X", "J", "V", "S", "D")

RECOVER_STREAK_BUTTON_LABEL = "Recuperar racha"
STREAK_RECOVERY_DIALOG_TITLE = "Recuperar racha"
STREAK_RECOVERY_CANCEL_LABEL = "Cancelar"
STREAK_RECOVERY_CONFIRM_LABEL = "Recuperar"
STREAK_RECOVERY_WARNING = (
    "Los días quedarán marcados como recuperados: contarán para la racha, "
    "pero no para «Días registrados»."
)


def icon_for_habit(icon_key: str):
    """Traducir una clave semántica de icono a un icono de Flet.

    Args:
        icon_key: Clave guardada en la base de datos.

    Returns:
        El icono de Flet correspondiente, o el icono por defecto.
    """
    return ICON_BY_KEY.get(icon_key, DEFAULT_SIDEBAR_ICON)


def format_streak_label(streak: int) -> str:
    """Formatear la racha para mostrarla en la barra lateral.

    Args:
        streak: Racha actual en días.

    Returns:
        Texto en español con la racha, o "Sin racha" si es 0.
    """
    if streak == 0:
        return "Sin racha"
    suffix = "s" if streak != 1 else ""
    return f"🔥 {streak} día{suffix}"


def format_date_display(d: date) -> str:
    """Formatear una fecha para mostrar al usuario en dd/mm/aaaa.

    Args:
        d: La fecha a formatear.

    Returns:
        La fecha como cadena en formato dd/mm/aaaa.
    """
    return format_date_label(d)
