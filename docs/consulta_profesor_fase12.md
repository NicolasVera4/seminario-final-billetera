# Consulta al profesor antes de la Fase 12 — Qash

Documento de trabajo para llevar a la reunión con el profesor. Resume qué se hizo en cada fase, qué se agregó o decidió más allá de lo que decían `PRD.md`/`TRD.md`/`PLAN.md`, y plantea dos dudas puntuales sobre la Fase 12 (datos de demo y documentación de referencia del asesoramiento) antes de avanzar con ella.

**Estado real del trabajo:** las Fases 0 a 11 están implementadas y con sus tests en verde (todo el "core" más las cuatro fases estirables: proyección/anomalías, voz, extracto CSV/Excel). La Fase 12 (cierre y demo) estaba pausada por las dos dudas de la sección 3 — **el profesor ya respondió (ver sección 5) y la Fase 12 se completó** el 05/11/2026.

---

## 1. Qué se hizo en cada fase

| Fase | Qué cubre | Resumen |
|---|---|---|
| 0 | Andamiaje | Repo desde cero, Docker Compose (`db`, `db_test`, Chroma, Ollama), Makefile, migración inicial con todas las tablas del TRD y seed de catálogos. |
| 1 | HU-01, HU-02 — Usuarios y sesión | Registro, login, bloqueo tras 5 intentos fallidos (15 min), JWT con renovación por actividad, aislamiento de datos entre usuarios. |
| 2 | HU-03 — Interpretación en lenguaje natural | `ProveedorLLM` (Groq) interpreta mensajes de chat y arma un borrador de movimiento; conversaciones y mensajes persistidos. |
| 3 | HU-04 — Validación y confirmación | Reglas de validación (monto, fecha, categoría, medio de pago), aviso de posible duplicado, nada se guarda sin confirmación explícita. |
| 4 | HU-07 — Historial | Listado de movimientos con filtros combinables, búsqueda, paginación. |
| 5 | HU-08, HU-09 — Dashboard y alertas | Totales del mes, evolución de 6 meses, distribución por categoría, alerta cuando una categoría supera 30% su promedio de 3 meses. |
| 6 | HU-05 — Comprobantes por imagen o PDF | OCR (Tesseract) para imágenes y PDF escaneado, lectura directa (pdfplumber) para PDF con texto; se arma un borrador por comprobante. |
| 7 | HU-06 — Resumen de tarjeta | PDF de varias páginas → N borradores (uno por consumo), detección de cuotas, pantalla de revisión antes de guardar en lote. |
| 8 | HU-10 — Asesoramiento con RAG | Carga de documentos de referencia → fragmentos → embeddings (Ollama) → Chroma. El chat responde con datos propios, con la documentación, o ambos, citando de dónde sale cada parte de la respuesta. Incluye rol ADMINISTRADOR para cargar/borrar documentos y gestionar usuarios. |
| 9 | HU-12, HU-13 — Proyección y anomalías | Proyección de gasto del mes siguiente (regresión lineal) y detección de meses con gasto atípico (IsolationForest), con los dos gráficos del dashboard. |
| 10 | HU-11 — Registrar un movimiento por voz | Grabación en el chat, transcripción (faster-whisper) y el texto queda editable antes de enviarlo, igual que si se hubiera escrito. |
| 11 | HU-14 — Importar un extracto en CSV o Excel | Detección de columnas (fecha/monto/descripción) por nombre o, si hace falta, con ayuda del LLM; filas inválidas se descartan y se informa cuántas; duplicados excluidos. |

---

## 2. Qué se agregó o se decidió más allá de lo escrito en PRD/TRD/PLAN

Repaso honesto, fase por fase. Donde no hay nada que listar, lo digo explícitamente — no todas las fases tuvieron desvíos.

**Fases 0, 2, 3, 4, 5, 6, 7:** sin desvíos del TRD/PRD más allá de lo ya documentado ahí. Fase 1 sí tuvo dos ajustes al modelo de datos (ver abajo), y Fase 4 un ajuste forzado por un cambio externo (Groq).

**Fase 1 — campos que el diagrama original no tenía:**
- `usuarios.rol`, `usuarios.intentos_fallidos`, `usuarios.bloqueado_hasta`, `usuarios.activo`: los exige la sección de Seguridad del TFG pero no estaban en el diagrama entidad-relación original. Están documentados como `[AJUSTE]` en `TRD.md` §3.
- `usuarios.nombre`: el mockup de "Crear cuenta" (Figura 7) tiene un campo Nombre que ni los criterios de aceptación de HU-01 ni el diagrama original contemplaban. Se agregó como campo obligatorio. Documentado como `[AJUSTE]` en `TRD.md` §3. Nunca se envía al modelo de lenguaje.

**Fase 4/5 (frontera) — el modelo de LLM que pedía el TFG ya no existe:**
- El TRD especificaba `llama-3.3-70b-versatile`. Al conectar con la API real de Groq, devolvía 404 (`model_not_found`) — está discontinuado. Se reemplazó por `openai/gpt-oss-120b` (el más grande disponible al momento). Esto **no fue una elección de alcance, fue un cambio forzado** porque el modelo original ya no existe en el proveedor. Documentado como `[AJUSTE]` en `TRD.md` §1 y §12, con el detalle en `docs/resultados_llm.md`.

**Fase 8 — un endpoint que estaba en el TRD pero PLAN.md nunca le asignó fase:**
- `PATCH /admin/usuarios/{id}` (desbloquear, editar, dar de baja) ya estaba descripto en `TRD.md` §4 desde el principio, pero ninguna fase de `PLAN.md` lo tenía agendado. Se implementó en la Fase 8 porque ya se estaba tocando el router `/admin`. **No es una funcionalidad inventada**, es un hueco de planificación que se detectó y se cerró.

**Fase 9 — comportamiento de `IsolationForest` que el TRD pedía validar empíricamente:**
- El propio TRD decía: "validar empíricamente... si con pocos puntos no es estable, documentar el ajuste" (TRD §9). Al validarlo, se confirmó la inestabilidad: con 4 a 6 meses de historial, el algoritmo casi siempre marca el mes más alejado del resto como anómalo aunque la diferencia sea mínima (2-3%). Se agregó una confirmación extra: un mes solo se reporta como anómalo si además se aparta 30% o más del promedio de los otros meses. Documentado como `[AJUSTE]` en `TRD.md` §9.
- Decisión menor no documentada como `[AJUSTE]` formal: como las funciones de análisis no reciben la fecha de alta de la cuenta, "historial suficiente" (≥3 o ≥4 meses, HU-12/HU-13 CA2) se calcula contando cuántos meses de la ventana tienen al menos un egreso cargado, no meses calendario desde el alta.

**Fase 10 — sin desvíos del TRD/PRD.** Una decisión de UI menor: el mockup muestra "🎤 Transcripto de un audio" debajo de un mensaje enviado por voz; como el TRD dice explícitamente que `POST /voz/transcribir` "no registra nada", esa marca es solo estado local del navegador (no se persiste, no cambia el contrato de datos).

**Fase 11 — varias decisiones de implementación donde el TRD no entraba en detalle:**
- El TRD menciona columnas de monto por sinónimos "monto, importe, debito, credito, amount" pero no dice qué hacer si un extracto trae columnas de débito y crédito **separadas**. Se asumió una sola columna de monto con signo (no se contempló el caso de dos columnas).
- No hay columna de "tipo" en el extracto, así que el tipo (ingreso/egreso) se infiere del signo del monto.
- El TRD solo prevé que el LLM intervenga para detectar columnas, no para clasificar cada fila. Por eso, a diferencia del resumen de tarjeta (donde el LLM sí sugiere categoría), en el extracto **todas las filas quedan sin categoría ni medio de pago** y el usuario las completa a mano en la pantalla de revisión.
- No había mockup para esta pantalla ni un ítem de frontend agendado en `PLAN.md` para esta fase. En vez de diseñar una pantalla nueva sin referencia visual, se reusó/generalizó la pantalla de revisión del resumen de tarjeta (Fase 7).

Todo esto también quedó anotado en `docs/PLAN.md`, al cierre de cada fase correspondiente.

---

## 3. Las dos dudas para plantear

### 3.1 — Datos de demo ficticios (lo que dispara esta consulta)

`PLAN.md` dice para la Fase 12: *"`make seed-demo`: usuario de demo con 6 meses de movimientos (incluye un mes anómalo y una categoría con alerta, como en la Figura 11)"*. Esto es lo que ya estaba planificado desde antes de que arrancara la Fase 12 — no es algo que yo haya propuesto ahora, pero es exactamente el punto que te genera dudas: son movimientos inventados para que la demo "se vea bien" (que haya una alerta, un mes anómalo, una proyección con tendencia), no datos reales de una persona ni de una fuente verificable.

Preguntas concretas para el profesor:
- ¿Es aceptable que el prototipo de un TFG se demuestre con datos sintéticos armados para mostrar cada funcionalidad (como ya lo plantea el `PLAN.md`), o se espera un dataset real o al menos verosímil/trazable a una fuente?
- Si tiene que ser real: ¿sirve que el propio Luciano cargue sus movimientos reales (o anonimizados) como demo, o el profesor tiene un criterio distinto (por ejemplo, un dataset público de referencia)?
- ¿Esto necesita quedar aclarado en el documento del TFG (que los datos de la demo son ilustrativos, no reales)?

### 3.2 — El documento de referencia del asesoramiento (HU-10, RAG)

Para que el asesoramiento (HU-10) tuviera algo que buscar, en la Fase 8 se cargó un único documento: `backend/app/datos_referencia/tips_finanzas_personales.txt`. Hay que ser preciso acá: **ese texto no es una fuente real citable — lo escribí yo (el asistente) como contenido original de ejemplo**, en español rioplatense, sobre buenas prácticas generales de finanzas personales (fondo de emergencia, gasto hormiga, evitar deuda de tarjeta a tasas altas, etc.). No está tomado de ningún libro, artículo ni autor existente.

Esto importa porque:
- El propio `TRD.md` (§10), al mostrar el formato de las fuentes citadas, pone como ejemplo `"titulo":"El hombre más rico de Babilonia"` — un libro real. Es decir, el diseño original parece asumir que el documento de referencia iba a ser una fuente real y citable, no un texto inventado para el prototipo.
- El criterio de aceptación CA3 de HU-10 dice que el sistema "indica de qué documento proviene" la respuesta. Tal como está hoy, el sistema cumple el criterio técnicamente (sí indica la fuente), pero esa fuente es un texto de relleno que yo generé, no un documento real que pueda citarse en el TFG.
- **No leí `docs/entregable3.pdf`** (tengo instrucción explícita de no tocarlo), así que no puedo confirmar si ese documento de referencia ya está mencionado ahí o si el entregable esperaba uno distinto.

Preguntas concretas para el profesor:
- Para la demo/defensa, ¿conviene reemplazar ese texto por contenido de una fuente real con atribución (por ejemplo, un capítulo o resumen citable de un libro de finanzas personales, respetando derechos de autor), o alcanza con aclarar en el TFG que es contenido ilustrativo armado para el prototipo?
- ¿El documento de referencia (sea cual sea) tiene que estar mencionado en el entregable final del TFG?

---

## 4. Qué quedaba pendiente de la Fase 12

Según `PLAN.md`, antes de la respuesta del profesor:
- `make seed-demo` con el usuario de demo (bloqueado por el punto 3.1).
- Documento(s) de referencia reales para el RAG (bloqueado por el punto 3.2).
- README con instructivo de puesta en marcha.
- Correr el `conjunto_oro.yaml` completo contra Groq real y actualizar `docs/resultados_llm.md`.
- Suite completa en verde y reporte de cobertura.

Los cinco puntos se completaron el 05/11/2026 (ver `docs/PLAN.md`, Fase 12, para el detalle y las decisiones tomadas en cada uno).

---

## 5. Respuesta del profesor (05/11/2026)

- **3.1 (datos de demo ficticios):** aprobado. Se pueden usar datos sintéticos en la demo del TFG, aclarando en el documento final que son ilustrativos y no reales. `make seed-demo` ya genera 6 meses de movimientos ficticios para el usuario de demo, con un mes de gasto anómalo, una categoría que dispara alerta y una tendencia visible en la proyección — tal como preveía `PLAN.md`. **Pendiente de Luciano:** incluir esa aclaración en el documento del TFG.
- **3.2 (documento de referencia del RAG):** resuelto. La base de conocimiento del asesoramiento ya no es el texto de ejemplo — ahora son tres documentos reales y citables, cargados por `make seed`/`make seed-demo`:
  - "OIT (2019). Economía familiar: herramientas para decidir mejor"
  - "Riveros-Cardozo y Becker (2020). Introducción a las finanzas personales"
  - "Tejeda-Hernández et al. (2021). Importancia de las finanzas personales en la salud financiera"

  Al cargarlos se encontró y corrigió un bug (no relacionado con la duda en sí): el prompt real de `responder` nunca incluía el texto de los fragmentos recuperados, por lo que el asesoramiento no estaba efectivamente anclado en la documentación aunque las fuentes mostradas al usuario fueran correctas. Documentado como `[AJUSTE]` en `TRD.md` §10.
