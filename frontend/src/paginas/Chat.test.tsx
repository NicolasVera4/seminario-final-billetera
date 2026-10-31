import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { HttpResponse, http } from 'msw'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it } from 'vitest'
import Chat from './Chat'
import { guardarToken } from '../api/cliente'
import { servidor } from '../test/servidor'

function renderizar() {
  return render(
    <MemoryRouter>
      <Chat />
    </MemoryRouter>,
  )
}

beforeEach(() => {
  guardarToken('token-valido')
  servidor.use(http.get('/api/chat/conversaciones', () => HttpResponse.json([])))
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
})
