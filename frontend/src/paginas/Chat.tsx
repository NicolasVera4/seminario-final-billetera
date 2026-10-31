import { useEffect, useState, type FormEvent } from 'react'
import TarjetaMovimiento from '../componentes/TarjetaMovimiento'
import type { Borrador, Conversacion, Mensaje } from '../api/chat'
import { enviarMensaje, listarConversaciones } from '../api/chat'

export default function Chat() {
  const [conversaciones, setConversaciones] = useState<Conversacion[]>([])
  const [conversacionId, setConversacionId] = useState<number | null>(null)
  const [mensajes, setMensajes] = useState<Mensaje[]>([])
  const [borradoresPorMensaje, setBorradoresPorMensaje] = useState<Record<number, Borrador>>({})
  const [texto, setTexto] = useState('')
  const [enviando, setEnviando] = useState(false)

  function actualizarConversaciones() {
    listarConversaciones()
      .then(setConversaciones)
      .catch(() => {})
  }

  useEffect(actualizarConversaciones, [])

  async function manejarEnvio(evento: FormEvent) {
    evento.preventDefault()
    const textoEnviado = texto.trim()
    if (!textoEnviado) return

    setTexto('')
    setEnviando(true)
    setMensajes((previos) => [
      ...previos,
      {
        id: Date.now(),
        rol: 'USUARIO',
        contenido: textoEnviado,
        fuentes: null,
        creado_en: new Date().toISOString(),
      },
    ])

    try {
      const resultado = await enviarMensaje(textoEnviado, conversacionId)
      setConversacionId(resultado.conversacion_id)
      setMensajes((previos) => [...previos, resultado.mensaje])
      if (resultado.borrador) {
        const borrador = resultado.borrador
        setBorradoresPorMensaje((previos) => ({ ...previos, [resultado.mensaje.id]: borrador }))
      }
      actualizarConversaciones()
    } finally {
      setEnviando(false)
    }
  }

  function descartarBorrador(mensajeId: number) {
    setBorradoresPorMensaje((previos) => {
      const { [mensajeId]: _descartado, ...resto } = previos
      return resto
    })
  }

  return (
    <div>
      <aside>
        <h2>Conversaciones</h2>
        <ul>
          {conversaciones.map((conversacion) => (
            <li key={conversacion.id}>{conversacion.titulo ?? 'Conversación'}</li>
          ))}
        </ul>
      </aside>
      <main>
        <ul>
          {mensajes.map((mensaje) => (
            <li key={mensaje.id}>
              <p>{mensaje.contenido}</p>
              {borradoresPorMensaje[mensaje.id] && (
                <TarjetaMovimiento
                  borrador={borradoresPorMensaje[mensaje.id]}
                  onDescartado={() => descartarBorrador(mensaje.id)}
                />
              )}
            </li>
          ))}
        </ul>
        <form onSubmit={manejarEnvio}>
          <input
            placeholder="Escribí un gasto o un ingreso, o hacé una pregunta..."
            value={texto}
            onChange={(evento) => setTexto(evento.target.value)}
          />
          <button type="submit" disabled={enviando}>
            Enviar
          </button>
        </form>
      </main>
    </div>
  )
}
