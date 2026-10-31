import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it } from 'vitest'
import BarraLateral from './BarraLateral'

describe('BarraLateral', () => {
  it('muestra los links de navegación a Chat e Historial', () => {
    render(
      <MemoryRouter>
        <BarraLateral />
      </MemoryRouter>,
    )

    expect(screen.getByRole('link', { name: 'Chat' })).toHaveAttribute('href', '/')
    expect(screen.getByRole('link', { name: 'Historial' })).toHaveAttribute('href', '/historial')
  })
})
