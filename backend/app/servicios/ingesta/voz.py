from app.proveedores.transcripcion import ErrorTranscripcion, Transcriptor
from app.servicios.errores import ErrorServicio

FORMATOS_ADMITIDOS = {"audio/webm", "audio/ogg", "audio/mpeg", "audio/mp3", "audio/wav", "audio/x-wav"}
TAMANO_MAXIMO_BYTES = 10 * 1024 * 1024

MENSAJE_FORMATO = "Formato de audio no admitido. Probá grabar de nuevo o escribí el mensaje."
MENSAJE_TAMANO = "El audio supera el tamaño máximo de 10 MB."
MENSAJE_NO_TRANSCRIBIBLE = "No pudimos transcribir el audio. Probá grabarlo de nuevo o escribí el mensaje."


class ErrorAudio(ErrorServicio):
    pass


def transcribir_audio(transcriptor: Transcriptor, contenido: bytes, content_type: str) -> str:
    if content_type not in FORMATOS_ADMITIDOS:
        raise ErrorAudio(415, MENSAJE_FORMATO)
    if len(contenido) > TAMANO_MAXIMO_BYTES:
        raise ErrorAudio(413, MENSAJE_TAMANO)

    try:
        texto = transcriptor.transcribir(contenido)
    except ErrorTranscripcion:
        raise ErrorAudio(422, MENSAJE_NO_TRANSCRIBIBLE)

    if not texto or not texto.strip():
        raise ErrorAudio(422, MENSAJE_NO_TRANSCRIBIBLE)

    return texto.strip()
