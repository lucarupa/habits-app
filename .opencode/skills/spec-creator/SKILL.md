---
name: Spec Creator
description: Crea especificaciones funcionales (spec.md), planes técnicos (plan.md) y listas de tareas (tasks.md) para nuevas funcionalidades spec-driven. Úsala cuando el usuario pida crear una spec, un plan o tasks, o seguir el flujo spec-driven del proyecto.
---

# Spec Creator

Skill adaptada para OpenCode. Su ID es `spec-creator` y las plantillas viven en el directorio `templates/` de esta misma skill.

## Cuándo activarse

- El usuario pide crear una especificación para una nueva funcionalidad.
- El usuario menciona "spec", "plan" o "tasks" en el contexto de una nueva historia de usuario.
- El usuario quiere seguir el proceso spec-driven del proyecto.

## Principios clave

- **NO escribir código**: esta skill produce solo documentación (`spec.md`, `plan.md`, `tasks.md`).
- **Lectura obligatoria de la constitución**: antes de cualquier acción, lee `docs/constitution.md` y respeta sus 6 principios.
- **Preguntas una por una**: haz como máximo 6 preguntas de clarificación y espera la respuesta del usuario antes de continuar. Usa la herramienta de preguntas de OpenCode (`question`).
- **El QUÉ y el POR QUÉ**: la spec describe el comportamiento, no la implementación técnica.
- **EARS para criterios**: usa notación EARS (Easy Approach to Requirements Syntax) en español para todos los criterios de aceptación.
- **Sin código en spec/plan**: prohibido incluir stack, arquitectura o nombres de archivos en `spec.md`; `plan.md` sí incluye decisiones técnicas, pero sin código.
- **Consistencia**: revisa las specs existentes antes de crear una nueva y mantén la numeración de RF y tareas.

## Flujo de trabajo

El proceso tiene 3 fases secuenciales. No saltes fases.

### Fase 1: Clarificación (preguntas al usuario)

1. Lee `docs/constitution.md` para entender los principios del proyecto.
2. Si existe una spec anterior en `specs/`, revísala para mantener consistencia.
3. Formula preguntas de clarificación **una por una** al usuario, cubriendo:
   - Comportamiento con casos límite.
   - Reglas de validación.
   - Qué queda fuera del alcance.
   - Preferencias de interfaz o formato.
   - Dependencias con funcionalidades existentes.
4. Máximo 6 preguntas. Anota las respuestas para usarlas en la spec.
5. Marca las dudas que el usuario no pueda resolver ahora como `[NECESITA ACLARACIÓN]`.

### Fase 2: Generar `spec.md`

Crea `specs/<numero>-<slug>/spec.md` siguiendo la plantilla `templates/spec-template.md`.

Estructura obligatoria:

1. Contexto y objetivo.
2. Usuarios.
3. Historias de usuario.
4. Requisitos funcionales numerados (RF-x) con criterios EARS.
5. Requisitos no funcionales.
6. Casos límite (tabla).
7. Fuera de alcance.
8. Criterios de finalización.
9. Dudas abiertas (si aplica).

Reglas:

- Cada RF tiene criterios de aceptación en notación EARS: "Si/Cuando [condición], entonces [resultado]".
- Los criterios son verificables: se puede escribir un test para cada uno.
- El QUÉ y el POR QUÉ, nunca el CÓMO técnico.
- No incluyas nombres de archivos, clases ni librerías en `spec.md`.

### Fase 3: Generar `plan.md` y `tasks.md`

Una vez el usuario aprueba `spec.md`:

1. Crea `specs/<numero>-<slug>/plan.md` siguiendo `templates/plan-template.md`:
   - Estructura de módulos.
   - Modelo de datos con ejemplo.
   - Algoritmos clave en pseudocódigo.
   - Decisiones técnicas justificadas, incluyendo la alternativa descartada.
   - Estrategia de tests.
2. Crea `specs/<numero>-<slug>/tasks.md` siguiendo `templates/tasks-template.md`:
   - Tareas pequeñas (máximo 20–30 minutos cada una).
   - Ordenadas por dependencia.
   - Cada tarea con los RF que cubre.
   - Criterio "Hecho cuando:" verificable.
   - Checkboxes para tracking.

## Patrones de uso

### Crear una spec desde cero

Usuario: "Crea la spec para agregar recordatorios a los hábitos".

Agente:

1. Activa esta skill.
2. Lee `docs/constitution.md`.
3. Revisa las specs existentes para mantener consistencia.
4. Hace las preguntas de clarificación una por una.
5. Genera `spec.md` con las respuestas.
6. Espera la aprobación del usuario.
7. Genera `plan.md` y `tasks.md`.

### Actualizar una spec existente

Usuario: "Agrega un nuevo RF a la spec 001".

Agente:

1. Lee la spec actual.
2. Formula preguntas solo sobre el nuevo RF.
3. Actualiza `spec.md` manteniendo la numeración.
4. Actualiza `plan.md` y `tasks.md` si es necesario.

## Recursos de la skill

- `templates/spec-template.md`: plantilla de especificación funcional.
- `templates/plan-template.md`: plantilla de plan de implementación.
- `templates/tasks-template.md`: plantilla de lista de tareas.
- `specs/001-habits-mvp/`: ejemplo completo de spec, plan y tasks.

Las rutas de `templates/` son relativas al directorio que contiene este `SKILL.md`.

## Reglas de validación

Antes de entregar cada archivo, verifica:

- [ ] `spec.md` no contiene código ni nombres de archivos.
- [ ] Todos los RF tienen criterios EARS en español.
- [ ] Los casos límite cubren los escenarios edge-case mencionados en las preguntas.
- [ ] `plan.md` enlaza cada sección con los RF que cubre.
- [ ] `tasks.md` tiene tareas de máximo 20–30 minutos.
- [ ] Cada tarea tiene un criterio "Hecho cuando:" verificable.
- [ ] No hay duplicación de RF entre tareas.

## Dudas abiertas

Si el usuario no puede aclarar algo ahora, márcalo como `[NECESITA ACLARACIÓN]` en la sección "Dudas abiertas" de `spec.md` y continúa con el resto. No bloquees el proceso.
