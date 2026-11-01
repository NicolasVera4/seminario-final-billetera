import { useEffect, useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import type { Catalogos } from '../api/catalogos'
import { obtenerCatalogos } from '../api/catalogos'
import type { ItemResumen } from '../api/archivos'
import { guardarMovimientos } from '../api/movimientos'

interface EstadoResumen {
  nombreArchivo: string
  paginasLeidas: number
  archivoRef: string
  comprobanteTipo: string
  items: ItemResumen[]
}

interface FilaResumen extends ItemResumen {
  id: number
  incluido: boolean
}

function formatearMonto(monto: number) {
  const formato = new Intl.NumberFormat('es-AR', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(monto)
  return `$${formato}`
}

function formatearFecha(fechaIso: string) {
  const [anio, mes, dia] = fechaIso.split('-')
  return `${dia}/${mes}/${anio}`
}

function pluralizar(cantidad: number, singular: string, plural: string) {
  return `${cantidad} ${cantidad === 1 ? singular : plural}`
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
  const seleccionadas = filas.filter((f) => f.incluido)
  const totalSeleccionado = seleccionadas.reduce((acumulado, f) => acumulado + f.monto, 0)
  const hayPendientesEnSeleccionadas = seleccionadas.some((f) => f.errores.length > 0)
  const puedeGuardar = seleccionadas.length > 0 && !hayPendientesEnSeleccionadas && !guardando

  async function manejarGuardar() {
    setGuardando(true)
    try {
      await guardarMovimientos(
        seleccionadas.map((fila) => ({
          monto: fila.monto,
          fecha: fila.fecha,
          tipo: fila.tipo,
          descripcion: fila.descripcion,
          categoria_id: fila.categoria_id,
          medio_pago_id: fila.medio_pago_id,
          cuota_numero: fila.cuota_numero,
          cuota_total: fila.cuota_total,
          origen: 'Resumen',
          archivo_ref: estado.archivoRef,
          comprobante_tipo: estado.comprobanteTipo as 'RESUMEN_TARJETA',
        })),
      )
      navegar('/historial')
    } finally {
      setGuardando(false)
    }
  }

  return (
    <div>
      <Link to="/chat">Volver al chat</Link>
      <p>Nada se guarda hasta que confirmes</p>

      <h1>Revisá los consumos del resumen</h1>
      <p>
        {estado.nombreArchivo}, {estado.paginasLeidas} páginas leídas. Medio de pago: tarjeta de crédito.
      </p>

      <p>{pluralizar(filas.length, 'consumo detectado', 'consumos detectados')}</p>
      {cantidadDuplicados > 0 && (
        <p>{pluralizar(cantidadDuplicados, 'posible duplicado', 'posibles duplicados')}</p>
      )}
      {cantidadSinCategoria > 0 && (
        <p>{pluralizar(cantidadSinCategoria, 'categoría para elegir', 'categorías para elegir')}</p>
      )}

      <table>
        <thead>
          <tr>
            <th>Incluir</th>
            <th>Fecha</th>
            <th>Descripción</th>
            <th>Cuota</th>
            <th>Categoría</th>
            <th>Monto</th>
            <th>Acciones</th>
          </tr>
        </thead>
        <tbody>
          {filas.map((fila) => (
            <tr key={fila.id}>
              <td>
                <input
                  type="checkbox"
                  aria-label={`Incluir ${fila.descripcion}`}
                  checked={fila.incluido}
                  onChange={(evento) => actualizarFila(fila.id, { incluido: evento.target.checked })}
                />
              </td>
              <td>{formatearFecha(fila.fecha)}</td>
              <td>
                {fila.descripcion}
                {fila.posible_duplicado && (
                  <p>Posible duplicado de un gasto que cargaste el {formatearFecha(fila.fecha)}.</p>
                )}
              </td>
              <td>{fila.cuota_numero && fila.cuota_total ? `${fila.cuota_numero} de ${fila.cuota_total}` : '—'}</td>
              <td>
                {fila.categoria_id != null ? (
                  catalogos?.categorias.find((c) => c.id === fila.categoria_id)?.nombre
                ) : (
                  <>
                    <label htmlFor={`categoria-${fila.id}`}>Categoría de {fila.descripcion}</label>
                    <select
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
                    <p>&quot;{fila.categoria_sugerida}&quot; no está en el catálogo.</p>
                  </>
                )}
              </td>
              <td>{formatearMonto(fila.monto)}</td>
              <td>
                {fila.posible_duplicado && (
                  <button type="button" onClick={() => actualizarFila(fila.id, { incluido: true })}>
                    Guardar igual
                  </button>
                )}
                <button type="button" onClick={() => descartarFila(fila.id)}>
                  Descartar {fila.descripcion}
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <p>
        {pluralizar(seleccionadas.length, 'movimiento seleccionado', 'movimientos seleccionados')} ·{' '}
        {formatearMonto(totalSeleccionado)}
      </p>
      {hayPendientesEnSeleccionadas && (
        <p>Elegí la categoría pendiente y decidí qué hacer con el posible duplicado para poder guardar.</p>
      )}
      <Link to="/chat">Cancelar</Link>
      <button type="button" onClick={manejarGuardar} disabled={!puedeGuardar}>
        Guardar {seleccionadas.length} movimientos
      </button>
    </div>
  )
}
