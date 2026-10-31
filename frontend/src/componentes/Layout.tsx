import type { ReactNode } from 'react'
import BarraLateral from './BarraLateral'
import RutaProtegida from './RutaProtegida'

export default function Layout({ children }: { children: ReactNode }) {
  return (
    <RutaProtegida>
      <BarraLateral />
      {children}
    </RutaProtegida>
  )
}
