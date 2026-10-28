# spec: 002-ui-redesign
"""Icono de la aplicación: archivo .ico y ventana de escritorio."""

from pathlib import Path

import pytest

pytest.importorskip("flet")

from habits.ui.page import APP_ICON_PATH, configure_page


class FakeWindow:
    """Ventana mínima usada por `configure_page`."""


class FakePage:
    """Página mínima que acepta las propiedades del tema y la ventana."""

    def __init__(self):
        self.window = FakeWindow()


def test_app_icon_file_exists_and_is_a_valid_ico():
    """RF-7.3: el icono de la aplicación es un .ico real."""
    icon_path = Path(APP_ICON_PATH)

    assert icon_path.name == "icon.ico"
    assert icon_path.exists()
    assert icon_path.read_bytes()[:4] == b"\x00\x00\x01\x00"


def test_app_icns_file_exists_and_is_a_valid_icns():
    """RF-7.3: macOS usa un .icns real para el icono del bundle."""
    icon_path = Path(APP_ICON_PATH).with_suffix(".icns")

    assert icon_path.name == "icon.icns"
    assert icon_path.exists()
    assert icon_path.read_bytes()[:4] == b"icns"


def test_configure_page_sets_the_window_icon():
    """RF-7.3: la ventana usa el icono personalizado de la aplicación."""
    page = FakePage()

    configure_page(page)

    assert page.window.icon == str(APP_ICON_PATH)
