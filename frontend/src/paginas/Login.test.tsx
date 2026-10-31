import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { HttpResponse, http } from 'msw'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import Login from './Login'
import { servidor } from '../test/servidor'

const { navegarMock } = vi.hoisted(() => ({ navegarMock: vi.fn() }))

vi.mock('react-router-dom', async (importOriginal) => {
  const real = await importOriginal<typeof import('react-router-dom')>()
  return { ...real, useNavigate: () => navegarMock }
})

function renderizar() {
  return render(
    <MemoryRouter>
      <Login />
    </MemoryRouter>,
  )
}

async function completarFormulario(correo: string, contrasena: string) {
  const usuario = userEvent.setup()
  await usuario.type(screen.getByLabelText('Correo electrónico'), correo)
  await usuario.type(screen.getByLabelText('Contraseña'), contrasena)
  await usuario.click(screen.getByRole('button', { name: 'Iniciar sesión' }))
}

describe('Login', () => {
  it('hu02_ca1 mensaje unico cuando el correo o la contrasena son incorrectos', async () => {
    servidor.use(
      http.post('/api/auth/login', () =>
        HttpResponse.json({ detail: 'El correo o la contraseña no son correctos.' }, { status: 401 }),
      ),
    )
    renderizar()

    await completarFormulario('luciano.vera@mail.com', 'incorrecta')

    expect(
      await screen.findByText('El correo o la contraseña no son correctos. Revisalos e intentá de nuevo.'),
    ).toBeInTheDocument()
  })

  it('hu02_ca2 datos correctos accede a la pantalla principal', async () => {
    servidor.use(
      http.post('/api/auth/login', () =>
        HttpResponse.json({ access_token: 'token-valido', token_type: 'bearer' }),
      ),
    )
    renderizar()

    await completarFormulario('luciano.vera@mail.com', 'contrasena123')

    expect(navegarMock).toHaveBeenCalledWith('/')
  })
})
