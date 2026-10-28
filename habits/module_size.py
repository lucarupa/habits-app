# spec: 006-code-organization
"""Medición y búsqueda de módulos de producción sobredimensionados.

Cuenta las líneas con contenido de un módulo Python usando `tokenize` y
localiza de forma recursiva los módulos que superan el límite de 250 líneas
(RF-1.2, RF-1.3, RF-1.4, RF-1.5, RF-3.1, RF-3.2, RF-3.5 y RF-3.6).

El conteo ignora líneas vacías, comentarios de línea completa, saltos,
indentación y marcas de fin de archivo. Cada línea física ocupada por código,
una docstring, una cadena multilínea o un comentario al final de una
instrucción cuenta una sola vez.
"""

import io
import tokenize
from pathlib import Path

CONTENT_LINE_LIMIT = 250
EXCLUDED_DIRECTORIES = {
    ".eggs",
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "env",
    "node_modules",
    "venv",
}
IGNORED_TOKENS = {
    tokenize.COMMENT,
    tokenize.DEDENT,
    tokenize.ENCODING,
    tokenize.ENDMARKER,
    tokenize.INDENT,
    tokenize.NEWLINE,
    tokenize.NL,
}


def count_content_lines(source: str) -> int:
    """Contar las líneas con contenido de una fuente Python.

    Args:
        source: Texto completo del módulo Python.

    Returns:
        El número de líneas físicas ocupadas por código, docstrings, cadenas
        multilínea o comentarios al final de una instrucción. Las líneas
        vacías y los comentarios de línea completa no cuentan (RF-1.2,
        RF-1.3, RF-1.4 y RF-3.2).
    """
    content_lines: set[int] = set()
    tokens = tokenize.generate_tokens(io.StringIO(source).readline)

    for token in tokens:
        if token.type in IGNORED_TOKENS:
            continue
        start_line, end_line = token.start[0], token.end[0]
        content_lines.update(range(start_line, end_line + 1))

    return len(content_lines)


def find_oversized_modules(
    root: str | Path,
    limit: int = CONTENT_LINE_LIMIT,
) -> list[tuple[str, int]]:
    """Buscar recursivamente los módulos que superan el límite de contenido.

    La búsqueda no usa una lista fija de archivos: cualquier módulo Python
    nuevo dentro de ``root`` se inspecciona automáticamente. Se omiten las
    cachés, los entornos virtuales, los directorios generados y las rutas que
    no se pueden leer o tokenizar (RF-3.1, RF-3.5 y RF-3.6).

    Args:
        root: Directorio raíz del paquete de producción.
        limit: Máximo de líneas con contenido permitido; por defecto, 250.

    Returns:
        Una lista de tuplas ``(ruta_relativa, líneas)`` ordenada por ruta. La
        ruta usa separadores POSIX para ser estable entre plataformas.
    """
    root_path = Path(root)
    offenders: list[tuple[str, int]] = []

    for path in root_path.rglob("*.py"):
        relative_path = path.relative_to(root_path)
        if any(
            part in EXCLUDED_DIRECTORIES for part in relative_path.parts[:-1]
        ):
            continue
        if path.is_dir():
            continue

        try:
            source = path.read_text(encoding="utf-8")
            line_count = count_content_lines(source)
        except (OSError, UnicodeDecodeError, tokenize.TokenError, SyntaxError):
            continue

        if line_count > limit:
            offenders.append((relative_path.as_posix(), line_count))

    return sorted(offenders, key=lambda offender: offender[0])


def format_oversized_modules_message(
    offenders: list[tuple[str, int]],
    limit: int = CONTENT_LINE_LIMIT,
) -> str:
    """Componer el mensaje en español con todos los módulos infractores.

    Args:
        offenders: Lista de tuplas ``(ruta_relativa, líneas)``.
        limit: Límite de líneas con contenido que se muestra en el mensaje.

    Returns:
        Un único texto con la ruta y el conteo de cada infractor, o una cadena
        vacía si no hay ninguno (RF-3.3 y RF-3.4).
    """
    if not offenders:
        return ""

    if len(offenders) == 1:
        header = (
            "El siguiente módulo supera el límite de "
            f"{limit} líneas con contenido:"
        )
    else:
        header = (
            "Los siguientes módulos superan el límite de "
            f"{limit} líneas con contenido:"
        )

    details = [
        f"- {path}: {line_count} líneas" for path, line_count in offenders
    ]
    return "\n".join([header, *details])


def ensure_modules_within_limit(
    root: str | Path,
    limit: int = CONTENT_LINE_LIMIT,
) -> None:
    """Fallar si algún módulo de ``root`` supera el límite de contenido.

    Args:
        root: Directorio raíz del paquete de producción.
        limit: Máximo de líneas con contenido permitido; por defecto, 250.

    Raises:
        AssertionError: Si hay uno o más infractores; el mensaje incluye la
            ruta y el conteo de todos ellos (RF-3.3).

    Returns:
        ``None`` sin emitir advertencias cuando todos los módulos cumplen
        (RF-3.4).
    """
    offenders = find_oversized_modules(root, limit)
    if offenders:
        raise AssertionError(
            format_oversized_modules_message(offenders, limit)
        )

