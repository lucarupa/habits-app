# Tareas de Implementación — 001 Habits MVP

Cada tarea está diseñada para completarse en 20–30 minutos. Se presentan en orden de dependencia: completa la tarea anterior antes de pasar a la siguiente.

---

## Fase 1: Preparación del proyecto

- [x] **Tarea 1.1:** Crear estructura de directorios y archivos vacíos
  - **RF:** Infraestructura
  - **Hecho cuando:** Existen los directorios `habits/`, `tests/`, `data/` y los archivos `habits/__init__.py`, `habits/core.py`, `habits/storage.py`, `habits/app.py`, `tests/test_core.py`, `tests/test_storage.py`.

- [x] **Tarea 1.2:** Configurar el entorno de desarrollo con pytest
  - **RF:** Infraestructura
  - **Hecho cuando:** El comando `pytest -q` se ejecuta sin errores (aunque no haya tests aún) y `pyproject.toml` o `pytest.ini` existe.

---

## Fase 2: Modelo de dominio (`core.py`)

- [x] **Tarea 2.1:** Definir la clase `Habit` con atributos `id`, `name`, `start_date` y type hints
  - **RF:** RF-1.1, RF-1.2
  - **Hecho cuando:** La clase `Habit` se puede instanciar con nombre y fecha de inicio, y todos los atributos tienen type hints.

- [x] **Tarea 2.2:** Implementar la función `create_habit(name, start_date=None)` con validaciones
  - **RF:** RF-1.1, RF-1.2, RF-1.3, RF-1.4, caso límite (fecha futura)
  - **Hecho cuando:** La función retorna un `Habit` válido, levanta excepción para nombre vacío, levanta excepción para nombre > 60 caracteres, asigna fecha actual si no se proporciona, y corrige fecha futura a fecha actual.

- [x] **Tarea 2.3:** Implementar la función `mark_completed(habit_id, completed_dates, today)`
  - **RF:** RF-2.1, RF-2.2, RF-2.3
  - **Hecho cuando:** La función retorna éxito al marcar un hábito, retorna un mensaje de advertencia si ya está marcado hoy, y rechaza fechas distintas a hoy.

- [x] **Tarea 2.4:** Implementar la función `calculate_streak(completed_dates, today)`
  - **RF:** RF-4.1, RF-4.2, RF-4.3, RF-4.4
  - **Hecho cuando:** La función retorna la racha correcta: cuenta hacia atrás desde hoy, retorna 0 si el último día no es hoy, retorna 1 para un solo día hoy, y se detiene ante un hueco.

- [x] **Tarea 2.5:** Implementar la función `list_habits_with_streak(habits, completions_by_habit, today)`
  - **RF:** RF-3.1, RF-3.2, RF-3.3, RF-3.4
  - **Hecho cuando:** La función retorna una lista de hábitos con su racha, ordenada por racha descendente y nombre alfabético como desempate, y retorna lista vacía cuando no hay hábitos.

---

## Fase 3: Tests de lógica de dominio (`test_core.py`)

- [x] **Tarea 3.1:** Escribir tests para `create_habit` (nombre válido, fecha por defecto, nombre vacío, nombre largo, fecha futura)
  - **RF:** RF-1.1, RF-1.2, RF-1.3, RF-1.4, caso límite
  - **Hecho cuando:** 5 tests pasan: `test_create_habit_valid_name`, `test_create_habit_default_start_date`, `test_create_habit_empty_name`, `test_create_habit_name_too_long`, `test_create_habit_future_start_date`.

- [x] **Tarea 3.2:** Escribir tests para `mark_completed` (éxito, duplicado hoy)
  - **RF:** RF-2.1, RF-2.2
  - **Hecho cuando:** 2 tests pasan: `test_mark_completed_success`, `test_mark_completed_already_today`.

- [x] **Tarea 3.3:** Escribir tests para `calculate_streak` (hoy, no hoy, un día, hueco, vacío)
  - **RF:** RF-4.1, RF-4.2, RF-4.3, RF-4.4
  - **Hecho cuando:** 5 tests pasan: `test_calculate_streak_today`, `test_calculate_streak_not_today`, `test_calculate_streak_single_day`, `test_calculate_streak_with_gap`, `test_calculate_streak_empty`.

- [x] **Tarea 3.4:** Escribir tests para `list_habits_with_streak` (orden por racha, desempate alfabético, lista vacía)
  - **RF:** RF-3.2, RF-3.3, RF-3.4
  - **Hecho cuando:** 3 tests pasan: `test_list_habits_sorted_by_streak`, `test_list_habits_alpha_tiebreak`, `test_list_habits_empty`.

- [x] **Tarea 3.5:** Verificar cobertura ≥80 % en `core.py`
  - **RF:** Constitución principio 4
  - **Hecho cuando:** `pytest --cov=habits.core --cov-report=term-missing` muestra ≥80 % de cobertura.

---

## Fase 4: Persistencia SQLite (`storage.py`)

- [x] **Tarea 4.1:** Implementar la función `init_db()` para crear las tablas `habits` y `completions`
  - **RF:** RFN-3
  - **Hecho cuando:** La función crea el archivo `data/habits.db` con las tablas definidas en el plan, incluyendo la restricción `UNIQUE(habit_id, completed_date)`.

- [x] **Tarea 4.2:** Implementar las funciones `create_habit_db(name, start_date)` y `get_habit_db(habit_id)`
  - **RF:** RF-1
  - **Hecho cuando:** Un hábito creado se puede leer de vuelta con los mismos datos.

- [x] **Tarea 4.3:** Implementar las funciones `mark_completed_db(habit_id, date)` y `is_completed_today_db(habit_id, today)`
  - **RF:** RF-2.1, RF-2.2
  - **Hecho cuando:** Marcar un hábito persiste la fecha y la consulta de duplicado retorna correctamente.

- [x] **Tarea 4.4:** Implementar las funciones `list_all_habits_db()` y `get_completions_db(habit_id)`
  - **RF:** RF-3
  - **Hecho cuando:** Se obtienen todos los hábitos y sus fechas de completado desde la base de datos.

---

## Fase 5: Tests de persistencia (`test_storage.py`)

- [x] **Tarea 5.1:** Escribir tests para creación y lectura de hábitos, y restricción UNIQUE
  - **RF:** RF-1, RF-2.2
  - **Hecho cuando:** 3 tests pasan: `test_create_habit_persists`, `test_get_completions_for_habit`, `test_unique_constraint_prevents_duplicate`.

- [x] **Tarea 5.2:** Escribir tests para listar hábitos y creación automática de BD
  - **RF:** RF-3, RFN-3
  - **Hecho cuando:** 2 tests pasan: `test_list_all_habits`, `test_database_created_on_first_use`.

- [x] **Tarea 5.3:** Verificar cobertura ≥80 % en `storage.py`
  - **RF:** Constitución principio 4
  - **Hecho cuando:** `pytest --cov=habits.storage --cov-report=term-missing` muestra ≥80 % de cobertura.

---

## Fase 6: Interfaz Flet (`app.py`)

- [x] **Tarea 6.1:** Crear la ventana principal de Flet con navegación entre vistas
  - **RF:** Infraestructura de UI
  - **Hecho cuando:** La app inicia con una ventana Flet que permite navegar entre al menos dos vistas.

- [x] **Tarea 6.2:** Implementar la vista de creación de hábitos con campo de nombre y fecha opcional
  - **RF:** RF-1.1, RF-1.2, RF-1.3, RF-1.4
  - **Hecho cuando:** El usuario puede ingresar un nombre y una fecha opcional, y al enviar se crea el hábito o se muestra el mensaje de error correspondiente.

- [x] **Tarea 6.3:** Implementar la vista de lista de hábitos con racha y botones de marcar
  - **RF:** RF-2.1, RF-2.2, RF-3.1, RF-3.2, RF-3.3, RF-3.4
  - **Hecho cuando:** La vista muestra todos los hábitos ordenados por racha descendente, cada uno con un botón para marcar como completado, y muestra mensajes adecuados (ya completado hoy, sin hábitos).

- [x] **Tarea 6.4:** Formatear las fechas en la interfaz usando el formato dd/mm/aaaa
  - **RF:** Dudas abiertas (formato de fecha)
  - **Hecho cuando:** Todas las fechas visibles para el usuario aparecen en formato dd/mm/aaaa.

- [x] **Tarea 6.5:** Conectar la UI con `core.py` y `storage.py` para el flujo completo
  - **RF:** RF-1, RF-2, RF-3, RF-4
  - **Hecho cuando:** El usuario puede crear un hábito, marcarlo como hecho hoy, y ver la lista actualizada con la racha correcta, sin recargar la app.

---

## Fase 7: Verificación final

- [x] **Tarea 7.1:** Ejecutar toda la suite de tests y confirmar que todo pasa
  - **RF:** Constitución principio 4
  - **Hecho cuando:** `pytest -q` retorna 0 fallos y la cobertura combinada en `core.py` y `storage.py` es ≥80 %.

- [x] **Tarea 7.2:** Verificar manualmente los criterios de finalización de la spec
  - **RF:** Criterios de finalización 1–6
  - **Hecho cuando:** Los 6 criterios de finalización de `spec.md` se cumplen al ejecutar la app manualmente.

- [x] **Tarea 7.3:** Actualizar `README.md` con descripción del proyecto y instrucciones de uso
  - **RF:** RFN-2
  - **Hecho cuando:** El `README.md` contiene una descripción breve, los requisitos (Python 3.12+, Flet), cómo ejecutar la app y una mención a los tests.
