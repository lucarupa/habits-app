# AGENTS.md — habits-app

## Proyecto
App de escritorio en Python para registrar hábitos de estudio y calcular rachas de días
consecutivos. Punto de entrada `habits/app.py`; lógica pura en `habits/domain/`; persistencia
SQLite en `habits/persistence/`; estado de la aplicación en `habits/state/`; formularios en
`habits/forms/`; interfaz Flet en `habits/ui/`; adaptadores del sistema en
`habits/notifications/`.

## Estilo
- Python 3.12+, type hints en todas las funciones públicas.
- flet 1.0.5+.
- Solo biblioteca estándar (pytest y pytest-cov únicamente para tests).
- Identificadores en inglés; mensajes de usuario en español.
- Cada módulo que implementa una spec incluye un comentario `# spec: <slug>`.

## Organización del código
- Ningún módulo de producción de `habits/` puede superar las **250 líneas con contenido**,
  incluidos los `__init__.py` y los subpaquetes nuevos.
- El conteo se hace con `habits/module_size.py`; la guardia global vive en
  `tests/test_module_size.py` y debe seguir pasando sin cambios.
- Cada módulo tiene una única responsabilidad. No se crean fachadas ni reexportaciones de
  compatibilidad: cada import apunta al módulo responsable (`habits.domain.habits`,
  `habits.persistence.habits_repo`, `habits.ui.sidebar`, etc.).
- `domain/`, `persistence/` y `state/` no importan Flet; `ui/` no importa SQLite ni los
  repositorios. `tests/test_architecture.py` protege la separación de capas y la ausencia de
  ciclos entre módulos.
- Si un módulo se acerca al límite, se divide por responsabilidad; no se comprime el código ni
  se amplía el límite.

## Reglas
- Lee `docs/constitution.md` y la spec activa en `specs/` antes de tocar código.
- No modifiques archivos dentro de `specs/` salvo petición explícita.
- Antes de añadir código nuevo, ubícalo en el paquete de su responsabilidad y comprueba el
  límite de tamaño.
- No añadas dependencias ni cambies el esquema SQLite sin una spec que lo justifique.
- Conserva el comportamiento visible, los datos, los textos en español y las funciones públicas
  existentes al reorganizar código.

## Al terminar cualquier tarea
- Ejecuta `pytest -q` y confirma en tu respuesta que todo pasa.
- Ejecuta también la suite completa con el intérprete del proyecto:
  `.venv\Scripts\python.exe -m pytest -q`.
- Mantén la cobertura de los módulos con lógica (`domain/`, `persistence/`, `state/`, `forms/`
  y `module_size.py`) en al menos el 80 %.
- Actualiza `README.md` con los cambios relevantes y, si cambian, con los conteos de pruebas y
  las expectativas de `tests/test_readme_*.py`.
