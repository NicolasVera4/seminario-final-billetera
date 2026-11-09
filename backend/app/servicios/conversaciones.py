from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.modelos.conversacion import Conversacion
from app.modelos.enums import RolMensaje
from app.modelos.mensaje import Mensaje
from app.modelos.usuario import Usuario


def obtener_o_crear_conversacion(
    sesion: Session, usuario: Usuario, conversacion_id: int | None, titulo_si_nueva: str
) -> Conversacion:
    if conversacion_id is not None:
        conversacion = sesion.get(Conversacion, conversacion_id)
        if conversacion is None or conversacion.usuario_id != usuario.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Conversación no encontrada."
            )
        return conversacion

    titulo = titulo_si_nueva.strip()[:40] or None
    conversacion = Conversacion(usuario_id=usuario.id, titulo=titulo)
    sesion.add(conversacion)
    sesion.flush()
    return conversacion


def guardar_mensaje(
    sesion: Session,
    conversacion: Conversacion,
    rol: RolMensaje,
    contenido: str,
    fuentes: list[dict] | None = None,
    transcripto: bool = False,
) -> Mensaje:
    mensaje = Mensaje(
        conversacion_id=conversacion.id,
        rol=rol,
        contenido=contenido,
        fuentes=fuentes,
        transcripto=transcripto,
    )
    sesion.add(mensaje)
    sesion.flush()
    sesion.refresh(mensaje)
    return mensaje
