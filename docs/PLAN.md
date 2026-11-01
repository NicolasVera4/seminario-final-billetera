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

## Fase 6 — Comprobantes por imagen o PDF (HU-05)
- Generar fixtures (ticket, factura con texto, factura escaneada).
- Tests: CA1–CA4; PDF con texto no pasa por OCR; PDF escaneado sí; 415 para formatos no admitidos; tamaño máximo.
- Frontend: adjuntar archivo desde el chat.
- [ ] Plan  - [ ] Rojo  - [ ] Verde  - [ ] Refactor  - [ ] Cierre

## Fase 7 — Resumen de tarjeta (HU-06)
- Fixture: resumen de 3 páginas con cuotas, en versión digital y rasterizada.
- Tests: CA1–CA5; todos los borradores con medio de pago Crédito; guardado en lote solo de los confirmados.
- Frontend: pantalla de revisión (Figura 10).
- [ ] Plan  - [ ] Rojo  - [ ] Verde  - [ ] Refactor  - [ ] Cierre

## Fase 8 — Asesoramiento con RAG (HU-10)
- `Embedder` + `FakeEmbedder` (vectores deterministas) + `EmbedderOllama`; Chroma `EphemeralClient` en tests.
- Tests: chunking, CA1–CA5, fuentes guardadas en `mensajes.fuentes`, aviso de que es orientativo, endpoints de admin (solo rol ADMINISTRADOR; el admin no puede leer movimientos).
- Script de carga de documentos de referencia.
- Frontend: Figura 13 con chips de fuentes.
- [ ] Plan  - [ ] Rojo  - [ ] Verde  - [ ] Refactor  - [ ] Cierre

## Fase 9 — Proyección y anomalías (HU-12, HU-13)
- Tests con series sintéticas: tendencia creciente, umbrales de 3 y 4 meses, outlier evidente marcado y meses normales no marcados.
- Frontend: los dos gráficos inferiores de la Figura 11.
- [ ] Plan  - [ ] Rojo  - [ ] Verde  - [ ] Refactor  - [ ] Cierre

## Fase 10 — Voz (HU-11)
- `Transcriptor` + `FakeTranscriptor` + `TranscriptorWhisper`.
- Tests: CA1–CA4; integración con `gasto.ogg`.
- Frontend: botón de micrófono (MediaRecorder), el texto queda editable en el campo.
- [ ] Plan  - [ ] Rojo  - [ ] Verde  - [ ] Refactor  - [ ] Cierre

## Fase 11 — Extracto CSV/Excel (HU-14)
- Tests: CA1–CA4 con al menos dos formatos de encabezado distintos, filas inválidas contadas, duplicados excluidos.
- [ ] Plan  - [ ] Rojo  - [ ] Verde  - [ ] Refactor  - [ ] Cierre

## Fase 12 — Cierre y demo
- [ ] `make seed-demo`: usuario de demo con 6 meses de movimientos (incluye un mes anómalo y una categoría con alerta, como en la Figura 11).
- [ ] README con instructivo de puesta en marcha (lo pide la consigna junto al link de la demo).
- [ ] Correr `conjunto_oro.yaml` completo y guardar el reporte en `docs/resultados_llm.md`.
- [ ] Suite completa en verde y reporte de cobertura.
