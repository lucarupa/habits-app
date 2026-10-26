# spec: 002-ui-redesign
"""Tests de la documentación del rediseño — Tarea 7.1.

Verifican que `README.md` describe el diseño y las estadísticas que exige la
spec 002. No requieren Flet.
"""

from pathlib import Path

from habits.core import DEFAULT_ICON
from habits.habit_form import ICON_LABELS

README_PATH = Path(__file__).resolve().parents[1] / "README.md"


def read_readme() -> str:
    """Leer el README completo en UTF-8."""
    return README_PATH.read_text(encoding="utf-8")


class TestReadmeDesign:
    """El README describe las zonas del nuevo diseño — Tarea 7.1."""

    def test_has_a_design_overview(self):
        """El diseño tiene una sección propia antes del detalle técnico."""
        readme = read_readme()

        assert "## Diseño de la interfaz" in readme
        assert "barra lateral" in readme.lower()
        assert "panel de detalle" in readme.lower()

    def test_describes_the_sidebar(self):
        """RF-1.2, RF-1.6, RF-7.2: barra lateral, lista y botón de creación."""
        readme = read_readme()

        assert "Mis hábitos" in readme
        assert "+ Nuevo" in readme
        assert "racha" in readme.lower()
        assert "seleccionado" in readme.lower()

    def test_describes_the_detail_panel(self):
        """RF-1.5, RF-2.1: encabezado, detalle y diálogo de creación."""
        readme = read_readme()

        assert "Hábito de estudio" in readme
        assert "Nuevo hábito" in readme or "diálogo modal" in readme

    def test_describes_the_three_statistics(self):
        """RF-3.1 a RF-3.5: racha actual, mejor racha y días registrados."""
        readme = read_readme()

        assert "Racha actual" in readme
        assert "Mejor racha" in readme
        assert "Días registrados" in readme

    def test_describes_the_heatmap(self):
        """RF-4.1 a RF-4.6: heatmap binario de 5 semanas."""
        readme = read_readme()

        assert "Heatmap de actividad" in readme
        assert "5 semanas" in readme
        assert "lunes a domingo" in readme

    def test_documents_every_icon_and_the_default(self):
        """RF-2.6, RF-2.8: catálogo de iconos semánticos y valor por defecto."""
        readme = read_readme()

        assert "## Iconos" in readme
        assert DEFAULT_ICON in readme
        for label in ICON_LABELS.values():
            assert label in readme

    def test_explains_how_to_run_the_app(self):
        """El README indica cómo iniciar la aplicación de escritorio."""
        readme = read_readme()

        assert "python -m habits.app" in readme

    def test_explains_how_to_run_the_tests(self):
        """El README indica cómo ejecutar la suite pura y la que usa Flet."""
        readme = read_readme()

        assert "pytest -q" in readme
        assert ".venv\\Scripts\\python.exe -m pytest -q" in readme
