import json
from collections.abc import Callable
from datetime import date
from typing import Protocol

from groq import Groq
from pydantic import ValidationError

from app.config import settings
from app.esquemas.chat import MensajeSalida
from app.esquemas.movimientos import Catalogo, Interpretacion, InterpretacionMovimiento
from app.modelos.enums import RolMensaje, TipoComprobante


class ErrorInterpretacion(Exception):
    """El modelo no devolvió un JSON valido tras reintentar."""


class ProveedorLLM(Protocol):
    def clasificar_e_interpretar(self, texto: str, hoy: date, catalogo: Catalogo) -> Interpretacion: ...

    def extraer_movimientos(
        self, texto_documento: str, tipo: TipoComprobante, catalogo: Catalogo
    ) -> list[InterpretacionMovimiento]: ...

    def responder(
        self,
        pregunta: str,
        contexto_usuario: str | None,
        fragmentos: list,
        historial: list[MensajeSalida],
    ) -> str: ...


def _construir_prompt_interpretacion(texto: str, hoy: date, catalogo: Catalogo) -> str:
    categorias = ", ".join(catalogo.categorias)
    medios_pago = ", ".join(catalogo.medios_pago)
    return (
        "Sos un asistente que interpreta mensajes de finanzas personales en español rioplatense.\n"
        f"Fecha de hoy: {hoy.isoformat()}.\n"
        f"Categorías válidas: {categorias}.\n"
        f"Medios de pago válidos: {medios_pago}.\n"
        "Respondé SOLO un JSON con esta forma exacta, sin texto adicional:\n"
        '{"intencion": "REGISTRO | CONSULTA_DATOS | CONSULTA_ASESORAMIENTO", '
        '"movimiento": {"monto": numero o null, "fecha": "AAAA-MM-DD" o null, "tipo": "INGRESO|EGRESO" o null, '
        '"medio_pago": "texto" o null, "descripcion": "texto" o null, "categoria": "texto" o null} o null, '
        '"faltantes": ["monto", ...]}\n'
        f"Mensaje del usuario: {texto}"
    )


def _construir_prompt_extraccion(texto_documento: str, tipo: TipoComprobante, catalogo: Catalogo) -> str:
    categorias = ", ".join(catalogo.categorias)
    medios_pago = ", ".join(catalogo.medios_pago)
    return (
        "Sos un asistente que lee comprobantes de pago en español rioplatense.\n"
        f"Tipo de documento: {tipo.value}.\n"
        f"Categorías válidas: {categorias}.\n"
        f"Medios de pago válidos: {medios_pago}.\n"
        "El documento representa UN SOLO movimiento (el total del comprobante), no detalles línea por línea.\n"
        "Respondé SOLO un JSON con esta forma exacta, sin texto adicional:\n"
        '{"movimientos": [{"monto": numero o null, "fecha": "AAAA-MM-DD" o null, '
        '"tipo": "INGRESO|EGRESO" o null, "medio_pago": "texto" o null, "descripcion": "texto" o null, '
        '"categoria": "texto" o null}]}\n'
        f"Texto extraído del documento:\n{texto_documento}"
    )


class ProveedorGroq:
    """Implementacion real: llama a Groq en modo JSON y reintenta una vez si la respuesta no valida."""

    def __init__(self, cliente_json: Callable[[str], str] | None = None):
        self._cliente_json = cliente_json or self._completar_con_groq

    def _completar_con_groq(self, prompt: str) -> str:
        cliente = Groq(api_key=settings.groq_api_key)
        respuesta = cliente.chat.completions.create(
            model=settings.groq_modelo,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
        )
        return respuesta.choices[0].message.content

    def clasificar_e_interpretar(self, texto: str, hoy: date, catalogo: Catalogo) -> Interpretacion:
        prompt = _construir_prompt_interpretacion(texto, hoy, catalogo)
        for _ in range(2):
            bruto = self._cliente_json(prompt)
            try:
                return Interpretacion.model_validate(json.loads(bruto))
            except (json.JSONDecodeError, ValidationError):
                continue
        raise ErrorInterpretacion

    def extraer_movimientos(
        self, texto_documento: str, tipo: TipoComprobante, catalogo: Catalogo
    ) -> list[InterpretacionMovimiento]:
        prompt = _construir_prompt_extraccion(texto_documento, tipo, catalogo)
        for _ in range(2):
            bruto = self._cliente_json(prompt)
            try:
                datos = json.loads(bruto)
                return [InterpretacionMovimiento.model_validate(m) for m in datos["movimientos"]]
            except (json.JSONDecodeError, ValidationError, KeyError, TypeError):
                continue
        raise ErrorInterpretacion

    def responder(
        self,
        pregunta: str,
        contexto_usuario: str | None,
        fragmentos: list,
        historial: list[MensajeSalida],
    ) -> str:
        mensajes = [
            {
                "role": "system",
                "content": "Sos Qash, un asistente de finanzas personales. Respondé en español rioplatense, de forma breve.",
            }
        ]
        for mensaje in historial:
            rol = "user" if mensaje.rol == RolMensaje.USUARIO else "assistant"
            mensajes.append({"role": rol, "content": mensaje.contenido})

        contenido = f"{contexto_usuario}\n\n{pregunta}" if contexto_usuario else pregunta
        mensajes.append({"role": "user", "content": contenido})

        cliente = Groq(api_key=settings.groq_api_key)
        respuesta = cliente.chat.completions.create(model=settings.groq_modelo, messages=mensajes)
        return respuesta.choices[0].message.content


def obtener_proveedor_llm() -> ProveedorLLM:
    return ProveedorGroq()
