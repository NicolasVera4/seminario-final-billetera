import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { HttpResponse, http } from 'msw'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import Registro from './Registro'
import { servidor } from '../test/servidor'

const { navegarMock } = vi.hoisted(() => ({ navegarMock: vi.fn() }))

vi.mock('react-router-dom', async (importOriginal) => {
  const real = await importOriginal<typeof import('react-router-dom')>()
  return { ...real, useNavigate: () => navegarMock }
})

function renderizar() {
  return render(
    <MemoryRouter>
      <Registro />
    </MemoryRouter>,
  )
}

async function completarFormulario(datos: {
  nombre?: string
  correo?: string
  contrasena?: string
  repetirContrasena?: string
}) {
  const usuario = userEvent.setup()
  if (datos.nombre !== undefined) {
    await usuario.type(screen.getByLabelText('Nombre'), datos.nombre)
  }
  if (datos.correo !== undefined) {
    await usuario.type(screen.getByLabelText('Correo electrónico'), datos.correo)
  }
  if (datos.contrasena !== undefined) {
    await usuario.type(screen.getByLabelText('Contraseña'), datos.contrasena)
  }
  if (datos.repetirContrasena !== undefined) {
    await usuario.type(screen.getByLabelText('Repetir contraseña'), datos.repetirContrasena)
  }
  await usuario.click(screen.getByRole('button', { name: 'Crear cuenta' }))
}

describe('Registro', () => {
  it('muestra la ayuda de minimo 8 caracteres', () => {
    renderizar()

    expect(screen.getByText('Mínimo 8 caracteres.')).toBeInTheDocument()
  })

  it('hu01_ca4 datos validos crea la cuenta y redirige a iniciar sesion', async () => {
    servidor.use(
      http.post('/api/auth/registro', () =>
        HttpResponse.json(
          { id: 1, nombre: 'Luciano Vera', correo: 'luciano.vera@mail.com', rol: 'USUARIO' },
          { status: 201 },
        ),
      ),
    )
    renderizar()

    await completarFormulario({
      nombre: 'Luciano Vera',
      correo: 'luciano.vera@mail.com',
      contrasena: 'contrasena123',
      repetirContrasena: 'contrasena123',
    })

    expect(navegarMock).toHaveBeenCalledWith('/login')
  })

  it('hu01_ca1 correo ya registrado muestra el error bajo el campo', async () => {
    servidor.use(
      http.post('/api/auth/registro', () =>
        HttpResponse.json({ detail: 'Ya existe una cuenta con este correo.' }, { status: 409 }),
      ),
    )
    renderizar()

    await completarFormulario({
      nombre: 'Luciano Vera',
      correo: 'luciano.vera@mail.com',
      contrasena: 'contrasena123',
      repetirContrasena: 'contrasena123',
    })

    expect(
      await screen.findByText('Ya existe una cuenta con este correo. Iniciá sesión o usá otro correo.'),
    ).toBeInTheDocument()
  })

  it('hu01_ca3 campo obligatorio vacio se señala sin llamar a la API', async () => {
    renderizar()

    await completarFormulario({
      correo: 'luciano.vera@mail.com',
      contrasena: 'contrasena123',
      repetirContrasena: 'contrasena123',
    })

    expect(await screen.findByText('Este campo es obligatorio.')).toBeInTheDocument()
    expect(navegarMock).not.toHaveBeenCalled()
  })

  it('las contraseñas que no coinciden se señalan sin llamar a la API', async () => {
    renderizar()

    await completarFormulario({
      nombre: 'Luciano Vera',
      correo: 'luciano.vera@mail.com',
      contrasena: 'contrasena123',
      repetirContrasena: 'otra-contrasena',
    })

    expect(await screen.findByText('Las contraseñas no coinciden.')).toBeInTheDocument()
    expect(navegarMock).not.toHaveBeenCalled()
  })
})
