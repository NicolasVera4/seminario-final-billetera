# TRD — Qash

Decisiones técnicas para implementar el PRD. Todo lo que figura acá está alineado con el Entregable 3 salvo los puntos marcados **[AJUSTE]**, que son decisiones nuevas que después hay que reflejar en el documento del TFG.

## 1. Stack

| Capa | Tecnología |
|---|---|
| Frontend | React 18 + Vite + TypeScript, Recharts, React Router, Vitest + React Testing Library + MSW |
| Backend | Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2.0, Alembic, Passlib[bcrypt], python-jose (JWT) |
| Base relacional | PostgreSQL 16 |
| Base vectorial | ChromaDB (servidor en contenedor; `EphemeralClient` en tests) |
| Embeddings | Ollama con `nomic-embed-text` |
| LLM | Groq, modelo `llama-3.3-70b-versatile` (modo JSON) |
| Voz | faster-whisper, modelo `small`, idioma `es`, CPU `int8` |
| OCR | Tesseract (`spa`) + pdf2image |
| PDF con texto | **[AJUSTE]** pdfplumber para leer PDFs digitales (resúmenes de tarjeta, facturas por mail) sin OCR. HU-05 CA2 ya implica que solo los escaneados pasan por OCR |
| Planillas | pandas + openpyxl (HU-14) |
| ML | scikit-learn (`LinearRegression`, `IsolationForest`) |
| Tests backend | pytest, pytest-cov, httpx (`TestClient`), factory helpers propios |
| Orquestación | Docker Compose |

## 2. Estructura del repositorio

```
qash/
├── CLAUDE.md
├── Makefile
├── docker-compose.yml          # db, db_test, chroma, ollama, backend, frontend
├── .env.example
├── docs/                       # PRD, TRD, PLAN, mockups, entregable3.pdf
├── backend/
│   ├── pyproject.toml
│   ├── alembic/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py           # Settings (pydantic-settings)
│   │   ├── db.py
│   │   ├── modelos/            # SQLAlchemy
│   │   ├── esquemas/           # Pydantic
│   │   ├── rutas/              # routers: auth, chat, movimientos, archivos, dashboard, admin
│   │   ├── servicios/
│   │   │   ├── auth.py
│   │   │   ├── interpretacion.py   # orquesta texto -> borrador de movimiento
│   │   │   ├── validacion.py       # reglas de HU-04 (funciones puras)
│   │   │   ├── ingesta/            # ocr.py, pdf.py, voz.py, planilla.py
│   │   │   ├── analisis.py         # totales, alertas, proyección, anomalías
│   │   │   └── asesoramiento.py    # RAG
│   │   └── proveedores/            # interfaces + implementaciones reales
│   │       ├── llm.py              # ProveedorLLM, ProveedorGroq
│   │       ├── embeddings.py       # Embedder, EmbedderOllama
│   │       └── transcripcion.py    # Transcriptor, TranscriptorWhisper
│   └── tests/
│       ├── conftest.py
│       ├── dobles.py               # FakeLLM, FakeEmbedder, FakeTranscriptor
│       ├── fixtures/               # tickets, resúmenes, planillas, audios de prueba
│       ├── unit/
│       ├── api/
│       └── integracion/            # @pytest.mark.integracion
└── frontend/
    └── src/
        ├── api/
        ├── paginas/                # Registro, Login, Chat, Dashboard, Historial, RevisionResumen
        ├── componentes/            # TarjetaMovimiento, Alertas, graficos/...
        └── test/
```

## 3. Modelo de datos

Base: diagrama entidad-relación del TFG (Figura 5). Tablas: `usuarios`, `categorias`, `medios_pago`, `origenes`, `movimientos`, `comprobantes`, `conversaciones`, `mensajes`, `documentos_referencia`.

**[AJUSTE]** Campos que exige la sección Seguridad y que el diagrama no tiene:
- `usuarios.rol` — enum `USUARIO | ADMINISTRADOR`, default `USUARIO`.
- `usuarios.intentos_fallidos` — int, default 0.
- `usuarios.bloqueado_hasta` — timestamp nullable.
- `usuarios.activo` — bool, default true (baja de cuentas por el administrador).

**[AJUSTE]** Campos para cuotas (HU-06 CA3), para que la "cuota 2 de 6" no quede solo en el texto:
- `movimientos.cuota_numero` — int nullable.
- `movimientos.cuota_total` — int nullable.

Enums: `tipo_movimiento (INGRESO, EGRESO)`, `tipo_comprobante (TICKET, FACTURA, RESUMEN_TARJETA, EXTRACTO)`, `rol_mensaje (USUARIO, ASISTENTE)`.

### Catálogos (seed)
- **Categorías** (tomadas de los mockups): Supermercado, Hogar y servicios, Restaurantes, Transporte, Salud y deporte, Indumentaria, Suscripciones, Sueldo, Otros.
- **Medios de pago:** Efectivo, Débito, Crédito, Transferencia, Billetera virtual.
- **Orígenes:** Texto, Voz, Comprobante, Resumen, Extracto.

Moneda por defecto `ARS`.

## 4. API REST

Prefijo `/api`. Todas salvo `auth` requieren `Authorization: Bearer <jwt>`.

| Método | Ruta | HU | Notas |
|---|---|---|---|
| POST | `/auth/registro` | 01 | 201 o 409 (correo existente) / 422 (validación) |
| POST | `/auth/login` | 02 | 200 con token; 401 con mensaje único; 423 si está bloqueada |
| GET | `/auth/yo` | 02 | datos del usuario autenticado |
| GET | `/catalogos` | 04 | categorías, medios de pago, orígenes |
| POST | `/chat/mensajes` | 03, 10 | body: `{conversacion_id?, texto}`; responde borrador de movimiento **o** respuesta de consulta |
| GET | `/chat/conversaciones` | 10 | lista lateral |
| GET | `/chat/conversaciones/{id}` | 10 | mensajes de una conversación |
| POST | `/movimientos/validar` | 04 | devuelve errores y advertencias de un borrador, no guarda |
| POST | `/movimientos` | 04 | guarda uno o varios confirmados (lote para resúmenes y extractos) |
| GET | `/movimientos` | 07 | filtros: `desde, hasta, categoria_id, tipo, medio_pago_id, q`, paginado |
| POST | `/archivos/comprobante` | 05 | multipart; responde 1 borrador |
| POST | `/archivos/resumen` | 06 | multipart; responde N borradores |
| POST | `/archivos/extracto` | 14 | multipart; responde N borradores + filas descartadas |
| POST | `/voz/transcribir` | 11 | multipart audio; responde `{texto}` (no registra nada) |
| GET | `/dashboard?mes=AAAA-MM` | 08, 09, 12, 13 | totales, evolución, por categoría, alertas, proyección, anomalías |
| GET/POST/DELETE | `/admin/documentos` | 10 | solo rol ADMINISTRADOR |
| PATCH | `/admin/usuarios/{id}` | — | desbloquear, editar, dar de baja; solo ADMINISTRADOR |

**Los borradores nunca se persisten como movimientos.** El backend devuelve el borrador interpretado; el frontend lo muestra en la tarjeta de confirmación y recién `POST /movimientos` guarda. El backend vuelve a validar al guardar (no confía en el cliente).

## 5. Autenticación y sesión

- bcrypt con `rounds=12` (testear que el hash empieza con `$2b$12$`).
- Contraseña 8–64 caracteres; correo normalizado a minúsculas.
- Bloqueo: al 5.º fallo consecutivo `bloqueado_hasta = ahora + 15 min`; un login exitoso resetea el contador. El tiempo se inyecta (`reloj`) para poder testearlo sin esperar.
- JWT HS256, `exp` a 30 minutos. **Vencimiento por inactividad:** cada respuesta autenticada devuelve el header `X-Token-Renovado` con un token nuevo; el frontend lo reemplaza. Sin actividad por 30 minutos, el token vence → 401 → el frontend redirige al login.
- Dependencia `usuario_actual` en FastAPI; todos los repositorios reciben `usuario_id` y filtran por él. Test obligatorio de aislamiento: el usuario B no ve ni modifica movimientos del usuario A (404, no 403, para no revelar existencia).

## 6. Interpretación con el modelo de lenguaje

Interfaz única (también cubre el riesgo R4 del TFG: cambiar de proveedor sin tocar el resto):

```python
class ProveedorLLM(Protocol):
    def clasificar_e_interpretar(self, texto: str, hoy: date, catalogo: Catalogo) -> Interpretacion: ...
    def extraer_movimientos(self, texto_documento: str, tipo: TipoComprobante, catalogo: Catalogo) -> list[BorradorMovimiento]: ...
    def responder(self, pregunta: str, contexto_usuario: str | None, fragmentos: list[Fragmento], historial: list[Mensaje]) -> str: ...
```

`Interpretacion` (salida JSON del modelo, validada con Pydantic):

```json
{
  "intencion": "REGISTRO | CONSULTA_DATOS | CONSULTA_ASESORAMIENTO",
  "movimiento": {
    "monto": 15000.00, "fecha": "2026-10-31", "tipo": "EGRESO",
    "medio_pago": "Débito", "descripcion": "Compra en el súper",
    "categoria": "Supermercado"
  },
  "faltantes": ["monto"]
}
```

Reglas de post-proceso (código propio, no del modelo):
- Fecha ausente → `hoy` (HU-03 CA2). El prompt recibe la fecha del día explícitamente.
- `monto` ausente → el asistente pregunta el monto y no se genera borrador (HU-03 CA3).
- Categoría que no está en el catálogo → se conserva como `categoria_sugerida` y `categoria_id = null` (HU-04 CA2).
- Medio de pago ausente → `medio_pago_id = null` (HU-04 CA3).
- Si el JSON del modelo no valida, un reintento; si vuelve a fallar, mensaje de error amable.
- **Privacidad:** el prompt nunca incluye nombre ni correo (test que inspecciona lo que recibe el `FakeLLM`).

## 7. Validación (HU-04) — funciones puras en `servicios/validacion.py`

Devuelve `errores` (bloquean guardado) y `advertencias` (requieren confirmación):
- Error: `monto <= 0`; `fecha > hoy`; `categoria_id` nulo o fuera de catálogo; `medio_pago_id` nulo.
- Advertencia `POSIBLE_DUPLICADO`:
  - Carga individual: mismo usuario, misma fecha, mismo monto y descripción normalizada igual (minúsculas, sin tildes, espacios colapsados).
  - Lotes de resumen y extracto (HU-06 CA5, HU-14 CA3): misma fecha y mismo monto, aunque la descripción difiera (el canal cambia el texto).
- HU-14 CA3 dice "no se duplica": en extractos, una fila idéntica a un movimiento existente se excluye del lote y se informa.

## 8. Ingesta de archivos

| Entrada | Pipeline |
|---|---|
| Imagen (jpg, png, webp) | Tesseract `spa` → texto → `extraer_movimientos(tipo=TICKET)` → se toma 1 |
| PDF con texto | pdfplumber → texto |
| PDF sin texto | pdf2image (todas las páginas) → Tesseract → texto |
| Resumen de tarjeta | texto de **todas** las páginas → `extraer_movimientos(tipo=RESUMEN_TARJETA)` → N borradores con medio de pago Crédito; cuotas → monto de la cuota del período y `cuota_numero/cuota_total` |
| CSV / XLSX | pandas; detección de columnas por sinónimos (`fecha, f. operacion, date`; `monto, importe, debito, credito, amount`; `descripcion, concepto, detalle`); si no se detecta, se pregunta al LLM con los encabezados y 3 filas de muestra |
| Audio (webm, ogg, mp3, wav) | faster-whisper → texto; vacío o error → aviso (HU-11 CA4) |

Formatos no admitidos → 415 con la lista de formatos (HU-05 CA3). Tamaño máximo 10 MB. Los archivos se guardan en un volumen (`/datos/archivos/{usuario_id}/...`) y se registra la fila en `comprobantes` al confirmar.

## 9. Análisis (dashboard)

Todo calculado sobre egresos confirmados del usuario, agregados por mes calendario.
- **Totales del mes** (HU-08 CA1): ingresos, egresos, saldo; variación vs. mes anterior.
- **Evolución** (CA2): últimos 6 meses.
- **Alertas** (HU-09): para cada categoría, `gasto_mes_actual > 1.30 * promedio(3 meses anteriores)`; requiere 3 meses previos con datos de esa categoría. Se recalcula en cada request al dashboard (no se cachea), lo que cumple CA4.
- **Proyección** (HU-12): `LinearRegression` sobre el total mensual de los últimos hasta 6 meses (x = índice de mes). Requiere ≥ 3 meses. Proyección negativa → se recorta a 0.
- **Anomalías** (HU-13): `IsolationForest(random_state=42, contamination=<configurable, default 0.15>)` sobre totales mensuales. Requiere ≥ 4 meses. Validar empíricamente con datos sintéticos que, con 6 meses donde uno duplica al resto, se marca solo ese mes; si con pocos puntos no es estable, documentar el ajuste y avisar (es material para el TFG).

## 10. Asesoramiento (RAG)

- Ingesta (admin o `make seed`): PDF/texto → fragmentos de ~800 caracteres con solapamiento de 100 → embeddings con Ollama → colección ChromaDB `fragmentos_referencia` con metadatos `documento_id, titulo, indice_fragmento`. Se guarda la fila en `documentos_referencia` con `cantidad_fragmentos`.
- Consulta:
  - `CONSULTA_DATOS` (HU-10 CA1): se responde **solo** con datos del usuario. No se genera SQL con el LLM: el backend arma un resumen estructurado (totales por categoría y mes de los últimos 6 meses, más los movimientos del período que nombre la pregunta) y se lo pasa al modelo como contexto.
  - `CONSULTA_ASESORAMIENTO` (CA2): resumen del usuario + top-4 fragmentos recuperados.
  - Sin movimientos (CA4): solo fragmentos y la aclaración explícita en la respuesta.
- Fuentes (CA3): se guardan en `mensajes.fuentes` (jsonb), p. ej. `[{"tipo":"documento","titulo":"El hombre más rico de Babilonia","fragmento":14},{"tipo":"movimientos","desde":"2026-06","hasta":"2026-09"}]`, y se muestran como chips.
- Toda respuesta de asesoramiento incluye que es orientativa y no reemplaza a un profesional (riesgo R7).
- Historial de conversación (CA5): se persisten todos los mensajes; al modelo se le pasan los últimos 10.

## 11. Estrategia de testing

| Nivel | Herramienta | Qué cubre |
|---|---|---|
| Unit backend | pytest | validación, post-proceso de interpretación, detección de columnas, análisis/ML, chunking |
| API backend | pytest + TestClient + Postgres de test | cada criterio de aceptación de punta a punta con dobles de LLM/embeddings/voz |
| Integración | `@pytest.mark.integracion` | Groq, Ollama, Tesseract y whisper reales con fixtures |
| Frontend | Vitest + RTL + MSW | lógica visible de los criterios: botón Guardar deshabilitado con datos faltantes, mensaje de login único, filtros del historial, estado vacío del dashboard, alertas |
| Calidad del LLM | `tests/integracion/conjunto_oro.yaml` | ~30 mensajes reales con la interpretación esperada; reporta % de aciertos por campo (métrica del riesgo R2, sirve para el TFG) |

Base de test: servicio `db_test` en Docker Compose (tmpfs). Esquema creado una vez por sesión con Alembic; cada test corre dentro de una transacción que se revierte.

Fixtures que hay que generar en el repo: ticket de supermercado (imagen), factura de servicio (PDF con texto), resumen de tarjeta de 3 páginas con cuotas (PDF generado con reportlab), el mismo resumen rasterizado (PDF sin texto), extracto CSV y XLSX con nombres de columnas distintos. El audio de prueba lo aporta el usuario (`tests/fixtures/audio/gasto.ogg`).

## 12. Variables de entorno

```
DATABASE_URL, DATABASE_URL_TEST, JWT_SECRETO, JWT_MINUTOS=30,
GROQ_API_KEY, GROQ_MODELO=llama-3.3-70b-versatile,
OLLAMA_URL, OLLAMA_MODELO_EMBEDDINGS=nomic-embed-text,
CHROMA_URL, WHISPER_MODELO=small, ARCHIVOS_DIR, CORS_ORIGENES
```
