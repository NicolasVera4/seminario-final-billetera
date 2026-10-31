import { HttpResponse, http } from 'msw'
import { describe, expect, it, vi } from 'vitest'
import { alVencerSesion, guardarToken, obtenerToken, solicitar } from './cliente'
import { servidor } from '../test/servidor'

describe('cliente API', () => {
  it('hu02_ca4 al recibir 401 borra el token y avisa que la sesion vencio', async () => {
    servidor.use(http.get('/api/algo', () => new HttpResponse(null, { status: 401 })))
    guardarToken('token-viejo')
    const manejador = vi.fn()
    alVencerSesion(manejador)

    await expect(solicitar('/algo')).rejects.toThrow()

    expect(obtenerToken()).toBeNull()
    expect(manejador).toHaveBeenCalledOnce()
  })

  it('reemplaza el token guardado cuando la respuesta trae X-Token-Renovado', async () => {
    servidor.use(
      http.get('/api/algo', () =>
        HttpResponse.json({}, { headers: { 'X-Token-Renovado': 'token-nuevo' } })
      )
    )
    guardarToken('token-viejo')

    await solicitar('/algo')

    expect(obtenerToken()).toBe('token-nuevo')
  })
})
