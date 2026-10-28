# spec: 006-code-organization
"""Tests del conteo de líneas con contenido — Tarea 1.1.

Definen el contrato de `count_content_lines(source)` antes de implementar
`habits/module_size.py`. El conteo debe ignorar líneas vacías y comentarios de
línea completa, y debe incluir código, docstrings, cadenas multilínea y
comentarios al final de una instrucción (RF-1.2, RF-1.3, RF-1.4, RF-1.5 y
RF-3.2). Los casos de 250 y 251 líneas fijan el límite inclusivo.
"""

from pathlib import Path

import pytest

from habits.module_size import (
    count_content_lines,
    ensure_modules_within_limit,
    find_oversized_modules,
    format_oversized_modules_message,
)

LIMIT = 250


def source_with_content_lines(count: int) -> str:
    """Construir una fuente Python con exactamente ``count`` líneas de código."""
    return "".join(f"value_{index} = {index}\n" for index in range(count))


def write_module(path: Path, lines: int = LIMIT + 1) -> None:
    """Crear un módulo Python temporal con la cantidad de líneas indicada."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source_with_content_lines(lines), encoding="utf-8")


def test_count_ignores_blank_and_whitespace_lines():
    """RF-1.2: las líneas vacías o solo con espacios no cuentan."""
    source = "\n   \n\t\nx = 1\n\n    \n"

    assert count_content_lines(source) == 1


def test_count_ignores_full_line_comments_with_and_without_indentation():
    """RF-1.3: los comentarios de línea completa no cuentan, tengan sangría o no."""
    source = (
        "# comentario sin sangría\n"
        "    # comentario con sangría\n"
        "\t# comentario con tabulación\n"
        "x = 1\n"
    )

    assert count_content_lines(source) == 1


def test_count_includes_code_and_inline_comments():
    """RF-1.4: el código y los comentarios al final de una instrucción cuentan."""
    source = (
        "x = 1  # comentario al final\n"
        "if x:\n"
        "    y = 2  # otro comentario\n"
    )

    assert count_content_lines(source) == 3


def test_count_includes_docstring_lines():
    """RF-1.4: cada línea física de una docstring cuenta como contenido."""
    source = (
        '"""Docstring del módulo.\n'
        "Segunda línea.\n"
        '"""\n'
        "\n"
        "x = 1\n"
    )

    assert count_content_lines(source) == 4


def test_count_handles_comment_like_line_inside_docstring():
    """RF-1.4: una línea que empieza por # dentro de una docstring sí cuenta."""
    source = (
        "def funcion():\n"
        '    """Texto de la función.\n'
        "\n"
        "    # esto forma parte de la docstring.\n"
        '    """\n'
        "    return 1\n"
    )

    assert count_content_lines(source) == 6


def test_count_includes_multiline_strings():
    """RF-1.4: las líneas de una cadena multilínea cuentan, aunque parezcan comentarios."""
    source = (
        'message = """Primera línea.\n'
        "# parece un comentario, pero es parte de la cadena.\n"
        'Última línea."""\n'
    )

    assert count_content_lines(source) == 3


def test_count_returns_zero_for_only_comments_and_blank_lines():
    """RF-1.2, RF-1.3: un archivo sin código tiene cero líneas con contenido."""
    source = "# solo comentarios\n\n   \n    # otra línea comentada\n"

    assert count_content_lines(source) == 0


def test_exactly_250_content_lines_meets_limit():
    """RF-1.5: 250 líneas con contenido cumplen el límite inclusivo."""
    count = count_content_lines(source_with_content_lines(LIMIT))

    assert count == 250
    assert count <= LIMIT


def test_251_content_lines_exceeds_limit():
    """RF-1.5: 251 líneas con contenido incumplen el límite."""
    count = count_content_lines(source_with_content_lines(LIMIT + 1))

    assert count == 251
    assert count > LIMIT


class TestFindOversizedModules:
    """Búsqueda recursiva de módulos sobredimensionados — Tarea 1.2."""

    def test_find_oversized_modules_scans_recursively(self, tmp_path):
        """RF-3.1: recorre subdirectorios y detecta cada módulo infractor."""
        write_module(tmp_path / "small.py", LIMIT)
        write_module(tmp_path / "package" / "module.py", LIMIT + 1)
        write_module(tmp_path / "package" / "nested" / "deep.py", LIMIT + 50)

        assert find_oversized_modules(tmp_path) == [
            ("package/module.py", LIMIT + 1),
            ("package/nested/deep.py", LIMIT + 50),
        ]

    def test_find_oversized_modules_detects_new_subpackages(self, tmp_path):
        """RF-3.6: un subpaquete añadido después se detecta sin lista manual."""
        write_module(tmp_path / "base.py", LIMIT)
        assert find_oversized_modules(tmp_path) == []

        package = tmp_path / "new_package"
        write_module(package / "__init__.py", 0)
        write_module(package / "subpackage" / "__init__.py", 0)
        write_module(package / "subpackage" / "module.py", LIMIT + 1)

        assert find_oversized_modules(tmp_path) == [
            ("new_package/subpackage/module.py", LIMIT + 1),
        ]

    def test_find_oversized_modules_ignores_caches_and_virtualenvs(
        self, tmp_path
    ):
        """RF-3.5: no inspecciona cachés, entornos virtuales ni archivos ajenos."""
        write_module(tmp_path / "app.py", LIMIT + 1)
        write_module(
            tmp_path / "__pycache__" / "app.cpython-312.py", LIMIT + 100
        )
        write_module(
            tmp_path / "package" / "__pycache__" / "module.py", LIMIT + 100
        )
        write_module(tmp_path / ".venv" / "lib" / "module.py", LIMIT + 100)
        write_module(tmp_path / "venv" / "lib" / "module.py", LIMIT + 100)
        (tmp_path / "notes.txt").write_text(
            source_with_content_lines(LIMIT + 100), encoding="utf-8"
        )

        assert find_oversized_modules(tmp_path) == [
            ("app.py", LIMIT + 1),
        ]

    def test_find_oversized_modules_returns_offenders_in_stable_order(
        self, tmp_path
    ):
        """RF-3.1: el orden por ruta es estable aunque cambie la creación."""
        write_module(tmp_path / "zebra.py", LIMIT + 1)
        write_module(tmp_path / "alpha.py", LIMIT + 2)
        write_module(tmp_path / "middle" / "sub" / "module.py", LIMIT + 3)

        first_scan = find_oversized_modules(tmp_path)
        second_scan = find_oversized_modules(tmp_path)

        expected = [
            ("alpha.py", LIMIT + 2),
            ("middle/sub/module.py", LIMIT + 3),
            ("zebra.py", LIMIT + 1),
        ]
        assert first_scan == expected
        assert second_scan == expected

    def test_find_oversized_modules_returns_empty_when_all_fit(self, tmp_path):
        """RF-3.1: sin infractores devuelve una lista vacía."""
        write_module(tmp_path / "empty.py", 0)
        write_module(tmp_path / "limit.py", LIMIT)
        write_module(tmp_path / "nested" / "small.py", 10)

        assert find_oversized_modules(tmp_path) == []

    def test_find_oversized_modules_ignores_uninspectable_paths(self, tmp_path):
        """RF-3.1: una ruta ilegible no impide encontrar los demás infractores."""
        write_module(tmp_path / "valid.py", LIMIT + 1)
        write_module(tmp_path / "valid_package" / "module.py", LIMIT + 2)
        (tmp_path / "invalid_encoding.py").write_bytes(
            b"\xff\xfe\x00" * (LIMIT + 1)
        )
        (tmp_path / "directory.py").mkdir()

        assert find_oversized_modules(tmp_path) == [
            ("valid.py", LIMIT + 1),
            ("valid_package/module.py", LIMIT + 2),
        ]


class TestOversizedModulesMessage:
    """Mensaje de infracción y guardia reutilizable — Tarea 1.4."""

    def test_format_message_lists_all_offenders_with_path_and_count(self):
        """RF-3.3: un único texto en español incluye ruta y conteo de todos."""
        offenders = [
            ("domain/big.py", LIMIT + 50),
            ("persistence/huge.py", LIMIT + 1),
        ]

        message = format_oversized_modules_message(offenders)

        assert "domain/big.py" in message
        assert f"{LIMIT + 50} líneas" in message
        assert "persistence/huge.py" in message
        assert f"{LIMIT + 1} líneas" in message
        assert str(LIMIT) in message
        assert "límite" in message

    def test_format_message_is_empty_when_all_modules_fit(self):
        """RF-3.4: sin infractores no se genera ningún mensaje."""
        assert format_oversized_modules_message([]) == ""

    def test_guard_passes_without_output_when_all_modules_fit(
        self, tmp_path, capsys
    ):
        """RF-3.4: la guardia no avisa cuando todos los módulos cumplen."""
        write_module(tmp_path / "small.py", LIMIT)
        write_module(tmp_path / "nested" / "empty.py", 0)

        assert ensure_modules_within_limit(tmp_path) is None
        assert capsys.readouterr().out == ""

    def test_guard_fails_with_all_offenders_in_one_message(self, tmp_path):
        """RF-3.3: la guardia falla con todos los infractores juntos."""
        write_module(tmp_path / "domain" / "big.py", LIMIT + 50)
        write_module(tmp_path / "persistence" / "huge.py", LIMIT + 1)

        with pytest.raises(AssertionError) as error:
            ensure_modules_within_limit(tmp_path)

        message = str(error.value)
        assert "domain/big.py" in message
        assert f"{LIMIT + 50} líneas" in message
        assert "persistence/huge.py" in message
        assert f"{LIMIT + 1} líneas" in message



