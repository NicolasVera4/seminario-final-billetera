from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import obtener_sesion
from app.dependencias import usuario_actual
from app.esquemas.dashboard import DashboardSalida
from app.modelos.usuario import Usuario
from app.servicios import dashboard as servicio_dashboard
from app.servicios.reloj import Reloj, obtener_reloj

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard", response_model=DashboardSalida)
def obtener(
    mes: str | None = None,
    usuario: Usuario = Depends(usuario_actual),
    sesion: Session = Depends(obtener_sesion),
    reloj: Reloj = Depends(obtener_reloj),
):
    return servicio_dashboard.obtener_dashboard(sesion, usuario, mes, reloj)
