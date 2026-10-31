from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import obtener_sesion
from app.dependencias import usuario_actual
from app.esquemas.movimientos import (
    MovimientoEntrada,
    MovimientoSalida,
    ResultadoValidacionSalida,
)
from app.modelos.usuario import Usuario
from app.servicios import movimientos as servicio_movimientos
from app.servicios.reloj import Reloj, obtener_reloj

router = APIRouter(prefix="/movimientos", tags=["movimientos"])


@router.post("/validar", response_model=ResultadoValidacionSalida)
def validar(
    datos: MovimientoEntrada,
    usuario: Usuario = Depends(usuario_actual),
    sesion: Session = Depends(obtener_sesion),
    reloj: Reloj = Depends(obtener_reloj),
):
    return servicio_movimientos.validar_borrador(sesion, usuario, datos, reloj)


@router.post("", response_model=list[MovimientoSalida], status_code=201)
def guardar(
    datos: list[MovimientoEntrada],
    usuario: Usuario = Depends(usuario_actual),
    sesion: Session = Depends(obtener_sesion),
    reloj: Reloj = Depends(obtener_reloj),
):
    return servicio_movimientos.guardar_movimientos(sesion, usuario, datos, reloj)
