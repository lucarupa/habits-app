# spec: 002-ui-redesign
"""Tests de la lógica de registro del día actual — Fase 6, RF-5.

Verifican la capa pura que persiste el registro y evita duplicados, sin Flet.
"""

import os
import tempfile
from datetime import date

from habits import registration as registration_module
from habits.app_state import AppState, load_app_state
from habits.registration import (
    REGISTRATION_BUTTON_LABEL,
    REGISTRATION_DUPLICATE_MESSAGE,
    REGISTRATION_SUCCESS_MESSAGE,
    REGISTRATION_TITLE,
    RegistrationResult,
    is_registered_today,
    register_today,
)
from habits.persistence.completions_repo import (
    get_completions_db,
    mark_completed_db,
)
from habits.persistence.habits_repo import create_habit_db
from habits.persistence.schema import init_db

TODAY = date(2024, 10, 24)


class TestRegistrationConstants:
    """Textos visibles exigidos por RF-5.1, RF-5.2 y RF-5.4."""

    def test_labels_are_in_spanish(self):
        assert REGISTRATION_TITLE == "Registrar hoy"
        assert REGISTRATION_BUTTON_LABEL == "Guardar"
        assert REGISTRATION_DUPLICATE_MESSAGE == "Ya registrado hoy"

    def test_duplicate_warning_uses_habit_name(self):
        """RF-1.2: el aviso identifica el hábito con el formato acordado."""
        assert registration_module.duplicate_warning(
            "Python"
        ) == "⚠️ «Python» ya está registrado hoy."


class TestRegisterToday:
    """Registro efectivo y prevención de duplicados — RF-5.3, RF-5.4."""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_habits.db")
        init_db(self.db_path)
        self.habit_id = create_habit_db(
            "Leer", "2024-10-01", icon="book", db_path=self.db_path
        )

    def teardown_method(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_first_registration_persists_today(self):
        """RF-5.3: Guardar registra la fecha actual y confirma."""
        result = register_today(self.habit_id, TODAY, db_path=self.db_path)

        assert result == RegistrationResult(
            success=True,
            message=REGISTRATION_SUCCESS_MESSAGE,
        )
        assert get_completions_db(self.habit_id, self.db_path) == [
            TODAY.isoformat()
        ]

    def test_second_registration_is_rejected(self):
        """RF-5.4: El segundo intento devuelve “Ya registrado hoy”."""
        register_today(self.habit_id, TODAY, db_path=self.db_path)

        result = register_today(self.habit_id, TODAY, db_path=self.db_path)

        assert result == RegistrationResult(
            success=False,
            message=REGISTRATION_DUPLICATE_MESSAGE,
        )

    def test_duplicate_does_not_create_an_extra_row(self):
        """RF-5.4: No se crea un registro duplicado."""
        register_today(self.habit_id, TODAY, db_path=self.db_path)
        register_today(self.habit_id, TODAY, db_path=self.db_path)

        assert get_completions_db(self.habit_id, self.db_path) == [
            TODAY.isoformat()
        ]

    def test_is_registered_today_reflects_the_database(self):
        """RF-5.2, RF-5.4: El estado de completado se consulta por fecha."""
        assert is_registered_today(
            self.habit_id, TODAY, db_path=self.db_path
        ) is False

        mark_completed_db(
            self.habit_id, TODAY.isoformat(), db_path=self.db_path
        )

        assert is_registered_today(
            self.habit_id, TODAY, db_path=self.db_path
        ) is True

    def test_registering_another_date_does_not_mark_today(self):
        """RF-5.5: Solo se registra la fecha recibida, sin elegir otras."""
        yesterday = TODAY.replace(day=23)

        register_today(self.habit_id, yesterday, db_path=self.db_path)

        assert is_registered_today(
            self.habit_id, TODAY, db_path=self.db_path
        ) is False
        assert get_completions_db(self.habit_id, self.db_path) == [
            yesterday.isoformat()
        ]


class TestAppStateTodayStatus:
    """El estado conoce si el hábito seleccionado está completado hoy."""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_habits.db")
        init_db(self.db_path)
        self.habit_id = create_habit_db(
            "Leer", "2024-10-01", icon="book", db_path=self.db_path
        )

    def teardown_method(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_false_without_records(self):
        state = load_app_state(self.db_path, today=TODAY)

        assert state.is_completed_today is False

    def test_true_after_registering_today(self):
        mark_completed_db(
            self.habit_id, TODAY.isoformat(), db_path=self.db_path
        )

        state = load_app_state(self.db_path, today=TODAY)

        assert state.is_completed_today is True

    def test_false_without_selected_habit(self):
        assert AppState(today=TODAY).is_completed_today is False

    def test_false_when_only_another_day_is_registered(self):
        mark_completed_db(
            self.habit_id,
            (TODAY.replace(day=23)).isoformat(),
            db_path=self.db_path,
        )

        state = load_app_state(self.db_path, today=TODAY)

        assert state.is_completed_today is False
