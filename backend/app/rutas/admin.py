from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.db import obtener_sesion
from app.dependencias import administrador_actual
from app.esquemas.admin import AdminUsuarioEntrada, AdminUsuarioSalida, DocumentoReferenciaSalida
from app.modelos.usuario import Usuario
from app.proveedores.embeddings import Embedder, obtener_embedder
from app.proveedores.vectorial import obtener_cliente_chroma
from app.servicios import admin as servicio_admin
from app.servicios import asesoramiento as servicio_asesoramiento
from app.servicios.ingesta.pdf import extraer_texto_pdf

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/documentos", response_model=list[DocumentoReferenciaSalida])
def listar_documentos(
    _admin: Usuario = Depends(administrador_actual),
    sesion: Session = Depends(obtener_sesion),
):
    return servicio_asesoramiento.listar_documentos(sesion)


@router.post("/documentos", response_model=DocumentoReferenciaSalida, status_code=status.HTTP_201_CREATED)
async def cargar_documento(
    titulo: str,
    archivo: UploadFile,
    _admin: Usuario = Depends(administrador_actual),
    sesion: Session = Depends(obtener_sesion),
    embedder: Embedder = Depends(obtener_embedder),
    cliente_chroma=Depends(obtener_cliente_chroma),
):
    contenido = await archivo.read()
    if archivo.content_type == "application/pdf":
        texto = extraer_texto_pdf(contenido)
    else:
        texto = contenido.decode("utf-8")
    return servicio_asesoramiento.cargar_documento(sesion, cliente_chroma, embedder, titulo, texto)


@router.delete("/documentos/{documento_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_documento(
    documento_id: int,
    _admin: Usuario = Depends(administrador_actual),
    sesion: Session = Depends(obtener_sesion),
    cliente_chroma=Depends(obtener_cliente_chroma),
):
    servicio_asesoramiento.eliminar_documento(sesion, cliente_chroma, documento_id)


@router.patch("/usuarios/{usuario_id}", response_model=AdminUsuarioSalida)
def editar_usuario(
    usuario_id: int,
    datos: AdminUsuarioEntrada,
    _admin: Usuario = Depends(administrador_actual),
    sesion: Session = Depends(obtener_sesion),
):
    usuario = servicio_admin.editar_usuario(sesion, usuario_id, datos)
    if usuario is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado.")
    return usuario
