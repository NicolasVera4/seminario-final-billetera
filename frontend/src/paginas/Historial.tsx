import { useEffect, useState, type ChangeEvent } from 'react'
import type { Catalogos } from '../api/catalogos'
import { obtenerCatalogos } from '../api/catalogos'
import type { FiltrosHistorial, MovimientoListado } from '../api/movimientos'
import { listarMovimientos } from '../api/movimientos'
import Layout from '../componentes/Layout'
import { IconoFlechaAdelante, IconoFlechaAtras } from '../componentes/iconos'

const POR_PAGINA = 15

function formatearMonto(monto: number, tipo: 'INGRESO' | 'EGRESO') {
  const formato = new Intl.NumberFormat('es-AR', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(monto)
  const signo = tipo === 'EGRESO' ? '−' : '+'
  return `${signo}$${formato}`
}

export default function Historial() {
  const [catalogos, setCatalogos] = useState<Catalogos | null>(null)
  const [desde, setDesde] = useState('')
  const [hasta, setHasta] = useState('')
  const [categoriaId, setCategoriaId] = useState<number | ''>('')
  const [tipo, setTipo] = useState<'' | 'INGRESO' | 'EGRESO'>('')
  const [medioPagoId, setMedioPagoId] = useState<number | ''>('')
  const [q, setQ] = useState('')
  const [pagina, setPagina] = useState(1)
  const [items, setItems] = useState<MovimientoListado[]>([])
  const [total, setTotal] = useState(0)

  useEffect(() => {
    obtenerCatalogos()
      .then(setCatalogos)
      .catch(() => {})
  }, [])

  useEffect(() => {
    const filtros: FiltrosHistorial = {
      desde: desde || undefined,
      hasta: hasta || undefined,
      categoria_id: categoriaId || undefined,
      tipo: tipo || undefined,
      medio_pago_id: medioPagoId || undefined,
      q: q || undefined,
      pagina,
      por_pagina: POR_PAGINA,
    }
    listarMovimientos(filtros)
      .then((resultado) => {
        setItems(resultado.items)
        setTotal(resultado.total)
      })
      .catch(() => {})
  }, [desde, hasta, categoriaId, tipo, medioPagoId, q, pagina])

  function conFiltro<T>(actualizar: (valor: T) => void) {
    return (valor: T) => {
      setPagina(1)
      actualizar(valor)
    }
  }

  function limpiarFiltros() {
    setDesde('')
    setHasta('')
    setCategoriaId('')
    setTipo('')
    setMedioPagoId('')
    setQ('')
    setPagina(1)
  }

  const totalPaginas = Math.max(1, Math.ceil(total / POR_PAGINA))

  return (
    <Layout>
      <header className="top">
        <div className="t">
          <div>
            <h1>Historial de movimientos</h1>
            <p>Todos tus ingresos y gastos, del más reciente al más antiguo</p>
          </div>
        </div>
      </header>
      <div className="content">
        <div className="card">
          <form className="fila" onSubmit={(evento) => evento.preventDefault()}>
            <div className="fl" style={{ flex: 1, minWidth: 200 }}>
              <label htmlFor="buscar">Buscar</label>
              <input
                className="inp"
                id="buscar"
                placeholder="Descripción o monto"
                value={q}
                onChange={(evento) => conFiltro(setQ)(evento.target.value)}
              />
            </div>

            <div className="fl">
              <label htmlFor="desde">Desde</label>
              <input
                className="inp"
                id="desde"
                type="date"
                value={desde}
                onChange={(evento) => conFiltro(setDesde)(evento.target.value)}
              />
            </div>

            <div className="fl">
              <label htmlFor="hasta">Hasta</label>
              <input
                className="inp"
                id="hasta"
                type="date"
                value={hasta}
                onChange={(evento) => conFiltro(setHasta)(evento.target.value)}
              />
            </div>

            <div className="fl">
              <label htmlFor="categoria">Categoría</label>
              <select
                className="sel"
                id="categoria"
                value={categoriaId}
                onChange={(evento: ChangeEvent<HTMLSelectElement>) =>
                  conFiltro(setCategoriaId)(evento.target.value ? Number(evento.target.value) : '')
                }
              >
                <option value="">Todas</option>
                {catalogos?.categorias.map((categoria) => (
                  <option key={categoria.id} value={categoria.id}>
                    {categoria.nombre}
                  </option>
                ))}
              </select>
            </div>

            <div className="fl">
              <label htmlFor="tipo">Tipo</label>
              <select
                className="sel"
                id="tipo"
                value={tipo}
                onChange={(evento: ChangeEvent<HTMLSelectElement>) =>
                  conFiltro(setTipo)(evento.target.value as '' | 'INGRESO' | 'EGRESO')
                }
              >
                <option value="">Todos</option>
                <option value="EGRESO">Egreso</option>
                <option value="INGRESO">Ingreso</option>
              </select>
            </div>

            <div className="fl">
              <label htmlFor="medio_pago">Medio de pago</label>
              <select
                className="sel"
                id="medio_pago"
                value={medioPagoId}
                onChange={(evento: ChangeEvent<HTMLSelectElement>) =>
                  conFiltro(setMedioPagoId)(evento.target.value ? Number(evento.target.value) : '')
                }
              >
                <option value="">Todos</option>
                {catalogos?.medios_pago.map((medio) => (
                  <option key={medio.id} value={medio.id}>
                    {medio.nombre}
                  </option>
                ))}
              </select>
            </div>

            <button className="btn ghost" type="button" onClick={limpiarFiltros}>
              Limpiar
            </button>
          </form>
        </div>

        {items.length === 0 ? (
          <p className="dim">No encontramos movimientos para esos criterios.</p>
        ) : (
          <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
            <table>
              <thead>
                <tr>
                  <th>Fecha</th>
                  <th>Descripción</th>
                  <th>Categoría</th>
                  <th>Medio de pago</th>
                  <th>Origen</th>
                  <th className="r">Monto</th>
                </tr>
              </thead>
              <tbody>
                {items.map((item) => (
                  <tr key={item.id}>
                    <td className="num dim nw">{item.fecha}</td>
                    <td>{item.descripcion}</td>
                    <td>{item.categoria ?? ''}</td>
                    <td>{item.medio_pago ?? ''}</td>
                    <td className="dim">{item.origen}</td>
                    <td className={`r num nw ${item.tipo === 'EGRESO' ? 'neg' : 'pos'}`}>
                      {formatearMonto(item.monto, item.tipo)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '12px 16px',
                borderTop: '1px solid var(--line)',
              }}
            >
              <span className="dim">
                Mostrando {items.length} de {total} movimientos
              </span>
              <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
                <button
                  className="btn sm"
                  type="button"
                  onClick={() => setPagina((p) => Math.max(1, p - 1))}
                  disabled={pagina <= 1}
                >
                  <IconoFlechaAtras />
                  Página anterior
                </button>
                <button
                  className="btn sm"
                  type="button"
                  onClick={() => setPagina((p) => Math.min(totalPaginas, p + 1))}
                  disabled={pagina >= totalPaginas}
                >
                  Página siguiente
                  <IconoFlechaAdelante />
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </Layout>
  )
}
