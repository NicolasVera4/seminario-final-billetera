import { useEffect, useRef, useState, type ChangeEvent, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import TarjetaMovimiento from '../componentes/TarjetaMovimiento'
import { subirAdjunto } from '../api/archivos'
import type { Borrador, Conversacion, Fuente, Mensaje } from '../api/chat'
import { enviarMensaje, listarConversaciones, obtenerConversacion } from '../api/chat'
import { ErrorApi } from '../api/cliente'
import { transcribirAudio } from '../api/voz'
import Layout from '../componentes/Layout'
import {
  IconoAdjuntar,
  IconoArchivo,
  IconoDocumento,
  IconoEnviar,
  IconoLogo,
  IconoMas,
  IconoMicrofono,
} from '../componentes/iconos'

interface MensajeChat extends Mensaje {
  /** Si el mensaje tiene un id real del backend. Los mensajes de subir un comprobante se arman
   * localmente (no pasan por /chat/mensajes), así que su id es falso: nunca hay que mandarlo
   * como mensaje_id al guardar un movimiento (rompe la FK en el backend). */
  persistido: boolean
}

const MENSAJE_ERROR_TRANSCRIPCION = 'No pudimos transcribir el audio. Probá grabarlo de nuevo o escribí el mensaje.'
const CLAVE_CONVERSACION_ACTIVA = 'qash_conversacion_activa'
const MESES_CORTOS = [
  'ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic',
]

function formatearFechaCorta(fechaIso: string) {
  const fecha = new Date(fechaIso)
  return `${fecha.getDate()} ${MESES_CORTOS[fecha.getMonth()]}`
}

function textoOptimistaAdjunto(archivo: File) {
  const tipo = archivo.type.startsWith('image/') ? 'una imagen' : 'un archivo'
  return `Cargaste ${tipo}: ${archivo.name}.`
}

export default function Chat() {
  const navegar = useNavigate()
  const [conversaciones, setConversaciones] = useState<Conversacion[]>([])
  const [conversacionId, setConversacionId] = useState<number | null>(null)
  const [mensajes, setMensajes] = useState<MensajeChat[]>([])
  const [borradoresPorMensaje, setBorradoresPorMensaje] = useState<Record<number, Borrador>>({})
  const [texto, setTexto] = useState('')
  const [enviando, setEnviando] = useState(false)
  const [procesandoArchivo, setProcesandoArchivo] = useState(false)
  const [grabando, setGrabando] = useState(false)
  const [vieneDeAudio, setVieneDeAudio] = useState(false)
  const grabadorRef = useRef<MediaRecorder | null>(null)

  function actualizarConversaciones() {
    listarConversaciones()
      .then(setConversaciones)
      .catch(() => {})
  }

  useEffect(actualizarConversaciones, [])

  useEffect(() => {
    const idGuardado = localStorage.getItem(CLAVE_CONVERSACION_ACTIVA)
    if (idGuardado) abrirConversacion(Number(idGuardado))
  }, [])

  function abrirConversacion(id: number) {
    obtenerConversacion(id)
      .then((mensajesConversacion) => {
        setConversacionId(id)
        setMensajes(mensajesConversacion.map((mensaje) => ({ ...mensaje, persistido: true })))
        setBorradoresPorMensaje({})
        localStorage.setItem(CLAVE_CONVERSACION_ACTIVA, String(id))
      })
      .catch(() => {})
  }

  function agregarMensajeAsistente(contenido: string): number {
    const id = Date.now() + Math.random()
    setMensajes((previos) => [
      ...previos,
      { id, rol: 'ASISTENTE', contenido, fuentes: null, creado_en: new Date().toISOString(), persistido: false },
    ])
    return id
  }

  async function manejarEnvio(evento: FormEvent) {
    evento.preventDefault()
    const textoEnviado = texto.trim()
    if (!textoEnviado) return

    const transcripto = vieneDeAudio
    setTexto('')
    setVieneDeAudio(false)
    setEnviando(true)
    setMensajes((previos) => [
      ...previos,
      {
        id: Date.now(),
        rol: 'USUARIO',
        contenido: textoEnviado,
        fuentes: null,
        creado_en: new Date().toISOString(),
        transcripto,
        persistido: false,
      },
    ])

    try {
      const resultado = await enviarMensaje(textoEnviado, conversacionId, transcripto)
      setConversacionId(resultado.conversacion_id)
      localStorage.setItem(CLAVE_CONVERSACION_ACTIVA, String(resultado.conversacion_id))
      setMensajes((previos) => [...previos, { ...resultado.mensaje, persistido: true }])
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
        contenido: textoOptimistaAdjunto(archivo),
        fuentes: null,
        creado_en: new Date().toISOString(),
        persistido: false,
      },
    ])
    setProcesandoArchivo(true)
    try {
      const resultado = await subirAdjunto(archivo, conversacionId)
      setConversacionId(resultado.conversacion_id)
      localStorage.setItem(CLAVE_CONVERSACION_ACTIVA, String(resultado.conversacion_id))
      actualizarConversaciones()

      if (resultado.modo === 'COMPROBANTE') {
        setMensajes((previos) => [
          ...previos,
          {
            id: resultado.mensaje_id,
            rol: 'ASISTENTE',
            contenido: resultado.mensaje,
            fuentes: null,
            creado_en: new Date().toISOString(),
            persistido: true,
          },
        ])
        if (resultado.borrador) {
          const borrador = resultado.borrador
          setBorradoresPorMensaje((previos) => ({ ...previos, [resultado.mensaje_id]: borrador }))
        }
        return
      }

      if (resultado.modo === 'RESUMEN') {
        navegar('/resumen', {
          state: {
            nombreArchivo: archivo.name,
            paginasLeidas: resultado.paginas_leidas,
            archivoRef: resultado.archivo_ref,
            comprobanteTipo: resultado.comprobante_tipo,
            items: resultado.items,
            conversacionId: resultado.conversacion_id,
          },
        })
        return
      }

      navegar('/resumen', {
        state: {
          nombreArchivo: archivo.name,
          paginasLeidas: 0,
          filasDescartadas: resultado.filas_descartadas,
          archivoRef: resultado.archivo_ref,
          comprobanteTipo: 'EXTRACTO',
          items: resultado.items,
          conversacionId: resultado.conversacion_id,
        },
      })
    } catch (error) {
      const texto = error instanceof ErrorApi ? error.message : 'No pudimos procesar el archivo.'
      agregarMensajeAsistente(texto)
    } finally {
      setProcesandoArchivo(false)
    }
  }

  async function manejarMicrofono() {
    if (grabando) {
      grabadorRef.current?.stop()
      return
    }

    const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
    const grabador = new MediaRecorder(stream)
    const partes: BlobPart[] = []
    grabador.ondataavailable = (evento) => partes.push(evento.data)
    grabador.onstop = async () => {
      stream.getTracks().forEach((pista) => pista.stop())
      setGrabando(false)

      try {
        const resultado = await transcribirAudio(new Blob(partes, { type: 'audio/webm' }))
        setTexto(resultado.texto)
        setVieneDeAudio(true)
      } catch (error) {
        const mensajeError = error instanceof ErrorApi ? error.message : MENSAJE_ERROR_TRANSCRIPCION
        agregarMensajeAsistente(mensajeError)
      }
    }

    grabadorRef.current = grabador
    grabador.start()
    setGrabando(true)
  }

  function descartarBorrador(mensajeId: number) {
    setBorradoresPorMensaje((previos) => {
      const { [mensajeId]: _descartado, ...resto } = previos
      return resto
    })
  }

  function manejarNuevaConversacion() {
    setConversacionId(null)
    setMensajes([])
    setBorradoresPorMensaje({})
    localStorage.removeItem(CLAVE_CONVERSACION_ACTIVA)
  }

  return (
    <Layout
      sidebarExtra={
        <div className="convs">
          <h2>Conversaciones</h2>
          <ul>
            {conversaciones.map((conversacion) => (
              <li key={conversacion.id} className={`conv ${conversacion.id === conversacionId ? 'on' : ''}`}>
                <button type="button" onClick={() => abrirConversacion(conversacion.id)}>
                  <b>{conversacion.titulo ?? 'Conversación'}</b>
                  <small>{formatearFechaCorta(conversacion.actualizado_en)}</small>
                </button>
              </li>
            ))}
          </ul>
        </div>
      }
    >
      <header className="top">
        <div className="t">
          <div className="logo">
            <IconoLogo />
          </div>
          <div>
            <h1>Qash</h1>
            <p>Tu billetera inteligente</p>
          </div>
        </div>
        <button className="btn sm" type="button" onClick={manejarNuevaConversacion}>
          <IconoMas />
          Nueva conversación
        </button>
      </header>
      <div className="chat">
        {mensajes.map((mensaje) =>
          mensaje.rol === 'USUARIO' ? (
            <div className="u" key={mensaje.id}>
              <span className="b">{mensaje.contenido}</span>
              {mensaje.transcripto && (
                <div className="meta">
                  <IconoMicrofono />
                  <span>Transcripto de un audio</span>
                </div>
              )}
            </div>
          ) : (
            <MensajeAsistente
              key={mensaje.id}
              mensaje={mensaje}
              borradorPendiente={borradoresPorMensaje[mensaje.id]}
              conversacionId={conversacionId}
              onDescartado={() => descartarBorrador(mensaje.id)}
            />
          ),
        )}
      </div>
      <form className="composer" onSubmit={manejarEnvio}>
        <div className="bar">
          <label className="ib" htmlFor="adjuntar" title="Adjuntar">
            <IconoAdjuntar />
            <span className="sr-solo">Adjuntar</span>
          </label>
          <input
            className="sr-solo"
            id="adjuntar"
            type="file"
            accept="image/jpeg,image/png,image/webp,application/pdf,text/csv,.csv,.xlsx,application/vnd.ms-excel,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            disabled={procesandoArchivo}
            onChange={manejarAdjuntar}
          />

          <input
            placeholder="Escribí un gasto o un ingreso, o hacé una pregunta..."
            value={texto}
            onChange={(evento) => setTexto(evento.target.value)}
          />
          <button className={`ib${grabando ? ' on' : ''}`} type="button" onClick={manejarMicrofono}>
            <IconoMicrofono />
            <span className="sr-solo">{grabando ? 'Detener grabación' : 'Grabar audio'}</span>
          </button>
          <button className="ib send" type="submit" disabled={enviando}>
            <IconoEnviar />
            <span className="sr-solo">Enviar</span>
          </button>
        </div>
        <small>
          {procesandoArchivo
            ? 'Procesando tu archivo... puede tardar un minuto o dos si tiene varias páginas.'
            : 'Podés adjuntar tickets, facturas, resúmenes de tarjeta (PDF o imagen) y extractos (CSV o Excel)'}
        </small>
      </form>
    </Layout>
  )
}

function MensajeAsistente({
  mensaje,
  borradorPendiente,
  conversacionId,
  onDescartado,
}: {
  mensaje: MensajeChat
  borradorPendiente: Borrador | undefined
  conversacionId: number | null
  onDescartado: () => void
}) {
  const borrador = borradorPendiente ?? mensaje.movimiento
  if (!borrador) {
    return (
      <div>
        {mensaje.fuentes && <ChipsOrigen fuentes={mensaje.fuentes} />}
        <div className="bot">
          <div className="ic">
            <IconoLogo />
          </div>
          <div className="bub">
            <p>{mensaje.contenido}</p>
            {mensaje.fuentes && <ListaFuentes fuentes={mensaje.fuentes} />}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div>
      <ChipsProcesamiento />
      <div className="bot">
        <div className="ic">
          <IconoLogo />
        </div>
        <div className="bot-mv">
          <TarjetaMovimiento
            borrador={borrador}
            conversacionId={mensaje.persistido ? conversacionId : null}
            mensajeId={mensaje.persistido ? mensaje.id : null}
            yaGuardado={!borradorPendiente}
            onDescartado={onDescartado}
          />
        </div>
      </div>
    </div>
  )
}

function ChipsOrigen({ fuentes }: { fuentes: Fuente[] }) {
  const consultoMovimientos = fuentes.some((fuente) => fuente.tipo === 'movimientos')
  const buscoDocumentacion = fuentes.some((fuente) => fuente.tipo === 'documento')
  if (!consultoMovimientos && !buscoDocumentacion) return null

  return (
    <div className="tools">
      {consultoMovimientos && (
        <span className="tool">
          <i />
          Consultó tus movimientos
        </span>
      )}
      {buscoDocumentacion && (
        <span className="tool">
          <i />
          Buscó en la documentación
        </span>
      )}
    </div>
  )
}

function ChipsProcesamiento() {
  return (
    <div className="tools">
      <span className="tool">
        <i />
        Interpretó el movimiento
      </span>
      <span className="tool">
        <i />
        Validó los datos
      </span>
    </div>
  )
}

function ListaFuentes({ fuentes }: { fuentes: Fuente[] }) {
  if (fuentes.length === 0) return null

  return (
    <div className="fuentes">
      <span className="dim" style={{ fontSize: 12, fontWeight: 600 }}>
        Fuentes
      </span>
      {fuentes.map((fuente, indice) => (
        <span className="pill" key={indice}>
          {fuente.tipo === 'documento' ? (
            <IconoDocumento />
          ) : (
            <IconoArchivo />
          )}
          {fuente.tipo === 'documento'
            ? `${fuente.titulo} · fragmento ${fuente.fragmento}`
            : `Tus movimientos de ${fuente.desde} a ${fuente.hasta}`}
        </span>
      ))}
    </div>
  )
}
