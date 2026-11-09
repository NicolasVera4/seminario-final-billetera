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
| LLM | Groq, modelo `openai/gpt-oss-120b` (modo JSON) **[AJUSTE]** — el TFG especificaba `llama-3.3-70b-versatile`, pero Groq lo discontinuó (confirmado contra la API real en la Fase 4, devolvía 404 `model_not_found`); se eligió el modelo más grande disponible hoy en Groq como reemplazo más cercano en capacidad |
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

**[AJUSTE]** `usuarios.nombre` — string, obligatorio. El mockup de Crear cuenta (Figura 7) tiene un campo "Nombre" que los CA de HU-01 y el diagrama original no contemplaban. Se agrega la columna y se trata como campo obligatorio igual que correo y contraseña (HU-01 CA3: vacío → se señala). Nunca se envía al LLM (ver política de privacidad).

**[AJUSTE]** Campos para cuotas (HU-06 CA3), para que la "cuota 2 de 6" no quede solo en el texto:
- `movimientos.cuota_numero` — int nullable.
- `movimientos.cuota_total` — int nullable.

**[AJUSTE]** Bug reportado en el ensayo de la demo (08/11/2026): al navegar al historial de
conversaciones (ver ítem HU-10 CA5 / sección 10), los movimientos del chat que ya estaban
**guardados** se veían como si nunca se hubieran interpretado — se perdían la tarjeta, los chips
("Interpretó el movimiento" / "Validó los datos") y la marca de "Transcripto de un audio". Causa:
nada vinculaba un movimiento guardado con el mensaje de chat que lo propuso (`movimientos` tenía
`conversacion_id` pero el frontend nunca lo mandaba, y no había forma de saber a qué mensaje
puntual correspondía), y si un mensaje venía de una transcripción de audio tampoco se persistía.
Se agregó:
- `movimientos.mensaje_id` — FK nullable a `mensajes.id` (migración `5f029e540b43`). El frontend
  ahora manda `conversacion_id` y `mensaje_id` al confirmar un movimiento desde el chat.
- `mensajes.transcripto` — bool, default `false` (misma migración).

`GET /chat/conversaciones/{id}` ahora devuelve, por cada mensaje, el movimiento ya guardado que le
corresponde (mismo shape que el borrador) y el flag `transcripto`, para que el frontend reconstruya
exactamente la misma tarjeta y chips que se vieron al momento de confirmar. Los borradores
**pendientes** (todavía no confirmados) siguen sin persistirse — esa limitación se mantiene a
propósito (ver sección 10).

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
| GET | `/chat/conversaciones/{id}` | 10 | mensajes de una conversación, con el movimiento ya guardado (si lo hay) y `transcripto` por mensaje |
| POST | `/movimientos/validar` | 04 | devuelve errores y advertencias de un borrador, no guarda |
| POST | `/movimientos` | 04 | guarda uno o varios confirmados (lote para resúmenes y extractos) |
| GET | `/movimientos` | 07 | filtros: `desde, hasta, categoria_id, tipo, medio_pago_id, q`, paginado |
| POST | `/archivos/comprobante` | 05 | multipart; responde 1 borrador |
| POST | `/archivos/resumen` | 06 | multipart; responde N borradores |
| POST | `/archivos/extracto` | 14 | multipart; responde N borradores + filas descartadas |
| POST | `/archivos/adjuntar` | 05, 06, 14 | multipart (`archivo` + `conversacion_id` opcional); une los tres anteriores, decide cuál usar, y además persiste un mensaje de usuario y uno del asistente en esa conversación |
| POST | `/voz/transcribir` | 11 | multipart audio; responde `{texto}` (no registra nada) |
| GET | `/dashboard?mes=AAAA-MM` | 08, 09, 12, 13 | totales, evolución, por categoría, alertas, proyección, anomalías |
| GET/POST/DELETE | `/admin/documentos` | 10 | solo rol ADMINISTRADOR |
| GET | `/admin/usuarios` | — | lista cuentas con rol USUARIO (nunca otros administradores); solo ADMINISTRADOR |
| PATCH | `/admin/usuarios/{id}` | — | desbloquear, editar, dar de baja; solo ADMINISTRADOR |

**Los borradores nunca se persisten como movimientos.** El backend devuelve el borrador interpretado; el frontend lo muestra en la tarjeta de confirmación y recién `POST /movimientos` guarda. El backend vuelve a validar al guardar (no confía en el cliente).

**[AJUSTE]** Pantalla de administrador, primera versión (09/11/2026). El backend de admin
(`/admin/documentos`, `/admin/usuarios`) ya existía de una fase anterior, pero nunca tuvo interfaz
— no hay mockup de admin en el TFG (las Figuras 7 a 13 son todas de usuario). Se armó siguiendo el
PRD textual ("Administrador: edita perfiles, desbloquea y da de baja cuentas, carga/reemplaza/
elimina la documentación de referencia del RAG. **No accede** a movimientos ni conversaciones de
usuarios"):
- `GET /admin/usuarios` (nuevo): lista las cuentas con rol `USUARIO` — nunca otras cuentas
  `ADMINISTRADOR` — con su estado (activa / bloqueada / de baja), para poder elegir a quién
  editar vía `PATCH /admin/usuarios/{id}` (que ya existía pero no tenía forma de listar usuarios
  para encontrar un `id`).
- Frontend nuevo: `AdminDocumentos.tsx` (listar/cargar/eliminar documentos de referencia) y
  `AdminUsuarios.tsx` (listar usuarios, desbloquear, dar de baja/reactivar), mismos estilos que el
  resto de la app (`.card`, tablas, `.btn`, `.pill`).
- `BarraLateral.tsx`: el `.nav` ahora depende del rol del usuario logueado (`GET /auth/yo`, que ya
  traía `rol`). Un `ADMINISTRADOR` ve "Documentación" y "Usuarios" en vez de "Dashboard", "Chat" e
  "Historial" (ninguna de esas tres aplica — un admin no puede usar ninguna, ver
  `test_admin_no_puede_*` en `tests/api/test_admin.py`).
- `Login.tsx`: después de iniciar sesión, redirige a `/admin/documentos` si el rol es
  `ADMINISTRADOR`, a `/` (chat) si es `USUARIO` — antes siempre mandaba a `/`, que para un admin
  hubiera fallado con 403 apenas intentara usar el chat.
- **A propósito no se agregó**: ninguna vista que muestre conversaciones ni su contenido para el
  admin — lo pidió el usuario en la conversación de diseño, pero choca directo con la restricción
  de privacidad del PRD citada arriba, así que se dejó afuera.

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

**[AJUSTE]** Bug encontrado en el ensayo de la demo (08/11/2026): tras HU-03 CA3 (el asistente pide
el monto), responder solo con el monto (p. ej. "5000") no completaba el registro — quedaba
"clavado" y había que repetir todo el mensaje de nuevo. Causa: `clasificar_e_interpretar` arma el
prompt solo con el mensaje actual, sin nada de la conversación previa, así que el segundo llamado
al LLM recibía "5000" sin ningún contexto de que era la respuesta a "¿Cuánto fue?" sobre "Pagué el
gimnasio". El camino de asesoramiento (`responder()`) sí recibía `historial`; el de
registro/interpretación nunca lo tuvo. Se corrigió pasándole también el historial reciente de la
conversación (mismos `CANTIDAD_MENSAJES_HISTORIAL=10` mensajes que ya se usaban para asesoramiento)
a `clasificar_e_interpretar`, que lo agrega al prompt como contexto de conversación. De paso, se
corrigió que ese historial se buscaba en la base **después** de guardar el mensaje del usuario
actual (podía incluirse a sí mismo duplicado); ahora se busca antes de guardarlo, para los dos
caminos (test en `tests/api/test_chat.py` y `tests/unit/test_proveedor_groq.py`).

**[AJUSTE]** Bug encontrado en el ensayo de la demo (05/11/2026): si Groq devuelve un error de API
(no "JSON inválido", sino por ejemplo `413 request too large` al mandar un documento largo, un
timeout o un error de red), `ProveedorGroq` no lo capturaba — el error de la librería `groq` se
propagaba sin atrapar y la ruta devolvía `500 Internal Server Error` en vez del `422` esperado.
Pasó en la práctica subiendo un resumen de cuenta real de 15 páginas (`/archivos/resumen`): el
texto superó el límite de tokens por minuto del modelo. Se corrigió moviendo la llamada al
cliente adentro del mismo `try` del reintento y agregando `groq.APIError` (clase base de todos
los errores del SDK: conexión, timeout, rate limit, etc.) a las excepciones atrapadas en
`clasificar_e_interpretar`, `extraer_movimientos` y `detectar_columnas` — ahora cualquier falla
de la API de Groq cuenta como intento fallido y, si se agotan los reintentos, levanta
`ErrorInterpretacion` igual que un JSON inválido (test en `tests/unit/test_proveedor_groq.py`).

**[AJUSTE]** Resultado inestable en resúmenes de tarjeta grandes (07/11/2026): subiendo el mismo
resumen real de 5 páginas tres veces seguidas, la cantidad de consumos detectados variaba de 5 a
12 entre corridas. Causas encontradas y corregidas:
- `_completar_con_groq` no fijaba `temperature` (quedaba en el default del proveedor, no
  determinístico) ni `max_tokens` explícito. Ahora usa `temperature=0, max_tokens=4096`.
- `procesar_resumen` mandaba el texto de **todo el documento concatenado** en un solo llamado al
  LLM, arriesgando el límite de tokens por minuto de Groq (ver el bug anterior) y forzando al
  modelo a procesar un bloque de texto grande de una sola vez. Ahora `extraer_texto_pdf_por_pagina`
  conserva el texto por página y `dividir_en_bloques` (`servicios/comprobantes.py`,
  `LIMITE_CARACTERES_BLOQUE=6000`) agrupa páginas consecutivas hasta ese límite antes de llamar al
  LLM una vez por bloque, uniendo los resultados — sin partir ni duplicar texto (test en
  `tests/unit/test_comprobantes.py` y `tests/api/test_resumen.py`).
- El prompt de extracción de resúmenes no distinguía entre consumos reales y otras líneas del
  resumen con fecha y monto (saldo anterior, pagos, impuestos/intereses/percepciones). Se agregó
  una exclusión explícita. Con un resumen real de 5 páginas (5 consumos reales, verificados
  visualmente contra el documento) el resultado pasó de variar 5-12 ítems a estabilizarse en
  10-12: ya no incluye saldo anterior ni pagos, los 2 consumos en cuotas y los montos de los 4
  consumos en pesos salen siempre bien, pero el modelo sigue incluyendo las líneas de
  impuestos/intereses del resumen como si fueran consumos pese a la instrucción explícita de
  excluirlas — se documenta como limitación del modelo (gpt-oss-120b), no se siguió iterando el
  prompt para no sobreajustarlo a un único documento.
- Se encontró además que `tests/conftest.py` usaba `chromadb.EphemeralClient()` para aislar cada
  test, pero esa clase comparte un singleton de proceso: dos instancias "separadas" terminan
  viendo las mismas colecciones (confirmado empíricamente), filtrando documentos cargados por un
  test hacia otro. Se cambió a `chromadb.PersistentClient(path=<directorio temporal por test>)`,
  que sí aísla de verdad. Esto estaba enmascarando una falla real: un test nuevo que verifica que
  las fuentes de un mismo documento no se dupliquen en la respuesta de asesoramiento pasaba o
  fallaba según qué otros tests hubieran corrido antes en el mismo proceso.
- De paso, `_recuperar_fragmentos` (`servicios/asesoramiento.py`) deduplica las fuentes de tipo
  "documento" por título: si Chroma devuelve varios fragmentos del mismo documento, antes
  aparecía una fuente repetida por cada fragmento — ahora cada documento aparece una sola vez.

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

**[AJUSTE]** Botón único "Adjuntar" en el chat (08/11/2026): el mockup (Figura 9) y el ensayo de
la demo mostraron un solo ícono de adjuntar, pero `POST /archivos/comprobante`, `/resumen` y
`/extracto` seguían siendo tres endpoints separados con tres inputs de archivo distintos en la UI.
Se agregó `POST /archivos/adjuntar`, que recibe cualquier archivo admitido y decide internamente
qué procesador usar (los tres endpoints originales se mantienen intactos, con sus mismos tests por
HU — `/adjuntar` los reutiliza, no los reemplaza):
- CSV/XLSX → `procesar_extracto` (sin ambigüedad, se identifica por `content-type`).
- Imagen → `procesar_comprobante` (sin ambigüedad).
- PDF → ambiguo, porque un comprobante puntual (HU-05) y un resumen de tarjeta (HU-06) son ambos
  PDF. Se resuelve por cantidad de páginas: 1 página → comprobante; 2 o más → resumen de tarjeta.
  Limitación conocida y aceptada: un resumen real de una sola página se procesaría como comprobante
  puntual (un solo movimiento en vez de varios). No es el caso típico de un resumen de tarjeta.

La respuesta trae un campo `modo` (`COMPROBANTE` | `RESUMEN` | `EXTRACTO`, unión discriminada en
`esquemas/archivos.py`) para que el frontend sepa si mostrar la tarjeta de confirmación en el chat
o navegar a la pantalla de revisión de lote. El frontend (`Chat.tsx`) ahora tiene un solo input de
archivo con `accept` como ayuda visual para el selector del SO (test en `tests/api/test_adjuntar.py`
y `Chat.test.tsx`).

**[AJUSTE]** Ronda de pruebas con archivos reales (09/11/2026): comprobantes (ticket, recibo de
sueldo), facturas en PDF y resúmenes grandes. Bugs encontrados y corregidos:
- **Crítico — guardar un movimiento desde un comprobante tiraba 500.** El mensaje que muestra el
  borrador de un comprobante se armaba solo en el navegador (`Chat.tsx`, nunca pasaba por el
  backend), así que su `id` era local (`Date.now()`), no uno real de la base. El cambio anterior
  que vincula `movimientos.mensaje_id` al guardar (ver sección 3) mandaba ese id falso, y el
  `INSERT` violaba la foreign key. Arreglo inmediato: el frontend solo manda `conversacion_id` /
  `mensaje_id` cuando el mensaje es uno que realmente vino del backend (`MensajeChat.persistido`
  en `Chat.tsx`). La solución de fondo quedó resuelta en la ronda del mismo día (ver más abajo:
  `/archivos/adjuntar` ahora persiste sus propios mensajes reales).
- **`RevisionResumen` volvía a "Historial" en vez de al chat al guardar un resumen o extracto.**
  Simplemente estaba hardcodeado así (`navegar('/historial')`); se corrigió a `/chat`.
- **Un resumen de varias páginas tarda ~2 minutos y la interfaz no lo mostraba.** Con
  `resumen28-8al1-10.pdf` (15 páginas, 7 bloques) se midió 1m56s reales contra Groq — no es un
  cuelgue, es el rate limit de tokens por minuto del plan actual, que ya se documentó en la sección
  del bug del 05/11. Como la interfaz no daba ninguna señal, parecía que el archivo "nunca se
  procesaba". Se agregó estado de carga: el input de adjuntar se deshabilita y el texto de ayuda
  del compositor cambia a "Procesando tu archivo..." mientras dura la subida.
- **Monto inconsistente en documentos con varios montos** (ej. recibo de sueldo: bruto,
  descuentos, neto): el prompt de extracción para comprobantes puntuales solo decía "el total del
  comprobante", sin aclarar qué hacer cuando hay varios montos en el documento — el modelo elegía
  uno distinto en cada corrida. Se agregó la instrucción explícita de usar el monto final neto (el
  que la persona efectivamente paga o cobra), nunca un subtotal, descuento o parcial. Mejora la
  consistencia pero no la elimina del todo: con el recibo de sueldo real de prueba, de 3 corridas 2
  dieron el mismo monto y 1 no pudo leer ninguno — queda una variable de calidad de OCR
  (Tesseract sobre una imagen de 794×757 con texto denso) que no se resuelve solo con el prompt.
  **Pendiente de decidir con el usuario:** si registrar el sueldo por foto de recibo es un caso que
  Qash debe soportar bien (el recibo de sueldo no es un "ticket/factura" en el sentido de HU-05 —
  tiene una estructura totalmente distinta, con múltiples montos con significados propios), o si
  alcanza con que el usuario lo cargue por texto cuando la foto falle. Resuelto: confirmado que
  funciona bien con la mejora del prompt (ticket y recibo de sueldo probados por el usuario,
  resultados correctos y estables).

**[AJUSTE]** Adjuntar un archivo ahora queda registrado en el chat como una conversación real
(09/11/2026). Antes, `/archivos/comprobante`, `/resumen` y `/extracto` (y el `/adjuntar` que los
unifica) no tocaban `conversaciones`/`mensajes` para nada — lo que se veía en el chat al subir un
archivo era pura puesta en escena del lado del cliente (`Chat.tsx` armaba mensajes con id local),
así que: (a) mostraba el nombre crudo del archivo en vez de un texto natural, y (b) al navegar a
otra conversación y volver, o al recargar, esos "mensajes" desaparecían por completo — nunca
habían existido en la base. `procesar_adjunto` ahora, al terminar de procesar el archivo con
éxito, crea o reutiliza una conversación (`conversacion_id` opcional, mandado por el frontend como
campo de formulario) y guarda dos mensajes reales: uno del usuario con un texto fijo según el tipo
(`MENSAJE_USUARIO_ADJUNTO_POR_TIPO` en `servicios/comprobantes.py`: "Cargaste un ticket.",
"Cargaste una factura.", "Cargaste un resumen de tarjeta." o "Cargaste un extracto." — nunca el
nombre del archivo) y uno del asistente con el resultado (el mismo mensaje de siempre para un
comprobante puntual; para resumen/extracto, "Encontré N consumos/movimientos, revisalos y
confirmalos."). La respuesta de `/adjuntar` ahora incluye `conversacion_id` y `mensaje_id` reales.
Se extrajo `obtener_o_crear_conversacion`/`guardar_mensaje` de `servicios/interpretacion.py` a un
módulo nuevo y compartido, `servicios/conversaciones.py`, para no duplicar esa lógica entre el
camino de texto y el de archivos.

En el frontend, `Chat.tsx` muestra el mensaje del usuario **apenas se elige el archivo** (antes
solo aparecía junto con la respuesta, varios segundos o minutos después, lo que sumado a la falta
de indicador de carga hacía parecer que no había pasado nada) con un texto adivinado del lado del
cliente por tipo de archivo (`textoOptimistaAdjunto`), que después convive con el mensaje real
guardado en el backend. Para un comprobante, la tarjeta de movimiento ahora usa el `conversacion_id`
/`mensaje_id` reales que devuelve el backend (antes nunca los mandaba). `RevisionResumen` recibe
`conversacionId` por `state` de navegación y lo manda en cada movimiento al guardar, para que
también queden asociados a esa conversación.

**Limitación que quedaba pendiente — resuelta el mismo día (09/11/2026):** un resumen o extracto
con un único movimiento no tenía forma de verse como tarjeta "Guardado" al volver a la
conversación, porque el mecanismo de `GET /chat/conversaciones/{id}` asocia **un** movimiento por
mensaje, y antes un resumen/extracto siempre mandaba a la pantalla de revisión en lote (incluso con
1 solo ítem) sin dejar ninguna tarjeta asociada a ningún mensaje. Encontrado probando
`Octubre_factura-telefono.pdf` (factura de teléfono, 3 páginas, 1 solo consumo real): el usuario
reportó que después de confirmarla en la pantalla de revisión, no quedaba nada mostrado en el chat.
Se corrigió en `procesar_adjunto`/`_resultado_desde_lote`: si un resumen o extracto encuentra
**exactamente un** movimiento, no tiene sentido lotearlo — se lo trata igual que subir la imagen de
un comprobante puntual (`modo: "COMPROBANTE"`, con su borrador, su `archivo_ref` y su
`comprobante_tipo` real — RESUMEN_TARJETA o EXTRACTO, no TICKET/FACTURA), así que usa exactamente
el mismo camino ya probado (tarjeta, chips, `conversacion_id`/`mensaje_id` reales, reconstrucción
al volver al chat) sin tocar nada del frontend. Con 2 o más movimientos, sigue yendo a la pantalla
de revisión en lote como corresponde — ahí sigue la limitación: esos movimientos no se reconstruyen
como tarjetas al volver (ver debajo).

**[AJUSTE]** El mensaje de usuario al adjuntar un archivo cambió de wording (09/11/2026): primero
decía "Cargaste un ticket."/"...una factura."/"...un resumen de tarjeta."/"...un extracto." según
`comprobante_tipo`, pero el usuario señaló que adivinar el tipo de documento está mal — un recibo
de sueldo no es un "ticket". Ahora dice simplemente **"Cargaste una imagen: {nombre}."** o
**"Cargaste un archivo: {nombre}."** (imagen si el `content-type` empieza con `image/`, archivo en
cualquier otro caso — PDF, CSV, XLSX), sin opinar sobre qué tipo de documento es. El texto
optimista del lado del cliente (`Chat.tsx`, antes de tener la respuesta del backend) usa el mismo
formato.

**[AJUSTE]** Mensaje de cierre al confirmar un lote de resumen/extracto (09/11/2026): con 2 o más
movimientos, el usuario señaló que "Encontré N consumos en tu resumen de tarjeta, revisalos y
confirmalos." quedaba raro — sonaba a pendiente de confirmar aunque el usuario ya los hubiera
guardado desde `RevisionResumen`. No se reconstruyen como tarjetas individuales al volver al chat
(ver limitación de la sección anterior, un movimiento por mensaje), pero ahora `guardar_movimientos`
(`servicios/movimientos.py`) detecta si el guardado vino de la pantalla de revisión en lote —
`item.origen in ("Resumen", "Extracto")`, ya seteado por `RevisionResumen.tsx`, y
`conversacion_id` presente — y deja un mensaje de cierre del asistente: **"Se cargó 1 movimiento
de tu extracto."** / **"Se cargaron N movimientos de tu resumen de tarjeta."**. Un movimiento
confirmado desde el chat de texto o un comprobante puntual (origen "Texto"/default) no dispara
esto — ya muestra su propio "Guardado" en la tarjeta, no necesita un mensaje aparte (test en
`tests/api/test_movimientos.py`). Como `Chat.tsx` ya recarga la conversación completa desde el
backend al volver a `/chat` (mismo mecanismo de `localStorage` + `obtenerConversacion` de la
sección de navegación del historial), este mensaje aparece solo, sin tocar nada del frontend.

**[AJUSTE]** Se probó subir `LIMITE_CARACTERES_BLOQUE` de 6000 a 9000 caracteres para reducir la
cantidad de llamados al LLM en resúmenes grandes (de 7 a 4 bloques con el archivo real de prueba de
15 páginas) y así bajar el tiempo de ~2 minutos. Resultado medido: el tiempo bajó poco (1m56s →
1m40s, ~14%, no proporcional a la baja de llamados — confirma que el límite real es el rate limit
de tokens por minuto de Groq, no el overhead por llamado) y la cantidad de consumos detectados
**bajó** de 18 a 12 — bloques más grandes hacen que el modelo se salga líneas. Se revirtió a 6000.
No hay una forma segura de acelerar esto sin cambiar de plan de Groq o de modelo; la mitigación
real es el indicador de carga ya agregado, no un bloque más grande.

**[AJUSTE]** Bug encontrado en el ensayo de la demo (08/11/2026): grabar un audio y transcribirlo
fallaba siempre con el mensaje de HU-11 CA4 ("No pudimos transcribir el audio..."), incluso con
grabaciones cortas y claras. Causa: `faster-whisper>=1.0` no fija una versión de su dependencia
`av` (PyAV); pip instalaba la última (`av 19.x`), que le sacó el parámetro `metadata_errors` a
`av.open()`. La función interna de faster-whisper que decodifica el audio (`decode_audio`) sigue
pasando ese parámetro, así que cualquier transcripción tiraba `TypeError` — `TranscriptorWhisper`
lo atrapaba como `except Exception` genérico y lo convertía en el aviso de "no pudimos
transcribir", ocultando que en realidad nunca llegaba a correr el modelo. Confirmado reproduciendo
`WhisperModel.transcribe()` directamente fuera de la app. Se corrigió fijando `av<19` en
`pyproject.toml` (probado que `av` 15 a 18 funcionan con `faster-whisper 1.2.1`; recién desde la
19 rompe). No se detectaba con los tests existentes porque usan `FakeTranscriptor` — el doble no
pasa por PyAV. Ya existía un test de integración para este flujo
(`tests/integracion/test_voz_integracion.py`) pero queda deshabilitado por `skipif` hasta que se
agregue el archivo de audio real `tests/fixtures/audio/gasto.ogg`, que todavía no está en el
repo.

**[AJUSTE]** Mensaje distinto cuando Groq devuelve rate limit (09/11/2026): probando con archivos
reales (`resumen28-8al1-10.pdf`, `resumen-septiembre.pdf`), de golpe empezaron a fallar con "No
pudimos leer el comprobante. Probá cargarlo por texto." — ya habían funcionado antes en la misma
sesión. Reproducido llamando a Groq directo: `429 rate_limit_exceeded`, límite **diario** de tokens
agotado (`tokens per day (TPD): Limit 200000, Used 198954`), no el límite por minuto del bug del
05/11. El mensaje de "no pudimos leer" es engañoso en este caso — no es un problema del documento,
es temporal (Groq ya informa cuándo se libera). Se agregó distinción: `ErrorInterpretacion` ahora
lleva un flag `limite_tasa` (seteado cuando la causa es específicamente `groq.RateLimitError`, no
cualquier `APIError`) en los cuatro métodos de `ProveedorGroq` que lo levantan
(`clasificar_e_interpretar`, `extraer_movimientos`, `detectar_columnas`, `categorizar_filas`); los
llamadores (`servicios/comprobantes.py`, `servicios/interpretacion.py`) eligen
`MENSAJE_LIMITE_TASA` ("Estamos recibiendo muchas solicitudes en este momento. Probá de nuevo en
unos minutos.") en vez del mensaje específico de cada caso cuando ese flag está prendido.
`responder()` (modo chat, no JSON) no tenía ningún manejo de errores de Groq — un rate limit ahí
tiraba 500 sin atrapar, un gap que no se había notado porque nunca se había probado asesoramiento
bajo rate limit; ahora atrapa `RateLimitError`/`APIError` y devuelve un mensaje en vez de tirar
(test en `tests/unit/test_proveedor_groq.py` y `tests/api/test_archivos.py`).

**[AJUSTE]** El extracto (HU-14) ahora también categoriza vía LLM (09/11/2026). HU-14 CA1 solo
pide identificar columnas de fecha, monto y descripción — nunca prometió categorizar — pero
`procesar_extracto` dejaba `categoria_id`/`medio_pago_id` en `null` para **todas** las filas sin
siquiera intentarlo, a diferencia de un comprobante o un resumen de tarjeta (HU-05/HU-06), que sí
le piden al LLM que categorice. El usuario señaló la inconsistencia: con un extracto de 18 filas,
tenía que elegir categoría y medio de pago a mano en las 18. Se agregó `ProveedorLLM.categorizar_filas`
(`descripciones: list[str], catalogo) -> list[CategoriaMedioPagoFila]`): un solo llamado al LLM con
todas las descripciones del extracto, devuelve una categoría y medio de pago sugeridos por línea,
**en el mismo orden** (si la cantidad devuelta no coincide con la cantidad pedida, se reintenta
una vez y después se abandona esa fila — nunca se inventa una correspondencia por las dudas). Es
una ayuda, no un requisito: si falla (rate limit, lo que sea), `procesar_extracto` igual importa
las filas sin categorizar, como antes de este cambio — nunca bloquea la importación completa por
esto. Las filas con una categoría sugerida que no está en el catálogo se comportan igual que en
comprobantes/resúmenes: quedan en `categoria_sugerida` para que el usuario elija una existente
(test en `tests/unit/test_proveedor_groq.py` y `tests/api/test_extracto.py`).

**[AJUSTE]** Bug encontrado en el ensayo de la demo (09/11/2026): en `RevisionResumen`, el total de
"N movimientos seleccionados · $..." mostraba literalmente **"$NaN"** con un resumen real
(`resumen-septiembre_anonimizado.pdf`), lo que hacía parecer que algo estaba roto (el usuario
pensó que había que reiniciar el backend). Causa: la misma clase de bug que ya se había encontrado
y corregido en el Dashboard — `ItemResumen.monto` llega del backend como **string** (`Decimal` →
string en el JSON), pero el frontend lo tipaba como `number`. `totalSeleccionado` se calculaba con
`acumulado + f.monto`: en JS, `+` entre un `number` y un `string` concatena en vez de sumar apenas
toca el primer string, así que el "total" terminaba siendo una concatenación de montos como
`"0660655.9438666.66..."`, y `Intl.NumberFormat().format()` de esa cadena da `NaN`. El formateo de
cada fila individual (`formatearMonto(fila.monto)`) no se notaba porque `Intl.NumberFormat` sí
coacciona un string individual a número correctamente — el bug solo aparecía en la suma. Se
corrigió: `ItemResumen.monto` ahora se tipa `string` (como realmente llega) y tanto
`formatearMonto` como el `reduce` del total y el payload que se manda a `POST /movimientos` pasan
`Number(fila.monto)` explícitamente. El mock de test usaba montos numéricos (`monto: 4599`), que
enmascaraba el bug igual que pasó con el Dashboard — se cambió a strings (test en
`RevisionResumen.test.tsx`, reproduce el "$NaN" exacto antes del fix).

**[AJUSTE]** Rotación a una segunda API key de Groq si la primera se queda sin tokens (09/11/2026).
El límite diario de Groq (ver AJUSTE anterior) es por cuenta, y durante los ensayos de la demo se
agotaba justo en medio de una prueba, sin forma de seguir probando hasta que se liberara. Se agregó
una variable opcional `GROQ_API_KEY_2` (`app/config.py`): si está configurada, `ProveedorGroq`
reintenta automáticamente con esa cuenta antes de darse por vencido, en vez de devolver
`MENSAJE_LIMITE_TASA` apenas la primera cuenta se queda sin tokens. El cambio se hizo en el punto
más bajo posible (`ProveedorGroq._llamar_rotando_api_key`, usado por `_completar_con_groq` y
`_completar_chat_con_groq`) para no tocar los cuatro métodos de retry de más arriba
(`clasificar_e_interpretar`, `extraer_movimientos`, `detectar_columnas`, `categorizar_filas`,
`responder`): cada uno sigue viendo, como antes, un solo `RateLimitError` si **todas** las cuentas
configuradas se quedaron sin tokens, y nada distinto si solo hay una cuenta configurada (no hay
regresión de comportamiento sin `GROQ_API_KEY_2`). Sin segunda key configurada, el comportamiento
es exactamente el de antes (test en `tests/unit/test_proveedor_groq.py`). Nota: usar varias cuentas
de Groq para esquivar su límite de uso gratuito puede no estar permitido por sus términos de
servicio — es una solución pensada para sostener los ensayos de la demo, no una decisión de
arquitectura para producción.

## 9. Análisis (dashboard)

Todo calculado sobre egresos confirmados del usuario, agregados por mes calendario.
- **Totales del mes** (HU-08 CA1): ingresos, egresos, saldo; variación vs. mes anterior.
- **Evolución** (CA2): últimos 6 meses.
- **Alertas** (HU-09): para cada categoría, `gasto_mes_actual > 1.30 * promedio(3 meses anteriores)`; requiere 3 meses previos con datos de esa categoría. Se recalcula en cada request al dashboard (no se cachea), lo que cumple CA4.
- **Proyección** (HU-12): `LinearRegression` sobre el total mensual de los últimos hasta 6 meses (x = índice de mes). Requiere ≥ 3 meses. Proyección negativa → se recorta a 0.
- **Anomalías** (HU-13): `IsolationForest(random_state=42, contamination=<configurable, default 0.15>)` sobre totales mensuales. Requiere ≥ 4 meses. Validar empíricamente con datos sintéticos que, con 6 meses donde uno duplica al resto, se marca solo ese mes; si con pocos puntos no es estable, documentar el ajuste y avisar (es material para el TFG).
  - **[AJUSTE]** Se validó empíricamente (Fase 9) que con tan pocos puntos (4 a 6 meses) `IsolationForest` marca casi siempre el mes más alejado del resto como anómalo (`predict() == -1`) aunque la diferencia sea mínima (ej. 2% por debajo del promedio) — el `contamination` configurado no cambia este comportamiento en este rango de tamaño de muestra. Se agregó una confirmación adicional: un mes que `IsolationForest` marca solo se reporta como anómalo si además se aparta un 30% o más del promedio de los otros meses de la ventana (`UMBRAL_DESVIACION_ANOMALIA` en `analisis.py`), mismo orden de magnitud que el umbral de alertas de HU-09. Con esto, series sin un outlier real no marcan ningún mes.

## 10. Asesoramiento (RAG)

- Ingesta (admin o `make seed`): PDF/texto → fragmentos de ~800 caracteres con solapamiento de 100 → embeddings con Ollama → colección ChromaDB `fragmentos_referencia` con metadatos `documento_id, titulo, indice_fragmento`. Se guarda la fila en `documentos_referencia` con `cantidad_fragmentos`.
- Consulta:
  - `CONSULTA_DATOS` (HU-10 CA1): se responde **solo** con datos del usuario. No se genera SQL con el LLM: el backend arma un resumen estructurado (totales por categoría y mes de los últimos 6 meses, más los movimientos del período que nombre la pregunta) y se lo pasa al modelo como contexto.
  - `CONSULTA_ASESORAMIENTO` (CA2): resumen del usuario + top-4 fragmentos recuperados.
  - Sin movimientos (CA4): solo fragmentos y la aclaración explícita en la respuesta.
- Fuentes (CA3): se guardan en `mensajes.fuentes` (jsonb), p. ej. `[{"tipo":"documento","titulo":"El hombre más rico de Babilonia","fragmento":14},{"tipo":"movimientos","desde":"2026-06","hasta":"2026-09"}]`, y se muestran como chips.
- Toda respuesta de asesoramiento incluye que es orientativa y no reemplaza a un profesional (riesgo R7).
- Historial de conversación (CA5): se persisten todos los mensajes; al modelo se le pasan los últimos 10.

**[AJUSTE]** Documentos de referencia reales: `make seed` carga tres fuentes citables (reemplazan un texto de ejemplo usado durante el desarrollo inicial, que no era una fuente real):
  - "OIT (2019). Economía familiar: herramientas para decidir mejor" (120 fragmentos)
  - "Riveros-Cardozo y Becker (2020). Introducción a las finanzas personales" (36 fragmentos)
  - "Tejeda-Hernández et al. (2021). Importancia de las finanzas personales en la salud financiera" (66 fragmentos)

  Los tres PDF tienen texto seleccionable (se leen con `pdfplumber` vía `extraer_texto_pdf`, sin necesidad de OCR).

**[AJUSTE]** Bug corregido: `ProveedorGroq.responder` armaba el mensaje al modelo usando `contexto_usuario` y la pregunta, pero **nunca incluía el texto de los `fragmentos` recuperados por Chroma** ni una instrucción explícita de ceñirse a esos datos — el parámetro se recibía pero no se usaba. Como los tests de API usan `FakeLLM` (que no reconstruye el prompt real), esto no se detectaba. Se corrigió para que el mensaje al modelo incluya los fragmentos y una instrucción del sistema de responder solo con los datos del usuario y los fragmentos provistos (test en `tests/unit/test_proveedor_groq.py`).

**[AJUSTE]** Bug encontrado en el ensayo de la demo (08/11/2026): las respuestas de asesoramiento
mostraban los encabezados internos "Datos del usuario" / "Fragmentos de documentación que aplican"
tal cual, citaban los fragmentos recuperados entre comillas en vez de sintetizar un consejo propio,
y venían en markdown (`**negrita**`) sin saltos de línea reales en vez de texto plano legible.
Causas: (1) `_completar_chat_con_groq` no fijaba `temperature` (quedaba en el default del
proveedor, ≈1, poco consistente) ni `max_tokens`; ahora usa `temperature=0.3, max_tokens=1024` —
más bajo que 0 porque es texto conversacional, no JSON estructurado, pero igual de consistente para
este caso. (2) El system prompt de `responder()` nunca decía explícitamente que "Datos del
usuario"/"Fragmentos de documentación" son contexto interno para el modelo, no secciones a
reproducir, ni prohibía citar los fragmentos textualmente o usar markdown. Se reforzó el prompt con
esas reglas y con pedirle una introducción que haga referencia a los movimientos del usuario antes
del consejo (test en `tests/unit/test_proveedor_groq.py`). De yapa, `.bub p` en el frontend ahora
usa `white-space: pre-wrap` para que los saltos de línea reales del modelo se vean.

**[AJUSTE]** Reforzado el 09/11/2026: pese a la instrucción de formato, de vez en cuando (no
seguido) igual respondía con `**negrita**` en markdown. Se cambió de "evitá el markdown" a una
prohibición explícita del carácter: "PROHIBIDO usar el caracter asterisco (*) en tu respuesta, para
lo que sea — ni negrita, ni viñetas, ni ningún otro uso", repitiendo la prohibición al final de la
regla de listas también. No elimina el riesgo por completo (es un modelo, no una regla dura), pero
reduce la frecuencia (test en `tests/unit/test_proveedor_groq.py`).

**[AJUSTE]** Layout: la página entera scrolleaba en vez de solo el panel de mensajes (09/11/2026).
`.frame` y `.side` usaban `min-height: 100vh` (un piso, no un techo) y `.main`/`.chat`/`.content`
no tenían altura acotada ni `overflow`, así que a medida que crecía una conversación o una lista
larga, crecía **toda la página** (sidebar, header y footer incluidos) y scrolleaba el documento
entero. Se cambió a `.frame { height: 100vh }` + `.side`/`.main { overflow: hidden }`, y se agregó
`overflow-y: auto` a `.chat` y a `.content` (usado por Dashboard/Historial/RevisionResumen) — ahora
sidebar, header y compositor quedan fijos, y solo el panel de contenido scrollea internamente.
Verificado renderizando el HTML real con el CSS compilado en un navegador (no es algo que jsdom
pueda verificar — no hace layout real).

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
GROQ_API_KEY, GROQ_API_KEY_2 (opcional, rotación si la primera se queda sin tokens),
GROQ_MODELO=openai/gpt-oss-120b,
OLLAMA_URL, OLLAMA_MODELO_EMBEDDINGS=nomic-embed-text,
CHROMA_URL, WHISPER_MODELO=small, ARCHIVOS_DIR, CORS_ORIGENES
```
