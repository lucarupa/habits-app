# Habits App

App de escritorio en Python para registrar hábitos de estudio y calcular rachas de días consecutivos. Proyecto educativo diseñado para ser mantenido por un desarrollador senior.

## Funcionalidades del MVP

- **Crear un hábito** con nombre (máx. 60 caracteres) y fecha de inicio opcional.
- **Marcar un hábito como completado** para el día actual, con advertencia si ya fue registrado.
- **Listar hábitos** ordenados por racha de días consecutivos descendente, con desempate alfabético.
- **Cálculo de racha estricta**: la racha cuenta hacia atrás desde hoy; si el último día no es hoy, la racha es cero.

## Stack tecnológico

- **Python 3.12+** estándar
- **Flet 1.0.5** — interfaz de escritorio
- **SQLite** — persistencia local (sin dependencias externas)
- **pytest** — pruebas unitarias (46 tests pasando)

## Estado de implementación

| Fase | Descripción | Estado |
|------|-------------|--------|
| Fase 1 | Preparación del proyecto | ✅ Completa |
| Fase 2 | Modelo de dominio (`core.py`) | ✅ Completa |
| Fase 3 | Tests de lógica de dominio | ✅ Completa |
| Fase 4 | Persistencia SQLite (`storage.py`) | ✅ Completa |
| Fase 5 | Tests de persistencia | ✅ Completa |
| Fase 6 | Interfaz Flet (`app.py`) | ✅ Completa |
| Fase 7 | Verificación final | ✅ Completa |

### Lógica de dominio implementada

Las siguientes funciones en `habits/core.py` están completas y testeadas:

- `create_habit(name, start_date)` — crea un hábito con validaciones de nombre y fecha.
- `mark_completed(habit_id, completed_dates, today)` — marca un hábito como completado hoy.
- `calculate_streak(completed_dates, today)` — calcula la racha de días consecutivos.
- `list_habits_with_streak(habits, completions_by_habit, today)` — lista hábitos ordenados por racha.

### Persistencia SQLite implementada

Las siguientes funciones en `habits/storage.py` están completas y testeadas:

- `init_db(db_path)` — crea las tablas `habits` y `completions` si no existen.
- `create_habit_db(name, start_date, db_path)` — inserta un hábito y retorna su ID.
- `get_habit_db(habit_id, db_path)` — lee un hábito por ID.
- `mark_completed_db(habit_id, completed_date, db_path)` — registra un completado.
- `is_completed_today_db(habit_id, today, db_path)` — verifica si un hábito ya está marcado hoy.
- `list_all_habits_db(db_path)` — obtiene todos los hábitos registrados.
- `get_completions_db(habit_id, db_path)` — obtiene las fechas de completado de un hábito.

## Requisitos

- Python 3.12 o superior
- `flet` — interfaz de escritorio
- `pytest` — pruebas unitarias (opcional, para desarrollo)

## Instalación

Usa el archivo `requirements.txt` para instalar todas las dependencias:

```bash
pip install -r requirements.txt
```

## Ejecutar en local

```bash
python -m habits.app
```

La aplicación se abre en una ventana de escritorio con dos vistas: crear hábito y listar hábitos con rachas.

## Ejecutar tests

```bash
pytest -q
```

Con cobertura:

```bash
pytest --cov=habits --cov-report=term-missing
```

## Generar ejecutable de producción

Usa el comando integrado de Flet para empaquetar la aplicación:

```bash
pip install flet[cli]
flet pack habits/app.py
```

Esto genera un ejecutable independiente en el directorio `dist/` sin necesidad de Python instalado en el equipo del usuario.

Opciones útiles:

```bash
# Ejecutable con nombre personalizado
flet pack habits/app.py --name "Habits App"

# Incluir icono personalizado
flet pack habits/app.py --icon icon.png
```

Para más opciones, consulta la [documentación de `flet pack`](https://flet.dev/docs/cli/flet-pack).

## Estructura del proyecto

```
habits/
├── __init__.py
├── core.py          # Lógica de dominio: modelos y cálculo de racha
├── storage.py       # Persistencia SQLite: CRUD de hábitos y registros
└── app.py           # Interfaz Flet (creación y lista con rachas implementadas)
tests/
├── test_core.py     # Tests de lógica de dominio (23 tests)
└── test_storage.py  # Tests de persistencia (23 tests)
data/
└── habits.db        # Base de datos SQLite (generada en runtime)
docs/
└── constitution.md  # 6 principios innegociables del proyecto
specs/
└── 001-habits-mvp/
    ├── spec.md      # Especificación funcional del MVP
    ├── plan.md      # Plan de implementación técnica
    └── tasks.md     # Tareas de implementación con checklist
```

## Documentación

- **Constitución del proyecto** — `docs/constitution.md`: 6 principios que guían el desarrollo.
- **Especificación 001** — `specs/001-habits-mvp/spec.md`: requisitos funcionales y no funcionales del MVP.
- **Plan de implementación** — `specs/001-habits-mvp/plan.md`: arquitectura, modelo de datos y decisiones técnicas.
- **Tareas** — `specs/001-habits-mvp/tasks.md`: checklist de tareas con criterios de aceptación.

## Agent Skills

- **spec-creator** — `.junie/skills/spec-creator/`: skill reutilizable para crear especificaciones de nuevas funcionalidades siguiendo el proceso spec-driven del proyecto. Incluye plantillas para `spec.md`, `plan.md` y `tasks.md`.

## Licencia

Este proyecto está bajo la [Apache License 2.0](LICENSE).
