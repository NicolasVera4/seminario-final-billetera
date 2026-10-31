# Resultados de interpretación con el LLM

## Primeras 10 entradas de `conjunto_oro.yaml` — 2026-10-31

Modelo: `openai/gpt-oss-120b` (Groq). Ver `[AJUSTE]` en `docs/TRD.md` §1: el modelo
original del TFG (`llama-3.3-70b-versatile`) fue discontinuado por Groq.

| Campo | Aciertos |
|---|---|
| intención | 10/10 (100%) |
| monto | 7/7 (100%) |
| tipo | 7/7 (100%) |
| medio de pago | 6/6 (100%) |
| categoría | 6/6 (100%) |
| faltantes (¿incluye lo obligatorio?) | 1/1 (100%) |

Nota de calibración: en "compré ropa" (CA3, sin monto) el modelo marcó
`faltantes: ["monto", "fecha", "medio_pago"]` en vez de solo `["monto"]`. No es un
error — el sistema solo exige que `"monto"` esté presente en `faltantes` para
pedirlo antes de continuar (`fecha` igual cae en `hoy` y `medio_pago` igual queda
pendiente de elegir en la Fase 3) — pero el test se ajustó para comparar por
subconjunto en vez de igualdad exacta de los faltantes.

El conjunto completo (~30 entradas) queda para la Fase 12.
