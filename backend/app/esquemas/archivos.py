from pydantic import BaseModel

from app.esquemas.movimientos import BorradorMovimientoSalida
from app.modelos.enums import TipoComprobante


class ComprobanteRespuesta(BaseModel):
    borrador: BorradorMovimientoSalida | None
    archivo_ref: str | None
    comprobante_tipo: TipoComprobante | None
    mensaje: str
