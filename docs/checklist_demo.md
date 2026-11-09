# Checklist manual antes de grabar la demo

Lo que no se puede probar por API — requiere el navegador. Login: `nicolas.vera@gmail.com` /
`UsuarioDemo2026` (después de correr `make seed-demo`).

## Voz (HU-11)

- [ ] En el chat, tocar el micrófono, decir un gasto en voz alta ("gasté dos mil pesos en un café")
      y detener la grabación. **Debería verse:** el texto transcripto aparece en el campo de
      mensaje, editable, antes de enviarlo.
- [ ] Editar una palabra del texto transcripto y enviarlo. **Debería verse:** sigue el mismo flujo
      que un mensaje escrito (aparece el chip "Interpretó el movimiento" y la tarjeta de
      confirmación).
- [ ] Probar en un ambiente con ruido de fondo o hablando rápido. **Debería verse:** si no se
      puede transcribir, un aviso claro sugiriendo repetir o escribir (no un error crudo).

## Dashboard — lectura visual

- [ ] Entrar con el usuario demo recién seedeado. **Debería verse:** la alerta de Restaurantes
      (ámbar), el gráfico de "Meses con gasto anómalo" con septiembre en rojo, y "Proyección de
      gasto" con la barra punteada del mes siguiente.
- [ ] Achicar la ventana del navegador a un ancho de notebook chico (~1280px). **Debería verse:**
      los gráficos no se cortan ni se superponen con la barra lateral.
- [ ] Mirar los números del dashboard con atención: formato de moneda ($15.000,00), signos +/− en
      rojo/verde en el historial.

## Tarjeta de confirmación de movimiento

- [ ] Mandar un mensaje de texto simple ("gasté 5000 en nafta") y mirar la tarjeta que aparece.
      **Debería verse:** monto grande y legible, categoría y medio de pago correctos, botón
      "Guardar movimiento" en verde, "Editar" y "Descartar" visibles sin scroll.
- [ ] Mandar un mensaje ambiguo ("compré algo") y mirar la tarjeta con datos faltantes.
      **Debería verse:** el select en rojo con el motivo abajo, el botón "Guardar" deshabilitado
      hasta completar.

## Tiempos de respuesta (para decidir qué cortar en edición)

- [ ] Cronometrar a ojo: un mensaje de texto simple (HU-03) — en la corrida automática tardó
      **~2 a 7 s**.
- [ ] Cronometrar: subir un comprobante (imagen o PDF corto) — tardó **~3 a 9 s**.
- [ ] Cronometrar: subir el resumen de tarjeta de varias páginas — tardó **~20 s**. Si en la
      grabación se nota largo, conviene cortar en edición o mostrarlo ya cargado.
- [ ] Cronometrar: una pregunta de asesoramiento (HU-10) — tardó **~18 a 22 s**, la más lenta de
      todo el recorrido. Considerar explicar en voz en off mientras carga, o cortar el tiempo
      muerto en edición.

## Admin (sin pantalla propia)

- [ ] Confirmar que no hay ningún lugar del frontend para entrar como administrador — es
      esperado (no hay mockup de pantalla de admin). Si se quiere mostrar esa parte del sistema
      en el video, va a ser necesario mostrarlo por la documentación de la API (`/docs` de
      FastAPI) en vez de la interfaz, o directamente no mostrarlo.

## Generales

- [ ] Revisar que no quede ningún mensaje de error de una prueba anterior visible en el chat del
      usuario demo (si se corrió el script E2E, `make seed-demo` ya se corrió al final para
      dejarlo limpio, pero conviene confirmarlo a ojo antes de grabar).
- [ ] Probar cerrar sesión y volver a entrar, para confirmar que el flujo de login se ve bien en
      cámara.
