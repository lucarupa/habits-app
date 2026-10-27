# Plan de Implementación — 005 Recordatorios locales por hábito

## Estructura de módulos

```
habits/
├── core.py              # Modelo de hábito y cálculos existentes
├── reminders.py         # Lógica pura: validación, etiquetas, vencimiento y textos
├── storage.py           # Persistencia SQLite: hábitos, registros y recordatorios
├── reminder_service.py  # Orquestación: recoge vencidos, reclama y notifica
├── notifications.py     # Adaptador de notificaciones y programación del sistema
├── reminder_runner.py   # Punto de entrada que ejecuta el planificador del sistema
├── app_state.py         # Estado de la app, incluido el recordatorio seleccionado
└── app.py               # Interfaz Flet: estado, diálogo y conexión con `main`
tests/
├── test_reminders.py             # Lógica pura de recordatorios
├── test_storage.py               # Persistencia y migración (ampliado)
├── test_app_state.py             # Estado con recordatorios (ampliado)
├── test_notifications.py         # Adaptador y programación con comandos simulados
├── test_reminder_service.py      # Servicio, idempotencia y errores
├── test_reminder_runner.py       # Entrada del planificador
├── test_reminder_widgets.py      # Estado y diálogo en Flet
├── test_reminder_flow.py         # Flujo integrado desde `main`
└── test_scope_guard_005.py       # Alcance y esquema permitido
```

- **`habits/reminders.py`** — Cubre RF-1.3, RF-1.6, RF-2.2, RF-2.4, RF-2.7, RF-2.9,
  RF-2.10, RF-3.6 y RF-4.5. Funciones puras sin Flet ni SQLite.
- **`habits/storage.py`** — Cubre RF-1.2 a RF-1.8, RF-2.3, RF-2.7, RF-3.4, RF-3.5 y RF-4.4.
  Encapsula el esquema y todas las consultas.
- **`habits/reminder_service.py`** — Cubre RF-2.1, RF-2.5 a RF-2.8, RF-3.2, RF-3.3 y RF-4.5.
  Orquesta la comprobación periódica y solo depende de funciones puras, almacenamiento y un
  notificador inyectable.
- **`habits/notifications.py`** — Cubre RF-2.3, RF-4.1 a RF-4.4 y RFN-5. Traduce la intención de
  notificar y programar a operaciones del sistema operativo.
- **`habits/reminder_runner.py`** — Cubre RF-2.1, RF-2.3 y RF-2.10. Ejecuta una comprobación
  cuando lo invoca el planificador del sistema.
- **`habits/app_state.py`** — Cubre RF-1.1, RF-1.7 y RF-3.5. Expone el estado del recordatorio
  del hábito seleccionado sin acceder a widgets.
- **`habits/app.py`** — Cubre RF-1.1 a RF-1.7, RF-3.1 a RF-3.7 y RF-4.2 a RF-4.4. Muestra el
  estado, abre el diálogo de configuración y sincroniza el planificador.

---

## Modelo de datos

### Tabla `reminders` (nueva)

| Columna | Tipo | Restricción | Descripción |
|---------|------|-------------|-------------|
| `habit_id` | INTEGER | PRIMARY KEY | Hábito asociado; un recordatorio como máximo por hábito |
| `enabled` | INTEGER | NOT NULL DEFAULT 0 | 0 = desactivado; 1 = activo |
| `reminder_time` | TEXT | NULL | Hora local en formato HH:MM |
| `effective_from` | TEXT | NOT NULL | Fecha local YYYY-MM-DD desde la que puede avisar |
| `last_notified_on` | TEXT | NULL | Fecha local del último aviso entregado |

La tabla se crea de forma idempotente en `init_db`. Los hábitos existentes no necesitan fila:
la ausencia de fila equivale a recordatorio desactivado (RF-1.3 y RF-1.8). `delete_habit_db`
elimina la fila de `reminders` dentro de la misma transacción que el hábito y sus registros
(RF-3.4).

### Ejemplo de datos

```
habits:
| id | name   | start_date | icon |
|----|--------|------------|------|
| 1  | Leer   | 2024-09-01 | book |
| 2  | Python | 2024-09-15 | code |

reminders:
| habit_id | enabled | reminder_time | effective_from | last_notified_on |
|----------|---------|---------------|----------------|------------------|
| 1        | 1       | 20:00         | 2024-10-01     | 2024-10-07       |
| 2        | 0       | 18:30         | 2024-10-01     | NULL             |
```

El hábito 1 recibió su aviso el 07/10 y no volverá a recibirlo ese día. El hábito 2 conserva
una hora configurada pero está desactivado, por lo que no genera avisos.

---

## Algoritmos clave (pseudocódigo)

### Validar y guardar la configuración (RF-1.2, RF-1.5, RF-1.6, RF-1.8)

```
funcion configure_reminder(habit_id, enabled, time_text, now):
    si no existe el hábito:
        lanzar error de dominio

    si no enabled:
        guardar enabled = 0 conservando la hora
        retornar configuración desactivada

    hora = validar_hora(time_text)          # HH:MM entre 00:00 y 23:59
    si hora es inválida:
        retornar error en español sin escribir

    effective_from = today(now)
    si hora <= hora_local(now):
        effective_from = today(now) + 1 día

    guardar o actualizar reminders(habit_id, 1, hora, effective_from)
    retornar configuración activa
```

**Casos cubiertos:**
- RF-1.2: una hora válida activa el recordatorio.
- RF-1.6: una hora vacía, incompleta o fuera de rango no cambia nada.
- RF-3.6: activar con la hora ya pasada retrasa el primer aviso al día siguiente.

### Determinar recordatorios vencidos (RF-2.1, RF-2.4, RF-2.5, RF-2.9, RF-2.10)

```
funcion due_reminders(now, today):
    candidatos = recordatorios activos con hora <= ahora
    resultado = vacío

    para cada candidato:
        si effective_from > today:
            continuar
        si last_notified_on == today:
            continuar
        si el hábito ya tiene registro en today:
            continuar
        si la fecha de inicio del hábito > today:
            continuar
        agregar candidato a resultado

    retornar resultado
```

La comparación de horas usa cadenas `HH:MM` con ceros a la izquierda. Un candidato cuya hora ya
pasó sigue vencido durante el mismo día local, lo que permite entregar el aviso tras un reinicio
o una reanudación del equipo (RF-2.10), pero nunca después de cambiar de día.

### Entregar y evitar duplicados (RF-2.6 a RF-2.8, RF-3.2, RF-4.5)

```
funcion deliver_due(now, db_path, notifier):
    para cada recordatorio en due_reminders(now, today):
        si claim_delivery(habit_id, today) falla:
            continuar                       # otro proceso ya lo reclamó

        resultado = notifier.send(reminder_message(habit.name))
        si resultado falla:
            release_delivery(habit_id)
            registrar error para aviso en la app
        sino:
            confirmar last_notified_on = today
```

La reclamación es un `UPDATE` condicional que solo afecta a la fila si
`last_notified_on` no es la fecha actual. Así dos ejecuciones simultáneas no duplican el aviso.
Si el envío falla, se libera la reclamación para reintentar en la siguiente comprobación. El
servicio devuelve un resumen de enviados y errores, sin mostrar interfaces.

### Sincronizar el planificador (RF-2.3, RF-3.4, RF-4.4)

```
funcion sync_scheduler(db_path):
    hay_activos = existen recordatorios habilitados
    runner = ruta del intérprete actual + módulo reminder_runner + db_path

    si hay_activos:
        instalar o actualizar tarea periódica cada minuto
    sino:
        eliminar tarea si existe

    si el sistema devuelve error:
        retornar error en español
```

Se usa una única tarea periódica por usuario y sistema operativo. Cada ejecución consulta la base
de datos y decide qué avisos corresponden. Esto evita reinstalar una tarea por hábito cuando se
cambia una hora y permite aplicar el mismo algoritmo en macOS y Windows.

---

## Decisiones técnicas

### 1. Una sola tarea periódica del sistema frente a una tarea por hábito

**Decisión:** Registrar una única tarea que ejecuta `habits.reminder_runner` cada minuto y deja
que el runner consulte la base de datos.

**Alternativa descartada:** Crear y destruir una tarea del sistema por cada recordatorio.

**Justificación:** Los cambios de hora, el borrado de hábitos y la recuperación tras suspensión
se resuelven en una sola consulta, sin riesgo de dejar tareas huérfanas. También reduce las
diferencias entre macOS y Windows y permite el límite de un aviso por hábito y día (RF-2.7,
RF-3.4 y RF-3.6).

### 2. Tabla `reminders` separada frente a columnas en `habits`

**Decisión:** Guardar la configuración en una tabla uno-a-uno `reminders`.

**Alternativa descartada:** Añadir `reminder_enabled`, `reminder_time` y columnas auxiliares a
`habits`.

**Justificación:** Mantiene la tabla de hábitos estable, permite que un hábito sin fila equivalga
a recordatorio desactivado y aísla las consultas del planificador. La eliminación se hace en la
misma transacción que el hábito (RF-1.8 y RF-3.4).

### 3. Idempotencia con `last_notified_on` frente a una tabla de entregas

**Decisión:** Guardar la fecha del último aviso en la propia fila del recordatorio y reclamarla
con un `UPDATE` condicional.

**Alternativa descartada:** Crear una tabla `reminder_deliveries` con una fila por aviso.

**Justificación:** Solo se necesita evitar más de un aviso por hábito y día; no hay historial de
notificaciones en el alcance. Una sola fila y una actualización atómica cubren RF-2.7 y RFN-7 con
menos datos y menos consultas.

### 4. Adaptador de sistema operativo inyectable

**Decisión:** Aislar las llamadas a macOS y Windows en `notifications.py`, con una interfaz de
notificador y planificador que recibe un ejecutor de comandos inyectable.

**Alternativa descartada:** Llamar directamente a comandos del sistema desde el servicio o desde
la interfaz.

**Justificación:** Permite probar toda la lógica sin enviar notificaciones reales y respeta la
separación UI/lógica de la constitución. Las pruebas del adaptador verifican los comandos
construidos, no el entorno del desarrollador.

### 5. Configuración en el detalle del hábito

**Decisión:** Mostrar el estado del recordatorio y un botón “Recordatorio” en el encabezado del
detalle. El botón abre un diálogo modal con activación, hora y acciones “Cancelar” y “Guardar”.

**Alternativa descartada:** Incluir la hora en el formulario de creación y edición del hábito.

**Justificación:** El recordatorio es una preferencia independiente del nombre, la fecha y el
icono; separarlo evita mezclar validaciones y permite cambiar la hora sin abrir el formulario de
edición (RF-1.1 a RF-1.5).

### 6. Comprobación de permisos mediante el adaptador

**Decisión:** Al activar un recordatorio, el adaptador comprueba la disponibilidad del sistema y
realiza una notificación de prueba. Solo si la operación termina correctamente se confirma la
activación; cualquier error se traduce a un mensaje en español y deja la configuración anterior.

**Alternativa descartada:** Activar el recordatorio siempre y limitarse a fallar en silencio
cuando el sistema bloquee las notificaciones.

**Justificación:** Evita que el usuario crea que tiene un recordatorio activo cuando el sistema
lo está bloqueando (RF-4.1 a RF-4.3). La prueba se realiza una sola vez al activar y el
adaptador puede simularse en tests.

### 7. Sincronización al iniciar y al cambiar la configuración

**Decisión:** Sincronizar la tarea del sistema al arrancar la aplicación y después de cada alta,
cambio o baja de recordatorio. Si no quedan recordatorios activos, se elimina la tarea.

**Alternativa descartada:** Instalar la tarea solo la primera vez y no volver a comprobarla.

**Justificación:** Mantiene la tarea actualizada si cambia la ruta del proyecto o del intérprete,
si el usuario desactiva todos los recordatorios o si una instalación anterior quedó incompleta
(RF-3.4 y RF-4.4).

---

## Estrategia de tests

### Tests de lógica pura (`test_reminders.py`)

| Prueba | RF cubierto | Descripción |
|--------|-------------|-------------|
| `test_validate_reminder_time_accepts_valid_hours` | RF-1.2 | Acepta 00:00, 09:05 y 23:59. |
| `test_validate_reminder_time_rejects_invalid_values` | RF-1.6 | Rechaza vacío, 24:00, 9:5 y texto. |
| `test_reminder_label_reflects_state_and_time` | RF-1.1 | “Sin recordatorio” o “Recordatorio a las HH:MM”. |
| `test_effective_date_is_today_before_time` | RF-3.1 | Una hora futura empieza hoy. |
| `test_effective_date_is_tomorrow_after_time` | RF-3.6 | Una hora pasada empieza mañana. |
| `test_reminder_message_includes_habit_name` | RF-2.2 | Texto exacto en español con el nombre. |
| `test_is_due_respects_enabled_time_and_date` | RF-2.1, RF-2.5, RF-2.9 | Solo vence si está activo, llegó la hora y empezó la vigencia. |
| `test_is_due_skips_completed_and_notified_today` | RF-2.4, RF-2.7 | No vence si ya hay registro o aviso hoy. |

### Tests de persistencia (`test_storage.py`)

| Prueba | RF cubierto | Descripción |
|--------|-------------|-------------|
| `test_init_db_creates_reminders_table` | RF-1.8 | La tabla existe y las bases antiguas siguen funcionando. |
| `test_save_and_get_reminder_db` | RF-1.2, RF-1.4, RF-1.7 | Guarda, actualiza y recupera la configuración. |
| `test_reminder_without_row_is_disabled` | RF-1.3, RF-1.8 | Un hábito sin fila se considera desactivado. |
| `test_list_due_reminders_db_filters_state` | RF-2.1, RF-2.4, RF-2.5, RF-2.9 | Solo devuelve activos, vencidos, vigentes y pendientes. |
| `test_claim_and_release_reminder_delivery` | RF-2.7, RFN-7 | La reclamación es atómica y libera tras un fallo. |
| `test_delete_habit_db_removes_reminder` | RF-3.4 | No quedan recordatorios huérfanos. |

### Tests del servicio y del runner (`test_reminder_service.py`, `test_reminder_runner.py`)

| Prueba | RF cubierto | Descripción |
|--------|-------------|-------------|
| `test_service_notifies_only_pending_habits` | RF-2.1, RF-2.4 | Envía a pendientes y omite completados. |
| `test_service_sends_one_notification_per_habit_and_day` | RF-2.7, RFN-7 | Dos ejecuciones seguidas no duplican avisos. |
| `test_service_uses_current_habit_name` | RF-3.5 | Un renombrado se refleja en el texto. |
| `test_service_releases_claim_when_delivery_fails` | RF-4.5 | Un fallo permite reintentar sin marcar como avisado. |
| `test_service_ignores_future_effective_date` | RF-3.6 | No avisa antes de la fecha efectiva. |
| `test_runner_uses_database_and_current_time` | RF-2.1, RF-2.3 | El runner compone el servicio y devuelve un resumen. |

### Tests del adaptador (`test_notifications.py`)

| Prueba | RF cubierto | Descripción |
|--------|-------------|-------------|
| `test_notifier_builds_macos_command` | RF-2.3, RFN-5 | Construye el comando de notificación de macOS. |
| `test_notifier_builds_windows_command` | RF-2.3, RFN-5 | Construye el comando de notificación de Windows. |
| `test_notifier_reports_permission_or_command_error` | RF-4.2, RF-4.3 | Traduce errores a un resultado fallido en español. |
| `test_scheduler_installs_single_minute_task` | RF-2.3 | Instala una única tarea periódica. |
| `test_scheduler_removes_task_when_no_reminders` | RF-3.4 | Elimina la tarea al desactivar todo. |
| `test_scheduler_reports_installation_error` | RF-4.4 | Un fallo no rompe la app y devuelve error. |

### Tests de widgets y flujo (`test_reminder_widgets.py`, `test_reminder_flow.py`)

| Prueba | RF cubierto | Descripción |
|--------|-------------|-------------|
| `test_header_shows_reminder_state_and_action` | RF-1.1 | El detalle muestra el estado y el botón. |
| `test_reminder_dialog_validates_time` | RF-1.6 | Una hora inválida no guarda ni cierra. |
| `test_reminder_dialog_saves_and_cancels` | RF-1.2, RF-1.4, RF-1.5 | Guardar persiste; cancelar no cambia nada. |
| `test_saving_reminder_syncs_scheduler` | RF-2.3, RF-4.4 | `main` sincroniza y muestra errores. |
| `test_reminder_flow_persists_after_reload` | RF-1.7 | La configuración sobrevive a reiniciar. |
| `test_reminder_flow_does_not_change_stats` | RF-2.8 | Registros, racha y heatmap no cambian. |

### Tests de documentación y alcance (`test_readme_reminders.py`, `test_scope_guard_005.py`)

| Prueba | RF cubierto | Descripción |
|--------|-------------|-------------|
| `test_readme_documents_reminder_configuration` | RF-1 | Documenta activación, hora y desactivación. |
| `test_readme_documents_closed_app_and_platforms` | RF-2.3, RFN-5 | Explica macOS/Windows y el funcionamiento con la app cerrada. |
| `test_readme_documents_reminder_limits` | RF-2.4, RF-2.5, RF-2.7 | Un aviso diario, solo pendientes y sin duplicados. |
| `test_scope_guard_allows_reminders_table_and_runner` | RF-2.1 | El esquema y el runner están permitidos. |
| `test_scope_guard_rejects_snooze_groups_and_network_delivery` | Fuera de alcance | No hay posponer, agrupar, correo ni red. |

### Cobertura objetivo

- ≥80 % en `habits/reminders.py`.
- ≥80 % en `habits/storage.py`.
- ≥80 % en `habits/reminder_service.py`.
- ≥80 % en `habits/app_state.py`.
- `habits/app.py` y `habits/notifications.py` se validan con widgets, flujos y adaptadores
  simulados.

### Ejecución

```bash
pytest -q
.venv/bin/python -m pytest -q
.venv/bin/python -m pytest --cov=habits --cov-report=term-missing -q
```

---

## Riesgos y mitigaciones

| Riesgo | Mitigación |
|--------|------------|
| El sistema operativo bloquea las notificaciones | Activación con prueba previa, mensajes en español y estado visible. |
| La tarea del sistema apunta a una ruta antigua del proyecto | Re-sincronizar al iniciar y al cambiar la configuración. |
| Dos ejecuciones del runner coinciden | Reclamación atómica con `last_notified_on` y transacción corta. |
| El equipo se suspende a la hora del aviso | El runner entrega el aviso vencido en la primera comprobación del mismo día local. |
| Cambios de hora o zona horaria | Usar siempre la hora y la fecha locales actuales; no se envían avisos de días anteriores. |
| La base de datos está bloqueada por la app abierta | Transacciones breves, timeout de SQLite y reintento en la siguiente ejecución. |
