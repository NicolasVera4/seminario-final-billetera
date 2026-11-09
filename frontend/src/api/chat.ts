import { solicitar } from './cliente'

export interface Conversacion {
  id: number
  titulo: string | null
  creado_en: string
  actualizado_en: string
}

export interface FuenteDocumento {
  tipo: 'documento'
  titulo: string
  fragmento: number
}

export interface FuenteMovimientos {
  tipo: 'movimientos'
  desde: string
  hasta: string
}

export type Fuente = FuenteDocumento | FuenteMovimientos

export interface Mensaje {
  id: number
  rol: 'USUARIO' | 'ASISTENTE'
  contenido: string
  fuentes: Fuente[] | null
  transcripto?: boolean
  creado_en: string
  /** Presente cuando el movimiento que propuso este mensaje ya se guardó (para reconstruir el
   * historial al navegar a una conversación vieja). */
  movimiento?: Borrador | null
}

export interface Borrador {
  monto: number
  fecha: string
  tipo: 'INGRESO' | 'EGRESO'
  descripcion: string
  categoria_id: number | null
  categoria_sugerida: string | null
  medio_pago_id: number | null
}

export interface ChatRespuesta {
  conversacion_id: number
  mensaje: Mensaje
  borrador: Borrador | null
}

export function listarConversaciones(): Promise<Conversacion[]> {
  return solicitar<Conversacion[]>('/chat/conversaciones')
}

export function obtenerConversacion(id: number): Promise<Mensaje[]> {
  return solicitar<Mensaje[]>(`/chat/conversaciones/${id}`)
}

export function enviarMensaje(
  texto: string,
  conversacionId: number | null,
  transcripto = false,
): Promise<ChatRespuesta> {
  return solicitar<ChatRespuesta>('/chat/mensajes', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ texto, conversacion_id: conversacionId, transcripto }),
  })
}
