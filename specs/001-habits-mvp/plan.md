# Plan de Implementación — 001 Habits MVP

## Estructura de módulos

```
habits/
├── __init__.py
├── core.py          # Lógica de dominio: modelos y cálculo de racha
├── storage.py       # Persistencia SQLite: CRUD de hábitos y registros diarios
└── app.py           # Interfaz Flet: vistas y navegación, sin lógica de negocio
tests/
├── test_core.py     # Tests de lógica de dominio
└── test_storage.py  # Tests de capa de persistencia
data/
└── habits.db        # Base de datos SQLite (generada en tiempo de ejecución)
```

- **`habits/core.py`** — Cubre RF-1, RF-2, RF-3, RF-4. Contiene las clases de dominio y las funciones puras de cálculo.
- **`habits/storage.py`** — Cubre RF-1, RF-2, RF-3. Encapsula todo el acceso a SQLite.
- **`habits/app.py`** — Cubre RF-1, RF-2, RF-3. Orquesta la interfaz Flet delegando a `core` y `storage`.

---

## Modelo de datos

### Tabla `habits`

| Columna | Tipo | Restricción | Descripción |
|---------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Identificador único |
| `name` | TEXT | NOT NULL, length ≤ 60 | Nombre del hábito |
| `start_date` | TEXT | NOT NULL, formato YYYY-MM-DD | Fecha de inicio |

### Tabla `completions`

| Columna | Tipo | Restricción | Descripción |
|---------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Identificador único |
| `habit_id` | INTEGER | NOT NULL, FOREIGN KEY → habits.id | Hábito asociado |
| `completed_date` | TEXT | NOT NULL, formato YYYY-MM-DD | Fecha del registro |
| | | UNIQUE(habit_id, completed_date) | Evita duplicados por día |

### Ejemplo de datos

```
habits:
| id | name              | start_date  |
|----|-------------------|-------------|
| 1  | Estudiar Python   | 2024-01-15  |
| 2  | Leer 30 minutos   | 2024-01-20  |

completions:
| id | habit_id | completed_date |
|----|----------|----------------|
| 1  | 1        | 2024-01-15     |
| 2  | 1        | 2024-01-16     |
| 3  | 1        | 2024-01-17     |
| 4  | 2        | 2024-01-20     |
```

En este ejemplo, el hábito "Estudiar Python" tiene racha 3 (días consecutivos 15-16-17), y "Leer 30 minutos" tiene racha 1 (solo el 20).

---

## Algoritmo de cálculo de racha (RF-4)

```
funcion calcular_racha(habit_id, fecha_actual):
    # Obtener todas las fechas completadas para este hábito, ordenadas descendente
    fechas = storage.obtener_fechas_completadas(habit_id, orden="DESC")

    si fechas esta vacia:
        retornar 0

    ultima_fecha = fechas[0]

    # RF-4.2: Si el último día no es hoy, la racha activa es cero
    si ultima_fecha != fecha_actual:
        retornar 0

    racha = 1
    fecha_esperada = ultima_fecha.restar_dias(1)

    para cada fecha en fechas[1:]:  # continuar en orden descendente
        si fecha == fecha_esperada:
            racha = racha + 1
            fecha_esperada = fecha.restar_dias(1)
        sino si fecha < fecha_esperada:
            # RF-4.4: Se encontró un hueco, detener conteo
            romper_ciclo

    retornar racha
```

**Casos cubiertos:**
- RF-4.1: Último día es hoy → cuenta hacia atrás mientras sea consecutivo.
- RF-4.2: Último día no es hoy → retorna 0 inmediatamente.
- RF-4.3: Un solo día registrado y es hoy → retorna 1 (el bucle no se ejecuta).
- RF-4.4: Hueco entre registros → el `romper_ciclo` detiene el conteo.

---

## Decisiones técnicas

### 1. SQLite sobre JSON para persistencia

**Decisión:** Usar SQLite (`habits/storage.py`) con dos tablas relacionales.

**Alternativa descartada:** Archivo JSON plano (`data/habits.json`).

**Justificación:** SQLite es parte del estándar de Python, soporta integridad referencial y la restricción `UNIQUE(habit_id, completed_date)` evita duplicados a nivel de base de datos, simplificando la validación de RF-2.2. JSON requeriría validación manual de duplicados en cada operación.

### 2. Clase de dominio `Habit` con métodos puros

**Decisión:** Modelar el hábito como una clase con atributos inmutables (`name`, `start_date`) y delegar el cálculo de racha a una función pura `calculate_streak(completions, today)`.

**Alternativa descartada:** Funciones sueltas que operan sobre diccionarios.

**Justificación:** Las clases permiten type hints claros, facilitan los tests unitarios y respetan el principio de separación UI/lógica (constitución principio 3). Los diccionarios perderían esa claridad tipada.

### 3. Vistas separadas en Flet

**Decisión:** Dos vistas Flet con navegación: una para crear hábitos y otra para listar con botones de marcar.

**Alternativa descartada:** Vista única con todo visible.

**Justificación:** La spec indica vistas separadas (pregunta 6 del proceso de clarificación). Aunque es más código, organiza mejor las tres funciones del MVP y prepara la app para futuras extensiones.

### 4. Fecha de inicio con validación de futuro

**Decisión:** En `core.py`, validar que `start_date` no sea posterior a la fecha actual; si lo es, usar la fecha actual.

**Alternativa descartada:** Rechazar la creación del hábito con error.

**Justificación:** El caso límite de la spec indica "el sistema rechaza la fecha y usa la fecha actual". Es más amigable que rechazar toda la operación.

---

## Estrategia de tests

### Tests de `habits/core.py` (test_core.py)

| Prueba | RF cubierto | Descripción |
|--------|-------------|-------------|
| `test_create_habit_valid_name` | RF-1.1 | Crear hábito con nombre válido retorna objeto `Habit` |
| `test_create_habit_default_start_date` | RF-1.2 | Sin fecha de inicio se asigna la fecha actual |
| `test_create_habit_empty_name` | RF-1.3 | Nombre vacío levanta excepción con mensaje en español |
| `test_create_habit_name_too_long` | RF-1.4 | Nombre > 60 caracteres levanta excepción |
| `test_create_habit_future_start_date` | Caso límite | Fecha en futuro se corrige a fecha actual |
| `test_mark_completed_success` | RF-2.1 | Marcar hábito retorna éxito |
| `test_mark_completed_already_today` | RF-2.2 | Marcar ya completado hoy retorna mensaje de advertencia |
| `test_calculate_streak_today` | RF-4.1 | Racha cuenta hacia atrás desde hoy |
| `test_calculate_streak_not_today` | RF-4.2 | Último día no es hoy, racha es 0 |
| `test_calculate_streak_single_day` | RF-4.3 | Un día hoy, racha es 1 |
| `test_calculate_streak_with_gap` | RF-4.4 | Hueco en registros detiene conteo |
| `test_calculate_streak_empty` | RF-4 | Sin registros, racha es 0 |
| `test_list_habits_sorted_by_streak` | RF-3.2 | Lista ordenada por racha descendente |
| `test_list_habits_alpha_tiebreak` | RF-3.3 | Misma racha, orden alfabético secundario |
| `test_list_habits_empty` | RF-3.4 | Sin hábitos, retorna lista vacía |

### Tests de `habits/storage.py` (test_storage.py)

| Prueba | RF cubierto | Descripción |
|--------|-------------|-------------|
| `test_create_habit_persists` | RF-1 | Crear y leer hábito de la base de datos |
| `test_get_completions_for_habit` | RF-2 | Obtener registros de completado |
| `test_unique_constraint_prevents_duplicate` | RF-2.2 | Intentar insertar duplicado levanta error de integridad |
| `test_list_all_habits` | RF-3 | Listar todos los hábitos |
| `test_database_created_on_first_use` | RFN-3 | La BD se crea automáticamente si no existe |

### Cobertura objetivo

- ≥80 % en `habits/core.py` (funciones puras y métodos de dominio).
- ≥80 % en `habits/storage.py` (capa de persistencia).
- `habits/app.py` se valida mediante verificación manual, no tests automatizados (respetando principio 3: la UI no contiene lógica testeable).

### Ejecución

```bash
pytest -q --cov=habits --cov-report=term-missing
```
