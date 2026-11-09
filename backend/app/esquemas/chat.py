from datetime import datetime

from pydantic import BaseModel

from app.esquemas.movimientos import BorradorMovimientoSalida
from app.modelos.enums import RolMensaje


class ChatEntrada(BaseModel):
    conversacion_id: int | None = None
    texto: str
    transcripto: bool = False


class MensajeSalida(BaseModel):
    id: int
    rol: RolMensaje
    contenido: str
    fuentes: list | None
    transcripto: bool = False
    creado_en: datetime
    movimiento: BorradorMovimientoSalida | None = None

    model_config = {"from_attributes": True}


class ConversacionSalida(BaseModel):
    id: int
    titulo: str | None
    creado_en: datetime
    actualizado_en: datetime

    model_config = {"from_attributes": True}


class ChatSalida(BaseModel):
    conversacion_id: int
    mensaje: MensajeSalida
    borrador: BorradorMovimientoSalida | None = None
