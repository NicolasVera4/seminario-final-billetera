import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { HttpResponse, http } from 'msw'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it } from 'vitest'
import RevisionResumen from './RevisionResumen'
import { servidor } from '../test/servidor'

const CATALOGOS = {
  categorias: [
    { id: 1, nombre: 'Suscripciones' },
    { id: 2, nombre: 'Restaurantes' },
  ],
  medios_pago: [{ id: 3, nombre: 'Crédito' }],
  origenes: [{ id: 4, nombre: 'Resumen' }],
}

const ESTADO_RESUMEN = {
  nombreArchivo: 'resumen_visa_septiembre.pdf',
  paginasLeidas: 3,
  archivoRef: '1/abc_resumen.pdf',
  comprobanteTipo: 'RESUMEN_TARJETA',
  items: [
    {
      monto: 4599,
      fecha: '2026-09-21',
      tipo: 'EGRESO',
      descripcion: 'Spotify',
      categoria_id: 1,
      categoria_sugerida: null,
      medio_pago_id: 3,
      cuota_numero: null,
      cuota_total: null,
      errores: [],
      posible_duplicado: false,
    },
    {
      monto: 32600,
      fecha: '2026-09-18',
      tipo: 'EGRESO',
      descripcion: 'Restaurante La Nieta',
      categoria_id: 2,
      categoria_sugerida: null,
      medio_pago_id: 3,
      cuota_numero: null,
      cuota_total: null,
      errores: [],
      posible_duplicado: true,
    },
    {
      monto: 15000,
      fecha: '2026-09-15',
      tipo: 'EGRESO',
      descripcion: 'Club Atlético cuota social',
      categoria_id: null,
      categoria_sugerida: 'Club',
      medio_pago_id: 3,
      cuota_numero: null,
      cuota_total: null,
      errores: ['CATEGORIA_INVALIDA'],
      posible_duplicado: false,
    },
    {
      monto: 18300,
      fecha: '2026-09-12',
      tipo: 'EGRESO',
      descripcion: 'Tienda deportiva zapatillas',
      categoria_id: 2,
      categoria_sugerida: null,
      medio_pago_id: 3,
      cuota_numero: 2,
      cuota_total: 6,
      errores: [],
      posible_duplicado: false,
    },
  ],
}

function renderizar(estado = ESTADO_RESUMEN) {
  return render(
    <MemoryRouter initialEntries={[{ pathname: '/resumen', state: estado }]}>
      <Routes>
        <Route path="/resumen" element={<RevisionResumen />} />
        <Route path="/" element={<div>Pantalla de chat</div>} />
      </Routes>
    </MemoryRouter>,
  )
}

beforeEach(() => {
  servidor.use(http.get('/api/catalogos', () => HttpResponse.json(CATALOGOS)))
})

describe('RevisionResumen', () => {
  it('hu06_ca1 y hu06_ca2 muestra cada consumo como fila separada y las paginas leidas', async () => {
    renderizar()

    expect(
      screen.getByText('resumen_visa_septiembre.pdf, 3 páginas leídas. Medio de pago: tarjeta de crédito.'),
    ).toBeInTheDocument()
    expect(screen.getByText('4 consumos detectados')).toBeInTheDocument()
    const filas = screen.getAllByRole('row')
    expect(filas).toHaveLength(5) // encabezado + 4 items
  })

  it('hu06_ca3 muestra la cuota del consumo en cuotas', async () => {
    renderizar()

    const filas = screen.getAllByRole('row')
    const filaZapatillas = filas.find((f) => f.textContent?.includes('Tienda deportiva zapatillas'))!
    expect(within(filaZapatillas).getByText('2 de 6')).toBeInTheDocument()
  })

  it('hu06_ca5 la fila con posible duplicado arranca destildada y ofrece guardar igual o descartar', async () => {
    renderizar()

    expect(
      screen.getByText('Posible duplicado de un gasto que cargaste el 18/09/2026.'),
    ).toBeInTheDocument()
    const checkboxNieta = screen.getByRole('checkbox', { name: /Restaurante La Nieta/ })
    expect(checkboxNieta).not.toBeChecked()
    expect(screen.getByRole('button', { name: 'Guardar igual' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Descartar Restaurante La Nieta' })).toBeInTheDocument()
  })

  it('la categoria sin resolver muestra el select con el motivo y bloquea el guardado', async () => {
    renderizar()

    expect(screen.getByText('"Club" no está en el catálogo.')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Guardar \d+ movimientos/ })).toBeDisabled()
  })

  it('al elegir la categoria pendiente se habilita el guardado', async () => {
    renderizar()
    const usuario = userEvent.setup()

    await usuario.selectOptions(screen.getByLabelText('Categoría de Club Atlético cuota social'), 'Restaurantes')

    expect(screen.getByRole('button', { name: /Guardar \d+ movimientos/ })).toBeEnabled()
  })

  it('hu06_ca4 guarda en lote solo los items tildados', async () => {
    let cuerpoEnviado: unknown = null
    servidor.use(
      http.post('/api/movimientos', async ({ request }) => {
        cuerpoEnviado = await request.json()
        return HttpResponse.json([], { status: 201 })
      }),
    )
    renderizar()
    const usuario = userEvent.setup()

    await usuario.selectOptions(screen.getByLabelText('Categoría de Club Atlético cuota social'), 'Restaurantes')
    await usuario.click(screen.getByRole('button', { name: /Guardar \d+ movimientos/ }))

    expect(cuerpoEnviado).toHaveLength(3)
    const descripciones = (cuerpoEnviado as Array<{ descripcion: string }>).map((m) => m.descripcion)
    expect(descripciones).not.toContain('Restaurante La Nieta')
    expect(descripciones).toContain('Spotify')
    expect(descripciones).toContain('Tienda deportiva zapatillas')
  })
})
