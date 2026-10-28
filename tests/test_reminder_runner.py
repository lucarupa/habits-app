# spec: 005-local-reminders
"""Tests del runner periódico de recordatorios — Tarea 5.3.

RF-2.1, RF-2.3 y RF-2.10: el runner lee la base indicada, usa la hora local,
devuelve el resumen del servicio y convierte un fallo en un código de salida
controlado con un mensaje en español.
"""

import os
import tempfile
from datetime import datetime

from habits.notifications.models import NotificationResult
from habits.reminder_runner import main, run_check
from habits.reminder_service import DeliverySummary
from habits.persistence.habits_repo import create_habit_db
from habits.persistence.reminders_repo import save_reminder_db
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


class TestRunCheck:
    """Composición del servicio por el runner — RF-2.1 y RF-2.3."""

    NOW = datetime(2024, 10, 24, 10, 0)

    def test_runner_uses_database_and_current_time(self, monkeypatch):
        """RF-2.1, RF-2.3: usa la base indicada y la hora local actual."""
        captured: dict = {}

        def fake_deliver(now, db_path, notifier):
            captured["now"] = now
            captured["db_path"] = db_path
            captured["notifier"] = notifier
            return DeliverySummary()

        monkeypatch.setattr(
            "habits.reminder_runner.deliver_due_reminders", fake_deliver
        )
        notifier = FakeNotifier()
        before = datetime.now()

        summary = run_check("custom/habits.db", notifier=notifier)

        after = datetime.now()
        assert summary == DeliverySummary()
        assert captured["db_path"] == "custom/habits.db"
        assert captured["notifier"] is notifier
        assert before <= captured["now"] <= after

    def test_runner_uses_explicit_time_and_returns_summary(self):
        """RF-2.1: devuelve el resumen del servicio para la hora indicada."""
        temp_dir = tempfile.mkdtemp()
        db_path = os.path.join(temp_dir, "test_reminders.db")
        try:
            init_db(db_path)
            habit_id = create_habit_db(
                "Leer", "2024-09-01", db_path=db_path
            )
            save_reminder_db(
                habit_id,
                True,
                "09:00",
                self.NOW.date().isoformat(),
                db_path=db_path,
            )
            notifier = FakeNotifier()

            summary = run_check(db_path, now=self.NOW, notifier=notifier)

            assert summary.sent == [habit_id]
            assert summary.errors == []
            assert len(notifier.messages) == 1
        finally:
            if os.path.exists(db_path):
                os.remove(db_path)

    def test_runner_uses_system_notifier_by_default(self, monkeypatch):
        """RF-2.3: sin notificador inyectado se usa el del sistema."""
        created: list[object] = []

        class RecordingNotifier:
            def __init__(self) -> None:
                created.append(self)

            def notify(self, message: str) -> NotificationResult:
                return NotificationResult(ok=True)

        monkeypatch.setattr(
            "habits.reminder_runner.SystemNotifier", RecordingNotifier
        )
        captured: dict = {}

        def fake_deliver(now, db_path, notifier):
            captured["notifier"] = notifier
            return DeliverySummary()

        monkeypatch.setattr(
            "habits.reminder_runner.deliver_due_reminders", fake_deliver
        )

        run_check("custom/habits.db")

        assert len(created) == 1
        assert captured["notifier"] is created[0]


class TestRunnerMain:
    """Entrada del runner y códigos de salida — RF-2.3 y RF-2.10."""

    NOW = datetime(2024, 10, 24, 10, 0)

    def test_main_parses_database_and_returns_zero(self, capsys):
        """RF-2.3: `--db` selecciona la base y un envío correcto sale con 0."""
        temp_dir = tempfile.mkdtemp()
        db_path = os.path.join(temp_dir, "test_reminders.db")
        try:
            init_db(db_path)
            habit_id = create_habit_db(
                "Leer", "2024-09-01", db_path=db_path
            )
            save_reminder_db(
                habit_id,
                True,
                "09:00",
                self.NOW.date().isoformat(),
                db_path=db_path,
            )
            notifier = FakeNotifier()

            exit_code = main(
                ["--db", db_path], now=self.NOW, notifier=notifier
            )

            captured = capsys.readouterr()
            assert exit_code == 0
            assert "Recordatorios enviados: 1" in captured.out
            assert len(notifier.messages) == 1
        finally:
            if os.path.exists(db_path):
                os.remove(db_path)

    def test_main_returns_one_when_delivery_reports_errors(
        self, monkeypatch, capsys
    ):
        """RF-2.3: los errores del servicio se muestran y salen con 1."""
        def fake_deliver(now, db_path, notifier):
            return DeliverySummary(
                sent=[],
                errors=["No se pudo enviar la notificación."],
            )

        monkeypatch.setattr(
            "habits.reminder_runner.deliver_due_reminders", fake_deliver
        )

        exit_code = main(
            ["--db", "data/habits.db"],
            now=self.NOW,
            notifier=FakeNotifier(),
        )

        captured = capsys.readouterr()
        assert exit_code == 1
        assert "No se pudo enviar la notificación." in captured.err

    def test_main_controls_a_service_failure(self, monkeypatch, capsys):
        """RF-2.10: un fallo del servicio no lanza excepción ni rompe el runner."""
        def failing_deliver(now, db_path, notifier):
            raise RuntimeError("database is locked")

        monkeypatch.setattr(
            "habits.reminder_runner.deliver_due_reminders", failing_deliver
        )

        exit_code = main(
            ["--db", "data/habits.db"],
            now=self.NOW,
            notifier=FakeNotifier(),
        )

        captured = capsys.readouterr()
        assert exit_code == 1
        assert "No se pudieron comprobar los recordatorios" in captured.err
        assert "database is locked" in captured.err

    def test_main_returns_zero_without_due_reminders(self, capsys):
        """RF-2.3: sin avisos pendientes el runner termina correctamente."""
        temp_dir = tempfile.mkdtemp()
        db_path = os.path.join(temp_dir, "test_reminders.db")
        try:
            init_db(db_path)

            exit_code = main(
                ["--db", db_path],
                now=self.NOW,
                notifier=FakeNotifier(),
            )

            captured = capsys.readouterr()
            assert exit_code == 0
            assert "Recordatorios enviados: 0" in captured.out
        finally:
            if os.path.exists(db_path):
                os.remove(db_path)

    def test_main_controls_a_missing_database(self, capsys):
        """RF-2.10: una base inexistente se comunica sin traza de error."""
        temp_dir = tempfile.mkdtemp()
        db_path = os.path.join(temp_dir, "missing.db")

        exit_code = main(
            ["--db", db_path],
            now=self.NOW,
            notifier=FakeNotifier(),
        )

        captured = capsys.readouterr()
        assert exit_code == 1
        assert "No se pudieron comprobar los recordatorios" in captured.err