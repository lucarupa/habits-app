# Plan de Implementación — 006 Organización del código y límite de tamaño por módulo

## Estructura de módulos

La reorganización sustituye los módulos monolíticos actuales por paquetes con responsabilidades
separadas. `habits/app.py` queda como punto de entrada y no se conserva una fachada de
compatibilidad: todos los imports internos y de tests se migran a las nuevas ubicaciones.

```
habits/
├── app.py                       # Punto de entrada y conexión de main()
├── theme.py                     # Paleta y dimensiones (sin cambios)
├── registration.py              # Registro del día (sin cambios de responsabilidad)
├── module_size.py               # Medición y búsqueda de módulos sobredimensionados
├── domain/
│   ├── models.py                # Habit, HabitStats, HeatmapDay, RecoverableGap
│   ├── habits.py                # Alta, edición y marcado de completados
│   ├── streaks.py               # Rachas, días registrados y orden de hábitos
│   ├── recovery.py              # Huecos recuperables y estadísticas con recuperados
│   └── heatmap.py               # Construcción pura del heatmap
├── persistence/
│   ├── schema.py                # init_db, HabitRow y migraciones
│   ├── habits_repo.py           # CRUD de hábitos
│   └── completions_repo.py      # Registros, recuperados y consultas
├── state/
│   ├── models.py                # HabitState, SidebarItem, DetailHeader y tarjetas
│   ├── app_state.py             # AppState y sus vistas derivadas
│   └── loader.py                # load_app_state
├── forms/
│   ├── models.py                # Datos, resultados, constantes e iconos
│   ├── validation.py            # Fechas, nombre e icono
│   └── service.py               # Crear y actualizar desde el formulario
└── ui/
    ├── common.py                # Iconos, etiquetas y formatos visuales
    ├── page.py                  # configure_page y configuración de ventana
    ├── sidebar.py               # Sidebar
    ├── detail_header.py         # HabitDetailHeader
    ├── stats.py                 # HabitStatsCards
    ├── heatmap.py               # ActivityHeatmap
    ├── registration_panel.py    # TodayRegistrationPanel
    ├── empty.py                 # EmptyDetailPanel
    ├── form_dialog.py           # HabitFormDialog
    ├── delete_dialog.py         # DeleteHabitDialog
    └── recovery_dialog.py       # StreakRecoveryDialog
tests/
├── test_module_size.py          # Reglas de conteo y guardia global
├── test_architecture.py         # Separación de capas y ausencia de ciclos
└── ...                          # Tests existentes con imports migrados
```

### Presupuesto estimado de líneas con contenido

| Módulo | Responsabilidad | Líneas estimadas |
|--------|-----------------|-----------------:|
| `habits/domain/models.py` | Modelos de dominio | 59 |
| `habits/domain/habits.py` | Operaciones sobre hábitos | 97 |
| `habits/domain/streaks.py` | Rachas y orden | 91 |
| `habits/domain/recovery.py` | Huecos y estadísticas | 67 |
| `habits/domain/heatmap.py` | Heatmap puro | 38 |
| `habits/persistence/schema.py` | Esquema y migraciones | 69 |
| `habits/persistence/habits_repo.py` | CRUD de hábitos | 111 |
| `habits/persistence/completions_repo.py` | Registros y consultas | 142 |
| `habits/state/models.py` | Modelos de estado y textos | 105 |
| `habits/state/app_state.py` | `AppState` | 154 |
| `habits/state/loader.py` | Carga del estado | 54 |
| `habits/forms/models.py` | Modelos y constantes del formulario | 81 |
| `habits/forms/validation.py` | Validación y fechas | 116 |
| `habits/forms/service.py` | Persistencia del formulario | 73 |
| `habits/ui/common.py` | Utilidades visuales | 70 |
| `habits/ui/page.py` | Configuración de página | 25 |
| `habits/ui/sidebar.py` | Barra lateral | 107 |
| `habits/ui/detail_header.py` | Encabezado | 96 |
| `habits/ui/stats.py` | Tarjetas | 65 |
| `habits/ui/heatmap.py` | Heatmap visual | 131 |
| `habits/ui/registration_panel.py` | Panel de registro | 99 |
| `habits/ui/empty.py` | Estado vacío | 47 |
| `habits/ui/form_dialog.py` | Diálogo de hábito | 216 |
| `habits/ui/delete_dialog.py` | Confirmación de borrado | 75 |
| `habits/ui/recovery_dialog.py` | Confirmación de recuperación | 95 |
| `habits/app.py` | Entrada y `main` | 174 |
| `habits/module_size.py` | Medición y guardia | 80 |

Los valores son estimaciones basadas en el código actual. Cualquier módulo que supere 250
líneas con contenido durante la implementación se divide antes de continuar.

---

## Modelo de datos

No cambia el esquema de SQLite. Se conservan las tablas `habits` y `completions`, sus columnas y
sus datos. Los módulos de persistencia solo cambian de ubicación y de organización interna.

### Ejemplo de datos (sin cambios)

```
habits:
| id | name   | start_date | icon |
|----|--------|------------|------|
| 1  | Leer   | 2024-09-01 | book |
| 2  | Python | 2024-09-15 | code |

completions:
| id | habit_id | completed_date | recovered |
|----|----------|----------------|-----------|
| 1  | 1        | 2024-10-25     | 0         |
| 2  | 1        | 2024-10-26     | 1         |
```

La refactorización no migra ni reescribe filas. La suite de persistencia existente debe seguir
pasando con la misma base y los mismos resultados.

---

## Algoritmos clave (pseudocódigo)

### Contar líneas con contenido (RF-1)

```
funcion count_content_lines(source):
    lineas_con_contenido = conjunto vacío
    tokens = tokenizar(source)

    para cada token en tokens:
        si token.tipo en {ENCODING, NL, NEWLINE, INDENT, DEDENT, ENDMARKER, COMMENT}:
            continuar

        para numero en rango(token.inicio_linea, token.fin_linea):
            agregar numero a lineas_con_contenido

    retornar tamaño(lineas_con_contenido)
```

El uso de tokens evita falsos negativos con líneas que comienzan por `#` dentro de una docstring
o una cadena multilínea. Cada línea física ocupada por una cadena cuenta como contenido. Las
líneas vacías y los comentarios de línea completa no generan tokens de contenido.

**Casos cubiertos:**
- RF-1.2: líneas vacías y solo espacios no cuentan.
- RF-1.3: comentarios completos no cuentan.
- RF-1.4: docstrings, cadenas multilínea y comentarios al final de código cuentan.
- RF-1.5: 250 cumple y 251 falla.

### Buscar módulos sobredimensionados (RF-3)

```
funcion find_oversized_modules(root, limite=250):
    infractores = vacío

    para cada archivo .py bajo root de forma recursiva:
        si la ruta contiene caché, entorno virtual o archivo generado:
            continuar
        conteo = count_content_lines(leer archivo)
        si conteo > limite:
            agregar (ruta relativa, conteo)

    retornar infractores ordenados por ruta
```

La búsqueda no usa una lista fija de archivos. Cualquier módulo nuevo dentro del paquete de
producción se detecta automáticamente. El test construye un mensaje con todos los infractores,
su ruta y su conteo.

### Migrar imports sin fachada (RF-2.5)

```
para cada módulo de producción y test:
    reemplazar imports de core por domain
    reemplazar imports de storage por persistence
    reemplazar imports de app_state por state
    reemplazar imports de habit_form por forms
    reemplazar imports de widgets de app por ui

eliminar los módulos monolíticos antiguos
ejecutar la suite completa después de cada fase
```

No se mantienen archivos de reexportación. Los nombres públicos se importan desde su nuevo
módulo de responsabilidad.

---

## Decisiones técnicas

### 1. Contar con `tokenize` frente a contar líneas de texto

**Decisión:** Analizar el archivo con `tokenize` y marcar las líneas ocupadas por tokens que no
sean comentarios, saltos, indentación ni fin de archivo.

**Alternativa descartada:** Recorrer líneas y descartar las que empiezan por `#` o están vacías.

**Justificación:** El método simple contaría mal las líneas con `#` dentro de docstrings o
cadenas multilínea y las líneas de continuación. `tokenize` aplica las reglas de RF-1 sin
ambigüedad y es parte de la biblioteca estándar.

### 2. Límite solo para producción y aplicado de forma recursiva

**Decisión:** Inspeccionar únicamente archivos Python dentro del paquete de producción,
incluidos subpaquetes y archivos de inicialización.

**Alternativa descartada:** Aplicar el límite a tests, scripts, documentación y configuración.

**Justificación:** Los tests y scripts tienen naturalezas distintas y ya superan el límite por
motivos justificados. La regla busca mantener legible el código que se mantiene a diario
(RF-1.6 y RF-1.7).

### 3. Paquetes por capa y responsabilidad

**Decisión:** Crear `domain`, `persistence`, `state`, `forms` y `ui`, cada uno con módulos
pequeños y una responsabilidad dominante.

**Alternativa descartada:** Dividir cada archivo grande en fragmentos numerados sin cambiar de
capa.

**Justificación:** La división mecánica cumple el número de líneas pero no mejora la navegación
ni la separación UI/lógica de la constitución. Los paquetes por capa hacen evidente dónde vive
cada cambio (RF-2.2 y RFN-6).

### 4. Eliminar las vistas heredadas no utilizadas

**Decisión:** Eliminar `CreateHabitView`, `ListHabitsView` y `create_main_view` porque no se usan
en la aplicación actual ni en los tests.

**Alternativa descartada:** Moverlas a un módulo `ui/legacy.py` para conservarlas.

**Justificación:** Conservar código muerto añade módulos y distracción, y obliga a mantener
imports que nadie usa. La eliminación no cambia el comportamiento actual (RF-5.3 y RF-5.4).

### 5. Migrar todos los imports y eliminar los monolíticos

**Decisión:** Actualizar tests y producción a las nuevas rutas y borrar `core.py`, `storage.py`,
`app_state.py` y `habit_form.py`.

**Alternativa descartada:** Dejar estos archivos como fachadas que reexporten los nombres
antiguos.

**Justificación:** Una fachada mantendría dos ubicaciones para el mismo código, ocultaría la
estructura nueva y podría volver a superar el límite. El usuario eligió migrar todos los imports
(RF-2.5).

### 6. Test de tamaño dentro de la suite normal

**Decisión:** Añadir la guardia de tamaño como un test de pytest, sin hooks ni herramientas
externas.

**Alternativa descartada:** Usar un hook de pre-commit o un script manual.

**Justificación:** La constitución ya exige ejecutar pytest antes de mergear; el test se ejecuta
en el mismo comando y no depende de configuración local (RF-3.1 y RFN-7).

### 7. Verificar también la separación de capas

**Decisión:** Añadir un test de arquitectura que compruebe que dominio, persistencia y estado no
importan Flet, que la UI no importa SQLite y que no hay ciclos entre módulos.

**Alternativa descartada:** Confiar solo en la revisión manual de la estructura.

**Justificación:** La división por responsabilidad debe quedar protegida contra futuras
regresiones, igual que el límite de tamaño (RF-2.2, RF-2.6 y RFN-6).

---

## Estrategia de tests

### Tests del medidor y de la guardia (`test_module_size.py`)

| Prueba | RF cubierto | Descripción |
|--------|-------------|-------------|
| `test_count_ignores_blank_and_comment_lines` | RF-1.2, RF-1.3 | Vacías y comentarios completos no cuentan. |
| `test_count_includes_code_docstrings_and_inline_comments` | RF-1.4 | Código, docstrings y comentarios al final cuentan. |
| `test_count_handles_comment_like_lines_inside_docstrings` | RF-1.4 | Una línea `#` dentro de una docstring cuenta. |
| `test_exactly_250_content_lines_passes` | RF-1.5 | El límite es inclusivo. |
| `test_251_content_lines_fails` | RF-1.5 | Un módulo por encima falla. |
| `test_find_oversized_modules_scans_recursively` | RF-3.1, RF-3.6 | Encuentra archivos en subpaquetes. |
| `test_find_oversized_modules_ignores_non_production_paths` | RF-3.5 | Ignora cachés y entornos virtuales. |
| `test_current_production_modules_respect_limit` | RF-1.1, RF-3.1 | Guardia global sobre todos los módulos reales. |

### Tests de arquitectura (`test_architecture.py`)

| Prueba | RF cubierto | Descripción |
|--------|-------------|-------------|
| `test_domain_persistence_and_state_do_not_import_flet` | RF-2.2, RFN-6 | La lógica no depende de widgets. |
| `test_ui_does_not_import_sqlite_or_repositories` | RF-2.2, RFN-6 | La interfaz no accede a datos. |
| `test_production_modules_have_no_import_cycles` | RF-2.6 | Detecta ciclos entre módulos. |
| `test_old_monolithic_modules_are_removed` | RF-2.5 | No quedan fachadas ni archivos antiguos. |
| `test_new_packages_are_importable` | RF-2.2 | Los paquetes y puntos de entrada existen. |

### Tests existentes migrados

| Grupo | Cambio | RF cubierto |
|-------|--------|-------------|
| `test_core.py` | Importa `domain` en lugar de `core`. | RF-5.1, RF-5.3 |
| `test_storage.py` | Importa `persistence` en lugar de `storage`. | RF-5.1, RF-5.2 |
| `test_app_state.py` | Importa `state` en lugar de `app_state`. | RF-5.1, RF-5.3 |
| `test_habit_form.py` | Importa `forms` en lugar de `habit_form`. | RF-5.1, RF-5.3 |
| Tests de widgets y flujos | Importan cada control desde `ui`. | RF-5.1, RF-5.4 |
| Tests de alcance y documentación | Actualizan rutas y conteos. | RF-4.3, RF-5.5 |

### Cobertura objetivo

- ≥80 % en los módulos de `habits/domain/`.
- ≥80 % en los módulos de `habits/persistence/`.
- ≥80 % en los módulos de `habits/state/`.
- ≥80 % en los módulos de `habits/forms/`.
- `habits/ui/` se valida con los tests de widgets y flujos existentes.
- `habits/module_size.py` se valida con sus tests unitarios.

### Ejecución

```bash
.venv/bin/python -m pytest -q
.venv/bin/python -m pytest --cov=habits --cov-report=term-missing -q
```

---

## Riesgos y mitigaciones

| Riesgo | Mitigación |
|--------|------------|
| La migración de imports rompe tests | Refactorizar por fases y ejecutar la suite después de cada una. |
| La división cambia el comportamiento | Mover código sin reescribir lógica; conservar firmas y textos. |
| Aparecen imports circulares | Depender de `domain` → `persistence` → `state` → `ui`, nunca al revés. |
| La guardia cuenta mal docstrings o comentarios | Usar `tokenize` y cubrir los casos límite con tests. |
| Un módulo nuevo vuelve a crecer | El test global falla en la suite normal. |
| Se conserva código muerto | Eliminar las vistas heredadas y verificar que no tienen referencias. |
| Los tests siguen importando rutas antiguas | Un test de arquitectura comprueba que los monolíticos ya no existen. |
