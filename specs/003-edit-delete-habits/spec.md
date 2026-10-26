# Especificación 003 — Edición y eliminación de hábitos

## Contexto y objetivo

La aplicación ya permite crear hábitos, seleccionarlos, consultar sus estadísticas y registrar
el día actual. Sin embargo, una vez creado un hábito no es posible corregir su nombre, su icono
ni su fecha de inicio, y tampoco es posible retirarlo cuando el usuario deja de seguirlo.

Esta actualización completa la gestión del ciclo de vida del hábito: añade la edición de sus
datos y la eliminación permanente con confirmación previa. Al editar se conservan todos los
registros diarios; al eliminar se borran también los registros asociados para no dejar datos
huérfanos.

Además, la fecha de inicio se elige con un calendario desplegable tanto al crear como al editar
un hábito. El calendario evita fechas futuras y sustituye la escritura manual de la fecha.

La actualización **no cambia las reglas de racha, las estadísticas, el heatmap ni el registro
del día actual**. Tampoco introduce minutos, sesiones, archivo de hábitos ni restauración de
elementos eliminados.

## Usuarios

- **Estudiante individual**: persona que sigue sus hábitos de estudio y necesita corregir datos
  mal introducidos o retirar hábitos que ya no forman parte de su rutina.

## Historias de usuario

1. Como estudiante, quiero corregir el nombre, el icono o la fecha de inicio de un hábito para
   mantener su información actualizada sin perder el progreso acumulado.
2. Como estudiante, quiero eliminar un hábito que ya no sigo para que deje de aparecer en mi
   lista y no ensucie mi vista diaria.
3. Como estudiante, quiero confirmar la eliminación antes de que ocurra para evitar borrar un
   hábito por error.
4. Como estudiante, quiero que al eliminar un hábito también desaparezcan sus registros para no
   conservar datos que ya no uso.
5. Como estudiante, quiero seguir viendo un hábito coherente después de editarlo, con su
   progreso y sus estadísticas intactos.
6. Como estudiante, quiero elegir la fecha de inicio en un calendario para no tener que
   recordar el formato ni escribirla a mano.

## Requisitos funcionales

### RF-1 — Acciones de gestión en el detalle

El panel de detalle del hábito seleccionado ofrece las acciones de edición y eliminación.

**Criterios de aceptación (EARS):**

- **RF-1.1** Cuando hay un hábito seleccionado, entonces el panel de detalle muestra las
  acciones “Editar” y “Eliminar”.
- **RF-1.2** Si no hay ningún hábito seleccionado porque la lista está vacía, entonces el panel
  principal muestra el estado vacío y no muestra las acciones “Editar” ni “Eliminar”.
- **RF-1.3** Cuando el usuario pulsa “Editar”, entonces se abre un diálogo modal con los datos
  actuales del hábito seleccionado.
- **RF-1.4** Cuando el usuario pulsa “Eliminar”, entonces se abre un diálogo de confirmación
  antes de borrar nada.
- **RF-1.5** Las acciones de edición y eliminación solo están disponibles desde el panel de
  detalle; la barra lateral no las muestra.
- **RF-1.6** Los textos de las acciones, los diálogos y los mensajes de error están en español.

### RF-2 — Editar un hábito

El usuario puede modificar el nombre, el icono y la fecha de inicio de un hábito existente.

**Criterios de aceptación (EARS):**

- **RF-2.1** Cuando se abre el diálogo de edición, entonces muestra un campo de nombre, un
  campo de fecha de inicio y un selector de icono.
- **RF-2.2** Cuando se abre el diálogo de edición, entonces los tres campos aparecen
  precargados con los valores actuales del hábito y la fecha se muestra en formato dd/mm/aaaa.
- **RF-2.3** Si el usuario intenta guardar con un nombre vacío o formado solo por espacios,
  entonces la aplicación muestra un mensaje de error indicando que el nombre es obligatorio y
  no modifica el hábito.
- **RF-2.4** Si el usuario intenta guardar con un nombre superior a 60 caracteres, entonces la
  aplicación muestra un mensaje de error indicando la longitud máxima y no modifica el hábito.
- **RF-2.5** Cuando el usuario guarda sin modificar la fecha de inicio, entonces la aplicación
  conserva la fecha de inicio actual del hábito.
- **RF-2.6** Cuando el usuario elige otra fecha en el calendario, entonces el campo de fecha
  muestra la nueva fecha en formato dd/mm/aaaa antes de guardar.
- **RF-2.7** Si el usuario intenta seleccionar una fecha futura, entonces el calendario mantiene
  ese día deshabilitado y no permite elegirlo.
- **RF-2.8** Si el usuario no selecciona un icono, entonces la aplicación conserva el icono
  actual del hábito.
- **RF-2.9** Cuando el usuario guarda datos válidos, entonces la aplicación persiste los
  cambios, cierra el diálogo y mantiene seleccionado el mismo hábito.
- **RF-2.10** Cuando el usuario cancela la edición, entonces el diálogo se cierra sin modificar
  ningún dato del hábito.
- **RF-2.11** Si el usuario guarda un nombre que ya usa otro hábito, entonces la aplicación
  permite la edición; no se valida la unicidad de nombres.
- **RF-2.12** Cuando se edita un hábito, entonces todos sus registros diarios se conservan
  íntegros, incluida la fecha de inicio modificada.
- **RF-2.13** Si la edición no se puede guardar por un fallo de persistencia, entonces la
  aplicación muestra un mensaje de error, mantiene el diálogo abierto y no deja cambios
  parciales.
- **RF-2.14** Los cambios guardados en la edición se conservan entre ejecuciones de la
  aplicación.

### RF-3 — Eliminar un hábito

El usuario puede eliminar de forma permanente un hábito y todos sus registros diarios.

**Criterios de aceptación (EARS):**

- **RF-3.1** Cuando se abre el diálogo de confirmación, entonces muestra el nombre del hábito y
  advierte de que la eliminación es permanente e incluye sus registros.
- **RF-3.2** El diálogo de confirmación ofrece las acciones “Cancelar” y “Eliminar”.
- **RF-3.3** Cuando el usuario cancela la eliminación, entonces el diálogo se cierra sin borrar
  el hábito ni sus registros, y la selección actual se mantiene.
- **RF-3.4** Cuando el usuario confirma la eliminación, entonces la aplicación borra el hábito
  y todos sus registros diarios asociados.
- **RF-3.5** Si el usuario pulsa “Eliminar”, entonces la aplicación no borra nada hasta que la
  confirmación se acepta.
- **RF-3.6** Cuando se elimina el hábito seleccionado y quedan otros hábitos, entonces la
  aplicación selecciona el primero de la lista ordenada por racha actual y desempate alfabético.
- **RF-3.7** Cuando se elimina el último hábito existente, entonces la aplicación muestra el
  estado vacío con la opción de crear un hábito.
- **RF-3.8** Si la eliminación no se puede completar por un fallo de persistencia, entonces la
  aplicación muestra un mensaje de error, conserva el hábito y no deja registros parcialmente
  borrados.
- **RF-3.9** Después de una eliminación confirmada, el hábito y sus registros ya no están
  disponibles en la aplicación.

### RF-4 — Actualización coherente de la vista

Los cambios de edición y eliminación se reflejan de inmediato en todas las zonas de la
aplicación, sin reiniciar.

**Criterios de aceptación (EARS):**

- **RF-4.1** Cuando se guarda una edición, entonces la barra lateral actualiza el nombre y el
  icono del hábito y vuelve a ordenar la lista si el desempate alfabético cambió.
- **RF-4.2** Cuando se guarda una edición, entonces el encabezado del panel de detalle muestra
  el nombre, el icono y la fecha de inicio actualizados.
- **RF-4.3** Cuando se guarda una edición, entonces las tarjetas de estadísticas, el heatmap y
  el panel “Registrar hoy” siguen mostrando los mismos valores que antes, porque los registros
  no cambian.
- **RF-4.4** Cuando se guarda una edición, entonces el hábito editado sigue seleccionado aunque
  su posición en la lista cambie.
- **RF-4.5** Cuando se confirma una eliminación, entonces la barra lateral deja de mostrar el
  hábito y el panel de detalle pasa al hábito seleccionado o al estado vacío.
- **RF-4.6** Cuando se elimina el último hábito y después se crea uno nuevo, entonces el nuevo
  hábito se muestra seleccionado y la aplicación vuelve al detalle normal.
- **RF-4.7** Cuando se cancela cualquier diálogo de edición o eliminación, entonces la vista
  permanece exactamente igual que antes de abrirlo.

### RF-5 — Selección de fecha con calendario

Tanto la creación como la edición de un hábito usan un calendario desplegable para elegir la
fecha de inicio. El campo de fecha no admite escritura manual.

**Criterios de aceptación (EARS):**

- **RF-5.1** Cuando se abre el diálogo de creación, entonces el campo de fecha muestra la fecha
  actual en formato dd/mm/aaaa.
- **RF-5.2** Cuando se abre el diálogo de edición, entonces el campo de fecha muestra la fecha
  de inicio actual del hábito en formato dd/mm/aaaa.
- **RF-5.3** Cuando el usuario pulsa el campo de fecha, entonces se despliega un calendario con
  la fecha del campo seleccionada.
- **RF-5.4** Cuando el usuario elige un día y confirma el calendario, entonces el campo muestra
  la fecha elegida en formato dd/mm/aaaa y el diálogo de creación o edición sigue abierto.
- **RF-5.5** Cuando el usuario cancela o cierra el calendario, entonces el campo conserva la
  fecha que tenía antes de abrirlo.
- **RF-5.6** Los días posteriores a hoy aparecen deshabilitados en el calendario y no se pueden
  seleccionar.
- **RF-5.7** El calendario muestra sus textos en español y organiza la semana de lunes a
  domingo.
- **RF-5.8** El campo de fecha no permite escribir manualmente; la fecha solo cambia mediante el
  calendario.
- **RF-5.9** Cuando se crea un hábito sin modificar la fecha, entonces la fecha de inicio es la
  fecha actual.
- **RF-5.10** Cuando se edita un hábito sin modificar la fecha, entonces se conserva su fecha de
  inicio actual.

La creación conserva las validaciones de nombre e icono de la spec 002; esta sección solo
sustituye el campo de texto de fecha por un calendario.

## Requisitos no funcionales

- **RFN-1** Los cambios de edición y las eliminaciones deben persistir en la base de datos local
  y conservarse entre ejecuciones de la aplicación.
- **RFN-2** La interfaz no debe contener cálculos ni acceso directo a los datos; debe delegar en
  la lógica de dominio y persistencia existente.
- **RFN-3** Las nuevas funciones puras y de persistencia deben tener pruebas unitarias y una
  cobertura mínima del 80 %.
- **RFN-4** La actualización no debe introducir dependencias externas distintas de las aprobadas
  por la constitución del proyecto ni requerir conexión a internet.
- **RFN-5** Guardar una edición o confirmar una eliminación debe reflejarse en la interfaz en
  menos de 1 segundo en un equipo de escritorio estándar.
- **RFN-6** El tiempo de inicio de la aplicación debe seguir por debajo de 3 segundos.
- **RFN-7** Las reglas de racha, estadísticas, heatmap, orden de la lista y registro del día
  actual definidas en las specs 001 y 002 no deben cambiar.
- **RFN-8** Todas las fechas visibles para el usuario se muestran en formato dd/mm/aaaa y todos
  los textos visibles están en español.

## Casos límite

| Caso | Comportamiento esperado |
|------|------------------------|
| Se abre la edición y no se cambia nada | Se guardan los mismos valores, el diálogo se cierra y el hábito sigue seleccionado. |
| Se edita con el nombre vacío o solo con espacios | Se muestra error y el diálogo permanece abierto sin modificar el hábito. |
| Se edita con un nombre de más de 60 caracteres | Se muestra error y el diálogo permanece abierto sin modificar el hábito. |
| Se abre el calendario y se cancela | El campo conserva la fecha que tenía antes de abrirlo. |
| Se intenta elegir una fecha futura | El día aparece deshabilitado y no se puede seleccionar. |
| Se intenta escribir la fecha manualmente | El campo no admite escritura; solo cambia con el calendario. |
| Se crea un hábito sin modificar la fecha | La fecha de inicio es la fecha actual. |
| Se edita sin modificar la fecha | Se conserva la fecha de inicio actual del hábito. |
| Se edita sin seleccionar icono | Se conserva el icono actual. |
| Se edita el nombre a uno ya usado por otro hábito | Se permite; no se valida unicidad. |
| Se cambia el nombre y cambia el orden alfabético | La lista se reordena y el hábito editado sigue seleccionado. |
| Se cambia la fecha de inicio a una posterior a algunos registros | Los registros se conservan; las estadísticas y el heatmap no se recalculan por la fecha de inicio. |
| Se pulsa “Eliminar” y luego “Cancelar” | No se borra nada y la selección actual se mantiene. |
| Se elimina un hábito con registros | Se borran el hábito y todos sus registros diarios. |
| Se elimina un hábito y quedan otros | Se selecciona el primero de la lista ordenada. |
| Se elimina el último hábito | Se muestra el estado vacío con “+ Crear hábito”. |
| Se elimina el último hábito y se crea otro | El nuevo hábito queda seleccionado y visible. |
| La edición o la eliminación falla al persistir | Se muestra un error y no se deja ningún cambio parcial. |

## Fuera de alcance

- Deshacer una eliminación o restaurar hábitos borrados.
- Archivar hábitos sin borrarlos.
- Edición o eliminación masiva de hábitos.
- Editar o borrar registros diarios concretos.
- Cambiar la fecha de un registro ya guardado.
- Usar el calendario nativo del sistema operativo; se usa el calendario desplegable de la
  aplicación.
- Escribir la fecha manualmente o elegir fechas futuras.
- Añadir minutos, sesiones o niveles de intensidad.
- Modificar las reglas de racha, las estadísticas o el heatmap.
- Acciones de edición o eliminación desde la barra lateral.
- Historial de cambios o auditoría de ediciones.
- Importación o exportación de datos.
- Recordatorios, notificaciones, cuentas o sincronización en la nube.
- Hábitos con frecuencia distinta a la diaria.
- Temas oscuros o personalización avanzada de la apariencia.

## Criterios de finalización

La funcionalidad se considera completa cuando se cumplen todas las condiciones siguientes:

1. El panel de detalle del hábito seleccionado muestra las acciones “Editar” y “Eliminar”.
2. La edición permite cambiar nombre, icono y fecha de inicio con las validaciones definidas y
   conserva todos los registros diarios.
3. La creación y la edición usan un calendario desplegable para la fecha de inicio, con los días
   futuros deshabilitados, textos en español y formato dd/mm/aaaa.
4. La eliminación exige confirmación y borra el hábito junto con todos sus registros.
5. Tras editar, la barra lateral y el detalle reflejan los cambios y el hábito sigue
   seleccionado.
6. Tras eliminar, se selecciona el siguiente hábito o se muestra el estado vacío si no queda
   ninguno.
7. Los cambios persisten entre ejecuciones y no dejan datos huérfanos.
8. Las reglas de racha, estadísticas, heatmap y registro del día actual siguen funcionando sin
   cambios.
9. Todos los tests unitarios pasan y las nuevas funciones tienen cobertura ≥80 %.

## Dudas abiertas

No hay dudas pendientes. Las decisiones de comportamiento se acordaron con el usuario antes de
redactar esta especificación.
