from sqlalchemy.orm import Session

from app.esquemas.chat import ChatEntrada, ChatSalida
from app.modelos.categoria import Categoria
from app.modelos.medio_pago import MedioPago
from app.modelos.usuario import Usuario
from app.proveedores.llm import ProveedorLLM
from app.servicios.reloj import Reloj


def procesar_mensaje(
    sesion: Session,
    usuario: Usuario,
    proveedor_llm: ProveedorLLM,
    reloj: Reloj,
    datos: ChatEntrada,
) -> ChatSalida:
    raise NotImplementedError


def resolver_categoria(categorias: list[Categoria], nombre: str | None) -> tuple[int | None, str | None]:
    """Devuelve (categoria_id, categoria_sugerida). Si nombre no esta en el catalogo, categoria_id es None."""
    raise NotImplementedError


def resolver_medio_pago(medios_pago: list[MedioPago], nombre: str | None) -> int | None:
    """Devuelve el id del medio de pago, o None si esta ausente o no esta en el catalogo."""
    raise NotImplementedError
