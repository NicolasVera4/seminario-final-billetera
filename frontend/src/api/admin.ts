import { solicitar } from './cliente'

export interface DocumentoReferencia {
  id: number
  titulo: string
  cantidad_fragmentos: number
  creado_en: string
}

export function listarDocumentos(): Promise<DocumentoReferencia[]> {
  return solicitar<DocumentoReferencia[]>('/admin/documentos')
}

export function cargarDocumento(titulo: string, archivo: File): Promise<DocumentoReferencia> {
  const formData = new FormData()
  formData.append('archivo', archivo)
  const parametros = new URLSearchParams({ titulo })
  return solicitar<DocumentoReferencia>(`/admin/documentos?${parametros}`, {
    method: 'POST',
    body: formData,
  })
}

export function eliminarDocumento(id: number): Promise<void> {
  return solicitar<void>(`/admin/documentos/${id}`, { method: 'DELETE' })
}

export interface AdminUsuario {
  id: number
  nombre: string
  correo: string
  activo: boolean
  bloqueado_hasta: string | null
}

export interface AdminUsuarioEntrada {
  nombre?: string
  correo?: string
  activo?: boolean
  desbloquear?: boolean
}

export function listarUsuarios(): Promise<AdminUsuario[]> {
  return solicitar<AdminUsuario[]>('/admin/usuarios')
}

export function editarUsuario(id: number, datos: AdminUsuarioEntrada): Promise<AdminUsuario> {
  return solicitar<AdminUsuario>(`/admin/usuarios/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(datos),
  })
}
