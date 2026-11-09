from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import obtener_sesion
from app.dependencias import usuario_no_admin
from app.esquemas.chat import ChatEntrada, ChatSalida, ConversacionSalida, MensajeSalida
from app.esquemas.movimientos import BorradorMovimientoSalida
from app.modelos.conversacion import Conversacion
from app.modelos.mensaje import Mensaje
from app.modelos.movimiento import Movimiento
from app.modelos.usuario import Usuario
from app.proveedores.embeddings import Embedder, obtener_embedder
from app.proveedores.llm import ProveedorLLM, obtener_proveedor_llm
from app.proveedores.vectorial import obtener_cliente_chroma
from app.servicios import interpretacion as servicio_interpretacion
from app.servicios.reloj import Reloj, obtener_reloj

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/mensajes", response_model=ChatSalida)
def enviar_mensaje(
    datos: ChatEntrada,
    usuario: Usuario = Depends(usuario_no_admin),
    sesion: Session = Depends(obtener_sesion),
    reloj: Reloj = Depends(obtener_reloj),
    proveedor_llm: ProveedorLLM = Depends(obtener_proveedor_llm),
    embedder: Embedder = Depends(obtener_embedder),
    cliente_chroma=Depends(obtener_cliente_chroma),
):
    return servicio_interpretacion.procesar_mensaje(
        sesion, usuario, proveedor_llm, reloj, datos, embedder, cliente_chroma
    )


@router.get("/conversaciones", response_model=list[ConversacionSalida])
def listar_conversaciones(
    usuario: Usuario = Depends(usuario_no_admin),
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
    usuario: Usuario = Depends(usuario_no_admin),
    sesion: Session = Depends(obtener_sesion),
):
    conversacion = sesion.get(Conversacion, conversacion_id)
    if conversacion is None or conversacion.usuario_id != usuario.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversación no encontrada.")

    mensajes = sesion.execute(
        select(Mensaje).where(Mensaje.conversacion_id == conversacion_id).order_by(Mensaje.creado_en)
    ).scalars().all()

    movimientos_por_mensaje = {
        movimiento.mensaje_id: movimiento
        for movimiento in sesion.execute(
            select(Movimiento).where(Movimiento.mensaje_id.in_([m.id for m in mensajes]))
        ).scalars().all()
    }

    salida = []
    for mensaje in mensajes:
        movimiento = movimientos_por_mensaje.get(mensaje.id)
        salida.append(
            MensajeSalida(
                id=mensaje.id,
                rol=mensaje.rol,
                contenido=mensaje.contenido,
                fuentes=mensaje.fuentes,
                transcripto=mensaje.transcripto,
                creado_en=mensaje.creado_en,
                movimiento=BorradorMovimientoSalida(
                    monto=movimiento.monto,
                    fecha=movimiento.fecha,
                    tipo=movimiento.tipo,
                    descripcion=movimiento.descripcion,
                    categoria_id=movimiento.categoria_id,
                    categoria_sugerida=movimiento.categoria_sugerida,
                    medio_pago_id=movimiento.medio_pago_id,
                )
                if movimiento
                else None,
            )
        )
    return salida
