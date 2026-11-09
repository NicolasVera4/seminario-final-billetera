import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { HttpResponse, http } from 'msw'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import Chat from './Chat'
import * as archivosApi from '../api/archivos'
import { subirAdjunto } from '../api/archivos'
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

afterEach(() => {
  vi.restoreAllMocks()
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

    expect(await screen.findByText('$15000')).toBeInTheDocument()
    expect(screen.getByText('Compra en el súper')).toBeInTheDocument()
    expect(screen.getByText('Interpretó el movimiento')).toBeInTheDocument()
    expect(screen.getByText('Validó los datos')).toBeInTheDocument()
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
      http.post('/api/archivos/adjuntar', () =>
        HttpResponse.json({
          modo: 'COMPROBANTE',
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
          conversacion_id: 1,
          mensaje_id: 2,
        }),
      ),
    )
    renderizar()
    const usuario = userEvent.setup()
    const archivo = new File(['contenido'], 'ticket.png', { type: 'image/png' })

    await usuario.upload(screen.getByLabelText('Adjuntar'), archivo)

    expect(await screen.findByText('Compra en el súper')).toBeInTheDocument()
    expect(screen.getByText('Interpretó el movimiento')).toBeInTheDocument()
    expect(screen.getByText('Validó los datos')).toBeInTheDocument()
    expect(screen.getByText('Cargaste una imagen: ticket.png.')).toBeInTheDocument()
  })

  it('al guardar un movimiento interpretado de un comprobante, manda el conversacion_id y mensaje_id reales que devolvió el backend', async () => {
    /* Bug reportado: el mensaje que arma el borrador de un comprobante se construía solo en el
     * navegador (nunca pasaba por el backend), así que su id era local/falso y no existía en la
     * base. Mandarlo como mensaje_id al guardar rompía la foreign key (500). Ahora /archivos/adjuntar
     * persiste la conversación y el mensaje en el backend y devuelve sus ids reales. */
    servidor.use(
      http.post('/api/archivos/adjuntar', () =>
        HttpResponse.json({
          modo: 'COMPROBANTE',
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
          conversacion_id: 7,
          mensaje_id: 42,
        }),
      ),
    )
    let cuerpoEnviado: unknown
    servidor.use(
      http.post('/api/movimientos', async ({ request }) => {
        cuerpoEnviado = await request.json()
        return HttpResponse.json(
          [
            {
              id: 1,
              monto: 15000,
              fecha: '2026-10-31',
              tipo: 'EGRESO',
              descripcion: 'Compra en el súper',
              categoria_id: 1,
              medio_pago_id: 2,
              origen_id: 1,
              creado_en: '2026-10-31T12:00:00Z',
            },
          ],
          { status: 201 },
        )
      }),
    )
    renderizar()
    const usuario = userEvent.setup()
    const archivo = new File(['contenido'], 'ticket.png', { type: 'image/png' })

    await usuario.upload(screen.getByLabelText('Adjuntar'), archivo)
    await usuario.click(await screen.findByRole('button', { name: 'Guardar movimiento' }))

    await screen.findByText('Guardado')
    expect(cuerpoEnviado).toMatchObject([{ conversacion_id: 7, mensaje_id: 42 }])
  })

  it('hu05_ca3 formato no admitido muestra el aviso de formatos', async () => {
    servidor.use(
      http.post('/api/archivos/adjuntar', () =>
        HttpResponse.json(
          { detail: 'Formato no admitido. Subí una imagen (jpg, png, webp) o un PDF.' },
          { status: 415 },
        ),
      ),
    )
    renderizar()
    // El input filtra por `accept`, pero eso solo ordena el selector del sistema operativo: un
    // archivo no admitido igual puede llegar (p. ej. "todos los archivos" o arrastrar y soltar),
    // así que el backend sigue siendo quien valida. `applyAccept: false` simula ese caso.
    const usuario = userEvent.setup({ applyAccept: false })
    const archivo = new File(['contenido'], 'notas.txt', { type: 'text/plain' })

    await usuario.upload(screen.getByLabelText('Adjuntar'), archivo)

    expect(
      await screen.findByText('Formato no admitido. Subí una imagen (jpg, png, webp) o un PDF.'),
    ).toBeInTheDocument()
  })

  it('hu05_ca4 sin monto legible avisa y sugiere cargarlo por texto', async () => {
    servidor.use(
      http.post('/api/archivos/adjuntar', () =>
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
      http.post('/api/archivos/adjuntar', () =>
        HttpResponse.json({
          modo: 'RESUMEN',
          items: [],
          archivo_ref: '1/abc_resumen.pdf',
          comprobante_tipo: 'RESUMEN_TARJETA',
          paginas_leidas: 3,
          conversacion_id: 1,
          mensaje_id: 2,
        }),
      ),
    )
    renderizar()
    const usuario = userEvent.setup()
    const archivo = new File(['contenido'], 'resumen.pdf', { type: 'application/pdf' })

    await usuario.upload(screen.getByLabelText('Adjuntar'), archivo)

    expect(navegarMock).toHaveBeenCalledWith(
      '/resumen',
      expect.objectContaining({
        state: expect.objectContaining({
          nombreArchivo: 'resumen.pdf',
          paginasLeidas: 3,
          conversacionId: 1,
        }),
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

  it('hu14 adjuntar un extracto navega a la pantalla de revisión', async () => {
    servidor.use(
      http.post('/api/archivos/adjuntar', () =>
        HttpResponse.json({
          modo: 'EXTRACTO',
          items: [],
          archivo_ref: '1/abc_extracto.csv',
          filas_descartadas: 1,
          conversacion_id: 1,
          mensaje_id: 2,
        }),
      ),
    )
    renderizar()
    const usuario = userEvent.setup()
    const archivo = new File(['contenido'], 'extracto.csv', { type: 'text/csv' })

    await usuario.upload(screen.getByLabelText('Adjuntar'), archivo)

    expect(navegarMock).toHaveBeenCalledWith(
      '/resumen',
      expect.objectContaining({
        state: expect.objectContaining({
          nombreArchivo: 'extracto.csv',
          comprobanteTipo: 'EXTRACTO',
          filasDescartadas: 1,
          conversacionId: 1,
        }),
      }),
    )
  })

  it('mientras se procesa un archivo adjunto, se muestra un indicador de carga', async () => {
    /* Bug reportado: un resumen de varias páginas puede tardar casi 2 minutos en procesarse
     * (varios llamados al LLM, uno por bloque, limitados por el rate limit de Groq) y la
     * interfaz no mostraba ningún indicio de que estaba trabajando — parecía colgada. */
    let resolverSubida: ((valor: Awaited<ReturnType<typeof subirAdjunto>>) => void) | undefined
    vi.spyOn(archivosApi, 'subirAdjunto').mockReturnValue(
      new Promise((resolve) => {
        resolverSubida = resolve
      }),
    )
    renderizar()
    const usuario = userEvent.setup()
    const archivo = new File(['contenido'], 'resumen.pdf', { type: 'application/pdf' })

    await usuario.upload(screen.getByLabelText('Adjuntar'), archivo)

    expect(await screen.findByText(/Procesando tu archivo/)).toBeInTheDocument()
    expect(screen.getByLabelText('Adjuntar')).toBeDisabled()

    resolverSubida?.({
      modo: 'EXTRACTO',
      items: [],
      archivo_ref: '1/x.csv',
      filas_descartadas: 0,
      conversacion_id: 1,
      mensaje_id: 2,
    })

    await waitFor(() => expect(screen.queryByText(/Procesando tu archivo/)).not.toBeInTheDocument())
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

  it('al hacer click en una conversación anterior, carga sus mensajes', async () => {
    servidor.use(
      http.get('/api/chat/conversaciones', () =>
        HttpResponse.json([
          { id: 1, titulo: 'Gastos de hoy', creado_en: '2026-10-31T12:00:00Z', actualizado_en: '2026-10-31T12:00:00Z' },
          { id: 2, titulo: 'Resumen Visa', creado_en: '2026-10-30T12:00:00Z', actualizado_en: '2026-10-30T12:00:00Z' },
        ]),
      ),
      http.get('/api/chat/conversaciones/1', () =>
        HttpResponse.json([
          { id: 10, rol: 'USUARIO', contenido: 'Gasté 500 en el súper', fuentes: null, creado_en: '2026-10-31T12:00:00Z' },
          {
            id: 11,
            rol: 'ASISTENTE',
            contenido: 'Encontré este movimiento, revisalo y confirmalo.',
            fuentes: null,
            creado_en: '2026-10-31T12:01:00Z',
          },
        ]),
      ),
    )
    renderizar()
    const usuario = userEvent.setup()

    await usuario.click(await screen.findByText('Gastos de hoy'))

    expect(await screen.findByText('Gasté 500 en el súper')).toBeInTheDocument()
    expect(screen.getByText('Encontré este movimiento, revisalo y confirmalo.')).toBeInTheDocument()
  })

  it('al navegar a una conversación vieja, un movimiento ya guardado se ve con sus chips y la tarjeta', async () => {
    servidor.use(
      http.get('/api/chat/conversaciones', () =>
        HttpResponse.json([
          { id: 1, titulo: 'Gaste 500 en el super', creado_en: '2026-10-31T12:00:00Z', actualizado_en: '2026-10-31T12:00:00Z' },
        ]),
      ),
      http.get('/api/chat/conversaciones/1', () =>
        HttpResponse.json([
          { id: 10, rol: 'USUARIO', contenido: 'Gasté 500 en el súper', fuentes: null, creado_en: '2026-10-31T12:00:00Z' },
          {
            id: 11,
            rol: 'ASISTENTE',
            contenido: 'Encontré este movimiento, revisalo y confirmalo.',
            fuentes: null,
            creado_en: '2026-10-31T12:01:00Z',
            movimiento: {
              monto: 500,
              fecha: '2026-10-31',
              tipo: 'EGRESO',
              descripcion: 'super',
              categoria_id: 1,
              categoria_sugerida: null,
              medio_pago_id: 2,
            },
          },
        ]),
      ),
    )
    renderizar()
    const usuario = userEvent.setup()

    await usuario.click(await screen.findByText('Gaste 500 en el super'))

    expect(await screen.findByText('Movimiento registrado')).toBeInTheDocument()
    expect(screen.getByText('Guardado')).toBeInTheDocument()
    expect(screen.getByText('Interpretó el movimiento')).toBeInTheDocument()
    expect(screen.getByText('Validó los datos')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Guardar movimiento' })).not.toBeInTheDocument()
    expect(screen.queryByText('Encontré este movimiento, revisalo y confirmalo.')).not.toBeInTheDocument()
  })

  it('al navegar a una conversación vieja, se mantiene la marca de audio transcripto', async () => {
    servidor.use(
      http.get('/api/chat/conversaciones', () =>
        HttpResponse.json([
          { id: 1, titulo: 'Pague el gimnasio', creado_en: '2026-10-31T12:00:00Z', actualizado_en: '2026-10-31T12:00:00Z' },
        ]),
      ),
      http.get('/api/chat/conversaciones/1', () =>
        HttpResponse.json([
          {
            id: 10,
            rol: 'USUARIO',
            contenido: 'Pagué el gimnasio',
            fuentes: null,
            transcripto: true,
            creado_en: '2026-10-31T12:00:00Z',
          },
        ]),
      ),
    )
    renderizar()
    const usuario = userEvent.setup()

    await usuario.click(await screen.findByText('Pague el gimnasio'))

    expect(await screen.findByText('Pagué el gimnasio')).toBeInTheDocument()
    expect(screen.getByText('Transcripto de un audio')).toBeInTheDocument()
  })

  it('al recargar la página, retoma la última conversación abierta', async () => {
    servidor.use(
      http.get('/api/chat/conversaciones', () =>
        HttpResponse.json([
          { id: 5, titulo: 'Gastos de hoy', creado_en: '2026-10-31T12:00:00Z', actualizado_en: '2026-10-31T12:00:00Z' },
        ]),
      ),
      http.get('/api/chat/conversaciones/5', () =>
        HttpResponse.json([
          { id: 20, rol: 'USUARIO', contenido: 'Pagué el gimnasio', fuentes: null, creado_en: '2026-10-31T12:00:00Z' },
        ]),
      ),
    )
    const primeraVez = renderizar()
    const usuario = userEvent.setup()
    await usuario.click(await screen.findByText('Gastos de hoy'))
    await screen.findByText('Pagué el gimnasio')
    primeraVez.unmount()

    renderizar()

    expect(await screen.findByText('Pagué el gimnasio')).toBeInTheDocument()
  })

  it('nueva conversación hace que el próximo reload no retome la anterior', async () => {
    servidor.use(
      http.get('/api/chat/conversaciones', () =>
        HttpResponse.json([
          { id: 5, titulo: 'Gastos de hoy', creado_en: '2026-10-31T12:00:00Z', actualizado_en: '2026-10-31T12:00:00Z' },
        ]),
      ),
      http.get('/api/chat/conversaciones/5', () =>
        HttpResponse.json([
          { id: 20, rol: 'USUARIO', contenido: 'Pagué el gimnasio', fuentes: null, creado_en: '2026-10-31T12:00:00Z' },
        ]),
      ),
    )
    const primeraVez = renderizar()
    const usuario = userEvent.setup()
    await usuario.click(await screen.findByText('Gastos de hoy'))
    await screen.findByText('Pagué el gimnasio')
    await usuario.click(screen.getByRole('button', { name: 'Nueva conversación' }))
    primeraVez.unmount()

    renderizar()

    await screen.findByText('Gastos de hoy')
    expect(screen.queryByText('Pagué el gimnasio')).not.toBeInTheDocument()
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
