import { HttpResponse, http } from 'msw'
import { setupServer } from 'msw/node'

export const servidor = setupServer(
  http.get('/api/auth/yo', () =>
    HttpResponse.json({ id: 1, nombre: 'Usuaria de prueba', correo: 'usuaria@mail.com', rol: 'USUARIO' }),
  ),
)
