import type { ReactNode } from 'react'
import BarraLateral from './BarraLateral'
import RutaProtegida from './RutaProtegida'

interface LayoutProps {
  children: ReactNode
  sidebarExtra?: ReactNode
}

export default function Layout({ children, sidebarExtra }: LayoutProps) {
  return (
    <RutaProtegida>
      <div className="frame">
        <BarraLateral>{sidebarExtra}</BarraLateral>
        <div className="main">{children}</div>
      </div>
    </RutaProtegida>
  )
}
