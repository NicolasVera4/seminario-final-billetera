import chromadb
from chromadb.api import ClientAPI

from app.config import settings

COLECCION_FRAGMENTOS = "fragmentos_referencia"


def obtener_cliente_chroma() -> ClientAPI:
    url = settings.chroma_url.replace("http://", "").replace("https://", "")
    host, _, puerto = url.partition(":")
    return chromadb.HttpClient(host=host, port=int(puerto) if puerto else 8000)
