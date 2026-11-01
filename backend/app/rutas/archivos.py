from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.db import obtener_sesion
from app.dependencias import usuario_no_admin
from app.esquemas.archivos import ComprobanteRespuesta, ResumenRespuesta
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
