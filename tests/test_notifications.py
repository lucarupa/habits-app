# spec: 005-local-reminders
"""Tests del adaptador de notificaciones — Tarea 4.1.

RF-2.3, RF-4.1, RF-4.2, RF-4.3 y RFN-5: construye los comandos de macOS y
Windows, envía el texto del recordatorio y traduce los fallos de permiso o de
ejecución a resultados controlados en español, usando un ejecutor simulado.
"""

import plistlib
import subprocess
from collections.abc import Callable

import pytest

from habits.notifications import (
    NOTIFICATION_TITLE,
    SCHEDULER_TASK_LABEL,
    SCHEDULER_TASK_NAME,
    NotificationResult,
    SchedulerResult,
    SystemNotifier,
    SystemScheduler,
)
from habits.reminders import reminder_message


def completed(returncode: int = 0, stderr: str = "") -> subprocess.CompletedProcess:
    """Construir un resultado de proceso simulado."""
    return subprocess.CompletedProcess(
        args=[],
        returncode=returncode,
        stdout="",
        stderr=stderr,
    )


def joined(command: list[str]) -> str:
    """Unir un comando en un único texto para inspeccionarlo."""
    return " ".join(command)


class TestNotifierCommands:
    """Construcción de los comandos por plataforma — RF-2.3 y RFN-5."""

    def test_notifier_builds_macos_command(self):
        """RF-2.3, RFN-5: macOS usa osascript con el texto en español."""
        notifier = SystemNotifier(platform="darwin")
        message = reminder_message("Leer")

        command = notifier.build_command(message)

        assert command[0] == "osascript"
        assert command[1] == "-e"
        assert "display notification" in command[2]
        assert message in command[2]
        assert NOTIFICATION_TITLE in command[2]

    def test_notifier_builds_windows_command(self):
        """RF-2.3, RFN-5: Windows usa PowerShell con una notificación toast."""
        notifier = SystemNotifier(platform="win32")
        message = reminder_message("Estudiar Python")

        command = notifier.build_command(message)
        text = joined(command)

        assert command[0].lower() in {"powershell", "powershell.exe"}
        assert "-NoProfile" in command
        assert "ToastNotification" in text
        assert message in text
        assert NOTIFICATION_TITLE in text

    def test_notifier_escapes_macos_quotes(self):
        """RF-2.3: un nombre con comillas no rompe el comando de macOS."""
        notifier = SystemNotifier(platform="darwin")
        message = reminder_message('Leer "Python"')

        command = notifier.build_command(message)

        assert '\\"Python\\"' in command[2]

    def test_notifier_rejects_unsupported_platform(self):
        """RFN-5: Linux y otros sistemas quedan fuera y se informa en español."""
        notifier = SystemNotifier(platform="linux")

        with pytest.raises(ValueError):
            notifier.build_command(reminder_message("Leer"))

        result = notifier.notify(reminder_message("Leer"))

        assert isinstance(result, NotificationResult)
        assert result.ok is False
        assert "macos" in result.message.lower()
        assert "windows" in result.message.lower()


class TestNotifierDelivery:
    """Envío y traducción de errores — RF-4.1, RF-4.2 y RF-4.3."""

    def test_notifier_returns_success_and_runs_the_command(self):
        """RF-4.1: espera el resultado del sistema antes de confirmar."""
        captured: list[list[str]] = []

        def runner(command: list[str]) -> subprocess.CompletedProcess:
            captured.append(command)
            return completed()

        notifier = SystemNotifier(platform="darwin", runner=runner)
        message = reminder_message("Leer")

        result = notifier.notify(message)

        assert result == NotificationResult(ok=True)
        assert captured == [notifier.build_command(message)]

    @pytest.mark.parametrize(
        ("platform", "stderr"),
        [
            ("darwin", "execution error: Not allowed to send notification. (-1743)"),
            ("win32", "Access is denied. (0x80070005)"),
        ],
        ids=["macos", "windows"],
    )
    def test_notifier_reports_permission_error(self, platform, stderr):
        """RF-4.2, RF-4.3: el permiso denegado se explica en español."""
        notifier = SystemNotifier(
            platform=platform,
            runner=lambda command: completed(returncode=1, stderr=stderr),
        )

        result = notifier.notify(reminder_message("Leer"))

        assert result.ok is False
        assert result.permission_denied is True
        assert "permiso" in result.message.lower()
        assert "notificaciones" in result.message.lower()

    def test_notifier_reports_execution_error(self):
        """RF-4.3: un fallo de ejecución no rompe la app y se informa."""
        notifier = SystemNotifier(
            platform="darwin",
            runner=lambda command: completed(
                returncode=1,
                stderr="The operation could not be completed.",
            ),
        )

        result = notifier.notify(reminder_message("Leer"))

        assert result.ok is False
        assert result.permission_denied is False
        assert "no se pudo" in result.message.lower()

    def test_notifier_reports_missing_command(self):
        """RF-4.3: si el comando del sistema no existe, devuelve un fallo."""
        def runner(command: list[str]) -> subprocess.CompletedProcess:
            raise FileNotFoundError("osascript")

        notifier = SystemNotifier(platform="darwin", runner=runner)

        result = notifier.notify(reminder_message("Leer"))

        assert result.ok is False
        assert result.permission_denied is False
        assert "no se pudo" in result.message.lower()

    def test_notifier_does_not_run_on_unsupported_platform(self):
        """RFN-5: sin plataforma compatible no se ejecuta ningún comando."""
        called: list[list[str]] = []

        def runner(command: list[str]) -> subprocess.CompletedProcess:
            called.append(command)
            return completed()

        notifier = SystemNotifier(platform="linux", runner=runner)

        result = notifier.notify(reminder_message("Leer"))

        assert result.ok is False
        assert called == []


def recording_runner(
    result: subprocess.CompletedProcess | None = None,
) -> tuple[list[list[str]], Callable[[list[str]], subprocess.CompletedProcess]]:
    """Crear un ejecutor que registra los comandos recibidos."""
    calls: list[list[str]] = []
    response = result

    def runner(command: list[str]) -> subprocess.CompletedProcess:
        calls.append(command)
        return response if response is not None else completed()

    return calls, runner


class TestScheduler:
    """Instalación, actualización y retirada del planificador.

    RF-2.3, RF-3.4 y RF-4.4: una única tarea periódica por plataforma, con
    actualización idempotente y errores controlados en español.
    """

    def test_scheduler_installs_single_minute_task_on_windows(self):
        """RF-2.3: Windows crea una tarea `schtasks` cada minuto."""
        calls, runner = recording_runner()
        scheduler = SystemScheduler(
            platform="win32",
            runner=runner,
            python_executable=r"C:\Python312\python.exe",
        )

        result = scheduler.sync(
            r"C:\proyectos\habits-app\data\habits.db",
            has_active_reminders=True,
        )

        assert result == SchedulerResult(ok=True)
        assert len(calls) == 1
        command = calls[0]
        assert command[:2] == ["schtasks", "/Create"]
        assert command[command.index("/SC") + 1] == "MINUTE"
        assert command[command.index("/MO") + 1] == "1"
        assert command[command.index("/TN") + 1] == SCHEDULER_TASK_NAME
        assert "/F" in command

        invocation = command[command.index("/TR") + 1]
        assert r"C:\Python312\python.exe" in invocation
        assert "-m habits.reminder_runner" in invocation
        assert "--db" in invocation
        assert r"C:\proyectos\habits-app\data\habits.db" in invocation

    def test_scheduler_installs_single_minute_task_on_macos(self, tmp_path):
        """RF-2.3: macOS instala un único agente `launchd` cada minuto."""
        calls, runner = recording_runner()
        scheduler = SystemScheduler(
            platform="darwin",
            runner=runner,
            python_executable="/usr/bin/python3",
            project_dir="/proyectos/habits-app",
            launch_agents_dir=tmp_path,
            uid=501,
        )

        result = scheduler.sync(
            "/proyectos/habits-app/data/habits.db",
            has_active_reminders=True,
        )

        plist_path = tmp_path / f"{SCHEDULER_TASK_LABEL}.plist"
        assert result == SchedulerResult(ok=True)
        assert plist_path.exists()

        plist = plistlib.loads(plist_path.read_bytes())
        assert plist["Label"] == SCHEDULER_TASK_LABEL
        assert plist["StartInterval"] == 60
        assert plist["RunAtLoad"] is False
        assert plist["WorkingDirectory"] == "/proyectos/habits-app"
        assert plist["ProgramArguments"] == [
            "/usr/bin/python3",
            "-m",
            "habits.reminder_runner",
            "--db",
            "/proyectos/habits-app/data/habits.db",
        ]
        assert calls[-1] == [
            "launchctl",
            "bootstrap",
            "gui/501",
            str(plist_path),
        ]

    def test_scheduler_updates_the_existing_windows_task(self):
        """RF-2.3: reinstalar usa la misma tarea y la sobrescribe con `/F`."""
        calls, runner = recording_runner()
        scheduler = SystemScheduler(platform="win32", runner=runner)

        scheduler.sync("data/habits.db", has_active_reminders=True)
        scheduler.sync("data/habits.db", has_active_reminders=True)

        assert len(calls) == 2
        assert all(command[:2] == ["schtasks", "/Create"] for command in calls)
        assert all("/F" in command for command in calls)
        assert all(
            command[command.index("/TN") + 1] == SCHEDULER_TASK_NAME
            for command in calls
        )

    def test_scheduler_updates_the_existing_macos_agent(self, tmp_path):
        """RF-2.3: actualizar mantiene un único plist y reinicia el agente."""
        calls, runner = recording_runner()
        scheduler = SystemScheduler(
            platform="darwin",
            runner=runner,
            launch_agents_dir=tmp_path,
            uid=501,
        )

        scheduler.sync("data/habits.db", has_active_reminders=True)
        scheduler.sync("data/habits.db", has_active_reminders=True)

        plists = list(tmp_path.glob("*.plist"))
        assert len(plists) == 1
        assert [command[1] for command in calls] == [
            "bootout",
            "bootstrap",
            "bootout",
            "bootstrap",
        ]

    def test_scheduler_removes_windows_task_when_no_reminders(self):
        """RF-3.4: sin recordatorios se elimina la tarea del sistema."""
        calls, runner = recording_runner()
        scheduler = SystemScheduler(platform="win32", runner=runner)

        result = scheduler.sync(
            "data/habits.db", has_active_reminders=False
        )

        assert result == SchedulerResult(ok=True)
        assert calls == [
            ["schtasks", "/Delete", "/TN", SCHEDULER_TASK_NAME, "/F"]
        ]

    def test_scheduler_removes_macos_agent_when_no_reminders(self, tmp_path):
        """RF-3.4: sin recordatorios se retira el agente y su plist."""
        calls, runner = recording_runner()
        scheduler = SystemScheduler(
            platform="darwin",
            runner=runner,
            launch_agents_dir=tmp_path,
            uid=501,
        )
        scheduler.sync("data/habits.db", has_active_reminders=True)
        calls.clear()

        result = scheduler.sync(
            "data/habits.db", has_active_reminders=False
        )

        plist_path = tmp_path / f"{SCHEDULER_TASK_LABEL}.plist"
        assert result == SchedulerResult(ok=True)
        assert not plist_path.exists()
        assert calls == [
            ["launchctl", "bootout", "gui/501", str(plist_path)]
        ]

    def test_scheduler_removal_without_task_is_a_no_op(self, tmp_path):
        """RF-3.4: si no hay tarea instalada, retirarla no falla."""
        calls, runner = recording_runner()
        scheduler = SystemScheduler(
            platform="darwin",
            runner=runner,
            launch_agents_dir=tmp_path,
            uid=501,
        )

        result = scheduler.sync(
            "data/habits.db", has_active_reminders=False
        )

        assert result == SchedulerResult(ok=True)
        assert calls == []

    def test_scheduler_reports_installation_error(self):
        """RF-4.4: un fallo al programar se informa sin romper la app."""
        _, runner = recording_runner(
            result=completed(returncode=1, stderr="Access is denied.")
        )
        scheduler = SystemScheduler(platform="win32", runner=runner)

        result = scheduler.sync(
            "data/habits.db", has_active_reminders=True
        )

        assert result.ok is False
        assert "no se pudo" in result.message.lower()
        assert "programar" in result.message.lower()

    def test_scheduler_reports_removal_error(self):
        """RF-4.4: un fallo al retirar la tarea también se controla."""
        _, runner = recording_runner(
            result=completed(returncode=1, stderr="Access is denied.")
        )
        scheduler = SystemScheduler(platform="win32", runner=runner)

        result = scheduler.sync(
            "data/habits.db", has_active_reminders=False
        )

        assert result.ok is False
        assert "no se pudo" in result.message.lower()
        assert "quitar" in result.message.lower()

    def test_scheduler_rejects_unsupported_platform(self):
        """RFN-5: sin macOS ni Windows no se instala nada y se informa."""
        calls, runner = recording_runner()
        scheduler = SystemScheduler(platform="linux", runner=runner)

        result = scheduler.sync(
            "data/habits.db", has_active_reminders=True
        )

        assert result.ok is False
        assert calls == []
        assert "macos" in result.message.lower()
        assert "windows" in result.message.lower()