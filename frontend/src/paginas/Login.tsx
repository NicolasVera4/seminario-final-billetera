import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { iniciarSesion, obtenerUsuarioActual } from '../api/auth'
import { IconoAlerta, IconoLogo } from '../componentes/iconos'

const ERROR_LOGIN = 'El correo o la contraseña no son correctos. Revisalos e intentá de nuevo.'

export default function Login() {
  const navegar = useNavigate()
  const [correo, setCorreo] = useState('')
  const [contrasena, setContrasena] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [enviando, setEnviando] = useState(false)

  async function manejarEnvio(evento: FormEvent) {
    evento.preventDefault()
    setError(null)
    setEnviando(true)
    try {
      await iniciarSesion({ correo, contrasena })
      const usuario = await obtenerUsuarioActual()
      navegar(usuario.rol === 'ADMINISTRADOR' ? '/admin/documentos' : '/')
    } catch {
      setError(ERROR_LOGIN)
    } finally {
      setEnviando(false)
    }
  }

  return (
    <div className="auth">
      <div className="left">
        <div className="brand">
          <div className="logo">
            <IconoLogo />
          </div>
          <b>Qash</b>
        </div>
        <div className="pitch">
          <h2>Anotá tus gastos como se los contarías a alguien.</h2>
          <p>
            Escribilos, dictalos o subí el comprobante. Qash los ordena por categoría y te avisa cuando algo
            se sale de lo habitual.
          </p>
          <div className="demo">
            <div className="u">
              <span className="b">Gasté 15000 en el súper con débito</span>
            </div>
            <div className="mini">
              <div>
                <span>Monto</span>
                <b>$15.000,00</b>
              </div>
              <div>
                <span>Medio de pago</span>
                <b>Débito</b>
              </div>
              <div>
                <span>Categoría</span>
                <b>Supermercado</b>
              </div>
              <div>
                <span>Fecha</span>
                <b>27/09/2026</b>
              </div>
            </div>
          </div>
        </div>
      </div>
      <div className="right">
        <div className="form">
          <h1>Iniciar sesión</h1>
          <p className="lead">Ingresá con el correo con el que creaste tu cuenta.</p>
          {error && (
            <div className="alert" role="alert">
              <IconoAlerta />
              <span>{error}</span>
            </div>
          )}
          <form onSubmit={manejarEnvio} noValidate>
            <div className="fg">
              <label htmlFor="correo">Correo electrónico</label>
              <input
                className="inp"
                id="correo"
                type="email"
                value={correo}
                onChange={(evento) => setCorreo(evento.target.value)}
              />
            </div>

            <div className="fg">
              <label htmlFor="contrasena">Contraseña</label>
              <input
                className="inp"
                id="contrasena"
                type="password"
                value={contrasena}
                onChange={(evento) => setContrasena(evento.target.value)}
              />
            </div>

            <button className="btn primary" type="submit" disabled={enviando}>
              Iniciar sesión
            </button>
          </form>
          <p className="alt">
            ¿No tenés cuenta? <Link to="/registro">Crear cuenta</Link>
          </p>
        </div>
      </div>
    </div>
  )
}
