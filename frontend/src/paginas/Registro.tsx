import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { registrar } from '../api/auth'
import { ErrorApi } from '../api/cliente'
import { IconoAlerta, IconoLogo } from '../componentes/iconos'

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
          <h1>Crear cuenta</h1>
          <p className="lead">Tus movimientos quedan guardados en tu cuenta y solo vos podés verlos.</p>
          <form onSubmit={manejarEnvio} noValidate>
            <div className="fg">
              <label htmlFor="nombre">Nombre</label>
              <input
                className={`inp${errorNombre ? ' bad' : ''}`}
                id="nombre"
                value={nombre}
                onChange={(evento) => setNombre(evento.target.value)}
              />
              {errorNombre && (
                <p className="help-bad" role="alert">
                  <IconoAlerta />
                  {errorNombre}
                </p>
              )}
            </div>

            <div className="fg">
              <label htmlFor="correo">Correo electrónico</label>
              <input
                className={`inp${errorCorreo ? ' bad' : ''}`}
                id="correo"
                type="email"
                value={correo}
                onChange={(evento) => setCorreo(evento.target.value)}
              />
              {errorCorreo && (
                <p className="help-bad" role="alert">
                  <IconoAlerta />
                  {errorCorreo}
                </p>
              )}
            </div>

            <div className="fg">
              <label htmlFor="contrasena">Contraseña</label>
              <input
                className={`inp${errorContrasena ? ' bad' : ''}`}
                id="contrasena"
                type="password"
                value={contrasena}
                onChange={(evento) => setContrasena(evento.target.value)}
              />
              <p className="hint">Mínimo 8 caracteres.</p>
            </div>

            <div className="fg">
              <label htmlFor="repetir-contrasena">Repetir contraseña</label>
              <input
                className="inp"
                id="repetir-contrasena"
                type="password"
                value={repetirContrasena}
                onChange={(evento) => setRepetirContrasena(evento.target.value)}
              />
              {errorContrasena && (
                <p className="help-bad" role="alert">
                  <IconoAlerta />
                  {errorContrasena}
                </p>
              )}
            </div>

            <button className="btn primary" type="submit" disabled={enviando}>
              Crear cuenta
            </button>
          </form>
          <p className="alt">
            ¿Ya tenés cuenta? <Link to="/login">Iniciar sesión</Link>
          </p>
        </div>
      </div>
    </div>
  )
}
