---
sessionId: session-261026-114129-1qlx
---

# Constitución del Proyecto

### `docs/constitution.md` — 6 principios innegociables

```markdown
# Constitución del Proyecto – Habits App

1. **Stack mínimo**: Python 3.10+ estándar + una única librería GUI (`customtkinter`). Cero frameworks web, cero contenedores.
2. **Spec-driven**: cada historia de usuario tiene un archivo `specs/\<slug\>.md`; el código que la cumple enlaza con un comentario `# spec: \<slug\>`.
3. **Separación UI/lógica**: la capa de interfaz nunca contiene cálculos ni acceso a datos; la lógica nunca importa widgets.
4. **Tests obligatorios**: toda función pura y cada método de dominio lleva un test unitario (`pytest`) con ≥80 % de cobertura antes de merge.
5. **Persistencia local**: datos en un solo archivo JSON (`data/habits.json`); sin base de datos externa ni conexión de red.
6. **Idioma**: código, comentarios y mensajes al usuario en español; documentación pública en español; nombres de variables en inglés cuando sea estándar.
```

*15 líneas exactas. Listo para tu aprobación.*

# Delivery Steps

### ✓ Step 1: Crear docs/constitution.md
Se creará el archivo `docs/constitution.md` en la raíz del proyecto con los 6 principios innegociables aprobados por el usuario.