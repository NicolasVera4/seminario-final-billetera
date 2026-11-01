import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { HttpResponse, http } from 'msw'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import Chat from './Chat'
import { guardarToken } from '../api/cliente'
import { servidor } from '../test/servidor'

const { navegarMock } = vi.hoisted(() => ({ navegarMock: vi.fn() }))

vi.mock('react-router-dom', async (importOriginal) => {
  const real = await importOriginal<typeof import('react-router-dom')>()
  return { ...real, useNavigate: () => navegarMock }
})

class GrabadorFalso {
  static instancias: GrabadorFalso[] = []
  ondataavailable: ((evento: { data: Blob }) => void) | null = null
  onstop: (() => void) | null = null

  constructor(public stream: MediaStream) {
    GrabadorFalso.instancias.push(this)
  }

  start() {}

  stop() {
    this.ondataavailable?.({ data: new Blob(['audio']) })
    this.onstop?.()
  }
}

function detenerGrabacionActual() {
  GrabadorFalso.instancias[GrabadorFalso.instancias.length - 1].stop()
}

function renderizar() {
  return render(
    <MemoryRouter>
      <Chat />
    </MemoryRouter>,
  )
}

beforeEach(() => {
  guardarToken('token-valido')
  GrabadorFalso.instancias = []
  vi.stubGlobal('MediaRecorder', GrabadorFalso)
  vi.stubGlobal('navigator', {
    ...navigator,
    mediaDevices: { getUserMedia: vi.fn().mockResolvedValue({ getTracks: () => [] }) },
  })
  servidor.use(
    http.get('/api/chat/conversaciones', () => HttpResponse.json([])),
    http.get('/api/catalogos', () =>
      HttpResponse.json({
        categorias: [{ id: 1, nombre: 'Supermercado' }],
        medios_pago: [{ id: 2, nombre: 'Débito' }],
        origenes: [{ id: 1, nombre: 'Texto' }],
      }),
    ),
    http.post('/api/movimientos/validar', () => HttpResponse.json({ errores: [], advertencias: [] })),
  )
})

describe('Chat', () => {
  it('muestra la lista de conversaciones en la barra lateral', async () => {
    servidor.use(
      http.get('/api/chat/conversaciones', () =>
        HttpResponse.json([
          { id: 1, titulo: 'Gastos de hoy', creado_en: '2026-10-31T12:00:00Z', actualizado_en: '2026-10-31T12:00:00Z' },
          { id: 2, titulo: 'Resumen Visa', creado_en: '2026-10-30T12:00:00Z', actualizado_en: '2026-10-30T12:00:00Z' },
        ]),
      ),
    )

    renderizar()

    expect(await screen.findByText('Gastos de hoy')).toBeInTheDocument()
    expect(screen.getByText('Resumen Visa')).toBeInTheDocument()
  })

  it('hu03_ca1 envía un mensaje y muestra el movimiento interpretado', async () => {
    servidor.use(
      http.post('/api/chat/mensajes', () =>
        HttpResponse.json({
          conversacion_id: 1,
          mensaje: {
            id: 2,
            rol: 'ASISTENTE',
            contenido: 'Encontré este movimiento, revisalo y confirmalo.',
            fuentes: null,
            creado_en: '2026-10-31T12:00:00Z',
          },
          borrador: {
            monto: 15000,
            fecha: '2026-10-31',
            tipo: 'EGRESO',
            descripcion: 'Compra en el súper',
            categoria_id: 1,
            categoria_sugerida: null,
            medio_pago_id: 2,
          },
        }),
      ),
    )
    renderizar()
    const usuario = userEvent.setup()

    await usuario.type(
      screen.getByPlaceholderText('Escribí un gasto o un ingreso, o hacé una pregunta...'),
      'gasté 15000 en el súper con débito',
    )
    await usuario.click(screen.getByRole('button', { name: 'Enviar' }))

    expect(await screen.findByText('Encontré este movimiento, revisalo y confirmalo.')).toBeInTheDocument()
    expect(screen.getByText('$15000')).toBeInTheDocument()
    expect(screen.getByText('Compra en el súper')).toBeInTheDocument()
  })

  it('hu03_ca3 cuando falta el monto, el asistente lo pide y no hay borrador', async () => {
    servidor.use(
      http.post('/api/chat/mensajes', () =>
        HttpResponse.json({
          conversacion_id: 1,
          mensaje: {
            id: 2,
            rol: 'ASISTENTE',
            contenido: 'Me falta el monto. ¿Cuánto fue?',
            fuentes: null,
            creado_en: '2026-10-31T12:00:00Z',
          },
          borrador: null,
        }),
      ),
    )
    renderizar()
    const usuario = userEvent.setup()

    await usuario.type(
      screen.getByPlaceholderText('Escribí un gasto o un ingreso, o hacé una pregunta...'),
      'compré cosas',
    )
    await usuario.click(screen.getByRole('button', { name: 'Enviar' }))

    expect(await screen.findByText('Me falta el monto. ¿Cuánto fue?')).toBeInTheDocument()
  })

  it('hu03_ca4 responde como consulta cuando el mensaje no describe un movimiento', async () => {
    servidor.use(
      http.post('/api/chat/mensajes', () =>
        HttpResponse.json({
          conversacion_id: 1,
          mensaje: {
            id: 2,
            rol: 'ASISTENTE',
            contenido: 'Todavía no tenés movimientos registrados.',
            fuentes: null,
            creado_en: '2026-10-31T12:00:00Z',
          },
          borrador: null,
        }),
      ),
    )
    renderizar()
    const usuario = userEvent.setup()

    await usuario.type(
      screen.getByPlaceholderText('Escribí un gasto o un ingreso, o hacé una pregunta...'),
      '¿cuánto gasté este mes?',
    )
    await usuario.click(screen.getByRole('button', { name: 'Enviar' }))

    expect(await screen.findByText('Todavía no tenés movimientos registrados.')).toBeInTheDocument()
  })

  it('hu05_ca1 adjuntar un comprobante muestra el movimiento interpretado', async () => {
    servidor.use(
      http.post('/api/archivos/comprobante', () =>
        HttpResponse.json({
          borrador: {
            monto: 15000,
            fecha: '2026-10-31',
            tipo: 'EGRESO',
            descripcion: 'Compra en el súper',
            categoria_id: 1,
            categoria_sugerida: null,
            medio_pago_id: 2,
          },
          archivo_ref: '1/abc_ticket.png',
          comprobante_tipo: 'TICKET',
          mensaje: 'Encontré este movimiento, revisalo y confirmalo.',
        }),
      ),
    )
    renderizar()
    const usuario = userEvent.setup()
    const archivo = new File(['contenido'], 'ticket.png', { type: 'image/png' })

    await usuario.upload(screen.getByLabelText('Adjuntar'), archivo)

    expect(await screen.findByText('Encontré este movimiento, revisalo y confirmalo.')).toBeInTheDocument()
    expect(screen.getByText('Compra en el súper')).toBeInTheDocument()
  })

  it('hu05_ca3 formato no admitido muestra el aviso de formatos', async () => {
    servidor.use(
      http.post('/api/archivos/comprobante', () =>
        HttpResponse.json(
          { detail: 'Formato no admitido. Subí una imagen (jpg, png, webp) o un PDF.' },
          { status: 415 },
        ),
      ),
    )
    renderizar()
    const usuario = userEvent.setup()
    const archivo = new File(['contenido'], 'notas.txt', { type: 'text/plain' })

    await usuario.upload(screen.getByLabelText('Adjuntar'), archivo)

    expect(
      await screen.findByText('Formato no admitido. Subí una imagen (jpg, png, webp) o un PDF.'),
    ).toBeInTheDocument()
  })

  it('hu05_ca4 sin monto legible avisa y sugiere cargarlo por texto', async () => {
    servidor.use(
      http.post('/api/archivos/comprobante', () =>
        HttpResponse.json(
          { detail: 'No pudimos leer un monto en el archivo. Probá cargarlo por texto.' },
          { status: 422 },
        ),
      ),
    )
    renderizar()
    const usuario = userEvent.setup()
    const archivo = new File(['contenido'], 'ticket.png', { type: 'image/png' })

    await usuario.upload(screen.getByLabelText('Adjuntar'), archivo)

    expect(
      await screen.findByText('No pudimos leer un monto en el archivo. Probá cargarlo por texto.'),
    ).toBeInTheDocument()
  })

  it('hu06 adjuntar un resumen de tarjeta navega a la pantalla de revisión', async () => {
    servidor.use(
      http.post('/api/archivos/resumen', () =>
        HttpResponse.json({
          items: [],
          archivo_ref: '1/abc_resumen.pdf',
          comprobante_tipo: 'RESUMEN_TARJETA',
          paginas_leidas: 3,
        }),
      ),
    )
    renderizar()
    const usuario = userEvent.setup()
    const archivo = new File(['contenido'], 'resumen.pdf', { type: 'application/pdf' })

    await usuario.upload(screen.getByLabelText('Adjuntar resumen de tarjeta'), archivo)

    expect(navegarMock).toHaveBeenCalledWith(
      '/resumen',
      expect.objectContaining({
        state: expect.objectContaining({ nombreArchivo: 'resumen.pdf', paginasLeidas: 3 }),
      }),
    )
  })

  it('hu10_ca3 muestra los chips de origen y de fuentes de una respuesta de asesoramiento', async () => {
    servidor.use(
      http.post('/api/chat/mensajes', () =>
        HttpResponse.json({
          conversacion_id: 1,
          mensaje: {
            id: 2,
            rol: 'ASISTENTE',
            contenido: 'Para ahorrar más, separá un 10% apenas cobrás.',
            fuentes: [
              { tipo: 'documento', titulo: 'Tips de ahorro', fragmento: 3 },
              { tipo: 'movimientos', desde: '2026-06', hasta: '2026-09' },
            ],
            creado_en: '2026-10-31T12:00:00Z',
          },
          borrador: null,
        }),
      ),
    )
    renderizar()
    const usuario = userEvent.setup()

    await usuario.type(
      screen.getByPlaceholderText('Escribí un gasto o un ingreso, o hacé una pregunta...'),
      '¿cómo puedo ahorrar más?',
    )
    await usuario.click(screen.getByRole('button', { name: 'Enviar' }))

    expect(await screen.findByText('Consultó tus movimientos')).toBeInTheDocument()
    expect(screen.getByText('Buscó en la documentación')).toBeInTheDocument()
    expect(screen.getByText('Tips de ahorro · fragmento 3')).toBeInTheDocument()
    expect(screen.getByText('Tus movimientos de 2026-06 a 2026-09')).toBeInTheDocument()
  })

  it('sin fuentes no muestra ningún chip de origen', async () => {
    servidor.use(
      http.post('/api/chat/mensajes', () =>
        HttpResponse.json({
          conversacion_id: 1,
          mensaje: {
            id: 2,
            rol: 'ASISTENTE',
            contenido: 'Me falta el monto. ¿Cuánto fue?',
            fuentes: null,
            creado_en: '2026-10-31T12:00:00Z',
          },
          borrador: null,
        }),
      ),
    )
    renderizar()
    const usuario = userEvent.setup()

    await usuario.type(
      screen.getByPlaceholderText('Escribí un gasto o un ingreso, o hacé una pregunta...'),
      'compré cosas',
    )
    await usuario.click(screen.getByRole('button', { name: 'Enviar' }))

    await screen.findByText('Me falta el monto. ¿Cuánto fue?')
    expect(screen.queryByText('Consultó tus movimientos')).not.toBeInTheDocument()
    expect(screen.queryByText('Buscó en la documentación')).not.toBeInTheDocument()
  })

  it('hu11_ca1_ca2 graba un audio, lo transcribe y pone el texto editable en el campo', async () => {
    servidor.use(
      http.post('/api/voz/transcribir', () =>
        HttpResponse.json({ texto: 'Gasté 15000 en el súper con débito' }),
      ),
    )
    renderizar()
    const usuario = userEvent.setup()

    await usuario.click(await screen.findByRole('button', { name: 'Grabar audio' }))
    expect(screen.getByRole('button', { name: 'Detener grabación' })).toBeInTheDocument()
    detenerGrabacionActual()

    const campo = (await screen.findByPlaceholderText(
      'Escribí un gasto o un ingreso, o hacé una pregunta...',
    )) as HTMLInputElement
    expect(campo.value).toBe('Gasté 15000 en el súper con débito')

    await usuario.type(campo, ' el jueves')
    expect(campo.value).toBe('Gasté 15000 en el súper con débito el jueves')
  })

  it('hu11_ca3 el texto transcripto enviado sigue el mismo flujo que uno escrito', async () => {
    servidor.use(
      http.post('/api/voz/transcribir', () =>
        HttpResponse.json({ texto: 'Gasté 15000 en el súper con débito' }),
      ),
      http.post('/api/chat/mensajes', () =>
        HttpResponse.json({
          conversacion_id: 1,
          mensaje: {
            id: 2,
            rol: 'ASISTENTE',
            contenido: 'Encontré este movimiento, revisalo y confirmalo.',
            fuentes: null,
            creado_en: '2026-10-31T12:00:00Z',
          },
          borrador: null,
        }),
      ),
    )
    renderizar()
    const usuario = userEvent.setup()

    await usuario.click(await screen.findByRole('button', { name: 'Grabar audio' }))
    detenerGrabacionActual()
    await screen.findByDisplayValue('Gasté 15000 en el súper con débito')
    await usuario.click(screen.getByRole('button', { name: 'Enviar' }))

    expect(await screen.findByText('Gasté 15000 en el súper con débito')).toBeInTheDocument()
    expect(screen.getByText('Transcripto de un audio')).toBeInTheDocument()
    expect(await screen.findByText('Encontré este movimiento, revisalo y confirmalo.')).toBeInTheDocument()
  })

  it('hu11_ca4 audio que no se puede transcribir avisa y sugiere repetirlo o escribirlo', async () => {
    servidor.use(
      http.post('/api/voz/transcribir', () =>
        HttpResponse.json(
          { detail: 'No pudimos transcribir el audio. Probá grabarlo de nuevo o escribí el mensaje.' },
          { status: 422 },
        ),
      ),
    )
    renderizar()
    const usuario = userEvent.setup()

    await usuario.click(await screen.findByRole('button', { name: 'Grabar audio' }))
    detenerGrabacionActual()

    expect(
      await screen.findByText('No pudimos transcribir el audio. Probá grabarlo de nuevo o escribí el mensaje.'),
    ).toBeInTheDocument()
  })
})
