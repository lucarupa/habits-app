# spec: 005-local-reminders
"""Tests de la lógica pura de recordatorios — Tarea 1.1.

Cubre RF-1.1, RF-1.2, RF-1.6, RF-2.2, RF-3.1 y RF-3.6. No requieren Flet ni
SQLite: describen el contrato de `habits/reminders.py` antes de implementarlo.
"""

from datetime import date, datetime

import pytest

from habits.reminders import (
    effective_date,
    is_due,
    reminder_label,
    reminder_message,
    validate_reminder_time,
)

NOW = datetime(2024, 10, 24, 9, 0)


class TestValidateReminderTime:
    """Validación de la hora local — RF-1.2 y RF-1.6."""

    @pytest.mark.parametrize("value", ["00:00", "09:05", "12:30", "23:59"])
    def test_validate_reminder_time_accepts_valid_hours(self, value):
        """RF-1.2: una hora HH:MM dentro del rango es válida."""
        assert validate_reminder_time(value) == value

    def test_validate_reminder_time_trims_surrounding_spaces(self):
        """RF-1.2: los espacios exteriores no invalidan la hora."""
        assert validate_reminder_time("  20:00  ") == "20:00"

    @pytest.mark.parametrize(
        "value",
        [
            "",
            "   ",
            "24:00",
            "23:60",
            "9:5",
            "9:05",
            "20:0",
            "20",
            "20:00:00",
            "ocho",
            "12:ab",
        ],
    )
    def test_validate_reminder_time_rejects_invalid_values(self, value):
        """RF-1.6: vacío, incompleto o fuera de rango no es válido."""
        assert validate_reminder_time(value) is None


class TestReminderLabel:
    """Etiqueta visible del estado del recordatorio — RF-1.1."""

    def test_label_of_disabled_reminder(self):
        """RF-1.1: sin recordatorio activo se muestra “Sin recordatorio”."""
        assert reminder_label(enabled=False, reminder_time=None) == "Sin recordatorio"

    def test_label_of_disabled_reminder_ignores_stored_time(self):
        """RF-1.1: desactivado se muestra desactivado aunque conserve la hora."""
        assert reminder_label(enabled=False, reminder_time="20:00") == "Sin recordatorio"

    def test_label_of_active_reminder_shows_the_time(self):
        """RF-1.1: activo muestra la hora configurada en HH:MM."""
        assert reminder_label(enabled=True, reminder_time="09:05") == (
            "Recordatorio a las 09:05"
        )

    def test_label_of_active_reminder_without_time_is_disabled(self):
        """RF-1.1: activo sin hora no puede mostrarse como activo."""
        assert reminder_label(enabled=True, reminder_time=None) == "Sin recordatorio"


class TestEffectiveDate:
    """Fecha desde la que puede avisar un recordatorio — RF-3.1 y RF-3.6."""

    def test_effective_date_is_today_before_time(self):
        """RF-3.1: una hora aún no alcanzada puede avisar hoy."""
        assert effective_date(NOW, "10:00") == date(2024, 10, 24)

    def test_effective_date_is_tomorrow_after_time(self):
        """RF-3.6: una hora ya pasada empieza a avisar mañana."""
        assert effective_date(NOW, "08:00") == date(2024, 10, 25)

    def test_effective_date_is_tomorrow_when_time_is_now(self):
        """RF-3.6: la hora actual ya se considera pasada, sin aviso inmediato."""
        assert effective_date(NOW, "09:00") == date(2024, 10, 25)

    def test_effective_date_rolls_over_month_and_year(self):
        """RF-3.6: el cálculo de mañana cruza fin de mes y de año."""
        last_day = datetime(2024, 12, 31, 23, 0)

        assert effective_date(last_day, "22:30") == date(2025, 1, 1)


class TestReminderMessage:
    """Texto exacto de la notificación — RF-2.2."""

    def test_reminder_message_includes_habit_name(self):
        """RF-2.2: el texto es exacto, en español e incluye el nombre."""
        assert reminder_message("Leer 30 minutos") == (
            "⏰ No olvides registrar «Leer 30 minutos» hoy."
        )

    def test_reminder_message_keeps_names_with_accents_and_symbols(self):
        """RF-2.2: el nombre visible se conserva tal cual."""
        assert "Programación & Álgebra" in reminder_message("Programación & Álgebra")

    def test_reminder_message_is_in_spanish(self):
        """RF-2.2: el texto usa vocabulario en español."""
        message = reminder_message("Practicar guitarra")

        assert "registrar" in message
        assert "hoy" in message


def due_reminder(**overrides):
    """Construir los datos de un recordatorio que vence con `NOW`."""
    values = {
        "enabled": True,
        "reminder_time": "09:00",
        "effective_from": date(2024, 10, 20),
        "start_date": date(2024, 10, 1),
        "last_notified_on": None,
        "completed_today": False,
    }
    values.update(overrides)
    return values


class TestIsDue:
    """Vencimiento del recordatorio — RF-2.1, RF-2.4, RF-2.5, RF-2.7, RF-2.9, RF-2.10."""

    def test_is_due_when_enabled_time_reached_and_valid(self):
        """RF-2.1: activo, hora alcanzada y fechas vigentes vence."""
        assert is_due(NOW, **due_reminder()) is True

    def test_is_due_when_time_is_exactly_now(self):
        """RF-2.1: la hora configurada ya alcanzada cuenta como vencida."""
        assert is_due(NOW, **due_reminder(reminder_time="09:00")) is True

    def test_is_due_is_false_when_disabled(self):
        """RF-2.5: un recordatorio desactivado no vence."""
        assert is_due(NOW, **due_reminder(enabled=False)) is False

    def test_is_due_is_false_before_the_configured_time(self):
        """RF-2.1: antes de la hora configurada todavía no vence."""
        assert is_due(NOW, **due_reminder(reminder_time="10:00")) is False

    def test_is_due_is_false_when_active_without_time(self):
        """RF-1.6: activo sin hora válida no puede vencer."""
        assert is_due(NOW, **due_reminder(reminder_time=None)) is False

    def test_is_due_is_false_before_effective_date(self):
        """RF-2.1: la vigencia empieza en `effective_from`."""
        assert is_due(NOW, **due_reminder(effective_from=date(2024, 10, 25))) is False

    def test_is_due_is_true_on_effective_date(self):
        """RF-2.1: el mismo día de la fecha efectiva ya puede vencer."""
        assert is_due(NOW, **due_reminder(effective_from=date(2024, 10, 24))) is True

    def test_is_due_is_false_before_habit_start_date(self):
        """RF-2.9: no se avisa antes de la fecha de inicio del hábito."""
        assert is_due(NOW, **due_reminder(start_date=date(2024, 10, 25))) is False

    def test_is_due_is_true_on_habit_start_date(self):
        """RF-2.9: el día de inicio del hábito ya puede vencer."""
        assert is_due(NOW, **due_reminder(start_date=date(2024, 10, 24))) is True

    def test_is_due_is_false_when_completed_today(self):
        """RF-2.4: un hábito ya registrado hoy no genera aviso."""
        assert is_due(NOW, **due_reminder(completed_today=True)) is False

    def test_is_due_is_false_when_already_notified_today(self):
        """RF-2.7: no se repite el aviso del mismo día local."""
        assert is_due(NOW, **due_reminder(last_notified_on=date(2024, 10, 24))) is False

    def test_is_due_is_true_when_last_notification_was_yesterday(self):
        """RF-2.7: el aviso de ayer no bloquea el de hoy."""
        assert is_due(NOW, **due_reminder(last_notified_on=date(2024, 10, 23))) is True

    def test_is_due_is_true_when_overdue_same_day(self):
        """RF-2.10: una hora pasada sigue vencida durante el mismo día."""
        assert is_due(NOW, **due_reminder(reminder_time="07:00")) is True

    def test_is_due_is_false_after_day_changed(self):
        """RF-2.10: nunca se envía un aviso retroactivo de otro día."""
        next_day = datetime(2024, 10, 25, 0, 30)

        assert is_due(next_day, **due_reminder(reminder_time="22:00")) is False
