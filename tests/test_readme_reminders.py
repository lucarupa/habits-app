# spec: 005-local-reminders
"""Tests de la documentación de los recordatorios — Tarea 7.1.

Verifican que `README.md` describe la configuración de los recordatorios, su
funcionamiento con la aplicación cerrada en macOS y Windows, el límite de un
aviso diario para hábitos pendientes y los conteos actuales de la suite.
No requieren Flet.
"""

import re
from pathlib import Path

README_PATH = Path(__file__).resolve().parents[1] / "README.md"

COUNT_PATTERN = re.compile(
    r"(\d+) pruebas puras \+ (\d+) con Flet \((\d+) en `\.venv`\)"
)


def read_readme() -> str:
    """Leer el README completo en UTF-8."""
    return README_PATH.read_text(encoding="utf-8")


class TestReadmeReminders:
    """El README documenta la spec 005 — Tarea 7.1."""

    def test_readme_documents_reminder_configuration(self):
        """RF-1: el README explica activar, cambiar la hora y desactivar."""
        readme = read_readme()

        assert "### Recordatorios locales" in readme
        assert "Recordatorio" in readme
        assert "Activar recordatorio" in readme
        assert "00:00-23:59" in readme
        assert "HH:MM" in readme
        assert "Sin recordatorio" in readme
        assert "Guardar" in readme
        assert "Cancelar" in readme
        assert "desactiv" in readme
        assert "ReminderDialog" in readme
        assert "save_reminder_db" in readme

    def test_readme_documents_closed_app_and_platforms(self):
        """RF-2.3, RFN-5: funciona con la app cerrada en macOS y Windows."""
        readme = read_readme()

        assert "app cerrada" in readme
        assert "macOS" in readme
        assert "Windows" in readme
        assert "launchd" in readme
        assert "schtasks" in readme
        assert "habits.reminder_runner" in readme
        assert "cada minuto" in readme
        assert "SystemScheduler" in readme

    def test_readme_documents_reminder_limits(self):
        """RF-2.4, RF-2.5, RF-2.7: solo pendientes, un aviso diario sin duplicados."""
        readme = read_readme()

        assert "un aviso al día" in readme
        assert "pendiente" in readme
        assert "no se repite" in readme
        assert "duplicad" in readme
        assert "desactivado" in readme

    def test_readme_documents_current_test_counts(self):
        """La documentación refleja un conteo coherente y actual de la suite."""
        readme = read_readme()

        counts = [
            tuple(int(value) for value in match)
            for match in COUNT_PATTERN.findall(readme)
        ]

        assert counts, "El README debe declarar los conteos de la suite"
        assert any(
            pure + flet == total and total >= 450
            for pure, flet, total in counts
        )
