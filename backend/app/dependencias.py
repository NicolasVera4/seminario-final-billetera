from fastapi import Depends
from sqlalchemy.orm import Session

from app.db import obtener_sesion
from app.modelos.usuario import Usuario
from app.servicios.reloj import Reloj, obtener_reloj


def usuario_actual(
    sesion: Session = Depends(obtener_sesion),
    reloj: Reloj = Depends(obtener_reloj),
) -> Usuario:
    raise NotImplementedError
