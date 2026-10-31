import { solicitar } from './cliente'

export interface ItemCatalogo {
  id: number
  nombre: string
}

export interface Catalogos {
  categorias: ItemCatalogo[]
  medios_pago: ItemCatalogo[]
  origenes: ItemCatalogo[]
}

export function obtenerCatalogos(): Promise<Catalogos> {
  return solicitar<Catalogos>('/catalogos')
}
