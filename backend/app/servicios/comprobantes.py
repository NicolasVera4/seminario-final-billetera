import uuid
from pathlib import Path

from sqlalchemy.orm import Session

from app.config import settings
from app.esquemas.archivos import ComprobanteRespuesta
from app.esquemas.movimientos import BorradorMovimientoSalida
from app.modelos.enums import TipoComprobante
from app.modelos.usuario import Usuario
from app.proveedores.llm import ErrorInterpretacion, ProveedorLLM
from app.servicios.ingesta.ocr import extraer_texto_imagen
from app.servicios.ingesta.pdf import extraer_texto_pdf
from app.servicios.interpretacion import obtener_catalogo, resolver_categoria, resolver_medio_pago
from app.servicios.reloj import Reloj

FORMATOS_ADMITIDOS = {
    "image/jpeg": TipoComprobante.TICKET,
    "image/png": TipoComprobante.TICKET,
    "image/webp": TipoComprobante.TICKET,
    "application/pdf": TipoComprobante.FACTURA,
}
TAMANO_MAXIMO_BYTES = 10 * 1024 * 1024

MENSAJE_FORMATOS = "Formato no admitido. Subí una imagen (jpg, png, webp) o un PDF."
MENSAJE_TAMANO = "El archivo supera el tamaño máximo de 10 MB."
MENSAJE_SIN_MONTO = "No pudimos leer un monto en el archivo. Probá cargarlo por texto."
MENSAJE_NO_INTERPRETABLE = "No pudimos leer el comprobante. Probá cargarlo por texto."
MENSAJE_MOVIMIENTO_INTERPRETADO = "Encontré este movimiento, revisalo y confirmalo."


class ErrorComprobante(Exception):
    def __init__(self, status_code: int, detail: str):
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


def procesar_comprobante(
    sesion: Session,
    usuario: Usuario,
    proveedor_llm: ProveedorLLM,
    reloj: Reloj,
    contenido: bytes,
    content_type: str,
    nombre_archivo: str,
) -> ComprobanteRespuesta:
    if content_type not in FORMATOS_ADMITIDOS:
        raise ErrorComprobante(415, MENSAJE_FORMATOS)
    if len(contenido) > TAMANO_MAXIMO_BYTES:
        raise ErrorComprobante(413, MENSAJE_TAMANO)

    tipo_comprobante = FORMATOS_ADMITIDOS[content_type]
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


def _guardar_archivo(usuario_id: int, nombre_original: str, contenido: bytes) -> str:
    directorio = Path(settings.archivos_dir) / str(usuario_id)
    directorio.mkdir(parents=True, exist_ok=True)
    nombre_archivo = f"{uuid.uuid4().hex}_{nombre_original}"
    (directorio / nombre_archivo).write_bytes(contenido)
    return f"{usuario_id}/{nombre_archivo}"
