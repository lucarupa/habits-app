# spec: 005-local-reminders
"""Verificación de los criterios de finalización de la spec 005 — Tarea 8.4.

Comprueba de extremo a extremo los criterios funcionales de la especificación
usando solo las APIs públicas de la lógica, la persistencia, el servicio y los
adaptadores del sistema. Los criterios de interfaz y de preservación de la
configuración ante fallos ya se ejercitan en `test_reminder_flow.py`; aquí se
verifican sin Flet para que también corran en la suite pura:

1. Configuración persistente con hora válida.
2. Un aviso diario para hábitos pendientes, también desde el runner.
3. Sin avisos para registrados, desactivados, futuros o eliminados; nombre actual.
4. Sin duplicados ni avisos retroactivos tras cambios, reinicios o fin del día.
5. Permisos y fallos del sistema comunicados en español sin excepciones.
6. Registros, rachas, estadísticas, heatmap y orden intactos.
7. Documentación pública de configuración, funcionamiento y límites.
"""

import os
import subprocess
import tempfile
from datetime import date, datetime

from habits.state.loader import load_app_state
from habits.notifications import (
    EXECUTION_FAILED_MESSAGE,
    PERMISSION_DENIED_MESSAGE,
    SCHEDULER_INSTALL_FAILED_MESSAGE,
    SCHEDULER_REMOVE_FAILED_MESSAGE,
    UNSUPPORTED_PLATFORM_MESSAGE,
    NotificationResult,
    SystemNotifier,
    SystemScheduler,
)
from habits.reminder_runner import run_check
from habits.reminder_service import DeliverySummary, deliver_due_reminders
from habits.reminders import (
    effective_date,
    reminder_message,
    validate_reminder_time,
)
from habits.persistence.completions_repo import mark_completed_db
from habits.persistence.habits_repo import (
    create_habit_db,
    delete_habit_db,
    update_habit_db,
)
from habits.persistence.reminders_repo import get_reminder_db, save_reminder_db
from habits.persistence.schema import init_db

NOW = datetime(2024, 10, 24, 9, 0)
TODAY = "2024-10-24"
START_DATE = "2024-09-01"


class RecordingNotifier:
    """Notificador simulado que registra los textos y confirma la entrega."""

    def __init__(self) -> None:
        self.messages: list[str] = []

    def notify(self, message: str) -> NotificationResult:
        """Registrar el aviso y confirmar que el sistema lo aceptó."""
        self.messages.append(message)
        return NotificationResult(ok=True)


def completed_process(
    returncode: int = 0, stderr: str = ""
) -> subprocess.CompletedProcess:
    """Construir el resultado de un comando del sistema simulado."""
    return subprocess.CompletedProcess(
        args=[], returncode=returncode, stdout="", stderr=stderr
    )


class TestFinalCriteria:
    """Criterios de finalización de la spec 005 — Tarea 8.4."""

    def setup_method(self):
        """Crear una base de datos temporal para cada escenario."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "final_verification.db")
        init_db(self.db_path)

    def teardown_method(self):
        """Eliminar la base de datos temporal al terminar."""
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def _create_habit(
        self, name: str = "Leer", start_date: str = START_DATE
    ) -> int:
        """Crear un hábito pendiente y devolver su identificador."""
        return create_habit_db(name, start_date, db_path=self.db_path)

    def _save_reminder(
        self,
        habit_id: int,
        *,
        enabled: bool = True,
        reminder_time: str | None = "09:00",
        effective_from: str = TODAY,
    ) -> None:
        """Guardar la configuración del recordatorio de un hábito."""
        save_reminder_db(
            habit_id,
            enabled,
            reminder_time,
            effective_from,
            db_path=self.db_path,
        )

    def test_criterion_1_configuration_is_valid_and_persists(self):
        """Criterio 1: hora válida y configuración conservada entre cargas."""
        habit_id = self._create_habit()

        initial = load_app_state(self.db_path, today=NOW.date())
        assert initial.selected is not None
        assert initial.selected.reminder_enabled is False
        assert initial.reminder_label == "Sin recordatorio"

        assert validate_reminder_time("07:30") == "07:30"
        assert validate_reminder_time("00:00") == "00:00"
        assert validate_reminder_time("23:59") == "23:59"
        for invalid in ("", "7:30", "24:00", "12:60", "abc", "07:30:00"):
            assert validate_reminder_time(invalid) is None

        self._save_reminder(habit_id, reminder_time="07:30")

        first_load = load_app_state(self.db_path, today=NOW.date())
        second_load = load_app_state(self.db_path, today=NOW.date())

        for state in (first_load, second_load):
            assert state.selected is not None
            assert state.selected.reminder_enabled is True
            assert state.selected.reminder_time == "07:30"
            assert state.reminder_label == "Recordatorio a las 07:30"

        reminder = get_reminder_db(habit_id, db_path=self.db_path)
        assert reminder is not None
        assert reminder.enabled is True
        assert reminder.reminder_time == "07:30"

    def test_criterion_2_pending_habit_gets_one_daily_reminder(self):
        """Criterio 2: un único aviso al día desde el runner periódico."""
        habit_id = self._create_habit("Leer")
        self._save_reminder(habit_id)
        notifier = RecordingNotifier()

        first = run_check(self.db_path, now=NOW, notifier=notifier)
        second = run_check(self.db_path, now=NOW, notifier=notifier)

        assert first == DeliverySummary(sent=[habit_id], errors=[])
        assert second == DeliverySummary(sent=[], errors=[])
        assert notifier.messages == [reminder_message("Leer")]
        assert "Leer" in notifier.messages[0]

    def test_criterion_3_skips_unusable_habits_and_uses_current_name(self):
        """Criterio 3: solo avisa hábitos pendientes, vigentes y existentes."""
        completed_id = self._create_habit("Completado")
        disabled_id = self._create_habit("Desactivado")
        future_id = self._create_habit("Futuro", start_date="2024-10-25")
        renamed_id = self._create_habit("Nombre antiguo")
        deleted_id = self._create_habit("Eliminado")

        for habit_id in (
            completed_id,
            disabled_id,
            future_id,
            renamed_id,
            deleted_id,
        ):
            self._save_reminder(habit_id)

        self._save_reminder(disabled_id, enabled=False)
        mark_completed_db(completed_id, TODAY, db_path=self.db_path)
        update_habit_db(
            renamed_id, "Nombre actual", START_DATE, db_path=self.db_path
        )
        delete_habit_db(deleted_id, db_path=self.db_path)
        notifier = RecordingNotifier()

        summary = run_check(self.db_path, now=NOW, notifier=notifier)

        assert summary.sent == [renamed_id]
        assert summary.errors == []
        assert notifier.messages == [reminder_message("Nombre actual")]
        assert get_reminder_db(deleted_id, db_path=self.db_path) is None

    def test_criterion_4_no_duplicates_or_retroactive_notices(self):
        """Criterio 4: cambios, reinicios y fin del día no duplican avisos."""
        habit_id = self._create_habit("Leer")
        self._save_reminder(habit_id, reminder_time="09:00")
        notifier = RecordingNotifier()

        first = deliver_due_reminders(NOW, self.db_path, notifier)
        assert first.sent == [habit_id]

        # Cambiar la hora después del aviso no lo repite ese mismo día.
        self._save_reminder(habit_id, reminder_time="18:00")
        same_day_later = datetime(2024, 10, 24, 18, 0)
        assert deliver_due_reminders(
            same_day_later, self.db_path, notifier
        ) == DeliverySummary()
        assert len(notifier.messages) == 1

        # Reiniciar la comprobación tampoco duplica el aviso.
        assert deliver_due_reminders(
            same_day_later, self.db_path, notifier
        ) == DeliverySummary()

        # Al día siguiente se usa la nueva hora y se avisa una sola vez.
        next_day = datetime(2024, 10, 25, 18, 0)
        assert deliver_due_reminders(next_day, self.db_path, notifier).sent == [
            habit_id
        ]
        assert len(notifier.messages) == 2

        # Pasada la medianoche no se recupera el aviso del día anterior.
        after_midnight = datetime(2024, 10, 26, 0, 1)
        assert deliver_due_reminders(
            after_midnight, self.db_path, notifier
        ) == DeliverySummary()
        assert len(notifier.messages) == 2

    def test_criterion_4_activation_after_time_waits_for_next_day(self):
        """Criterio 4: activar con la hora ya pasada no avisa de inmediato."""
        habit_id = self._create_habit("Leer")

        assert effective_date(NOW, "09:00") == date(2024, 10, 25)
        assert effective_date(datetime(2024, 10, 24, 8, 0), "09:00") == date(
            2024, 10, 24
        )

        self._save_reminder(
            habit_id, reminder_time="09:00", effective_from="2024-10-25"
        )
        notifier = RecordingNotifier()

        assert deliver_due_reminders(
            datetime(2024, 10, 24, 23, 59), self.db_path, notifier
        ) == DeliverySummary()
        assert notifier.messages == []

        assert deliver_due_reminders(
            datetime(2024, 10, 25, 9, 0), self.db_path, notifier
        ).sent == [habit_id]

    def test_criterion_5_permissions_and_failures_are_reported_in_spanish(self):
        """Criterio 5: permisos y fallos se comunican sin romper la aplicación."""
        denied = SystemNotifier(
            platform="darwin",
            runner=lambda _command: completed_process(
                1, "permission denied"
            ),
        ).notify("Aviso")

        assert denied.ok is False
        assert denied.permission_denied is True
        assert denied.message == PERMISSION_DENIED_MESSAGE
        assert "ajustes del sistema" in denied.message

        def raise_oserror(_command):
            raise OSError("sin acceso")

        failed = SystemNotifier(
            platform="win32", runner=raise_oserror
        ).notify("Aviso")
        assert failed.ok is False
        assert failed.message == EXECUTION_FAILED_MESSAGE
        assert "seguirá funcionando" in failed.message

        unsupported = SystemNotifier(platform="linux").notify("Aviso")
        assert unsupported.ok is False
        assert unsupported.message == UNSUPPORTED_PLATFORM_MESSAGE

        install_failure = SystemScheduler(
            platform="win32",
            runner=lambda _command: completed_process(1),
        ).sync(self.db_path, has_active_reminders=True)
        assert install_failure.ok is False
        assert install_failure.message == SCHEDULER_INSTALL_FAILED_MESSAGE

        remove_failure = SystemScheduler(
            platform="win32",
            runner=lambda _command: completed_process(1),
        ).sync(self.db_path, has_active_reminders=False)
        assert remove_failure.ok is False
        assert remove_failure.message == SCHEDULER_REMOVE_FAILED_MESSAGE

    def test_criterion_5_failed_scheduling_keeps_previous_configuration(self):
        """Criterio 5: un fallo del sistema no borra la configuración previa."""
        habit_id = self._create_habit("Leer")
        self._save_reminder(habit_id, reminder_time="09:00")

        result = SystemScheduler(
            platform="win32",
            runner=lambda _command: completed_process(1),
        ).sync(self.db_path, has_active_reminders=True)

        assert result.ok is False
        reminder = get_reminder_db(habit_id, db_path=self.db_path)
        assert reminder is not None
        assert reminder.enabled is True
        assert reminder.reminder_time == "09:00"

    def test_criterion_6_reminders_do_not_change_records_or_order(self):
        """Criterio 6: avisar no altera registros, rachas, heatmap ni orden."""
        first_id = self._create_habit("Alpha")
        second_id = self._create_habit("Zebra")
        mark_completed_db(first_id, TODAY, db_path=self.db_path)
        mark_completed_db(
            first_id, "2024-10-23", db_path=self.db_path
        )
        mark_completed_db(second_id, "2024-10-22", db_path=self.db_path)
        self._save_reminder(first_id)
        self._save_reminder(second_id)

        before = load_app_state(self.db_path, today=NOW.date())
        before_order = [habit.habit.id for habit in before.habits]
        before_selected = before.selected
        assert before_selected is not None
        before_stats = before_selected.stats
        before_completions = set(before_selected.completed_dates)
        before_heatmap = before.heatmap_cells()

        deliver_due_reminders(NOW, self.db_path, RecordingNotifier())

        after = load_app_state(self.db_path, today=NOW.date())
        after_selected = after.selected
        assert after_selected is not None
        assert [habit.habit.id for habit in after.habits] == before_order
        assert after_selected.habit.id == before_selected.habit.id
        assert after_selected.stats == before_stats
        assert after_selected.completed_dates == before_completions
        assert after.heatmap_cells() == before_heatmap
        assert after.is_completed_today is before.is_completed_today

    def test_criterion_7_readme_documents_reminders(self):
        """Criterio 7: la documentación pública describe configuración y límites."""
        readme = (
            os.path.join(os.path.dirname(__file__), os.pardir, "README.md")
        )
        with open(readme, encoding="utf-8") as handle:
            content = handle.read()

        assert "### Recordatorios locales" in content
        assert "Activar recordatorio" in content
        assert "HH:MM" in content
        assert "Sin recordatorio" in content
        assert "app cerrada" in content
        assert "macOS" in content
        assert "Windows" in content
        assert "un aviso al día" in content
        assert "pendiente" in content
        assert "duplicad" in content
