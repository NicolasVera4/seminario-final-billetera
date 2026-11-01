from app.proveedores.transcripcion import Transcriptor

FORMATOS_ADMITIDOS = {"audio/webm", "audio/ogg", "audio/mpeg", "audio/mp3", "audio/wav", "audio/x-wav"}
TAMANO_MAXIMO_BYTES = 10 * 1024 * 1024

MENSAJE_FORMATO = "Formato de audio no admitido. Probá grabar de nuevo o escribí el mensaje."
MENSAJE_TAMANO = "El audio supera el tamaño máximo de 10 MB."
MENSAJE_NO_TRANSCRIBIBLE = "No pudimos transcribir el audio. Probá grabarlo de nuevo o escribí el mensaje."


class ErrorAudio(Exception):
    def __init__(self, status_code: int, detail: str):
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


def transcribir_audio(transcriptor: Transcriptor, contenido: bytes, content_type: str) -> str:
    raise NotImplementedError
