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
  /** Como todo monto que devuelve el backend (Decimal -> string en el JSON). Nunca sumar/restar
   * sin pasar por Number(...) primero: con `+` entre number y string, JS concatena en vez de
   * sumar. */
  monto: string
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

interface IdsConversacion {
  conversacion_id: number
  mensaje_id: number
}

export type AdjuntoRespuesta =
  | ({ modo: 'COMPROBANTE' } & ComprobanteRespuesta & IdsConversacion)
  | ({ modo: 'RESUMEN' } & ResumenRespuesta & IdsConversacion)
  | ({ modo: 'EXTRACTO' } & ExtractoRespuesta & IdsConversacion)

export function subirAdjunto(archivo: File, conversacionId: number | null): Promise<AdjuntoRespuesta> {
  const formData = new FormData()
  formData.append('archivo', archivo)
  if (conversacionId != null) {
    formData.append('conversacion_id', String(conversacionId))
  }
  return solicitar<AdjuntoRespuesta>('/archivos/adjuntar', {
    method: 'POST',
    body: formData,
  })
}
