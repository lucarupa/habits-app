# AGENTS.md — habits-app

## Proyecto
App de escritorio en Python para registrar hábitos de estudio y calcular rachas de días
consecutivos. Núcleo puro (`habits/core.py`) + capa app (`habits/app.py`).
Persistencia en SQLite local (`habits/storage.py`).

## Estilo
- Python 3.12+, type hints en todas las funciones públicas.
- Solo biblioteca estándar (pytest únicamente para tests).
- Identificadores en inglés; mensajes de usuario en español.

## Reglas
- Lee `docs/constitution.md` y la spec activa en `specs/` antes de tocar código.
- No modifiques archivos dentro de `specs/` salvo petición explícita.

## Al terminar cualquier tarea
- Ejecuta `pytest -q` y confirma en tu respuesta que todo pasa.
- Actualiza el archivo `README.md` con los cambios relevantes.