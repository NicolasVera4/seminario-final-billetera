import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { HttpResponse, http } from 'msw'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it } from 'vitest'
import AdminDocumentos from './AdminDocumentos'
import { guardarToken } from '../api/cliente'
import { servidor } from '../test/servidor'

function renderizar() {
  return render(
    <MemoryRouter>
      <AdminDocumentos />
    </MemoryRouter>,
  )
}

beforeEach(() => {
  guardarToken('token-valido')
})

describe('AdminDocumentos', () => {
  it('lista los documentos de referencia cargados', async () => {
    servidor.use(
      http.get('/api/admin/documentos', () =>
        HttpResponse.json([
          { id: 1, titulo: 'OIT (2019). Economía familiar', cantidad_fragmentos: 120, creado_en: '2026-10-01T12:00:00Z' },
        ]),
      ),
    )
    renderizar()

    expect(await screen.findByText('OIT (2019). Economía familiar')).toBeInTheDocument()
    expect(screen.getByText('120')).toBeInTheDocument()
  })

  it('sin documentos, avisa que todavía no se cargó ninguno', async () => {
    servidor.use(http.get('/api/admin/documentos', () => HttpResponse.json([])))
    renderizar()

    expect(await screen.findByText('Todavía no cargaste ningún documento.')).toBeInTheDocument()
  })

  it('carga un documento nuevo y actualiza la lista', async () => {
    let cargado = false
    servidor.use(
      http.get('/api/admin/documentos', () =>
        HttpResponse.json(
          cargado
            ? [{ id: 2, titulo: 'Tips de ahorro', cantidad_fragmentos: 5, creado_en: '2026-11-09T12:00:00Z' }]
            : [],
        ),
      ),
      http.post('/api/admin/documentos', () => {
        cargado = true
        return HttpResponse.json(
          { id: 2, titulo: 'Tips de ahorro', cantidad_fragmentos: 5, creado_en: '2026-11-09T12:00:00Z' },
          { status: 201 },
        )
      }),
    )
    renderizar()
    const usuario = userEvent.setup()
    await screen.findByText('Todavía no cargaste ningún documento.')

    await usuario.type(screen.getByLabelText('Título'), 'Tips de ahorro')
    const archivo = new File(['contenido'], 'tips.txt', { type: 'text/plain' })
    await usuario.upload(screen.getByLabelText('Archivo'), archivo)
    await usuario.click(screen.getByRole('button', { name: 'Cargar documento' }))

    expect(await screen.findByText('Tips de ahorro')).toBeInTheDocument()
  })

  it('elimina un documento', async () => {
    let eliminado = false
    servidor.use(
      http.get('/api/admin/documentos', () =>
        HttpResponse.json(
          eliminado
            ? []
            : [{ id: 1, titulo: 'Tips', cantidad_fragmentos: 3, creado_en: '2026-10-01T12:00:00Z' }],
        ),
      ),
      http.delete('/api/admin/documentos/1', () => {
        eliminado = true
        return new HttpResponse(null, { status: 204 })
      }),
    )
    renderizar()
    const usuario = userEvent.setup()
    await screen.findByText('Tips')

    await usuario.click(screen.getByRole('button', { name: 'Eliminar Tips' }))

    expect(await screen.findByText('Todavía no cargaste ningún documento.')).toBeInTheDocument()
  })
})
