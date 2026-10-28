# spec: 005-local-reminders
# spec: 006-code-organization
"""Notificador que usa los comandos nativos de macOS y Windows.

Construye y ejecuta el aviso del recordatorio y traduce los fallos a
resultados controlados en español (RF-2.3, RF-4.1 a RF-4.3 y RFN-5).
"""

import sys

from habits.notifications.common import (
    Runner,
    escape_applescript,
    escape_powershell,
    is_permission_error,
    run_command,
)
from habits.notifications.models import (
    EXECUTION_FAILED_MESSAGE,
    NOTIFICATION_TITLE,
    PERMISSION_DENIED_MESSAGE,
    UNSUPPORTED_PLATFORM_MESSAGE,
    NotificationResult,
)


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
        self._runner = runner or run_command

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
        if is_permission_error(stderr):
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
            f'display notification "{escape_applescript(message)}" '
            f'with title "{escape_applescript(NOTIFICATION_TITLE)}"'
        )
        return ["osascript", "-e", script]

    def _windows_command(self, message: str) -> list[str]:
        """Construir el comando PowerShell de Windows."""
        title = escape_powershell(NOTIFICATION_TITLE)
        body = escape_powershell(message)
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
