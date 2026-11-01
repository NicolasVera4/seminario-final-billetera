import tempfile
from typing import Protocol

from faster_whisper import WhisperModel

from app.config import settings


class ErrorTranscripcion(Exception):
    """El modelo no pudo transcribir el audio."""


class Transcriptor(Protocol):
    def transcribir(self, contenido: bytes) -> str: ...


class TranscriptorWhisper:
    def __init__(self):
        self._modelo: WhisperModel | None = None

    def _obtener_modelo(self) -> WhisperModel:
        if self._modelo is None:
            self._modelo = WhisperModel(settings.whisper_modelo, device="cpu", compute_type="int8")
        return self._modelo

    def transcribir(self, contenido: bytes) -> str:
        try:
            with tempfile.NamedTemporaryFile(suffix=".audio") as archivo_temporal:
                archivo_temporal.write(contenido)
                archivo_temporal.flush()
                segmentos, _ = self._obtener_modelo().transcribe(archivo_temporal.name, language="es")
                return " ".join(segmento.text.strip() for segmento in segmentos).strip()
        except Exception as error:
            raise ErrorTranscripcion from error


def obtener_transcriptor() -> Transcriptor:
    return TranscriptorWhisper()
