import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { HttpResponse, http } from 'msw'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it } from 'vitest'
import Dashboard from './Dashboard'
import { guardarToken } from '../api/cliente'
import { servidor } from '../test/servidor'

beforeEach(() => {
  guardarToken('token-valido')
})

function dashboardRespuesta(overrides = {}) {
  // Los montos van como string: así los serializa de verdad el backend (Decimal -> string en el
  // JSON). Un mock con numbers acá hubiera dejado pasar el bug de Recharts sin poder graficar.
  return {
    anio: 2026,
    mes: 9,
    ingresos: { monto: '980000.00', variacion_texto: 'Igual que en agosto.' },
    egresos: { monto: '612450.00', variacion_texto: '3,8% más que en agosto.' },
    saldo: '367550.00',
    evolucion: [
      { anio: 2026, mes: 7, ingresos: '980000.00', egresos: '520000.00' },
      { anio: 2026, mes: 8, ingresos: '980000.00', egresos: '590000.00' },
      { anio: 2026, mes: 9, ingresos: '980000.00', egresos: '612450.00' },
    ],
    distribucion_categorias: [
      { categoria: 'Supermercado', categoria_id: 1, monto: '168300.00', porcentaje: 27 },
      { categoria: 'Transporte', categoria_id: 4, monto: '71000.00', porcentaje: 12 },
    ],
    alertas: [
      {
        categoria: 'Restaurantes',
        categoria_id: 3,
        porcentaje: 42,
        monto_actual: '86400.00',
        promedio: '60800.00',
      },
    ],
    proyeccion: { datos_suficientes: true, anio: 2026, mes: 10, monto: '640000.0' },
    anomalias: {
      datos_suficientes: true,
      meses: [
        {
          anio: 2026,
          mes: 7,
          monto: '820000.00',
          promedio_otros_meses: '586000.00',
          porcentaje_sobre_promedio: 40,
        },
      ],
    },
    hay_movimientos: true,
    ...overrides,
  }
}

function renderizar() {
  return render(
    <MemoryRouter>
      <Dashboard />
    </MemoryRouter>,
  )
}

describe('Dashboard', () => {
  it('hu08_ca1 muestra ingresos, gastos y saldo del mes con su variación', async () => {
    servidor.use(http.get('/api/dashboard', () => HttpResponse.json(dashboardRespuesta())))
    renderizar()

    expect(await screen.findByText('$980.000,00')).toBeInTheDocument()
    expect(screen.getByText('Igual que en agosto.')).toBeInTheDocument()
    expect(screen.getByText('$612.450,00')).toBeInTheDocument()
    expect(screen.getByText('3,8% más que en agosto.')).toBeInTheDocument()
    expect(screen.getByText('$367.550,00')).toBeInTheDocument()
  })

  it('hu08_ca2 muestra el flujo mensual con ingresos y gastos', async () => {
    servidor.use(http.get('/api/dashboard', () => HttpResponse.json(dashboardRespuesta())))
    renderizar()

    expect(await screen.findByText('Flujo mensual')).toBeInTheDocument()
    expect(screen.getAllByText('Ingresos').length).toBeGreaterThan(0)
    expect(screen.getAllByText('Gastos').length).toBeGreaterThan(0)
  })

  it('hu08_ca3 muestra la distribución de gastos por categoría', async () => {
    servidor.use(http.get('/api/dashboard', () => HttpResponse.json(dashboardRespuesta())))
    renderizar()

    expect(await screen.findByText('Gastos por categoría')).toBeInTheDocument()
    expect(screen.getByText('Supermercado')).toBeInTheDocument()
    expect(screen.getByText('27%')).toBeInTheDocument()
  })

  it('hu08_ca4 sin movimientos indica que no hay datos', async () => {
    servidor.use(
      http.get('/api/dashboard', () =>
        HttpResponse.json(
          dashboardRespuesta({ hay_movimientos: false, distribucion_categorias: [], alertas: [] }),
        ),
      ),
    )
    renderizar()

    expect(
      await screen.findByText(
        'Todavía no cargaste movimientos este mes. Contale un gasto a Qash en el chat para empezar.',
      ),
    ).toBeInTheDocument()
  })

  it('hu09_ca3 la alerta muestra categoría, gasto actual y promedio', async () => {
    servidor.use(http.get('/api/dashboard', () => HttpResponse.json(dashboardRespuesta())))
    renderizar()

    expect(
      await screen.findByText(
        'Restaurantes: llevás $86.400,00 este mes. Tu promedio de los últimos 3 meses es $60.800,00.',
      ),
    ).toBeInTheDocument()
    expect(screen.getByText('+42%')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Ver movimientos' })).toBeInTheDocument()
  })

  it('sin alertas no muestra el bloque de alertas', async () => {
    servidor.use(
      http.get('/api/dashboard', () => HttpResponse.json(dashboardRespuesta({ alertas: [] }))),
    )
    renderizar()

    await screen.findByText('Flujo mensual')
    expect(screen.queryByText(/por encima de lo habitual/)).not.toBeInTheDocument()
  })

  it('hu12_ca1 muestra la proyección de gasto del próximo mes', async () => {
    servidor.use(http.get('/api/dashboard', () => HttpResponse.json(dashboardRespuesta())))
    renderizar()

    expect(await screen.findByText('Proyección de gasto')).toBeInTheDocument()
    expect(screen.getByText('$640.000,00')).toBeInTheDocument()
  })

  it('hu12_ca2 indica que no hay datos suficientes para proyectar el gasto', async () => {
    servidor.use(
      http.get('/api/dashboard', () =>
        HttpResponse.json(
          dashboardRespuesta({ proyeccion: { datos_suficientes: false, anio: null, mes: null, monto: null } }),
        ),
      ),
    )
    renderizar()

    expect(
      await screen.findByText('Todavía no hay suficiente historial para proyectar el gasto del próximo mes.'),
    ).toBeInTheDocument()
  })

  it('hu12_ca3 diferencia la proyección de los meses de gasto real', async () => {
    servidor.use(http.get('/api/dashboard', () => HttpResponse.json(dashboardRespuesta())))
    renderizar()

    await screen.findByText('Proyección de gasto')
    expect(screen.getByText('Gasto real')).toBeInTheDocument()
    expect(screen.getByText('Proyección')).toBeInTheDocument()
  })

  it('hu13_ca1 muestra los meses con gasto anómalo detectados', async () => {
    servidor.use(http.get('/api/dashboard', () => HttpResponse.json(dashboardRespuesta())))
    renderizar()

    expect(await screen.findByText('Meses con gasto anómalo')).toBeInTheDocument()
    expect(screen.getByText('1 mes')).toBeInTheDocument()
  })

  it('hu13_ca2 indica que no hay datos suficientes para detectar anomalías', async () => {
    servidor.use(
      http.get('/api/dashboard', () =>
        HttpResponse.json(dashboardRespuesta({ anomalias: { datos_suficientes: false, meses: [] } })),
      ),
    )
    renderizar()

    expect(
      await screen.findByText('Todavía no hay suficiente historial para detectar meses anómalos.'),
    ).toBeInTheDocument()
  })

  it('hu13_ca3 muestra el mes anómalo con su monto y porcentaje', async () => {
    servidor.use(http.get('/api/dashboard', () => HttpResponse.json(dashboardRespuesta())))
    renderizar()

    expect(
      await screen.findByText('Julio 2026 · $820.000,00 · 40% más que el promedio de los otros meses'),
    ).toBeInTheDocument()
  })

  it('cambiar el mes vuelve a pedir el dashboard de ese mes', async () => {
    servidor.use(
      http.get('/api/dashboard', ({ request }) => {
        const url = new URL(request.url)
        if (url.searchParams.get('mes') === '2026-08') {
          return HttpResponse.json(
            dashboardRespuesta({
              mes: 8,
              ingresos: { monto: '500000.00', variacion_texto: 'Igual que en julio.' },
            }),
          )
        }
        return HttpResponse.json(dashboardRespuesta())
      }),
    )
    renderizar()
    await screen.findByText('$980.000,00')

    const usuario = userEvent.setup()
    await usuario.click(screen.getByLabelText('Mes'))
    await usuario.click(screen.getByRole('option', { name: 'agosto 2026' }))

    expect(await screen.findByText('$500.000,00')).toBeInTheDocument()
  })
})
