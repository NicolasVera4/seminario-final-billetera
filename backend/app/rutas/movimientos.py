from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db import obtener_sesion
from app.dependencias import usuario_no_admin
from app.esquemas.movimientos import (
    HistorialSalida,
    MovimientoEntrada,
    MovimientoSalida,
    ResultadoValidacionSalida,
)
from app.modelos.enums import TipoMovimiento
from app.modelos.usuario import Usuario
from app.servicios import movimientos as servicio_movimientos
from app.servicios.reloj import Reloj, obtener_reloj

router = APIRouter(prefix="/movimientos", tags=["movimientos"])


@router.post("/validar", response_model=ResultadoValidacionSalida)
def validar(
    datos: MovimientoEntrada,
    usuario: Usuario = Depends(usuario_no_admin),
    sesion: Session = Depends(obtener_sesion),
    reloj: Reloj = Depends(obtener_reloj),
):
    return servicio_movimientos.validar_borrador(sesion, usuario, datos, reloj)


@router.post("", response_model=list[MovimientoSalida], status_code=201)
def guardar(
    datos: list[MovimientoEntrada],
    usuario: Usuario = Depends(usuario_no_admin),
    sesion: Session = Depends(obtener_sesion),
    reloj: Reloj = Depends(obtener_reloj),
):
    return servicio_movimientos.guardar_movimientos(sesion, usuario, datos, reloj)


@router.get("", response_model=HistorialSalida)
def listar(
    desde: date | None = None,
    hasta: date | None = None,
    categoria_id: int | None = None,
    tipo: TipoMovimiento | None = None,
    medio_pago_id: int | None = None,
    q: str | None = None,
    pagina: int = Query(default=1, ge=1),
    por_pagina: int = Query(default=15, ge=1, le=100),
    usuario: Usuario = Depends(usuario_no_admin),
    sesion: Session = Depends(obtener_sesion),
):
    return servicio_movimientos.listar_movimientos(
        sesion, usuario, desde, hasta, categoria_id, tipo, medio_pago_id, q, pagina, por_pagina
    )
