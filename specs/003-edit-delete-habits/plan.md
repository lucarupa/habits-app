# Plan de Implementación — 003 Edición y eliminación de hábitos

## Estructura de módulos

```
habits/
├── core.py          # Función pura de actualización y validaciones de dominio
├── storage.py       # Actualización y borrado transaccional en SQLite
├── habit_form.py    # Validación y persistencia de la edición
├── app_state.py     # Reutilizado sin cambios para recargar y seleccionar
├── theme.py         # Reutilizado sin cambios
└── app.py           # Acciones del detalle, modal de edición y confirmación
tests/
├── test_core.py
├── test_storage.py
├── test_habit_form.py
├── test_habit_dialog.py
├── test_detail_widgets.py
├── test_edit_delete_flow.py   # Nuevo: flujo integrado de edición y borrado
└── test_readme.py
data/
└── habits.db        # Sin cambios de esquema
```

- **`habits/core.py`** — Cubre RF-2.3, RF-2.4, RF-2.7 y RF-2.12. Añade una función pura que
  valida y devuelve un hábito actualizado conservando su identificador.
- **`habits/storage.py`** — Cubre RF-2.14, RF-3.4, RF-3.8 y RFN-1. Añade la actualización de
  una fila y el borrado transaccional del hábito con sus registros.
- **`habits/habit_form.py`** — Cubre RF-2 y RF-5. Valida nombre, fecha e icono para la edición
  y delega la persistencia en `core.py` y `storage.py`. No importa Flet.
- **`habits/app_state.py`** — Cubre RF-3.6, RF-3.7 y RF-4.5. Se reutiliza `load_app_state`, que
  ya ordena por racha y selecciona el primer hábito, o deja la selección vacía.
- **`habits/app.py`** — Cubre RF-1, RF-2.1, RF-2.2, RF-2.9, RF-2.10, RF-3.1 a RF-3.3, RF-4 y
  RF-5. Añade las acciones del detalle, el modo edición del modal, el calendario y el diálogo
  de confirmación.
- **`habits/theme.py`** — Sin cambios; se reutilizan colores, radios y espaciados.

Todos los módulos tocados reciben el comentario `# spec: 003-edit-delete-habits`, según el
principio 2 de la constitución.

---

## Modelo de datos

### Tabla `habits` (sin cambios)

| Columna | Tipo | Restricción | Descripción |
|---------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Identificador único |
| `name` | TEXT | NOT NULL | Nombre del hábito |
| `start_date` | TEXT | NOT NULL | Fecha de inicio en YYYY-MM-DD |
| `icon` | TEXT | NOT NULL DEFAULT 'book' | Clave semántica del icono |

### Tabla `completions` (sin cambios)

| Columna | Tipo | Restricción | Descripción |
|---------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Identificador del registro |
| `habit_id` | INTEGER | NOT NULL, FK a `habits.id` | Hábito asociado |
| `completed_date` | TEXT | NOT NULL | Fecha completada en YYYY-MM-DD |
| `UNIQUE(habit_id, completed_date)` | — | Restricción compuesta | Evita duplicados |

**No hay migración de esquema.** La edición actualiza columnas existentes y la eliminación
borra filas existentes. No se añaden tablas ni columnas.

### Ejemplo de datos

```
habits:
| id | name    | start_date | icon |
|----|---------|------------|------|
| 1  | Python  | 2026-09-01 | code |
| 2  | Lectura | 2026-10-01 | book |

completions:
| id | habit_id | completed_date |
|----|----------|----------------|
| 1  | 1        | 2026-10-24     |
| 2  | 1        | 2026-10-25     |
| 3  | 2        | 2026-10-25     |
```

Editar el hábito 1 cambia `name`, `start_date` e `icon`, pero mantiene las filas 1 y 2 de
`completions` (RF-2.12). Eliminar el hábito 1 borra también sus filas 1 y 2 (RF-3.4).

---

## Algoritmos clave (pseudocódigo)

### Actualizar un hábito en el dominio (RF-2)

```
funcion update_habit(habit, name, start_date, icon, today):
    nombre = recortar(name)

    si nombre está vacío:
        error "El nombre del hábito es obligatorio."

    si longitud(nombre) > 60:
        error "El nombre del hábito no puede superar 60 caracteres."

    si start_date es None:
        start_date = habit.start_date

    si start_date > today:
        error "La fecha de inicio no puede ser futura."

    si icon no pertenece al catálogo:
        icon = habit.icon

    retornar Habit(
        id = habit.id,
        name = nombre,
        start_date = start_date,
        icon = icon
    )
```

**Casos cubiertos:**
- RF-2.3: nombre vacío o solo espacios.
- RF-2.4: nombre de más de 60 caracteres.
- RF-2.7: fecha futura rechazada como defensa del dominio.
- RF-2.8: icono no válido conserva el actual.
- RF-2.12: el identificador y los registros asociados no cambian.

### Validar y persistir una edición (RF-2, RF-5)

```
funcion update_habit_from_form(habit, data, db_path, today):
    validar nombre con las mismas reglas de creación

    si data.start_date está vacío:
        fecha = habit.start_date
    sino:
        fecha = parsear dd/mm/aaaa de forma estricta

    si fecha > today:
        error "La fecha de inicio no puede ser futura."

    icono = data.icon si es válido, si no habit.icon
    actualizado = update_habit(habit, data.name, fecha, icono, today)

    update_habit_db(
        habit_id = actualizado.id,
        name = actualizado.name,
        start_date = actualizado.start_date,
        icon = actualizado.icon,
        db_path = db_path
    )

    retornar UpdateHabitResult(
        habit_id = actualizado.id,
        name = actualizado.name,
        start_date = actualizado.start_date,
        icon = actualizado.icon
    )
```

**Casos cubiertos:**
- RF-2.1 y RF-2.2: datos precargados y fecha mostrada en dd/mm/aaaa.
- RF-2.5: fecha vacía conserva la fecha actual del hábito.
- RF-2.7: fecha futura rechazada aunque el calendario ya la bloquee.
- RF-2.9 y RF-2.14: persistencia y cierre correcto.
- RF-2.13: si la persistencia falla, no se devuelve un resultado exitoso.

### Eliminar un hábito y sus registros (RF-3)

```
funcion delete_habit_db(habit_id, db_path):
    abrir conexión
    iniciar transacción

    borrar de completions donde habit_id = habit_id
    resultado = borrar de habits donde id = habit_id

    si resultado no afectó ninguna fila:
        revertir transacción
        error "El hábito no existe."

    confirmar transacción
    cerrar conexión
```

**Casos cubiertos:**
- RF-3.4: se borran el hábito y todos sus registros.
- RF-3.8: cualquier error revierte la transacción completa; no quedan registros huérfanos.
- RF-3.9: tras confirmar, no queda nada accesible del hábito.

### Elegir la fecha con el calendario (RF-5)

```
al abrir el diálogo de creación:
    fecha_seleccionada = today
    campo_fecha.valor = formatear(fecha_seleccionada)

al abrir el diálogo de edición:
    fecha_seleccionada = hábito.start_date
    campo_fecha.valor = formatear(fecha_seleccionada)

al pulsar el campo de fecha:
    calendario.valor = fecha_seleccionada
    calendario.fecha_actual = today
    calendario.última_fecha = today
    calendario.modo_entrada = solo_calendario
    calendario.idioma = español
    mostrar calendario

al confirmar una fecha:
    fecha_seleccionada = fecha elegida
    campo_fecha.valor = formatear(fecha_seleccionada)
    mantener abierto el diálogo de crear o editar

al cancelar o cerrar el calendario:
    no modificar fecha_seleccionada ni campo_fecha
```

**Casos cubiertos:**
- RF-5.1 y RF-5.2: fecha inicial precargada en cada modo.
- RF-5.3 y RF-5.4: apertura y confirmación del calendario.
- RF-5.5: cancelar conserva el valor anterior.
- RF-5.6: días posteriores a hoy deshabilitados.
- RF-5.7: textos en español y semana de lunes a domingo.
- RF-5.8: campo de fecha de solo lectura.
- RF-5.9 y RF-5.10: fecha por defecto en creación y conservación en edición.

### Selección después de eliminar (RF-3.6, RF-3.7, RF-4.5)

```
funcion on_habit_deleted(habit_id):
    delete_habit_db(habit_id)

    nuevo_estado = load_app_state(db_path)
    # load_app_state ordena por racha y nombre,
    # y selecciona el primer hábito si existe.

    si nuevo_estado.is_empty:
        mostrar estado vacío
    sino:
        mostrar el detalle del primer hábito ordenado
```

**Casos cubiertos:**
- RF-3.6: se selecciona el primero de la lista ordenada.
- RF-3.7: si no queda ninguno, se muestra el estado vacío.
- RF-4.5: barra lateral y detalle quedan coherentes.

---

## Decisiones técnicas

### 1. Un solo modal para crear y editar

**Decisión:** Reutilizar `HabitFormDialog` con dos modos, creación y edición, y dos métodos de
apertura que precargan los campos correspondientes.

**Alternativa descartada:** Crear un diálogo independiente para la edición.

**Justificación:** Los campos y las validaciones son casi idénticos (RF-2.1 a RF-2.10). Un solo
control evita duplicar la lógica de validación y mantiene los tests existentes de creación con
cambios mínimos. También conserva un único punto donde se integra el calendario (RF-5).

### 2. Calendario desplegable de Flet

**Decisión:** Usar el control de calendario de Flet en modo solo calendario, con idioma español,
`última_fecha` igual a hoy y el campo de fecha en solo lectura.

**Alternativa descartada:** Invocar el calendario nativo de Windows.

**Justificación:** La constitución limita la interfaz a Flet y a la biblioteca estándar; el
calendario nativo requeriría otra dependencia o una segunda librería GUI. El usuario aprobó
explícitamente el calendario de Flet. La configuración elegida cumple RF-5.6 a RF-5.8 sin
dependencias nuevas (RFN-4).

### 3. Borrado transaccional explícito

**Decisión:** En una única transacción, borrar primero los registros de `completions` y después
la fila de `habits`, comprobando que la fila del hábito existía.

**Alternativa descartada:** Confiar en `ON DELETE CASCADE` con claves foráneas activadas.

**Justificación:** Las bases de datos existentes se crearon sin `ON DELETE CASCADE` y SQLite no
activa las claves foráneas por defecto. Añadir la cascada exigiría migrar el esquema y recrear
tablas. El borrado explícito cumple RF-3.4 y RF-3.8 sin migración y es fácil de probar.

### 4. Reutilizar `load_app_state` para la selección posterior

**Decisión:** Tras eliminar, recargar el estado completo; `load_app_state` ya ordena por racha y
nombre y selecciona el primer hábito, o deja `selected_id` vacío.

**Alternativa descartada:** Calcular en la interfaz cuál es el siguiente hábito y pasarlo como
selección explícita.

**Justificación:** Evita duplicar la regla de orden (RF-3.6) en la capa de interfaz, respeta la
separación UI/lógica (RFN-2) y garantiza que el estado vacío aparezca solo cuando no quedan
hábitos (RF-3.7).

### 5. Fecha estricta al editar, normalización al crear

**Decisión:** En la edición, una fecha futura o inválida se rechaza con un error. En la creación
se conserva el comportamiento existente de normalizar una fecha futura a hoy como defensa.

**Alternativa descartada:** Aplicar la misma normalización a la edición.

**Justificación:** El calendario ya impide elegir fechas futuras (RF-5.6), por lo que un valor
futuro en edición solo puede llegar por un estado corrupto o una llamada directa; rechazarlo
evita guardar datos incoherentes. En creación se mantiene la compatibilidad con las pruebas y
el comportamiento de la spec 002.

### 6. Mantener el formulario con fecha en texto dd/mm/aaaa

**Decisión:** `HabitFormData.start_date` sigue siendo una cadena en dd/mm/aaaa. El modal
formatea la fecha elegida en el calendario y la envía con el formato existente.

**Alternativa descartada:** Cambiar el contrato del formulario a un objeto `date`.

**Justificación:** Reduce el impacto en los tests y en el código existente, y mantiene una única
forma de validar y mostrar fechas (RFN-8). La fecha del calendario siempre es válida, así que
el formato no se convierte en una fuente de errores para el usuario.

---

## Estrategia de tests

Cada fase empieza escribiendo las pruebas que deben fallar y después la implementación. Los
tests puros no requieren Flet; los de interfaz se ejecutan con `.venv`.

### Tests de `habits/core.py` (`test_core.py`)

| Prueba | RF cubierto | Descripción |
|--------|-------------|-------------|
| `test_update_habit_changes_fields_and_keeps_id` | RF-2.9, RF-2.12 | Devuelve un hábito con nombre, fecha e icono nuevos y el mismo ID. |
| `test_update_habit_strips_name` | RF-2.3 | Elimina espacios sobrantes del nombre. |
| `test_update_habit_rejects_empty_name` | RF-2.3 | Lanza error con nombre vacío o solo espacios. |
| `test_update_habit_rejects_long_name` | RF-2.4 | Lanza error con más de 60 caracteres. |
| `test_update_habit_rejects_future_date` | RF-2.7 | Lanza error si la fecha es posterior a hoy. |
| `test_update_habit_keeps_current_icon_when_invalid` | RF-2.8 | Usa el icono actual si la clave no pertenece al catálogo. |

### Tests de `habits/storage.py` (`test_storage.py`)

| Prueba | RF cubierto | Descripción |
|--------|-------------|-------------|
| `test_update_habit_db_updates_existing_row` | RF-2.14 | Cambia nombre, fecha e icono y se lee de nuevo. |
| `test_update_habit_db_raises_for_unknown_id` | RF-2.13 | Lanza error si el hábito no existe. |
| `test_delete_habit_db_removes_habit_and_completions` | RF-3.4 | Borra el hábito y todas sus fechas asociadas. |
| `test_delete_habit_db_keeps_other_habits` | RF-3.4 | No afecta a otros hábitos ni a sus registros. |
| `test_delete_habit_db_raises_for_unknown_id` | RF-3.8 | Lanza error y no deja cambios parciales. |

### Tests de `habits/habit_form.py` (`test_habit_form.py`)

| Prueba | RF cubierto | Descripción |
|--------|-------------|-------------|
| `test_validate_update_keeps_current_date_when_empty` | RF-2.5 | Fecha vacía conserva la fecha actual del hábito. |
| `test_validate_update_rejects_future_date` | RF-2.7 | Fecha futura lanza error. |
| `test_validate_update_keeps_current_icon_when_missing` | RF-2.8 | Sin icono conserva el actual. |
| `test_validate_update_rejects_empty_name` | RF-2.3 | Nombre vacío lanza error. |
| `test_update_habit_from_form_persists_changes` | RF-2.9, RF-2.14 | Guarda los cambios y devuelve el resultado. |
| `test_update_habit_from_form_does_not_touch_completions` | RF-2.12 | Los registros existentes permanecen intactos. |

### Tests de interfaz (`test_habit_dialog.py`)

| Prueba | RF cubierto | Descripción |
|--------|-------------|-------------|
| `test_open_create_prefills_today_and_read_only_date` | RF-5.1, RF-5.8 | El campo muestra hoy y no es editable. |
| `test_open_edit_prefills_current_habit_values` | RF-2.2, RF-5.2 | Nombre, icono y fecha actual precargados. |
| `test_clicking_date_opens_calendar_with_future_blocked` | RF-5.3, RF-5.6 | Se abre el calendario con `last_date` igual a hoy. |
| `test_selecting_date_updates_field_and_keeps_dialog_open` | RF-5.4 | Confirmar una fecha actualiza el campo y no cierra el modal. |
| `test_canceling_calendar_keeps_previous_date` | RF-5.5 | Cancelar no cambia el campo. |
| `test_edit_submit_persists_and_notifies` | RF-2.9 | Guardar una edición cierra el modal y notifica el resultado. |
| `test_edit_cancel_does_not_change_the_habit` | RF-2.10 | Cancelar deja intactos los datos. |
| `test_edit_validation_error_keeps_dialog_open` | RF-2.3, RF-2.4 | Los errores mantienen el modal abierto. |
| `test_calendar_uses_spanish_locale_and_week_start` | RF-5.7 | El calendario usa locale español. |

### Tests de acciones y flujo (`test_detail_widgets.py`, `test_edit_delete_flow.py`)

| Prueba | RF cubierto | Descripción |
|--------|-------------|-------------|
| `test_detail_header_shows_edit_and_delete_actions` | RF-1.1 | Con hábito seleccionado aparecen ambas acciones. |
| `test_empty_detail_hides_edit_and_delete_actions` | RF-1.2 | Sin hábitos no aparecen las acciones. |
| `test_edit_action_opens_prefilled_dialog` | RF-1.3 | Pulsar “Editar” abre el modal con los datos actuales. |
| `test_delete_action_opens_confirmation_with_name` | RF-1.4, RF-3.1 | El diálogo muestra el nombre y advierte del borrado. |
| `test_delete_cancel_keeps_habit_and_selection` | RF-3.3 | Cancelar no borra nada. |
| `test_delete_confirm_removes_habit_and_records` | RF-3.4 | Confirmar elimina el hábito y sus registros. |
| `test_delete_selects_next_habit_in_order` | RF-3.6 | Se selecciona el primero de la lista restante. |
| `test_delete_last_habit_shows_empty_state` | RF-3.7 | Al borrar el último aparece el estado vacío. |
| `test_edit_refreshes_sidebar_detail_and_keeps_selection` | RF-4.1 a RF-4.4 | La vista refleja los cambios sin perder la selección. |
| `test_delete_database_error_keeps_habit` | RF-3.8 | Un fallo muestra error y conserva el hábito. |

### Cobertura objetivo

- ≥80 % en `habits/core.py` (funciones puras y métodos de dominio).
- ≥80 % en `habits/storage.py` (capa de persistencia).
- ≥80 % en `habits/habit_form.py` (validación y flujo de edición).
- `habits/app.py` se valida con tests de widgets y verificación visual/manual.

### Ejecución

```bash
pytest -q
.venv\Scripts\python.exe -m pytest -q
pytest --cov=habits --cov-report=term-missing -q
```
