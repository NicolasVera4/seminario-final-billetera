from sqlalchemy.orm import Session

from app.esquemas.auth import LoginEntrada, RegistroEntrada
from app.modelos.usuario import Usuario
from app.servicios.reloj import Reloj


def registrar_usuario(sesion: Session, datos: RegistroEntrada) -> Usuario:
    raise NotImplementedError


def autenticar(sesion: Session, datos: LoginEntrada, reloj: Reloj) -> str:
    raise NotImplementedError
