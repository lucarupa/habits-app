# spec: 002-ui-redesign
"""Tests del tema visual y la ventana — Tarea 3.5, RF-7.1, RF-7.3."""

from habits.theme import (
    ACCENT_GREEN,
    BACKGROUND,
    DETAIL_MIN_WIDTH,
    SELECTED_BG,
    SIDEBAR_BG,
    SIDEBAR_WIDTH,
    SURFACE,
    WINDOW_HEIGHT,
    WINDOW_MIN_HEIGHT,
    WINDOW_MIN_WIDTH,
    WINDOW_WIDTH,
    window_config,
)


class TestTheme:
    """Tests de la paleta y la configuración de ventana — Tarea 3.5."""

    def test_uses_cream_background_and_light_surfaces(self):
        """RF-7.1: Fondo crema y superficies claras."""
        assert BACKGROUND == "#f6efe0"
        assert SURFACE == "#fffdf8"
        assert SIDEBAR_BG == "#f1e7d5"

    def test_uses_green_accents(self):
        """RF-7.1: Acento verde y fondo suave para la selección."""
        assert ACCENT_GREEN == "#2e7d32"
        assert SELECTED_BG == "#e3f1e4"

    def test_window_fits_sidebar_and_detail(self):
        """RF-7.3: La ventana cabe la barra lateral y el detalle sin scroll horizontal."""
        config = window_config()

        assert config == {
            "width": WINDOW_WIDTH,
            "height": WINDOW_HEIGHT,
            "min_width": WINDOW_MIN_WIDTH,
            "min_height": WINDOW_MIN_HEIGHT,
        }
        assert WINDOW_WIDTH >= SIDEBAR_WIDTH + DETAIL_MIN_WIDTH
        assert WINDOW_MIN_WIDTH >= SIDEBAR_WIDTH + DETAIL_MIN_WIDTH
        assert WINDOW_HEIGHT >= WINDOW_MIN_HEIGHT
