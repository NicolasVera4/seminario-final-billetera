from fastapi import Depends, HTTPException, Request, Response, status
from jose import JWTError
from sqlalchemy.orm import Session

from app.db import obtener_sesion
from app.modelos.enums import RolUsuario
from app.modelos.usuario import Usuario
from app.servicios.seguridad import decodificar_token, generar_token


def usuario_actual(
    request: Request,
    response: Response,
    sesion: Session = Depends(obtener_sesion),
) -> Usuario:
    encabezado = request.headers.get("Authorization", "")
    if not encabezado.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No autenticado.")

    token = encabezado.removeprefix("Bearer ")
    try:
        payload = decodificar_token(token)
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Sesión vencida.")

    usuario = sesion.get(Usuario, int(payload["sub"]))
    if usuario is None or not usuario.activo:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No autenticado.")

    response.headers["X-Token-Renovado"] = generar_token(usuario.id)
    return usuario


def usuario_no_admin(usuario: Usuario = Depends(usuario_actual)) -> Usuario:
    """El administrador no accede a movimientos ni conversaciones de usuarios (PRD, perfiles)."""
    if usuario.rol == RolUsuario.ADMINISTRADOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Los administradores no acceden a los movimientos ni a las conversaciones.",
        )
    return usuario


def administrador_actual(usuario: Usuario = Depends(usuario_actual)) -> Usuario:
    if usuario.rol != RolUsuario.ADMINISTRADOR:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Requiere rol administrador.")
    return usuario
