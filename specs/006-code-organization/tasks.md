# Tareas de implementación — 006 Organización del código y límite de tamaño por módulo

## Fase 1: Medidor de tamaño (`module_size.py`)

- [x] **Tarea 1.1:** Escribir los tests del conteo de líneas con contenido
  - **RF:** RF-1.2, RF-1.3, RF-1.4, RF-1.5, RF-3.2
  - **Hecho cuando:** Los tests cubren líneas vacías, comentarios completos con y sin sangría,
    código, docstrings, cadenas multilínea, comentarios al final de una instrucción y una línea
    `#` dentro de una docstring; los casos de 250 y 251 líneas quedan definidos y la suite
    muestra los fallos esperados.

- [x] **Tarea 1.2:** Escribir los tests de búsqueda de módulos sobredimensionados
  - **RF:** RF-3.1, RF-3.5, RF-3.6
  - **Hecho cuando:** Los tests usan directorios temporales para comprobar el recorrido
    recursivo, la detección de subpaquetes nuevos, la exclusión de cachés y entornos virtuales y
    el orden estable de los infractores; la suite muestra los fallos esperados.

- [x] **Tarea 1.3:** Implementar `habits/module_size.py`
  - **RF:** RF-1.1, RF-1.2, RF-1.3, RF-1.4, RF-1.5, RF-3.1, RF-3.2, RF-3.5, RF-3.6
  - **Hecho cuando:** El módulo cuenta líneas con `tokenize`, localiza módulos de producción de
    forma recursiva, ignora rutas no inspeccionables y devuelve ruta y conteo de cada infractor;
    los tests de las tareas 1.1 y 1.2 pasan.

- [x] **Tarea 1.4:** Escribir el test unitario del mensaje de infracción
  - **RF:** RF-3.3, RF-3.4
  - **Hecho cuando:** Un test comprueba que el mensaje incluye todos los infractores con su ruta
    y conteo en un único texto en español, y que no hay mensaje cuando todos cumplen; la suite
    muestra el fallo esperado.

- [x] **Tarea 1.5:** Implementar la composición del mensaje y la guardia reutilizable
  - **RF:** RF-3.3, RF-3.4
  - **Hecho cuando:** El módulo ofrece una función que falla con todos los infractores juntos y
    otra que pasa sin advertencias cuando no hay ninguno; el test de la tarea 1.4 pasa.

## Fase 2: Paquete de dominio (`habits/domain/`)

- [x] **Tarea 2.1:** Migrar los tests de dominio a las nuevas rutas
  - **RF:** RF-2.1, RF-2.5, RF-5.1, RF-5.3
  - **Hecho cuando:** `tests/test_core.py` y los tests que usan funciones de dominio importan
    desde `habits.domain`, conservan los mismos casos y la suite muestra los fallos esperados por
    los módulos aún inexistentes.

- [x] **Tarea 2.2:** Crear `habits/domain/models.py`
  - **RF:** RF-2.2, RF-2.3, RF-5.3
  - **Hecho cuando:** `Habit`, `HabitStats`, `HeatmapDay` y `RecoverableGap` se importan desde el
    nuevo módulo con las mismas entradas, salidas y textos, sin dependencias de Flet ni SQLite.

- [x] **Tarea 2.3:** Crear `habits/domain/habits.py`
  - **RF:** RF-2.2, RF-2.3, RF-5.3
  - **Hecho cuando:** Las operaciones de alta, edición y marcado de completados se trasladan sin
    reescribir su lógica ni sus validaciones, y sus tests pasan desde la nueva ruta.

- [x] **Tarea 2.4:** Crear `habits/domain/streaks.py`, `recovery.py` y `heatmap.py`
  - **RF:** RF-2.1, RF-2.2, RF-2.3, RF-5.3
  - **Hecho cuando:** Rachas, orden de hábitos, huecos recuperables, estadísticas con recuperados
    y construcción del heatmap quedan separados por responsabilidad, cada módulo respeta el
    límite y los tests de dominio pasan.

- [x] **Tarea 2.5:** Eliminar `habits/core.py` y verificar el dominio
  - **RF:** RF-2.5, RF-2.6, RF-2.7, RF-5.1
  - **Hecho cuando:** No queda ninguna referencia a `habits.core`, todos los imports apuntan a
    `habits.domain`, no hay ciclos entre los nuevos módulos y la suite vuelve a pasar.

## Fase 3: Paquete de persistencia (`habits/persistence/`)

- [ ] **Tarea 3.1:** Migrar los tests de persistencia a las nuevas rutas
  - **RF:** RF-2.1, RF-2.5, RF-5.1, RF-5.2
  - **Hecho cuando:** `tests/test_storage.py` y los tests que preparan bases de datos importan
    desde `habits.persistence`, conservan el esquema y los datos de prueba y la suite muestra los
    fallos esperados.

- [ ] **Tarea 3.2:** Crear `habits/persistence/schema.py`
  - **RF:** RF-2.2, RF-5.2, RF-5.6
  - **Hecho cuando:** `init_db`, `HabitRow` y la inicialización del esquema se trasladan sin
    cambiar tablas, columnas ni datos, y los tests de creación de base pasan.

- [ ] **Tarea 3.3:** Crear `habits/persistence/habits_repo.py`
  - **RF:** RF-2.2, RF-2.3, RF-5.2, RF-5.3
  - **Hecho cuando:** El CRUD de hábitos se importa desde el nuevo módulo, conserva firmas y
    resultados y sus tests pasan.

- [ ] **Tarea 3.4:** Crear `habits/persistence/completions_repo.py`
  - **RF:** RF-2.2, RF-2.3, RF-5.2, RF-5.3
  - **Hecho cuando:** Registros, días recuperados y consultas se trasladan sin alterar el
    esquema ni los cálculos, y sus tests pasan.

- [ ] **Tarea 3.5:** Eliminar `habits/storage.py` y verificar la persistencia
  - **RF:** RF-2.5, RF-2.6, RF-2.7, RF-5.1, RF-5.2
  - **Hecho cuando:** No queda ninguna referencia a `habits.storage`, los repositorios no
    dependen de la interfaz y la suite de persistencia pasa con los mismos resultados.

## Fase 4: Paquete de estado (`habits/state/`)

- [ ] **Tarea 4.1:** Migrar los tests de estado a las nuevas rutas
  - **RF:** RF-2.1, RF-2.5, RF-5.1, RF-5.3
  - **Hecho cuando:** `tests/test_app_state.py` y los tests que construyen estados importan desde
    `habits.state`, conservan los mismos casos y la suite muestra los fallos esperados.

- [ ] **Tarea 4.2:** Crear `habits/state/models.py`
  - **RF:** RF-2.2, RF-2.3, RF-5.3
  - **Hecho cuando:** `HabitState`, `SidebarItem`, `DetailHeader`, las tarjetas de estadísticas y
    sus textos se importan desde el nuevo módulo, sin dependencias de Flet ni SQLite.

- [ ] **Tarea 4.3:** Crear `habits/state/app_state.py` y `loader.py`
  - **RF:** RF-2.2, RF-2.3, RF-2.6, RF-5.3
  - **Hecho cuando:** `AppState`, sus vistas derivadas y `load_app_state` se trasladan con las
    mismas entradas, salidas y cálculos, y los tests de estado pasan.

- [ ] **Tarea 4.4:** Eliminar `habits/app_state.py` y verificar el estado
  - **RF:** RF-2.5, RF-2.6, RF-2.7, RF-5.1
  - **Hecho cuando:** No queda ninguna referencia a `habits.app_state`, el paquete de estado no
    importa Flet ni SQLite y la suite vuelve a pasar.

## Fase 5: Paquete de formularios (`habits/forms/`)

- [ ] **Tarea 5.1:** Migrar los tests del formulario a las nuevas rutas
  - **RF:** RF-2.1, RF-2.5, RF-5.1, RF-5.3
  - **Hecho cuando:** `tests/test_habit_form.py` y los tests que validan o guardan formularios
    importan desde `habits.forms`, conservan los mismos casos y la suite muestra los fallos
    esperados.

- [ ] **Tarea 5.2:** Crear `habits/forms/models.py`
  - **RF:** RF-2.2, RF-2.3, RF-5.3
  - **Hecho cuando:** Los datos del formulario, resultados, constantes e iconos se importan desde
    el nuevo módulo con los mismos valores y textos.

- [ ] **Tarea 5.3:** Crear `habits/forms/validation.py` y `service.py`
  - **RF:** RF-2.2, RF-2.3, RF-5.3
  - **Hecho cuando:** La validación de fechas, nombre e icono y el alta o actualización desde el
    formulario se trasladan sin reescribir reglas ni mensajes, y sus tests pasan.

- [ ] **Tarea 5.4:** Eliminar `habits/habit_form.py` y verificar los formularios
  - **RF:** RF-2.5, RF-2.6, RF-2.7, RF-5.1
  - **Hecho cuando:** No queda ninguna referencia a `habits.habit_form`, el paquete no depende de
    Flet ni de widgets y la suite vuelve a pasar.

## Fase 6: Paquete de interfaz (`habits/ui/`)

- [ ] **Tarea 6.1:** Migrar los tests de widgets a las nuevas rutas
  - **RF:** RF-2.1, RF-2.4, RF-2.5, RF-5.1, RF-5.4
  - **Hecho cuando:** Los tests de widgets, diálogos y flujos importan cada control desde
    `habits.ui`, conservan sus aserciones sobre textos, callbacks y estructura y la suite muestra
    los fallos esperados.

- [ ] **Tarea 6.2:** Crear `habits/ui/common.py` y `page.py`
  - **RF:** RF-2.2, RF-2.4, RF-5.3, RF-5.4
  - **Hecho cuando:** Los iconos, etiquetas, formatos visuales y la configuración de página se
    importan desde los nuevos módulos con el mismo comportamiento observable.

- [ ] **Tarea 6.3:** Crear los componentes de la vista principal
  - **RF:** RF-2.1, RF-2.2, RF-2.4, RF-5.4
  - **Hecho cuando:** `Sidebar`, `HabitDetailHeader`, `HabitStatsCards`, `ActivityHeatmap`,
    `TodayRegistrationPanel` y `EmptyDetailPanel` viven en módulos separados, respetan el límite
    y los tests de widgets pasan.

- [ ] **Tarea 6.4:** Crear los diálogos de la interfaz
  - **RF:** RF-2.1, RF-2.2, RF-2.4, RF-5.4
  - **Hecho cuando:** `HabitFormDialog`, `DeleteHabitDialog` y `StreakRecoveryDialog` se importan
    desde `habits.ui`, mantienen textos, validaciones y callbacks y sus tests pasan.

- [ ] **Tarea 6.5:** Reducir `habits/app.py` a punto de entrada
  - **RF:** RF-2.1, RF-2.2, RF-2.4, RF-2.5, RF-5.4
  - **Hecho cuando:** `app.py` solo conserva `main` y la conexión entre estado, persistencia y
    widgets; se eliminan `CreateHabitView`, `ListHabitsView` y `create_main_view` por no tener
    referencias, y los tests de flujo pasan.

- [ ] **Tarea 6.6:** Verificar la interfaz completa
  - **RF:** RF-2.6, RF-2.7, RF-5.1, RF-5.4
  - **Hecho cuando:** La UI no importa SQLite ni repositorios, no hay ciclos, todos los módulos de
    `habits/ui/` respetan el límite y la suite de widgets y flujos vuelve a pasar.

## Fase 7: Guardias de arquitectura y de tamaño

- [ ] **Tarea 7.1:** Escribir los tests de arquitectura
  - **RF:** RF-2.2, RF-2.5, RF-2.6, RFN-6
  - **Hecho cuando:** Los tests comprueban que dominio, persistencia y estado no importan Flet,
    que la UI no importa SQLite ni repositorios, que no hay ciclos, que los módulos monolíticos
    ya no existen y que los paquetes nuevos son importables; la suite muestra los fallos
    esperados si hay infracciones.

- [ ] **Tarea 7.2:** Corregir las dependencias detectadas
  - **RF:** RF-2.6, RF-2.7, RFN-6
  - **Hecho cuando:** Los tests de la tarea 7.1 pasan y la separación de capas queda alineada con
    la constitución.

- [ ] **Tarea 7.3:** Activar la guardia global del límite de tamaño
  - **RF:** RF-1.1, RF-1.6, RF-3.1, RF-3.3, RF-3.6
  - **Hecho cuando:** `tests/test_module_size.py` recorre el paquete de producción real, detecta
    automáticamente los módulos nuevos y falla con un único mensaje que lista ruta y conteo de
    todos los infractores.

- [ ] **Tarea 7.4:** Ajustar los módulos que superen el límite
  - **RF:** RF-1.1, RF-1.8, RF-2.1
  - **Hecho cuando:** Todos los módulos de producción, incluidos archivos de inicialización y
    subpaquetes, tienen 250 líneas con contenido o menos, y la guardia global pasa.

## Fase 8: Documentación

- [ ] **Tarea 8.1:** Escribir o ajustar los tests de documentación
  - **RF:** RF-4.1, RF-4.2, RF-4.3, RF-4.4
  - **Hecho cuando:** Los tests comprueban que la documentación describe el límite de 250 líneas,
    la forma de contar, las exclusiones, la responsabilidad de cada paquete y los conteos reales
    de la suite; la suite muestra los fallos esperados.

- [ ] **Tarea 8.2:** Actualizar `README.md`
  - **RF:** RF-4.1, RF-4.2, RF-4.3
  - **Hecho cuando:** El README incluye la regla de tamaño, la forma de contar, los archivos
    excluidos, la estructura de `habits/` con la responsabilidad de cada módulo y los conteos
    actualizados de pruebas.

- [ ] **Tarea 8.3:** Revisar la documentación de las specs
  - **RF:** RF-4.4
  - **Hecho cuando:** `spec.md`, `plan.md` y `tasks.md` de la spec 006 reflejan el estado final,
    las decisiones aplicadas y las tareas completadas.

## Fase 9: Verificación final

- [ ] **Tarea 9.1:** Ejecutar la suite completa y la cobertura
  - **RF:** RF-5.1, RF-5.5, RFN-7
  - **Hecho cuando:** `.venv/bin/python -m pytest -q` pasa sin fallos y la cobertura de los
    módulos de `domain`, `persistence`, `state`, `forms` y `module_size` alcanza al menos el
    80 %.

- [ ] **Tarea 9.2:** Verificar la conservación del comportamiento y los datos
  - **RF:** RF-5.2, RF-5.3, RF-5.4, RF-5.6
  - **Hecho cuando:** Se comprueba que una base existente conserva hábitos, registros, días
    recuperados, rachas, estadísticas y heatmap; que creación, edición, borrado, registro, aviso
    de duplicado y recuperación de racha funcionan igual; y que no hay dependencias ni cambios
    de esquema.

- [ ] **Tarea 9.3:** Verificar los criterios de finalización
  - **RF:** Todos
  - **Hecho cuando:** Todos los módulos de producción cumplen el límite, no quedan módulos
    monolíticos ni fachadas, las guardias de tamaño y arquitectura pasan, la documentación está
    actualizada y `tasks.md` queda completamente marcado.
