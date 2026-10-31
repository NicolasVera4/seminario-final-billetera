# Qash — Instrucciones para Claude Code

Qash es un asistente web de finanzas personales basado en modelos de lenguaje. Es el prototipo del Trabajo Final de Graduación de Luciano Vera (Ingeniería en Software, Universidad Siglo 21).

El repositorio arranca vacío: todo el código se escribe acá desde cero. No traigas ni copies código de otros proyectos o repositorios.

## Fuentes de verdad (leer antes de cada fase)

| Archivo | Qué contiene | Prioridad ante conflicto |
|---|---|---|
| `docs/PRD.md` | Qué hace el sistema: historias de usuario y criterios de aceptación (extraído del Entregable 3) | 1 — manda sobre todo |
| `docs/TRD.md` | Cómo se construye: arquitectura, modelo de datos, contratos, reglas | 2 |
| `docs/PLAN.md` | Fases, orden, tests por fase y estado de avance | 3 |
| `docs/mockups/` | Capturas de las pantallas diseñadas (Figuras 7 a 13 del TFG) | Referencia visual |
| `docs/entregable3.pdf` | Documento completo del TFG | Contexto |

Si encontrás una contradicción entre estos archivos, o un criterio de aceptación ambiguo, **frená y preguntá**. No asumas.

## Forma de trabajo: TDD por fases (obligatorio)

Se trabaja **una fase por vez**, en el orden de `docs/PLAN.md`. Cada fase sigue estos pasos sin saltear ninguno:

1. **Plan.** Leé la fase en `PLAN.md` y los criterios de aceptación de sus historias en `PRD.md`. Presentá en pocas líneas qué tests vas a escribir y qué archivos vas a tocar. Esperá el OK.
2. **Rojo.** Escribí todos los tests de la fase (backend y frontend). Cada criterio de aceptación tiene al menos un test, nombrado con su ID: `test_hu03_ca2_mensaje_sin_fecha_toma_la_fecha_del_dia`. Corré la suite y **mostrá que fallan por la razón esperada** (no por errores de import o de sintaxis). Commit: `test(HU-03): criterios de aceptación en rojo`.
3. **Verde.** Implementá lo mínimo para que pasen. Corré la suite completa (no solo los tests nuevos) hasta que todo esté en verde. Commit: `feat(HU-03): ...`.
4. **Refactor.** Limpiá duplicaciones y nombres sin cambiar comportamiento; la suite sigue en verde. Commit: `refactor(...)` si hubo cambios.
5. **Cierre.** Marcá la fase en `PLAN.md`, escribí un resumen de 5 a 10 líneas (qué se hizo, decisiones tomadas, pendientes) y **frená**. No arranques la fase siguiente sin OK.

### Reglas sobre los tests
- **Nunca modifiques un test para que pase.** Si creés que un test está mal, explicá por qué y pedí permiso antes de cambiarlo.
- No borres ni saltees tests (`skip`, `xfail`) sin permiso.
- Los tests unitarios **no llaman a servicios externos**: Groq, Ollama y faster-whisper se reemplazan por dobles (`FakeLLM`, `FakeEmbedder`, `FakeTranscriptor`). Los tests que sí usan el servicio real se marcan `@pytest.mark.integracion` y no corren por defecto.
- Cada bug que aparezca se reproduce primero con un test en rojo.

## Convenciones

- **Idioma del dominio: español.** Tablas, columnas, modelos, schemas, endpoints y variables de dominio en español y sin tildes (`movimientos`, `medio_pago_id`, `/api/movimientos`). Lo técnico genérico puede quedar en inglés (`router`, `session`, `config`).
- Textos de la interfaz en español rioplatense, como en los mockups ("Escribí un gasto…", "Elegí una categoría").
- Python 3.12, tipado completo, Pydantic v2, SQLAlchemy 2.0 (estilo `Mapped[]`), Alembic para migraciones.
- Frontend: React + Vite + TypeScript, Recharts, llamadas a la API centralizadas en `frontend/src/api/`.
- Montos con `Decimal` en backend (`NUMERIC(14,2)` en base); nunca `float` para dinero.
- Commits en formato convencional, en español.
- Nada de secretos en el repo: todo por variables de entorno (`.env`, con `.env.example` versionado).

## Comandos

```bash
make up            # levanta la pila con Docker Compose
make test          # backend + frontend, sin tests de integración
make test-back     # pytest
make test-front    # vitest
make test-int      # tests marcados como integracion (requiere GROQ_API_KEY y Ollama)
make migrar        # alembic upgrade head
make seed          # carga catálogos y datos de demo
```

Si algún comando todavía no existe, crearlo es parte de la Fase 0.

## Qué no hacer
- No agregar dependencias que no estén en el TRD sin preguntar (el stack está declarado en el TFG y cambiarlo obliga a cambiar el documento).
- No enviar nombre ni correo del usuario al modelo de lenguaje.
- No guardar un movimiento sin confirmación explícita del usuario.
