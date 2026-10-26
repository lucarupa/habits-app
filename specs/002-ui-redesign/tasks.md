# Tareas de Implementación — 002 Rediseño de interfaz con estadísticas

Cada tarea está pensada para completarse en 20–30 minutos. Las tareas de dominio y persistencia
siguen un enfoque TDD: primero el test que falla, después la implementación.

> No se deben añadir minutos, sesiones, “Quitar registro”, Ajustes ni Progreso. Tampoco se
> modifica la spec 001; esta spec amplía únicamente la interfaz y las estadísticas derivadas.

---

## Fase 1: Modelo de dominio y estadísticas (`core.py`)

- [x] **Tarea 1.1:** Añadir el icono al modelo `Habit` y a `create_habit`
  - **RF:** RF-2.6, RF-2.8
  - **Hecho cuando:** Existen tests que verifican el icono por defecto, el icono elegido y el
    icono inválido; `Habit` y `create_habit` aceptan `icon` sin romper los tests existentes.

- [x] **Tarea 1.2:** Implementar `calculate_best_streak(completed_dates)`
  - **RF:** RF-3.3
  - **Hecho cuando:** Tests para vacío, un día, días consecutivos, huecos y racha actual como
    mejor racha pasan; la función retorna el bloque consecutivo más largo.

- [x] **Tarea 1.3:** Implementar `count_registered_days` y `HabitStats`
  - **RF:** RF-3.2, RF-3.4, RF-3.5
  - **Hecho cuando:** `HabitStats` contiene racha actual, mejor racha y días registrados;
    los tests de hábito vacío, activo e inactivo pasan sin duplicar el cálculo de racha.

- [x] **Tarea 1.4:** Implementar `build_activity_heatmap`
  - **RF:** RF-4.1, RF-4.2, RF-4.3, RF-4.4, RF-4.6
  - **Hecho cuando:** La función devuelve 35 celdas de 5 semanas por 7 días, marca completados,
    hoy y días futuros; los tests de dimensiones, contenido y heatmap vacío pasan.

- [x] **Tarea 1.5:** Verificar cobertura de `habits/core.py`
  - **RF:** RFN-4
  - **Hecho cuando:** `pytest --cov=habits.core --cov-report=term-missing` muestra ≥80 % y
    todos los tests de dominio pasan.

---

## Fase 2: Persistencia del icono (`storage.py`)

- [x] **Tarea 2.1:** Escribir tests de migración y columna `icon`
  - **RF:** RF-2.8, RF-2.9
  - **Hecho cuando:** Los tests fallan inicialmente y cubren: base nueva con columna `icon`,
    base antigua migrada con valor `book`, y conservación de hábitos y registros.

- [x] **Tarea 2.2:** Implementar la columna `icon` y la migración en `init_db`
  - **RF:** RF-2.8, RF-2.9, RFN-1
  - **Hecho cuando:** Una base nueva crea `icon TEXT NOT NULL DEFAULT 'book'`; una base
    existente recibe la columna sin perder datos y `init_db` sigue siendo idempotente.

- [x] **Tarea 2.3:** Actualizar `HabitRow`, `create_habit_db`, `get_habit_db` y
  `list_all_habits_db` para devolver el icono
  - **RF:** RF-2.8
  - **Hecho cuando:** El icono se guarda y se lee de vuelta; los tests existentes de creación,
    lectura y listado siguen pasando; los nuevos tests de icono pasan.

- [x] **Tarea 2.4:** Verificar cobertura de `habits/storage.py`
  - **RF:** RFN-4, RFN-1
  - **Hecho cuando:** `pytest --cov=habits.storage --cov-report=term-missing` muestra ≥80 % y
    la suite completa pasa.

---

## Fase 3: Estructura visual y navegación (`app.py`)

- [x] **Tarea 3.1:** Crear el cargador de estado de la aplicación
  - **RF:** RF-1.1, RF-1.3, RF-1.5, RFN-3
  - **Hecho cuando:** La app obtiene hábitos y fechas desde `storage`, calcula rachas y
    estadísticas con `core`, y mantiene el identificador del hábito seleccionado sin lógica
    duplicada en los widgets.

- [x] **Tarea 3.2:** Construir la barra lateral con “Mis hábitos”, “+ Nuevo” y lista de hábitos
  - **RF:** RF-1.2, RF-1.4, RF-1.6, RF-7.2
  - **Hecho cuando:** Cada elemento muestra icono, nombre y racha; el orden es racha
    descendente con desempate alfabético; el seleccionado se resalta y se puede cambiar.

- [x] **Tarea 3.3:** Construir el encabezado del panel de detalle
  - **RF:** RF-3.1, RF-7.4
  - **Hecho cuando:** El detalle muestra icono, nombre, “Hábito de estudio” y fecha de inicio
    en dd/mm/aaaa del hábito seleccionado.

- [x] **Tarea 3.4:** Construir el estado vacío
  - **RF:** RF-6.1, RF-6.2, RF-6.4
  - **Hecho cuando:** Sin hábitos, la barra lateral muestra “No hay hábitos aún” y el panel
    principal muestra ilustración, título y botón “+ Crear hábito”; al crear el primero, el
    estado desaparece.

- [x] **Tarea 3.5:** Aplicar el tema visual y el tamaño de ventana
  - **RF:** RF-7.1, RF-7.3, RF-7.5
  - **Hecho cuando:** La interfaz usa fondo crema, superficies claras y acentos verdes; la
    ventana permite ver barra lateral y detalle sin scroll horizontal; los textos están en
    español.

---

## Fase 4: Creación de hábitos con diálogo modal

- [x] **Tarea 4.1:** Crear el diálogo modal con nombre, fecha e icono
  - **RF:** RF-2.1, RF-2.6
  - **Hecho cuando:** “+ Nuevo” y “+ Crear hábito” abren el mismo diálogo; el selector muestra
    el catálogo de iconos y permite elegir uno o dejar el valor por defecto.

- [x] **Tarea 4.2:** Implementar las validaciones del formulario
  - **RF:** RF-2.2, RF-2.3, RF-2.5, RF-2.10
  - **Hecho cuando:** Nombre vacío, nombre >60, fecha inválida y fecha futura producen el
    mensaje correcto; el diálogo no se cierra ante error y no se crea el hábito.

- [x] **Tarea 4.3:** Persistir la creación y refrescar la interfaz
  - **RF:** RF-2.7, RF-2.9
  - **Hecho cuando:** Al guardar, el hábito se persiste con su icono, el diálogo se cierra, la
    barra lateral se actualiza y el nuevo hábito queda seleccionado.

- [x] **Tarea 4.4:** Conectar el CTA del estado vacío con el diálogo
  - **RF:** RF-6.3
  - **Hecho cuando:** El botón “+ Crear hábito” del estado vacío abre el mismo modal y, tras
    crear, se muestra el detalle del hábito.

---

## Fase 5: Estadísticas y heatmap

- [x] **Tarea 5.1:** Construir las tarjetas de estadísticas
  - **RF:** RF-3.2, RF-3.3, RF-3.4, RF-3.5, RF-3.6
  - **Hecho cuando:** El detalle muestra “Racha actual”, “Mejor racha” y “Días registrados”
    usando `get_habit_stats`; un hábito sin registros muestra 0 en las tres tarjetas.

- [x] **Tarea 5.2:** Construir el heatmap de 5 semanas
  - **RF:** RF-4.1, RF-4.2, RF-4.3, RF-4.4, RF-4.5, RF-4.6
  - **Hecho cuando:** Se pinta una cuadrícula de 7 filas por 5 columnas; los días completados
    se distinguen de los no completados; hoy está resaltado; los días futuros se ven como no
    disponibles; la leyenda “No completado / Completado” es visible.

- [x] **Tarea 5.3:** Refrescar estadísticas y heatmap tras un registro
  - **RF:** RF-3.6, RF-4.7
  - **Hecho cuando:** Al registrar hoy, las tarjetas, la celda de hoy, la leyenda y la racha
    de la barra lateral se actualizan sin reiniciar la aplicación.

---

## Fase 6: Registro del día actual

- [ ] **Tarea 6.1:** Construir el panel “Registrar hoy”
  - **RF:** RF-5.1, RF-5.2, RF-5.5, RF-5.6
  - **Hecho cuando:** El panel muestra la fecha actual en dd/mm/aaaa y un botón “Guardar”
    habilitado cuando el hábito no está completado hoy; no hay selector de fecha, minutos ni
    “Quitar registro”.

- [ ] **Tarea 6.2:** Implementar el guardado y la prevención de duplicados
  - **RF:** RF-5.3, RF-5.4
  - **Hecho cuando:** “Guardar” persiste el día actual, muestra confirmación y actualiza la
    interfaz; si ya estaba completado, muestra “Ya registrado hoy” y no crea un duplicado.

- [ ] **Tarea 6.3:** Verificar manualmente el flujo completo
  - **RF:** RF-5
  - **Hecho cuando:** Se crea un hábito, se registra hoy, se ve la racha 1, se vuelve a pulsar
    Guardar y aparece el mensaje de duplicado; al reiniciar, los datos siguen visibles.

---

## Fase 7: Verificación final

- [ ] **Tarea 7.1:** Actualizar `README.md` con el nuevo diseño y las estadísticas
  - **RF:** Documentación
  - **Hecho cuando:** El README describe la barra lateral, el detalle, las tres estadísticas,
    el heatmap, los iconos y cómo ejecutar la app y los tests.

- [ ] **Tarea 7.2:** Ejecutar la suite completa y la cobertura
  - **RF:** RFN-4
  - **Hecho cuando:** `pytest -q` retorna 0 fallos y la cobertura de `core.py` y `storage.py`
    es ≥80 %.

- [ ] **Tarea 7.3:** Verificar manualmente los criterios de finalización y los RFN de la spec 002
  - **RF:** Todos
  - **Hecho cuando:** Se cumplen los 8 criterios de finalización de
    `specs/002-ui-redesign/spec.md`, la app inicia en menos de 3 segundos, funciona sin
    conexión y no se añadieron dependencias externas no aprobadas.

- [ ] **Tarea 7.4:** Comparar la interfaz con los mockups y ajustar detalles visuales
  - **RF:** RF-7
  - **Hecho cuando:** La barra lateral, el detalle, las tarjetas, el heatmap, el modal y el
    estado vacío se aproximan a los mockups sin añadir funcionalidades fuera de alcance.

- [ ] **Tarea 7.5:** Revisar que no se haya añadido nada fuera de alcance
  - **RF:** RF-5.5
  - **Hecho cuando:** No existen minutos, sesiones, “Quitar registro”, Ajustes ni Progreso, y
    la suite sigue pasando.
