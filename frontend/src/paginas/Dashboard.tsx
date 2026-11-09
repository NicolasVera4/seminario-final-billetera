import { useEffect, useRef, useState } from 'react'
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { Link } from 'react-router-dom'
import type { Dashboard as DashboardData } from '../api/dashboard'
import { obtenerDashboard } from '../api/dashboard'
import Layout from '../componentes/Layout'
import { IconoAlerta, IconoCalendario, IconoChevronAbajo } from '../componentes/iconos'

const MESES_ES = [
  'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
  'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre',
]
const COLORES = ['#16a34a', '#2563eb', '#f59e0b', '#dc2626', '#7c3aed', '#db2777', '#0d9488', '#6b7280']

function formatearMonto(monto: number) {
  const formato = new Intl.NumberFormat('es-AR', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(monto)
  return `$${formato}`
}

function claveMes(anio: number, mes: number) {
  return `${anio}-${String(mes).padStart(2, '0')}`
}

function capitalizar(texto: string) {
  return texto.charAt(0).toUpperCase() + texto.slice(1)
}

function abreviarMes(mes: number) {
  return MESES_ES[mes - 1].slice(0, 3)
}

function mesAnteriorCliente(anio: number, mes: number): [number, number] {
  return mes === 1 ? [anio - 1, 12] : [anio, mes - 1]
}

// Opciones del selector: una ventana fija de meses terminada en el mes real de hoy (capturado una
// sola vez al cargar). No se recalcula a partir de los datos mostrados, para que elegir un mes
// viejo no haga "desaparecer" los meses más recientes de la lista (quedaban inalcanzables).
function opcionesMes(referencia: { anio: number; mes: number }, cantidad: number) {
  const opciones: { anio: number; mes: number }[] = []
  let anio = referencia.anio
  let mes = referencia.mes
  for (let i = 0; i < cantidad; i++) {
    opciones.push({ anio, mes })
    ;[anio, mes] = mesAnteriorCliente(anio, mes)
  }
  return opciones.reverse()
}

export default function Dashboard() {
  const [mesParam, setMesParam] = useState<string | null>(null)
  const [datos, setDatos] = useState<DashboardData | null>(null)
  const [mesReferencia, setMesReferencia] = useState<{ anio: number; mes: number } | null>(null)

  useEffect(() => {
    obtenerDashboard(mesParam ?? undefined)
      .then((resultado) => {
        setDatos(resultado)
        if (mesParam === null) {
          setMesParam(claveMes(resultado.anio, resultado.mes))
          setMesReferencia({ anio: resultado.anio, mes: resultado.mes })
        }
      })
      .catch(() => {})
  }, [mesParam])

  if (!datos) {
    return <Layout>{null}</Layout>
  }

  // El backend serializa Decimal como string en el JSON (p. ej. "55500.00"); Recharts necesita
  // numeros reales para calcular ángulos/escalas, si no recibe `NaN` y no dibuja nada.
  const datosEvolucion = datos.evolucion.map((punto) => ({
    nombre: abreviarMes(punto.mes),
    Ingresos: Number(punto.ingresos),
    Gastos: Number(punto.egresos),
  }))

  const datosProyeccion = [
    ...datos.evolucion.map((punto) => ({
      nombre: abreviarMes(punto.mes),
      real: Number(punto.egresos),
    })),
    ...(datos.proyeccion.datos_suficientes && datos.proyeccion.mes !== null && datos.proyeccion.monto !== null
      ? [{ nombre: abreviarMes(datos.proyeccion.mes), proyectado: Number(datos.proyeccion.monto) }]
      : []),
  ]

  const datosDistribucion = datos.distribucion_categorias.map((categoria) => ({
    ...categoria,
    monto: Number(categoria.monto),
  }))

  const mesesAnomalos = new Set(datos.anomalias.meses.map((m) => claveMes(m.anio, m.mes)))
  const datosAnomalias = datos.evolucion.map((punto) => ({
    nombre: abreviarMes(punto.mes),
    monto: Number(punto.egresos),
    esAnomalo: mesesAnomalos.has(claveMes(punto.anio, punto.mes)),
  }))

  return (
    <Layout>
      <header className="top">
        <div className="t">
          <div>
            <h1>Panel de finanzas</h1>
            <p>Resumen del mes seleccionado</p>
          </div>
        </div>
        <SelectorMes
          valor={mesParam ?? ''}
          opciones={(mesReferencia ? opcionesMes(mesReferencia, 12) : []).map(({ anio, mes }) => ({
            clave: claveMes(anio, mes),
            etiqueta: `${MESES_ES[mes - 1]} ${anio}`,
          }))}
          onCambiar={setMesParam}
        />
      </header>
      <div className="content">
        <div className="grid-3">
          <div className="card">
            <h2>Ingresos del mes</h2>
            <p className="num pos" style={{ fontSize: 28, fontWeight: 700, marginTop: 6 }}>
              {formatearMonto(datos.ingresos.monto)}
            </p>
            <p className="dim" style={{ fontSize: 12, marginTop: 4 }}>
              {datos.ingresos.variacion_texto}
            </p>
          </div>
          <div className="card">
            <h2>Gastos del mes</h2>
            <p className="num neg" style={{ fontSize: 28, fontWeight: 700, marginTop: 6 }}>
              {formatearMonto(datos.egresos.monto)}
            </p>
            <p className="dim" style={{ fontSize: 12, marginTop: 4 }}>
              {datos.egresos.variacion_texto}
            </p>
          </div>
          <div className="card">
            <h2>Saldo</h2>
            <p className="num" style={{ fontSize: 28, fontWeight: 700, marginTop: 6 }}>
              {formatearMonto(datos.saldo)}
            </p>
            <p className="dim" style={{ fontSize: 12, marginTop: 4 }}>
              Lo que te queda después de tus gastos
            </p>
          </div>
        </div>

        {datos.alertas.length > 0 && (
          <div className="card" style={{ background: 'var(--amber-soft)', borderColor: 'var(--amber-line)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, color: 'var(--amber)' }}>
              <IconoAlerta />
              <h2 style={{ color: '#92400e' }}>
                {datos.alertas.length} {datos.alertas.length === 1 ? 'categoría' : 'categorías'} por encima
                de lo habitual
              </h2>
            </div>
            <ul>
              {datos.alertas.map((alerta) => (
                <li
                  key={alerta.categoria_id}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 14,
                    padding: '12px 0',
                    borderTop: '1px solid var(--amber-line)',
                  }}
                >
                  <span className="pill warn">
                    <IconoAlerta />+{alerta.porcentaje}%
                  </span>
                  <p style={{ flex: 1 }}>
                    {alerta.categoria}: llevás {formatearMonto(alerta.monto_actual)} este mes. Tu promedio
                    de los últimos 3 meses es {formatearMonto(alerta.promedio)}.
                  </p>
                  <Link className="btn sm" to="/historial">
                    Ver movimientos
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        )}

        {!datos.hay_movimientos ? (
          <p className="dim">
            Todavía no cargaste movimientos este mes. Contale un gasto a Qash en el chat para empezar.
          </p>
        ) : (
          <>
            <div className="grid-2">
              <div className="card">
                <h2>Flujo mensual</h2>
                <p className="sub">Ingresos y gastos de los últimos 6 meses</p>
                <LineChart width={480} height={260} data={datosEvolucion}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#eef0f3" />
                  <XAxis dataKey="nombre" stroke="#9ca3af" fontSize={11} />
                  <YAxis stroke="#9ca3af" fontSize={11} />
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="Ingresos" stroke="#16a34a" strokeWidth={2.5} />
                  <Line type="monotone" dataKey="Gastos" stroke="#dc2626" strokeWidth={2.5} />
                </LineChart>
              </div>

              <div className="card">
                <h2>Gastos por categoría</h2>
                <p className="sub">Distribución del mes</p>
                <div style={{ display: 'flex', gap: 24, alignItems: 'center' }}>
                  <div style={{ position: 'relative', width: 180, height: 180, flex: 'none' }}>
                    <PieChart width={180} height={180}>
                      <Pie
                        data={datosDistribucion}
                        dataKey="monto"
                        nameKey="categoria"
                        innerRadius={55}
                        outerRadius={85}
                      >
                        {datos.distribucion_categorias.map((_, indice) => (
                          <Cell key={indice} fill={COLORES[indice % COLORES.length]} />
                        ))}
                      </Pie>
                      <Tooltip />
                    </PieChart>
                    <div
                      style={{
                        position: 'absolute',
                        inset: 0,
                        display: 'flex',
                        flexDirection: 'column',
                        alignItems: 'center',
                        justifyContent: 'center',
                        pointerEvents: 'none',
                      }}
                    >
                      <span className="dim" style={{ fontSize: 11 }}>
                        Total
                      </span>
                      <span style={{ fontSize: 15, fontWeight: 700 }}>
                        {formatearMonto(datos.egresos.monto).replace(/,00$/, '')}
                      </span>
                    </div>
                  </div>
                  <ul style={{ flex: 1, fontSize: 13 }}>
                    {datos.distribucion_categorias.map((categoria, indice) => (
                      <li
                        key={categoria.categoria_id}
                        style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '3px 0' }}
                      >
                        <i
                          style={{
                            width: 10,
                            height: 10,
                            borderRadius: 3,
                            background: COLORES[indice % COLORES.length],
                            flex: 'none',
                            display: 'inline-block',
                          }}
                        />
                        <span style={{ flex: 1 }}>{categoria.categoria}</span>
                        <span className="num dim">{formatearMonto(categoria.monto)}</span>
                        <span className="num" style={{ width: 40, textAlign: 'right', fontWeight: 600 }}>
                          {categoria.porcentaje}%
                        </span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>

            <div className="grid-2">
              <div className="card">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <div>
                    <h2>Proyección de gasto</h2>
                    <p className="sub">Estimada con tus últimos 6 meses</p>
                  </div>
                  {datos.proyeccion.datos_suficientes && datos.proyeccion.monto !== null && (
                    <div style={{ textAlign: 'right' }}>
                      {datos.proyeccion.mes !== null && (
                        <p className="dim" style={{ fontSize: 12 }}>
                          {capitalizar(MESES_ES[datos.proyeccion.mes - 1])} {datos.proyeccion.anio}
                        </p>
                      )}
                      <p className="num" style={{ fontSize: 20, fontWeight: 700, color: '#b45309' }}>
                        {formatearMonto(datos.proyeccion.monto)}
                      </p>
                    </div>
                  )}
                </div>
                {datos.proyeccion.datos_suficientes && datos.proyeccion.monto !== null ? (
                  <BarChart width={480} height={220} data={datosProyeccion} barSize={28} barCategoryGap="30%">
                    <CartesianGrid strokeDasharray="3 3" stroke="#eef0f3" />
                    <XAxis dataKey="nombre" stroke="#9ca3af" fontSize={11} />
                    <YAxis stroke="#9ca3af" fontSize={11} />
                    <Tooltip cursor={false} />
                    <Legend />
                    <Bar dataKey="real" name="Gasto real" fill="#f87171" radius={[4, 4, 0, 0]} />
                    <Bar
                      dataKey="proyectado"
                      name="Proyección"
                      fill="#fffbeb"
                      stroke="#d97706"
                      strokeWidth={1.8}
                      strokeDasharray="5 4"
                      radius={[4, 4, 0, 0]}
                    />
                  </BarChart>
                ) : (
                  <p className="dim">Todavía no hay suficiente historial para proyectar el gasto del próximo mes.</p>
                )}
              </div>

              <div className="card">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <div>
                    <h2>Meses con gasto anómalo</h2>
                    <p className="sub">Meses que se apartan de tu comportamiento habitual</p>
                  </div>
                  {datos.anomalias.datos_suficientes && (
                    <span className="pill bad">
                      <IconoAlerta />
                      {datos.anomalias.meses.length} {datos.anomalias.meses.length === 1 ? 'mes' : 'meses'}
                    </span>
                  )}
                </div>
                {datos.anomalias.datos_suficientes ? (
                  <>
                    <BarChart width={480} height={220} data={datosAnomalias}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#eef0f3" />
                      <XAxis dataKey="nombre" stroke="#9ca3af" fontSize={11} />
                      <YAxis stroke="#9ca3af" fontSize={11} />
                      <Tooltip cursor={false} />
                      <Bar dataKey="monto" radius={[4, 4, 0, 0]}>
                        {datosAnomalias.map((punto, indice) => (
                          <Cell key={indice} fill={punto.esAnomalo ? '#dc2626' : '#cbd5e1'} />
                        ))}
                      </Bar>
                    </BarChart>
                    <div style={{ display: 'flex', justifyContent: 'center', flexWrap: 'wrap', gap: 6 }}>
                      {datos.anomalias.meses.map((mesAnomalo) => (
                        <span key={claveMes(mesAnomalo.anio, mesAnomalo.mes)} className="pill bad">
                          {capitalizar(MESES_ES[mesAnomalo.mes - 1])} {mesAnomalo.anio} ·{' '}
                          {formatearMonto(mesAnomalo.monto)} · {Math.abs(mesAnomalo.porcentaje_sobre_promedio)}%{' '}
                          {mesAnomalo.porcentaje_sobre_promedio >= 0 ? 'más' : 'menos'} que el promedio de
                          los otros meses
                        </span>
                      ))}
                    </div>
                  </>
                ) : (
                  <p className="dim">Todavía no hay suficiente historial para detectar meses anómalos.</p>
                )}
              </div>
            </div>
          </>
        )}
      </div>
    </Layout>
  )
}

interface OpcionMes {
  clave: string
  etiqueta: string
}

function SelectorMes({
  valor,
  opciones,
  onCambiar,
}: {
  valor: string
  opciones: OpcionMes[]
  onCambiar: (clave: string) => void
}) {
  const [abierto, setAbierto] = useState(false)
  const contenedorRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    function alTocarFuera(evento: MouseEvent) {
      if (contenedorRef.current && !contenedorRef.current.contains(evento.target as Node)) {
        setAbierto(false)
      }
    }
    document.addEventListener('mousedown', alTocarFuera)
    return () => document.removeEventListener('mousedown', alTocarFuera)
  }, [])

  const etiquetaActual = opciones.find((opcion) => opcion.clave === valor)?.etiqueta ?? ''

  return (
    <div className="sel-personalizado" ref={contenedorRef}>
      <button
        type="button"
        className="sel"
        aria-label="Mes"
        aria-haspopup="listbox"
        aria-expanded={abierto}
        onClick={() => setAbierto((previo) => !previo)}
      >
        <IconoCalendario />
        <span>{etiquetaActual}</span>
        <IconoChevronAbajo />
      </button>
      {abierto && (
        <ul className="sel-lista" role="listbox">
          {opciones.map((opcion) => (
            <li key={opcion.clave}>
              <button
                type="button"
                role="option"
                aria-selected={opcion.clave === valor}
                className={opcion.clave === valor ? 'on' : ''}
                onClick={() => {
                  onCambiar(opcion.clave)
                  setAbierto(false)
                }}
              >
                {opcion.etiqueta}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
