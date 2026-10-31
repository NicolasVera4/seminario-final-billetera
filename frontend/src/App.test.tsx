import { render, screen } from '@testing-library/react'
import { beforeEach, describe, expect, it } from 'vitest'
import App from './App'
import { borrarToken } from './api/cliente'

describe('App', () => {
  beforeEach(() => {
    borrarToken()
  })

  it('sin sesión, la ruta raíz redirige a Iniciar sesión', () => {
    render(<App />)

    expect(screen.getByRole('heading', { name: 'Iniciar sesión' })).toBeInTheDocument()
  })
})
