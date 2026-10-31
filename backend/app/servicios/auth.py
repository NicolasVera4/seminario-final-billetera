from datetime import timedelta

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.esquemas.auth import LoginEntrada, RegistroEntrada
from app.modelos.usuario import Usuario
from app.servicios.reloj import Reloj
from app.servicios.seguridad import generar_token, hash_contrasena, verificar_contrasena

MENSAJE_ERROR_LOGIN = "El correo o la contraseña no son correctos."
MENSAJE_CUENTA_BLOQUEADA = "Cuenta bloqueada por intentos fallidos. Probá de nuevo en unos minutos."
MAX_INTENTOS_FALLIDOS = 5
MINUTOS_BLOQUEO = 15


def registrar_usuario(sesion: Session, datos: RegistroEntrada) -> Usuario:
    usuario = Usuario(
        nombre=datos.nombre,
        correo=datos.correo.lower(),
        contrasena_hash=hash_contrasena(datos.contrasena),
    )
    sesion.add(usuario)
    sesion.commit()
    sesion.refresh(usuario)
    return usuario


def autenticar(sesion: Session, datos: LoginEntrada, reloj: Reloj) -> str:
    correo_normalizado = datos.correo.lower()
    usuario = sesion.execute(
        select(Usuario).where(Usuario.correo == correo_normalizado)
    ).scalar_one_or_none()

    if usuario is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=MENSAJE_ERROR_LOGIN)

    ahora = reloj.ahora()
    if usuario.bloqueado_hasta is not None:
        if ahora < usuario.bloqueado_hasta:
            raise HTTPException(status_code=status.HTTP_423_LOCKED, detail=MENSAJE_CUENTA_BLOQUEADA)
        usuario.bloqueado_hasta = None
        usuario.intentos_fallidos = 0

    if not verificar_contrasena(datos.contrasena, usuario.contrasena_hash):
        usuario.intentos_fallidos += 1
        if usuario.intentos_fallidos >= MAX_INTENTOS_FALLIDOS:
            usuario.bloqueado_hasta = ahora + timedelta(minutes=MINUTOS_BLOQUEO)
        sesion.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=MENSAJE_ERROR_LOGIN)

    usuario.intentos_fallidos = 0
    usuario.bloqueado_hasta = None
    sesion.commit()

    return generar_token(usuario.id)
