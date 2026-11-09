import { useEffect, useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import type { Catalogos } from '../api/catalogos'
import { obtenerCatalogos } from '../api/catalogos'
import type { ItemResumen } from '../api/archivos'
import { guardarMovimientos } from '../api/movimientos'
import Layout from '../componentes/Layout'
import { IconoAlerta, IconoArchivo, IconoCheck, IconoDescartar, IconoFlechaAtras } from '../componentes/iconos'

interface EstadoResumen {
  nombreArchivo: string
  paginasLeidas: number
  filasDescartadas?: number
  archivoRef: string
  comprobanteTipo: string
  items: ItemResumen[]
  conversacionId?: number
}

interface FilaResumen extends ItemResumen {
  id: number
  incluido: boolean
}

function formatearMonto(monto: number | string) {
  const formato = new Intl.NumberFormat('es-AR', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(Number(monto))
  return `$${formato}`
}

function formatearFecha(fechaIso: string) {
  const [anio, mes, dia] = fechaIso.split('-')
  return `${dia}/${mes}/${anio}`
}

function pluralizar(cantidad: number, singular: string, plural: string) {
  return `${cantidad} ${cantidad === 1 ? singular : plural}`
}

const ORIGEN_POR_COMPROBANTE: Record<string, string> = {
  RESUMEN_TARJETA: 'Resumen',
  EXTRACTO: 'Extracto',
}

export default function RevisionResumen() {
  const ubicacion = useLocation()
  const navegar = useNavigate()
  const estado = ubicacion.state as EstadoResumen

  const [catalogos, setCatalogos] = useState<Catalogos | null>(null)
  const [filas, setFilas] = useState<FilaResumen[]>(
    estado.items.map((item, indice) => ({ ...item, id: indice, incluido: !item.posible_duplicado })),
  )
  const [guardando, setGuardando] = useState(false)

  useEffect(() => {
    obtenerCatalogos()
      .then(setCatalogos)
      .catch(() => {})
  }, [])

  function actualizarFila(id: number, cambios: Partial<FilaResumen>) {
    setFilas((previas) => previas.map((fila) => (fila.id === id ? { ...fila, ...cambios } : fila)))
  }

  function descartarFila(id: number) {
    setFilas((previas) => previas.filter((fila) => fila.id !== id))
  }

  const cantidadDuplicados = filas.filter((f) => f.posible_duplicado).length
  const cantidadSinCategoria = filas.filter((f) => f.errores.includes('CATEGORIA_INVALIDA')).length
  const cantidadSinMedioPago = filas.filter((f) => f.errores.includes('MEDIO_PAGO_FALTANTE')).length
  const seleccionadas = filas.filter((f) => f.incluido)
  const totalSeleccionado = seleccionadas.reduce((acumulado, f) => acumulado + Number(f.monto), 0)
  const hayPendientesEnSeleccionadas = seleccionadas.some((f) => f.errores.length > 0)
  const puedeGuardar = seleccionadas.length > 0 && !hayPendientesEnSeleccionadas && !guardando

  async function manejarGuardar() {
    setGuardando(true)
    try {
      await guardarMovimientos(
        seleccionadas.map((fila) => ({
          monto: Number(fila.monto),
          fecha: fila.fecha,
          tipo: fila.tipo,
          descripcion: fila.descripcion,
          categoria_id: fila.categoria_id,
          medio_pago_id: fila.medio_pago_id,
          cuota_numero: fila.cuota_numero,
          cuota_total: fila.cuota_total,
          origen: ORIGEN_POR_COMPROBANTE[estado.comprobanteTipo] ?? 'Resumen',
          archivo_ref: estado.archivoRef,
          comprobante_tipo: estado.comprobanteTipo as 'RESUMEN_TARJETA' | 'EXTRACTO',
          conversacion_id: estado.conversacionId ?? null,
        })),
      )
      navegar('/chat')
    } finally {
      setGuardando(false)
    }
  }

  return (
    <Layout>
      <header className="top">
        <div className="t">
          <Link className="btn sm ghost" to="/chat">
            <IconoFlechaAtras />
            Volver al chat
          </Link>
        </div>
        <span className="dim" style={{ fontSize: 13 }}>
          Nada se guarda hasta que confirmes
        </span>
      </header>
      <div className="content">
        <div className="card" style={{ display: 'flex', alignItems: 'center', gap: 18 }}>
          <div className="logo" style={{ width: 44, height: 44 }}>
            <IconoArchivo />
          </div>
          <div style={{ flex: 1 }}>
            <h1>Revisá los consumos del resumen</h1>
            {estado.comprobanteTipo === 'EXTRACTO' ? (
              <p className="sub">
                {estado.nombreArchivo}, {estado.items.length + (estado.filasDescartadas ?? 0)} filas leídas,{' '}
                {estado.filasDescartadas ?? 0} descartadas.
              </p>
            ) : (
              <p className="sub">
                {estado.nombreArchivo}, {estado.paginasLeidas} páginas leídas. Medio de pago: tarjeta de
                crédito.
              </p>
            )}
          </div>
          <span className="pill">{pluralizar(filas.length, 'consumo detectado', 'consumos detectados')}</span>
          {cantidadDuplicados > 0 && (
            <span className="pill warn">
              <IconoAlerta />
              {pluralizar(cantidadDuplicados, 'posible duplicado', 'posibles duplicados')}
            </span>
          )}
          {cantidadSinCategoria > 0 && (
            <span className="pill bad">
              <IconoAlerta />
              {pluralizar(cantidadSinCategoria, 'categoría para elegir', 'categorías para elegir')}
            </span>
          )}
          {cantidadSinMedioPago > 0 && (
            <span className="pill bad">
              <IconoAlerta />
              {pluralizar(cantidadSinMedioPago, 'medio de pago para elegir', 'medios de pago para elegir')}
            </span>
          )}
        </div>

        <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
          <table>
            <thead>
              <tr>
                <th>Incluir</th>
                <th>Fecha</th>
                <th>Descripción</th>
                <th>Cuota</th>
                <th>Categoría</th>
                <th>Medio de pago</th>
                <th className="r">Monto</th>
                <th className="r">Acciones</th>
              </tr>
            </thead>
            <tbody>
              {filas.map((fila) => (
                <tr key={fila.id} style={fila.posible_duplicado ? { background: '#fffdf5' } : undefined}>
                  <td>
                    <input
                      type="checkbox"
                      aria-label={`Incluir ${fila.descripcion}`}
                      checked={fila.incluido}
                      onChange={(evento) => actualizarFila(fila.id, { incluido: evento.target.checked })}
                    />
                  </td>
                  <td className="num nw">{formatearFecha(fila.fecha)}</td>
                  <td>
                    {fila.descripcion}
                    {fila.posible_duplicado && (
                      <p className="dim" style={{ marginTop: 6, fontSize: 12 }}>
                        Posible duplicado de un gasto que cargaste el {formatearFecha(fila.fecha)}.
                      </p>
                    )}
                  </td>
                  <td className="dim nw">
                    {fila.cuota_numero && fila.cuota_total ? `${fila.cuota_numero} de ${fila.cuota_total}` : '—'}
                  </td>
                  <td>
                    {fila.categoria_id != null ? (
                      catalogos?.categorias.find((c) => c.id === fila.categoria_id)?.nombre
                    ) : (
                      <>
                        <label htmlFor={`categoria-${fila.id}`}>Categoría de {fila.descripcion}</label>
                        <select
                          className="sel bad"
                          id={`categoria-${fila.id}`}
                          value=""
                          onChange={(evento) =>
                            actualizarFila(fila.id, {
                              categoria_id: Number(evento.target.value),
                              errores: fila.errores.filter((e) => e !== 'CATEGORIA_INVALIDA'),
                            })
                          }
                        >
                          <option value="">Elegí una categoría</option>
                          {catalogos?.categorias.map((categoria) => (
                            <option key={categoria.id} value={categoria.id}>
                              {categoria.nombre}
                            </option>
                          ))}
                        </select>
                        {fila.categoria_sugerida && (
                          <p className="help-bad">&quot;{fila.categoria_sugerida}&quot; no está en el catálogo.</p>
                        )}
                      </>
                    )}
                  </td>
                  <td>
                    {fila.medio_pago_id != null ? (
                      catalogos?.medios_pago.find((m) => m.id === fila.medio_pago_id)?.nombre
                    ) : (
                      <>
                        <label htmlFor={`medio-pago-${fila.id}`}>Medio de pago de {fila.descripcion}</label>
                        <select
                          className="sel bad"
                          id={`medio-pago-${fila.id}`}
                          value=""
                          onChange={(evento) =>
                            actualizarFila(fila.id, {
                              medio_pago_id: Number(evento.target.value),
                              errores: fila.errores.filter((e) => e !== 'MEDIO_PAGO_FALTANTE'),
                            })
                          }
                        >
                          <option value="">Elegí un medio de pago</option>
                          {catalogos?.medios_pago.map((medioPago) => (
                            <option key={medioPago.id} value={medioPago.id}>
                              {medioPago.nombre}
                            </option>
                          ))}
                        </select>
                      </>
                    )}
                  </td>
                  <td className="r num neg nw">{formatearMonto(fila.monto)}</td>
                  <td className="r nw">
                    {fila.posible_duplicado && (
                      <button className="btn sm" type="button" onClick={() => actualizarFila(fila.id, { incluido: true })}>
                        <IconoCheck />
                        Guardar igual
                      </button>
                    )}
                    <button className="btn sm ghost" type="button" onClick={() => descartarFila(fila.id)}>
                      <IconoDescartar />
                      Descartar {fila.descripcion}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="card" style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{ flex: 1 }}>
            <b>
              {pluralizar(seleccionadas.length, 'movimiento seleccionado', 'movimientos seleccionados')} ·{' '}
              {formatearMonto(totalSeleccionado)}
            </b>
            {hayPendientesEnSeleccionadas && (
              <p className="sub">
                Elegí la categoría pendiente y decidí qué hacer con el posible duplicado para poder guardar.
              </p>
            )}
          </div>
          <Link className="btn ghost" to="/chat">
            Cancelar
          </Link>
          <button className="btn primary" type="button" onClick={manejarGuardar} disabled={!puedeGuardar}>
            <IconoCheck />
            Guardar {seleccionadas.length} movimientos
          </button>
        </div>
      </div>
    </Layout>
  )
}
