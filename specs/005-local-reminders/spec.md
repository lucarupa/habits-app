# Especificación 005 — Recordatorios locales por hábito

## Contexto y objetivo

La aplicación permite registrar hábitos de estudio y consultar rachas y estadísticas, pero no
avisa al usuario cuando se acerca el final del día y todavía no ha registrado alguno de sus
hábitos. Quien mantiene varios hábitos puede olvidar uno sin darse cuenta y romper una racha que
había mantenido durante semanas.

Esta funcionalidad añade un recordatorio diario opcional para cada hábito. El usuario elige una
hora local y, si el hábito sigue pendiente en ese momento, recibe una notificación del sistema
operativo. El recordatorio debe funcionar aunque la aplicación esté cerrada en macOS y Windows,
sin depender de que el usuario tenga la ventana abierta.

Los recordatorios no registran el hábito, no modifican la racha ni las estadísticas y no añaden
dependencias de red. Cada hábito puede tener como máximo un recordatorio diario y el usuario
puede cambiarlo o desactivarlo en cualquier momento.

## Usuarios

- **Estudiante con varios hábitos**: persona que mantiene una lista de hábitos y necesita un
  aviso puntual para no olvidar el registro diario de cada uno.
- **Estudiante que ya registró parte de sus hábitos**: persona que quiere recibir avisos
  únicamente de los hábitos que aún tiene pendientes, sin ruido innecesario.

## Historias de usuario

1. Como estudiante, quiero activar un recordatorio diario para un hábito concreto, para que la
   aplicación me avise si todavía no lo he registrado.
2. Como estudiante, quiero elegir la hora de cada recordatorio, para adaptarlo a mi rutina y a
   la de cada hábito.
3. Como estudiante, quiero recibir el aviso aunque tenga la aplicación cerrada, para no depender
   de acordarme de abrirla.
4. Como estudiante, quiero que el aviso mencione el nombre del hábito, para saber de inmediato
   cuál me falta registrar.
5. Como estudiante, quiero que no me avisen de hábitos ya registrados o con el recordatorio
   desactivado, para recibir solo avisos útiles.
6. Como estudiante, quiero poder cambiar la hora o desactivar el recordatorio, para corregir mi
   configuración sin perder el historial del hábito.
7. Como estudiante, quiero que un fallo o una denegación de permisos no rompa la aplicación ni
   duplique avisos, para mantener la confianza en mis datos.

## Requisitos funcionales

### RF-1 — Configurar el recordatorio de un hábito

Cada hábito dispone de una configuración de recordatorio independiente, desactivada por defecto.

**Criterios de aceptación (EARS):**

- **RF-1.1** Cuando el usuario consulta el detalle de un hábito, entonces ve si su recordatorio
  está desactivado o, si está activo, la hora configurada en formato HH:MM.
- **RF-1.2** Cuando el usuario activa el recordatorio de un hábito y elige una hora válida,
  entonces la configuración se guarda y se muestra como activa con esa hora.
- **RF-1.3** Cuando se crea un hábito nuevo, entonces su recordatorio queda desactivado hasta
  que el usuario lo active.
- **RF-1.4** Cuando el usuario cambia la hora de un recordatorio activo, entonces se conserva la
  nueva hora y se descarta la anterior.
- **RF-1.5** Cuando el usuario desactiva un recordatorio, entonces no se envían avisos futuros
  para ese hábito y su estado vuelve a mostrarse como desactivado.
- **RF-1.6** Cuando el usuario introduce una hora vacía, incompleta o fuera del rango
  00:00–23:59, entonces la configuración no cambia y se muestra un mensaje de error en español.
- **RF-1.7** Cuando la aplicación se cierra y se vuelve a abrir, entonces los recordatorios
  activos y sus horas se conservan.
- **RF-1.8** Cuando un hábito existente se actualiza antes de esta funcionalidad, entonces su
  recordatorio queda desactivado por defecto, sin alterar sus registros ni estadísticas.

### RF-2 — Enviar el recordatorio diario

El recordatorio se entrega como una notificación del sistema operativo en la hora local
configurada, siempre que el hábito siga pendiente.

**Criterios de aceptación (EARS):**

- **RF-2.1** Cuando llega la hora local configurada de un hábito con recordatorio activo y el
  hábito no se ha registrado ese día, entonces el sistema operativo muestra una notificación.
- **RF-2.2** Cuando se muestra la notificación, entonces su texto incluye el nombre visible del
  hábito y está en español.
- **RF-2.3** Cuando llega la hora configurada con la aplicación cerrada o en segundo plano,
  entonces la notificación se muestra igualmente en macOS y Windows.
- **RF-2.4** Cuando un hábito ya está registrado antes de su hora de recordatorio, entonces no
  se muestra la notificación de ese hábito ese día.
- **RF-2.5** Cuando el recordatorio de un hábito está desactivado, entonces no se muestra
  ninguna notificación para ese hábito.
- **RF-2.6** Cuando varios hábitos comparten la misma hora, entonces cada hábito pendiente
  genera su propia notificación identificable por nombre.
- **RF-2.7** Cuando ya se mostró la notificación de un hábito en el día local actual, entonces
  no se muestra una segunda notificación para ese hábito ese mismo día, aunque la aplicación se
  reinicie o se repita la comprobación.
- **RF-2.8** Cuando se muestra una notificación, entonces el hábito no se marca como registrado
  y la racha, las estadísticas, el heatmap y el orden de la lista permanecen sin cambios.
- **RF-2.9** Cuando la fecha local del hábito es anterior a su fecha de inicio, entonces no se
  muestra la notificación.
- **RF-2.10** Cuando el equipo está apagado o suspendido a la hora configurada, entonces el
  aviso se entrega en la primera ocasión disponible del mismo día local si el hábito sigue
  pendiente; si el día local ya terminó, no se envía un aviso retroactivo.

### RF-3 — Mantener coherentes los cambios y cancelaciones

Los cambios en el hábito o en su recordatorio deben afectar únicamente a los avisos futuros y no
deben dejar notificaciones obsoletas.

**Criterios de aceptación (EARS):**

- **RF-3.1** Cuando el usuario cambia la hora antes de que llegue el recordatorio de ese día,
  entonces el aviso se rige por la nueva hora.
- **RF-3.2** Cuando el usuario cambia la hora después de que ya se mostró el aviso de ese día,
  entonces no se muestra un segundo aviso ese día y la nueva hora se aplica desde el día
  siguiente.
- **RF-3.3** Cuando el usuario desactiva el recordatorio antes de su hora, entonces el aviso de
  ese día no se muestra.
- **RF-3.4** Cuando el usuario elimina un hábito, entonces se cancelan sus recordatorios futuros
  y no se muestran avisos posteriores.
- **RF-3.5** Cuando el usuario cambia el nombre de un hábito, entonces los avisos futuros usan
  el nombre actualizado.
- **RF-3.6** Cuando el usuario activa un recordatorio cuya hora ya pasó en el día actual,
  entonces no se envía un aviso inmediato y el primer aviso ocurre al día siguiente.
- **RF-3.7** Cuando el usuario registra el hábito después de recibir el aviso, entonces no se
  envían avisos adicionales ese día ni se altera el registro realizado.

### RF-4 — Gestionar permisos y fallos del sistema

La aplicación debe explicar los problemas de permisos o programación sin perder la
configuración existente ni bloquear el resto de funciones.

**Criterios de aceptación (EARS):**

- **RF-4.1** Cuando el usuario activa por primera vez un recordatorio y el sistema operativo
  solicita permiso, entonces la aplicación espera la respuesta antes de confirmar la activación.
- **RF-4.2** Si el usuario deniega el permiso de notificaciones, entonces el recordatorio no
  queda activo y se muestra un mensaje en español que explica cómo habilitarlo.
- **RF-4.3** Si el sistema operativo revoca el permiso con un recordatorio ya activo, entonces no
  se muestran avisos, la aplicación sigue funcionando y el estado del permiso se comunica en
  español.
- **RF-4.4** Si la programación del recordatorio falla en el sistema operativo, entonces la
  configuración anterior se conserva, se muestra un aviso en español y la aplicación no se
  cierra ni pierde datos.
- **RF-4.5** Si la comprobación de hábitos pendientes falla, entonces no se envía una
  notificación con datos incompletos ni se duplican avisos ya realizados.

## Requisitos no funcionales

- **RFN-1** Todos los textos visibles y las notificaciones están en español; las horas se
  muestran en formato HH:MM y las fechas en dd/mm/aaaa.
- **RFN-2** Los recordatorios funcionan sin conexión a internet y no envían datos a servicios
  externos.
- **RFN-3** La configuración de recordatorios se conserva entre ejecuciones y no altera los
  hábitos, registros, rachas ni estadísticas existentes.
- **RFN-4** La entrega de una notificación no debe retrasar ni bloquear la interfaz; configurar
  o desactivar un recordatorio debe reflejarse de inmediato.
- **RFN-5** El sistema admite macOS y Windows. Linux y otros sistemas quedan fuera de esta
  versión.
- **RFN-6** Un permiso denegado, una notificación no entregada o un fallo del sistema no deben
  impedir registrar hábitos, consultar estadísticas ni usar el resto de la aplicación.
- **RFN-7** Las comprobaciones de recordatorios son idempotentes: repetir una comprobación no
  genera avisos duplicados ni cambios en los datos.
- **RFN-8** La funcionalidad incluye pruebas automatizadas y mantiene la cobertura exigida por la
  constitución del proyecto.

## Casos límite

| Caso | Comportamiento esperado |
|------|------------------------|
| Dos hábitos tienen la misma hora | Se muestran dos notificaciones independientes, una por hábito pendiente. |
| El hábito se registra antes de la hora | No se muestra la notificación de ese hábito ese día. |
| El hábito se registra después del aviso | No se envían más avisos ese día; el registro y la racha se actualizan con normalidad. |
| Se desactiva el recordatorio antes de la hora | No se muestra el aviso de ese día. |
| Se cambia la hora después del aviso | No se repite el aviso ese día; la nueva hora se aplica al día siguiente. |
| Se elimina el hábito | Se cancelan sus avisos futuros y no queda ninguna notificación pendiente. |
| Se renombra el hábito | El siguiente aviso usa el nombre nuevo. |
| Se activa un recordatorio con la hora ya pasada | No hay aviso inmediato; el primero se envía al día siguiente. |
| La aplicación está cerrada a la hora del aviso | El sistema operativo entrega la notificación en macOS y Windows. |
| El equipo está apagado o suspendido a la hora | Se intenta entregar ese mismo día local si el hábito sigue pendiente; nunca después de terminar el día. |
| El permiso de notificaciones está denegado | El recordatorio no se activa y se explica cómo habilitar el permiso. |
| Se revoca el permiso con recordatorios activos | No se envían avisos; la app sigue operativa y comunica el problema. |
| Cambia la zona horaria o el reloj | El siguiente aviso usa la hora local vigente y se mantiene el límite de uno por hábito y día local. |
| El hábito se creó hoy después de su hora de recordatorio | No se envía aviso inmediato; el primero ocurre al día siguiente si sigue pendiente. |
| Todos los hábitos ya están registrados | No se muestra ninguna notificación. |

## Fuera de alcance

- Recordatorios con varios horarios por hábito o repetición por intervalos.
- Programación por días concretos de la semana o calendarios personalizados.
- Avisos por correo, SMS, push remoto o cualquier servicio de red.
- Posponer, silenciar temporalmente o agrupar notificaciones desde la aplicación.
- Acciones dentro de la notificación, como registrar el hábito directamente.
- Recordatorios de días pasados no registrados.
- Recordatorios para hábitos archivados, porque la aplicación no tiene archivado.
- Soporte para Linux u otros sistemas operativos.
- Cambiar las reglas de racha, las estadísticas, el heatmap o el registro del día actual.

## Criterios de finalización

La funcionalidad se considera completa cuando se cumplen todas las condiciones siguientes:

1. Cada hábito permite activar, cambiar y desactivar un recordatorio diario con una hora local
   válida, y la configuración persiste entre ejecuciones.
2. Un hábito pendiente con recordatorio activo genera una única notificación del sistema al día
   en su hora local, incluso con la aplicación cerrada en macOS y Windows.
3. Los hábitos ya registrados, desactivados o inexistentes no generan notificaciones; los avisos
   usan el nombre actualizado y respetan la fecha de inicio.
4. Los cambios de hora, las cancelaciones y los reinicios no producen avisos duplicados ni
   avisos retroactivos después de terminar el día local.
5. La denegación o revocación de permisos y los fallos de programación se comunican en español
   sin romper la aplicación ni perder la configuración anterior.
6. Los recordatorios no modifican registros, rachas, estadísticas, heatmap ni orden de la lista.
7. La documentación pública describe la configuración, el funcionamiento y los límites de los
   recordatorios.
8. La suite de pruebas pasa y la cobertura de los módulos con lógica alcanza al menos el 80 %.

## Dudas abiertas

- Ninguna. Las decisiones de comportamiento pendientes quedan resueltas en los requisitos y los
  casos límite anteriores.
