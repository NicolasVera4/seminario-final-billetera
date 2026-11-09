import { useEffect, useState, type FormEvent } from 'react'
import type { DocumentoReferencia } from '../api/admin'
import { cargarDocumento, eliminarDocumento, listarDocumentos } from '../api/admin'
import { ErrorApi } from '../api/cliente'
import Layout from '../componentes/Layout'
import { IconoDescartar, IconoDocumento } from '../componentes/iconos'

function formatearFecha(fechaIso: string) {
  return new Date(fechaIso).toLocaleDateString('es-AR')
}

export default function AdminDocumentos() {
  const [documentos, setDocumentos] = useState<DocumentoReferencia[]>([])
  const [titulo, setTitulo] = useState('')
  const [archivo, setArchivo] = useState<File | null>(null)
  const [cargando, setCargando] = useState(false)
  const [error, setError] = useState<string | null>(null)

  function actualizar() {
    listarDocumentos()
      .then(setDocumentos)
      .catch(() => {})
  }

  useEffect(actualizar, [])

  async function manejarEnvio(evento: FormEvent) {
    evento.preventDefault()
    if (!titulo.trim() || !archivo) return

    setCargando(true)
    setError(null)
    try {
      await cargarDocumento(titulo.trim(), archivo)
      setTitulo('')
      setArchivo(null)
      actualizar()
    } catch (err) {
      setError(err instanceof ErrorApi ? err.message : 'No pudimos cargar el documento.')
    } finally {
      setCargando(false)
    }
  }

  async function manejarEliminar(id: number) {
    await eliminarDocumento(id)
    actualizar()
  }

  return (
    <Layout>
      <header className="top">
        <div className="t">
          <div>
            <h1>Documentación de referencia</h1>
            <p>Los documentos que Qash usa para dar consejos de asesoramiento</p>
          </div>
        </div>
      </header>
      <div className="content">
        <div className="card">
          <h2>Cargar un documento</h2>
          <p className="sub">PDF o texto plano</p>
          <form className="fila" onSubmit={manejarEnvio} style={{ marginTop: 14 }}>
            <div className="fl" style={{ flex: 1, minWidth: 200 }}>
              <label htmlFor="titulo">Título</label>
              <input
                className="inp"
                id="titulo"
                value={titulo}
                onChange={(evento) => setTitulo(evento.target.value)}
              />
            </div>
            <div className="fl">
              <label htmlFor="archivo">Archivo</label>
              <input
                id="archivo"
                type="file"
                accept="application/pdf,text/plain"
                onChange={(evento) => setArchivo(evento.target.files?.[0] ?? null)}
              />
            </div>
            <button className="btn primary" type="submit" disabled={cargando || !titulo.trim() || !archivo}>
              Cargar documento
            </button>
          </form>
          {error && (
            <p className="help-bad" style={{ marginTop: 10 }}>
              {error}
            </p>
          )}
        </div>

        {documentos.length === 0 ? (
          <p className="dim">Todavía no cargaste ningún documento.</p>
        ) : (
          <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
            <table>
              <thead>
                <tr>
                  <th>Título</th>
                  <th>Fragmentos</th>
                  <th>Cargado</th>
                  <th className="r">Acciones</th>
                </tr>
              </thead>
              <tbody>
                {documentos.map((documento) => (
                  <tr key={documento.id}>
                    <td>
                      <span style={{ display: 'inline-flex', alignItems: 'center', gap: 8 }}>
                        <IconoDocumento />
                        {documento.titulo}
                      </span>
                    </td>
                    <td className="dim num">{documento.cantidad_fragmentos}</td>
                    <td className="dim nw">{formatearFecha(documento.creado_en)}</td>
                    <td className="r nw">
                      <button
                        className="btn sm ghost"
                        type="button"
                        onClick={() => manejarEliminar(documento.id)}
                      >
                        <IconoDescartar />
                        Eliminar {documento.titulo}
                      </button>
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
