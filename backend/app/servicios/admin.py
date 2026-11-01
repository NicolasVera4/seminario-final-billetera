from sqlalchemy.orm import Session

from app.esquemas.admin import AdminUsuarioEntrada
from app.modelos.usuario import Usuario


def editar_usuario(sesion: Session, usuario_id: int, datos: AdminUsuarioEntrada) -> Usuario | None:
    usuario = sesion.get(Usuario, usuario_id)
    if usuario is None:
        return None

    if datos.nombre is not None:
        usuario.nombre = datos.nombre
    if datos.correo is not None:
        usuario.correo = datos.correo.lower()
    if datos.activo is not None:
        usuario.activo = datos.activo
    if datos.desbloquear:
        usuario.bloqueado_hasta = None
        usuario.intentos_fallidos = 0

    sesion.commit()
    sesion.refresh(usuario)
    return usuario
