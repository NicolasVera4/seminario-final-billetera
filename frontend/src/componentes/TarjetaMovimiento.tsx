import type { Borrador } from '../api/chat'

export interface TarjetaMovimientoProps {
  borrador: Borrador
  onGuardado?: () => void
  onDescartado?: () => void
}

export default function TarjetaMovimiento({ borrador }: TarjetaMovimientoProps) {
  return <div>{borrador.descripcion}</div>
}
