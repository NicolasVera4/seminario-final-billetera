from fastapi import APIRouter, Depends, HTTPException, UploadFile

from app.dependencias import usuario_no_admin
from app.esquemas.voz import TranscripcionRespuesta
from app.modelos.usuario import Usuario
from app.proveedores.transcripcion import Transcriptor, obtener_transcriptor
from app.servicios.ingesta.voz import ErrorAudio, transcribir_audio

router = APIRouter(prefix="/voz", tags=["voz"])


@router.post("/transcribir", response_model=TranscripcionRespuesta)
async def transcribir(
    archivo: UploadFile,
    usuario: Usuario = Depends(usuario_no_admin),
    transcriptor: Transcriptor = Depends(obtener_transcriptor),
):
    contenido = await archivo.read()
    try:
        texto = transcribir_audio(transcriptor, contenido, archivo.content_type)
    except ErrorAudio as error:
        raise HTTPException(status_code=error.status_code, detail=error.detail)
    return TranscripcionRespuesta(texto=texto)
