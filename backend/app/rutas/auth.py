from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db import obtener_sesion
from app.dependencias import usuario_actual
from app.esquemas.auth import LoginEntrada, RegistroEntrada, TokenSalida, UsuarioSalida
from app.modelos.usuario import Usuario
from app.servicios import auth as servicio_auth
from app.servicios.reloj import Reloj, obtener_reloj

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/registro", response_model=UsuarioSalida, status_code=status.HTTP_201_CREATED)
def registro(datos: RegistroEntrada, sesion: Session = Depends(obtener_sesion)):
    try:
        return servicio_auth.registrar_usuario(sesion, datos)
    except IntegrityError:
        sesion.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ya existe una cuenta con este correo.")


@router.post("/login", response_model=TokenSalida)
def login(
    datos: LoginEntrada,
    sesion: Session = Depends(obtener_sesion),
    reloj: Reloj = Depends(obtener_reloj),
):
    token = servicio_auth.autenticar(sesion, datos, reloj)
    return TokenSalida(access_token=token)


@router.get("/yo", response_model=UsuarioSalida)
def yo(usuario: Usuario = Depends(usuario_actual)):
    return usuario
