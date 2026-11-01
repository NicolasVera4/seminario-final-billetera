import type { Borrador } from './chat'
import { solicitar } from './cliente'

export interface ComprobanteRespuesta {
  borrador: Borrador | null
  archivo_ref: string | null
  comprobante_tipo: string | null
  mensaje: string
}

export function subirComprobante(archivo: File): Promise<ComprobanteRespuesta> {
  const formData = new FormData()
  formData.append('archivo', archivo)
  return solicitar<ComprobanteRespuesta>('/archivos/comprobante', {
    method: 'POST',
    body: formData,
  })
}

export interface ItemResumen {
  monto: number
  fecha: string
  tipo: 'INGRESO' | 'EGRESO'
  descripcion: string
  categoria_id: number | null
  categoria_sugerida: string | null
  medio_pago_id: number | null
  cuota_numero: number | null
  cuota_total: number | null
  errores: string[]
  posible_duplicado: boolean
}

export interface ResumenRespuesta {
  items: ItemResumen[]
  archivo_ref: string
  comprobante_tipo: string
  paginas_leidas: number
}

export function subirResumen(archivo: File): Promise<ResumenRespuesta> {
  const formData = new FormData()
  formData.append('archivo', archivo)
  return solicitar<ResumenRespuesta>('/archivos/resumen', {
    method: 'POST',
    body: formData,
  })
}

export interface ExtractoRespuesta {
  items: ItemResumen[]
  archivo_ref: string
  filas_descartadas: number
}

export function subirExtracto(archivo: File): Promise<ExtractoRespuesta> {
  const formData = new FormData()
  formData.append('archivo', archivo)
  return solicitar<ExtractoRespuesta>('/archivos/extracto', {
    method: 'POST',
    body: formData,
  })
}
