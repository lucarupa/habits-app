# spec: 003-edit-delete-habits
"""Tests de la documentación de edición y eliminación — Tarea 7.1.

Verifican que `README.md` describe la edición, la eliminación con confirmación,
el calendario de fecha, el borrado de registros asociados y los conteos de la
suite. No requieren Flet.
"""

from pathlib import Path

README_PATH = Path(__file__).resolve().parents[1] / "README.md"


def read_readme() -> str:
    """Leer el README completo en UTF-8."""
    return README_PATH.read_text(encoding="utf-8")


class TestReadmeEditDelete:
    """El README documenta la spec 003 — Tarea 7.1."""

    def test_has_a_section_for_editing_and_deleting(self):
        """La edición y el borrado tienen una sección propia."""
        readme = read_readme()

        assert "### Edición y eliminación de hábitos" in readme

    def test_documents_the_editing_flow(self):
        """RF-1.3, RF-2.1, RF-2.2, RF-2.9, RF-2.10: edición desde el detalle."""
        readme = read_readme()

        assert "Editar hábito" in readme
        assert "precargados" in readme
        assert "conserva el hábito seleccionado" in readme
        assert "Cancelar no modifica nada" in readme

    def test_documents_delete_confirmation_and_associated_records(self):
        """RF-3.1 a RF-3.8: confirmación, borrado de registros y selección."""
        readme = read_readme()

        assert "diálogo de confirmación" in readme
        assert "permanente" in readme
        assert "delete_habit_db" in readme
        assert "transacción" in readme
        assert "estado vacío" in readme
        assert "conserva el hábito" in readme

    def test_documents_the_calendar_and_blocked_future_days(self):
        """RF-5.1 a RF-5.8: fecha de solo lectura, calendario y días futuros."""
        readme = read_readme()

        assert "solo lectura" in readme
        assert "dd/mm/aaaa" in readme
        assert "calendario" in readme
        assert "español" in readme
        assert "días futuros" in readme

    def test_documents_the_current_test_counts(self):
        """La documentación refleja los conteos actuales de la suite."""
        readme = read_readme()

        assert "442 pruebas puras" in readme
        assert "121 con Flet" in readme
        assert "563 en `.venv`" in readme
