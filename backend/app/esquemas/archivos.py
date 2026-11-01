from datetime import date
from decimal import Decimal

from pydantic import BaseModel

from app.esquemas.movimientos import BorradorMovimientoSalida
from app.modelos.enums import TipoComprobante, TipoMovimiento


class ComprobanteRespuesta(BaseModel):
    borrador: BorradorMovimientoSalida | None
    archivo_ref: str | None
    comprobante_tipo: TipoComprobante | None
    mensaje: str


class ItemResumenSalida(BaseModel):
    monto: Decimal
    fecha: date
    tipo: TipoMovimiento
    descripcion: str
    categoria_id: int | None
    categoria_sugerida: str | None
    medio_pago_id: int | None
    cuota_numero: int | None
    cuota_total: int | None
    errores: list[str]
    posible_duplicado: bool


class ResumenRespuesta(BaseModel):
    items: list[ItemResumenSalida]
    archivo_ref: str
    comprobante_tipo: TipoComprobante
    paginas_leidas: int


class ExtractoRespuesta(BaseModel):
    items: list[ItemResumenSalida]
    archivo_ref: str
    filas_descartadas: int
