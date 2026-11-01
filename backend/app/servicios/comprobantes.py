from sqlalchemy.orm import Session

from app.esquemas.archivos import ComprobanteRespuesta
from app.modelos.enums import TipoComprobante
from app.modelos.usuario import Usuario
from app.proveedores.llm import ProveedorLLM
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
    raise NotImplementedError
