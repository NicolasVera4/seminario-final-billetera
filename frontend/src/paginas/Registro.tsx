import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { registrar } from '../api/auth'
import { ErrorApi } from '../api/cliente'

const OBLIGATORIO = 'Este campo es obligatorio.'
const CORREO_EXISTE = 'Ya existe una cuenta con este correo. Iniciá sesión o usá otro correo.'
const CONTRASENAS_NO_COINCIDEN = 'Las contraseñas no coinciden.'

export default function Registro() {
  const navegar = useNavigate()
  const [nombre, setNombre] = useState('')
  const [correo, setCorreo] = useState('')
  const [contrasena, setContrasena] = useState('')
  const [repetirContrasena, setRepetirContrasena] = useState('')
  const [errorNombre, setErrorNombre] = useState<string | null>(null)
  const [errorCorreo, setErrorCorreo] = useState<string | null>(null)
  const [errorContrasena, setErrorContrasena] = useState<string | null>(null)
  const [enviando, setEnviando] = useState(false)

  async function manejarEnvio(evento: FormEvent) {
    evento.preventDefault()
    setErrorNombre(null)
    setErrorCorreo(null)
    setErrorContrasena(null)

    let hayError = false
    if (!nombre.trim()) {
      setErrorNombre(OBLIGATORIO)
      hayError = true
    }
    if (!correo.trim()) {
      setErrorCorreo(OBLIGATORIO)
      hayError = true
    }
    if (!contrasena.trim()) {
      setErrorContrasena(OBLIGATORIO)
      hayError = true
    }
    if (!hayError && contrasena !== repetirContrasena) {
      setErrorContrasena(CONTRASENAS_NO_COINCIDEN)
      hayError = true
    }
    if (hayError) return

    setEnviando(true)
    try {
      await registrar({ nombre, correo, contrasena })
      navegar('/login')
    } catch (error) {
      if (error instanceof ErrorApi && error.status === 409) {
        setErrorCorreo(CORREO_EXISTE)
      } else {
        setErrorCorreo('No se pudo crear la cuenta. Probá de nuevo.')
      }
    } finally {
      setEnviando(false)
    }
  }

  return (
    <div>
      <h1>Crear cuenta</h1>
      <p>Tus movimientos quedan guardados en tu cuenta y solo vos podés verlos.</p>
      <form onSubmit={manejarEnvio} noValidate>
        <label htmlFor="nombre">Nombre</label>
        <input id="nombre" value={nombre} onChange={(evento) => setNombre(evento.target.value)} />
        {errorNombre && <p role="alert">{errorNombre}</p>}

        <label htmlFor="correo">Correo electrónico</label>
        <input
          id="correo"
          type="email"
          value={correo}
          onChange={(evento) => setCorreo(evento.target.value)}
        />
        {errorCorreo && <p role="alert">{errorCorreo}</p>}

        <label htmlFor="contrasena">Contraseña</label>
        <input
          id="contrasena"
          type="password"
          value={contrasena}
          onChange={(evento) => setContrasena(evento.target.value)}
        />
        <p>Mínimo 8 caracteres.</p>

        <label htmlFor="repetir-contrasena">Repetir contraseña</label>
        <input
          id="repetir-contrasena"
          type="password"
          value={repetirContrasena}
          onChange={(evento) => setRepetirContrasena(evento.target.value)}
        />
        {errorContrasena && <p role="alert">{errorContrasena}</p>}

        <button type="submit" disabled={enviando}>
          Crear cuenta
        </button>
      </form>
      <p>
        ¿Ya tenés cuenta? <Link to="/login">Iniciar sesión</Link>
      </p>
    </div>
  )
}
