# spec: 005-local-reminders
"""Tests del servicio de entrega de recordatorios — Tarea 5.1.

Cubren RF-2.1, RF-2.4, RF-2.6, RF-2.7, RF-2.8, RF-3.2, RF-3.3, RF-3.5,
RF-4.5 y RFN-7: solo se avisa a hábitos pendientes y vencidos, una vez por
hábito y día, con el nombre actualizado, liberando la reclamación si el envío
falla y sin alterar registros ni estadísticas.
"""

import os
import tempfile
from datetime import datetime, timedelta

from habits.state.loader import load_app_state
from habits.notifications import NotificationResult
from habits.reminder_service import DeliverySummary, deliver_due_reminders
from habits.reminders import reminder_message
from habits.persistence.completions_repo import mark_completed_db
from habits.persistence.habits_repo import create_habit_db, update_habit_db
from habits.persistence.reminders_repo import get_reminder_db, save_reminder_db
from habits.persistence.schema import init_db


class FakeNotifier:
    """Notificador simulado que registra los textos enviados."""

    def __init__(self, results: list[NotificationResult] | None = None) -> None:
        self.messages: list[str] = []
        self._results = list(results or [])

    def notify(self, message: str) -> NotificationResult:
        """Registrar el texto y devolver el siguiente resultado preparado."""
        self.messages.append(message)
        if self._results:
            return self._results.pop(0)
        return NotificationResult(ok=True)


class TestDeliverDueReminders:
    """Entrega periódica de recordatorios — Tarea 5.1."""

    NOW = datetime(2024, 10, 24, 10, 0)
    TODAY = "2024-10-24"

    def setup_method(self):
        """Crear una base de datos temporal para cada test."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_reminders.db")
        init_db(self.db_path)

    def teardown_method(self):
        """Limpiar la base de datos temporal después de cada test."""
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def _create_habit(
        self, name: str = "Leer", start_date: str = "2024-09-01"
    ) -> int:
        """Crear un hábito de prueba y devolver su identificador."""
        return create_habit_db(name, start_date, db_path=self.db_path)

    def _save_reminder(
        self,
        habit_id: int,
        enabled: bool = True,
        reminder_time: str | None = "09:00",
        effective_from: str = "2024-10-24",
    ) -> None:
        """Guardar una configuración de recordatorio para el hábito."""
        save_reminder_db(
            habit_id,
            enabled,
            reminder_time,
            effective_from,
            db_path=self.db_path,
        )

    def test_service_notifies_only_pending_habits(self):
        """RF-2.1, RF-2.4: avisa al pendiente y omite el ya registrado."""
        pending_id = self._create_habit("Leer")
        completed_id = self._create_habit("Python")
        self._save_reminder(pending_id)
        self._save_reminder(completed_id)
        mark_completed_db(
            completed_id, self.TODAY, db_path=self.db_path
        )
        notifier = FakeNotifier()

        summary = deliver_due_reminders(self.NOW, self.db_path, notifier)

        assert summary.sent == [pending_id]
        assert summary.errors == []
        assert notifier.messages == [reminder_message("Leer")]

    def test_service_sends_one_notification_per_habit_and_day(self):
        """RF-2.7, RFN-7: repetir la comprobación no duplica el aviso."""
        habit_id = self._create_habit("Leer")
        self._save_reminder(habit_id)
        notifier = FakeNotifier()

        first = deliver_due_reminders(self.NOW, self.db_path, notifier)
        second = deliver_due_reminders(self.NOW, self.db_path, notifier)

        assert first.sent == [habit_id]
        assert second == DeliverySummary(sent=[], errors=[])
        assert len(notifier.messages) == 1
        reminder = get_reminder_db(habit_id, db_path=self.db_path)
        assert reminder is not None
        assert reminder.last_notified_on == self.TODAY

    def test_service_uses_current_habit_name(self):
        """RF-3.5: el aviso usa el nombre actualizado del hábito."""
        habit_id = self._create_habit("Leer")
        self._save_reminder(habit_id)
        update_habit_db(
            habit_id,
            "Leer filosofía",
            "2024-09-01",
            db_path=self.db_path,
        )
        notifier = FakeNotifier()

        deliver_due_reminders(self.NOW, self.db_path, notifier)

        assert notifier.messages == [reminder_message("Leer filosofía")]

    def test_service_ignores_future_effective_date(self):
        """RF-3.6: no se avisa antes de la fecha efectiva."""
        habit_id = self._create_habit("Leer")
        self._save_reminder(habit_id, effective_from="2024-10-25")
        notifier = FakeNotifier()

        summary = deliver_due_reminders(self.NOW, self.db_path, notifier)

        assert summary == DeliverySummary(sent=[], errors=[])
        assert notifier.messages == []

    def test_service_releases_claim_when_delivery_fails(self):
        """RF-4.5, RFN-7: un fallo libera la entrega para poder reintentar."""
        habit_id = self._create_habit("Leer")
        self._save_reminder(habit_id)
        notifier = FakeNotifier(
            results=[
                NotificationResult(
                    ok=False,
                    message="No se pudo enviar la notificación.",
                ),
                NotificationResult(ok=True),
            ]
        )

        failed = deliver_due_reminders(self.NOW, self.db_path, notifier)

        assert failed.sent == []
        assert failed.errors == ["No se pudo enviar la notificación."]
        reminder = get_reminder_db(habit_id, db_path=self.db_path)
        assert reminder is not None
        assert reminder.last_notified_on is None

        retried = deliver_due_reminders(self.NOW, self.db_path, notifier)

        assert retried.sent == [habit_id]
        assert retried.errors == []
        assert len(notifier.messages) == 2

    def test_service_does_not_change_habit_stats(self):
        """RF-2.8: avisar no marca el hábito ni altera racha ni estadísticas."""
        habit_id = self._create_habit("Leer")
        yesterday = self.NOW.date() - timedelta(days=1)
        mark_completed_db(
            habit_id, yesterday.isoformat(), db_path=self.db_path
        )
        self._save_reminder(habit_id)
        before = load_app_state(self.db_path, today=self.NOW.date())
        notifier = FakeNotifier()

        deliver_due_reminders(self.NOW, self.db_path, notifier)

        after = load_app_state(self.db_path, today=self.NOW.date())
        assert after.selected is not None
        assert before.selected is not None
        assert after.selected.completed_dates == {yesterday}
        assert after.selected.stats == before.selected.stats
        assert after.selected.habit.id == habit_id
        assert after.is_completed_today is False

    def test_service_sends_one_notification_per_habit_sharing_time(self):
        """RF-2.6: dos hábitos a la misma hora generan dos avisos."""
        first_id = self._create_habit("Alpha")
        second_id = self._create_habit("Zebra")
        self._save_reminder(first_id, reminder_time="09:00")
        self._save_reminder(second_id, reminder_time="09:00")
        notifier = FakeNotifier()

        summary = deliver_due_reminders(self.NOW, self.db_path, notifier)

        assert set(summary.sent) == {first_id, second_id}
        assert set(notifier.messages) == {
            reminder_message("Alpha"),
            reminder_message("Zebra"),
        }

    def test_service_skips_after_time_change_on_the_same_day(self):
        """RF-3.2: cambiar la hora tras el aviso no lo repite ese día."""
        habit_id = self._create_habit("Leer")
        self._save_reminder(habit_id, reminder_time="09:00")
        notifier = FakeNotifier()
        deliver_due_reminders(self.NOW, self.db_path, notifier)

        self._save_reminder(habit_id, reminder_time="09:30")
        summary = deliver_due_reminders(self.NOW, self.db_path, notifier)

        assert summary == DeliverySummary(sent=[], errors=[])
        assert len(notifier.messages) == 1

    def test_service_skips_disabled_reminder_before_its_time(self):
        """RF-3.3: desactivar antes de la hora cancela el aviso del día."""
        habit_id = self._create_habit("Leer")
        self._save_reminder(habit_id, enabled=False)
        notifier = FakeNotifier()

        summary = deliver_due_reminders(self.NOW, self.db_path, notifier)

        assert summary == DeliverySummary(sent=[], errors=[])
        assert notifier.messages == []

    def test_service_returns_empty_summary_without_reminders(self):
        """RFN-7: sin recordatorios no hay envíos ni errores."""
        notifier = FakeNotifier()

        summary = deliver_due_reminders(self.NOW, self.db_path, notifier)

        assert summary == DeliverySummary(sent=[], errors=[])
        assert notifier.messages == []