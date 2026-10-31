import { solicitar } from './cliente'

export interface MovimientoEntrada {
  monto: number
  fecha: string
  tipo: 'INGRESO' | 'EGRESO'
  descripcion: string
  categoria_id: number | null
  medio_pago_id: number | null
  origen?: string
  conversacion_id?: number | null
}

export interface ResultadoValidacion {
  errores: string[]
  advertencias: string[]
}

export interface MovimientoSalida {
  id: number
  monto: number
  fecha: string
  tipo: 'INGRESO' | 'EGRESO'
  descripcion: string
  categoria_id: number | null
  medio_pago_id: number | null
  origen_id: number
  creado_en: string
}

export function validarMovimiento(datos: MovimientoEntrada): Promise<ResultadoValidacion> {
  return solicitar<ResultadoValidacion>('/movimientos/validar', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(datos),
  })
}

export function guardarMovimientos(datos: MovimientoEntrada[]): Promise<MovimientoSalida[]> {
  return solicitar<MovimientoSalida[]>('/movimientos', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(datos),
  })
}
