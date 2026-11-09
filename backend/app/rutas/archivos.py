from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.db import obtener_sesion
from app.dependencias import usuario_no_admin
from app.esquemas.archivos import (
    AdjuntoRespuesta,
    ComprobanteAdjuntoRespuesta,
    ComprobanteRespuesta,
    ExtractoAdjuntoRespuesta,
    ExtractoRespuesta,
    ResumenAdjuntoRespuesta,
    ResumenRespuesta,
)
from app.modelos.usuario import Usuario
from app.proveedores.llm import ProveedorLLM, obtener_proveedor_llm
from app.servicios import comprobantes as servicio_comprobantes
from app.servicios.comprobantes import ErrorComprobante
from app.servicios.reloj import Reloj, obtener_reloj

router = APIRouter(prefix="/archivos", tags=["archivos"])


@router.post("/comprobante", response_model=ComprobanteRespuesta)
async def subir_comprobante(
    archivo: UploadFile,
    usuario: Usuario = Depends(usuario_no_admin),
    sesion: Session = Depends(obtener_sesion),
    reloj: Reloj = Depends(obtener_reloj),
    proveedor_llm: ProveedorLLM = Depends(obtener_proveedor_llm),
):
    contenido = await archivo.read()
    try:
        return servicio_comprobantes.procesar_comprobante(
            sesion, usuario, proveedor_llm, reloj, contenido, archivo.content_type, archivo.filename
        )
    except ErrorComprobante as error:
        raise HTTPException(status_code=error.status_code, detail=error.detail)


@router.post("/resumen", response_model=ResumenRespuesta)
async def subir_resumen(
    archivo: UploadFile,
    usuario: Usuario = Depends(usuario_no_admin),
    sesion: Session = Depends(obtener_sesion),
    reloj: Reloj = Depends(obtener_reloj),
    proveedor_llm: ProveedorLLM = Depends(obtener_proveedor_llm),
):
    contenido = await archivo.read()
    try:
        return servicio_comprobantes.procesar_resumen(
            sesion, usuario, proveedor_llm, reloj, contenido, archivo.content_type, archivo.filename
        )
    except ErrorComprobante as error:
        raise HTTPException(status_code=error.status_code, detail=error.detail)


@router.post("/adjuntar", response_model=AdjuntoRespuesta)
async def subir_adjunto(
    archivo: UploadFile,
    conversacion_id: int | None = Form(default=None),
    usuario: Usuario = Depends(usuario_no_admin),
    sesion: Session = Depends(obtener_sesion),
    reloj: Reloj = Depends(obtener_reloj),
    proveedor_llm: ProveedorLLM = Depends(obtener_proveedor_llm),
):
    contenido = await archivo.read()
    try:
        modo, resultado, conv_id, mensaje_id = servicio_comprobantes.procesar_adjunto(
            sesion,
            usuario,
            proveedor_llm,
            reloj,
            contenido,
            archivo.content_type,
            archivo.filename,
            conversacion_id,
        )
    except ErrorComprobante as error:
        raise HTTPException(status_code=error.status_code, detail=error.detail)

    extra = {"conversacion_id": conv_id, "mensaje_id": mensaje_id}
    if modo == "COMPROBANTE":
        return ComprobanteAdjuntoRespuesta(**resultado.model_dump(), **extra)
    if modo == "RESUMEN":
        return ResumenAdjuntoRespuesta(**resultado.model_dump(), **extra)
    return ExtractoAdjuntoRespuesta(**resultado.model_dump(), **extra)


@router.post("/extracto", response_model=ExtractoRespuesta)
async def subir_extracto(
    archivo: UploadFile,
    usuario: Usuario = Depends(usuario_no_admin),
    sesion: Session = Depends(obtener_sesion),
    reloj: Reloj = Depends(obtener_reloj),
    proveedor_llm: ProveedorLLM = Depends(obtener_proveedor_llm),
):
    contenido = await archivo.read()
    try:
        return servicio_comprobantes.procesar_extracto(
            sesion, usuario, proveedor_llm, reloj, contenido, archivo.content_type, archivo.filename
        )
    except ErrorComprobante as error:
        raise HTTPException(status_code=error.status_code, detail=error.detail)
