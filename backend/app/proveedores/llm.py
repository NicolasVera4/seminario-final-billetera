from collections.abc import Callable
from datetime import date
from typing import Protocol

from app.esquemas.chat import MensajeSalida
from app.esquemas.movimientos import BorradorMovimientoSalida, Catalogo, Interpretacion
from app.modelos.enums import TipoComprobante


class ErrorInterpretacion(Exception):
    """El modelo no devolvió un JSON valido tras reintentar."""


class ProveedorLLM(Protocol):
    def clasificar_e_interpretar(self, texto: str, hoy: date, catalogo: Catalogo) -> Interpretacion: ...

    def extraer_movimientos(
        self, texto_documento: str, tipo: TipoComprobante, catalogo: Catalogo
    ) -> list[BorradorMovimientoSalida]: ...

    def responder(
        self,
        pregunta: str,
        contexto_usuario: str | None,
        fragmentos: list,
        historial: list[MensajeSalida],
    ) -> str: ...


class ProveedorGroq:
    """Implementacion real: llama a Groq en modo JSON y reintenta una vez si la respuesta no valida."""

    def __init__(self, cliente_json: Callable[[str], str] | None = None):
        self._cliente_json = cliente_json or self._completar_con_groq

    def _completar_con_groq(self, prompt: str) -> str:
        raise NotImplementedError

    def clasificar_e_interpretar(self, texto: str, hoy: date, catalogo: Catalogo) -> Interpretacion:
        raise NotImplementedError

    def extraer_movimientos(
        self, texto_documento: str, tipo: TipoComprobante, catalogo: Catalogo
    ) -> list[BorradorMovimientoSalida]:
        raise NotImplementedError

    def responder(
        self,
        pregunta: str,
        contexto_usuario: str | None,
        fragmentos: list,
        historial: list[MensajeSalida],
    ) -> str:
        raise NotImplementedError


def obtener_proveedor_llm() -> ProveedorLLM:
    return ProveedorGroq()
