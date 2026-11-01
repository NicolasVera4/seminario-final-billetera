import { solicitar } from './cliente'

export interface TotalMes {
  monto: number
  variacion_texto: string
}

export interface PuntoEvolucion {
  anio: number
  mes: number
  ingresos: number
  egresos: number
}

export interface CategoriaDistribucion {
  categoria: string
  categoria_id: number
  monto: number
  porcentaje: number
}

export interface Alerta {
  categoria: string
  categoria_id: number
  porcentaje: number
  monto_actual: number
  promedio: number
}

export interface Proyeccion {
  datos_suficientes: boolean
  anio: number | null
  mes: number | null
  monto: number | null
}

export interface MesAnomalo {
  anio: number
  mes: number
  monto: number
  promedio_otros_meses: number
  porcentaje_sobre_promedio: number
}

export interface Anomalias {
  datos_suficientes: boolean
  meses: MesAnomalo[]
}

export interface Dashboard {
  anio: number
  mes: number
  ingresos: TotalMes
  egresos: TotalMes
  saldo: number
  evolucion: PuntoEvolucion[]
  distribucion_categorias: CategoriaDistribucion[]
  alertas: Alerta[]
  proyeccion: Proyeccion
  anomalias: Anomalias
  hay_movimientos: boolean
}

export function obtenerDashboard(mes?: string): Promise<Dashboard> {
  return solicitar<Dashboard>(`/dashboard${mes ? `?mes=${mes}` : ''}`)
}
