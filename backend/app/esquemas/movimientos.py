from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel

from app.modelos.enums import TipoComprobante, TipoMovimiento


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
    cuota_numero: int | None = None
    cuota_total: int | None = None


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


class ItemCategoriaSalida(BaseModel):
    id: int
    nombre: str

    model_config = {"from_attributes": True}


class CatalogosSalida(BaseModel):
    categorias: list[ItemCategoriaSalida]
    medios_pago: list[ItemCategoriaSalida]
    origenes: list[ItemCategoriaSalida]


class MovimientoEntrada(BaseModel):
    monto: Decimal
    fecha: date
    tipo: TipoMovimiento
    descripcion: str
    categoria_id: int | None = None
    medio_pago_id: int | None = None
    origen: str = "Texto"
    conversacion_id: int | None = None
    comprobante_id: int | None = None
    cuota_numero: int | None = None
    cuota_total: int | None = None
    archivo_ref: str | None = None
    comprobante_tipo: TipoComprobante | None = None


class ResultadoValidacionSalida(BaseModel):
    errores: list[str]
    advertencias: list[str]


class MovimientoSalida(BaseModel):
    id: int
    monto: Decimal
    fecha: date
    tipo: TipoMovimiento
    descripcion: str
    categoria_id: int | None
    medio_pago_id: int | None
    origen_id: int
    creado_en: datetime

    model_config = {"from_attributes": True}


class MovimientoListadoSalida(BaseModel):
    id: int
    fecha: date
    descripcion: str
    categoria: str | None
    medio_pago: str | None
    origen: str
    monto: Decimal
    tipo: TipoMovimiento


class HistorialSalida(BaseModel):
    items: list[MovimientoListadoSalida]
    total: int
    pagina: int
    por_pagina: int
