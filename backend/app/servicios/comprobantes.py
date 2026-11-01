import io
import uuid
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import pdfplumber
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.esquemas.archivos import ComprobanteRespuesta, ExtractoRespuesta, ItemResumenSalida, ResumenRespuesta
from app.esquemas.movimientos import BorradorMovimientoSalida, Catalogo
from app.modelos.enums import TipoComprobante, TipoMovimiento
from app.modelos.movimiento import Movimiento
from app.modelos.usuario import Usuario
from app.proveedores.llm import ErrorInterpretacion, ProveedorLLM
from app.servicios.errores import ErrorServicio
from app.servicios.ingesta.ocr import extraer_texto_imagen
from app.servicios.ingesta.pdf import extraer_texto_pdf
from app.servicios.ingesta.planilla import (
    detectar_columnas_por_sinonimos,
    leer_filas,
    parsear_fecha,
    parsear_monto,
)
from app.servicios.interpretacion import obtener_catalogo, resolver_categoria, resolver_medio_pago
from app.servicios.reloj import Reloj
from app.servicios.validacion import es_posible_duplicado_lote, validar_campos

FORMATOS_ADMITIDOS = {
    "image/jpeg": TipoComprobante.TICKET,
    "image/png": TipoComprobante.TICKET,
    "image/webp": TipoComprobante.TICKET,
    "application/pdf": TipoComprobante.FACTURA,
}
FORMATOS_ADMITIDOS_RESUMEN = {"application/pdf": TipoComprobante.RESUMEN_TARJETA}
FORMATOS_ADMITIDOS_EXTRACTO = {
    "text/csv": TipoComprobante.EXTRACTO,
    "application/vnd.ms-excel": TipoComprobante.EXTRACTO,
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": TipoComprobante.EXTRACTO,
}
TAMANO_MAXIMO_BYTES = 10 * 1024 * 1024

MENSAJE_FORMATOS = "Formato no admitido. Subí una imagen (jpg, png, webp) o un PDF."
MENSAJE_FORMATOS_RESUMEN = "Formato no admitido. Subí el PDF del resumen de tu tarjeta."
MENSAJE_FORMATOS_EXTRACTO = "Formato no admitido. Subí un CSV o Excel (.csv, .xlsx)."
MENSAJE_TAMANO = "El archivo supera el tamaño máximo de 10 MB."
MENSAJE_SIN_MONTO = "No pudimos leer un monto en el archivo. Probá cargarlo por texto."
MENSAJE_NO_INTERPRETABLE = "No pudimos leer el comprobante. Probá cargarlo por texto."
MENSAJE_COLUMNAS_NO_DETECTADAS = "No pudimos identificar las columnas de fecha y monto del archivo."
MENSAJE_MOVIMIENTO_INTERPRETADO = "Encontré este movimiento, revisalo y confirmalo."


class ErrorComprobante(ErrorServicio):
    pass


@dataclass
class ContextoLote:
    """Catalogo y datos del usuario que necesita validar/deduplicar un lote (resumen o extracto)."""

    categorias: list
    medios_pago: list
    catalogo: Catalogo
    categorias_validas: set[int]
    medios_pago_validos: set[int]
    hoy: date
    existentes: list[tuple]


def _contexto_lote(sesion: Session, usuario: Usuario, reloj: Reloj) -> ContextoLote:
    categorias, medios_pago, catalogo = obtener_catalogo(sesion)
    return ContextoLote(
        categorias=categorias,
        medios_pago=medios_pago,
        catalogo=catalogo,
        categorias_validas={c.id for c in categorias},
        medios_pago_validos={m.id for m in medios_pago},
        hoy=reloj.ahora().date(),
        existentes=_montos_existentes(sesion, usuario.id),
    )


def _validar_formato_y_tamano(
    content_type: str, contenido: bytes, formatos_admitidos: dict[str, TipoComprobante], mensaje_formato: str
) -> TipoComprobante:
    if content_type not in formatos_admitidos:
        raise ErrorComprobante(415, mensaje_formato)
    if len(contenido) > TAMANO_MAXIMO_BYTES:
        raise ErrorComprobante(413, MENSAJE_TAMANO)
    return formatos_admitidos[content_type]


def procesar_comprobante(
    sesion: Session,
    usuario: Usuario,
    proveedor_llm: ProveedorLLM,
    reloj: Reloj,
    contenido: bytes,
    content_type: str,
    nombre_archivo: str,
) -> ComprobanteRespuesta:
    tipo_comprobante = _validar_formato_y_tamano(content_type, contenido, FORMATOS_ADMITIDOS, MENSAJE_FORMATOS)
    if content_type == "application/pdf":
        texto = extraer_texto_pdf(contenido)
    else:
        texto = extraer_texto_imagen(contenido)

    categorias, medios_pago, catalogo = obtener_catalogo(sesion)

    try:
        movimientos = proveedor_llm.extraer_movimientos(texto, tipo_comprobante, catalogo)
    except ErrorInterpretacion:
        raise ErrorComprobante(422, MENSAJE_NO_INTERPRETABLE)

    if not movimientos or movimientos[0].monto is None:
        raise ErrorComprobante(422, MENSAJE_SIN_MONTO)

    movimiento = movimientos[0]
    categoria_id, categoria_sugerida = resolver_categoria(categorias, movimiento.categoria)
    medio_pago_id = resolver_medio_pago(medios_pago, movimiento.medio_pago)

    archivo_ref = _guardar_archivo(usuario.id, nombre_archivo, contenido)

    borrador = BorradorMovimientoSalida(
        monto=movimiento.monto,
        fecha=movimiento.fecha or reloj.ahora().date(),
        tipo=movimiento.tipo or "EGRESO",
        descripcion=movimiento.descripcion or nombre_archivo,
        categoria_id=categoria_id,
        categoria_sugerida=categoria_sugerida,
        medio_pago_id=medio_pago_id,
    )

    return ComprobanteRespuesta(
        borrador=borrador,
        archivo_ref=archivo_ref,
        comprobante_tipo=tipo_comprobante,
        mensaje=MENSAJE_MOVIMIENTO_INTERPRETADO,
    )


def procesar_resumen(
    sesion: Session,
    usuario: Usuario,
    proveedor_llm: ProveedorLLM,
    reloj: Reloj,
    contenido: bytes,
    content_type: str,
    nombre_archivo: str,
) -> ResumenRespuesta:
    tipo_comprobante = _validar_formato_y_tamano(
        content_type, contenido, FORMATOS_ADMITIDOS_RESUMEN, MENSAJE_FORMATOS_RESUMEN
    )
    texto = extraer_texto_pdf(contenido)
    with pdfplumber.open(io.BytesIO(contenido)) as pdf:
        paginas_leidas = len(pdf.pages)

    contexto = _contexto_lote(sesion, usuario, reloj)

    try:
        movimientos = proveedor_llm.extraer_movimientos(texto, tipo_comprobante, contexto.catalogo)
    except ErrorInterpretacion:
        raise ErrorComprobante(422, MENSAJE_NO_INTERPRETABLE)

    medio_pago_credito_id = resolver_medio_pago(contexto.medios_pago, "Crédito")

    items = []
    for movimiento in movimientos:
        categoria_id, categoria_sugerida = resolver_categoria(contexto.categorias, movimiento.categoria)
        fecha = movimiento.fecha or contexto.hoy
        errores = validar_campos(
            movimiento.monto,
            fecha,
            categoria_id,
            medio_pago_credito_id,
            contexto.hoy,
            contexto.categorias_validas,
            contexto.medios_pago_validos,
        )
        posible_duplicado = (
            movimiento.monto is not None
            and es_posible_duplicado_lote(fecha, movimiento.monto, contexto.existentes)
        )
        items.append(
            ItemResumenSalida(
                monto=movimiento.monto if movimiento.monto is not None else 0,
                fecha=fecha,
                tipo=movimiento.tipo or TipoMovimiento.EGRESO,
                descripcion=movimiento.descripcion or "Consumo",
                categoria_id=categoria_id,
                categoria_sugerida=categoria_sugerida,
                medio_pago_id=medio_pago_credito_id,
                cuota_numero=movimiento.cuota_numero,
                cuota_total=movimiento.cuota_total,
                errores=errores,
                posible_duplicado=posible_duplicado,
            )
        )

    archivo_ref = _guardar_archivo(usuario.id, nombre_archivo, contenido)

    return ResumenRespuesta(
        items=items,
        archivo_ref=archivo_ref,
        comprobante_tipo=tipo_comprobante,
        paginas_leidas=paginas_leidas,
    )


def procesar_extracto(
    sesion: Session,
    usuario: Usuario,
    proveedor_llm: ProveedorLLM,
    reloj: Reloj,
    contenido: bytes,
    content_type: str,
    nombre_archivo: str,
) -> ExtractoRespuesta:
    _validar_formato_y_tamano(content_type, contenido, FORMATOS_ADMITIDOS_EXTRACTO, MENSAJE_FORMATOS_EXTRACTO)

    try:
        filas = leer_filas(contenido, nombre_archivo)
    except Exception:
        raise ErrorComprobante(422, MENSAJE_NO_INTERPRETABLE)

    encabezados = list(filas.columns)
    columnas = detectar_columnas_por_sinonimos(encabezados)
    if columnas["fecha"] is None or columnas["monto"] is None:
        filas_muestra = filas.head(3).astype(str).values.tolist()
        try:
            detectadas = proveedor_llm.detectar_columnas(encabezados, filas_muestra)
        except ErrorInterpretacion:
            raise ErrorComprobante(422, MENSAJE_COLUMNAS_NO_DETECTADAS)
        columnas["fecha"] = columnas["fecha"] or detectadas.fecha
        columnas["monto"] = columnas["monto"] or detectadas.monto
        columnas["descripcion"] = columnas["descripcion"] or detectadas.descripcion

    if columnas["fecha"] is None or columnas["monto"] is None:
        raise ErrorComprobante(422, MENSAJE_COLUMNAS_NO_DETECTADAS)

    contexto = _contexto_lote(sesion, usuario, reloj)

    items = []
    filas_descartadas = 0
    for _, fila in filas.iterrows():
        fecha = parsear_fecha(fila[columnas["fecha"]])
        monto_con_signo = parsear_monto(str(fila[columnas["monto"]]))
        if fecha is None or monto_con_signo is None:
            filas_descartadas += 1
            continue

        tipo = TipoMovimiento.EGRESO if monto_con_signo < 0 else TipoMovimiento.INGRESO
        monto = abs(monto_con_signo)
        descripcion = (
            str(fila[columnas["descripcion"]]).strip() if columnas["descripcion"] else ""
        ) or "Movimiento importado"
        errores = validar_campos(
            monto, fecha, None, None, contexto.hoy, contexto.categorias_validas, contexto.medios_pago_validos
        )
        posible_duplicado = es_posible_duplicado_lote(fecha, monto, contexto.existentes)
        items.append(
            ItemResumenSalida(
                monto=monto,
                fecha=fecha,
                tipo=tipo,
                descripcion=descripcion,
                categoria_id=None,
                categoria_sugerida=None,
                medio_pago_id=None,
                cuota_numero=None,
                cuota_total=None,
                errores=errores,
                posible_duplicado=posible_duplicado,
            )
        )

    archivo_ref = _guardar_archivo(usuario.id, nombre_archivo, contenido)

    return ExtractoRespuesta(items=items, archivo_ref=archivo_ref, filas_descartadas=filas_descartadas)


def _montos_existentes(sesion: Session, usuario_id: int) -> list[tuple]:
    filas = sesion.execute(
        select(Movimiento.fecha, Movimiento.monto).where(Movimiento.usuario_id == usuario_id)
    ).all()
    return [(fecha, monto) for fecha, monto in filas]


def _guardar_archivo(usuario_id: int, nombre_original: str, contenido: bytes) -> str:
    directorio = Path(settings.archivos_dir) / str(usuario_id)
    directorio.mkdir(parents=True, exist_ok=True)
    nombre_archivo = f"{uuid.uuid4().hex}_{nombre_original}"
    (directorio / nombre_archivo).write_bytes(contenido)
    return f"{usuario_id}/{nombre_archivo}"
