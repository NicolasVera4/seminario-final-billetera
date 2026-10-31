import { useEffect, useState } from 'react'
import type { Catalogos } from '../api/catalogos'
import { obtenerCatalogos } from '../api/catalogos'
import type { Borrador } from '../api/chat'
import { guardarMovimientos, validarMovimiento } from '../api/movimientos'

export interface TarjetaMovimientoProps {
  borrador: Borrador
  onGuardado?: () => void
  onDescartado?: () => void
}

const ETIQUETA_TIPO: Record<string, string> = { EGRESO: 'Egreso', INGRESO: 'Ingreso' }

function formatearMonto(monto: number) {
  return `$${monto}`
}

function mensajeCategoria(categoriaSugerida: string | null) {
  return categoriaSugerida
    ? `"${categoriaSugerida}" no está en el catálogo. Elegí una.`
    : 'El mensaje no indica la categoría. Elegí una.'
}

interface SelectCatalogoProps {
  id: string
  etiqueta: string
  valor: number | null
  opciones: { id: number; nombre: string }[]
  placeholder: string
  mensajeError: string
  onCambiar: (valor: number | null) => void
}

function SelectCatalogo({ id, etiqueta, valor, opciones, placeholder, mensajeError, onCambiar }: SelectCatalogoProps) {
  return (
    <>
      <label htmlFor={id}>{etiqueta}</label>
      <select
        id={id}
        value={valor ?? ''}
        onChange={(evento) => onCambiar(evento.target.value ? Number(evento.target.value) : null)}
      >
        <option value="">{placeholder}</option>
        {opciones.map((opcion) => (
          <option key={opcion.id} value={opcion.id}>
            {opcion.nombre}
          </option>
        ))}
      </select>
      <p>{mensajeError}</p>
    </>
  )
}

export default function TarjetaMovimiento({ borrador, onGuardado, onDescartado }: TarjetaMovimientoProps) {
  const [catalogos, setCatalogos] = useState<Catalogos | null>(null)
  const [monto, setMonto] = useState(borrador.monto)
  const [fecha, setFecha] = useState(borrador.fecha)
  const [tipo, setTipo] = useState(borrador.tipo)
  const [descripcion, setDescripcion] = useState(borrador.descripcion)
  const [categoriaId, setCategoriaId] = useState(borrador.categoria_id)
  const [medioPagoId, setMedioPagoId] = useState(borrador.medio_pago_id)
  const [errores, setErrores] = useState<string[]>([])
  const [advertencias, setAdvertencias] = useState<string[]>([])
  const [editando, setEditando] = useState(false)
  const [guardado, setGuardado] = useState(false)
  const [guardando, setGuardando] = useState(false)

  useEffect(() => {
    obtenerCatalogos()
      .then(setCatalogos)
      .catch(() => {})
  }, [])

  useEffect(() => {
    validarMovimiento({
      monto,
      fecha,
      tipo,
      descripcion,
      categoria_id: categoriaId,
      medio_pago_id: medioPagoId,
    })
      .then((resultado) => {
        setErrores(resultado.errores)
        setAdvertencias(resultado.advertencias)
      })
      .catch(() => {})
  }, [monto, fecha, tipo, descripcion, categoriaId, medioPagoId])

  async function manejarGuardar() {
    setGuardando(true)
    try {
      await guardarMovimientos([
        { monto, fecha, tipo, descripcion, categoria_id: categoriaId, medio_pago_id: medioPagoId },
      ])
      setGuardado(true)
      onGuardado?.()
    } finally {
      setGuardando(false)
    }
  }

  const nombreCategoria = catalogos?.categorias.find((c) => c.id === categoriaId)?.nombre ?? ''
  const nombreMedioPago = catalogos?.medios_pago.find((m) => m.id === medioPagoId)?.nombre ?? ''

  if (guardado) {
    return (
      <div>
        <p>Movimiento registrado</p>
        <p>Guardado</p>
        <dl>
          <dt>Monto</dt>
          <dd>{formatearMonto(monto)}</dd>
          <dt>Fecha</dt>
          <dd>{fecha}</dd>
          <dt>Tipo</dt>
          <dd>{ETIQUETA_TIPO[tipo] ?? tipo}</dd>
          <dt>Categoría</dt>
          <dd>{nombreCategoria}</dd>
          <dt>Medio de pago</dt>
          <dd>{nombreMedioPago}</dd>
          <dt>Descripción</dt>
          <dd>{descripcion}</dd>
        </dl>
      </div>
    )
  }

  return (
    <div>
      <p>Revisá el movimiento antes de guardarlo</p>
      {errores.length > 0 && <p>{errores.length} datos para completar</p>}

      {editando ? (
        <>
          <label htmlFor="monto">Monto</label>
          <input
            id="monto"
            type="number"
            value={monto}
            onChange={(evento) => setMonto(Number(evento.target.value))}
          />
          <label htmlFor="fecha">Fecha</label>
          <input id="fecha" type="date" value={fecha} onChange={(evento) => setFecha(evento.target.value)} />
          <label htmlFor="descripcion">Descripción</label>
          <input
            id="descripcion"
            value={descripcion}
            onChange={(evento) => setDescripcion(evento.target.value)}
          />
        </>
      ) : (
        <dl>
          <dt>Monto</dt>
          <dd>{formatearMonto(monto)}</dd>
          <dt>Fecha</dt>
          <dd>{fecha}</dd>
          <dt>Tipo</dt>
          <dd>{ETIQUETA_TIPO[tipo] ?? tipo}</dd>
          <dt>Descripción</dt>
          <dd>{descripcion}</dd>
        </dl>
      )}
      {errores.includes('MONTO_INVALIDO') && <p>El monto no es válido.</p>}
      {errores.includes('FECHA_FUTURA') && <p>La fecha no puede ser posterior a hoy.</p>}

      {categoriaId != null && !errores.includes('CATEGORIA_INVALIDA') ? (
        <p>Categoría: {nombreCategoria}</p>
      ) : (
        <SelectCatalogo
          id="categoria"
          etiqueta="Categoría"
          valor={categoriaId}
          opciones={catalogos?.categorias ?? []}
          placeholder="Elegí una categoría"
          mensajeError={mensajeCategoria(borrador.categoria_sugerida)}
          onCambiar={setCategoriaId}
        />
      )}

      {medioPagoId != null && !errores.includes('MEDIO_PAGO_FALTANTE') ? (
        <p>Medio de pago: {nombreMedioPago}</p>
      ) : (
        <SelectCatalogo
          id="medio_pago"
          etiqueta="Medio de pago"
          valor={medioPagoId}
          opciones={catalogos?.medios_pago ?? []}
          placeholder="Elegí un medio de pago"
          mensajeError="El mensaje no indica cómo pagaste."
          onCambiar={setMedioPagoId}
        />
      )}

      {advertencias.includes('POSIBLE_DUPLICADO') && <p>Aviso: posible duplicado. Revisá antes de guardar.</p>}

      <button type="button" onClick={manejarGuardar} disabled={errores.length > 0 || guardando}>
        Guardar movimiento
      </button>
      <button type="button" onClick={() => setEditando(true)}>
        Editar
      </button>
      <button type="button" onClick={() => onDescartado?.()}>
        Descartar
      </button>
    </div>
  )
}
