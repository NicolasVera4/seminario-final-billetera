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
  mensaje_id?: number | null
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

export interface FiltrosHistorial {
  desde?: string
  hasta?: string
  categoria_id?: number
  tipo?: 'INGRESO' | 'EGRESO'
  medio_pago_id?: number
  q?: string
  pagina?: number
  por_pagina?: number
}

export interface MovimientoListado {
  id: number
  fecha: string
  descripcion: string
  categoria: string | null
  medio_pago: string | null
  origen: string
  monto: number
  tipo: 'INGRESO' | 'EGRESO'
}

export interface Historial {
  items: MovimientoListado[]
  total: number
  pagina: number
  por_pagina: number
}

export function listarMovimientos(filtros: FiltrosHistorial = {}): Promise<Historial> {
  const params = new URLSearchParams()
  for (const [clave, valor] of Object.entries(filtros)) {
    if (valor !== undefined && valor !== '') {
      params.set(clave, String(valor))
    }
  }
  const query = params.toString()
  return solicitar<Historial>(`/movimientos${query ? `?${query}` : ''}`)
}
