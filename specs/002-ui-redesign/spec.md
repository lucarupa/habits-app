# Especificación 002 — Rediseño de interfaz con estadísticas

## Contexto y objetivo

La aplicación ya cumple el MVP funcional de la spec 001: crear hábitos, marcarlos como
completados hoy y consultarlos con su racha. Sin embargo, su interfaz actual es básica y no
se parece a los mockups de referencia.

Esta actualización reorganiza la experiencia en una barra lateral persistente con todos los
hábitos y un panel principal de detalle. Además, incorpora estadísticas derivadas de los
registros existentes: racha actual, mejor racha, días registrados y un heatmap binario de
actividad de las últimas cinco semanas.

La actualización **no añade minutos, sesiones ni registro de fechas distintas a hoy**. Conserva
las reglas funcionales del MVP y mejora la forma de presentarlas.

## Usuarios

- **Estudiante individual**: persona que sigue sus hábitos de estudio y quiere ver su progreso
  de forma visual, sin cuentas ni sincronización.

## Historias de usuario

1. Como estudiante, quiero navegar entre mis hábitos desde una barra lateral para cambiar de
   uno a otro rápidamente.
2. Como estudiante, quiero ver un resumen visual de mi progreso para motivarme a mantener la
   constancia.
3. Como estudiante, quiero crear un hábito eligiendo un icono para reconocerlo de un vistazo.
4. Como estudiante, quiero registrar el día actual desde el detalle del hábito para mantener
   mi racha sin salir de esa vista.
5. Como estudiante sin hábitos, quiero ver un estado vacío claro que me invite a crear el
   primero.

## Requisitos funcionales

### RF-1 — Estructura general y navegación

La aplicación presenta una barra lateral con todos los hábitos y un panel principal con el
detalle del hábito seleccionado.

**Criterios de aceptación (EARS):**

- **RF-1.1** Cuando la aplicación se abre y existen hábitos, entonces muestra una barra
  lateral con la lista de hábitos y un panel principal con el detalle del hábito seleccionado.
- **RF-1.2** La barra lateral muestra, para cada hábito, su icono, su nombre y su racha actual.
- **RF-1.3** Los hábitos de la barra lateral se ordenan por racha actual de mayor a menor y,
  si hay empate, alfabéticamente por nombre.
- **RF-1.4** Cuando el usuario selecciona un hábito de la barra lateral, entonces el panel
  principal muestra su detalle y el hábito seleccionado queda resaltado visualmente.
- **RF-1.5** Cuando la aplicación se abre con hábitos existentes, entonces selecciona
  automáticamente el primero de la lista ordenada.
- **RF-1.6** La barra lateral incluye un botón “+ Nuevo” para crear un hábito.
- **RF-1.7** La barra lateral no muestra botones de “Ajustes” ni “Progreso”.

### RF-2 — Crear un hábito

El usuario puede crear un hábito desde un diálogo modal sin abandonar la vista actual.

**Criterios de aceptación (EARS):**

- **RF-2.1** Cuando el usuario pulsa “+ Nuevo” o “+ Crear hábito”, entonces se abre un diálogo
  modal con un campo de nombre, un campo de fecha opcional y un selector de icono.
- **RF-2.2** Si el usuario intenta guardar con un nombre vacío, entonces la aplicación muestra
  un mensaje de error indicando que el nombre es obligatorio y no crea el hábito.
- **RF-2.3** Si el usuario intenta guardar con un nombre superior a 60 caracteres, entonces la
  aplicación muestra un mensaje de error indicando la longitud máxima y no crea el hábito.
- **RF-2.4** Si el usuario no proporciona una fecha de inicio, entonces la aplicación asigna la
  fecha actual.
- **RF-2.5** Si el usuario proporciona una fecha de inicio futura, entonces la aplicación usa
  la fecha actual como fecha de inicio.
- **RF-2.6** Si el usuario no selecciona un icono, entonces la aplicación asigna un icono por
  defecto.
- **RF-2.7** Cuando el hábito se crea correctamente, entonces el diálogo se cierra, el hábito
  aparece en la barra lateral y queda seleccionado en el panel principal.
- **RF-2.8** El icono elegido para un hábito se conserva entre ejecuciones de la aplicación.
- **RF-2.9** Los hábitos creados antes de esta actualización, que no tengan icono, reciben un
  icono por defecto y siguen siendo visibles y utilizables.
- **RF-2.10** Si la fecha introducida no tiene el formato dd/mm/aaaa o no es una fecha válida,
  entonces la aplicación muestra un mensaje de error y no crea el hábito.

### RF-3 — Panel de detalle y estadísticas

El panel principal muestra la información del hábito seleccionado y tres estadísticas
derivadas de sus registros.

**Criterios de aceptación (EARS):**

- **RF-3.1** Cuando hay un hábito seleccionado, entonces el panel principal muestra su icono,
  su nombre, el subtítulo “Hábito de estudio” y su fecha de inicio en formato dd/mm/aaaa.
- **RF-3.2** El panel de detalle muestra una tarjeta “Racha actual” con la racha activa del
  hábito.
- **RF-3.3** El panel de detalle muestra una tarjeta “Mejor racha” con la mayor cantidad de
  días consecutivos registrados en cualquier momento de la historia del hábito.
- **RF-3.4** El panel de detalle muestra una tarjeta “Días registrados” con la cantidad de
  fechas distintas en las que el hábito fue completado.
- **RF-3.5** Si el hábito no tiene ningún registro, entonces las tres tarjetas muestran 0.
- **RF-3.6** Cuando se registra el día actual, entonces las tres tarjetas se actualizan
  inmediatamente, sin reiniciar la aplicación.

**Definiciones de las estadísticas:**

| Estadística | Definición |
|-------------|------------|
| Racha actual | Días consecutivos que terminan hoy. Si el último registro no es hoy, la racha actual es 0. |
| Mejor racha | Mayor cantidad de días consecutivos registrados en toda la historia del hábito. Si no hay registros, es 0. |
| Días registrados | Cantidad de fechas distintas con al menos un registro de completado. No cuenta sesiones ni minutos. |

### RF-4 — Heatmap de actividad

El panel de detalle muestra un mapa visual de la actividad reciente del hábito.

**Criterios de aceptación (EARS):**

- **RF-4.1** El panel de detalle muestra el heatmap “Actividad (últimas 5 semanas)” con una
  cuadrícula de 5 semanas calendario (35 días) que incluye la fecha actual.
- **RF-4.2** El heatmap organiza los días en 7 filas, de lunes a domingo, y 5 columnas, una por
  semana.
- **RF-4.3** Cada día disponible del heatmap se muestra como “completado” o “no completado”;
  no se usan niveles de intensidad ni minutos. Los días posteriores a hoy se muestran como no
  disponibles.
- **RF-4.4** El día actual queda resaltado dentro del heatmap.
- **RF-4.5** El heatmap incluye una leyenda que distingue “No completado” de “Completado”.
- **RF-4.6** Si el hábito no tiene registros en la ventana de 5 semanas, entonces todos los
  días disponibles se muestran como “no completado”.
- **RF-4.7** Cuando se registra el día actual, entonces la celda de hoy y la leyenda se
  actualizan inmediatamente.

### RF-5 — Registrar el día actual

El panel de detalle incluye una acción simplificada para registrar el completado de hoy.

**Criterios de aceptación (EARS):**

- **RF-5.1** El panel de detalle muestra un panel “Registrar hoy” con la fecha actual en
  formato dd/mm/aaaa.
- **RF-5.2** Si el hábito no está completado hoy, entonces el panel muestra un botón “Guardar”
  habilitado.
- **RF-5.3** Cuando el usuario pulsa “Guardar”, entonces la aplicación registra la fecha
  actual, muestra una confirmación y actualiza la barra lateral, las estadísticas y el heatmap.
- **RF-5.4** Si el hábito ya está completado hoy, entonces el panel muestra el mensaje “Ya
  registrado hoy” y no permite crear un registro duplicado.
- **RF-5.5** El panel “Registrar hoy” no permite elegir otra fecha, no solicita minutos y no
  ofrece la opción “Quitar registro”.
- **RF-5.6** La fecha mostrada en el panel corresponde al día actual al abrir o refrescar la
  vista.

### RF-6 — Estado vacío

Cuando no existen hábitos, la aplicación muestra un estado vacío que invita a crear el primero.

**Criterios de aceptación (EARS):**

- **RF-6.1** Si no existen hábitos, entonces la barra lateral muestra el mensaje “No hay
  hábitos aún”.
- **RF-6.2** Si no existen hábitos, entonces el panel principal muestra una ilustración, el
  título “Crea tu primer hábito para empezar tu racha” y un botón “+ Crear hábito”.
- **RF-6.3** Cuando el usuario pulsa “+ Crear hábito” en el estado vacío, entonces se abre el
  mismo diálogo modal de creación.
- **RF-6.4** Cuando se crea el primer hábito, entonces el estado vacío desaparece y se muestra
  el detalle del nuevo hábito.

### RF-7 — Apariencia y consistencia visual

La interfaz debe acercarse a los mockups de referencia y mantener la legibilidad.

**Criterios de aceptación (EARS):**

- **RF-7.1** La interfaz usa un tema claro con fondo crema, superficies claras y acentos
  verdes.
- **RF-7.2** El hábito seleccionado en la barra lateral se distingue por un fondo y un
  indicador lateral visibles.
- **RF-7.3** La ventana principal se abre en un tamaño de escritorio que permite ver la barra
  lateral y el panel de detalle sin desplazamiento horizontal.
- **RF-7.4** Todas las fechas visibles para el usuario se muestran en formato dd/mm/aaaa.
- **RF-7.5** Todos los textos visibles para el usuario están en español.

## Requisitos no funcionales

- **RFN-1** Los hábitos, sus iconos y sus registros de completado deben conservarse entre
  ejecuciones de la aplicación.
- **RFN-2** La actualización debe conservar el cálculo estricto de la racha definido en la
  spec 001 y el orden por racha descendente con desempate alfabético.
- **RFN-3** La interfaz no debe duplicar cálculos de estadísticas ni acceder directamente a los
  datos; debe delegar en la lógica de dominio del proyecto.
- **RFN-4** Las nuevas funciones puras de cálculo de estadísticas deben tener pruebas unitarias
  y una cobertura mínima del 80 %.
- **RFN-5** La aplicación debe seguir funcionando sin conexión a internet.
- **RFN-6** La aplicación debe iniciar en menos de 3 segundos en un equipo de escritorio
  estándar.
- **RFN-7** La actualización no debe introducir dependencias externas distintas de las
  aprobadas por la constitución del proyecto.

## Casos límite

| Caso | Comportamiento esperado |
|------|------------------------|
| No hay hábitos | Se muestra el estado vacío con la barra lateral y el botón de creación. |
| Hábito sin registros | Racha actual, mejor racha y días registrados muestran 0; el heatmap está vacío. |
| Último registro no es hoy | La racha actual es 0, pero la mejor racha y los días registrados conservan su valor. |
| Hábito ya completado hoy | El panel muestra “Ya registrado hoy” y no permite duplicados. |
| Se intenta crear con nombre vacío | Se muestra error y el diálogo permanece abierto. |
| Se intenta crear con nombre de más de 60 caracteres | Se muestra error y el diálogo permanece abierto. |
| Se elige una fecha futura | Se usa la fecha actual como fecha de inicio. |
| Se introduce una fecha con formato inválido o inexistente | Se muestra un error y no se crea el hábito. |
| Se crea un hábito con un nombre duplicado | Se permite; no se valida unicidad de nombres. |
| Se marca hoy un hábito creado ayer que no se marcó ayer | La racha actual pasa a ser 1, porque no hubo continuidad. |
| No se elige icono | Se asigna el icono por defecto. |
| Hábito existente sin icono | Recibe el icono por defecto y sigue funcionando. |
| Varios hábitos con la misma racha | Se ordenan alfabéticamente por nombre. |
| Se crea un hábito | El nuevo hábito aparece seleccionado en la barra lateral y en el detalle. |
| La aplicación se abre con hábitos | Se selecciona el primero de la lista ordenada. |
| Cambia el día con la aplicación abierta | Al refrescar la vista, la fecha de “Registrar hoy” y el estado de completado se actualizan. |

## Fuera de alcance

- Registro de sesiones con minutos.
- Registro de fechas distintas a la fecha actual.
- Opción “Quitar registro” o desmarcar un día ya completado.
- Pantallas de “Ajustes” y “Progreso”.
- Edición o eliminación de hábitos.
- Heatmap con niveles de intensidad basados en minutos o sesiones.
- Estadísticas adicionales como promedios, gráficos o exportación.
- Notificaciones, recordatorios, cuentas o sincronización en la nube.
- Temas oscuros o personalización avanzada de la apariencia.
- Hábitos con frecuencia distinta a la diaria.

## Criterios de finalización

La actualización se considera completa cuando se cumplen todas las condiciones siguientes:

1. La aplicación muestra la barra lateral con hábitos ordenados y el panel de detalle del
   hábito seleccionado.
2. Se puede crear un hábito con nombre, fecha opcional e icono, con las validaciones definidas.
3. Se puede registrar el día actual desde el panel “Registrar hoy” y el estado se actualiza
   inmediatamente.
4. Las tarjetas de racha actual, mejor racha y días registrados muestran valores correctos.
5. El heatmap binario de las últimas cinco semanas refleja los registros del hábito.
6. El estado vacío aparece cuando no hay hábitos y permite crear el primero.
7. Los hábitos existentes y sus registros se conservan; los hábitos sin icono reciben uno por
   defecto.
8. Todos los tests unitarios pasan y las nuevas funciones de cálculo tienen cobertura ≥80 %.

## Dudas abiertas

- **Nombre de la aplicación**: los mockups muestran “Study Tracker”, mientras que la
  aplicación actual se llama “Habits App”. ¿Se mantiene “Habits App” o se adopta “Study
  Tracker”? `[NECESITA ACLARACIÓN]`
- **Conjunto exacto de iconos predefinidos**: se definirá en el plan de implementación; no
  bloquea la spec.
- **Persistencia del hábito seleccionado entre sesiones**: esta spec asume que al abrir la
  aplicación se selecciona el primero de la lista ordenada; no se conserva la selección
  anterior.
