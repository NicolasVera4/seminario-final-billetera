from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel

from app.modelos.enums import TipoMovimiento


class Catalogo(BaseModel):
    categorias: list[str]
    medios_pago: list[str]


class InterpretacionMovimiento(BaseModel):
    monto: Decimal | None = None
    fecha: date | None = None
    tipo: TipoMovimiento | None = None
    medio_pago: str | None = None
    descripcion: str | None = None
    categoria: str | None = None


class Interpretacion(BaseModel):
    intencion: Literal["REGISTRO", "CONSULTA_DATOS", "CONSULTA_ASESORAMIENTO"]
    movimiento: InterpretacionMovimiento | None = None
    faltantes: list[str] = []


class BorradorMovimientoSalida(BaseModel):
    monto: Decimal
    fecha: date
    tipo: TipoMovimiento
    descripcion: str
    categoria_id: int | None
    categoria_sugerida: str | None
    medio_pago_id: int | None
