import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { describe, expect, it } from 'vitest'
import RutaProtegida from './RutaProtegida'
import { borrarToken, guardarToken } from '../api/cliente'

function renderizar() {
  return render(
    <MemoryRouter initialEntries={['/']}>
      <Routes>
        <Route
          path="/"
          element={
            <RutaProtegida>
              <div>Contenido protegido</div>
            </RutaProtegida>
          }
        />
        <Route path="/login" element={<div>Pantalla de login</div>} />
      </Routes>
    </MemoryRouter>,
  )
}

describe('RutaProtegida', () => {
  it('redirige a login si no hay token', () => {
    borrarToken()
    renderizar()

    expect(screen.getByText('Pantalla de login')).toBeInTheDocument()
  })

  it('muestra el contenido si hay token', () => {
    guardarToken('token-valido')
    renderizar()

    expect(screen.getByText('Contenido protegido')).toBeInTheDocument()
  })
})
