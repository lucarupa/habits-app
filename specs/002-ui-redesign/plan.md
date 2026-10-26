# Plan de Implementación — 002 Rediseño de interfaz con estadísticas

## Estructura de módulos

```text
habits/
├── __init__.py
├── core.py          # Modelo, rachas y nuevas estadísticas puras
├── storage.py       # Persistencia SQLite, incluido el icono del hábito
└── app.py           # Interfaz Flet: barra lateral, detalle, modal y heatmap
tests/
├── test_core.py     # Tests de dominio y estadísticas
└── test_storage.py  # Tests de persistencia, iconos y migración
data/
└── habits.db        # Base de datos SQLite existente o generada en runtime
```

- **`habits/core.py`** — Cubre RF-2.6, RF-2.8, RF-3.2 a RF-3.6 y RF-4.1 a RF-4.7. Añade el
  icono al modelo y las funciones puras de estadísticas y heatmap. No importa Flet.
- **`habits/storage.py`** — Cubre RF-2.8, RF-2.9 y RFN-1. Añade la columna `icon`, la
  migración de bases existentes y el CRUD actualizado. No contiene lógica de presentación.
- **`habits/app.py`** — Cubre RF-1, RF-2.1 a RF-2.5, RF-2.7, RF-2.10, RF-3.1, RF-4, RF-5,
  RF-6 y RF-7. Orquesta la interfaz y delega cálculos y datos en `core.py` y `storage.py`.
- **`tests/test_core.py`** — Cubre las funciones puras nuevas y las existentes.
- **`tests/test_storage.py`** — Cubre la persistencia del icono y la migración.

> Nota: el nombre visible de la aplicación queda pendiente entre “Habits App” y “Study
> Tracker”. Mientras se aclare, el plan usa “Habits App” como valor por defecto; el cambio
> afecta solo a textos de la interfaz.

---

## Modelo de datos

### Tabla `habits` (modificada)

| Columna | Tipo | Restricción | Descripción |
|---------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Identificador único |
| `name` | TEXT | NOT NULL | Nombre del hábito (≤ 60 caracteres en la capa de dominio) |
| `start_date` | TEXT | NOT NULL | Fecha de inicio en formato YYYY-MM-DD |
| `icon` | TEXT | NOT NULL DEFAULT `'book'` | Clave semántica del icono elegido |

### Tabla `completions` (sin cambios)

| Columna | Tipo | Restricción | Descripción |
|---------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Identificador único |
| `habit_id` | INTEGER | NOT NULL, FOREIGN KEY → habits.id | Hábito asociado |
| `completed_date` | TEXT | NOT NULL, formato YYYY-MM-DD | Fecha del registro |
| | | UNIQUE(habit_id, completed_date) | Evita duplicados por día |

### Ejemplo de datos

```text
habits:
| id | name              | start_date  | icon   |
|----|-------------------|-------------|--------|
| 1  | Estudiar Python   | 2024-10-01  | code   |
| 2  | Leer 30 minutos   | 2024-10-20  | book   |

completions:
| id | habit_id | completed_date |
|----|----------|----------------|
| 1  | 1        | 2024-10-24     |
| 2  | 1        | 2024-10-25     |
| 3  | 2        | 2024-10-25     |
```

El hábito 1 tiene racha actual 2, mejor racha 2 y 2 días registrados. El hábito 2 tiene
racha actual 1, mejor racha 1 y 1 día registrado.

### Migración de datos existentes

`init_db` debe:

1. Crear la tabla `habits` con la columna `icon` si la base es nueva.
2. Consultar `PRAGMA table_info(habits)` si la tabla ya existe.
3. Si falta `icon`, ejecutar `ALTER TABLE habits ADD COLUMN icon TEXT NOT NULL DEFAULT 'book'`.
4. No modificar ni perder los registros existentes.

Esto cubre RF-2.8 y RF-2.9.

---

## Algoritmos clave (pseudocódigo)

### Racha actual (RF-3.2, reutiliza la regla de 001)

Se conserva `calculate_streak(completed_dates, today)`:

```text
funcion calcular_racha(completed_dates, today):
    si no hay fechas:
        retornar 0

    ordenar fechas descendente
    si la fecha más reciente != today:
        retornar 0

    racha = 1
    fecha_esperada = today - 1 día
    para cada fecha en fechas[1:]:
        si fecha == fecha_esperada:
            racha += 1
            fecha_esperada -= 1 día
        sino si fecha < fecha_esperada:
            romper
    retornar racha
```

### Mejor racha (RF-3.3)

```text
funcion calcular_mejor_racha(completed_dates):
    si no hay fechas:
        retornar 0

    ordenar fechas ascendente
    mejor = 1
    actual = 1
    para cada par (anterior, actual_fecha) consecutivo:
        si actual_fecha == anterior + 1 día:
            actual += 1
        sino:
            mejor = max(mejor, actual)
            actual = 1
    retornar max(mejor, actual)
```

### Días registrados (RF-3.4)

```text
funcion contar_dias_registrados(completed_dates):
    retornar cantidad de fechas distintas en completed_dates
```

### Estadísticas del hábito (RF-3.2 a RF-3.5)

```text
funcion obtener_estadisticas(completed_dates, today):
    retornar {
        racha_actual: calcular_racha(completed_dates, today),
        mejor_racha: calcular_mejor_racha(completed_dates),
        dias_registrados: contar_dias_registrados(completed_dates)
    }
```

### Heatmap de 5 semanas (RF-4.1 a RF-4.7)

```text
funcion construir_heatmap(completed_dates, today, weeks=5):
    lunes_semana_actual = today - weekday(today)
    lunes_inicial = lunes_semana_actual - (weeks - 1) * 7 días
    celdas = []

    para offset en 0..(weeks * 7 - 1):
        fecha = lunes_inicial + offset días
        celdas.agregar({
            fecha: fecha,
            completado: fecha en completed_dates,
            es_hoy: fecha == today,
            es_futuro: fecha > today,
            dia_semana: weekday(fecha),   # 0 = lunes
            semana: offset // 7           # 0..4
        })

    retornar celdas
```

La UI pinta cada celda en una cuadrícula de 7 filas (lunes a domingo) por 5 columnas
(semanas). Las celdas futuras se muestran como no disponibles. Esto permite que el heatmap
tenga siempre 35 posiciones y se parezca al mockup.

### Icono del hábito (RF-2.6, RF-2.8)

```text
constantes:
    ICONOS_VALIDOS = {book, code, science, language, music, art, math, fitness}
    ICONO_POR_DEFECTO = book

funcion crear_habito(name, start_date, icon):
    validar nombre
    si icon no está en ICONOS_VALIDOS:
        icon = ICONO_POR_DEFECTO
    si start_date es futura:
        start_date = today
    retornar Habit(..., icon=icon)
```

La UI traduce las claves semánticas (`book`, `code`, etc.) a iconos de Flet. La capa de
dominio no conoce Flet.

---

## Decisiones técnicas

### 1. Almacenar una clave semántica de icono, no el nombre del icono de Flet

**Decisión:** Guardar en `habits.icon` una clave como `book`, `code` o `science`, y mapearla a
un icono de Flet en `app.py`.

**Alternativa descartada:** Guardar directamente nombres de iconos de Flet, por ejemplo
`Icons.MENU_BOOK`.

**Justificación:** Mantiene la separación UI/lógica de la constitución (principio 3). Si en el
futuro cambia la librería gráfica, los datos siguen siendo válidos. Cubre RF-2.8.

### 2. Migración aditiva de SQLite

**Decisión:** Añadir la columna `icon` con `ALTER TABLE` cuando la base existente no la tenga,
usando `DEFAULT 'book'`.

**Alternativa descartada:** Recrear la tabla `habits` y copiar los datos.

**Justificación:** Es una migración simple, idempotente y sin pérdida de datos. Cubre RF-2.9 y
RFN-1.

### 3. Estadísticas puras en `core.py`

**Decisión:** Implementar `HabitStats`, `calculate_best_streak`,
`count_registered_days`, `get_habit_stats` y `build_activity_heatmap` en `core.py`, sin Flet.

**Alternativa descartada:** Calcular las estadísticas dentro de los widgets de la interfaz.

**Justificación:** Cumple la separación UI/lógica (RFN-3), permite tests unitarios (RFN-4) y
evita duplicar la lógica de rachas. Cubre RF-3 y RF-4.

### 4. Un solo layout con barra lateral y panel de detalle

**Decisión:** Sustituir la navegación por vistas completas por un layout de dos zonas: barra
lateral persistente y panel de detalle. La creación se resuelve con un diálogo modal.

**Alternativa descartada:** Mantener las vistas separadas actuales y solo cambiar los colores.

**Justificación:** Es la estructura de los mockups y permite cambiar de hábito sin recargar la
aplicación. Cubre RF-1 y RF-6.

### 5. Heatmap binario construido en el dominio

**Decisión:** `build_activity_heatmap` devuelve 35 celdas con fecha, estado, día de la semana,
semana, `es_hoy` y `es_futuro`. La UI solo pinta.

**Alternativa descartada:** Generar los widgets del heatmap dentro de `core.py` o calcular los
días en `app.py`.

**Justificación:** El cálculo queda testeado y la UI no contiene lógica. Cubre RF-4 y RFN-3.

### 6. Sin sesiones ni minutos

**Decisión:** Reutilizar la tabla `completions` existente. No se añaden columnas de minutos ni
una tabla de sesiones.

**Alternativa descartada:** Añadir una tabla `sessions` con fecha y minutos.

**Justificación:** El usuario excluyó minutos y sesiones del alcance. Cubre RF-5.5 y mantiene
el MVP simple.

### 7. Estado seleccionado en memoria

**Decisión:** Al abrir la aplicación se selecciona el primer hábito de la lista ordenada. La
selección no se persiste entre sesiones.

**Alternativa descartada:** Guardar el último hábito seleccionado en la base de datos.

**Justificación:** Es suficiente para el MVP y evita una preferencia adicional. La spec deja
esta decisión documentada.

---

## Estrategia de tests

### Tests de `habits/core.py` (`test_core.py`)

| Prueba | RF cubierto | Descripción |
|--------|-------------|-------------|
| `test_create_habit_default_icon` | RF-2.6 | Sin icono se asigna el icono por defecto. |
| `test_create_habit_selected_icon` | RF-2.8 | El icono elegido se conserva en el objeto. |
| `test_create_habit_invalid_icon` | RF-2.6 | Un icono no válido se sustituye por el defecto. |
| `test_calculate_best_streak_empty` | RF-3.3 | Sin registros, la mejor racha es 0. |
| `test_calculate_best_streak_single` | RF-3.3 | Un solo día registrado da mejor racha 1. |
| `test_calculate_best_streak_consecutive` | RF-3.3 | Varios días consecutivos se cuentan completos. |
| `test_calculate_best_streak_with_gaps` | RF-3.3 | Los huecos separan bloques y se toma el mayor. |
| `test_calculate_best_streak_includes_current` | RF-3.3 | La racha actual puede ser la mejor. |
| `test_count_registered_days_empty` | RF-3.4 | Sin registros, los días registrados son 0. |
| `test_count_registered_days_distinct` | RF-3.4 | Se cuentan fechas distintas, no repeticiones. |
| `test_get_habit_stats_empty` | RF-3.5 | Sin registros, las tres estadísticas son 0. |
| `test_get_habit_stats_active` | RF-3.2, RF-3.3, RF-3.4 | Hábito con racha activa devuelve valores correctos. |
| `test_get_habit_stats_inactive` | RF-3.2 | Si el último día no es hoy, la racha actual es 0. |
| `test_build_activity_heatmap_dimensions` | RF-4.1, RF-4.2 | Devuelve 35 celdas repartidas en 5 semanas y 7 días. |
| `test_build_activity_heatmap_marks_completed` | RF-4.3 | Las fechas completadas se marcan como completadas. |
| `test_build_activity_heatmap_today` | RF-4.4 | La celda de hoy se marca con `es_hoy`. |
| `test_build_activity_heatmap_future_days` | RF-4.3 | Los días posteriores a hoy se marcan como futuros. |
| `test_build_activity_heatmap_empty` | RF-4.6 | Sin registros, ninguna celda disponible está completada. |

### Tests de `habits/storage.py` (`test_storage.py`)

| Prueba | RF cubierto | Descripción |
|--------|-------------|-------------|
| `test_init_db_creates_icon_column` | RF-2.8 | Una base nueva incluye la columna `icon`. |
| `test_init_db_migrates_existing_habits` | RF-2.9 | Una base antigua recibe `icon` con valor por defecto. |
| `test_init_db_migration_preserves_data` | RF-2.9, RFN-1 | La migración conserva hábitos y registros. |
| `test_create_habit_persists_icon` | RF-2.8 | El icono se guarda y se lee de vuelta. |
| `test_create_habit_db_default_icon` | RF-2.6 | Sin icono se guarda el valor por defecto. |
| `test_get_habit_db_returns_icon` | RF-2.8 | `get_habit_db` devuelve el icono. |
| `test_list_all_habits_db_returns_icon` | RF-2.8 | El listado incluye el icono de cada hábito. |

### Verificación manual de la interfaz

`habits/app.py` no se testea con pytest porque es la capa de presentación. Se verifica
manualmente:

- Barra lateral con orden por racha y desempate alfabético.
- Selección visual y cambio de detalle.
- Estadísticas correctas para hábito activo, inactivo y vacío.
- Heatmap de 5 semanas, celda de hoy y días futuros.
- Creación modal con nombre, fecha e icono, incluyendo errores.
- Estado vacío y CTA.
- Registro de hoy, mensaje de duplicado y actualización inmediata.
- Conservación de datos y migración de hábitos sin icono.

### Cobertura objetivo

- ≥80 % en `habits/core.py`.
- ≥80 % en `habits/storage.py`.
- `habits/app.py` se valida manualmente, respetando la constitución.

### Ejecución

```bash
pytest -q
pytest --cov=habits --cov-report=term-missing
```
