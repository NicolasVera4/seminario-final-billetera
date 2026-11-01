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
