# spec: 005-local-reminders
"""Fixtures compartidas de la suite.

Sustituye el planificador y el notificador del sistema por dobles inertes
cuando los tests montan `main`, para no crear tareas reales en el sistema
operativo ni mostrar notificaciones durante las pruebas. Los tests que
necesitan observar el comportamiento inyectan sus propios dobles.
"""

import pytest


class _SilentNotifier:
    """Notificador que siempre confirma la entrega."""

    def notify(self, message: str):
        from habits.notifications import NotificationResult

        return NotificationResult(ok=True)


class _SilentScheduler:
    """Planificador que siempre confirma la sincronización."""

    def sync(self, db_path: str, *, has_active_reminders: bool):
        from habits.notifications import SchedulerResult

        return SchedulerResult(ok=True)


@pytest.fixture(autouse=True)
def stub_system_adapters(monkeypatch):
    """Evitar efectos reales del sistema al montar la aplicación."""
    try:
        import habits.app as app_module
    except ImportError:  # sin Flet, los tests de interfaz se omiten
        return

    monkeypatch.setattr(app_module, "SystemNotifier", _SilentNotifier)
    monkeypatch.setattr(app_module, "SystemScheduler", _SilentScheduler)
