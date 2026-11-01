from datetime import datetime

from pydantic import BaseModel


class DocumentoReferenciaSalida(BaseModel):
    id: int
    titulo: str
    cantidad_fragmentos: int
    creado_en: datetime

    model_config = {"from_attributes": True}


class AdminUsuarioEntrada(BaseModel):
    nombre: str | None = None
    correo: str | None = None
    activo: bool | None = None
    desbloquear: bool = False


class AdminUsuarioSalida(BaseModel):
    id: int
    nombre: str
    correo: str
    activo: bool
    bloqueado_hasta: datetime | None

    model_config = {"from_attributes": True}
