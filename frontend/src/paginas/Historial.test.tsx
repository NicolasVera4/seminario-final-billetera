import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { HttpResponse, http } from 'msw'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it } from 'vitest'
import Historial from './Historial'
import { servidor } from '../test/servidor'

const CATALOGOS = {
  categorias: [
    { id: 1, nombre: 'Supermercado' },
    { id: 2, nombre: 'Sueldo' },
  ],
  medios_pago: [
    { id: 1, nombre: 'Débito' },
    { id: 2, nombre: 'Transferencia' },
  ],
  origenes: [{ id: 1, nombre: 'Texto' }],
}

function historialRespuesta(items: unknown[], overrides = {}) {
  return { items, total: items.length, pagina: 1, por_pagina: 15, ...overrides }
}

function renderizar() {
  return render(
    <MemoryRouter>
      <Historial />
    </MemoryRouter>,
  )
}

beforeEach(() => {
  servidor.use(http.get('/api/catalogos', () => HttpResponse.json(CATALOGOS)))
})

describe('Historial', () => {
  it('hu07_ca1 muestra los movimientos del más reciente al más antiguo con sus datos', async () => {
    servidor.use(
      http.get('/api/movimientos', () =>
        HttpResponse.json(
          historialRespuesta([
            {
              id: 1,
              fecha: '2026-09-27',
              descripcion: 'Compra en el súper',
              categoria: 'Supermercado',
              medio_pago: 'Débito',
              origen: 'Texto',
              monto: 15000,
              tipo: 'EGRESO',
            },
            {
              id: 2,
              fecha: '2026-09-03',
              descripcion: 'Sueldo',
              categoria: 'Sueldo',
              medio_pago: 'Transferencia',
              origen: 'Texto',
              monto: 980000,
              tipo: 'INGRESO',
            },
          ]),
        ),
      ),
    )
    renderizar()

    const filas = await screen.findAllByRole('row')
    expect(within(filas[1]).getByText('Compra en el súper')).toBeInTheDocument()
    expect(within(filas[1]).getByText('−$15.000,00')).toBeInTheDocument()
    expect(within(filas[2]).getByText('Sueldo')).toBeInTheDocument()
    expect(within(filas[2]).getByText('+$980.000,00')).toBeInTheDocument()
  })

  it('hu07_ca2 filtrar por categoría vuelve a pedir la lista con ese filtro', async () => {
    servidor.use(
      http.get('/api/movimientos', ({ request }) => {
        const url = new URL(request.url)
        if (url.searchParams.get('categoria_id') === '2') {
          return HttpResponse.json(
            historialRespuesta([
              {
                id: 2,
                fecha: '2026-09-03',
                descripcion: 'Sueldo',
                categoria: 'Sueldo',
                medio_pago: 'Transferencia',
                origen: 'Texto',
                monto: 980000,
                tipo: 'INGRESO',
              },
            ]),
          )
        }
        return HttpResponse.json(historialRespuesta([]))
      }),
    )
    renderizar()
    await screen.findByText('No encontramos movimientos para esos criterios.')

    const usuario = userEvent.setup()
    await usuario.selectOptions(screen.getByLabelText('Categoría'), 'Sueldo')

    expect(await screen.findByText('Sueldo')).toBeInTheDocument()
  })

  it('hu07_ca3 busca por texto', async () => {
    servidor.use(
      http.get('/api/movimientos', ({ request }) => {
        const url = new URL(request.url)
        if (url.searchParams.get('q') === 'gimnasio') {
          return HttpResponse.json(
            historialRespuesta([
              {
                id: 3,
                fecha: '2026-09-27',
                descripcion: 'Cuota del gimnasio',
                categoria: 'Salud y deporte',
                medio_pago: 'Transferencia',
                origen: 'Texto',
                monto: 28000,
                tipo: 'EGRESO',
              },
            ]),
          )
        }
        return HttpResponse.json(historialRespuesta([]))
      }),
    )
    renderizar()
    await screen.findByText('No encontramos movimientos para esos criterios.')

    const usuario = userEvent.setup()
    await usuario.type(screen.getByPlaceholderText('Descripción o monto'), 'gimnasio')

    expect(await screen.findByText('Cuota del gimnasio')).toBeInTheDocument()
  })

  it('hu07_ca4 sin resultados informa que no hay movimientos', async () => {
    servidor.use(http.get('/api/movimientos', () => HttpResponse.json(historialRespuesta([]))))
    renderizar()

    expect(
      await screen.findByText('No encontramos movimientos para esos criterios.'),
    ).toBeInTheDocument()
  })

  it('muestra el total y permite pasar de página', async () => {
    servidor.use(
      http.get('/api/movimientos', ({ request }) => {
        const url = new URL(request.url)
        if (url.searchParams.get('pagina') === '2') {
          return HttpResponse.json(
            historialRespuesta(
              [
                {
                  id: 9,
                  fecha: '2026-09-01',
                  descripcion: 'Alquiler',
                  categoria: null,
                  medio_pago: 'Transferencia',
                  origen: 'Texto',
                  monto: 250000,
                  tipo: 'EGRESO',
                },
              ],
              { total: 16, pagina: 2 },
            ),
          )
        }
        return HttpResponse.json(
          historialRespuesta(
            Array.from({ length: 15 }, (_, i) => ({
              id: i,
              fecha: '2026-09-27',
              descripcion: `Mov ${i}`,
              categoria: 'Supermercado',
              medio_pago: 'Débito',
              origen: 'Texto',
              monto: 1000,
              tipo: 'EGRESO',
            })),
            { total: 16 },
          ),
        )
      }),
    )
    renderizar()

    expect(await screen.findByText('Mostrando 15 de 16 movimientos')).toBeInTheDocument()

    const usuario = userEvent.setup()
    await usuario.click(screen.getByRole('button', { name: 'Página siguiente' }))

    expect(await screen.findByText('Alquiler')).toBeInTheDocument()
  })
})
