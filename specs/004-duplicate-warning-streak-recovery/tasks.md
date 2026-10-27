# Tareas de implementación — 004 Aviso de registro duplicado y recuperación de racha

## Fase 1: Detección del hueco recuperable (`core.py`)

- [x] **Tarea 1.1:** Escribir los tests de `find_recoverable_gap`
  - **RF:** RF-2.1, RF-2.2, RF-2.3, RF-2.18
  - **Hecho cuando:** Los tests cubren huecos de 1, 2 y 3 días entre registros, huecos de cola
    antes de hoy, hoy registrado, ausencia de registros y elección del hueco más reciente; la
    suite muestra los fallos esperados porque la función aún no existe.

- [x] **Tarea 1.2:** Implementar `RecoverableGap` y `find_recoverable_gap`
  - **RF:** RF-2.1, RF-2.2, RF-2.3, RF-2.18
  - **Hecho cuando:** La función pura devuelve las fechas del hueco más reciente cuando tiene
    uno o dos días, devuelve `None` en los demás casos y los tests de la tarea 1.1 pasan.

- [x] **Tarea 1.3:** Escribir los tests de estadísticas y heatmap con días recuperados
  - **RF:** RF-2.9, RF-2.10, RF-2.11
  - **Hecho cuando:** Los tests verifican que la racha actual y la mejor racha incluyen los
    recuperados, que “Días registrados” los excluye y que la celda del heatmap se marca como
    recuperada; la suite muestra los fallos esperados.

- [x] **Tarea 1.4:** Extender `get_habit_stats`, `count_registered_days` y el heatmap
  - **RF:** RF-2.9, RF-2.10, RF-2.11
  - **Hecho cuando:** Las funciones aceptan `recovered_dates` con valor por defecto vacío,
    `HeatmapDay` incluye `recovered` y los tests de la tarea 1.3 pasan sin romper los tests
    existentes de rachas y heatmap.

## Fase 2: Persistencia de días recuperados (`storage.py`)

- [ ] **Tarea 2.1:** Escribir los tests del esquema y de la migración
  - **RF:** RF-2.8, RF-2.15, RF-2.17
  - **Hecho cuando:** Los tests comprueban que una base nueva tiene `recovered` con valor 0 por
    defecto, que una base antigua recibe la columna sin perder registros y que la migración es
    idempotente; la suite muestra los fallos esperados.

- [ ] **Tarea 2.2:** Implementar la columna `recovered` y la migración en `init_db`
  - **RF:** RF-2.8, RF-2.15, RF-2.17
  - **Hecho cuando:** `init_db` crea la columna en bases nuevas y la añade a las existentes
    mediante una comprobación de columnas, y los tests de la tarea 2.1 pasan.

- [ ] **Tarea 2.3:** Escribir los tests de `mark_recovered_days_db` y `get_recovered_dates_db`
  - **RF:** RF-2.8, RF-2.15, RF-2.16, RF-2.17
  - **Hecho cuando:** Los tests cubren la inserción con `recovered = 1`, la conservación de un
    registro normal previo, el error con un hábito inexistente sin filas parciales, la consulta
    ordenada de recuperados y el borrado del hábito con sus recuperados; la suite muestra los
    fallos esperados.

- [ ] **Tarea 2.4:** Implementar la escritura y consulta de días recuperados
  - **RF:** RF-2.8, RF-2.15, RF-2.16, RF-2.17
  - **Hecho cuando:** `mark_recovered_days_db` inserta en una transacción con `INSERT OR IGNORE`,
    `get_recovered_dates_db` devuelve solo las fechas recuperadas y los tests de la tarea 2.3
    pasan.

## Fase 3: Estado y estadísticas de la aplicación (`app_state.py`)

- [ ] **Tarea 3.1:** Escribir los tests de carga y cálculo con recuperados
  - **RF:** RF-2.1, RF-2.2, RF-2.9, RF-2.10, RF-2.11, RF-2.12, RF-2.15
  - **Hecho cuando:** Los tests verifican que el estado carga `recovered_dates`, que el hueco
    recuperable sigue al hábito seleccionado, que las tarjetas excluyen recuperados de “Días
    registrados” y que el heatmap recibe las fechas recuperadas; la suite muestra los fallos
    esperados.

- [ ] **Tarea 3.2:** Implementar `HabitState.recovered_dates`, la carga y el hueco recuperable
  - **RF:** RF-2.1, RF-2.2, RF-2.9, RF-2.10, RF-2.11, RF-2.12, RF-2.15
  - **Hecho cuando:** `load_app_state` lee las fechas recuperadas, `HabitState` las conserva,
    `AppState` expone el hueco del hábito seleccionado, `heatmap_cells` propaga las fechas
    recuperadas y los tests de la tarea 3.1 pasan.

- [ ] **Tarea 3.3:** Añadir la etiqueta del heatmap y ajustar las pruebas de estado existentes
  - **RF:** RF-2.11
  - **Hecho cuando:** Existe la etiqueta “Recuperado” en el estado, los tests de `test_app_state`
    y `test_stats_heatmap` pasan y no se rompe ninguna construcción previa de `HabitState` o
    `HeatmapDay`.

## Fase 4: Aviso de registro duplicado (`registration.py` y `app.py`)

- [ ] **Tarea 4.1:** Escribir los tests del texto y del flujo de duplicado
  - **RF:** RF-1.1 a RF-1.9
  - **Hecho cuando:** Los tests cubren el texto “⚠️ «nombre» ya está registrado hoy.”, que un
    clic duplicado muestra el aviso sin insertar otra fila, que un registro nuevo no muestra el
    aviso y que el panel muestra “Ya registrado hoy” al intentar duplicar; la suite muestra los
    fallos esperados.

- [ ] **Tarea 4.2:** Implementar el texto del aviso y el SnackBar en `main`
  - **RF:** RF-1.1 a RF-1.9
  - **Hecho cuando:** `registration.py` expone una función pura para el texto, `main` muestra un
    `SnackBar` no bloqueante solo cuando `register_today` devuelve duplicado y los tests de la
    tarea 4.1 pasan.

## Fase 5: Recuperación en la interfaz (`app.py`)

- [ ] **Tarea 5.1:** Escribir los tests de la acción “Recuperar racha” en el panel
  - **RF:** RF-2.1, RF-2.2, RF-2.3, RF-2.4
  - **Hecho cuando:** Los tests verifican que la acción aparece con huecos de uno y dos días, se
    oculta con tres días o sin registros, y notifica al callback de `main`; la suite muestra los
    fallos esperados.

- [ ] **Tarea 5.2:** Implementar el botón “Recuperar racha” en `TodayRegistrationPanel`
  - **RF:** RF-2.1, RF-2.2, RF-2.3, RF-2.4
  - **Hecho cuando:** El panel consulta el hueco del estado, muestra u oculta la acción y delega
    el clic en `on_recover`; los tests de la tarea 5.1 pasan.

- [ ] **Tarea 5.3:** Escribir los tests del diálogo de recuperación
  - **RF:** RF-2.4 a RF-2.8, RF-2.19
  - **Hecho cuando:** Los tests cubren el título, el nombre del hábito, el número de días, la
    advertencia sobre estadísticas, “Cancelar” sin cambios y “Recuperar” notificando las fechas;
    la suite muestra los fallos esperados.

- [ ] **Tarea 5.4:** Implementar `StreakRecoveryDialog`
  - **RF:** RF-2.4 a RF-2.8, RF-2.19
  - **Hecho cuando:** El diálogo modal se abre con los datos del hábito, cierra sin notificar al
    cancelar, notifica el hábito y las fechas al confirmar y los tests de la tarea 5.3 pasan.

- [ ] **Tarea 5.5:** Escribir los tests del heatmap con estado recuperado
  - **RF:** RF-2.11
  - **Hecho cuando:** Los tests verifican la leyenda “Recuperado”, el color propio de la celda y
    el tooltip “Recuperado”; la suite muestra los fallos esperados.

- [ ] **Tarea 5.6:** Implementar el color y la leyenda del heatmap
  - **RF:** RF-2.11
  - **Hecho cuando:** `theme.py` define el color de recuperado, `ActivityHeatmap` lo usa con
    prioridad sobre el completado, añade la leyenda y el tooltip, y los tests de la tarea 5.5
    pasan.

- [ ] **Tarea 5.7:** Escribir los tests del flujo integrado de recuperación
  - **RF:** RF-2.7 a RF-2.16
  - **Hecho cuando:** Los tests montan `main`, confirman una recuperación, verifican la base de
    datos, la racha, “Días registrados”, el heatmap, la desaparición de la acción, la
    persistencia tras recargar, la cancelación y el fallo de persistencia; la suite muestra los
    fallos esperados.

- [ ] **Tarea 5.8:** Conectar la recuperación en `main`
  - **RF:** RF-2.7 a RF-2.16
  - **Hecho cuando:** `main` abre el diálogo con el hueco calculado, llama a
    `mark_recovered_days_db`, recarga conservando el hábito, muestra un aviso ante error y los
    tests de la tarea 5.7 pasan.

## Fase 6: Documentación y verificación final

- [ ] **Tarea 6.1:** Actualizar `README.md`
  - **RF:** Todos
  - **Hecho cuando:** El README documenta el aviso de duplicado, la recuperación de rachas de
    uno o dos días, el diálogo, el estado “Recuperado” del heatmap, que los recuperados no
    cuentan para “Días registrados” y los nuevos conteos de tests.

- [ ] **Tarea 6.2:** Ejecutar la suite completa y la cobertura
  - **RF:** RFN-3, RFN-4
  - **Hecho cuando:** `pytest -q` y `.venv/bin/python -m pytest -q` pasan sin fallos y la
    cobertura de `core.py`, `storage.py`, `app_state.py` y `registration.py` es ≥80 %.

- [ ] **Tarea 6.3:** Verificar los criterios de finalización y el alcance
  - **RF:** Todos
  - **Hecho cuando:** Se comprueba que el aviso aparece solo en duplicados, que la recuperación
    solo se ofrece con huecos de uno o dos días, que los recuperados cuentan para la racha pero
    no para “Días registrados”, que el heatmap los distingue y que no se añadieron selección
    manual de días, deshacer, notificaciones del sistema ni recuperación de huecos largos. Se
    actualiza la guardia de alcance y `tasks.md` queda marcado.
