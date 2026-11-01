from chromadb.api import ClientAPI
from sqlalchemy.orm import Session

from app.esquemas.chat import MensajeSalida
from app.modelos.documento_referencia import DocumentoReferencia
from app.modelos.usuario import Usuario
from app.proveedores.embeddings import Embedder
from app.proveedores.llm import ProveedorLLM
from app.servicios.reloj import Reloj

DISCLAIMER = "Esto es orientativo y no reemplaza el asesoramiento de un profesional."


def cargar_documento(
    sesion: Session, cliente_chroma: ClientAPI, embedder: Embedder, titulo: str, texto: str
) -> DocumentoReferencia:
    raise NotImplementedError


def eliminar_documento(sesion: Session, cliente_chroma: ClientAPI, documento_id: int) -> None:
    raise NotImplementedError


def listar_documentos(sesion: Session) -> list[DocumentoReferencia]:
    raise NotImplementedError


def responder_consulta(
    sesion: Session,
    usuario: Usuario,
    cliente_chroma: ClientAPI,
    embedder: Embedder,
    proveedor_llm: ProveedorLLM,
    reloj: Reloj,
    pregunta: str,
    intencion: str,
    historial: list[MensajeSalida],
) -> tuple[str, list[dict]]:
    raise NotImplementedError
