# Tareas de implementación — 005 Recordatorios locales por hábito

## Fase 1: Lógica pura de recordatorios (`reminders.py`)

- [x] **Tarea 1.1:** Escribir los tests de validación, etiqueta, fecha efectiva y texto
  - **RF:** RF-1.1, RF-1.2, RF-1.6, RF-2.2, RF-3.1, RF-3.6
  - **Hecho cuando:** Los tests cubren horas válidas e inválidas, la etiqueta del estado, el
    cálculo de hoy/mañana y el texto exacto de la notificación; la suite muestra los fallos
    esperados.

- [x] **Tarea 1.2:** Implementar `habits/reminders.py`
  - **RF:** RF-1.1, RF-1.2, RF-1.6, RF-2.2, RF-3.1, RF-3.6
  - **Hecho cuando:** Las funciones puras validan HH:MM, generan la etiqueta y el texto, y
    calculan la fecha efectiva; los tests de la tarea 1.1 pasan.

- [x] **Tarea 1.3:** Escribir los tests de vencimiento del recordatorio
  - **RF:** RF-2.1, RF-2.4, RF-2.5, RF-2.7, RF-2.9, RF-2.10
  - **Hecho cuando:** Los tests cubren activo/inactivo, hora alcanzada, fecha efectiva, hábito
    completado, aviso ya enviado y fecha de inicio; la suite muestra los fallos esperados.

- [x] **Tarea 1.4:** Implementar la evaluación de vencimiento
  - **RF:** RF-2.1, RF-2.4, RF-2.5, RF-2.7, RF-2.9, RF-2.10
  - **Hecho cuando:** La función pura decide si un recordatorio vence sin acceder a SQLite ni a
    Flet; los tests de la tarea 1.3 pasan.

## Fase 2: Persistencia de recordatorios (`storage.py`)

- [x] **Tarea 2.1:** Escribir los tests del esquema y del CRUD
  - **RF:** RF-1.2, RF-1.3, RF-1.4, RF-1.7, RF-1.8, RF-3.4
  - **Hecho cuando:** Los tests cubren creación de la tabla, alta y actualización, hábito sin
    fila como desactivado, lectura y borrado junto al hábito; la suite muestra los fallos
    esperados.

- [x] **Tarea 2.2:** Implementar la tabla `reminders` y su CRUD
  - **RF:** RF-1.2, RF-1.3, RF-1.4, RF-1.7, RF-1.8, RF-3.4
  - **Hecho cuando:** `init_db` crea la tabla de forma idempotente, el CRUD persiste la
    configuración y `delete_habit_db` elimina el recordatorio en la misma transacción; los tests
    de la tarea 2.1 pasan.

- [x] **Tarea 2.3:** Escribir los tests de consulta de vencidos y reclamación
  - **RF:** RF-2.1, RF-2.4, RF-2.5, RF-2.7, RF-2.9, RFN-7
  - **Hecho cuando:** Los tests cubren filtrado por estado, hora, fecha efectiva, completado y
    aviso previo, además de reclamar y liberar la entrega; la suite muestra los fallos esperados.

- [x] **Tarea 2.4:** Implementar la consulta de vencidos y la reclamación atómica
  - **RF:** RF-2.1, RF-2.4, RF-2.5, RF-2.7, RF-2.9, RFN-7
  - **Hecho cuando:** La consulta devuelve solo recordatorios que deben avisar y la reclamación
    con `last_notified_on` evita duplicados; los tests de la tarea 2.3 pasan.

- [x] **Tarea 2.5:** Actualizar las guardias de alcance de las specs 002, 003 y 004
  - **RF:** RF-1.8, RF-2.7, RFN-5
  - **Hecho cuando:** Las guardias reconocen la tabla `reminders` y los conceptos de recordatorio
    como parte de la spec 005, mantienen prohibidos deshacer, selección manual, huecos largos y
    tablas ajenas, y toda la suite vuelve a pasar.

## Fase 3: Estado de la aplicación (`app_state.py`)

- [x] **Tarea 3.1:** Escribir los tests del recordatorio en el estado
  - **RF:** RF-1.1, RF-1.3, RF-1.7, RF-3.5
  - **Hecho cuando:** Los tests comprueban que `HabitState` expone la configuración, que un
    hábito sin fila aparece desactivado y que el nombre actualizado se refleja; la suite muestra
    los fallos esperados.

- [x] **Tarea 3.2:** Cargar el recordatorio en `HabitState` y `AppState`
  - **RF:** RF-1.1, RF-1.3, RF-1.7, RF-3.5
  - **Hecho cuando:** `load_app_state` incorpora la configuración y el estado ofrece la etiqueta
    del recordatorio del hábito seleccionado; los tests de la tarea 3.1 pasan.

## Fase 4: Adaptador de notificaciones y planificador (`notifications.py`)

- [x] **Tarea 4.1:** Escribir los tests de los comandos de notificación
  - **RF:** RF-2.3, RF-4.1, RF-4.2, RF-4.3, RFN-5
  - **Hecho cuando:** Los tests verifican los comandos de macOS y Windows, el texto enviado y la
    traducción de errores de permiso o ejecución, usando un ejecutor simulado; la suite muestra
    los fallos esperados.

- [x] **Tarea 4.2:** Implementar el notificador por plataforma
  - **RF:** RF-2.3, RF-4.1, RF-4.2, RF-4.3, RFN-5
  - **Hecho cuando:** El adaptador envía la notificación con el texto en español, informa del
    permiso y convierte los fallos en resultados controlados; los tests de la tarea 4.1 pasan.

- [x] **Tarea 4.3:** Escribir los tests de instalación y retirada del planificador
  - **RF:** RF-2.3, RF-3.4, RF-4.4
  - **Hecho cuando:** Los tests cubren instalar una única tarea periódica, actualizarla,
    eliminarla cuando no hay recordatorios y manejar un error de instalación; la suite muestra
    los fallos esperados.

- [x] **Tarea 4.4:** Implementar el planificador del sistema
  - **RF:** RF-2.3, RF-3.4, RF-4.4
  - **Hecho cuando:** El adaptador instala o retira la tarea con los comandos de cada plataforma
    y devuelve errores en español sin lanzar excepciones a la interfaz; los tests de la tarea
    4.3 pasan.

## Fase 5: Servicio y ejecución periódica (`reminder_service.py`, `reminder_runner.py`)

- [ ] **Tarea 5.1:** Escribir los tests del servicio de entrega
  - **RF:** RF-2.1, RF-2.4, RF-2.6, RF-2.7, RF-2.8, RF-3.2, RF-3.3, RF-4.5, RFN-7
  - **Hecho cuando:** Los tests cubren solo pendientes, un aviso por hábito y día, nombre
    actualizado, fecha efectiva, fallo con liberación de la reclamación y ausencia de cambios en
    las estadísticas; la suite muestra los fallos esperados.

- [ ] **Tarea 5.2:** Implementar el servicio de entrega
  - **RF:** RF-2.1, RF-2.4, RF-2.6, RF-2.7, RF-2.8, RF-3.2, RF-3.3, RF-4.5, RFN-7
  - **Hecho cuando:** El servicio recoge vencidos, reclama, notifica, confirma o libera y
    devuelve un resumen sin depender de Flet; los tests de la tarea 5.1 pasan.

- [ ] **Tarea 5.3:** Escribir los tests del runner periódico
  - **RF:** RF-2.1, RF-2.3, RF-2.10
  - **Hecho cuando:** Los tests verifican la lectura de la base y la hora actual, el resumen de
    ejecución y un fallo controlado del servicio; la suite muestra los fallos esperados.

- [ ] **Tarea 5.4:** Implementar `habits/reminder_runner.py`
  - **RF:** RF-2.1, RF-2.3, RF-2.10
  - **Hecho cuando:** El módulo puede ejecutarse con una ruta de base de datos, usa la hora local
    y devuelve un código de salida controlado; los tests de la tarea 5.3 pasan.

## Fase 6: Interfaz de configuración (`app.py`)

- [ ] **Tarea 6.1:** Escribir los tests del estado en el encabezado
  - **RF:** RF-1.1, RF-3.5
  - **Hecho cuando:** Los tests comprueban “Sin recordatorio”, la hora activa, el nombre
    actualizado y el botón “Recordatorio”; la suite muestra los fallos esperados.

- [ ] **Tarea 6.2:** Mostrar el recordatorio en el encabezado del detalle
  - **RF:** RF-1.1, RF-3.5
  - **Hecho cuando:** El encabezado muestra el estado y notifica el clic del botón sin acceder a
    datos; los tests de la tarea 6.1 pasan.

- [ ] **Tarea 6.3:** Escribir los tests del diálogo de recordatorio
  - **RF:** RF-1.2, RF-1.4, RF-1.5, RF-1.6
  - **Hecho cuando:** Los tests cubren activación, hora inválida sin guardar, cambio de hora,
    cancelación sin cambios y notificación del resultado; la suite muestra los fallos esperados.

- [ ] **Tarea 6.4:** Implementar `ReminderDialog`
  - **RF:** RF-1.2, RF-1.4, RF-1.5, RF-1.6
  - **Hecho cuando:** El diálogo modal valida la hora, guarda o cancela y solo notifica la
    configuración al confirmar; los tests de la tarea 6.3 pasan.

- [ ] **Tarea 6.5:** Escribir los tests de la conexión en `main`
  - **RF:** RF-1.2, RF-1.7, RF-3.4, RF-4.2, RF-4.4
  - **Hecho cuando:** Los tests montan `main`, guardan y recargan la configuración, sincronizan
    el planificador, eliminan el hábito y muestran errores de sistema; la suite muestra los
    fallos esperados.

- [ ] **Tarea 6.6:** Conectar la configuración y la sincronización en `main`
  - **RF:** RF-1.2, RF-1.7, RF-3.4, RF-4.2, RF-4.4
  - **Hecho cuando:** `main` abre el diálogo, guarda con `storage`, sincroniza al iniciar y tras
    cada cambio, elimina la tarea al borrar el último recordatorio y muestra avisos en español;
    los tests de la tarea 6.5 pasan.

## Fase 7: Documentación

- [ ] **Tarea 7.1:** Escribir los tests de la documentación de recordatorios
  - **RF:** RF-1, RF-2.3, RF-2.4, RF-2.5, RF-2.7, RFN-5
  - **Hecho cuando:** Los tests comprueban la configuración, el funcionamiento con la app
    cerrada, macOS y Windows, el límite de un aviso diario, los pendientes y los conteos de la
    suite; la suite muestra los fallos esperados.

- [ ] **Tarea 7.2:** Actualizar `README.md`
  - **RF:** RF-1, RF-2.3, RF-2.4, RF-2.5, RF-2.7, RFN-5
  - **Hecho cuando:** El README documenta activación, hora, desactivación, notificaciones con la
    app cerrada, plataformas, límites y los conteos actualizados; los tests de la tarea 7.1
    pasan.

## Fase 8: Alcance y verificación final

- [ ] **Tarea 8.1:** Escribir la guardia de alcance de la spec 005
  - **RF:** RF-2.1, RF-2.7, RF-3.4, RFN-5
  - **Hecho cuando:** Los tests permiten la tabla `reminders` y el runner, y rechazan posponer,
    agrupar, programar por días, enviar por red o modificar registros y estadísticas desde la
    notificación; la suite muestra los fallos esperados si hay infracciones.

- [ ] **Tarea 8.2:** Ajustar el código o las guardias según el resultado
  - **RF:** RF-2.1, RF-2.7, RF-3.4, RFN-5
  - **Hecho cuando:** La guardia de la tarea 8.1 pasa y las guardias de las specs anteriores
    siguen pasando.

- [ ] **Tarea 8.3:** Ejecutar la suite completa y la cobertura
  - **RF:** RFN-7, RFN-8
  - **Hecho cuando:** `.venv/bin/python -m pytest -q` pasa sin fallos y la cobertura de
    `reminders.py`, `storage.py`, `reminder_service.py` y `app_state.py` es ≥80 %.

- [ ] **Tarea 8.4:** Verificar los criterios de finalización
  - **RF:** Todos
  - **Hecho cuando:** Se comprueba la configuración persistente, el aviso único para pendientes,
    la ausencia de avisos duplicados o retroactivos, el funcionamiento con la app cerrada en
    macOS y Windows, el manejo de permisos y errores, y que registros, rachas, estadísticas y
    heatmap no cambian; `tasks.md` queda completamente marcado.
