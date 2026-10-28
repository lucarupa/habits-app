# spec: 004-duplicate-warning-streak-recovery
"""Tests de la documentación de la spec 004 — Tarea 6.1.

Verifican que `README.md` describe el aviso de registro duplicado, la
recuperación de rachas, el estado recuperado del heatmap y los conteos
actuales de la suite. No requieren Flet.
"""

from pathlib import Path

README_PATH = Path(__file__).resolve().parents[1] / "README.md"


def read_readme() -> str:
    """Leer el README completo en UTF-8."""
    return README_PATH.read_text(encoding="utf-8")


class TestReadmeStreakRecovery:
    """El README documenta la spec 004 — Tarea 6.1."""

    def test_readme_documents_duplicate_warning(self):
        """RF-1: el README explica el aviso y su texto exacto."""
        readme = read_readme()

        assert "### Aviso de registro duplicado" in readme
        assert "⚠️ «nombre» ya está registrado hoy." in readme
        assert "SnackBar" in readme
        assert "no bloqueante" in readme
        assert "sin crear filas adicionales" in readme

    def test_readme_documents_streak_recovery(self):
        """RF-2: el README explica el límite, el diálogo y las estadísticas."""
        readme = read_readme()

        assert "### Recuperación de rachas" in readme
        assert "hueco más reciente" in readme
        assert "uno o dos días" in readme
        assert "Recuperar racha" in readme
        assert "StreakRecoveryDialog" in readme
        assert "Cancelar" in readme
        assert "mark_recovered_days_db" in readme
        assert "transacción" in readme
        assert "no cuentan para “Días registrados”" in readme
        assert "conserva el hábito seleccionado" in readme

    def test_readme_documents_recovered_heatmap_state(self):
        """RF-2.11: el README menciona el estado “Recuperado”."""
        readme = read_readme()

        assert "### Heatmap con días recuperados" in readme
        assert "Recuperado" in readme
        assert "ámbar" in readme
        assert "leyenda" in readme
        assert "tooltip" in readme

    def test_readme_documents_current_test_counts(self):
        """La documentación refleja los conteos actuales de la suite."""
        readme = read_readme()

        assert "442 pruebas puras" in readme
        assert "121 con Flet" in readme
        assert "563 en `.venv`" in readme
