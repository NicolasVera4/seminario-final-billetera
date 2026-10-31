from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import obtener_sesion
from app.dependencias import usuario_actual
from app.esquemas.chat import ChatEntrada, ChatSalida, ConversacionSalida, MensajeSalida
from app.modelos.conversacion import Conversacion
from app.modelos.mensaje import Mensaje
from app.modelos.usuario import Usuario
from app.proveedores.llm import ProveedorLLM, obtener_proveedor_llm
from app.servicios import interpretacion as servicio_interpretacion
from app.servicios.reloj import Reloj, obtener_reloj

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/mensajes", response_model=ChatSalida)
def enviar_mensaje(
    datos: ChatEntrada,
    usuario: Usuario = Depends(usuario_actual),
    sesion: Session = Depends(obtener_sesion),
    reloj: Reloj = Depends(obtener_reloj),
    proveedor_llm: ProveedorLLM = Depends(obtener_proveedor_llm),
):
    return servicio_interpretacion.procesar_mensaje(sesion, usuario, proveedor_llm, reloj, datos)


@router.get("/conversaciones", response_model=list[ConversacionSalida])
def listar_conversaciones(
    usuario: Usuario = Depends(usuario_actual),
    sesion: Session = Depends(obtener_sesion),
):
    conversaciones = sesion.execute(
        select(Conversacion)
        .where(Conversacion.usuario_id == usuario.id)
        .order_by(Conversacion.actualizado_en.desc())
    ).scalars().all()
    return conversaciones


@router.get("/conversaciones/{conversacion_id}", response_model=list[MensajeSalida])
def obtener_conversacion(
    conversacion_id: int,
    usuario: Usuario = Depends(usuario_actual),
    sesion: Session = Depends(obtener_sesion),
):
    conversacion = sesion.get(Conversacion, conversacion_id)
    if conversacion is None or conversacion.usuario_id != usuario.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversación no encontrada.")

    mensajes = sesion.execute(
        select(Mensaje).where(Mensaje.conversacion_id == conversacion_id).order_by(Mensaje.creado_en)
    ).scalars().all()
    return mensajes
