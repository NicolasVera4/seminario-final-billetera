from sqlalchemy.orm import Session

from app.esquemas.movimientos import (
    CatalogosSalida,
    MovimientoEntrada,
    MovimientoSalida,
    ResultadoValidacionSalida,
)
from app.modelos.usuario import Usuario
from app.servicios.reloj import Reloj


def obtener_catalogos(sesion: Session) -> CatalogosSalida:
    raise NotImplementedError


def validar_borrador(
    sesion: Session, usuario: Usuario, datos: MovimientoEntrada, reloj: Reloj
) -> ResultadoValidacionSalida:
    raise NotImplementedError


def guardar_movimientos(
    sesion: Session, usuario: Usuario, datos: list[MovimientoEntrada], reloj: Reloj
) -> list[MovimientoSalida]:
    raise NotImplementedError
