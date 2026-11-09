import { useEffect, useState } from 'react'
import type { Catalogos } from '../api/catalogos'
import { obtenerCatalogos } from '../api/catalogos'
import type { Borrador } from '../api/chat'
import { guardarMovimientos, validarMovimiento } from '../api/movimientos'
import { IconoAlerta, IconoCheck, IconoEditar } from './iconos'

export interface TarjetaMovimientoProps {
  borrador: Borrador
  conversacionId?: number | null
  mensajeId?: number | null
  yaGuardado?: boolean
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
    <div className="fl">
      <label htmlFor={id}>{etiqueta}</label>
      <select
        className="sel bad"
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
      <p className="help-bad">{mensajeError}</p>
    </div>
  )
}

export default function TarjetaMovimiento({
  borrador,
  conversacionId,
  mensajeId,
  yaGuardado,
  onGuardado,
  onDescartado,
}: TarjetaMovimientoProps) {
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
  const [guardado, setGuardado] = useState(!!yaGuardado)
  const [guardando, setGuardando] = useState(false)

  useEffect(() => {
    obtenerCatalogos()
      .then(setCatalogos)
      .catch(() => {})
  }, [])

  useEffect(() => {
    if (guardado) return
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
  }, [guardado, monto, fecha, tipo, descripcion, categoriaId, medioPagoId])

  async function manejarGuardar() {
    setGuardando(true)
    try {
      await guardarMovimientos([
        {
          monto,
          fecha,
          tipo,
          descripcion,
          categoria_id: categoriaId,
          medio_pago_id: medioPagoId,
          conversacion_id: conversacionId,
          mensaje_id: mensajeId,
        },
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
      <div className="mv">
        <div className="hd">
          <b>Movimiento registrado</b>
          <span className="pill ok">
            <IconoCheck />
            Guardado
          </span>
        </div>
        <div className="grid">
          <div className="fl">
            <label>Monto</label>
            <div className="v big num">{formatearMonto(monto)}</div>
          </div>
          <div className="fl">
            <label>Tipo</label>
            <div className="v">{ETIQUETA_TIPO[tipo] ?? tipo}</div>
          </div>
          <div className="fl">
            <label>Fecha</label>
            <div className="v">{fecha}</div>
          </div>
          <div className="fl">
            <label>Medio de pago</label>
            <div className="v">{nombreMedioPago}</div>
          </div>
          <div className="fl">
            <label>Categoría</label>
            <div className="v">{nombreCategoria}</div>
          </div>
          <div className="fl">
            <label>Descripción</label>
            <div className="v">{descripcion}</div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="mv">
      <div className="hd">
        <b>Revisá el movimiento antes de guardarlo</b>
        {errores.length > 0 && (
          <span className="pill warn">
            <IconoAlerta />
            {errores.length} datos para completar
          </span>
        )}
      </div>

      <div className="grid">
        {editando ? (
          <>
            <div className="fl">
              <label htmlFor="monto">Monto</label>
              <input
                className="inp"
                id="monto"
                type="number"
                value={monto}
                onChange={(evento) => setMonto(Number(evento.target.value))}
              />
            </div>
            <div className="fl">
              <label htmlFor="fecha">Fecha</label>
              <input
                className="inp"
                id="fecha"
                type="date"
                value={fecha}
                onChange={(evento) => setFecha(evento.target.value)}
              />
            </div>
            <div className="fl">
              <label htmlFor="descripcion">Descripción</label>
              <input
                className="inp"
                id="descripcion"
                value={descripcion}
                onChange={(evento) => setDescripcion(evento.target.value)}
              />
            </div>
          </>
        ) : (
          <>
            <div className="fl">
              <label>Monto</label>
              <div className="v big num">{formatearMonto(monto)}</div>
            </div>
            <div className="fl">
              <label>Tipo</label>
              <div className="v">{ETIQUETA_TIPO[tipo] ?? tipo}</div>
            </div>
            <div className="fl">
              <label>Fecha</label>
              <div className="v">{fecha}</div>
            </div>
            <div className="fl">
              <label>Descripción</label>
              <div className="v">{descripcion}</div>
            </div>
          </>
        )}
        {errores.includes('MONTO_INVALIDO') && <p className="help-bad">El monto no es válido.</p>}
        {errores.includes('FECHA_FUTURA') && <p className="help-bad">La fecha no puede ser posterior a hoy.</p>}

        {categoriaId != null && !errores.includes('CATEGORIA_INVALIDA') ? (
          <div className="fl">
            <label>Categoría</label>
            <div className="v">{nombreCategoria}</div>
          </div>
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
          <div className="fl">
            <label>Medio de pago</label>
            <div className="v">{nombreMedioPago}</div>
          </div>
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
      </div>

      {advertencias.includes('POSIBLE_DUPLICADO') && (
        <p className="help-bad" style={{ padding: '0 18px' }}>
          Aviso: posible duplicado. Revisá antes de guardar.
        </p>
      )}

      <div className="ft">
        <button
          className="btn primary"
          type="button"
          onClick={manejarGuardar}
          disabled={errores.length > 0 || guardando}
        >
          <IconoCheck />
          Guardar movimiento
        </button>
        <button className="btn" type="button" onClick={() => setEditando(true)}>
          <IconoEditar />
          Editar
        </button>
        <button className="btn ghost" type="button" onClick={() => onDescartado?.()}>
          Descartar
        </button>
        {errores.length > 0 && <span className="note">Completá los datos marcados para guardar</span>}
      </div>
    </div>
  )
}
