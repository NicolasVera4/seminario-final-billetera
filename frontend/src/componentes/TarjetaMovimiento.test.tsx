import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { HttpResponse, http } from 'msw'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import TarjetaMovimiento from './TarjetaMovimiento'
import { servidor } from '../test/servidor'

const CATALOGOS = {
  categorias: [
    { id: 1, nombre: 'Supermercado' },
    { id: 2, nombre: 'Restaurantes' },
  ],
  medios_pago: [
    { id: 1, nombre: 'Efectivo' },
    { id: 2, nombre: 'Débito' },
  ],
  origenes: [{ id: 1, nombre: 'Texto' }],
}

const BORRADOR_VALIDO = {
  monto: 15000,
  fecha: '2026-10-31',
  tipo: 'EGRESO' as const,
  descripcion: 'Compra en el súper',
  categoria_id: 1,
  categoria_sugerida: null,
  medio_pago_id: 2,
}

function mockearValidar(errores: string[], advertencias: string[] = []) {
  servidor.use(
    http.post('/api/movimientos/validar', () => HttpResponse.json({ errores, advertencias })),
  )
}

beforeEach(() => {
  servidor.use(http.get('/api/catalogos', () => HttpResponse.json(CATALOGOS)))
})

afterEach(() => {
  vi.restoreAllMocks()
})

describe('TarjetaMovimiento', () => {
  it('hu04_ca1 monto invalido deshabilita Guardar y lo señala', async () => {
    mockearValidar(['MONTO_INVALIDO'])
    render(<TarjetaMovimiento borrador={{ ...BORRADOR_VALIDO, monto: 0 }} />)

    expect(await screen.findByText(/el monto/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Guardar movimiento' })).toBeDisabled()
  })

  it('hu04_ca2 categoria fuera de catálogo muestra select con el motivo', async () => {
    mockearValidar(['CATEGORIA_INVALIDA'])
    render(
      <TarjetaMovimiento
        borrador={{ ...BORRADOR_VALIDO, categoria_id: null, categoria_sugerida: 'Gimnasio' }}
      />,
    )

    expect(await screen.findByText('"Gimnasio" no está en el catálogo. Elegí una.')).toBeInTheDocument()
    expect(screen.getByLabelText('Categoría')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Guardar movimiento' })).toBeDisabled()
  })

  it('hu04_ca3 sin medio de pago muestra select con el motivo', async () => {
    mockearValidar(['MEDIO_PAGO_FALTANTE'])
    render(<TarjetaMovimiento borrador={{ ...BORRADOR_VALIDO, medio_pago_id: null }} />)

    expect(await screen.findByText('El mensaje no indica cómo pagaste.')).toBeInTheDocument()
    expect(screen.getByLabelText('Medio de pago')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Guardar movimiento' })).toBeDisabled()
  })

  it('al elegir la categoría faltante se revalida y se habilita Guardar', async () => {
    mockearValidar(['CATEGORIA_INVALIDA'])
    render(
      <TarjetaMovimiento
        borrador={{ ...BORRADOR_VALIDO, categoria_id: null, categoria_sugerida: 'Gimnasio' }}
      />,
    )
    await screen.findByText('"Gimnasio" no está en el catálogo. Elegí una.')

    mockearValidar([])
    const usuario = userEvent.setup()
    await usuario.selectOptions(screen.getByLabelText('Categoría'), 'Restaurantes')

    expect(await screen.findByRole('button', { name: 'Guardar movimiento' })).toBeEnabled()
  })

  it('hu04_ca4 posible duplicado muestra el aviso y Guardar sigue habilitado', async () => {
    mockearValidar([], ['POSIBLE_DUPLICADO'])
    render(<TarjetaMovimiento borrador={BORRADOR_VALIDO} />)

    expect(await screen.findByText(/posible duplicado/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Guardar movimiento' })).toBeEnabled()
  })

  it('hu04_ca5 movimiento valido confirmado se guarda', async () => {
    mockearValidar([])
    servidor.use(
      http.post('/api/movimientos', () =>
        HttpResponse.json(
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
        ),
      ),
    )
    const alGuardar = vi.fn()
    render(<TarjetaMovimiento borrador={BORRADOR_VALIDO} onGuardado={alGuardar} />)
    await screen.findByRole('button', { name: 'Guardar movimiento' })

    const usuario = userEvent.setup()
    await usuario.click(screen.getByRole('button', { name: 'Guardar movimiento' }))

    expect(await screen.findByText('Movimiento registrado')).toBeInTheDocument()
    expect(screen.getByText('Guardado')).toBeInTheDocument()
    expect(alGuardar).toHaveBeenCalledOnce()
  })

  it('el botón Editar habilita editar el monto', async () => {
    mockearValidar([])
    render(<TarjetaMovimiento borrador={BORRADOR_VALIDO} />)
    await screen.findByRole('button', { name: 'Guardar movimiento' })

    const usuario = userEvent.setup()
    await usuario.click(screen.getByRole('button', { name: 'Editar' }))

    expect(screen.getByLabelText('Monto')).toBeInTheDocument()
  })

  it('al guardar, envía conversacion_id y mensaje_id para poder reconstruir el historial', async () => {
    mockearValidar([])
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
    render(<TarjetaMovimiento borrador={BORRADOR_VALIDO} conversacionId={7} mensajeId={42} />)
    await screen.findByRole('button', { name: 'Guardar movimiento' })

    const usuario = userEvent.setup()
    await usuario.click(screen.getByRole('button', { name: 'Guardar movimiento' }))

    await screen.findByText('Guardado')
    expect(cuerpoEnviado).toMatchObject([{ conversacion_id: 7, mensaje_id: 42 }])
  })

  it('con yaGuardado, muestra directamente la tarjeta de movimiento registrado sin validar de nuevo', async () => {
    render(<TarjetaMovimiento borrador={BORRADOR_VALIDO} yaGuardado />)

    expect(await screen.findByText('Movimiento registrado')).toBeInTheDocument()
    expect(screen.getByText('Guardado')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Guardar movimiento' })).not.toBeInTheDocument()
  })

  it('el botón Descartar avisa al padre', async () => {
    mockearValidar([])
    const alDescartar = vi.fn()
    render(<TarjetaMovimiento borrador={BORRADOR_VALIDO} onDescartado={alDescartar} />)
    await screen.findByRole('button', { name: 'Guardar movimiento' })

    const usuario = userEvent.setup()
    await usuario.click(screen.getByRole('button', { name: 'Descartar' }))

    expect(alDescartar).toHaveBeenCalledOnce()
  })
})
