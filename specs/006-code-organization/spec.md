# Especificación 006 — Organización del código y límite de tamaño por módulo

## Contexto y objetivo

El proyecto ha crecido con las specs 001 a 005 y algunos módulos de producción concentran
demasiadas responsabilidades y cientos de líneas. Un archivo grande dificulta localizar código,
revisar cambios, escribir pruebas aisladas y evitar conflictos entre varias personas. El riesgo
aumenta con la llegada de nuevas funcionalidades, como los recordatorios de la spec 005.

Esta funcionalidad establece una regla objetiva y automática: **ningún módulo de producción puede
superar las 250 líneas con contenido**. Para cumplirla, los módulos actuales que superan el
límite se reorganizan por responsabilidad, sin cambiar el comportamiento visible de la
aplicación ni sus datos.

La regla no se aplica a archivos de tests, scripts auxiliares, documentación ni configuración.
La verificación forma parte de la suite de pruebas, de modo que un módulo nuevo que supere el
límite haga fallar la integración continua local antes de mergear.

## Usuarios

- **Desarrollador del proyecto**: necesita módulos pequeños, con una responsabilidad clara, para
  entender y modificar el código sin leer archivos de más de mil líneas.
- **Revisor de cambios**: necesita que la suite detecte automáticamente un módulo demasiado
  grande y que las revisiones se limiten a áreas concretas.
- **Usuario final**: necesita que la reorganización no altere el comportamiento, los datos, los
  textos ni las estadísticas de la aplicación.
- **Nuevo colaborador**: necesita una estructura predecible y documentada para saber dónde
  añadir una funcionalidad sin engordar un módulo existente.

## Historias de usuario

1. Como desarrollador, quiero que cada módulo de producción tenga como máximo 250 líneas con
   contenido, para poder entenderlo y modificarlo en una sola sesión.
2. Como desarrollador, quiero que los módulos se dividan por responsabilidad, para saber dónde
   buscar la lógica de dominio, la persistencia, el estado y cada parte de la interfaz.
3. Como revisor, quiero que un test falle cuando un módulo supere el límite, para no depender de
   una revisión manual.
4. Como revisor, quiero que el test indique la ruta y el conteo de cada archivo infractor, para
   corregirlo sin adivinar.
5. Como usuario, quiero que la reorganización conserve intactos los hábitos, registros, rachas,
   estadísticas, heatmap y mensajes, para seguir usando la aplicación con confianza.
6. Como nuevo colaborador, quiero que la estructura y la regla estén documentadas, para añadir
   código en el módulo correcto desde el primer cambio.

## Requisitos funcionales

### RF-1 — Límite de 250 líneas con contenido por módulo

Todo módulo de producción debe respetar un límite objetivo y verificable.

**Criterios de aceptación (EARS):**

- **RF-1.1** Cuando se cuenta un módulo de producción, entonces su número de líneas con
  contenido no puede superar 250.
- **RF-1.2** Cuando una línea está vacía o contiene solo espacios en blanco, entonces no cuenta
  para el límite.
- **RF-1.3** Cuando una línea es un comentario de línea completa, entonces no cuenta para el
  límite.
- **RF-1.4** Cuando una línea contiene código, una docstring o un comentario al final de una
  instrucción, entonces cuenta como una línea con contenido.
- **RF-1.5** Cuando un módulo tiene exactamente 250 líneas con contenido, entonces cumple el
  límite; cuando tiene 251 o más, entonces lo incumple.
- **RF-1.6** La regla se aplica a todos los módulos del paquete de producción, incluidos los
  archivos de inicialización y los que se añadan en subpaquetes futuros.
- **RF-1.7** La regla no se aplica a archivos de tests, scripts auxiliares, documentación,
  configuración ni datos.
- **RF-1.8** Cuando un módulo de producción se divide, entonces cada módulo resultante también
  respeta el límite.

### RF-2 — Reorganización por responsabilidad

Los módulos que superan el límite se dividen en piezas con una responsabilidad identificable.

**Criterios de aceptación (EARS):**

- **RF-2.1** Cuando un módulo de producción supera el límite, entonces se divide hasta que todos
  sus módulos resultantes cumplan la regla.
- **RF-2.2** Cuando se crea un módulo nuevo, entonces su responsabilidad principal se puede
  describir en una frase y no mezcla lógica de dominio con acceso a datos ni con widgets.
- **RF-2.3** Cuando se reorganiza el código, entonces se conservan las reglas de negocio,
  validaciones, cálculos, mensajes al usuario y orden de las operaciones.
- **RF-2.4** Cuando se reorganiza la interfaz, entonces cada componente visual mantiene su
  comportamiento, textos, callbacks y estado observable.
- **RF-2.5** Cuando se mueve una función o clase, entonces todas las referencias internas y
  pruebas apuntan a su nueva ubicación; no se conserva una fachada de compatibilidad con las
  rutas antiguas.
- **RF-2.6** Cuando se completa la reorganización, entonces no existen dependencias circulares
  entre los módulos resultantes.
- **RF-2.7** Cuando se completa la reorganización, entonces no se duplica lógica, constante ni
  validación para evitar dependencias entre módulos.
- **RF-2.8** Cuando se añade una funcionalidad futura, entonces puede ubicarse en un módulo
  existente o nuevo sin superar el límite.

### RF-3 — Verificación automática del límite

La regla se comprueba en cada ejecución de la suite de pruebas.

**Criterios de aceptación (EARS):**

- **RF-3.1** Cuando se ejecuta la suite, entonces un test recorre todos los módulos de producción
  de forma recursiva.
- **RF-3.2** Cuando el test cuenta líneas, entonces aplica exactamente las mismas reglas de
  contenido, comentarios, docstrings y espacios que RF-1.
- **RF-3.3** Cuando uno o varios módulos superan el límite, entonces el test falla y muestra la
  ruta y el conteo de todos los archivos infractores en un único mensaje.
- **RF-3.4** Cuando todos los módulos cumplen el límite, entonces el test pasa sin emitir
  advertencias.
- **RF-3.5** Cuando existen cachés, entornos virtuales o archivos generados, entonces el test no
  los inspecciona ni los cuenta.
- **RF-3.6** Cuando se añade un módulo nuevo dentro del paquete de producción, entonces el test
  lo detecta sin necesidad de modificar una lista manual de archivos.
- **RF-3.7** Cuando el test se ejecuta desde la raíz del proyecto o mediante pytest, entonces
  localiza el paquete de producción de forma estable.

### RF-4 — Documentación de la regla y de la estructura

La regla y la nueva organización deben quedar documentadas para el equipo.

**Criterios de aceptación (EARS):**

- **RF-4.1** Cuando un desarrollador consulta la documentación, entonces encuentra el límite de
  250 líneas con contenido, la forma de contar y los archivos excluidos.
- **RF-4.2** Cuando un desarrollador consulta la documentación, entonces encuentra una
  descripción de la responsabilidad de cada módulo de producción y de sus subpaquetes.
- **RF-4.3** Cuando se actualiza la documentación, entonces los conteos de pruebas reflejan la
  suite real.
- **RF-4.4** Cuando se completa la funcionalidad, entonces la spec y sus tareas quedan
  actualizadas con el estado final.

### RF-5 — Conservación del comportamiento y la calidad

La reorganización no debe introducir cambios funcionales ni degradar la calidad existente.

**Criterios de aceptación (EARS):**

- **RF-5.1** Cuando se ejecuta la suite existente, entonces todas las pruebas siguen pasando
  después de actualizar las rutas de importación.
- **RF-5.2** Cuando se comparan los datos de una base existente, entonces hábitos, registros,
  días recuperados, rachas, estadísticas y heatmap no cambian.
- **RF-5.3** Cuando se usan las funciones y componentes públicos, entonces sus entradas, salidas,
  textos y efectos observables son los mismos.
- **RF-5.4** Cuando se ejecuta la aplicación, entonces la creación, edición, borrado, registro,
  aviso de duplicado y recuperación de racha siguen funcionando igual.
- **RF-5.5** Cuando se mide la cobertura, entonces los módulos con lógica mantienen al menos el
  80 % exigido por la constitución.
- **RF-5.6** Cuando se completa la reorganización, entonces no se añaden dependencias, servicios
  ni cambios en el esquema de datos.

## Requisitos no funcionales

- **RFN-1** La regla se aplica solo a código de producción; tests y scripts pueden superar el
  límite si su naturaleza lo justifica.
- **RFN-2** La comprobación del límite no realiza llamadas de red ni modifica archivos.
- **RFN-3** La comprobación debe completarse en menos de un segundo en un proyecto de este
  tamaño.
- **RFN-4** Los módulos resultantes mantienen nombres claros, en inglés cuando corresponda, y
  documentación en español según la constitución.
- **RFN-5** La reorganización no añade dependencias externas ni cambia la versión de Python
  soportada.
- **RFN-6** La separación entre interfaz, lógica de dominio y persistencia se conserva en todos
  los módulos resultantes.
- **RFN-7** La suite completa y la cobertura se ejecutan con el intérprete del proyecto y
  permanecen verdes antes de mergear.
- **RFN-8** La documentación pública sigue en español y los mensajes de error del test de tamaño
  también.

## Casos límite

| Caso | Comportamiento esperado |
|------|------------------------|
| Un módulo tiene exactamente 250 líneas con contenido | Cumple el límite. |
| Un módulo tiene 251 líneas con contenido | Incumple y el test falla indicando ruta y conteo. |
| Un archivo contiene solo comentarios y líneas vacías | Cuenta 0 líneas con contenido y cumple. |
| Una línea tiene código y un comentario al final | Cuenta como una línea con contenido. |
| Una docstring ocupa varias líneas | Cada línea de la docstring cuenta como contenido. |
| Un comentario de línea completa tiene sangría | No cuenta. |
| Un archivo de test supera las 250 líneas | No se inspecciona ni genera error. |
| Un script auxiliar supera las 250 líneas | No se inspecciona ni genera error. |
| Se añade un subpaquete de producción | Todos sus módulos se inspeccionan automáticamente. |
| Se añade un archivo vacío al paquete de producción | Cumple con 0 líneas. |
| Un módulo se divide en varios archivos | Todos los resultantes deben cumplir el límite. |
| Hay cachés o entornos virtuales dentro del proyecto | Se ignoran y no se cuentan. |
| Varios módulos incumplen a la vez | El test muestra todos en un único fallo. |
| Un módulo queda con imports sin usar tras la división | Se eliminan antes de dar la tarea por completada. |
| La división produce imports circulares | Se corrige la ubicación de responsabilidades antes de continuar. |
| Un archivo existente ya cumple el límite | No se divide ni se renombra sin necesidad. |

## Fuera de alcance

- Aplicar el límite a archivos de tests, scripts, documentación o configuración.
- Limitar el tamaño de funciones, clases o métodos individuales.
- Añadir reglas de linting, formato, tipos o complejidad ciclomática.
- Cambiar el comportamiento funcional, los textos o los datos de la aplicación.
- Añadir nuevas funcionalidades de usuario.
- Crear una fachada de compatibilidad para imports antiguos.
- Configurar integración continua, hooks de Git o herramientas externas.
- Reorganizar el esquema de SQLite o migrar datos.
- Renombrar hábitos, registros o conceptos del dominio.
- Dividir automáticamente archivos o generar código.

## Criterios de finalización

La funcionalidad se considera completa cuando se cumplen todas las condiciones siguientes:

1. Todos los módulos de producción, incluidos los archivos de inicialización y subpaquetes,
   tienen como máximo 250 líneas con contenido.
2. Los módulos actuales que superaban el límite se han dividido por responsabilidad y no queda
   ninguno fuera de la regla.
3. Todas las referencias e imports internos apuntan a las nuevas ubicaciones, sin fachada de
   compatibilidad.
4. Existe un test automático que recorre el paquete de producción, aplica las reglas de conteo y
   muestra todos los infractores con su ruta y número de líneas.
5. La suite completa pasa con el intérprete del proyecto y la cobertura de los módulos con lógica
   sigue siendo al menos del 80 %.
6. El comportamiento visible, los datos, los textos y las funciones públicas se conservan.
7. La documentación describe el límite, la forma de contar, las exclusiones y la nueva estructura
   de módulos.
8. No se añadieron dependencias ni cambios en el esquema de datos.

## Estado de implementación

Las fases 1 a 8 están completadas: el medidor de tamaño, los paquetes `domain`,
`persistence`, `state`, `forms`, `ui` y `notifications`, las guardias de arquitectura y de
tamaño, y la documentación de la regla y de la estructura. La fase 9 queda pendiente para la
verificación final de la suite y la cobertura.

Decisiones aplicadas durante la implementación:

- `habits/notifications.py` también superaba el límite tras la spec 005, así que se dividió en
  `notifications/models.py`, `common.py`, `notifier.py` y `scheduler.py` (Tarea 7.4).
- No se conservaron fachadas: todos los imports de producción y de tests apuntan al módulo de
  su responsabilidad.
- La guardia global descubre los módulos nuevos de forma recursiva y falla con un único
  mensaje que lista ruta y conteo de todos los infractores.
- La suite queda en 428 pruebas puras + 121 con Flet (549 en `.venv`), y el README documenta
  el límite, la forma de contar, las exclusiones y la estructura final.

## Dudas abiertas

- Ninguna. El alcance, la forma de contar, los archivos afectados, la estrategia de división y la
  verificación automática quedan resueltos en los requisitos anteriores.
