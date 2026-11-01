from pydantic import BaseModel


class TranscripcionRespuesta(BaseModel):
    texto: str
