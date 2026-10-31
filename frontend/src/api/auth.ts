import { guardarToken, solicitar } from './cliente'

export interface RegistroEntrada {
  nombre: string
  correo: string
  contrasena: string
}

export interface LoginEntrada {
  correo: string
  contrasena: string
}

export interface UsuarioSalida {
  id: number
  nombre: string
  correo: string
  rol: string
}

interface TokenSalida {
  access_token: string
  token_type: string
}

export function registrar(datos: RegistroEntrada): Promise<UsuarioSalida> {
  return solicitar<UsuarioSalida>('/auth/registro', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(datos),
  })
}

export async function iniciarSesion(datos: LoginEntrada): Promise<TokenSalida> {
  const resultado = await solicitar<TokenSalida>('/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(datos),
  })
  guardarToken(resultado.access_token)
  return resultado
}
