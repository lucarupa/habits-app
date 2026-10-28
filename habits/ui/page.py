# spec: 002-ui-redesign
# spec: 006-code-organization
"""Configuración de la página y de la ventana de escritorio.

Conserva el tema claro, el tamaño de ventana y el icono personalizado del
módulo monolítico anterior (RF-2.2 y RF-5.4).
"""

from pathlib import Path

import flet as ft

from habits.theme import (
    ACCENT_GREEN,
    BACKGROUND,
    WINDOW_HEIGHT,
    WINDOW_MIN_HEIGHT,
    WINDOW_MIN_WIDTH,
    WINDOW_WIDTH,
)

APP_ICON_PATH = Path(__file__).resolve().parents[2] / "img" / "icon.ico"


def configure_page(page: ft.Page) -> None:
    """Aplicar el tema claro y el tamaño de ventana de escritorio.

    Usa fondo crema, superficies claras y acentos verdes, y abre la ventana
    con espacio suficiente para la barra lateral y el panel de detalle.
    """
    page.title = "Habits App"
    page.bgcolor = BACKGROUND
    page.theme_mode = ft.ThemeMode.LIGHT
    page.theme = ft.Theme(color_scheme_seed=ACCENT_GREEN)
    page.padding = 0
    page.window.width = WINDOW_WIDTH
    page.window.height = WINDOW_HEIGHT
    page.window.min_width = WINDOW_MIN_WIDTH
    page.window.min_height = WINDOW_MIN_HEIGHT
    if APP_ICON_PATH.exists():
        page.window.icon = str(APP_ICON_PATH)
