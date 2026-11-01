from sqlalchemy.orm import Session

from app.esquemas.admin import AdminUsuarioEntrada
from app.modelos.usuario import Usuario


def editar_usuario(sesion: Session, usuario_id: int, datos: AdminUsuarioEntrada) -> Usuario | None:
    raise NotImplementedError
