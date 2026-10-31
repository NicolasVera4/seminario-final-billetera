# Mockups de Qash

Capturas de las pantallas diseñadas para el TFG (Figuras 7 a 13 del Entregable 3). Son la referencia visual del frontend: el diseño (estructura, textos, colores y estados) tiene que respetarse. Los datos que aparecen son de ejemplo.

| Archivo | Pantalla | Historias | Qué tiene que verse |
|---|---|---|---|
| `fig07-crear-cuenta.png` | Crear cuenta | HU-01 | Panel izquierdo de presentación + formulario (nombre, correo, contraseña, repetir contraseña). Error de correo existente bajo el campo; ayuda "Mínimo 8 caracteres." |
| `fig08-iniciar-sesion.png` | Iniciar sesión | HU-02 | Mismo layout. Error único arriba del formulario: "El correo o la contraseña no son correctos." |
| `fig09-chat-registro-movimientos.png` | Chat: registro | HU-03, HU-04, HU-11 | Barra lateral (Dashboard, Chat, Historial, conversaciones, usuario). Chips de pasos ("Interpretó el movimiento", "Validó los datos"). Tarjeta guardada y tarjeta con "2 datos para completar": selects en rojo con el motivo, botón Guardar deshabilitado, Editar, Descartar. Etiqueta "Transcripto de un audio". Barra inferior con adjuntar, micrófono y enviar |
| `fig10-revision-resumen-tarjeta.png` | Revisión de resumen | HU-06 | Encabezado con archivo, páginas leídas, cierre y medio de pago. Chips de conteo (consumos, posible duplicado, categoría para elegir). Tabla con checkbox, cuota "2 de 6", select de categoría, acciones por fila, "Guardar igual / Descartar" en el duplicado. Pie con total seleccionado y botón deshabilitado hasta resolver pendientes |
| `fig11-dashboard.png` | Dashboard | HU-08, HU-09, HU-12, HU-13 | Selector de mes. Tres tarjetas (ingresos, gastos, saldo) con comparación vs. mes anterior. Bloque de alertas con %, monto actual, promedio y "Ver movimientos". Flujo mensual (líneas), gastos por categoría (dona + leyenda con %), proyección (barras + barra punteada) y meses anómalos (barra roja + nota) |
| `fig12-historial.png` | Historial | HU-07 | Filtros: buscar, desde, hasta, categoría, tipo, medio de pago, Limpiar. Tabla con fecha, descripción, categoría (chip), medio de pago, origen y monto (egresos en rojo con "−", ingresos en verde con "+"). Paginación |
| `fig13-chat-asesoramiento.png` | Chat: asesoramiento | HU-10 | Chips "Consultó tus movimientos" / "Buscó en la documentación". Respuesta con montos en negrita. Chips de fuentes (documento + fragmento, rango de movimientos) |

## Estilo general
- Fondo claro, tarjetas blancas con borde gris suave y esquinas redondeadas.
- Color principal verde (botones, mensajes del usuario, ítem activo de la barra lateral); rojo para errores y egresos; ámbar para advertencias.
- Montos con formato argentino: `$15.000,00`. Fechas `dd/mm/aaaa`.
- Textos en español rioplatense, tal como aparecen en las capturas.
