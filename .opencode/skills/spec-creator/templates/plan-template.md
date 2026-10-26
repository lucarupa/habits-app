# Plan de Implementación — <NUMERO> <TITULO>

## Estructura de módulos

```
habits/
├── core.py          # Lógica de dominio: modelos y cálculos puros
├── storage.py       # Persistencia SQLite: CRUD
└── app.py           # Interfaz Flet: vistas y navegación
tests/
├── test_core.py     # Tests de lógica de dominio
└── test_storage.py  # Tests de capa de persistencia
data/
└── habits.db        # Base de datos SQLite
```

- **`habits/core.py`** — Cubre [lista de RF]. Contiene las clases de dominio y las funciones puras.
- **`habits/storage.py`** — Cubre [lista de RF]. Encapsula todo el acceso a SQLite.
- **`habits/app.py`** — Cubre [lista de RF]. Orquesta la interfaz Flet delegando a `core` y `storage`.

---

## Modelo de datos

### Tabla `[nombre]` (nueva o modificada)

| Columna | Tipo | Restricción | Descripción |
|---------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Identificador único |
| `[col1]` | [TIPO] | [RESTRICCION] | [Descripcion] |
| `[col2]` | [TIPO] | [RESTRICCION] | [Descripcion] |

### Ejemplo de datos

```
[tabla]:
| id | [col1] | [col2] |
|----|--------|--------|
| 1  | ...    | ...    |
```

[Explica brevemente el ejemplo y cómo se relaciona con los RF.]

---

## Algoritmos clave (pseudocódigo)

### [Nombre del algoritmo] (RF-X)

```
funcion nombre_algoritmo(parametros):
    # Paso 1: [descripcion]
    variable = operacion()

    si condicion:
        retornar resultado

    # Paso 2: [descripcion]
    para cada elemento en coleccion:
        si cumple_condicion(elemento):
            acumular(elemento)
        sino:
            romper_ciclo

    retornar resultado_final
```

**Casos cubiertos:**
- RF-X.1: [Descripcion del caso.]
- RF-X.2: [Descripcion del caso.]

---

## Decisiones técnicas

### 1. [Nombre de la decisión]

**Decisión:** [Que se eligió.]

**Alternativa descartada:** [Que se consideró pero no se eligió.]

**Justificación:** [Por qué se eligió esta opción, referenciando RF o principios de la constitución.]

### 2. [Nombre de la decisión]

**Decisión:** [Que se eligió.]

**Alternativa descartada:** [Que se consideró pero no se eligió.]

**Justificación:** [Por qué se eligió esta opción.]

---

## Estrategia de tests

### Tests de `habits/core.py` (test_core.py)

| Prueba | RF cubierto | Descripción |
|--------|-------------|-------------|
| `test_[nombre]` | RF-X.Y | [Que verifica la prueba.] |

### Tests de `habits/storage.py` (test_storage.py)

| Prueba | RF cubierto | Descripción |
|--------|-------------|-------------|
| `test_[nombre]` | RF-X | [Que verifica la prueba.] |

### Cobertura objetivo

- ≥80 % en `habits/core.py` (funciones puras y métodos de dominio).
- ≥80 % en `habits/storage.py` (capa de persistencia).
- `habits/app.py` se valida mediante verificación manual.

### Ejecución

```bash
pytest -q --cov=habits --cov-report=term-missing
```
