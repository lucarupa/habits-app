# Especificación 001 — MVP de Hábitos

## Contexto y objetivo

El usuario necesita una aplicación de escritorio para registrar hábitos de estudio y visualizar
su progreso mediante rachas de días consecutivos. El objetivo del MVP es ofrecer las tres
acciones esenciales: crear un hábito, marcarlo como completado el día actual y consultar la
lista de hábitos con su racha activa.

La app busca motivar la constancia mostrando de forma inmediata cuántos días seguidos se ha
mantenido cada hábito, sin complicaciones ni configuraciones avanzadas.

## Usuarios

- **Estudiante individual**: persona que desea seguir sus hábitos de estudio personales sin
  necesidad de cuentas, sincronización ni compartición con otros.

## Historias de usuario

1. Como estudiante, quiero crear un hábito con un nombre para poder empezar a seguirlo.
2. Como estudiante, quiero marcar un hábito como completado hoy para registrar mi progreso.
3. Como estudiante, quiero ver la lista de mis hábitos ordenados por racha para motivarme a
   mantener los más largos.

## Requisitos funcionales

### RF-1 — Crear un hábito

El sistema permite al usuario registrar un nuevo hábito identificándolo con un nombre y una
fecha de inicio.

**Criterios de aceptación (EARS):**

- **RF-1.1** Si el usuario proporciona un nombre no vacío, entonces el sistema crea el hábito
  con esa fecha de inicio.
- **RF-1.2** Si el usuario no proporciona una fecha de inicio, entonces el sistema asigna la
  fecha actual como fecha de inicio.
- **RF-1.3** Si el usuario intenta crear un hábito con un nombre vacío, entonces el sistema
  rechaza la operación y muestra un mensaje de error indicando que el nombre es obligatorio.
- **RF-1.4** Si el usuario intenta crear un hábito con un nombre superior a 60 caracteres,
  entonces el sistema rechaza la operación y muestra un mensaje de error indicando la longitud
  máxima permitida.

### RF-2 — Marcar un hábito como completado hoy

El sistema permite al usuario registrar que un hábito se cumplió el día actual.

**Criterios de aceptación (EARS):**

- **RF-2.1** Cuando el usuario marca un hábito como completado, entonces el sistema registra
  la fecha actual como un día cumplido para ese hábito.
- **RF-2.2** Si el usuario intenta marcar un hábito que ya está completado para el día actual,
  entonces el sistema muestra un mensaje indicando que el hábito ya fue registrado hoy.
- **RF-2.3** El sistema no permite marcar un hábito como completado para una fecha distinta a
  la fecha actual.

### RF-3 — Listar hábitos con racha

El sistema muestra todos los hábitos creados junto con su racha de días consecutivos activa.

**Criterios de aceptación (EARS):**

- **RF-3.1** Cuando el usuario solicita la lista de hábitos, entonces el sistema muestra cada
  hábito con su nombre y su racha actual de días consecutivos.
- **RF-3.2** La lista se ordena de mayor a menor según la racha de días consecutivos.
- **RF-3.3** Si dos o más hábitos tienen la misma racha, entonces se ordenan alfabéticamente
  por nombre como criterio secundario.
- **RF-3.4** Si no existen hábitos registrados, entonces el sistema muestra un mensaje
  indicando que no hay hábitos creados.

### RF-4 — Cálculo de racha estricta

El sistema calcula la racha de días consecutivos de un hábito contando hacia atrás desde la
última fecha registrada, siempre que los días sean consecutivos sin interrupciones.

**Criterios de aceptación (EARS):**

- **RF-4.1** Si el último día registrado es hoy, entonces la racha incluye hoy y cuenta hacia
  atrás mientras los días sean consecutivos.
- **RF-4.2** Si el último día registrado no es hoy, entonces la racha activa es cero.
- **RF-4.3** Si un hábito tiene un solo día registrado y es hoy, entonces su racha es uno.
- **RF-4.4** Si faltan días entre registros consecutivos, entonces la racha se detiene en el
  bloque continuo más reciente.

## Requisitos no funcionales

- **RFN-1** La aplicación debe iniciar en menos de 3 segundos en un equipo de escritorio
  estándar.
- **RFN-2** Todos los mensajes dirigidos al usuario deben estar en español.
- **RFN-3** Los datos deben persistir entre ejecuciones de la aplicación sin requerir
  configuración adicional por parte del usuario.
- **RFN-4** La aplicación debe funcionar sin conexión a internet.

## Casos límite

| Caso | Comportamiento esperado |
|------|------------------------|
| Crear hábito con nombre duplicado | El sistema permite crearlo; no se valida unicidad de nombres en el MVP. |
| Marcar hábito creado ayer sin marcar ayer | La racha se reinicia a 1 al marcar hoy, ya que no hubo continuidad. |
| Lista vacía de hábitos | Se muestra un mensaje amigable invitando al usuario a crear su primer hábito. |
| Fecha de inicio en el futuro | El sistema rechaza la fecha y usa la fecha actual como fecha de inicio. |

## Fuera de alcance

- Eliminar o editar hábitos existentes.
- Marcar un hábito como completado para fechas distintas a la actual.
- Sincronización en la nube o cuentas de usuario.
- Notificaciones o recordatorios automáticos.
- Estadísticas adicionales (promedios, gráficos, exportación).
- Hábitos recurrentes con frecuencia distinta a diaria.

## Criterios de finalización

El MVP se considera completo cuando se cumplen todas las condiciones siguientes:

1. El usuario puede crear un hábito con nombre y fecha de inicio.
2. El usuario puede marcar un hábito como completado para el día actual.
3. El usuario puede ver la lista de hábitos ordenada por racha descendente.
4. La racha se calcula correctamente según la regla estricta definida en RF-4.
5. Los datos persisten entre ejecuciones de la aplicación.
6. Todos los tests unitarios pasan con cobertura ≥80 % en la lógica de dominio.

## Dudas abiertas

- Longitud máxima del nombre del hábito: 60 caracteres.
- Formato de fecha en la interfaz: dd/mm/aaaa.
