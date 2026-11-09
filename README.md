# Qash

Asistente de finanzas personales. Prototipo del Trabajo Final de Graduación de Luciano Vera
(Ingeniería en Software, Universidad Siglo 21).

## Requisitos

- Docker y Docker Compose
- Python 3.12 (para correr tests, migraciones y el seed desde `backend/.venv`)
- Node 20+ (para el frontend)
- GNU Make
- Para correr los tests de backend fuera de Docker: `tesseract-ocr`, `tesseract-ocr-spa` y
  `poppler-utils` instalados en el sistema (ya vienen en la imagen de `backend/Dockerfile`; si se
  corre todo con `docker compose up`, no hace falta instalarlos aparte)

## Variables de entorno

Copiar `.env.example` a `.env` en la raíz del repo (`backend/.env` es un symlink al mismo archivo):

```bash
cp .env.example .env
```

Completar `GROQ_API_KEY` con una clave propia de [Groq](https://console.groq.com) — el resto de
las variables ya tienen valores por defecto que funcionan en desarrollo. **Nunca commitear `.env`**
(ya está en `.gitignore`).

| Variable | Para qué es |
|---|---|
| `DATABASE_URL` / `DATABASE_URL_TEST` | Conexión a Postgres (app y tests) |
| `JWT_SECRETO` | Firma de los tokens de sesión |
| `GROQ_API_KEY` | Clave de Groq (interpretación de mensajes y asesoramiento) |
| `GROQ_API_KEY_2` | Opcional. Segunda cuenta de Groq: si la primera se queda sin tokens (límite diario), se reintenta automáticamente con esta antes de avisarle al usuario |
| `GROQ_MODELO` | Modelo de Groq a usar (`openai/gpt-oss-120b` por defecto) |
| `OLLAMA_URL` / `OLLAMA_MODELO_EMBEDDINGS` | Embeddings para el asesoramiento con RAG |
| `CHROMA_URL` | Base vectorial de los documentos de referencia |
| `WHISPER_MODELO` | Modelo de transcripción de audio (voz) |
| `ARCHIVOS_DIR` | Dónde se guardan los comprobantes/resúmenes/extractos subidos |
| `CORS_ORIGENES` | Orígenes permitidos para llamar a la API (el frontend en desarrollo) |

## Puesta en marcha

1. Levantar la infraestructura (base de datos, Chroma y Ollama):

   ```bash
   docker compose up -d db chroma ollama
   ```

2. Descargar el modelo de embeddings en Ollama (una sola vez; el primer `docker compose up` lo
   crea vacío):

   ```bash
   docker compose exec ollama ollama pull nomic-embed-text
   ```

3. Crear el entorno de Python del backend (si no existe) e instalar dependencias:

   ```bash
   cd backend && python3.12 -m venv .venv && . .venv/bin/activate && pip install -e ".[dev]"
   ```

4. Correr las migraciones:

   ```bash
   make migrar
   ```

5. Cargar datos. Para empezar de cero (catálogos + los 3 documentos de referencia del RAG):

   ```bash
   make seed
   ```

   Para una demo con datos de ejemplo (catálogos, documentos de referencia, un usuario con 6 meses
   de movimientos ficticios y un administrador — ver "Credenciales de demo" abajo):

   ```bash
   make seed-demo
   ```

6. Levantar el backend y el frontend:

   ```bash
   docker compose up backend frontend
   ```

## Entrar al sistema

- Frontend: http://localhost:5173
- Backend (API): http://localhost:8000/api

### Credenciales de demo

`make seed-demo` crea estas dos cuentas (datos y contraseñas de ejemplo, no reales):

| Rol | Correo | Contraseña |
|---|---|---|
| Usuario | `nicolas.vera@gmail.com` | `UsuarioDemo2026` |
| Administrador | `nicolas.vera+admin@gmail.com` | `AdminDemo2026` |

El usuario de demo tiene 6 meses de movimientos ficticios (mayo a octubre de 2026: ingresos,
gastos por categoría) armados para mostrar un mes con gasto anómalo, una alerta por categoría y
una proyección de gasto con tendencia — son datos ilustrativos para la demo, no reales. El límite
queda fijo en el 31/10/2026 a propósito, sin importar cuándo se corra `make seed-demo`: así, lo que
se cargue en vivo durante la demo (con fecha del día real) nunca se mezcla con los datos de
prueba — queda siempre en un mes posterior y separado. `make seed-demo` también borra las
conversaciones de chat que haya probado la cuenta demo (texto, voz, comprobantes) — volver a
correrlo deja todo, movimientos y chat, en el estado limpio inicial.

## Tests

```bash
make test        # backend + frontend, sin tests de integración
make test-back    # solo backend
make test-front    # solo frontend
make test-int      # tests de integración (necesitan GROQ_API_KEY y Ollama/Chroma corriendo)
make coverage       # suite de backend con reporte de cobertura
```

## Documentación

- `docs/PRD.md` — qué hace el sistema (historias de usuario y criterios de aceptación)
- `docs/TRD.md` — cómo está construido (arquitectura, modelo de datos, decisiones `[AJUSTE]`)
- `docs/PLAN.md` — fases de desarrollo y su estado
- `docs/resultados_llm.md` — evaluación de la interpretación del LLM contra el conjunto de oro
