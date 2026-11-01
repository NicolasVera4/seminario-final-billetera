import { useEffect, useState } from 'react'
import {
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

export default function Dashboard() {
  const [mesParam, setMesParam] = useState<string | null>(null)
  const [datos, setDatos] = useState<DashboardData | null>(null)

  useEffect(() => {
    obtenerDashboard(mesParam ?? undefined)
      .then((resultado) => {
        setDatos(resultado)
        if (mesParam === null) {
          setMesParam(claveMes(resultado.anio, resultado.mes))
        }
      })
      .catch(() => {})
  }, [mesParam])

  if (!datos) {
    return null
  }

  const datosEvolucion = datos.evolucion.map((punto) => ({
    nombre: MESES_ES[punto.mes - 1].slice(0, 3),
    Ingresos: punto.ingresos,
    Gastos: punto.egresos,
  }))

  return (
    <div>
      <h1>Panel de finanzas</h1>
      <p>Resumen del mes seleccionado</p>

      <label htmlFor="selector-mes">Mes</label>
      <select
        id="selector-mes"
        value={mesParam ?? ''}
        onChange={(evento) => setMesParam(evento.target.value)}
      >
        {datos.evolucion.map((punto) => {
          const clave = claveMes(punto.anio, punto.mes)
          return (
            <option key={clave} value={clave}>
              {MESES_ES[punto.mes - 1]} {punto.anio}
            </option>
          )
        })}
      </select>

      <section>
        <article>
          <h2>Ingresos del mes</h2>
          <p>{formatearMonto(datos.ingresos.monto)}</p>
          <p>{datos.ingresos.variacion_texto}</p>
        </article>
        <article>
          <h2>Gastos del mes</h2>
          <p>{formatearMonto(datos.egresos.monto)}</p>
          <p>{datos.egresos.variacion_texto}</p>
        </article>
        <article>
          <h2>Saldo</h2>
          <p>{formatearMonto(datos.saldo)}</p>
          <p>Lo que te queda después de tus gastos</p>
        </article>
      </section>

      {datos.alertas.length > 0 && (
        <section>
          <h2>
            {datos.alertas.length} {datos.alertas.length === 1 ? 'categoría' : 'categorías'} por encima de
            lo habitual
          </h2>
          <ul>
            {datos.alertas.map((alerta) => (
              <li key={alerta.categoria_id}>
                <span>+{alerta.porcentaje}%</span>
                <p>
                  {alerta.categoria}: llevás {formatearMonto(alerta.monto_actual)} este mes. Tu promedio de
                  los últimos 3 meses es {formatearMonto(alerta.promedio)}.
                </p>
                <Link to="/historial">Ver movimientos</Link>
              </li>
            ))}
          </ul>
        </section>
      )}

      {!datos.hay_movimientos ? (
        <p>Todavía no cargaste movimientos este mes. Contale un gasto a Qash en el chat para empezar.</p>
      ) : (
        <>
          <section>
            <h2>Flujo mensual</h2>
            <LineChart width={500} height={300} data={datosEvolucion}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="nombre" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="Ingresos" stroke="#16a34a" />
              <Line type="monotone" dataKey="Gastos" stroke="#dc2626" />
            </LineChart>
          </section>

          <section>
            <h2>Gastos por categoría</h2>
            <PieChart width={300} height={300}>
              <Pie
                data={datos.distribucion_categorias}
                dataKey="monto"
                nameKey="categoria"
                innerRadius={60}
                outerRadius={100}
              >
                {datos.distribucion_categorias.map((_, indice) => (
                  <Cell key={indice} fill={COLORES[indice % COLORES.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
            <ul>
              {datos.distribucion_categorias.map((categoria) => (
                <li key={categoria.categoria_id}>
                  <span>{categoria.categoria}</span>
                  <span>{formatearMonto(categoria.monto)}</span>
                  <span>{categoria.porcentaje}%</span>
                </li>
              ))}
            </ul>
          </section>
        </>
      )}
    </div>
  )
}
