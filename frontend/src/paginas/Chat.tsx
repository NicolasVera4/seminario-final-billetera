import { useEffect, useState, type ChangeEvent, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import TarjetaMovimiento from '../componentes/TarjetaMovimiento'
import { subirComprobante, subirResumen } from '../api/archivos'
import type { Borrador, Conversacion, Fuente, Mensaje } from '../api/chat'
import { enviarMensaje, listarConversaciones } from '../api/chat'
import { ErrorApi } from '../api/cliente'

export default function Chat() {
  const navegar = useNavigate()
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

  function agregarMensajeAsistente(contenido: string): number {
    const id = Date.now() + Math.random()
    setMensajes((previos) => [
      ...previos,
      { id, rol: 'ASISTENTE', contenido, fuentes: null, creado_en: new Date().toISOString() },
    ])
    return id
  }

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

  async function manejarAdjuntar(evento: ChangeEvent<HTMLInputElement>) {
    const archivo = evento.target.files?.[0]
    evento.target.value = ''
    if (!archivo) return

    setMensajes((previos) => [
      ...previos,
      {
        id: Date.now(),
        rol: 'USUARIO',
        contenido: archivo.name,
        fuentes: null,
        creado_en: new Date().toISOString(),
      },
    ])

    try {
      const resultado = await subirComprobante(archivo)
      const idMensaje = agregarMensajeAsistente(resultado.mensaje)
      if (resultado.borrador) {
        const borrador = resultado.borrador
        setBorradoresPorMensaje((previos) => ({ ...previos, [idMensaje]: borrador }))
      }
    } catch (error) {
      const texto = error instanceof ErrorApi ? error.message : 'No pudimos procesar el archivo.'
      agregarMensajeAsistente(texto)
    }
  }

  async function manejarAdjuntarResumen(evento: ChangeEvent<HTMLInputElement>) {
    const archivo = evento.target.files?.[0]
    evento.target.value = ''
    if (!archivo) return

    try {
      const resultado = await subirResumen(archivo)
      navegar('/resumen', {
        state: {
          nombreArchivo: archivo.name,
          paginasLeidas: resultado.paginas_leidas,
          archivoRef: resultado.archivo_ref,
          comprobanteTipo: resultado.comprobante_tipo,
          items: resultado.items,
        },
      })
    } catch (error) {
      const texto = error instanceof ErrorApi ? error.message : 'No pudimos procesar el resumen.'
      agregarMensajeAsistente(texto)
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
              {mensaje.fuentes && <ChipsOrigen fuentes={mensaje.fuentes} />}
              <p>{mensaje.contenido}</p>
              {mensaje.fuentes && <ListaFuentes fuentes={mensaje.fuentes} />}
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
          <label htmlFor="adjuntar">Adjuntar</label>
          <input id="adjuntar" type="file" onChange={manejarAdjuntar} />
          <label htmlFor="adjuntar-resumen">Adjuntar resumen de tarjeta</label>
          <input id="adjuntar-resumen" type="file" onChange={manejarAdjuntarResumen} />
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

function ChipsOrigen({ fuentes }: { fuentes: Fuente[] }) {
  const consultoMovimientos = fuentes.some((fuente) => fuente.tipo === 'movimientos')
  const buscoDocumentacion = fuentes.some((fuente) => fuente.tipo === 'documento')
  if (!consultoMovimientos && !buscoDocumentacion) return null

  return (
    <div>
      {consultoMovimientos && <span>Consultó tus movimientos</span>}
      {buscoDocumentacion && <span>Buscó en la documentación</span>}
    </div>
  )
}

function ListaFuentes({ fuentes }: { fuentes: Fuente[] }) {
  if (fuentes.length === 0) return null

  return (
    <ul>
      {fuentes.map((fuente, indice) => (
        <li key={indice}>
          {fuente.tipo === 'documento'
            ? `${fuente.titulo} · fragmento ${fuente.fragmento}`
            : `Tus movimientos de ${fuente.desde} a ${fuente.hasta}`}
        </li>
      ))}
    </ul>
  )
}
