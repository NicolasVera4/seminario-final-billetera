import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { HttpResponse, http } from 'msw'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it } from 'vitest'
import AdminUsuarios from './AdminUsuarios'
import { guardarToken } from '../api/cliente'
import { servidor } from '../test/servidor'

function renderizar() {
  return render(
    <MemoryRouter>
      <AdminUsuarios />
    </MemoryRouter>,
  )
}

beforeEach(() => {
  guardarToken('token-valido')
})

describe('AdminUsuarios', () => {
  it('lista los usuarios con su estado', async () => {
    servidor.use(
      http.get('/api/admin/usuarios', () =>
        HttpResponse.json([
          { id: 1, nombre: 'Usuaria Activa', correo: 'activa@mail.com', activo: true, bloqueado_hasta: null },
          {
            id: 2,
            nombre: 'Usuaria Bloqueada',
            correo: 'bloqueada@mail.com',
            activo: true,
            bloqueado_hasta: '2026-11-09T13:00:00Z',
          },
          { id: 3, nombre: 'Usuaria De Baja', correo: 'baja@mail.com', activo: false, bloqueado_hasta: null },
        ]),
      ),
    )
    renderizar()

    expect(await screen.findByText('Usuaria Activa')).toBeInTheDocument()
    expect(screen.getByText('Activa')).toBeInTheDocument()
    expect(screen.getByText('Bloqueada')).toBeInTheDocument()
    expect(screen.getByText('De baja')).toBeInTheDocument()
  })

  it('desbloquea a una usuaria bloqueada', async () => {
    let bloqueadoHasta: string | null = '2026-11-09T13:00:00Z'
    servidor.use(
      http.get('/api/admin/usuarios', () =>
        HttpResponse.json([
          { id: 2, nombre: 'Usuaria Bloqueada', correo: 'bloqueada@mail.com', activo: true, bloqueado_hasta: bloqueadoHasta },
        ]),
      ),
      http.patch('/api/admin/usuarios/2', () => {
        bloqueadoHasta = null
        return HttpResponse.json({
          id: 2,
          nombre: 'Usuaria Bloqueada',
          correo: 'bloqueada@mail.com',
          activo: true,
          bloqueado_hasta: null,
        })
      }),
    )
    renderizar()
    const usuario = userEvent.setup()
    await screen.findByText('Bloqueada')

    await usuario.click(screen.getByRole('button', { name: 'Desbloquear a Usuaria Bloqueada' }))

    expect(await screen.findByText('Activa')).toBeInTheDocument()
  })

  it('da de baja a una usuaria activa', async () => {
    let activo = true
    servidor.use(
      http.get('/api/admin/usuarios', () =>
        HttpResponse.json([
          { id: 1, nombre: 'Usuaria Activa', correo: 'activa@mail.com', activo, bloqueado_hasta: null },
        ]),
      ),
      http.patch('/api/admin/usuarios/1', () => {
        activo = false
        return HttpResponse.json({ id: 1, nombre: 'Usuaria Activa', correo: 'activa@mail.com', activo: false, bloqueado_hasta: null })
      }),
    )
    renderizar()
    const usuario = userEvent.setup()
    await screen.findByText('Activa')

    await usuario.click(screen.getByRole('button', { name: 'Dar de baja a Usuaria Activa' }))

    expect(await screen.findByText('De baja')).toBeInTheDocument()
  })
})
