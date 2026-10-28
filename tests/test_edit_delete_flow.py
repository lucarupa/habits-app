# spec: 003-edit-delete-habits
"""Tests del flujo integrado de edición y eliminación — Tareas 6.1 y 6.2.

Se ejecutan con el intérprete del proyecto (`.venv`), que tiene Flet instalado.
Con un Python sin Flet el módulo se omite para no romper la suite pura.
"""

import os
import sqlite3
import tempfile
from datetime import date, timedelta

import pytest

pytest.importorskip("flet")

import flet as ft

from habits.app import main
from habits.ui.delete_dialog import DeleteHabitDialog
from habits.ui.form_dialog import HabitFormDialog
from habits.state.models import EMPTY_SIDEBAR_MESSAGE
from habits.persistence.completions_repo import (
    get_completions_db,
    mark_completed_db,
)
from habits.persistence.habits_repo import create_habit_db, get_habit_db
from habits.persistence.schema import init_db
from habits.theme import SELECTED_BG

TODAY = date.today()


class FakeWindow:
    """Ventana mínima usada por `configure_page`."""

    width = None
    height = None
    min_width = None
    min_height = None
    icon = None


class FakeView:
    """Vista raíz mínima que contiene los controles añadidos a la página."""

    def __init__(self):
        self.controls = []


class FakePage:
    """Página mínima que registra los diálogos abiertos y cerrados."""

    def __init__(self):
        self.open_dialogs = []
        self.updates = 0
        self.views = [FakeView()]
        self.window = FakeWindow()
        self.title = ""
        self.bgcolor = None
        self.theme_mode = None
        self.theme = None
        self.padding = None

    def add(self, *controls):
        """Añadir controles a la vista raíz, como `flet.Page.add`."""
        self.views[0].controls.extend(controls)

    def show_dialog(self, dialog):
        dialog.open = True
        self.open_dialogs.append(dialog)

    def pop_dialog(self):
        if not self.open_dialogs:
            return None
        dialog = self.open_dialogs.pop()
        dialog.open = False
        return dialog

    def update(self):
        self.updates += 1


def collect_texts(control) -> list[str]:
    """Recorrer un árbol de controles Flet y recoger sus textos."""
    texts: list[str] = []
    value = getattr(control, "value", None)
    if isinstance(value, str):
        texts.append(value)
    for child in getattr(control, "controls", None) or []:
        texts.extend(collect_texts(child))
    content = getattr(control, "content", None)
    if content is not None:
        texts.extend(collect_texts(content))
    return texts


def find_form_dialog(callback) -> HabitFormDialog:
    """Extraer el `HabitFormDialog` capturado por un callback de `main`."""
    if callback is None:
        raise AssertionError("main no conectó el callback de creación o edición")
    for cell in callback.__closure__ or ():
        content = cell.cell_contents
        if isinstance(content, HabitFormDialog):
            return content
    raise AssertionError("No se encontró el HabitFormDialog en el callback")


def find_delete_dialog(callback) -> DeleteHabitDialog:
    """Extraer el `DeleteHabitDialog` capturado por un callback de `main`."""
    if callback is None:
        raise AssertionError("main no conectó el callback de eliminación")
    for cell in callback.__closure__ or ():
        content = cell.cell_contents
        if isinstance(content, DeleteHabitDialog):
            return content
    raise AssertionError("No se encontró el DeleteHabitDialog en el callback")


def sidebar_names(sidebar) -> list[str]:
    """Leer los nombres visibles en la barra lateral, en su orden."""
    return [
        item.content.controls[2].value
        for item in sidebar._items_column.controls
    ]


class TestEditFlow:
    """Tests del flujo integrado de edición — Tarea 6.1."""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_habits.db")
        init_db(self.db_path)
        self.reading_id = create_habit_db(
            "Lectura", "2024-09-01", icon="book", db_path=self.db_path
        )
        self.python_id = create_habit_db(
            "Python", "2024-09-15", icon="code", db_path=self.db_path
        )
        self.page = FakePage()

    def teardown_method(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def open_app(self):
        """Montar `main` y devolver los widgets del detalle."""
        main(self.page, db_path=self.db_path)
        layout = self.page.views[0].controls[0].content
        sidebar = layout.controls[0]
        detail_column = layout.controls[1]
        return (
            sidebar,
            detail_column.controls[0],
            detail_column.controls[1],
            detail_column.controls[2],
            detail_column.controls[3],
        )

    def mark_python_streak(self) -> None:
        """Registrar hoy y ayer para que Python tenga racha y estadísticas."""
        mark_completed_db(
            self.python_id, TODAY.isoformat(), db_path=self.db_path
        )
        mark_completed_db(
            self.python_id,
            (TODAY - timedelta(days=1)).isoformat(),
            db_path=self.db_path,
        )

    def test_edit_refreshes_sidebar_detail_and_keeps_selection(self):
        """RF-2.9, RF-4.2, RF-4.3, RF-4.4: edición coherente sin perder datos."""
        self.mark_python_streak()
        sidebar, header, stats, heatmap, registration = self.open_app()

        assert header.state.selected.habit.id == self.python_id
        assert sidebar_names(sidebar) == ["Python", "Lectura"]
        stats_before = [card.value for card in stats.cards]
        heatmap_before = [
            (day.date, day.completed, day.is_today)
            for row in heatmap.rows
            for day in row
        ]
        completions_before = get_completions_db(self.python_id, self.db_path)
        registration_before = (
            registration._date_text.value,
            registration.message,
        )

        assert header.edit_button is not None
        header.edit_button.on_click(None)
        dialog = find_form_dialog(header.on_edit)

        assert dialog.dialog.open is True
        assert dialog.name_field.value == "Python"
        assert dialog.icon_dropdown.value == "code"
        assert dialog.date_field.value == "15/09/2024"

        dialog.name_field.value = "Python avanzado"
        dialog.icon_dropdown.value = "science"
        dialog.date_field.value = "20/09/2024"
        dialog.submit()

        assert dialog.dialog.open is False
        assert self.page.open_dialogs == []

        row = get_habit_db(self.python_id, self.db_path)
        assert row is not None
        assert row.name == "Python avanzado"
        assert row.start_date == "2024-09-20"
        assert row.icon == "science"

        assert sidebar.state.selected.habit.id == self.python_id
        assert sidebar_names(sidebar) == ["Python avanzado", "Lectura"]
        sidebar_item = sidebar._items_column.controls[0].content
        assert sidebar_item.controls[1].icon == ft.Icons.SCIENCE
        assert sidebar_item.controls[3].value == "🔥 2 días"

        header_texts = collect_texts(header)
        assert "Python avanzado" in header_texts
        assert "Inicio: 20/09/2024" in header_texts

        assert [card.value for card in stats.cards] == stats_before
        assert [
            (day.date, day.completed, day.is_today)
            for row in heatmap.rows
            for day in row
        ] == heatmap_before
        assert (
            registration._date_text.value,
            registration.message,
        ) == registration_before
        assert get_completions_db(self.python_id, self.db_path) == completions_before

    def test_edit_reorders_sidebar_when_name_changes(self):
        """RF-4.1, RF-4.4: el desempate alfabético reordena sin perder selección."""
        sidebar, header, _stats, _heatmap, _registration = self.open_app()

        assert header.state.selected.habit.id == self.reading_id
        assert sidebar_names(sidebar) == ["Lectura", "Python"]

        header.edit_button.on_click(None)
        dialog = find_form_dialog(header.on_edit)
        dialog.name_field.value = "Zebra"

        dialog.submit()

        assert sidebar_names(sidebar) == ["Python", "Zebra"]
        assert sidebar.state.selected.habit.id == self.reading_id
        assert header.state.selected.habit.id == self.reading_id
        assert header.state.detail_header().name == "Zebra"

        items = sidebar.state.sidebar_items()
        assert [item.name for item in items] == ["Python", "Zebra"]
        assert items[1].habit_id == self.reading_id
        assert items[1].selected is True
        assert sidebar._items_column.controls[1].bgcolor == SELECTED_BG

    def test_edit_cancel_keeps_view_unchanged(self):
        """RF-4.7: cancelar la edición deja la vista y el hábito intactos."""
        sidebar, header, _stats, _heatmap, _registration = self.open_app()
        sidebar_before = sidebar_names(sidebar)
        header_before = collect_texts(header)

        header.edit_button.on_click(None)
        dialog = find_form_dialog(header.on_edit)
        dialog.name_field.value = "Cambiado"
        dialog.date_field.value = "01/08/2024"
        dialog.icon_dropdown.value = "art"
        dialog.dialog.actions[0].on_click(None)

        assert dialog.dialog.open is False
        assert self.page.open_dialogs == []
        assert sidebar_names(sidebar) == sidebar_before
        assert collect_texts(header) == header_before
        assert sidebar.state.selected.habit.id == self.reading_id

        row = get_habit_db(self.reading_id, self.db_path)
        assert row is not None
        assert (row.name, row.start_date, row.icon) == (
            "Lectura",
            "2024-09-01",
            "book",
        )


class TestDeleteFlow:
    """Tests del flujo integrado de eliminación — Tarea 6.2."""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_habits.db")
        init_db(self.db_path)
        self.page = FakePage()

    def teardown_method(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def add_habit(
        self,
        name: str,
        start_date: str = "2024-09-01",
        icon: str = "book",
        completed: tuple[date, ...] = (),
    ) -> int:
        """Crear un hábito y, opcionalmente, registrar días completados."""
        habit_id = create_habit_db(
            name, start_date, icon=icon, db_path=self.db_path
        )
        for day in completed:
            mark_completed_db(
                habit_id, day.isoformat(), db_path=self.db_path
            )
        return habit_id

    def open_app(self):
        """Montar `main` y devolver los widgets del detalle."""
        main(self.page, db_path=self.db_path)
        layout = self.page.views[0].controls[0].content
        sidebar = layout.controls[0]
        detail_column = layout.controls[1]
        return (
            sidebar,
            detail_column.controls[0],
            detail_column.controls[1],
            detail_column.controls[2],
            detail_column.controls[3],
            detail_column.controls[4],
        )

    def confirm_delete(self, header):
        """Pulsar “Eliminar” y aceptar el diálogo de confirmación."""
        header.delete_button.on_click(None)
        dialog = find_delete_dialog(header.on_delete)
        dialog.dialog.actions[1].on_click(None)
        return dialog

    def test_delete_confirm_removes_habit_and_records(self):
        """RF-3.4, RF-4.5: confirmar borra el hábito y sus registros."""
        habit_id = self.add_habit("Python", completed=(TODAY,))
        sidebar, header, stats, heatmap, registration, empty_panel = (
            self.open_app()
        )
        assert sidebar.state.selected.habit.id == habit_id

        self.confirm_delete(header)

        assert self.page.open_dialogs == []
        assert get_habit_db(habit_id, self.db_path) is None
        assert get_completions_db(habit_id, self.db_path) == []
        assert sidebar.state.is_empty is True
        assert EMPTY_SIDEBAR_MESSAGE in collect_texts(sidebar)
        assert header.visible is False
        assert stats.visible is False
        assert heatmap.visible is False
        assert registration.visible is False
        assert empty_panel.visible is True

    def test_delete_selects_next_habit_in_order(self):
        """RF-3.6, RF-4.5: se selecciona el primero de la lista restante."""
        python_id = self.add_habit(
            "Python", completed=(TODAY, TODAY - timedelta(days=1))
        )
        arte_id = self.add_habit("Arte")
        self.add_habit("Lectura")
        sidebar, header, _stats, _heatmap, _registration, empty_panel = (
            self.open_app()
        )

        assert header.state.selected.habit.id == python_id
        assert sidebar_names(sidebar) == ["Python", "Arte", "Lectura"]

        self.confirm_delete(header)

        assert get_habit_db(python_id, self.db_path) is None
        assert sidebar_names(sidebar) == ["Arte", "Lectura"]
        assert sidebar.state.selected.habit.id == arte_id
        assert header.state.selected.habit.id == arte_id
        assert header.state.detail_header().name == "Arte"
        assert header.visible is True
        assert empty_panel.visible is False

    def test_delete_last_habit_shows_empty_state_and_allows_creating(self):
        """RF-3.7, RF-4.6: al borrar el último aparece el estado vacío."""
        habit_id = self.add_habit("Python")
        sidebar, header, _stats, _heatmap, _registration, empty_panel = (
            self.open_app()
        )
        assert sidebar.state.selected.habit.id == habit_id

        self.confirm_delete(header)

        assert header.visible is False
        assert empty_panel.visible is True
        assert EMPTY_SIDEBAR_MESSAGE in collect_texts(sidebar)

        sidebar.on_new()
        dialog = find_form_dialog(sidebar.on_new)
        dialog.name_field.value = "Nuevo"
        dialog.submit()

        assert len(sidebar_names(sidebar)) == 1
        assert sidebar_names(sidebar) == ["Nuevo"]
        assert sidebar.state.selected.habit.id is not None
        assert header.visible is True
        assert header.state.detail_header().name == "Nuevo"
        assert empty_panel.visible is False
        assert get_habit_db(
            sidebar.state.selected.habit.id, self.db_path
        ) is not None

    def test_delete_database_error_keeps_habit(self, monkeypatch):
        """RF-3.8: un fallo de persistencia conserva el hábito y sus registros."""
        habit_id = self.add_habit("Python", completed=(TODAY,))
        sidebar, header, _stats, _heatmap, _registration, empty_panel = (
            self.open_app()
        )

        def fail_delete(*args, **kwargs):
            raise sqlite3.OperationalError("fallo simulado")

        monkeypatch.setattr("habits.app.delete_habit_db", fail_delete)

        self.confirm_delete(header)

        assert get_habit_db(habit_id, self.db_path) is not None
        assert get_completions_db(habit_id, self.db_path) == [
            TODAY.isoformat()
        ]
        assert sidebar_names(sidebar) == ["Python"]
        assert sidebar.state.selected.habit.id == habit_id
        assert header.visible is True
        assert header.state.detail_header().name == "Python"
        assert empty_panel.visible is False

        snack = self.page.open_dialogs[-1]
        assert isinstance(snack, ft.SnackBar)
        assert any(
            "No se pudo eliminar" in text
            for text in collect_texts(snack)
        )
