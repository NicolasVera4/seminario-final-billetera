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

## Conjunto completo (30 entradas) — 2026-11-05

Las entradas 11 a 30 se agregaron en la Fase 12: mensajes sintéticos (no relevados de
usuarios reales) escritos para cubrir más categorías, medios de pago, jerga rioplatense
("lucas", "palos") y las dos intenciones de consulta (`CONSULTA_DATOS`,
`CONSULTA_ASESORAMIENTO`), que las primeras 10 no ejercitaban. Mismo modelo
(`openai/gpt-oss-120b`).

| Campo | Aciertos |
|---|---|
| intención | 30/30 (100%) |
| monto | 19/20 (95%) |
| tipo | 20/20 (100%) |
| medio de pago | 18/18 (100%) |
| categoría | 15/15 (100%) |
| faltantes (¿incluye lo obligatorio?) | 3/3 (100%) |

Nota de calibración: el único error de monto fue "pagué 2 palos por el auto nuevo,
transferencia" → el modelo interpretó 2000 en vez de 2.000.000. "Palos" (un millón en
jerga rioplatense) no lo resuelve bien; en cambio "lucas" (mil) sí lo interpretó
correctamente en todos los casos del conjunto ("gasté 3 lucas en el kiosco" → 3000).
No se corrigió nada en el prompt para este caso puntual: documentar la limitación real
del modelo es justamente el objetivo de esta métrica (riesgo R2 del TFG), no maquillarla.
