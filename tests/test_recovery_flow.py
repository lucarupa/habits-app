# spec: 004-duplicate-warning-streak-recovery
"""Tests del flujo integrado de recuperación de racha — Tarea 5.7.

Montan `main`, abren el diálogo desde el panel, confirman o cancelan la
recuperación y comprueban la base de datos, las estadísticas, el heatmap y la
persistencia. Se ejecutan con el intérprete del proyecto (`.venv`); sin Flet
el módulo se omite para no romper la suite pura.
"""

import os
import sqlite3
import tempfile
from datetime import date, timedelta

import pytest

pytest.importorskip("flet")

import flet as ft

from habits.app import main
from habits.app_state import load_app_state
from habits.storage import (
    create_habit_db,
    get_recovered_dates_db,
    init_db,
    mark_completed_db,
)
from habits.theme import HEATMAP_RECOVERED

TODAY = date.today()
GAP_DATES = (
    TODAY - timedelta(days=2),
    TODAY - timedelta(days=1),
)


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
    for attribute in ("value", "text"):
        value = getattr(control, attribute, None)
        if isinstance(value, str):
            texts.append(value)
    for attribute in ("title", "content"):
        child = getattr(control, attribute, None)
        if child is not None:
            texts.extend(collect_texts(child))
    for child in getattr(control, "controls", None) or []:
        texts.extend(collect_texts(child))
    return texts


def find_recovery_dialog(page: FakePage) -> ft.AlertDialog:
    """Devolver el diálogo de recuperación abierto en la página."""
    dialogs = [
        dialog
        for dialog in page.open_dialogs
        if isinstance(dialog, ft.AlertDialog)
    ]
    if not dialogs:
        raise AssertionError("main no abrió el diálogo de recuperación")
    return dialogs[-1]


def find_heatmap_cell(heatmap, day: date):
    """Localizar el control de la celda de una fecha en el heatmap."""
    for row_index, row in enumerate(heatmap.rows):
        for column_index, cell in enumerate(row):
            if cell.date == day:
                return heatmap._grid.controls[row_index].controls[
                    column_index
                ]
    raise AssertionError(f"No se encontró la celda {day}")


class TestRecoveryFlow:
    """Flujo integrado de recuperación — Tarea 5.7, RF-2.7 a RF-2.16."""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_habits.db")
        init_db(self.db_path)
        self.habit_id = create_habit_db(
            "Leer", "2024-09-01", icon="book", db_path=self.db_path
        )
        mark_completed_db(
            self.habit_id, TODAY.isoformat(), db_path=self.db_path
        )
        mark_completed_db(
            self.habit_id,
            (TODAY - timedelta(days=3)).isoformat(),
            db_path=self.db_path,
        )
        self.page = FakePage()

    def teardown_method(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def open_app(self, page: FakePage | None = None):
        """Montar `main` y devolver los widgets del detalle."""
        target = page or self.page
        main(target, db_path=self.db_path)
        layout = target.views[0].controls[0].content
        sidebar = layout.controls[0]
        detail_column = layout.controls[1]
        return (
            sidebar,
            detail_column.controls[0],
            detail_column.controls[1],
            detail_column.controls[2],
            detail_column.controls[3],
        )

    def open_recovery_dialog(self, registration):
        """Pulsar “Recuperar racha” y devolver el diálogo abierto."""
        assert registration._recover_button.visible is True
        registration._recover_button.on_click(None)
        return find_recovery_dialog(self.page)

    def confirm_recovery(self, registration) -> ft.AlertDialog:
        """Abrir el diálogo y confirmar la recuperación."""
        dialog = self.open_recovery_dialog(registration)
        dialog.actions[1].on_click(None)
        assert dialog.open is False
        return dialog

    def test_recover_streak_updates_db_and_view(self):
        """RF-2.8 a RF-2.12: confirmar recupera días y actualiza la vista."""
        sidebar, _header, stats, heatmap, registration = self.open_app()

        assert [card.value for card in stats.cards] == [1, 1, 2]

        dialog = self.open_recovery_dialog(registration)
        texts = collect_texts(dialog)

        assert dialog.modal is True
        assert "Leer" in texts
        assert any("2 días" in text for text in texts)

        dialog.actions[1].on_click(None)

        assert self.page.open_dialogs == []
        assert get_recovered_dates_db(self.habit_id, self.db_path) == [
            day.isoformat() for day in GAP_DATES
        ]
        assert [card.value for card in stats.cards] == [4, 4, 2]

        for day in GAP_DATES:
            assert (
                find_heatmap_cell(heatmap, day).bgcolor
                == HEATMAP_RECOVERED
            )

        assert registration._recover_button.visible is False
        sidebar_item = sidebar._items_column.controls[0].content
        assert sidebar_item.controls[3].value == "🔥 4 días"

    def test_recover_streak_keeps_registered_days(self):
        """RF-2.10: “Días registrados” no cuenta los días recuperados."""
        _sidebar, _header, stats, _heatmap, registration = self.open_app()

        registered_before = stats.cards[2].value
        self.confirm_recovery(registration)

        assert registered_before == 2
        assert stats.cards[2].value == 2
        assert stats.cards[0].value == 4

    def test_recover_streak_persists_after_reload(self):
        """RF-2.15: los días recuperados sobreviven a una recarga."""
        _sidebar, _header, _stats, _heatmap, registration = self.open_app()

        self.confirm_recovery(registration)

        reloaded = load_app_state(self.db_path, today=TODAY)
        selected = reloaded.selected

        assert selected is not None
        assert selected.recovered_dates == set(GAP_DATES)
        assert selected.stats.current_streak == 4
        assert selected.stats.best_streak == 4
        assert selected.stats.registered_days == 2

        second_page = FakePage()
        _sidebar2, _header2, stats2, heatmap2, registration2 = (
            self.open_app(second_page)
        )

        assert [card.value for card in stats2.cards] == [4, 4, 2]
        assert registration2._recover_button.visible is False
        for day in GAP_DATES:
            assert (
                find_heatmap_cell(heatmap2, day).bgcolor
                == HEATMAP_RECOVERED
            )

    def test_recover_streak_cancel_changes_nothing(self):
        """RF-2.7: cancelar deja la base de datos y la vista igual."""
        _sidebar, _header, stats, _heatmap, registration = self.open_app()
        stats_before = [card.value for card in stats.cards]

        dialog = self.open_recovery_dialog(registration)
        dialog.actions[0].on_click(None)

        assert dialog.open is False
        assert self.page.open_dialogs == []
        assert get_recovered_dates_db(self.habit_id, self.db_path) == []
        assert [card.value for card in stats.cards] == stats_before
        assert registration._recover_button.visible is True

    def test_recover_streak_database_error_keeps_state(self, monkeypatch):
        """RF-2.16: un fallo no deja recuperaciones parciales y avisa."""
        _sidebar, _header, stats, heatmap, registration = self.open_app()
        stats_before = [card.value for card in stats.cards]

        def fail_recovery(*args, **kwargs):
            raise sqlite3.OperationalError("fallo simulado")

        monkeypatch.setattr(
            "habits.app.mark_recovered_days_db", fail_recovery
        )

        self.confirm_recovery(registration)

        assert get_recovered_dates_db(self.habit_id, self.db_path) == []
        assert [card.value for card in stats.cards] == stats_before
        assert registration._recover_button.visible is True
        for day in GAP_DATES:
            assert (
                find_heatmap_cell(heatmap, day).bgcolor
                != HEATMAP_RECOVERED
            )

        snack = self.page.open_dialogs[-1]
        assert isinstance(snack, ft.SnackBar)
        assert any(
            "No se pudo recuperar" in text
            for text in collect_texts(snack)
        )
