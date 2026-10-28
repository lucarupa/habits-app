# spec: 006-code-organization
"""Tests de la documentación de la organización — Tarea 8.1.

Verifican que `README.md` describe el límite de 250 líneas con contenido, la
forma de contar, las exclusiones, la responsabilidad de cada paquete y módulo,
y los conteos reales de la suite. También comprueban que la spec 006 conserva
su estado final (RF-4.1, RF-4.2, RF-4.3 y RF-4.4).
"""

import importlib.util
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
README_PATH = ROOT / "README.md"
SPEC_DIR = ROOT / "specs" / "006-code-organization"
VENV_PYTHONS = (
    ROOT / ".venv" / "Scripts" / "python.exe",
    ROOT / ".venv" / "bin" / "python",
)

COUNT_PATTERN = re.compile(
    r"(\d+) pruebas puras \+ (\d+) con Flet \((\d+) en `\.venv`\)"
)

PACKAGE_RESPONSIBILITIES = {
    "habits/domain/": ("dominio", "racha"),
    "habits/persistence/": ("persistencia", "sqlite"),
    "habits/state/": ("estado",),
    "habits/forms/": ("formulario",),
    "habits/ui/": ("interfaz",),
    "habits/notifications/": ("notific",),
}

MODULE_RESPONSIBILITIES = {
    "app.py": ("entrada",),
    "module_size.py": ("límite", "tamaño"),
    "theme.py": ("tema",),
    "registration.py": ("registro",),
    "reminders.py": ("recordatorio",),
    "reminder_service.py": ("entrega",),
    "reminder_runner.py": ("runner",),
}

EXCLUDED_PATHS = (
    "__pycache__",
    ".venv",
    "venv",
    "build",
    "dist",
    "node_modules",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".git",
)


def read_readme() -> str:
    """Leer el README completo en UTF-8."""
    return README_PATH.read_text(encoding="utf-8")


def venv_python() -> Path | None:
    """Devolver el intérprete del entorno virtual si existe."""
    for candidate in VENV_PYTHONS:
        if candidate.exists():
            return candidate
    return None


def flet_installed() -> bool:
    """Indicar si Flet está disponible en el intérprete actual."""
    return importlib.util.find_spec("flet") is not None


def collected_test_count(python: str) -> int:
    """Contar las pruebas que pytest recopila con un intérprete."""
    result = subprocess.run(
        [python, "-m", "pytest", "--collect-only", "-q"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    match = re.search(r"(\d+) tests? collected", result.stdout)
    assert match is not None, result.stdout + result.stderr
    return int(match.group(1))


def readme_counts() -> tuple[int, int, int]:
    """Leer los conteos de pruebas declarados en el README."""
    counts = [
        tuple(int(value) for value in match)
        for match in COUNT_PATTERN.findall(read_readme())
    ]
    assert counts, "El README no declara los conteos de la suite"
    assert len(set(counts)) == 1, (
        "El README declara conteos de pruebas distintos entre secciones"
    )
    pure, flet, total = counts[0]
    return pure, flet, total


class TestReadmeSizeRule:
    """El README documenta la regla de tamaño — RF-4.1."""

    def test_documents_the_250_content_line_limit(self):
        """RF-4.1: el límite de 250 líneas con contenido es explícito."""
        readme = read_readme()

        assert "250" in readme
        assert "líneas con contenido" in readme.lower()

    def test_explains_how_content_lines_are_counted(self):
        """RF-4.1: se explica qué cuenta y qué no cuenta."""
        readme = read_readme().lower()

        for term in (
            "vacías",
            "comentarios",
            "docstring",
            "cadenas multilínea",
            "al final",
        ):
            assert term in readme

    def test_lists_the_excluded_paths(self):
        """RF-4.1: se enumeran los directorios que no se inspeccionan."""
        readme = read_readme()

        for excluded in EXCLUDED_PATHS:
            assert excluded in readme


class TestReadmeStructure:
    """El README describe la estructura y sus responsabilidades — RF-4.2."""

    @pytest.mark.parametrize(
        ("path", "keywords"),
        PACKAGE_RESPONSIBILITIES.items(),
    )
    def test_describes_each_package_responsibility(self, path, keywords):
        """RF-4.2: cada subpaquete aparece con su responsabilidad."""
        readme = read_readme().lower()

        assert path in readme
        assert any(keyword in readme for keyword in keywords)

    @pytest.mark.parametrize(
        ("module", "keywords"),
        MODULE_RESPONSIBILITIES.items(),
    )
    def test_describes_each_module_responsibility(self, module, keywords):
        """RF-4.2: cada módulo de producción aparece con su responsabilidad."""
        readme = read_readme().lower()

        assert module in readme
        assert any(keyword in readme for keyword in keywords)

    def test_structure_does_not_present_legacy_modules_as_current(self):
        """RF-2.5, RF-4.2: la estructura ya no muestra los módulos monolíticos."""
        readme = read_readme()
        structure = readme.split("## Estructura del proyecto", 1)[1]
        habits_block = structure.split("tests/", 1)[0]
        top_level = [
            line.split("──", 1)[1].strip()
            for line in habits_block.splitlines()
            if line.startswith(("├──", "└──"))
        ]

        for legacy in ("core.py", "storage.py", "app_state.py", "habit_form.py"):
            assert legacy not in top_level


class TestReadmeTestCounts:
    """El README refleja los conteos reales de la suite — RF-4.3."""

    def test_declares_consistent_counts(self):
        """RF-4.3: las pruebas puras y con Flet suman el total declarado."""
        pure, flet, total = readme_counts()

        assert pure + flet == total

    @pytest.mark.skipif(
        flet_installed(),
        reason="los conteos puros se miden en un Python sin Flet",
    )
    def test_pure_counts_match_the_current_suite(self):
        """RF-4.3: el conteo puro coincide con la suite recopilada sin Flet."""
        pure, _, _ = readme_counts()

        assert pure == collected_test_count(sys.executable)

    @pytest.mark.skipif(
        venv_python() is None,
        reason="no hay entorno virtual .venv",
    )
    def test_flet_counts_match_the_current_suite(self):
        """RF-4.3: el total coincide con la suite recopilada en `.venv`."""
        _, _, total = readme_counts()

        assert total == collected_test_count(str(venv_python()))


class TestSpecDocumentation:
    """La spec 006 conserva su estado final — RF-4.4."""

    def test_spec_documentation_reflects_the_final_state(self):
        """RF-4.4: spec, plan y tasks reflejan estado, decisiones y tareas."""
        for name in ("spec.md", "plan.md", "tasks.md"):
            assert (SPEC_DIR / name).exists()

        spec = (SPEC_DIR / "spec.md").read_text(encoding="utf-8")
        plan = (SPEC_DIR / "plan.md").read_text(encoding="utf-8")
        tasks = (SPEC_DIR / "tasks.md").read_text(encoding="utf-8")

        assert "## Estado de implementación" in spec
        assert "fases 1 a 8" in spec.lower()
        assert "250" in spec

        assert "## Estado final de la implementación" in plan
        assert "### Decisiones aplicadas" in plan
        assert "250" in plan
        for path in (
            "habits/domain/",
            "habits/persistence/",
            "habits/state/",
            "habits/forms/",
            "habits/ui/",
            "habits/notifications/",
        ):
            assert path in plan
        for module in (
            "reminders.py",
            "reminder_service.py",
            "reminder_runner.py",
            "persistence/reminders_repo.py",
            "ui/reminder_dialog.py",
        ):
            assert module in plan

        for task in (
            "1.1",
            "1.2",
            "1.3",
            "1.4",
            "1.5",
            "2.1",
            "2.2",
            "2.3",
            "2.4",
            "2.5",
            "3.1",
            "3.2",
            "3.3",
            "3.4",
            "3.5",
            "4.1",
            "4.2",
            "4.3",
            "4.4",
            "5.1",
            "5.2",
            "5.3",
            "5.4",
            "6.1",
            "6.2",
            "6.3",
            "6.4",
            "6.5",
            "6.6",
            "7.1",
            "7.2",
            "7.3",
            "7.4",
            "8.1",
            "8.2",
            "8.3",
        ):
            assert f"- [x] **Tarea {task}:**" in tasks
