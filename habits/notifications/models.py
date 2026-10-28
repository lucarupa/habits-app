# spec: 005-local-reminders
# spec: 006-code-organization
"""Tipos de resultado y textos de los adaptadores del sistema.

Conserva los mismos mensajes y valores del módulo anterior, sin depender de
Flet (RF-1.8, RF-2.1, RF-2.3 y RF-5.3).
"""

from dataclasses import dataclass

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
