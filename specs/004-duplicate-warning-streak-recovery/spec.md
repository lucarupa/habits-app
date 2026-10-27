# Especificación 004 — Aviso de registro duplicado y recuperación de racha

## Contexto y objetivo

La aplicación ya impide registrar dos veces el mismo hábito en el día actual y muestra el texto
“Ya registrado hoy” en el panel de registro. Sin embargo, si el usuario vuelve a pulsar
“Guardar” no recibe una confirmación visual suficientemente clara de que el día ya estaba
registrado: el intento parece no hacer nada.

Además, cuando el usuario olvida registrar un día, la racha se rompe aunque haya mantenido el
hábito durante semanas. Esta actualización permite recuperar la racha rota cuando el hueco más
reciente es de uno o dos días, marcando esos días como recuperados. Los días recuperados suman
a la racha actual y a la mejor racha, pero no a “Días registrados”, y se distinguen visualmente
en el heatmap.

La funcionalidad **no cambia las reglas de racha de los días normales, las estadísticas, el
orden de la lista ni el registro del día actual**, y **no añade recordatorios automáticos ni
notificaciones del sistema**.

## Usuarios

- **Estudiante individual**: persona que registra sus hábitos de estudio a diario y necesita
  saber con claridad cuándo ya ha completado el registro del día, así como corregir un olvido
  puntual sin perder una racha larga.

## Historias de usuario

1. Como estudiante, quiero recibir un aviso claro al intentar registrar de nuevo un hábito que
   ya completé hoy, para saber que mi registro anterior sigue guardado.
2. Como estudiante, quiero que el aviso mencione el nombre del hábito, para identificar de
   inmediato a cuál se refiere aunque tenga varios en la lista.
3. Como estudiante, quiero que el aviso desaparezca solo y no me obligue a cerrar una ventana,
   para seguir usando la aplicación sin interrupciones.
4. Como estudiante, quiero recuperar una racha rota cuando he olvidado registrar uno o dos días,
   para no perder el progreso que había acumulado.
5. Como estudiante, quiero confirmar la recuperación antes de que se marquen días como
   recuperados, para evitar alterar mi historial por error.
6. Como estudiante, quiero distinguir los días recuperados de los días realmente registrados,
   para saber qué días completé y cuáles recuperé después.
7. Como estudiante, quiero que los días recuperados cuenten para mi racha pero no inflen mi
   contador de “Días registrados”, para mantener estadísticas honestas.

## Requisitos funcionales

### RF-1 — Aviso al pulsar “Guardar” con el día ya registrado

El panel “Registrar hoy” avisa mediante un mensaje emergente no bloqueante cuando el usuario
intenta registrar un hábito que ya está completado en la fecha actual.

**Criterios de aceptación (EARS):**

- **RF-1.1** Cuando el hábito seleccionado ya está registrado hoy y el usuario pulsa “Guardar”,
  entonces la aplicación muestra un aviso emergente no bloqueante en la parte inferior de la
  ventana.
- **RF-1.2** Cuando se muestra el aviso, entonces su texto es
  “⚠️ «<nombre del hábito>» ya está registrado hoy.”, usando el nombre visible del hábito.
- **RF-1.3** Cuando se muestra el aviso, entonces la aplicación no crea un registro nuevo ni
  modifica el registro ya existente.
- **RF-1.4** Cuando el hábito seleccionado no está registrado hoy y el usuario pulsa “Guardar”,
  entonces la aplicación registra el día con el comportamiento actual y no muestra este aviso.
- **RF-1.5** Cuando el usuario vuelve a pulsar “Guardar” sobre un hábito ya registrado hoy,
  entonces el aviso se muestra de nuevo y se siguen sin crear registros duplicados.
- **RF-1.6** El aviso desaparece automáticamente tras unos segundos sin requerir que el usuario
  lo cierre.
- **RF-1.7** Cuando el usuario intenta registrar de nuevo un hábito ya registrado hoy, entonces
  el panel “Registrar hoy” muestra el texto “Ya registrado hoy” además del aviso emergente.
- **RF-1.8** El aviso no bloquea la interacción con la aplicación: el usuario puede cambiar de
  hábito, registrar otro o seguir navegando mientras está visible.
- **RF-1.9** Los textos del aviso están en español y la fecha del panel se sigue mostrando en
  formato dd/mm/aaaa.

### RF-2 — Recuperar una racha rota

El panel “Registrar hoy” ofrece recuperar la racha cuando el hueco más reciente del hábito
seleccionado es de uno o dos días consecutivos sin registro.

**Definición de hueco recuperable:** es el intervalo de uno o dos días consecutivos sin registro
más reciente del hábito. Puede estar situado entre dos días registrados o entre el último día
registrado y la fecha actual. El día de hoy nunca se marca como recuperado: si no está
registrado, se registra con la acción normal. Los días recuperados cuentan como días con
registro para calcular la racha y para localizar huecos posteriores.

**Criterios de aceptación (EARS):**

- **RF-2.1** Cuando el hueco más reciente del hábito seleccionado es de uno o dos días
  consecutivos sin registro, entonces el panel “Registrar hoy” muestra la acción
  “Recuperar racha”.
- **RF-2.2** Si el hueco más reciente es de tres o más días consecutivos sin registro, entonces
  la acción “Recuperar racha” no se muestra.
- **RF-2.3** Si el hábito no tiene ningún registro previo, entonces la acción “Recuperar racha”
  no se muestra.
- **RF-2.4** Cuando el usuario pulsa “Recuperar racha”, entonces se abre un diálogo de
  confirmación que muestra el nombre del hábito y cuántos días se van a recuperar.
- **RF-2.5** El diálogo advierte de que los días quedarán marcados como recuperados y de que
  contarán para la racha, pero no para “Días registrados”.
- **RF-2.6** El diálogo ofrece las acciones “Cancelar” y “Recuperar”.
- **RF-2.7** Cuando el usuario cancela, entonces el diálogo se cierra sin marcar ningún día ni
  modificar la racha.
- **RF-2.8** Cuando el usuario confirma, entonces la aplicación marca como recuperados todos los
  días del hueco recuperable y cierra el diálogo.
- **RF-2.9** Cuando se recupera la racha, entonces la racha actual y la mejor racha incluyen los
  días recuperados.
- **RF-2.10** Cuando se recupera la racha, entonces “Días registrados” no aumenta por los días
  recuperados.
- **RF-2.11** Cuando se recupera la racha, entonces el heatmap muestra los días recuperados con
  un estado visual distinto del completado normal y del no completado, e incluye una etiqueta
  “Recuperado” en su leyenda.
- **RF-2.12** Después de recuperar la racha, el hábito sigue seleccionado, la barra lateral
  actualiza su racha y la acción “Recuperar racha” desaparece para ese hueco.
- **RF-2.13** Cuando el usuario pulse “Guardar” después de recuperar la racha y el día actual
  siga sin registrar, entonces el registro del día actual funciona con normalidad.
- **RF-2.14** Si el día actual ya estaba registrado, entonces el aviso de registro duplicado de
  RF-1 sigue funcionando sin cambios después de recuperar la racha.
- **RF-2.15** Los días recuperados se conservan entre ejecuciones de la aplicación.
- **RF-2.16** Si la recuperación no se puede guardar por un fallo de persistencia, entonces la
  aplicación muestra un mensaje de error y no deja días recuperados parciales.
- **RF-2.17** Si un día del hueco ya tiene un registro normal, entonces no se marca como
  recuperado ni se modifica ese registro.
- **RF-2.18** Solo se ofrece recuperar el hueco más reciente; los huecos anteriores no se
  recuperan en la misma acción.
- **RF-2.19** Los textos del diálogo y de la acción están en español.

### RF-3 — Coherencia de datos y de la vista

La recuperación y el aviso de duplicado son operaciones coherentes con el resto de la
aplicación.

**Criterios de aceptación (EARS):**

- **RF-3.1** Cuando se recupera una racha, entonces la tarjeta de racha actual, la de mejor
  racha y el orden de la barra lateral se actualizan de inmediato.
- **RF-3.2** Cuando se recupera una racha, entonces las estadísticas de “Días registrados” y los
  registros normales del hábito no cambian.
- **RF-3.3** Cuando se recupera una racha, entonces las estadísticas, el heatmap y el orden de
  los demás hábitos no cambian.
- **RF-3.4** Cuando se muestra el aviso de registro duplicado, entonces la racha, las
  estadísticas, el heatmap y el orden de la barra lateral permanecen iguales.
- **RF-3.5** Las reglas de racha de los días registrados normalmente siguen siendo las mismas
  que en las specs anteriores; los días recuperados solo añaden una excepción explícita.
- **RF-3.6** El registro del día actual y el aviso de duplicado no requieren conexión a internet
  ni acceso directo a los datos desde la interfaz.

## Requisitos no funcionales

- **RFN-1** El aviso y la recuperación no deben requerir conexión a internet ni añadir
  dependencias externas distintas de las aprobadas por la constitución del proyecto.
- **RFN-2** La interfaz no debe contener cálculos ni acceso directo a los datos; debe delegar en
  la lógica de dominio y persistencia existente.
- **RFN-3** La nueva lógica debe tener pruebas automatizadas y la cobertura de los módulos con
  lógica debe mantenerse en un mínimo del 80 %.
- **RFN-4** Las reglas de racha de los días normales, las estadísticas, el heatmap, el orden de
  la lista y el registro del día actual definidas en las specs 001, 002 y 003 no deben cambiar,
  salvo por el tratamiento explícito de los días recuperados.
- **RFN-5** El aviso debe aparecer y la recuperación debe reflejarse en la interfaz en menos de
  1 segundo tras la acción del usuario en un equipo de escritorio estándar.
- **RFN-6** El tiempo de inicio de la aplicación debe seguir por debajo de 3 segundos.
- **RFN-7** Todos los textos visibles para el usuario deben estar en español y las fechas deben
  mostrarse en formato dd/mm/aaaa.
- **RFN-8** La recuperación debe ser atómica: o se marcan todos los días del hueco o no se marca
  ninguno.

## Casos límite

| Caso | Comportamiento esperado |
|------|------------------------|
| Se pulsa “Guardar” con el hábito ya registrado hoy | Aparece el aviso con el nombre del hábito y no se crea un registro duplicado. |
| Se pulsa “Guardar” varias veces seguidas sobre un hábito ya registrado | El aviso se muestra de nuevo en cada intento y el registro sigue contando una sola vez. |
| Se registra un hábito que aún no estaba registrado hoy | El registro se crea con normalidad y no aparece el aviso de duplicado. |
| El hueco más reciente es de un día | Se ofrece recuperar la racha y se marca ese día como recuperado. |
| El hueco más reciente es de dos días | Se ofrece recuperar la racha y se marcan ambos días como recuperados. |
| El hueco más reciente es de tres días o más | No se ofrece recuperar la racha. |
| El hábito no tiene ningún registro previo | No se ofrece recuperar la racha. |
| Hoy no está registrado y el hueco anterior es de dos días | Se recuperan los dos días pasados y después se puede registrar hoy con normalidad. |
| Hoy ya está registrado y antes hay un hueco de dos días | Se ofrece recuperar los dos días del hueco sin alterar el registro de hoy. |
| Hay varios huecos y el más reciente es de tres días | No se ofrece recuperar, aunque un hueco anterior fuera de uno o dos días. |
| Se confirma la recuperación | Los días recuperados cuentan para la racha actual y la mejor racha, pero no para “Días registrados”. |
| Se cancela el diálogo de recuperación | No se marca ningún día y la racha permanece igual. |
| Se recupera la racha y se reinicia la aplicación | Los días recuperados siguen marcados y la racha se conserva. |
| La recuperación falla al persistir | Se muestra un error y no queda ningún día recuperado parcialmente. |
| Un día del hueco ya tiene un registro normal | No se modifica ese registro ni se marca como recuperado. |
| El nombre del hábito es largo | El aviso y el diálogo siguen identificando el hábito y no bloquean la aplicación. |
| Se cambia de hábito mientras el aviso está visible | El aviso desaparece solo; la navegación y el nuevo hábito funcionan con normalidad. |
| No hay ningún hábito seleccionado | El panel de registro no está visible y no se muestra ningún aviso ni acción de recuperar. |

## Fuera de alcance

- Recordatorios automáticos o avisos cuando la aplicación está cerrada.
- Notificaciones del sistema operativo.
- Recuperar rachas con huecos de tres o más días.
- Elegir manualmente qué días concretos se recuperan.
- Editar o borrar registros diarios concretos, incluidos los recuperados.
- Cambiar la fecha de un registro ya guardado.
- Deshacer una recuperación o volver un día recuperado a no registrado.
- Historial de recuperaciones o de avisos.
- Avisos por correo, cuentas o sincronización en la nube.
- Añadir minutos, sesiones, niveles de intensidad o hábitos con frecuencia distinta a la diaria.
- Temas oscuros o personalización avanzada de la apariencia.

## Criterios de finalización

La funcionalidad se considera completa cuando se cumplen todas las condiciones siguientes:

1. Al pulsar “Guardar” sobre un hábito ya registrado hoy aparece un aviso emergente no
   bloqueante con su nombre.
2. El aviso no crea registros duplicados ni modifica el registro existente.
3. El registro normal de un hábito no registrado hoy sigue funcionando sin aviso de duplicado.
4. El panel muestra el texto “Ya registrado hoy” al intentar registrar de nuevo un hábito ya
   registrado.
5. La acción “Recuperar racha” aparece solo cuando el hueco más reciente es de uno o dos días.
6. La recuperación pide confirmación, muestra cuántos días se recuperarán y se puede cancelar
   sin cambios.
7. Los días recuperados cuentan para la racha actual y la mejor racha, pero no para
   “Días registrados”.
8. El heatmap distingue los días recuperados con su propia etiqueta.
9. La recuperación persiste entre ejecuciones y es atómica ante fallos.
10. Rachas, estadísticas normales, heatmap y orden de la lista siguen funcionando sin cambios
    fuera del tratamiento de los días recuperados.
11. El aviso desaparece automáticamente y no bloquea la navegación.
12. Todos los tests pasan y la cobertura de los módulos con lógica se mantiene en ≥80 %.
13. No se añaden recordatorios automáticos, notificaciones del sistema ni dependencias nuevas.

## Dudas abiertas

No hay dudas pendientes. Las decisiones de comportamiento se acordaron con el usuario antes de
redactar esta especificación.
