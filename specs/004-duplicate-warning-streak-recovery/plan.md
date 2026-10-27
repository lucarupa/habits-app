# Plan de Implementación — 004 Aviso de registro duplicado y recuperación de racha

## Estructura de módulos

```
habits/
├── core.py          # Lógica de dominio: modelos, rachas, huecos y heatmap
├── storage.py       # Persistencia SQLite: hábitos, registros y recuperados
├── app_state.py     # Estado de la aplicación: une storage y core sin Flet
├── registration.py  # Registro del día actual y mensajes de duplicado
├── theme.py         # Colores del heatmap y dimensiones de ventana
└── app.py           # Interfaz Flet: panel, diálogo, aviso y heatmap
tests/
├── test_core.py                    # Dominio y algoritmos de huecos
├── test_storage.py                 # Persistencia y migración
├── test_app_state.py               # Estado, estadísticas y heatmap
├── test_registration.py            # Registro y mensaje de duplicado
├── test_registration_widgets.py    # Panel y diálogo de recuperación
├── test_stats_heatmap.py           # Tarjetas y heatmap con recuperados
├── test_recovery_flow.py           # Flujo integrado de recuperación
├── test_duplicate_warning_flow.py  # Flujo integrado del aviso
├── test_readme_edit_delete.py      # Documentación y conteos
└── test_scope_guard_003.py         # Alcance y esquema permitido
data/
└── habits.db        # Base de datos SQLite (runtime)
```

- **`habits/core.py`** — Cubre RF-2.1 a RF-2.3, RF-2.9 a RF-2.11 y RF-3.1 a RF-3.5.
  Añade la detección pura del hueco recuperable, la exclusión de días recuperados del
  contador de “Días registrados” y el estado `recovered` del heatmap.
- **`habits/storage.py`** — Cubre RF-2.8, RF-2.15, RF-2.16 y RF-2.17. Añade la columna
  `recovered`, la migración de bases existentes y la escritura atómica de días recuperados.
- **`habits/app_state.py`** — Cubre RF-2.1, RF-2.12, RF-3.1 y RF-3.3. Carga los días
  recuperados, calcula el hueco del hábito seleccionado y propaga el estado al heatmap.
- **`habits/registration.py`** — Cubre RF-1.2 y RF-1.4. Centraliza el texto del aviso de
  duplicado y conserva la prevención de registros repetidos.
- **`habits/theme.py`** — Cubre RF-2.11. Define el color del estado recuperado del heatmap.
- **`habits/app.py`** — Cubre RF-1.1 a RF-1.9, RF-2.4 a RF-2.8, RF-2.12 a RF-2.14 y
  RF-3.1 a RF-3.6. Añade el aviso emergente, la acción “Recuperar racha”, el diálogo de
  confirmación, la leyenda del heatmap y la conexión con la persistencia en `main`.

---

## Modelo de datos

### Tabla `completions` (modificada)

| Columna | Tipo | Restricción | Descripción |
|---------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Identificador único del registro |
| `habit_id` | INTEGER | NOT NULL, FK `habits.id` | Hábito al que pertenece |
| `completed_date` | TEXT | NOT NULL, UNIQUE con `habit_id` | Fecha en formato YYYY-MM-DD |
| `recovered` | INTEGER | NOT NULL DEFAULT 0 | 0 = registro normal; 1 = día recuperado |

No se crean tablas nuevas. Un día recuperado sigue siendo una fila de `completions`, pero
con `recovered = 1`. La restricción `UNIQUE(habit_id, completed_date)` impide duplicados entre
registros normales y recuperados.

### Migración

`init_db` comprueba `PRAGMA table_info(completions)`. Si la columna `recovered` no existe,
ejecuta `ALTER TABLE completions ADD COLUMN recovered INTEGER NOT NULL DEFAULT 0`. Las bases de
datos existentes conservan todos sus registros y los interpretan como normales. La operación es
idempotente, igual que la migración previa de la columna `icon` en `habits`.

### Ejemplo de datos

```
completions:
| id | habit_id | completed_date | recovered |
|----|----------|----------------|-----------|
| 1  | 1        | 2026-10-18     | 0         |
| 2  | 1        | 2026-10-19     | 0         |
| 3  | 1        | 2026-10-20     | 1         |
| 4  | 1        | 2026-10-21     | 0         |
```

El hábito 1 tiene dos días normales, un día recuperado y otro normal. La racha actual y la
mejor racha cuentan las cuatro fechas; “Días registrados” cuenta solo las filas con
`recovered = 0`. El heatmap pinta el 20/10 como recuperado y los demás como completados.

---

## Algoritmos clave (pseudocódigo)

### Detectar el hueco recuperable (RF-2.1 a RF-2.3, RF-2.18)

```
funcion find_recoverable_gap(completed_dates, today):
    si completed_dates está vacío:
        retornar None

    fechas = ordenar(completed_dates)
    ultima = fechas[-1]

    # Hueco de cola: días entre el último registro y hoy, sin incluir hoy.
    cola = días desde ultima + 1 hasta today - 1
    si longitud(cola) == 1 o 2:
        retornar RecoverableGap(cola)
    si longitud(cola) >= 3:
        retornar None

    # No hay hueco de cola (hoy o ayer ya están registrados).
    # Buscar el hueco más reciente entre dos registros consecutivos.
    para cada par (anterior, siguiente) en orden descendente:
        hueco = días entre anterior y siguiente, excluyendo extremos
        si longitud(hueco) == 1 o 2:
            retornar RecoverableGap(hueco)
        si longitud(hueco) >= 3:
            retornar None

    retornar None
```

**Casos cubiertos:**
- RF-2.1: un hueco de uno o dos días devuelve sus fechas.
- RF-2.2: un hueco de tres o más días devuelve `None`, aunque existan huecos anteriores.
- RF-2.3: un hábito sin registros devuelve `None`.
- RF-2.18: solo se devuelve el hueco más reciente.
- El día de hoy nunca forma parte del hueco; si no está registrado, se registra después con
  la acción normal.

### Calcular estadísticas con días recuperados (RF-2.9, RF-2.10)

```
funcion get_habit_stats(completed_dates, today, recovered_dates = vacío):
    racha_actual = calculate_streak(completed_dates, today)
    mejor_racha = calculate_best_streak(completed_dates)
    dias_registrados = count_registered_days(
        completed_dates,
        recovered_dates
    )
    retornar HabitStats(racha_actual, mejor_racha, dias_registrados)

funcion count_registered_days(completed_dates, recovered_dates = vacío):
    retornar longitud(completed_dates - recovered_dates)
```

`calculate_streak` y `calculate_best_streak` no cambian: reciben todas las fechas, incluidas
las recuperadas. Solo “Días registrados” excluye el subconjunto recuperado.

### Marcar días recuperados (RF-2.8, RF-2.15 a RF-2.17)

```
funcion mark_recovered_days_db(habit_id, fechas, db_path):
    abrir conexión y BEGIN

    si el hábito no existe:
        rollback
        lanzar ValueError("El hábito no existe.")

    para cada fecha en fechas:
        INSERT OR IGNORE INTO completions
            (habit_id, completed_date, recovered)
            VALUES (habit_id, fecha, 1)

    commit
    cerrar conexión
```

`INSERT OR IGNORE` conserva intacto cualquier registro normal que ya exista para esa fecha.
Si falla cualquier inserción, la transacción se revierte completa y no quedan días recuperados
parciales.

### Aviso de registro duplicado (RF-1.1 a RF-1.5)

```
funcion on_register_today():
    seleccionado = estado.seleccionado
    si seleccionado es None:
        retornar

    resultado = register_today(seleccionado.id, estado.hoy, db_path)
    si resultado.success es falso:
        mostrar SnackBar(duplicate_warning(seleccionado.nombre))
    registration.message = resultado.message
    refresh_views(seleccionado.id)
```

`register_today` sigue siendo la única vía de persistencia del día actual y conserva la
prevención de duplicados. El aviso solo se muestra cuando el resultado es de duplicado; un
registro correcto no muestra el SnackBar.

---

## Decisiones técnicas

### 1. Marcar los días recuperados con una columna en `completions`

**Decisión:** Añadir `recovered INTEGER NOT NULL DEFAULT 0` a `completions` y migrar las bases
existentes.

**Alternativa descartada:** Crear una tabla separada `recovered_days`.

**Justificación:** La columna reutiliza la restricción `UNIQUE(habit_id, completed_date)`, evita
duplicados entre un registro normal y uno recuperado, simplifica las consultas de racha y
heatmap y permite borrar todos los registros con el hábito en la misma transacción. Una tabla
separada obligaría a unir dos fuentes y aumentaría el riesgo de datos huérfanos (RF-2.15 y
RF-2.16).

### 2. Mantener `get_completions_db` devolviendo todas las fechas

**Decisión:** `get_completions_db` sigue devolviendo todas las fechas, incluidas las
recuperadas. Se añade `get_recovered_dates_db` para obtener el subconjunto con
`recovered = 1`.

**Alternativa descartada:** Cambiar `get_completions_db` para devolver solo registros normales.

**Justificación:** El cálculo de racha necesita todas las fechas y los llamadores existentes
esperan la lista completa. Añadir una consulta específica mantiene la compatibilidad y permite
que `app_state` calcule el subconjunto normal sin duplicar SQL.

### 3. Extender las funciones puras con parámetros opcionales

**Decisión:** `get_habit_stats`, `count_registered_days` y `build_activity_heatmap` reciben
`recovered_dates` con valor por defecto vacío. `HeatmapDay` añade `recovered: bool = False` al
final.

**Alternativa descartada:** Cambiar las firmas de forma obligatoria y actualizar todos los
llamadores de golpe.

**Justificación:** Los valores por defecto preservan los tests y el comportamiento de las specs
001–003, y permiten que solo los llamadores nuevos pasen el subconjunto recuperado. El campo
nuevo del heatmap tiene valor por defecto para no romper construcciones posicionales existentes.

### 4. Recuperar solo el hueco más reciente

**Decisión:** `find_recoverable_gap` devuelve como máximo un hueco, el más reciente, y solo si
tiene uno o dos días. Si el hueco más reciente tiene tres o más días, no se ofrece recuperación
aunque existan huecos anteriores más pequeños.

**Alternativa descartada:** Recuperar todos los huecos pequeños del historial en una sola
acción.

**Justificación:** La spec limita la recuperación a un máximo de dos días y a la racha rota más
reciente (RF-2.2 y RF-2.18). Recuperar huecos antiguos alteraría el historial sin relación con
la racha que el usuario acaba de perder.

### 5. La acción vive en el panel y la persistencia en `main`

**Decisión:** `TodayRegistrationPanel` muestra “Recuperar racha” y delega en `main` mediante un
callback. `StreakRecoveryDialog` solo confirma y devuelve el hábito y las fechas; `main` llama a
`mark_recovered_days_db` y recarga la vista.

**Alternativa descartada:** Hacer que el diálogo o el panel accedan directamente a SQLite.

**Justificación:** Respeta la Constitución (principio 3) y el patrón ya usado por
`DeleteHabitDialog`. La interfaz no contiene cálculos ni acceso a datos, y el flujo se puede
probar con una página Flet simulada.

### 6. Aviso de duplicado mediante SnackBar no bloqueante

**Decisión:** Al recibir un resultado de duplicado de `register_today`, `main` muestra un
`SnackBar` con el texto “⚠️ «nombre» ya está registrado hoy.” y mantiene el mensaje
“Ya registrado hoy” del panel.

**Alternativa descartada:** Abrir un diálogo modal o deshabilitar el botón “Guardar”.

**Justificación:** El usuario quiere un aviso claro pero no bloqueante (RF-1.6 y RF-1.8). Un
diálogo interrumpiría el flujo y deshabilitar el botón impediría que el clic produzca el aviso
solicitado.

### 7. Heatmap con estado recuperado propio

**Decisión:** Añadir un color ámbar para los días recuperados, una etiqueta “Recuperado” en la
leyenda y un tooltip específico. Los días recuperados se pintan con prioridad sobre el verde de
completado.

**Alternativa descartada:** Pintar los días recuperados igual que los completados.

**Justificación:** RF-2.11 exige distinguirlos para que el usuario sepa qué días registró y
cuáles recuperó. El color debe ser distinto del verde de completado y del gris de no completado.

### 8. Migración idempotente y transacción atómica

**Decisión:** Migrar con `ALTER TABLE ... ADD COLUMN` solo si falta la columna. La escritura de
días recuperados usa una transacción con `INSERT OR IGNORE` y comprueba la existencia del
hábito.

**Alternativa descartada:** Recrear la tabla `completions` o insertar fila por fila sin
transacción.

**Justificación:** Recrear la tabla es más arriesgado para datos existentes. La transacción
garantiza RF-2.16 (sin recuperaciones parciales) y `INSERT OR IGNORE` garantiza RF-2.17 (no
modificar registros normales existentes).

---

## Estrategia de tests

### Tests de `habits/core.py` (`test_core.py`)

| Prueba | RF cubierto | Descripción |
|--------|-------------|-------------|
| `test_find_recoverable_gap_without_dates` | RF-2.3 | Sin registros no hay hueco. |
| `test_find_recoverable_gap_one_day_between_records` | RF-2.1 | Un día faltante entre dos registros. |
| `test_find_recoverable_gap_two_days_between_records` | RF-2.1 | Dos días faltantes entre dos registros. |
| `test_find_recoverable_gap_three_days_returns_none` | RF-2.2 | Un hueco de tres días no se recupera. |
| `test_find_recoverable_gap_one_day_before_today` | RF-2.1, RF-2.13 | Hueco de cola de un día. |
| `test_find_recoverable_gap_two_days_before_today` | RF-2.1, RF-2.13 | Hueco de cola de dos días. |
| `test_find_recoverable_gap_three_days_before_today_returns_none` | RF-2.2 | Hueco de cola de tres días. |
| `test_find_recoverable_gap_today_completed_with_two_day_gap` | RF-2.1, RF-2.14 | Hoy registrado y hueco anterior de dos días. |
| `test_find_recoverable_gap_ignores_older_gap_when_latest_is_large` | RF-2.2, RF-2.18 | El hueco más reciente manda. |
| `test_find_recoverable_gap_returns_latest_small_gap` | RF-2.18 | Se devuelve el hueco más reciente. |
| `test_stats_include_recovered_days_in_streaks` | RF-2.9 | Racha actual y mejor racha incluyen recuperados. |
| `test_registered_days_exclude_recovered_days` | RF-2.10 | “Días registrados” no cuenta recuperados. |
| `test_heatmap_marks_recovered_days` | RF-2.11 | La celda recuperada tiene `completed=True` y `recovered=True`. |

### Tests de `habits/storage.py` (`test_storage.py`)

| Prueba | RF cubierto | Descripción |
|--------|-------------|-------------|
| `test_init_db_adds_recovered_column` | RF-2.15 | La tabla nueva incluye `recovered` con 0 por defecto. |
| `test_init_db_migrates_existing_completions_table` | RF-2.15 | Una base antigua recibe la columna sin perder filas. |
| `test_mark_recovered_days_db_persists_flagged_rows` | RF-2.8 | Las fechas se guardan con `recovered = 1`. |
| `test_mark_recovered_days_db_keeps_existing_normal_record` | RF-2.17 | Un registro normal previo no se convierte en recuperado. |
| `test_mark_recovered_days_db_raises_for_unknown_habit` | RF-2.16 | Un hábito inexistente no deja filas. |
| `test_get_recovered_dates_db_returns_only_recovered` | RF-2.8 | Solo devuelve las fechas recuperadas, ordenadas. |
| `test_get_completions_db_includes_recovered_dates` | RF-2.9 | La consulta general incluye recuperados para la racha. |
| `test_delete_habit_db_removes_recovered_days` | RF-2.15 | El borrado no deja registros recuperados huérfanos. |

### Tests de `habits/app_state.py` (`test_app_state.py`)

| Prueba | RF cubierto | Descripción |
|--------|-------------|-------------|
| `test_load_app_state_reads_recovered_dates` | RF-2.15 | El estado conserva el subconjunto recuperado. |
| `test_recoverable_gap_follows_selected_habit` | RF-2.1, RF-2.12 | El hueco se calcula para el hábito seleccionado. |
| `test_recoverable_gap_is_none_for_three_days` | RF-2.2 | Un hueco largo no ofrece acción. |
| `test_stats_cards_exclude_recovered_from_registered_days` | RF-2.10 | La tarjeta de días registrados no cuenta recuperados. |
| `test_heatmap_cells_flag_recovered_days` | RF-2.11 | El heatmap recibe las fechas recuperadas. |

### Tests de `habits/registration.py` (`test_registration.py`)

| Prueba | RF cubierto | Descripción |
|--------|-------------|-------------|
| `test_duplicate_warning_uses_habit_name` | RF-1.2 | El texto incluye el nombre y el formato acordado. |
| `test_register_today_still_rejects_duplicates` | RF-1.3 | El registro duplicado no inserta una segunda fila. |

### Tests de widgets y flujos (`test_registration_widgets.py`, `test_stats_heatmap.py`)

| Prueba | RF cubierto | Descripción |
|--------|-------------|-------------|
| `test_panel_shows_recover_button_for_one_day_gap` | RF-2.1 | La acción aparece con un hueco de un día. |
| `test_panel_shows_recover_button_for_two_day_gap` | RF-2.1 | La acción aparece con un hueco de dos días. |
| `test_panel_hides_recover_button_for_three_day_gap` | RF-2.2 | La acción no aparece con un hueco largo. |
| `test_panel_hides_recover_button_without_records` | RF-2.3 | La acción no aparece sin historial. |
| `test_recover_button_notifies_main` | RF-2.4 | El panel delega la acción en su callback. |
| `test_recovery_dialog_shows_name_and_day_count` | RF-2.4, RF-2.5 | El diálogo explica qué se recuperará. |
| `test_recovery_dialog_cancel_keeps_state` | RF-2.7 | Cancelar no notifica ni modifica la racha. |
| `test_recovery_dialog_confirm_notifies_dates` | RF-2.8 | Confirmar devuelve el hábito y las fechas. |
| `test_heatmap_legend_includes_recovered` | RF-2.11 | La leyenda muestra “Recuperado”. |
| `test_recovered_cell_has_own_color_and_tooltip` | RF-2.11 | La celda recuperada se distingue visualmente. |

### Tests de flujo integrado (`test_recovery_flow.py`, `test_duplicate_warning_flow.py`)

| Prueba | RF cubierto | Descripción |
|--------|-------------|-------------|
| `test_register_duplicate_shows_snackbar` | RF-1.1, RF-1.2 | El clic sobre un día ya registrado muestra el aviso con el nombre. |
| `test_register_duplicate_does_not_add_rows` | RF-1.3 | El aviso no crea un registro extra. |
| `test_register_new_day_does_not_show_duplicate_warning` | RF-1.4 | El registro normal no muestra el aviso. |
| `test_recover_streak_updates_db_and_view` | RF-2.8 a RF-2.12 | Confirmar recupera los días, actualiza racha y oculta la acción. |
| `test_recover_streak_keeps_registered_days` | RF-2.10 | “Días registrados” no cambia. |
| `test_recover_streak_persists_after_reload` | RF-2.15 | Los días recuperados sobreviven a una recarga. |
| `test_recover_streak_cancel_changes_nothing` | RF-2.7 | Cancelar deja la base y la vista igual. |
| `test_recover_streak_database_error_keeps_state` | RF-2.16 | Un fallo no deja recuperaciones parciales y muestra aviso. |

### Tests de documentación y alcance

| Prueba | RF cubierto | Descripción |
|--------|-------------|-------------|
| `test_readme_documents_duplicate_warning` | RF-1 | El README explica el aviso y su texto. |
| `test_readme_documents_streak_recovery` | RF-2 | El README explica el límite de dos días, el diálogo y las estadísticas. |
| `test_readme_documents_recovered_heatmap_state` | RF-2.11 | El README menciona el estado “Recuperado”. |
| `test_scope_guard_allows_recovered_column` | RF-2.15 | El esquema permitido incluye `recovered` y sigue sin tablas fuera de alcance. |
| `test_scope_guard_rejects_manual_gap_selection` | RF-2.18 | La interfaz no permite elegir días concretos ni recuperar huecos largos. |

### Cobertura objetivo

- ≥80 % en `habits/core.py`.
- ≥80 % en `habits/storage.py`.
- ≥80 % en `habits/app_state.py`.
- ≥80 % en `habits/registration.py`.
- `habits/app.py` se valida con tests de widgets y flujos integrados con una página simulada.

### Ejecución

```bash
pytest -q
.venv/bin/python -m pytest -q
pytest --cov=habits --cov-report=term-missing -q
```
