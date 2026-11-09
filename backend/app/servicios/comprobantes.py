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
from app.esquemas.movimientos import BorradorMovimientoSalida, Catalogo, CategoriaMedioPagoFila
from app.modelos.enums import RolMensaje, TipoComprobante, TipoMovimiento
from app.modelos.movimiento import Movimiento
from app.modelos.usuario import Usuario
from app.proveedores.llm import MENSAJE_LIMITE_TASA, ErrorInterpretacion, ProveedorLLM
from app.servicios.conversaciones import guardar_mensaje, obtener_o_crear_conversacion
from app.servicios.errores import ErrorServicio
from app.servicios.ingesta.ocr import extraer_texto_imagen
from app.servicios.ingesta.pdf import contar_paginas_pdf, extraer_texto_pdf, extraer_texto_pdf_por_pagina
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
# Margen conservador bajo el limite de tokens por minuto de Groq (8000 TPM en el plan actual):
# ~4 caracteres por token en espanol, deja lugar para el resto del prompt (instrucciones, catalogo).
LIMITE_CARACTERES_BLOQUE = 6000

MENSAJE_FORMATOS = "Formato no admitido. Subí una imagen (jpg, png, webp) o un PDF."
MENSAJE_FORMATOS_ADJUNTO = (
    "Formato no admitido. Subí una imagen (jpg, png, webp), un PDF o un CSV/Excel."
)
MENSAJE_FORMATOS_RESUMEN = "Formato no admitido. Subí el PDF del resumen de tu tarjeta."
MENSAJE_FORMATOS_EXTRACTO = "Formato no admitido. Subí un CSV o Excel (.csv, .xlsx)."
MENSAJE_TAMANO = "El archivo supera el tamaño máximo de 10 MB."
MENSAJE_SIN_MONTO = "No pudimos leer un monto en el archivo. Probá cargarlo por texto."
MENSAJE_NO_INTERPRETABLE = "No pudimos leer el comprobante. Probá cargarlo por texto."
MENSAJE_COLUMNAS_NO_DETECTADAS = "No pudimos identificar las columnas de fecha y monto del archivo."
MENSAJE_MOVIMIENTO_INTERPRETADO = "Encontré este movimiento, revisalo y confirmalo."


def _mensaje_usuario_adjunto(content_type: str, nombre_archivo: str) -> str:
    """Mensaje que queda en el chat del lado del usuario al adjuntar un archivo. Nunca adivina
    qué tipo de documento es (un recibo de sueldo no es un "ticket") — solo dice que se cargó
    un archivo o una imagen, con su nombre."""
    tipo = "una imagen" if content_type.startswith("image/") else "un archivo"
    return f"Cargaste {tipo}: {nombre_archivo}."


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
    except ErrorInterpretacion as error:
        raise ErrorComprobante(422, MENSAJE_LIMITE_TASA if error.limite_tasa else MENSAJE_NO_INTERPRETABLE)

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


def dividir_en_bloques(paginas_texto: list[str], limite: int) -> list[str]:
    """Agrupa paginas consecutivas en bloques de hasta `limite` caracteres, sin partir ni
    duplicar texto, para no superar el limite de tokens por llamada al LLM."""
    bloques: list[str] = []
    actual = ""
    for texto_pagina in paginas_texto:
        if not texto_pagina.strip():
            continue
        if actual and len(actual) + 1 + len(texto_pagina) > limite:
            bloques.append(actual)
            actual = texto_pagina
        else:
            actual = f"{actual}\n{texto_pagina}" if actual else texto_pagina
    if actual:
        bloques.append(actual)
    return bloques


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
    paginas_texto = extraer_texto_pdf_por_pagina(contenido)
    paginas_leidas = len(paginas_texto)
    bloques = dividir_en_bloques(paginas_texto, LIMITE_CARACTERES_BLOQUE)

    contexto = _contexto_lote(sesion, usuario, reloj)

    try:
        movimientos = []
        for bloque in bloques:
            movimientos.extend(proveedor_llm.extraer_movimientos(bloque, tipo_comprobante, contexto.catalogo))
    except ErrorInterpretacion as error:
        raise ErrorComprobante(422, MENSAJE_LIMITE_TASA if error.limite_tasa else MENSAJE_NO_INTERPRETABLE)

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
        except ErrorInterpretacion as error:
            raise ErrorComprobante(
                422, MENSAJE_LIMITE_TASA if error.limite_tasa else MENSAJE_COLUMNAS_NO_DETECTADAS
            )
        columnas["fecha"] = columnas["fecha"] or detectadas.fecha
        columnas["monto"] = columnas["monto"] or detectadas.monto
        columnas["descripcion"] = columnas["descripcion"] or detectadas.descripcion

    if columnas["fecha"] is None or columnas["monto"] is None:
        raise ErrorComprobante(422, MENSAJE_COLUMNAS_NO_DETECTADAS)

    contexto = _contexto_lote(sesion, usuario, reloj)

    filas_validas = []
    filas_descartadas = 0
    for _, fila in filas.iterrows():
        fecha = parsear_fecha(fila[columnas["fecha"]])
        monto_con_signo = parsear_monto(str(fila[columnas["monto"]]))
        if fecha is None or monto_con_signo is None:
            filas_descartadas += 1
            continue

        descripcion = (
            str(fila[columnas["descripcion"]]).strip() if columnas["descripcion"] else ""
        ) or "Movimiento importado"
        filas_validas.append((fecha, monto_con_signo, descripcion))

    categorizaciones = _categorizar_filas_extracto(
        proveedor_llm, [descripcion for _, _, descripcion in filas_validas], contexto.catalogo
    )

    items = []
    for (fecha, monto_con_signo, descripcion), categorizacion in zip(filas_validas, categorizaciones):
        tipo = TipoMovimiento.EGRESO if monto_con_signo < 0 else TipoMovimiento.INGRESO
        monto = abs(monto_con_signo)
        categoria_id, categoria_sugerida = resolver_categoria(contexto.categorias, categorizacion.categoria)
        medio_pago_id = resolver_medio_pago(contexto.medios_pago, categorizacion.medio_pago)
        errores = validar_campos(
            monto,
            fecha,
            categoria_id,
            medio_pago_id,
            contexto.hoy,
            contexto.categorias_validas,
            contexto.medios_pago_validos,
        )
        posible_duplicado = es_posible_duplicado_lote(fecha, monto, contexto.existentes)
        items.append(
            ItemResumenSalida(
                monto=monto,
                fecha=fecha,
                tipo=tipo,
                descripcion=descripcion,
                categoria_id=categoria_id,
                categoria_sugerida=categoria_sugerida,
                medio_pago_id=medio_pago_id,
                cuota_numero=None,
                cuota_total=None,
                errores=errores,
                posible_duplicado=posible_duplicado,
            )
        )

    archivo_ref = _guardar_archivo(usuario.id, nombre_archivo, contenido)

    return ExtractoRespuesta(items=items, archivo_ref=archivo_ref, filas_descartadas=filas_descartadas)


def _categorizar_filas_extracto(
    proveedor_llm: ProveedorLLM, descripciones: list[str], catalogo: Catalogo
) -> list[CategoriaMedioPagoFila]:
    """Le pide al LLM una categoría y medio de pago por fila, igual que ya se hace para
    comprobantes y resúmenes de tarjeta. Es una ayuda, no un requisito: si falla (rate limit,
    lo que sea), se degrada a dejar todas las filas sin categorizar en vez de bloquear la
    importación completa — el usuario siempre puede completarlas a mano."""
    if not descripciones:
        return []
    try:
        return proveedor_llm.categorizar_filas(descripciones, catalogo)
    except ErrorInterpretacion:
        return [CategoriaMedioPagoFila() for _ in descripciones]


def procesar_adjunto(
    sesion: Session,
    usuario: Usuario,
    proveedor_llm: ProveedorLLM,
    reloj: Reloj,
    contenido: bytes,
    content_type: str,
    nombre_archivo: str,
    conversacion_id: int | None = None,
) -> tuple[str, ComprobanteRespuesta | ResumenRespuesta | ExtractoRespuesta, int, int]:
    """Un solo punto de entrada para el botón 'Adjuntar' del chat: decide qué procesador usar
    según el tipo de archivo. CSV/Excel y las imágenes no son ambiguos. Un PDF sí lo es (un
    ticket o factura puntual y un resumen de tarjeta son ambos PDF), así que se distingue por
    cantidad de páginas: un PDF de una sola página se trata como comprobante puntual; de varias,
    como resumen de tarjeta con varios movimientos.

    Además de procesar el archivo, registra lo que pasó como dos mensajes de chat (uno del
    usuario, amigable — nunca el nombre del archivo — y uno del asistente con el resultado), para
    que la acción quede en el historial de la conversación igual que un mensaje de texto."""
    if content_type in FORMATOS_ADMITIDOS_EXTRACTO:
        resultado_lote = procesar_extracto(
            sesion, usuario, proveedor_llm, reloj, contenido, content_type, nombre_archivo
        )
        modo, resultado, texto_asistente = _resultado_desde_lote(
            resultado_lote, TipoComprobante.EXTRACTO, "movimiento", "movimientos", "tu extracto"
        )
    elif content_type == "application/pdf" and contar_paginas_pdf(contenido) > 1:
        resultado_lote = procesar_resumen(
            sesion, usuario, proveedor_llm, reloj, contenido, content_type, nombre_archivo
        )
        modo, resultado, texto_asistente = _resultado_desde_lote(
            resultado_lote, TipoComprobante.RESUMEN_TARJETA, "consumo", "consumos", "tu resumen de tarjeta"
        )
    elif content_type in FORMATOS_ADMITIDOS:
        modo = "COMPROBANTE"
        resultado = procesar_comprobante(
            sesion, usuario, proveedor_llm, reloj, contenido, content_type, nombre_archivo
        )
        texto_asistente = resultado.mensaje
    else:
        raise ErrorComprobante(415, MENSAJE_FORMATOS_ADJUNTO)

    conversacion = obtener_o_crear_conversacion(sesion, usuario, conversacion_id, nombre_archivo)
    guardar_mensaje(
        sesion, conversacion, RolMensaje.USUARIO, _mensaje_usuario_adjunto(content_type, nombre_archivo)
    )
    mensaje_asistente = guardar_mensaje(sesion, conversacion, RolMensaje.ASISTENTE, texto_asistente)
    sesion.commit()

    return modo, resultado, conversacion.id, mensaje_asistente.id


def _resultado_desde_lote(
    resultado_lote: ResumenRespuesta | ExtractoRespuesta,
    tipo_comprobante: TipoComprobante,
    singular: str,
    plural: str,
    posesivo: str,
) -> tuple[str, ComprobanteRespuesta | ResumenRespuesta | ExtractoRespuesta, str]:
    """Un resumen o extracto con un único movimiento no tiene nada para lotear: se trata igual
    que subir la imagen de un comprobante puntual (misma tarjeta, mismos chips, confirmable al
    toque), en vez de mandar al usuario a la pantalla de revisión en lote para un solo ítem."""
    if len(resultado_lote.items) == 1:
        item = resultado_lote.items[0]
        borrador = BorradorMovimientoSalida(
            monto=item.monto,
            fecha=item.fecha,
            tipo=item.tipo,
            descripcion=item.descripcion,
            categoria_id=item.categoria_id,
            categoria_sugerida=item.categoria_sugerida,
            medio_pago_id=item.medio_pago_id,
        )
        comprobante = ComprobanteRespuesta(
            borrador=borrador,
            archivo_ref=resultado_lote.archivo_ref,
            comprobante_tipo=tipo_comprobante,
            mensaje=MENSAJE_MOVIMIENTO_INTERPRETADO,
        )
        return "COMPROBANTE", comprobante, MENSAJE_MOVIMIENTO_INTERPRETADO

    cantidad = len(resultado_lote.items)
    texto = f"Encontré {cantidad} {singular if cantidad == 1 else plural} en {posesivo}, revisalos y confirmalos."
    modo = "RESUMEN" if tipo_comprobante == TipoComprobante.RESUMEN_TARJETA else "EXTRACTO"
    return modo, resultado_lote, texto


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
