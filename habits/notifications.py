# spec: 005-local-reminders
"""Adaptador de notificaciones del sistema operativo.

Construye y ejecuta los comandos de macOS y Windows para mostrar el aviso de
un recordatorio, sin depender de Flet. Los fallos se traducen a resultados
controlados en español y el ejecutor de comandos es inyectable para poder
probarse sin enviar notificaciones reales (RF-2.3, RF-4.1 a RF-4.3, RFN-5).
"""

from collections.abc import Callable
from dataclasses import dataclass
import os
from pathlib import Path
import plistlib
import subprocess
import sys

NOTIFICATION_TITLE = "Hábitos de estudio"

SCHEDULER_TASK_LABEL = "com.habits.reminders"
SCHEDULER_TASK_NAME = "HabitsReminders"
SCHEDULER_START_INTERVAL_SECONDS = 60

PERMISSION_DENIED_MESSAGE = (
    "No se pudo enviar la notificación: el sistema denegó el permiso. "
    "Habilita las notificaciones de «Hábitos de estudio» en los ajustes del "
    "sistema y vuelve a intentarlo."
)
EXECUTION_FAILED_MESSAGE = (
    "No se pudo enviar la notificación del recordatorio. "
    "La aplicación seguirá funcionando con normalidad."
)
UNSUPPORTED_PLATFORM_MESSAGE = (
    "Los recordatorios solo están disponibles en macOS y Windows."
)
SCHEDULER_INSTALL_FAILED_MESSAGE = (
    "No se pudo programar el recordatorio en el sistema. "
    "La configuración anterior se conserva."
)
SCHEDULER_REMOVE_FAILED_MESSAGE = (
    "No se pudo quitar el recordatorio del sistema. "
    "La aplicación seguirá funcionando con normalidad."
)
UNSUPPORTED_SCHEDULER_PLATFORM_MESSAGE = (
    "Los recordatorios automáticos solo están disponibles en macOS y Windows."
)

_PERMISSION_MARKERS = (
    "permission",
    "not allowed",
    "denied",
    "denegado",
    "no permitido",
    "0x80070005",
)

Runner = Callable[[list[str]], subprocess.CompletedProcess]


@dataclass(frozen=True)
class NotificationResult:
    """Resultado de intentar mostrar una notificación.

    Atributos:
        ok: Indica si el sistema aceptó la notificación.
        message: Explicación en español cuando hay un fallo; vacía si fue bien.
        permission_denied: Indica si el fallo se debe a permisos del sistema.
    """

    ok: bool
    message: str = ""
    permission_denied: bool = False


@dataclass(frozen=True)
class SchedulerResult:
    """Resultado de sincronizar la tarea periódica del sistema.

    Atributos:
        ok: Indica si la tarea quedó instalada, actualizada o retirada.
        message: Explicación en español cuando hay un fallo; vacía si fue bien.
    """

    ok: bool
    message: str = ""


def _run_command(command: list[str]) -> subprocess.CompletedProcess:
    """Ejecutar un comando del sistema y capturar su salida."""
    return subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=False,
    )


def _escape_applescript(value: str) -> str:
    """Escapar un texto para incluirlo en una cadena de AppleScript."""
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _escape_powershell(value: str) -> str:
    """Escapar un texto para incluirlo en una cadena de PowerShell."""
    normalized = value.replace("\r", " ").replace("\n", " ")
    return normalized.replace("'", "''")


def _is_permission_error(stderr: str) -> bool:
    """Indicar si la salida del sistema sugiere un permiso denegado."""
    normalized = stderr.lower()
    return any(marker in normalized for marker in _PERMISSION_MARKERS)


class SystemNotifier:
    """Notificador que usa los comandos nativos de macOS y Windows.

    Args:
        platform: Identificador de plataforma; por defecto, `sys.platform`.
        runner: Ejecutor inyectable que recibe el comando y devuelve el
            resultado del proceso. Si se omite, se usa `subprocess.run`.
    """

    def __init__(
        self,
        platform: str | None = None,
        runner: Runner | None = None,
    ) -> None:
        self.platform = platform if platform is not None else sys.platform
        self._runner = runner or _run_command

    def build_command(self, message: str) -> list[str]:
        """Construir el comando nativo que muestra la notificación.

        Args:
            message: Texto en español que se mostrará al usuario.

        Returns:
            El comando listo para ejecutarse en la plataforma actual.

        Raises:
            ValueError: Si la plataforma no es macOS ni Windows (RFN-5).
        """
        if self.platform == "darwin":
            return self._macos_command(message)
        if self.platform in {"win32", "cygwin", "msys"}:
            return self._windows_command(message)
        raise ValueError(UNSUPPORTED_PLATFORM_MESSAGE)

    def notify(self, message: str) -> NotificationResult:
        """Mostrar una notificación y devolver el resultado del sistema.

        La llamada es síncrona: espera a que el sistema responda para que la
        activación de un recordatorio solo se confirme si la notificación de
        prueba se entregó (RF-4.1). Un permiso denegado, un fallo de ejecución
        o una plataforma no compatible se traducen a un resultado en español
        sin propagar excepciones (RF-4.2, RF-4.3 y RFN-5).

        Args:
            message: Texto en español que se mostrará al usuario.

        Returns:
            Un NotificationResult con el desenlace del envío.
        """
        try:
            command = self.build_command(message)
        except ValueError:
            return NotificationResult(
                ok=False,
                message=UNSUPPORTED_PLATFORM_MESSAGE,
            )

        try:
            result = self._runner(command)
        except OSError:
            return NotificationResult(
                ok=False,
                message=EXECUTION_FAILED_MESSAGE,
            )

        if result.returncode == 0:
            return NotificationResult(ok=True)

        stderr = result.stderr or ""
        if _is_permission_error(stderr):
            return NotificationResult(
                ok=False,
                message=PERMISSION_DENIED_MESSAGE,
                permission_denied=True,
            )

        return NotificationResult(
            ok=False,
            message=EXECUTION_FAILED_MESSAGE,
        )

    def _macos_command(self, message: str) -> list[str]:
        """Construir el comando `osascript` de macOS."""
        script = (
            f'display notification "{_escape_applescript(message)}" '
            f'with title "{_escape_applescript(NOTIFICATION_TITLE)}"'
        )
        return ["osascript", "-e", script]

    def _windows_command(self, message: str) -> list[str]:
        """Construir el comando PowerShell de Windows."""
        title = _escape_powershell(NOTIFICATION_TITLE)
        body = _escape_powershell(message)
        script = (
            "[Windows.UI.Notifications.ToastNotificationManager, "
            "Windows.UI.Notifications, ContentType = WindowsRuntime] > $null; "
            "$template = [Windows.UI.Notifications.ToastNotificationManager]::"
            "GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::"
            "ToastText02); "
            "$texts = $template.GetElementsByTagName('text'); "
            "$texts.Item(0).AppendChild("
            f"$template.CreateTextNode('{title}')) > $null; "
            "$texts.Item(1).AppendChild("
            f"$template.CreateTextNode('{body}')) > $null; "
            "$toast = [Windows.UI.Notifications.ToastNotification]::new("
            "$template); "
            "[Windows.UI.Notifications.ToastNotificationManager]::"
            f"CreateToastNotifier('{title}').Show($toast)"
        )
        return ["powershell", "-NoProfile", "-NonInteractive", "-Command", script]


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
        self._runner = runner or _run_command
        self.python_executable = str(python_executable or sys.executable)
        self.project_dir = (
            str(project_dir)
            if project_dir is not None
            else str(Path(__file__).resolve().parents[1])
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
