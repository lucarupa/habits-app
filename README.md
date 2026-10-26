# Habits App

App de escritorio en Python para registrar hábitos de estudio y calcular rachas de días consecutivos. Proyecto educativo diseñado para ser mantenido por un desarrollador senior.

## Funcionalidades del MVP

- **Crear un hábito** con nombre (máx. 60 caracteres) y fecha de inicio opcional.
- **Marcar un hábito como completado** para el día actual, con advertencia si ya fue registrado.
- **Registrar hoy** desde el panel de detalle con la fecha actual y confirmación inmediata; los duplicados se rechazan.
- **Listar hábitos** ordenados por racha de días consecutivos descendente, con desempate alfabético.
- **Ver estadísticas** del hábito seleccionado: racha actual, mejor racha y días registrados.
- **Heatmap de actividad** de las últimas 5 semanas, con días completados, no completados y futuros.
- **Cálculo de racha estricta**: la racha cuenta hacia atrás desde hoy; si el último día no es hoy, la racha es cero.

## Stack tecnológico

- **Python 3.12+** estándar
- **Flet 1.0.5** — interfaz de escritorio
- **SQLite** — persistencia local (sin dependencias externas)
- **pytest** — 149 pruebas puras + 31 de interfaz con Flet (180 en `.venv`)

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

- `create_habit(name, start_date, icon)` — crea un hábito con validaciones de nombre, fecha e icono.
- `mark_completed(habit_id, completed_dates, today)` — marca un hábito como completado hoy.
- `calculate_streak(completed_dates, today)` — calcula la racha de días consecutivos.
- `calculate_best_streak(completed_dates)` — calcula la mejor racha histórica de días consecutivos.
- `count_registered_days(completed_dates)` — cuenta las fechas distintas registradas.
- `get_habit_stats(completed_dates, today)` — devuelve racha actual, mejor racha y días registrados.
- `build_activity_heatmap(completed_dates, today, weeks=5)` — construye las celdas del heatmap de actividad.
- `list_habits_with_streak(habits, completions_by_habit, today)` — lista hábitos ordenados por racha.

### Persistencia SQLite implementada

Las siguientes funciones en `habits/storage.py` están completas y testeadas:

- `init_db(db_path)` — crea las tablas `habits` y `completions` si no existen, y migra bases antiguas añadiendo la columna `icon` (valor por defecto `book`).
- `create_habit_db(name, start_date, icon, db_path)` — inserta un hábito con su icono y retorna su ID.
- `get_habit_db(habit_id, db_path)` — lee un hábito por ID, incluido su icono.
- `mark_completed_db(habit_id, completed_date, db_path)` — registra un completado.
- `is_completed_today_db(habit_id, today, db_path)` — verifica si un hábito ya está marcado hoy.
- `list_all_habits_db(db_path)` — obtiene todos los hábitos registrados, incluidos sus iconos.
- `get_completions_db(habit_id, db_path)` — obtiene las fechas de completado de un hábito.

### Cargador de estado implementado

Las siguientes piezas en `habits/app_state.py` están completas y testeadas:

- `load_app_state(db_path, today)` — obtiene hábitos y fechas desde `storage.py`, calcula estadísticas con `core.py`, ordena por racha descendente y nombre ascendente, y selecciona el primer hábito.
- `AppState` — mantiene la lista de hábitos, el ID seleccionado y la fecha usada para las estadísticas y el heatmap.
- `HabitState` — agrupa un hábito, sus estadísticas y sus fechas completadas.
- `AppState.stat_cards()` — devuelve las tres tarjetas con sus valores.
- `AppState.heatmap_cells()` / `heatmap_rows()` — construyen las 35 celdas y las agrupan en 7 filas de lunes a domingo por 5 semanas.
- `AppState.is_completed_today` — indica si el hábito seleccionado ya tiene un registro para la fecha actual.

Este módulo no importa Flet: la interfaz solo consume el estado ya calculado (RFN-3).

### Barra lateral implementada

En `habits/app.py`:

- `Sidebar` — barra lateral con “Mis hábitos”, el botón “+ Nuevo” y la lista de hábitos. Cada elemento muestra icono, nombre y racha; el seleccionado se resalta con fondo verde y un indicador lateral.
- `icon_for_habit(icon_key)` — traduce la clave semántica del icono a un icono de Flet.
- `format_streak_label(streak)` — formatea la racha en español (“Sin racha”, “🔥 1 día”, “🔥 2 días”).

### Encabezado de detalle implementado

- `AppState.detail_header()` — devuelve el icono, nombre, subtítulo “Hábito de estudio” y fecha de inicio en dd/mm/aaaa del hábito seleccionado.
- `DetailHeader` — datos puros del encabezado, sin dependencia de Flet.
- `HabitDetailHeader` — control Flet que muestra una caja con el icono, el nombre, el subtítulo y la línea “Inicio: dd/mm/aaaa”.
- `format_date_label(fecha)` — formatea todas las fechas visibles como dd/mm/aaaa (RF-7.4).

### Estado vacío implementado

- `AppState.is_empty` — indica si no hay ningún hábito registrado.
- `AppState.empty_state()` — devuelve los textos del estado vacío o `None` cuando ya hay hábitos.
- `EmptyState` — agrupa el mensaje de la barra lateral, el título y el texto del botón.
- `Sidebar` — muestra “No hay hábitos aún” cuando la lista está vacía.
- `EmptyDetailPanel` — muestra ilustración, “Crea tu primer hábito para empezar tu racha” y el botón “+ Crear hábito”; se oculta al crear el primero.

### Tema visual y ventana

- `habits/theme.py` — paleta pura y dimensiones: fondo crema, superficies claras, acento verde, barra lateral de 280 px y ventana inicial de 1120×720 (mínimo 960×600).
- `configure_page(page)` en `habits/app.py` — aplica `ThemeMode.LIGHT`, el color semilla verde, el fondo crema y el tamaño mínimo de ventana.
- `main()` — monta el layout de dos zonas: barra lateral y panel de detalle, sin scroll horizontal.

### Creación de hábitos con diálogo modal

- `habits/habit_form.py` — lógica pura del formulario, sin Flet:
  - `ICON_CATALOG` e `ICON_LABELS` — catálogo de iconos con su etiqueta en español.
  - `parse_start_date(value, today)` — interpreta `dd/mm/aaaa`; sin fecha o con fecha futura usa hoy y rechaza formatos o fechas inexistentes.
  - `validate_habit_form(data, today)` — exige nombre de 1 a 60 caracteres y normaliza fecha e icono.
  - `create_habit_from_form(data, db_path, today)` — valida y persiste el hábito, devolviendo su ID.
- `HabitFormDialog` en `habits/app.py` — diálogo modal con nombre, fecha opcional e icono; ante un error permanece abierto y al guardar se cierra.
- `main()` — “+ Nuevo” y “+ Crear hábito” abren el mismo modal; al crear, recarga el estado, actualiza la barra lateral y selecciona el hábito nuevo para mostrar su detalle.
- `main()` monta el layout con `page.add(...)` sobre la vista raíz de la página; el diálogo modal solo se renderiza si la vista raíz se conserva válida.

### Estadísticas y heatmap

- `StatCard` — modelo puro con el título y el valor de cada tarjeta.
- `HabitStatsCards` — muestra “Racha actual”, “Mejor racha” y “Días registrados”; sin registros, las tres valen 0.
- `ActivityHeatmap` — cuadrícula de 7 filas (lunes a domingo) por 5 columnas (semanas), con la celda de hoy resaltada, los días futuros atenuados y la leyenda “No completado / Completado”.
- `refresh_views()` en `main()` — recarga el estado y refresca barra lateral, encabezado, tarjetas, heatmap y estado vacío. Al registrar el día actual, las tres zonas se actualizan sin reiniciar la aplicación.
- Los campos de estado y de modelo (`state`, `cards`, `rows`) usan `skip_field()` para quedar fuera del árbol de serialización de Flet; así los dataclasses frozen de `core.py` y `app_state.py` nunca reciben atributos internos de control.

### Registro del día actual

- `habits/registration.py` — lógica pura del registro, sin Flet:
  - `RegistrationResult` — indica si el guardado tuvo éxito y el mensaje para el usuario.
  - `is_registered_today(habit_id, today, db_path)` — consulta si ya existe el registro del día.
  - `register_today(habit_id, today, db_path)` — persiste el completado de hoy y devuelve “✅ Registro guardado”; si ya existía, devuelve “Ya registrado hoy” sin crear un duplicado.
- `TodayRegistrationPanel` — panel “Registrar hoy” con la fecha en dd/mm/aaaa y un botón “Guardar”. No incluye selector de fecha, minutos ni “Quitar registro”; cuando el hábito ya está completado muestra “Ya registrado hoy”.
- `main()` — al pulsar “Guardar” registra la fecha actual, muestra la confirmación y refresca la barra lateral, las estadísticas, el heatmap y el propio panel. Los datos permanecen al reiniciar la aplicación.

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

La aplicación se abre en una ventana de escritorio con la barra lateral de hábitos y el panel de detalle, que incluye las tarjetas de estadísticas, el heatmap de 5 semanas y el panel “Registrar hoy”. El botón “+ Nuevo” y el CTA del estado vacío abren el mismo diálogo modal de creación.

## Ejecutar tests

```bash
pytest -q
```

`tests/test_habit_dialog.py`, `tests/test_detail_widgets.py`, `tests/test_serialization.py` y `tests/test_registration_widgets.py` requieren Flet y se omiten automáticamente en un Python sin Flet. Para ejecutar la suite completa, usa el intérprete del proyecto:

```bash
.venv\Scripts\python.exe -m pytest -q
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
├── app_state.py     # Cargador de estado: une storage y core sin Flet
├── habit_form.py    # Validación y persistencia del formulario modal
├── registration.py  # Registro del día actual y prevención de duplicados
├── theme.py         # Tema visual y dimensiones de ventana
└── app.py           # Interfaz Flet: barra lateral, detalle, modal y registro
tests/
├── test_core.py     # Tests de lógica de dominio (43 tests)
├── test_storage.py  # Tests de persistencia (31 tests)
├── test_app_state.py # Tests del estado, barra lateral, detalle y vacío (15 tests)
├── test_theme.py    # Tests del tema y la ventana (3 tests)
├── test_habit_form.py # Tests del formulario modal (35 tests)
├── test_stats_heatmap.py # Tests de estadísticas y heatmap (12 tests)
├── test_registration.py # Tests del registro del día actual (10 tests)
├── test_habit_dialog.py # Tests del diálogo Flet (10 tests, requiere .venv)
├── test_detail_widgets.py # Tests de tarjetas y heatmap Flet (8 tests, requiere .venv)
├── test_registration_widgets.py # Tests del panel y flujo de registro (7 tests, requiere .venv)
└── test_serialization.py # Regresión de serialización Flet (6 tests, requiere .venv)
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
- **Especificación 002** — `specs/002-ui-redesign/spec.md`: rediseño de interfaz con barra lateral, estadísticas y heatmap.
- **Plan 002** — `specs/002-ui-redesign/plan.md`: modelo de datos del icono, algoritmos de estadísticas y estrategia de tests.
- **Tareas 002** — `specs/002-ui-redesign/tasks.md`: checklist de implementación del rediseño.
- **Plan de implementación** — `specs/001-habits-mvp/plan.md`: arquitectura, modelo de datos y decisiones técnicas.
- **Tareas** — `specs/001-habits-mvp/tasks.md`: checklist de tareas con criterios de aceptación.

## Agent Skills

- **spec-creator (OpenCode)** — `.opencode/skills/spec-creator/`: skill adaptada para OpenCode que permite crear especificaciones de nuevas funcionalidades siguiendo el proceso spec-driven del proyecto. Incluye plantillas para `spec.md`, `plan.md` y `tasks.md`.
- **spec-creator (Junie, legado)** — `.junie/skills/spec-creator/`: versión original de la skill conservada para compatibilidad con Junie.
- **commit (OpenCode)** — `.opencode/skills/commit/`: skill que prepara commits siguiendo la convención del repositorio (un commit por fase de spec, asunto `feature: …, spec<NNN> f<FASE>`) y verifica la suite antes de commitear.

## Licencia

Este proyecto está bajo la [Apache License 2.0](LICENSE).
