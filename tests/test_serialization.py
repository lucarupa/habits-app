# spec: 002-ui-redesign
"""Regresión de serialización de los controles Flet.

Reproduce el fallo `FrozenInstanceError: cannot assign to field '_parent'`
que ocurría al actualizar la página cuando el estado contenía hábitos.
Los modelos de `app_state.py` y `core.py` son dataclasses frozen y no deben
formar parte del árbol de controles que Flet serializa.
"""

import os
import tempfile
from datetime import date

import pytest

pytest.importorskip("flet")

from flet.controls.base_control import BaseControl
from flet.controls.object_patch import ObjectPatch

from habits.app import (
    ActivityHeatmap,
    EmptyDetailPanel,
    HabitDetailHeader,
    HabitStatsCards,
    Sidebar,
)
from habits.app_state import AppState, load_app_state
from habits.storage import create_habit_db, init_db, mark_completed_db

TODAY = date(2024, 10, 24)


def serialize(control) -> None:
    """Ejecutar el mismo diff que Flet usa al actualizar la página."""
    ObjectPatch.from_diff(
        control,
        control,
        control_cls=BaseControl,
        parent=None,
        path=None,
        frozen=False,
    )


class TestControlSerialization:
    """Los controles deben poder serializarse tras refrescar el estado."""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_habits.db")
        init_db(self.db_path)
        self.habit_id = create_habit_db(
            "Leer", "2024-10-01", icon="book", db_path=self.db_path
        )
        self.before = load_app_state(self.db_path, today=TODAY)

        mark_completed_db(
            self.habit_id, TODAY.isoformat(), db_path=self.db_path
        )
        self.after = load_app_state(self.db_path, today=TODAY)

    def teardown_method(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def _refresh_with(self, control, state: AppState) -> None:
        serialize(control)
        control.state = state
        control.refresh()
        serialize(control)

    def test_sidebar_serializes_after_state_refresh(self):
        """La barra lateral no debe atravesar `Habit`, `HabitStats` ni `SidebarItem`."""
        self._refresh_with(Sidebar(state=self.before), self.after)

    def test_detail_header_serializes_after_state_refresh(self):
        """El encabezado no debe atravesar el estado ni `DetailHeader`."""
        self._refresh_with(HabitDetailHeader(state=self.before), self.after)

    def test_stats_cards_serialize_after_state_refresh(self):
        """Las tarjetas no deben atravesar `StatCard`."""
        self._refresh_with(HabitStatsCards(state=self.before), self.after)

    def test_heatmap_serializes_after_state_refresh(self):
        """El heatmap no debe atravesar `HeatmapDay`."""
        self._refresh_with(ActivityHeatmap(state=self.before), self.after)

    def test_empty_panel_serializes_after_state_refresh(self):
        """El estado vacío no debe atravesar `AppState`."""
        self._refresh_with(EmptyDetailPanel(state=self.before), self.after)
