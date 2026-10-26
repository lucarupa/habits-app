# spec: 002-ui-redesign
"""Tema visual y dimensiones de ventana de la aplicación.

Constantes puras, sin dependencia de Flet, para poder testearlas (Tarea 3.5).
La capa de presentación (`app.py`) las traduce a propiedades de la página.
"""

BACKGROUND = "#f6efe0"
SURFACE = "#fffdf8"
SIDEBAR_BG = "#f1e7d5"
SELECTED_BG = "#e3f1e4"
ACCENT_GREEN = "#2e7d32"
TEXT_PRIMARY = "#2f2f2f"
TEXT_SECONDARY = "#777777"

SIDEBAR_WIDTH = 280
DETAIL_MIN_WIDTH = 640

WINDOW_WIDTH = 1120
WINDOW_HEIGHT = 720
WINDOW_MIN_WIDTH = 960
WINDOW_MIN_HEIGHT = 600


def window_config() -> dict[str, int]:
    """Devolver el tamaño inicial y mínimo de la ventana principal.

    Returns:
        Un diccionario con `width`, `height`, `min_width` y `min_height`.
    """
    return {
        "width": WINDOW_WIDTH,
        "height": WINDOW_HEIGHT,
        "min_width": WINDOW_MIN_WIDTH,
        "min_height": WINDOW_MIN_HEIGHT,
    }
