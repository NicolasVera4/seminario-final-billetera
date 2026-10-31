from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import obtener_sesion
from app.dependencias import usuario_actual
from app.esquemas.movimientos import CatalogosSalida
from app.modelos.usuario import Usuario
from app.servicios import movimientos as servicio_movimientos

router = APIRouter(tags=["catalogos"])


@router.get("/catalogos", response_model=CatalogosSalida)
def obtener_catalogos(
    usuario: Usuario = Depends(usuario_actual),
    sesion: Session = Depends(obtener_sesion),
):
    return servicio_movimientos.obtener_catalogos(sesion)
