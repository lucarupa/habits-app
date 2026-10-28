# spec: 005-local-reminders
# spec: 006-code-organization
"""Planificador que instala una única tarea periódica del sistema.

En macOS usa un agente `launchd` con `StartInterval` y en Windows una tarea
`schtasks` cada minuto. La tarea ejecuta `habits.reminder_runner` con la ruta
de la base de datos (RF-2.3, RF-3.4 y RF-4.4).
"""

import os
from pathlib import Path
import plistlib
import subprocess
import sys

from habits.notifications.common import Runner, run_command
from habits.notifications.models import (
    SCHEDULER_INSTALL_FAILED_MESSAGE,
    SCHEDULER_REMOVE_FAILED_MESSAGE,
    SCHEDULER_START_INTERVAL_SECONDS,
    SCHEDULER_TASK_LABEL,
    SCHEDULER_TASK_NAME,
    UNSUPPORTED_SCHEDULER_PLATFORM_MESSAGE,
    SchedulerResult,
)


class SystemScheduler:
    """Planificador que instala una única tarea periódica del sistema.

    En macOS usa un agente `launchd` con `StartInterval` y en Windows una
    tarea `schtasks` cada minuto. La tarea ejecuta `habits.reminder_runner`
    con la ruta de la base de datos; el runner decide qué avisos corresponden
    en cada comprobación (RF-2.3, RF-3.4 y RF-4.4).

    Args:
        platform: Identificador de plataforma; por defecto, `sys.platform`.
        runner: Ejecutor inyectable que recibe el comando y devuelve el
            resultado del proceso. Si se omite, se usa `subprocess.run`.
        python_executable: Intérprete usado para ejecutar el runner.
        project_dir: Directorio de trabajo del runner; por defecto, la raíz
            del proyecto.
        launch_agents_dir: Directorio de agentes de macOS; por defecto,
            `~/Library/LaunchAgents`. Se inyecta en los tests.
        uid: Identificador de usuario para `launchctl`; por defecto, el del
            proceso actual.
    """

    def __init__(
        self,
        platform: str | None = None,
        runner: Runner | None = None,
        python_executable: str | None = None,
        project_dir: str | Path | None = None,
        launch_agents_dir: str | Path | None = None,
        uid: int | None = None,
    ) -> None:
        self.platform = platform if platform is not None else sys.platform
        self._runner = runner or run_command
        self.python_executable = str(python_executable or sys.executable)
        self.project_dir = (
            str(project_dir)
            if project_dir is not None
            else str(Path(__file__).resolve().parents[2])
        )
        self.launch_agents_dir = (
            Path(launch_agents_dir)
            if launch_agents_dir is not None
            else Path.home() / "Library" / "LaunchAgents"
        )
        if uid is not None:
            self.uid = uid
        else:
            self.uid = os.getuid() if hasattr(os, "getuid") else 0

    @property
    def plist_path(self) -> Path:
        """Devolver la ruta del agente `launchd` de macOS."""
        return self.launch_agents_dir / f"{SCHEDULER_TASK_LABEL}.plist"

    def sync(
        self,
        db_path: str,
        *,
        has_active_reminders: bool,
    ) -> SchedulerResult:
        """Instalar, actualizar o retirar la tarea periódica del sistema.

        La operación es idempotente: si hay recordatorios activos se instala o
        actualiza una única tarea, y si no los hay se retira. Un fallo del
        sistema se traduce a un resultado en español sin lanzar excepciones
        (RF-2.3, RF-3.4 y RF-4.4).

        Args:
            db_path: Ruta de la base de datos que leerá el runner.
            has_active_reminders: Indica si existe al menos un recordatorio
                activo.

        Returns:
            Un SchedulerResult con el desenlace de la sincronización.
        """
        if self.platform == "darwin":
            return self._sync_macos(db_path, has_active_reminders)
        if self.platform in {"win32", "cygwin", "msys"}:
            return self._sync_windows(db_path, has_active_reminders)
        return SchedulerResult(
            ok=False,
            message=UNSUPPORTED_SCHEDULER_PLATFORM_MESSAGE,
        )

    def _run(self, command: list[str]) -> subprocess.CompletedProcess | None:
        """Ejecutar un comando y devolver None si el sistema no puede lanzarlo."""
        try:
            return self._runner(command)
        except OSError:
            return None

    def _sync_windows(
        self, db_path: str, has_active_reminders: bool
    ) -> SchedulerResult:
        """Instalar o retirar la tarea `schtasks` de Windows."""
        if has_active_reminders:
            command = self._windows_install_command(db_path)
        else:
            command = self._windows_remove_command()

        result = self._run(command)
        if result is None or result.returncode != 0:
            return SchedulerResult(
                ok=False,
                message=(
                    SCHEDULER_INSTALL_FAILED_MESSAGE
                    if has_active_reminders
                    else SCHEDULER_REMOVE_FAILED_MESSAGE
                ),
            )
        return SchedulerResult(ok=True)

    def _windows_install_command(self, db_path: str) -> list[str]:
        """Construir el comando que crea o reemplaza la tarea de Windows."""
        invocation = (
            f'"{self.python_executable}" -m habits.reminder_runner '
            f'--db "{db_path}"'
        )
        return [
            "schtasks",
            "/Create",
            "/SC",
            "MINUTE",
            "/MO",
            "1",
            "/TN",
            SCHEDULER_TASK_NAME,
            "/TR",
            invocation,
            "/F",
        ]

    def _windows_remove_command(self) -> list[str]:
        """Construir el comando que elimina la tarea de Windows."""
        return [
            "schtasks",
            "/Delete",
            "/TN",
            SCHEDULER_TASK_NAME,
            "/F",
        ]

    def _sync_macos(
        self, db_path: str, has_active_reminders: bool
    ) -> SchedulerResult:
        """Instalar, actualizar o retirar el agente `launchd` de macOS."""
        if not has_active_reminders:
            return self._remove_macos_agent()

        plist_path = self.plist_path
        try:
            plist_path.parent.mkdir(parents=True, exist_ok=True)
            plist_path.write_bytes(plistlib.dumps(self._macos_plist(db_path)))
        except OSError:
            return SchedulerResult(
                ok=False,
                message=SCHEDULER_INSTALL_FAILED_MESSAGE,
            )

        # `bootout` falla si el agente aún no estaba cargado; se ignora para
        # que la primera instalación y las actualizaciones sean idempotentes.
        self._run(self._macos_bootout_command())
        result = self._run(self._macos_bootstrap_command())
        if result is None or result.returncode != 0:
            return SchedulerResult(
                ok=False,
                message=SCHEDULER_INSTALL_FAILED_MESSAGE,
            )
        return SchedulerResult(ok=True)

    def _remove_macos_agent(self) -> SchedulerResult:
        """Retirar el agente de macOS y borrar su plist."""
        plist_path = self.plist_path
        if not plist_path.exists():
            return SchedulerResult(ok=True)

        result = self._run(self._macos_bootout_command())
        if result is None or result.returncode != 0:
            return SchedulerResult(
                ok=False,
                message=SCHEDULER_REMOVE_FAILED_MESSAGE,
            )

        try:
            plist_path.unlink(missing_ok=True)
        except OSError:
            return SchedulerResult(
                ok=False,
                message=SCHEDULER_REMOVE_FAILED_MESSAGE,
            )
        return SchedulerResult(ok=True)

    def _macos_plist(self, db_path: str) -> dict:
        """Construir el contenido del agente `launchd` de macOS."""
        return {
            "Label": SCHEDULER_TASK_LABEL,
            "ProgramArguments": [
                self.python_executable,
                "-m",
                "habits.reminder_runner",
                "--db",
                db_path,
            ],
            "WorkingDirectory": self.project_dir,
            "StartInterval": SCHEDULER_START_INTERVAL_SECONDS,
            "RunAtLoad": False,
        }

    def _macos_bootstrap_command(self) -> list[str]:
        """Construir el comando que carga el agente de macOS."""
        return [
            "launchctl",
            "bootstrap",
            f"gui/{self.uid}",
            str(self.plist_path),
        ]

    def _macos_bootout_command(self) -> list[str]:
        """Construir el comando que descarga el agente de macOS."""
        return [
            "launchctl",
            "bootout",
            f"gui/{self.uid}",
            str(self.plist_path),
        ]
