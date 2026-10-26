---
name: Commit
description: Crea commits en habits-app siguiendo la convención observada en el historial del repositorio: un commit por fase de spec, asunto en inglés con el marcador `spec<NNN> f<FASE>` y sin cuerpo. Úsala cuando el usuario pida hacer un commit, preparar los cambios para commitear, redactar un mensaje de commit o revisar si el árbol está listo para commitear.
---

# Commit

Skill para preparar y crear commits en este repositorio respetando la convención que ya
usa el proyecto. No inventa un estilo nuevo: replica y hace explícito el patrón del
historial de `habits-app`.

## Cuándo activarse

- El usuario pide "haz commit", "commitea esto" o "prepara el commit".
- El usuario pide redactar o revisar un mensaje de commit.
- Hay que decidir qué archivos entran en un commit tras terminar una tarea o fase.
- El usuario quiere comprobar si la suite está verde antes de commitear.

## Convención observada

El historial real del repositorio es la fuente de verdad:

```text
feature: implement icon column in habits table, spec002 f2
feature: implement calculate_best_streak, spec002 f1
add spec 002
first commit
```

Reglas que se deducen de ese historial:

1. **Un commit por fase de la spec, no por tarea.** Las tareas T1.1–T1.5 se agruparon en
   `spec002 f1`; las tareas T2.1–T2.4 en `spec002 f2`.
2. **Asunto de una sola línea.** Sin cuerpo, sin footer y sin firma.
3. **Prefijo `feature:` para cambios de producto** (código, tests, tasks y README de la fase).
4. **Resumen en inglés, en minúsculas y en imperativo** después de `feature:`.
5. **Marcador de spec al final:** `, spec<NNN> f<FASE>`.
   - `spec<NNN>` sin espacio: `spec002`.
   - `f<FASE>` sin espacio: `f1`, `f2`.
   - La fase es la del bloque "Fase N" de `specs/<NNN>-*/tasks.md`, no el número de tarea.
6. **Commits de documentación** usan `add spec <NNN>` (con espacio y sin prefijo).
7. **Commit inicial** usa `first commit`.
8. **Longitud del asunto:** mantenerlo por debajo de 72 caracteres.
9. **Commit atómico por fase:** código, tests, `tasks.md` (casillas marcadas) y `README.md`
   viajan juntos. No mezclar dos fases ni dos specs en el mismo commit.

### Plantillas de mensaje

| Situación | Plantilla | Ejemplo |
|-----------|-----------|---------|
| Fase de spec completada | `feature: <resumen en inglés>, spec<NNN> f<FASE>` | `feature: implement icon column in habits table, spec002 f2` |
| Nueva spec/plan/tasks | `add spec <NNN>` | `add spec 002` |
| Bootstrap del repo | `first commit` | `first commit` |

Si el usuario pide una excepción (por ejemplo, un hotfix), propone `fix: <resumen>, spec<NNN> f<FASE>`
o `chore: <resumen>` y confirma antes de usarla. No cambies la convención por iniciativa propia.

## Flujo de trabajo

### 1. Inspeccionar el estado

```bash
git status --short
git log -5 --pretty=format:'%h|%ad|%s' --date=short
git diff --stat
git diff
```

- Identifica qué fase de `specs/<NNN>-*/tasks.md` está completa.
- Comprueba que no haya cambios ajenos a esa fase mezclados en el árbol.
- Si hay cambios sin relación, sepáralos o pregunta al usuario antes de commitear.

### 2. Verificar la suite

```bash
pytest -q
```

- **No crear el commit si la suite está roja.** La constitución exige tests antes de merge.
- Si la fase incluye cobertura, ejecuta también:

```bash
pytest --cov=habits --cov-report=term-missing -q
```

### 3. Revisar qué se va a commitear

```bash
git diff --cached --stat
```

- Nunca commitear `data/*.db`, `__pycache__/`, `.venv/`, `.coverage`, `htmlcov/` ni secretos.
  Ya están en `.gitignore`; verifica que no se hayan forzado con `git add -f`.
- Incluye en el mismo commit:
  - Código de producción de la fase.
  - Tests nuevos o modificados.
  - `specs/<NNN>-*/tasks.md` con las casillas `[x]`.
  - `README.md` si cambió el comportamiento, el conteo de tests o la documentación.

### 4. Preparar el commit

Añade archivos explícitamente, no con `git add .`:

```bash
git add habits/ tests/ specs/<NNN>-*/tasks.md README.md
```

Ajusta la lista a los archivos reales de la fase. Revisa una última vez:

```bash
git status --short
```

### 5. Crear el commit

```bash
git commit -m "feature: <resumen en inglés>, spec<NNN> f<FASE>"
```

Ejemplo:

```bash
git commit -m "feature: implement icon column in habits table, spec002 f2"
```

### 6. Verificar el resultado

```bash
git log -1 --stat
git status --short
```

- Confirma que el asunto tiene el formato correcto.
- Confirma que el árbol queda limpio o que solo quedan cambios de la siguiente fase.

## Ejemplos de decisión

### Terminé T2.4 y la fase 2 está completa

- Archivos: `habits/storage.py`, `tests/test_storage.py`, `specs/002-ui-redesign/tasks.md`, `README.md`.
- Mensaje: `feature: implement icon column in habits table, spec002 f2`.
- Un solo commit, aunque haya habido varios turnos de agente.

### Terminé solo T2.3 pero T2.4 sigue pendiente

- No commitear todavía si el usuario trabaja por fases.
- Si el usuario pide commit igualmente, usar el alcance real:
  `feature: return icon from storage queries, spec002 f2` y avisar de que la fase no está cerrada.

### Añadí una spec nueva sin código

- Archivos: `specs/<NNN>-*/spec.md`, `plan.md`, `tasks.md`.
- Mensaje: `add spec <NNN>`.

## Checklist antes de commitear

- [ ] `pytest -q` pasa.
- [ ] El árbol solo contiene cambios de una fase/spec.
- [ ] `tasks.md` tiene marcadas las tareas incluidas.
- [ ] `README.md` refleja los cambios relevantes (funciones, tests, estado).
- [ ] No hay `data/*.db`, cachés, entornos virtuales ni secretos staged.
- [ ] El asunto sigue `feature: <resumen en inglés>, spec<NNN> f<FASE>`.
- [ ] El asunto no supera 72 caracteres.
- [ ] El commit se verificó con `git log -1 --stat`.

## Lo que NO hace esta skill

- No hace `git push` ni crea Pull Requests salvo petición explícita.
- No reescribe historial (`rebase`, `amend`, `reset --hard`) sin confirmación del usuario.
- No cambia la convención de mensajes por iniciativa propia.
