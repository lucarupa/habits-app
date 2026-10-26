# spec: 002-ui-redesign
"""Layout del estado vacío del panel de detalle."""

import os
import tempfile
from datetime import date

import pytest

pytest.importorskip("flet")

import flet as ft

from habits.app import main
from habits.storage import create_habit_db, init_db

TODAY = date(2024, 10, 24)


class FakeWindow:
    """Ventana mínima usada por `configure_page`."""


class FakeView:
    """Vista raíz mínima que contiene los controles añadidos a la página."""

    def __init__(self):
        self.controls = []


class FakePage:
    """Página mínima suficiente para montar la interfaz."""

    def __init__(self):
        self.open_dialogs = []
        self.views = [FakeView()]
        self.window = FakeWindow()

    def add(self, *controls):
        """Añadir controles a la vista raíz."""
        self.views[0].controls.extend(controls)

    def show_dialog(self, dialog):
        """Registrar un diálogo abierto."""
        dialog.open = True
        self.open_dialogs.append(dialog)

    def pop_dialog(self):
        """Cerrar el último diálogo abierto."""
        if not self.open_dialogs:
            return None
        dialog = self.open_dialogs.pop()
        dialog.open = False
        return dialog

    def update(self):
        """Simular el repintado de la página."""


def detail_controls(page):
    """Devolver la columna de detalle y sus controles principales."""
    layout = page.views[0].controls[0].content
    detail_column = layout.controls[1]
    header = detail_column.controls[0]
    empty_panel = detail_column.controls[4]
    return detail_column, header, empty_panel


def test_empty_state_fills_the_detail_panel_and_centers_its_content():
    """RF-6.2: el estado vacío se centra en el panel disponible."""
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "empty.db")
    init_db(db_path)
    page = FakePage()
    try:
        main(page, db_path=db_path)

        detail_column, header, empty_panel = detail_controls(page)

        assert detail_column.scroll is None
        assert detail_column.horizontal_alignment == ft.CrossAxisAlignment.STRETCH
        assert empty_panel.expand is True
        assert empty_panel.alignment == ft.Alignment.CENTER
        assert empty_panel.visible is True
        assert header.visible is False
    finally:
        if os.path.exists(db_path):
            os.remove(db_path)


def test_detail_restores_scroll_and_header_when_habits_exist():
    """RF-1.1, RF-6.4: con hábitos vuelve el detalle normal."""
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "habits.db")
    init_db(db_path)
    create_habit_db("Leer", TODAY.isoformat(), db_path=db_path)
    page = FakePage()
    try:
        main(page, db_path=db_path)

        detail_column, header, empty_panel = detail_controls(page)

        assert detail_column.scroll == ft.ScrollMode.AUTO
        assert header.visible is True
        assert empty_panel.visible is False
    finally:
        if os.path.exists(db_path):
            os.remove(db_path)
