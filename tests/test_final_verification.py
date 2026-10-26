# spec: 002-ui-redesign
"""Verificación automatizada de los RFN de la spec 002 — Tarea 7.3.

Los 8 criterios funcionales de finalización ya están cubiertos por la suite
existente (`test_app_state.py`, `test_habit_dialog.py`,
`test_registration_widgets.py`, `test_stats_heatmap.py` y `test_storage.py`).
Aquí se comprueban los requisitos no funcionales que faltaban: dependencias
aprobadas (RFN-7), funcionamiento sin red (RFN-5) e inicio rápido (RFN-6).
"""

import ast
import subprocess
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
APPROVED_DEPENDENCIES = {"flet", "pytest", "pytest-cov"}
NETWORK_MODULES = {
    "aiohttp",
    "ftplib",
    "http",
    "httpx",
    "requests",
    "smtplib",
    "socket",
    "urllib",
    "xmlrpc",
}
STARTUP_LIMIT_SECONDS = 3.0


def dependency_name(requirement: str) -> str:
    """Extraer el nombre de un requisito sin versión ni extras."""
    name = requirement.split(";")[0]
    for separator in ("==", ">=", "<=", "~=", "!=", ">", "<", "["):
        name = name.split(separator)[0]
    return name.strip().lower()


def test_requirements_use_only_approved_dependencies():
    """RFN-7: no se añaden dependencias fuera de flet y pytest."""
    lines = (ROOT / "requirements.txt").read_text(
        encoding="utf-8"
    ).splitlines()

    dependencies = {
        dependency_name(line)
        for line in lines
        if line.strip() and not line.strip().startswith("#")
    }

    assert dependencies <= APPROVED_DEPENDENCIES


def test_production_code_does_not_import_network_libraries():
    """RFN-5: la aplicación no usa red y funciona sin conexión."""
    offenders: set[str] = set()

    for path in sorted((ROOT / "habits").glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                modules = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                modules = [node.module]
            else:
                continue

            for module in modules:
                if module.split(".")[0] in NETWORK_MODULES:
                    offenders.add(f"{path.name}: {module}")

    assert offenders == set()


def test_app_starts_in_less_than_three_seconds():
    """RFN-6: el arranque en frío de la app tarda menos de 3 s."""
    pytest.importorskip("flet")

    start = time.perf_counter()
    subprocess.run(
        [sys.executable, "-c", "import habits.app"],
        cwd=ROOT,
        check=True,
        timeout=STARTUP_LIMIT_SECONDS * 2,
        capture_output=True,
    )
    elapsed = time.perf_counter() - start

    assert elapsed < STARTUP_LIMIT_SECONDS, f"arranque lento: {elapsed:.2f}s"
