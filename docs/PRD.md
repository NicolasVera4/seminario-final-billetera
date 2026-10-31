# PRD — Qash

Extraído del Entregable 3 del TFG ("Asistente basado en modelos de lenguaje para la gestión y el asesoramiento de finanzas personales"). Ante cualquier duda, el documento completo está en `docs/entregable3.pdf`.

## Objetivo del prototipo
Prototipo de asistente web que registre, valide y categorice los movimientos financieros personales cargados en lenguaje natural, para ofrecer al usuario un seguimiento de sus gastos con alertas, proyecciones y asesoramiento financiero basado en su propio historial.

**Límites:** desde el registro del usuario en el sistema hasta la obtención de alertas y asesoramiento basado en sus movimientos.

## Alcances
1. Gestión de usuarios: registro e inicio de sesión.
2. Registro de movimientos: texto, voz, imagen, PDF o extracto CSV/Excel, con interpretación, validación, categorización y confirmación.
3. Control de gastos: historial con filtros, informes de flujo mensual y gasto por categoría, alertas de desvío.
4. Proyección de gastos: estimación del gasto de los meses siguientes y detección de meses atípicos.
5. Asesoramiento financiero: consultas respondidas con el historial del usuario y documentación de referencia (RAG).

## Perfiles
- **Usuario:** registra, confirma o corrige sus movimientos, consulta historial, informes y alertas, pide asesoramiento. Solo ve lo propio.
- **Administrador:** edita perfiles, desbloquea y da de baja cuentas, carga/reemplaza/elimina la documentación de referencia del RAG. **No accede** a movimientos ni conversaciones de usuarios.

## Product backlog

| ID | Historia | Prioridad | Puntos | Depende de |
|---|---|---|---|---|
| HU-01 | Registrarse en el sistema | Alta | 5 | — |
| HU-02 | Iniciar sesión | Alta | 3 | HU-01 |
| HU-03 | Registrar un movimiento en lenguaje natural | Alta | 8 | HU-02 |
| HU-04 | Validar y confirmar un movimiento interpretado | Alta | 8 | HU-03 |
| HU-05 | Cargar un comprobante o factura por imagen o PDF | Alta | 8 | HU-04 |
| HU-06 | Cargar el resumen de tarjeta en PDF | Alta | 13 | HU-04 |
| HU-07 | Consultar el historial de movimientos | Alta | 5 | HU-04 |
| HU-08 | Consultar el dashboard financiero | Alta | 5 | HU-04 |
| HU-09 | Recibir alertas de desvío de gasto por categoría | Alta | 8 | HU-08 |
| HU-10 | Recibir asesoramiento financiero | Alta | 13 | HU-04 |
| HU-11 | Registrar un movimiento por voz | Media | 3 | HU-03 |
| HU-12 | Consultar la proyección de gasto | Media | 8 | HU-08 |
| HU-13 | Detectar meses con gasto anómalo | Media | 8 | HU-08 |
| HU-14 | Importar un extracto en CSV o Excel | Baja | 8 | HU-04 |

## Historias y criterios de aceptación

### HU-01 — Registrarse en el sistema
Como usuario, quiero crear una cuenta con mi correo y una contraseña para que mis movimientos queden guardados y solo yo pueda verlos.
- **CA1** Correo ya registrado → aviso de error.
- **CA2** Contraseña de menos de 8 caracteres → se indica la restricción.
- **CA3** Campo obligatorio vacío → se señala qué campos faltan.
- **CA4** Datos válidos → se crea la cuenta y se dirige al inicio de sesión.

### HU-02 — Iniciar sesión
Como usuario registrado, quiero ingresar con mi correo y contraseña para acceder a mi información financiera.
- **CA1** Correo o contraseña incorrectos → mensaje de error sin indicar cuál de los dos falló.
- **CA2** Datos correctos → accede a la pantalla principal.
- **CA3** Con sesión iniciada, en cualquier sección solo ve los movimientos que él registró.
- **CA4** Sesión vencida → al intentar una acción se le pide volver a iniciar sesión.

### HU-03 — Registrar un movimiento en lenguaje natural
Como usuario, quiero escribir un gasto o un ingreso como lo diría en una conversación para registrarlo sin completar un formulario.
- **CA1** "gasté 15000 en el súper con débito" → se identifican monto, fecha, tipo, medio de pago, descripción y categoría, y se muestran para confirmar.
- **CA2** Mensaje sin fecha → se toma la fecha del día.
- **CA3** Mensaje sin monto → el asistente pide el monto antes de continuar.
- **CA4** Mensaje que no describe un movimiento (p. ej. una pregunta) → no se registra nada y se responde como consulta.

### HU-04 — Validar y confirmar un movimiento interpretado
Como usuario, quiero revisar los datos interpretados antes de que se guarden para corregir errores de interpretación o de categoría.
- **CA1** Monto ≤ 0 o fecha posterior a hoy → no se permite guardar y se señala el dato inválido.
- **CA2** Categoría propuesta fuera del catálogo → se marca para que el usuario elija una del catálogo.
- **CA3** Movimiento sin medio de pago → el usuario debe seleccionarlo antes de guardar.
- **CA4** Misma fecha, monto y descripción que uno ya registrado → aviso de posible duplicado y se pide confirmación.
- **CA5** Movimiento válido confirmado (con o sin correcciones) → se guarda en su historial.

### HU-05 — Cargar un comprobante o factura por imagen o PDF
Como usuario, quiero subir la foto o el PDF de un comprobante o factura de servicio para registrar el pago sin tipearlo.
- **CA1** Imagen o PDF de ticket/factura → se extrae el texto y se interpreta como **un único** movimiento, que se muestra para confirmar.
- **CA2** PDF escaneado sin texto seleccionable → se aplica OCR.
- **CA3** Archivo que no es imagen ni PDF → se rechaza y se informan los formatos admitidos.
- **CA4** Archivo del que no se puede leer un monto → aviso, no se registra nada y se sugiere cargarlo por texto.

### HU-06 — Cargar el resumen de tarjeta en PDF
Como usuario, quiero subir el PDF del resumen de mi tarjeta para registrar todos los consumos del período de una vez.
- **CA1** PDF reconocido como resumen de tarjeta → cada consumo se identifica como movimiento separado.
- **CA2** Resumen de varias páginas → se leen todas.
- **CA3** Consumo en cuotas → se registra el monto de la cuota del período.
- **CA4** Los movimientos extraídos se pueden confirmar, corregir o descartar uno por uno antes de guardar.
- **CA5** Consumo ya registrado por otro canal → aparece señalado como posible duplicado.

### HU-07 — Consultar el historial de movimientos
Como usuario, quiero ver todos mis movimientos en una lista y filtrarla para encontrar rápido un gasto puntual.
- **CA1** Al abrir: movimientos del más reciente al más antiguo, con fecha, descripción, categoría, medio de pago y monto.
- **CA2** Filtro por rango de fechas, categoría, tipo o medio de pago → solo los que cumplen.
- **CA3** Búsqueda por texto o monto → coincidencias en descripción o monto.
- **CA4** Filtro sin resultados → se informa que no hay movimientos para esos criterios.

### HU-08 — Consultar el dashboard financiero
Como usuario, quiero ver un resumen gráfico de mis finanzas para entender en qué se va mi dinero cada mes.
- **CA1** Total de ingresos, egresos y saldo del mes.
- **CA2** Con varios meses: gráfico de evolución mensual de ingresos y egresos.
- **CA3** Distribución del gasto del mes por categoría.
- **CA4** Sin movimientos: se indica que no hay datos y cómo empezar a cargarlos.

### HU-09 — Recibir alertas de desvío de gasto por categoría
Como usuario, quiero un aviso cuando el gasto de una categoría se dispara para corregirlo antes de fin de mes.
- **CA1** Gasto acumulado del mes en una categoría > 30 % sobre el promedio de esa categoría en los tres meses anteriores → alerta en el dashboard.
- **CA2** Categoría con menos de tres meses de historial → no se genera alerta.
- **CA3** La alerta indica categoría, gasto actual y promedio de referencia.
- **CA4** Al guardar un movimiento confirmado, las alertas se recalculan.

### HU-10 — Recibir asesoramiento financiero
Como usuario, quiero hacerle preguntas sobre mis finanzas a un asistente para obtener recomendaciones basadas en mis propios movimientos.
- **CA1** Pregunta sobre sus gastos ("¿cuánto gasté en comida en agosto?") → responde con datos de su historial.
- **CA2** Consulta de asesoramiento ("¿cómo puedo ahorrar más?") → combina sus movimientos con la documentación precargada.
- **CA3** Si usa la documentación, indica de qué documento proviene.
- **CA4** Usuario sin movimientos → responde solo con la documentación y aclara que no tiene datos propios para personalizar.
- **CA5** Al volver a ingresar puede retomar una conversación anterior.

### HU-11 — Registrar un movimiento por voz
Como usuario, quiero dictar un gasto o ingreso cuando no me resulta cómodo escribir.
- **CA1** Audio grabado desde la aplicación → se transcribe a texto.
- **CA2** El texto aparece en el campo de mensaje y se puede editar antes de enviar.
- **CA3** Enviado, sigue el mismo flujo que un movimiento escrito.
- **CA4** Audio que no se puede transcribir → aviso y sugerencia de repetirlo o escribirlo.

### HU-12 — Consultar la proyección de gasto
Como usuario, quiero ver una estimación de cuánto voy a gastar el mes próximo para planificar mi presupuesto.
- **CA1** Historial ≥ 3 meses → se ve el gasto proyectado del mes siguiente.
- **CA2** Historial < 3 meses → se informa que no hay datos suficientes.
- **CA3** La proyección aparece junto a los meses reales en el gráfico, diferenciada visualmente.

### HU-13 — Detectar meses con gasto anómalo
Como usuario, quiero que se marquen los meses en que gasté fuera de lo habitual para revisar qué pasó.
- **CA1** Historial ≥ 4 meses → se marcan los meses cuyo gasto se aparta del comportamiento habitual.
- **CA2** Historial < 4 meses → se informa que no hay datos suficientes.
- **CA3** El mes anómalo aparece resaltado en el gráfico de evolución con su monto.

### HU-14 — Importar un extracto en CSV o Excel
Como usuario, quiero importar el extracto de mi cuenta en CSV o Excel para cargar muchos movimientos de una vez.
- **CA1** Se identifican las columnas de fecha, monto y descripción aunque tengan nombres distintos.
- **CA2** Filas sin fecha o monto válidos → se descartan y se informa cuántas no se importaron.
- **CA3** Fila igual a un movimiento ya registrado → no se duplica.
- **CA4** Los movimientos válidos se muestran en una lista para confirmar antes de guardar.

## Políticas de seguridad (sección Seguridad del TFG)
1. Identificación por correo único + contraseña.
2. Contraseña de 8 a 64 caracteres, sin reglas de composición obligatorias (OWASP).
3. Hash bcrypt vía Passlib, factor de trabajo 12. Nunca texto plano.
4. Login fallido: mensaje único. 5 intentos fallidos consecutivos → bloqueo de 15 minutos. El administrador puede desbloquear.
5. JWT firmado que vence a los 30 minutos de inactividad.
6. HTTPS en producción (TLS en el servidor).
7. Toda consulta filtrada por el usuario autenticado. Al modelo de lenguaje no se le envía nombre ni correo.
