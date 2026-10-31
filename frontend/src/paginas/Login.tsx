import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { iniciarSesion } from '../api/auth'

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
      navegar('/')
    } catch {
      setError(ERROR_LOGIN)
    } finally {
      setEnviando(false)
    }
  }

  return (
    <div>
      <h1>Iniciar sesión</h1>
      <p>Ingresá con el correo con el que creaste tu cuenta.</p>
      {error && <p role="alert">{error}</p>}
      <form onSubmit={manejarEnvio} noValidate>
        <label htmlFor="correo">Correo electrónico</label>
        <input
          id="correo"
          type="email"
          value={correo}
          onChange={(evento) => setCorreo(evento.target.value)}
        />

        <label htmlFor="contrasena">Contraseña</label>
        <input
          id="contrasena"
          type="password"
          value={contrasena}
          onChange={(evento) => setContrasena(evento.target.value)}
        />

        <button type="submit" disabled={enviando}>
          Iniciar sesión
        </button>
      </form>
      <p>
        ¿No tenés cuenta? <Link to="/registro">Crear cuenta</Link>
      </p>
    </div>
  )
}
