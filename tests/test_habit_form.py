# spec: 002-ui-redesign
# spec: 003-edit-delete-habits
"""Tests de la lógica del formulario de creación — Fase 4.

Cubre RF-2.2, RF-2.3, RF-2.4, RF-2.5, RF-2.6, RF-2.7, RF-2.9 y RF-2.10.
"""

import os
import tempfile
from datetime import date, timedelta

import pytest

from habits import habit_form
from habits.app_state import load_app_state
from habits.domain.models import ALLOWED_ICONS, DEFAULT_ICON, Habit
from habits.habit_form import (
    DATE_FORMAT_ERROR,
    ICON_CATALOG,
    ICON_LABELS,
    MAX_NAME_LENGTH,
    NAME_REQUIRED_ERROR,
    NAME_TOO_LONG_ERROR,
    CreateHabitResult,
    HabitFormData,
    HabitFormResult,
    create_habit_from_form,
    normalize_icon,
    parse_start_date,
    validate_habit_form,
)
from habits.storage import (
    create_habit_db,
    get_completions_db,
    get_habit_db,
    init_db,
    list_all_habits_db,
    mark_completed_db,
)

TODAY = date(2024, 10, 24)


class TestIconCatalog:
    """Tests del catálogo de iconos — RF-2.6."""

    def test_catalog_covers_all_allowed_icons(self):
        """RF-2.6: El selector ofrece todos los iconos permitidos."""
        assert set(ICON_CATALOG) == set(ALLOWED_ICONS)
        assert DEFAULT_ICON in ICON_CATALOG

    def test_every_icon_has_a_spanish_label(self):
        """RF-2.6: Cada icono del catálogo tiene una etiqueta visible."""
        assert set(ICON_LABELS) == set(ICON_CATALOG)
        assert all(label.strip() for label in ICON_LABELS.values())

    def test_normalize_keeps_valid_icon(self):
        """RF-2.6: Un icono válido se conserva."""
        assert normalize_icon("code") == "code"

    @pytest.mark.parametrize("value", [None, "", "unknown"])
    def test_normalize_falls_back_to_default(self, value):
        """RF-2.6: Un icono ausente o inválido usa el valor por defecto."""
        assert normalize_icon(value) == DEFAULT_ICON


class TestParseStartDate:
    """Tests del parseo de la fecha opcional — RF-2.4, RF-2.5, RF-2.10."""

    @pytest.mark.parametrize("value", ["", "   "])
    def test_blank_date_uses_today(self, value):
        """RF-2.4: Sin fecha se asigna la fecha actual."""
        assert parse_start_date(value, today=TODAY) == TODAY

    def test_parses_valid_dd_mm_yyyy_date(self):
        """RF-2.10: Una fecha válida en dd/mm/aaaa se interpreta bien."""
        assert parse_start_date("05/01/2024", today=TODAY) == date(2024, 1, 5)

    def test_today_is_accepted(self):
        """RF-2.10: La fecha actual es válida."""
        assert parse_start_date("24/10/2024", today=TODAY) == TODAY

    def test_future_date_falls_back_to_today(self):
        """RF-2.5: Una fecha futura se corrige a la fecha actual."""
        future = (TODAY + timedelta(days=10)).strftime("%d/%m/%Y")

        assert parse_start_date(future, today=TODAY) == TODAY

    @pytest.mark.parametrize(
        "value",
        [
            "2024-01-05",
            "1/2/2024",
            "05/01/24",
            "31/02/2024",
            "05/13/2024",
            "00/01/2024",
            "texto",
        ],
    )
    def test_invalid_date_raises_with_spanish_message(self, value):
        """RF-2.10: Una fecha inválida produce el mensaje esperado."""
        with pytest.raises(ValueError, match=DATE_FORMAT_ERROR):
            parse_start_date(value, today=TODAY)


class TestValidateHabitForm:
    """Tests de las validaciones del formulario — RF-2.2, RF-2.3, RF-2.10."""

    @pytest.mark.parametrize("name", ["", "   "])
    def test_empty_name_is_rejected(self, name):
        """RF-2.2: El nombre vacío muestra el mensaje obligatorio."""
        data = HabitFormData(name=name)

        with pytest.raises(ValueError, match=NAME_REQUIRED_ERROR):
            validate_habit_form(data, today=TODAY)

    def test_name_over_sixty_characters_is_rejected(self):
        """RF-2.3: Más de 60 caracteres muestra el mensaje de longitud."""
        data = HabitFormData(name="a" * (MAX_NAME_LENGTH + 1))

        with pytest.raises(ValueError, match=NAME_TOO_LONG_ERROR):
            validate_habit_form(data, today=TODAY)

    def test_exactly_sixty_characters_is_allowed(self):
        """RF-2.3: El límite de 60 caracteres es inclusivo."""
        data = HabitFormData(name="a" * MAX_NAME_LENGTH)

        result = validate_habit_form(data, today=TODAY)

        assert result.name == "a" * MAX_NAME_LENGTH

    def test_name_is_trimmed(self):
        """RF-2.2: El nombre se guarda sin espacios sobrantes."""
        result = validate_habit_form(
            HabitFormData(name="  Estudiar Python  "), today=TODAY
        )

        assert result.name == "Estudiar Python"

    def test_valid_icon_is_preserved(self):
        """RF-2.6: El icono elegido se conserva."""
        result = validate_habit_form(
            HabitFormData(name="Leer", icon="science"), today=TODAY
        )

        assert result.icon == "science"

    @pytest.mark.parametrize("icon", [None, "", "unknown"])
    def test_missing_icon_uses_default(self, icon):
        """RF-2.6: Sin selección de icono se usa el valor por defecto."""
        result = validate_habit_form(
            HabitFormData(name="Leer", icon=icon), today=TODAY
        )

        assert result.icon == DEFAULT_ICON

    def test_blank_date_uses_today(self):
        """RF-2.4: El formulario sin fecha usa la fecha actual."""
        result = validate_habit_form(
            HabitFormData(name="Leer", start_date=""), today=TODAY
        )

        assert result.start_date == TODAY

    def test_future_date_uses_today(self):
        """RF-2.5: El formulario con fecha futura usa la fecha actual."""
        future = (TODAY + timedelta(days=1)).strftime("%d/%m/%Y")

        result = validate_habit_form(
            HabitFormData(name="Leer", start_date=future), today=TODAY
        )

        assert result.start_date == TODAY

    def test_returns_form_result(self):
        """El resultado agrupa nombre normalizado, fecha e icono."""
        result = validate_habit_form(
            HabitFormData(
                name="  Leer  ",
                start_date="01/09/2024",
                icon="book",
            ),
            today=TODAY,
        )

        assert result == HabitFormResult(
            name="Leer",
            start_date=date(2024, 9, 1),
            icon="book",
        )


class TestCreateHabitFromForm:
    """Tests de persistencia desde el formulario — RF-2.7, RF-2.9."""

    def setup_method(self):
        """Crear una base de datos temporal para cada test."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_habits.db")
        init_db(self.db_path)

    def teardown_method(self):
        """Limpiar la base de datos temporal después de cada test."""
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_persists_name_date_and_icon(self):
        """RF-2.7, RF-2.9: Guarda nombre, fecha e icono y devuelve el ID."""
        result = create_habit_from_form(
            HabitFormData(
                name="Estudiar Python",
                start_date="01/09/2024",
                icon="code",
            ),
            db_path=self.db_path,
            today=TODAY,
        )

        assert isinstance(result, CreateHabitResult)
        assert result.habit_id > 0
        assert result.name == "Estudiar Python"
        assert result.start_date == date(2024, 9, 1)
        assert result.icon == "code"

        row = get_habit_db(result.habit_id, self.db_path)
        assert row is not None
        assert row.name == "Estudiar Python"
        assert row.start_date == "2024-09-01"
        assert row.icon == "code"

    def test_blank_date_persists_today(self):
        """RF-2.4: Sin fecha se persiste la fecha actual."""
        result = create_habit_from_form(
            HabitFormData(name="Leer"),
            db_path=self.db_path,
            today=TODAY,
        )

        row = get_habit_db(result.habit_id, self.db_path)
        assert row is not None
        assert row.start_date == TODAY.isoformat()

    def test_missing_icon_persists_default(self):
        """RF-2.6: Sin icono se persiste el icono por defecto."""
        result = create_habit_from_form(
            HabitFormData(name="Leer", icon=""),
            db_path=self.db_path,
            today=TODAY,
        )

        row = get_habit_db(result.habit_id, self.db_path)
        assert row is not None
        assert row.icon == DEFAULT_ICON

    def test_validation_error_does_not_persist(self):
        """RF-2.2, RF-2.3, RF-2.10: Un error no crea el hábito."""
        with pytest.raises(ValueError):
            create_habit_from_form(
                HabitFormData(name="   "),
                db_path=self.db_path,
                today=TODAY,
            )

        assert list_all_habits_db(self.db_path) == []

    def test_created_habit_appears_selected_in_app_state(self):
        """RF-2.7, RF-6.3: Tras crear, el hábito aparece y puede seleccionarse."""
        result = create_habit_from_form(
            HabitFormData(name="Leer", icon="book"),
            db_path=self.db_path,
            today=TODAY,
        )

        state = load_app_state(self.db_path, today=TODAY)

        assert not state.is_empty
        assert state.empty_state() is None
        assert state.selected_id == result.habit_id

        state.select(result.habit_id)
        header = state.detail_header()
        assert header is not None
        assert header.name == "Leer"
        assert header.icon == "book"


class TestValidateHabitUpdate:
    """Tests de validate_habit_update() — Tarea 3.1, RF-2.3, RF-2.5, RF-2.7, RF-2.8."""

    def _habit(self) -> Habit:
        """Hábito de referencia con datos anteriores a TODAY."""
        return Habit(
            id=1,
            name="Python",
            start_date=date(2024, 9, 1),
            icon="code",
        )

    def test_validate_update_keeps_current_date_when_empty(self):
        """RF-2.5: Sin fecha nueva se conserva la fecha actual del hábito."""
        habit = self._habit()

        result = habit_form.validate_habit_update(
            habit,
            HabitFormData(
                name="Python avanzado",
                start_date="",
                icon=None,
            ),
            today=TODAY,
        )

        assert result.start_date == habit.start_date
        assert result.name == "Python avanzado"
        assert result.icon == "code"

    def test_validate_update_rejects_future_date(self):
        """RF-2.7: Una fecha futura se rechaza al editar."""
        habit = self._habit()
        future = (TODAY + timedelta(days=1)).strftime("%d/%m/%Y")

        with pytest.raises(ValueError, match="futura"):
            habit_form.validate_habit_update(
                habit,
                HabitFormData(name="Python", start_date=future),
                today=TODAY,
            )

    def test_validate_update_keeps_current_icon_when_missing(self):
        """RF-2.8: Sin icono se conserva el icono actual del hábito."""
        habit = self._habit()

        for icon in (None, ""):
            result = habit_form.validate_habit_update(
                habit,
                HabitFormData(name="Python", icon=icon),
                today=TODAY,
            )

            assert result.icon == "code"

    def test_validate_update_rejects_empty_name(self):
        """RF-2.3: Nombre vacío o solo espacios lanza error."""
        habit = self._habit()

        for name in ("", "   "):
            with pytest.raises(ValueError, match=NAME_REQUIRED_ERROR):
                habit_form.validate_habit_update(
                    habit,
                    HabitFormData(name=name),
                    today=TODAY,
                )


class TestUpdateHabitFromForm:
    """Tests de update_habit_from_form() — Tarea 3.1, RF-2.9, RF-2.12, RF-2.14."""

    def setup_method(self):
        """Crear una base de datos temporal para cada test."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_habits.db")
        init_db(self.db_path)

    def teardown_method(self):
        """Limpiar la base de datos temporal después de cada test."""
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def _stored_habit(self) -> Habit:
        """Persistir un hábito de referencia y devolverlo como Habit."""
        habit_id = create_habit_db(
            "Python", "2024-09-01", icon="code", db_path=self.db_path
        )
        return Habit(
            id=habit_id,
            name="Python",
            start_date=date(2024, 9, 1),
            icon="code",
        )

    def test_update_habit_from_form_persists_changes(self):
        """RF-2.9, RF-2.14: Guarda los cambios y devuelve el resultado."""
        habit = self._stored_habit()

        result = habit_form.update_habit_from_form(
            habit,
            HabitFormData(
                name="Python avanzado",
                start_date="01/10/2024",
                icon="science",
            ),
            db_path=self.db_path,
            today=TODAY,
        )

        assert result == habit_form.UpdateHabitResult(
            habit_id=habit.id,
            name="Python avanzado",
            start_date=date(2024, 10, 1),
            icon="science",
        )

        row = get_habit_db(habit.id, self.db_path)
        assert row is not None
        assert row.name == "Python avanzado"
        assert row.start_date == "2024-10-01"
        assert row.icon == "science"

    def test_update_habit_from_form_does_not_touch_completions(self):
        """RF-2.12: Los registros diarios permanecen intactos tras editar."""
        habit = self._stored_habit()
        mark_completed_db(habit.id, "2024-10-20", self.db_path)
        mark_completed_db(habit.id, "2024-10-21", self.db_path)

        habit_form.update_habit_from_form(
            habit,
            HabitFormData(
                name="Python avanzado",
                start_date="",
                icon="science",
            ),
            db_path=self.db_path,
            today=TODAY,
        )

        assert get_completions_db(habit.id, self.db_path) == [
            "2024-10-20",
            "2024-10-21",
        ]
        row = get_habit_db(habit.id, self.db_path)
        assert row is not None
        assert row.name == "Python avanzado"
        assert row.icon == "science"
