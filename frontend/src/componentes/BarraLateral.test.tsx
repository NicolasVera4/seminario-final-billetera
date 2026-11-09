import { render, screen } from '@testing-library/react'
import { HttpResponse, http } from 'msw'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it } from 'vitest'
import BarraLateral from './BarraLateral'
import { servidor } from '../test/servidor'

function renderizar() {
  return render(
    <MemoryRouter>
      <BarraLateral />
    </MemoryRouter>,
  )
}

describe('BarraLateral', () => {
  it('para un usuario, muestra los links de navegación a Dashboard, Chat e Historial', async () => {
    renderizar()

    expect(await screen.findByRole('link', { name: 'Dashboard' })).toHaveAttribute('href', '/dashboard')
    expect(screen.getByRole('link', { name: 'Chat' })).toHaveAttribute('href', '/chat')
    expect(screen.getByRole('link', { name: 'Historial' })).toHaveAttribute('href', '/historial')
  })

  it('para un administrador, muestra Documentación y Usuarios en vez de Dashboard/Chat/Historial', async () => {
    servidor.use(
      http.get('/api/auth/yo', () =>
        HttpResponse.json({ id: 2, nombre: 'Admin', correo: 'admin@mail.com', rol: 'ADMINISTRADOR' }),
      ),
    )
    renderizar()

    expect(await screen.findByRole('link', { name: 'Documentación' })).toHaveAttribute(
      'href',
      '/admin/documentos',
    )
    expect(screen.getByRole('link', { name: 'Usuarios' })).toHaveAttribute('href', '/admin/usuarios')
    expect(screen.queryByRole('link', { name: 'Dashboard' })).not.toBeInTheDocument()
    expect(screen.queryByRole('link', { name: 'Chat' })).not.toBeInTheDocument()
    expect(screen.queryByRole('link', { name: 'Historial' })).not.toBeInTheDocument()
  })
})
