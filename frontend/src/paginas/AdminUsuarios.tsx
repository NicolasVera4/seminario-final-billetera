import { useEffect, useState } from 'react'
import type { AdminUsuario } from '../api/admin'
import { editarUsuario, listarUsuarios } from '../api/admin'
import Layout from '../componentes/Layout'
import { IconoCheck, IconoDesbloquear } from '../componentes/iconos'

export default function AdminUsuarios() {
  const [usuarios, setUsuarios] = useState<AdminUsuario[]>([])

  function actualizar() {
    listarUsuarios()
      .then(setUsuarios)
      .catch(() => {})
  }

  useEffect(actualizar, [])

  async function manejarDesbloquear(id: number) {
    await editarUsuario(id, { desbloquear: true })
    actualizar()
  }

  async function manejarActivo(id: number, activo: boolean) {
    await editarUsuario(id, { activo })
    actualizar()
  }

  return (
    <Layout>
      <header className="top">
        <div className="t">
          <div>
            <h1>Usuarios</h1>
            <p>Cuentas registradas en Qash</p>
          </div>
        </div>
      </header>
      <div className="content">
        {usuarios.length === 0 ? (
          <p className="dim">Todavía no hay usuarios registrados.</p>
        ) : (
          <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
            <table>
              <thead>
                <tr>
                  <th>Nombre</th>
                  <th>Correo</th>
                  <th>Estado</th>
                  <th className="r">Acciones</th>
                </tr>
              </thead>
              <tbody>
                {usuarios.map((usuario) => (
                  <tr key={usuario.id}>
                    <td>{usuario.nombre}</td>
                    <td className="dim">{usuario.correo}</td>
                    <td>
                      {!usuario.activo ? (
                        <span className="pill bad">De baja</span>
                      ) : usuario.bloqueado_hasta ? (
                        <span className="pill warn">Bloqueada</span>
                      ) : (
                        <span className="pill ok">Activa</span>
                      )}
                    </td>
                    <td className="r nw">
                      {usuario.bloqueado_hasta && (
                        <button
                          className="btn sm"
                          type="button"
                          onClick={() => manejarDesbloquear(usuario.id)}
                        >
                          <IconoDesbloquear />
                          Desbloquear a {usuario.nombre}
                        </button>
                      )}
                      {usuario.activo ? (
                        <button
                          className="btn sm ghost"
                          type="button"
                          onClick={() => manejarActivo(usuario.id, false)}
                        >
                          Dar de baja a {usuario.nombre}
                        </button>
                      ) : (
                        <button
                          className="btn sm"
                          type="button"
                          onClick={() => manejarActivo(usuario.id, true)}
                        >
                          <IconoCheck />
                          Reactivar a {usuario.nombre}
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </Layout>
  )
}
