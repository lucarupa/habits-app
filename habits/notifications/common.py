# spec: 005-local-reminders
# spec: 006-code-organization
"""Ejecución de comandos y escapado compartidos por los adaptadores.

Mantiene el ejecutor inyectable y las traducciones de permisos del módulo
anterior, sin depender de Flet (RF-1.8, RF-2.1 y RF-2.3).
"""

from collections.abc import Callable
import subprocess

Runner = Callable[[list[str]], subprocess.CompletedProcess]

_PERMISSION_MARKERS = (
    "permission",
    "not allowed",
    "denied",
    "denegado",
    "no permitido",
    "0x80070005",
)


def run_command(command: list[str]) -> subprocess.CompletedProcess:
    """Ejecutar un comando del sistema y capturar su salida."""
    return subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=False,
    )


def escape_applescript(value: str) -> str:
    """Escapar un texto para incluirlo en una cadena de AppleScript."""
    return value.replace("\\", "\\\\").replace('"', '\\"')


def escape_powershell(value: str) -> str:
    """Escapar un texto para incluirlo en una cadena de PowerShell."""
    normalized = value.replace("\r", " ").replace("\n", " ")
    return normalized.replace("'", "''")


def is_permission_error(stderr: str) -> bool:
    """Indicar si la salida del sistema sugiere un permiso denegado."""
    normalized = stderr.lower()
    return any(marker in normalized for marker in _PERMISSION_MARKERS)
