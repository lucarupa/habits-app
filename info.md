Vamos a crear la constitución de un proyecto nuevo: una app de escritorio en Python para 
registrar hábitos de estudio y calcular rachas. Es un proyecto educativo que 
debe poder mantener un desarrollador senior.

Proponme un docs/constitution.md con 6 principios innegociables, cortos y
verificables, que cubran: simplicidad del stack, relación entre spec y código,
separación entre lógica e interfaz, política de tests, persistencia de datos
e idioma del código y los mensajes. Máximo 15 líneas. Espera mi aprobación.


NO escribas código en ningún momento. Vamos a redactar la especificación de la
primera funcionalidad de habits-cli. Lee docs/constitution.md.

Idea inicial: una app de escritorio con tres funciones: crear un hábito, marcarlo como hecho
hoy, y listar los hábitos con su racha de días consecutivos.

Tu trabajo:
1. Hazme preguntas de UNA en UNA para eliminar ambigüedades (casos límite,
   comportamiento con errores, qué queda fuera del MVP). Máximo 6 preguntas.
2. Con mis respuestas, genera specs/001-habits-mvp/spec.md con esta estructura:
   contexto y objetivo, usuarios, historias de usuario, requisitos funcionales
   numerados (RF-x) con criterios de aceptación en notación EARS en español,
   requisitos no funcionales, casos límite, fuera de alcance, criterios de
   finalización y dudas abiertas marcadas como [NECESITA ACLARACIÓN].
3. El QUÉ y el POR QUÉ. Nada de stack, arquitectura ni nombres de archivos:
   eso irá en el plan.


Lee `docs/constitution.md` y `specs/001-habits-mvp/spec.md`. NO escribas código.
Genera specs/001-habits-mvp/plan.md con: estructura de módulos, modelo de datos con un ejemplo,
algoritmo de cálculo de racha en pseudocódigo, decisiones técnicas justificadas (y su alternativa descartada), 
y estrategia de tests. Todo debe respetar la constitución y cubrir todos los RF. Marca qué RF cubre cada parte.


NO escribas código. A partir de spec.md y plan.md, genera specs/001-habits-mvp/tasks.md:
tareas pequeñas (máx. 20-30 min cada una), en orden de dependencia, cada una
con los RF que cubre y una línea "Hecho cuando:" verificable. Usa checkboxes.