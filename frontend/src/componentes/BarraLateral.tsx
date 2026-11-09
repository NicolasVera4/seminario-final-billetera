import { useEffect, useState, type ReactNode } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { obtenerUsuarioActual } from '../api/auth'
import { borrarToken } from '../api/cliente'
import {
  IconoChat,
  IconoDashboard,
  IconoDocumento,
  IconoHistorial,
  IconoLogo,
  IconoSalir,
  IconoUsuarios,
} from './iconos'

interface Usuario {
  nombre: string
  correo: string
  rol: string
}

function claseActiva(actual: string, ruta: string) {
  return actual === ruta ? 'on' : ''
}

function iniciales(nombre: string) {
  return nombre
    .trim()
    .split(/\s+/)
    .map((parte) => parte[0])
    .slice(0, 2)
    .join('')
    .toUpperCase()
}

export default function BarraLateral({ children }: { children?: ReactNode }) {
  const ubicacion = useLocation()
  const navegar = useNavigate()
  const [usuario, setUsuario] = useState<Usuario | null>(null)

  useEffect(() => {
    obtenerUsuarioActual()
      .then(setUsuario)
      .catch(() => {})
  }, [])

  function cerrarSesion() {
    borrarToken()
    navegar('/login')
  }

  return (
    <aside className="side">
      <div className="brand">
        <div className="logo">
          <IconoLogo />
        </div>
        <b>Qash</b>
      </div>
      <nav className="nav">
        {usuario?.rol === 'ADMINISTRADOR' ? (
          <>
            <Link to="/admin/documentos" className={claseActiva(ubicacion.pathname, '/admin/documentos')}>
              <IconoDocumento />
              Documentación
            </Link>
            <Link to="/admin/usuarios" className={claseActiva(ubicacion.pathname, '/admin/usuarios')}>
              <IconoUsuarios />
              Usuarios
            </Link>
          </>
        ) : (
          <>
            <Link to="/dashboard" className={claseActiva(ubicacion.pathname, '/dashboard')}>
              <IconoDashboard />
              Dashboard
            </Link>
            <Link
              to="/chat"
              className={ubicacion.pathname === '/' || ubicacion.pathname === '/chat' ? 'on' : ''}
            >
              <IconoChat />
              Chat
            </Link>
            <Link to="/historial" className={claseActiva(ubicacion.pathname, '/historial')}>
              <IconoHistorial />
              Historial
            </Link>
          </>
        )}
      </nav>
      {children}
      {usuario && (
        <div className="me">
          <div className="av">{iniciales(usuario.nombre)}</div>
          <div className="datos">
            <b>{usuario.nombre}</b>
            <small>{usuario.correo}</small>
          </div>
          <button type="button" title="Cerrar sesión" onClick={cerrarSesion}>
            <IconoSalir />
          </button>
        </div>
      )}
    </aside>
  )
}
