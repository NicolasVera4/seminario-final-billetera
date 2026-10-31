from datetime import datetime

from pydantic import BaseModel

from app.esquemas.movimientos import BorradorMovimientoSalida
from app.modelos.enums import RolMensaje


class ChatEntrada(BaseModel):
    conversacion_id: int | None = None
    texto: str


class MensajeSalida(BaseModel):
    id: int
    rol: RolMensaje
    contenido: str
    fuentes: list | None
    creado_en: datetime

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
