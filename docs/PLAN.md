# Plan de desarrollo — Qash

Cada fase sigue el ciclo de `CLAUDE.md`: Plan → Rojo → Verde → Refactor → Cierre. Marcar `[x]` al terminar cada paso.

**Contexto de fechas:** la codificación arranca el 31/10/2026 y el TP4 se entrega el 09/11/2026. La consigna pide para esa fecha el core funcionando y una demo; el código completo se exige en la defensa oral. Las fases 0 a 8 son el core; 9 a 11 pueden quedar para después de la entrega si no llegamos.

---

## Fase 0 — Andamiaje desde cero ✅
El proyecto arranca en un repositorio nuevo y vacío: no se reutiliza ni se copia código de desarrollos anteriores. Todo se escribe en este repo, siguiendo el ciclo TDD.
- [x] `git init`, `.gitignore` (Python, Node, `.env`, volúmenes de datos) y primer commit con `CLAUDE.md` y `docs/`.
- [x] Estructura de carpetas del TRD, `docker-compose.yml` (incluye `db_test`), `Makefile`, `.env.example`.
- [x] pytest, Alembic y Vitest configurados.
- [x] **Rojo/Verde:** `test_salud_responde_ok` (`GET /api/salud`) y un test de render de `App` en el frontend.
- [x] Migración inicial con todas las tablas del TRD §3 y seed de catálogos.

## Fase 1 — Usuarios y sesión (HU-01, HU-02) ✅
Tests mínimos:
- HU-01 CA1–CA4, contraseña > 64 → 422, hash bcrypt con factor 12, correo normalizado.
- HU-02 CA1 (mismo mensaje para correo inexistente y contraseña errónea), CA2, CA3 (aislamiento entre dos usuarios), CA4 (token vencido → 401).
- Bloqueo tras 5 fallos, desbloqueo a los 15 min (reloj inyectado), reset del contador tras login exitoso.
- Header `X-Token-Renovado` en respuestas autenticadas.
- Frontend: pantallas de Crear cuenta e Iniciar sesión (Figuras 7 y 8), mensajes de error, redirección al login cuando la API devuelve 401.
- [x] Plan  - [x] Rojo  - [x] Verde  - [x] Refactor  - [x] Cierre

## Fase 2 — Interpretación en lenguaje natural (HU-03) ✅
- `ProveedorLLM` + `FakeLLM` + `ProveedorGroq`.
- Tests: HU-03 CA1–CA4 con `FakeLLM`; el prompt no contiene nombre ni correo; JSON inválido → reintento → error amable; persistencia de conversación y mensajes.
- Frontend: pantalla de chat (Figura 9) con lista de conversaciones a la izquierda.
- Integración: primeras 10 entradas de `conjunto_oro.yaml` contra Groq real.
- [x] Plan  - [x] Rojo  - [x] Verde  - [x] Refactor  - [x] Cierre

## Fase 3 — Validación y confirmación (HU-04) ✅
- Tests unitarios de `validacion.py` para cada regla; tests de API de CA1–CA5; el backend revalida al guardar aunque el cliente mande datos inválidos.
- Frontend: `TarjetaMovimiento` con los dos estados de la Figura 9 (guardado / "2 datos para completar"), botón Guardar deshabilitado, editar y descartar, aviso de duplicado.
- [x] Plan  - [x] Rojo  - [x] Verde  - [x] Refactor  - [x] Cierre

## Fase 4 — Historial (HU-07) ✅
- Tests: orden descendente, cada filtro por separado y combinados, búsqueda por texto y por monto, estado vacío, paginación, aislamiento por usuario.
- Frontend: Figura 12.
- [x] Plan  - [x] Rojo  - [x] Verde  - [x] Refactor  - [x] Cierre

## Fase 5 — Dashboard y alertas (HU-08, HU-09) ✅
- Tests unitarios de `analisis.py` con datos sintéticos: totales, evolución, distribución, regla del 30 %, sin alerta con menos de 3 meses, contenido de la alerta, recálculo tras guardar.
- Frontend: Figura 11 (sin proyección ni anomalías todavía), estado vacío.
- [x] Plan  - [x] Rojo  - [x] Verde  - [x] Refactor  - [x] Cierre

## Fase 6 — Comprobantes por imagen o PDF (HU-05) ✅
- Generar fixtures (ticket, factura con texto, factura escaneada).
- Tests: CA1–CA4; PDF con texto no pasa por OCR; PDF escaneado sí; 415 para formatos no admitidos; tamaño máximo.
- Frontend: adjuntar archivo desde el chat.
- [x] Plan  - [x] Rojo  - [x] Verde  - [x] Refactor  - [x] Cierre

## Fase 7 — Resumen de tarjeta (HU-06) ✅
- Fixture: resumen de 3 páginas con cuotas, en versión digital y rasterizada.
- Tests: CA1–CA5; todos los borradores con medio de pago Crédito; guardado en lote solo de los confirmados.
- Frontend: pantalla de revisión (Figura 10).
- [x] Plan  - [x] Rojo  - [x] Verde  - [x] Refactor  - [x] Cierre

## Fase 8 — Asesoramiento con RAG (HU-10) ✅
- `Embedder` + `FakeEmbedder` (vectores deterministas) + `EmbedderOllama`; Chroma `EphemeralClient` en tests.
- Tests: chunking, CA1–CA5, fuentes guardadas en `mensajes.fuentes`, aviso de que es orientativo, endpoints de admin (solo rol ADMINISTRADOR; el admin no puede leer movimientos).
- Script de carga de documentos de referencia.
- Frontend: Figura 13 con chips de fuentes.
- [x] Plan  - [x] Rojo  - [x] Verde  - [x] Refactor  - [x] Cierre

**Extra sumado en esta fase (no estaba agendado en ningún lado):** `PATCH /admin/usuarios/{id}` (desbloquear, editar, dar de baja), del TRD §4, que no tenía fase asignada.

**Actualización posterior (04/11/2026), a pedido del profesor:** se reemplazó el documento de referencia de ejemplo por tres fuentes reales y citables (ver `docs/TRD.md` §10, `[AJUSTE]`). Al cargarlas contra los documentos reales se encontró y corrigió un bug: `ProveedorGroq.responder` nunca incluía el texto de los fragmentos recuperados en el mensaje al modelo (pasaba por el parámetro pero no se usaba), por lo que el asesoramiento real no estaba efectivamente anclado en la documentación aunque las fuentes mostradas al usuario fueran correctas. Suite completa verificada en verde (186 tests) después del fix.

## Fase 9 — Proyección y anomalías (HU-12, HU-13) ✅
- Tests con series sintéticas: tendencia creciente, umbrales de 3 y 4 meses, outlier evidente marcado y meses normales no marcados.
- Frontend: los dos gráficos inferiores de la Figura 11.
- [x] Plan  - [x] Rojo  - [x] Verde  - [x] Refactor  - [x] Cierre

**Ajuste encontrado y documentado en el TRD:** con 4 a 6 puntos, `IsolationForest` marca casi siempre el mes más alejado del resto aunque la diferencia sea mínima; se agregó una confirmación de que el mes se aparte 30% o más del promedio de los otros meses antes de reportarlo como anómalo (ver `docs/TRD.md` sección 9, `[AJUSTE]`).

## Fase 10 — Voz (HU-11) ✅
- `Transcriptor` + `FakeTranscriptor` + `TranscriptorWhisper`.
- Tests: CA1–CA4; integración con `gasto.ogg`.
- Frontend: botón de micrófono (MediaRecorder), el texto queda editable en el campo.
- [x] Plan  - [x] Rojo  - [x] Verde  - [x] Refactor  - [x] Cierre

**Pendiente:** el test de integración (`tests/integracion/test_voz_integracion.py`) necesita que subas `tests/fixtures/audio/gasto.ogg` — se saltea solo mientras no esté.

## Fase 11 — Extracto CSV/Excel (HU-14) ✅
- Tests: CA1–CA4 con al menos dos formatos de encabezado distintos, filas inválidas contadas, duplicados excluidos.
- [x] Plan  - [x] Rojo  - [x] Verde  - [x] Refactor  - [x] Cierre

**Decisiones de esta fase (no estaban especificadas en el TRD):** se asume una sola columna de monto con signo (no columnas separadas de débito/crédito); el tipo (ingreso/egreso) se infiere del signo del monto, ya que no hay columna de tipo; categoría y medio de pago quedan sin resolver (el TRD solo prevé el LLM para detectar columnas, no para clasificar cada fila) y se completan a mano en la revisión. No había mockup ni ítem de frontend agendado para esta fase, así que se reusó la pantalla de revisión del resumen de tarjeta (generalizada) en vez de crear una nueva.

## Fase 12 — Cierre y demo ✅
- [x] `make seed-demo`: usuario de demo con 6 meses de movimientos (incluye un mes anómalo y una categoría con alerta, como en la Figura 11).
- [x] README con instructivo de puesta en marcha (lo pide la consigna junto al link de la demo).
- [x] Correr `conjunto_oro.yaml` completo y guardar el reporte en `docs/resultados_llm.md`.
- [x] Suite completa en verde y reporte de cobertura.
- [x] Plan  - [x] Rojo  - [x] Verde  - [x] Refactor  - [x] Cierre

**Resumen de cierre (05/11/2026):** retomada tras la respuesta del profesor a `docs/consulta_profesor_fase12.md` (datos sintéticos aceptados aclarando que son ilustrativos; RAG resuelto con 3 documentos reales). `make seed-demo` (nuevo, `app/seed_demo.py`) crea un usuario demo (`nicolas.vera@gmail.com` / `UsuarioDemo2026`) y un administrador (`nicolas.vera+admin@gmail.com` / `AdminDemo2026`), carga catálogos y los 3 documentos de referencia, y genera 6 meses de movimientos relativos a la fecha en que se ejecuta (re-ejecutable: se regeneran en cada corrida). Las cantidades están calibradas para disparar a la vez la alerta de HU-09 (Restaurantes +60%), un mes anómalo de HU-13 (compra puntual de Indumentaria) y una proyección con tendencia creciente de HU-12 — verificado con tests y contra el dashboard real. El `conjunto_oro.yaml` se completó de 10 a 30 entradas (las 20 nuevas son sintéticas, escritas para esta fase, no mensajes reales relevados) y corrió completo contra Groq real: 100% en intención/tipo/medio de pago/categoría/faltantes, 95% en monto (único error: "2 palos" interpretado como 2.000 en vez de 2.000.000 — limitación real del modelo con esa jerga, documentada tal cual en `docs/resultados_llm.md`, sin maquillarla). README nuevo en la raíz. Suite completa: 193 tests de backend + 62 de frontend, 96% de cobertura de líneas en `backend/app` (lo no cubierto son las funciones que llaman servicios reales — Groq, Ollama, Chroma, Whisper —, ejercitadas solo por los tests de integración). De paso, al cargar los documentos reales se encontró y corrigió un bug real en `ProveedorGroq.responder` (no incluía los fragmentos recuperados en el prompt real; ver `[AJUSTE]` en `TRD.md` §10). Pendiente, no de código: que Luciano aclare en el documento del TFG que los datos de la demo son ilustrativos (pedido explícito del profesor).

**Corrección (09/11/2026):** "6 meses relativos a la fecha en que se ejecuta" se cambió a un límite fijo (31/10/2026) — pedido para el ensayo de la demo: si se regeneraba el mismo día de la demo, el mes más reciente de los datos de prueba coincidía con el mes real, y cualquier movimiento cargado en vivo se mezclaba con los sintéticos. Además, tras un primer ensayo real que dejó conversaciones de chat cargadas, `make seed-demo` ahora también las borra (antes solo limpiaba movimientos) — así que volver a correrlo deja la cuenta demo completamente limpia. Ver `[AJUSTE]` correspondiente en `TRD.md`.
