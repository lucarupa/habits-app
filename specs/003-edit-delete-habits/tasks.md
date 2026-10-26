# Tareas de implementación — 003 Edición y eliminación de hábitos

## Fase 1: Dominio de edición (`core.py`)

- [x] **Tarea 1.1:** Escribir los tests de `update_habit`
  - **RF:** RF-2.3, RF-2.4, RF-2.7, RF-2.8, RF-2.9, RF-2.12
  - **Hecho cuando:** `tests/test_core.py` incluye los seis casos del plan (campos e ID, recorte
    de nombre, nombre vacío, nombre largo, fecha futura e icono inválido) y fallan porque la
    función todavía no existe.

- [x] **Tarea 1.2:** Implementar `update_habit` en `core.py`
  - **RF:** RF-2.3, RF-2.4, RF-2.7, RF-2.8, RF-2.12
  - **Hecho cuando:** La función valida nombre y fecha, conserva el ID y el icono actual cuando
    corresponde, y todos los tests de la tarea 1.1 pasan.

## Fase 2: Persistencia de edición y eliminación (`storage.py`)

- [x] **Tarea 2.1:** Escribir los tests de `update_habit_db`
  - **RF:** RF-2.13, RF-2.14
  - **Hecho cuando:** `tests/test_storage.py` comprueba que actualiza una fila existente, que
    persiste los tres campos y que lanza error con un ID inexistente; los tests fallan porque la
    función no existe.

- [x] **Tarea 2.2:** Escribir los tests de `delete_habit_db`
  - **RF:** RF-3.4, RF-3.8
  - **Hecho cuando:** `tests/test_storage.py` comprueba que borra el hábito y sus registros, que
    no afecta a otros hábitos y que lanza error con un ID inexistente; los tests fallan porque
    la función no existe.

- [x] **Tarea 2.3:** Implementar `update_habit_db` y `delete_habit_db`
  - **RF:** RF-2.13, RF-2.14, RF-3.4, RF-3.8, RFN-1
  - **Hecho cuando:** La actualización escribe nombre, fecha e icono; el borrado elimina primero
    los registros y después el hábito dentro de una transacción; los tests de las tareas 2.1 y
    2.2 pasan y no quedan registros huérfanos.

## Fase 3: Lógica del formulario de edición (`habit_form.py`)

- [x] **Tarea 3.1:** Escribir los tests de validación y persistencia de la edición
  - **RF:** RF-2.3, RF-2.5, RF-2.7, RF-2.8, RF-2.9, RF-2.12, RF-2.14
  - **Hecho cuando:** `tests/test_habit_form.py` cubre fecha vacía que conserva la actual, fecha
    futura rechazada, icono ausente que conserva el actual, nombre vacío, persistencia correcta y
    registros intactos; los tests fallan porque las funciones no existen.

- [x] **Tarea 3.2:** Implementar `UpdateHabitResult`, `validate_habit_update` y
  `update_habit_from_form`
  - **RF:** RF-2.3, RF-2.5, RF-2.7, RF-2.8, RF-2.9, RF-2.12, RF-2.14
  - **Hecho cuando:** La validación reutiliza las reglas de nombre, resuelve la fecha de edición
    de forma estricta, delega en `update_habit` y `update_habit_db`, y todos los tests de la
    tarea 3.1 pasan.

## Fase 4: Calendario y modo edición del modal (`app.py`)

- [ ] **Tarea 4.1:** Escribir los tests del calendario en el diálogo de creación
  - **RF:** RF-5.1, RF-5.3, RF-5.4, RF-5.5, RF-5.6, RF-5.7, RF-5.8
  - **Hecho cuando:** `tests/test_habit_dialog.py` comprueba que el campo de fecha es de solo
    lectura, que muestra la fecha actual al abrir, que al pulsarlo se muestra un calendario con
    los días futuros bloqueados, que elegir una fecha actualiza el campo sin cerrar el modal, que
    cancelar conserva el valor y que el calendario usa español. Se actualizan los tests
    existentes que esperaban un campo de fecha vacío.

- [ ] **Tarea 4.2:** Implementar el calendario y el campo de fecha de solo lectura
  - **RF:** RF-5.1, RF-5.3, RF-5.4, RF-5.5, RF-5.6, RF-5.7, RF-5.8
  - **Hecho cuando:** El diálogo usa un calendario de Flet en modo solo calendario, con última
    fecha igual a hoy, idioma español y campo de fecha no editable; los tests de la tarea 4.1
    pasan.

- [ ] **Tarea 4.3:** Escribir los tests del modo edición del modal
  - **RF:** RF-1.3, RF-2.1, RF-2.2, RF-2.3, RF-2.4, RF-2.9, RF-2.10, RF-5.2
  - **Hecho cuando:** `tests/test_habit_dialog.py` comprueba que el modo edición precarga nombre,
    icono y fecha, que guardar persiste y notifica, que cancelar no modifica el hábito y que un
    error de validación mantiene el modal abierto; los tests fallan porque el modo edición no
    existe.

- [ ] **Tarea 4.4:** Implementar el modo edición del `HabitFormDialog`
  - **RF:** RF-1.3, RF-2.1, RF-2.2, RF-2.9, RF-2.10, RF-5.2
  - **Hecho cuando:** El diálogo distingue creación y edición, precarga los datos del hábito,
    cambia el título, envía la edición a `update_habit_from_form` y conserva el flujo de creación;
    los tests de la tarea 4.3 pasan y los de creación siguen verdes.

## Fase 5: Acciones del detalle y confirmación de borrado (`app.py`)

- [ ] **Tarea 5.1:** Escribir los tests de las acciones del detalle
  - **RF:** RF-1.1, RF-1.2, RF-1.3, RF-1.4, RF-1.5
  - **Hecho cuando:** Los tests comprueban que “Editar” y “Eliminar” aparecen con un hábito
    seleccionado, que no aparecen en el estado vacío, que la barra lateral no las muestra y que
    cada botón invoca su callback con el ID correcto; fallan porque las acciones no existen.

- [ ] **Tarea 5.2:** Implementar las acciones en `HabitDetailHeader`
  - **RF:** RF-1.1, RF-1.2, RF-1.3, RF-1.4, RF-1.5
  - **Hecho cuando:** El encabezado muestra ambas acciones, las oculta sin selección y notifica
    edición y eliminación mediante callbacks; los tests de la tarea 5.1 pasan.

- [ ] **Tarea 5.3:** Escribir los tests del diálogo de confirmación de borrado
  - **RF:** RF-3.1, RF-3.2, RF-3.3, RF-3.5
  - **Hecho cuando:** Los tests comprueban que el diálogo muestra el nombre y la advertencia, que
    ofrece “Cancelar” y “Eliminar”, que cancelar no borra nada y que solo se notifica al
    confirmar; fallan porque el diálogo no existe.

- [ ] **Tarea 5.4:** Implementar el diálogo de confirmación de borrado
  - **RF:** RF-3.1, RF-3.2, RF-3.3, RF-3.5
  - **Hecho cuando:** El diálogo muestra el nombre del hábito, advierte del borrado permanente de
    sus registros, cancela sin cambios y notifica la confirmación con el ID; los tests de la
    tarea 5.3 pasan.

## Fase 6: Integración en `main` (`app.py`)

- [ ] **Tarea 6.1:** Escribir los tests del flujo integrado de edición
  - **RF:** RF-2.9, RF-4.1, RF-4.2, RF-4.3, RF-4.4, RF-4.7
  - **Hecho cuando:** `tests/test_edit_delete_flow.py` comprueba que editar desde el detalle
    actualiza barra lateral y encabezado, mantiene la selección, reordena si cambia el nombre y
    conserva estadísticas, heatmap y registros; fallan porque `main` aún no conecta la edición.

- [ ] **Tarea 6.2:** Escribir los tests del flujo integrado de eliminación
  - **RF:** RF-3.4, RF-3.6, RF-3.7, RF-3.8, RF-4.5, RF-4.6
  - **Hecho cuando:** `tests/test_edit_delete_flow.py` comprueba que confirmar borra hábito y
    registros, que se selecciona el siguiente hábito, que al borrar el último aparece el estado
    vacío, que se puede crear otro después y que un error de persistencia conserva el hábito;
    fallan porque `main` aún no conecta la eliminación.

- [ ] **Tarea 6.3:** Conectar edición y eliminación en `main`
  - **RF:** RF-1.3, RF-1.4, RF-3.3, RF-3.6, RF-3.7, RF-3.8, RF-4.1 a RF-4.7
  - **Hecho cuando:** Los callbacks del encabezado abren el modal de edición y el diálogo de
    confirmación; guardar refresca conservando el hábito editado; confirmar borra y recarga la
    selección o el estado vacío; los tests de las tareas 6.1 y 6.2 pasan.

## Fase 7: Documentación y verificación final

- [ ] **Tarea 7.1:** Actualizar `README.md`
  - **RF:** Todos
  - **Hecho cuando:** El README documenta la edición, la eliminación con confirmación, el
    calendario de fecha, el borrado de registros asociados y los nuevos conteos de tests.

- [ ] **Tarea 7.2:** Ejecutar la suite completa y la cobertura
  - **RF:** RFN-3, RFN-7
  - **Hecho cuando:** `pytest -q` y `.venv\Scripts\python.exe -m pytest -q` pasan sin fallos y la
    cobertura de `core.py`, `storage.py` y `habit_form.py` es ≥80 %.

- [ ] **Tarea 7.3:** Verificar manualmente los criterios de finalización y el alcance
  - **RF:** Todos
  - **Hecho cuando:** Se comprueba en la aplicación que editar y eliminar funcionan, que el
    calendario bloquea futuras, que la selección posterior es correcta y que no se añadieron
    deshacer, archivar, borrado masivo ni edición de registros. `tasks.md` queda marcado.
