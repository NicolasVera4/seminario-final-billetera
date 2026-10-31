const BASE_URL = '/api'

let manejadorVencimiento: (() => void) | null = null

export function alVencerSesion(fn: () => void) {
  manejadorVencimiento = fn
}

const CLAVE_TOKEN = 'qash_token'

export function guardarToken(token: string) {
  localStorage.setItem(CLAVE_TOKEN, token)
}

export function obtenerToken(): string | null {
  return localStorage.getItem(CLAVE_TOKEN)
}

export function borrarToken() {
  localStorage.removeItem(CLAVE_TOKEN)
}

export class ErrorApi extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

export async function solicitar<T>(ruta: string, opciones: RequestInit = {}): Promise<T> {
  const respuesta = await fetch(`${BASE_URL}${ruta}`, opciones)
  const cuerpo = await respuesta.json().catch(() => null)

  if (!respuesta.ok) {
    throw new ErrorApi(respuesta.status, cuerpo?.detail ?? 'Error inesperado.')
  }

  return cuerpo as T
}
