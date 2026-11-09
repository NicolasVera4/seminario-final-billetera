import json
from collections.abc import Callable
from datetime import date
from typing import Protocol

from groq import APIError, Groq, RateLimitError
from pydantic import ValidationError

from app.config import settings
from app.esquemas.chat import MensajeSalida
from app.esquemas.movimientos import (
    Catalogo,
    CategoriaMedioPagoFila,
    ColumnasDetectadas,
    Interpretacion,
    InterpretacionMovimiento,
)
from app.modelos.enums import RolMensaje, TipoComprobante

MENSAJE_LIMITE_TASA = "Estamos recibiendo muchas solicitudes en este momento. Probá de nuevo en unos minutos."


class ErrorInterpretacion(Exception):
    """El modelo no devolvió un JSON valido tras reintentar."""

    def __init__(self, limite_tasa: bool = False):
        super().__init__()
        self.limite_tasa = limite_tasa


class ProveedorLLM(Protocol):
    def clasificar_e_interpretar(
        self, texto: str, hoy: date, catalogo: Catalogo, historial: list[MensajeSalida] | None = None
    ) -> Interpretacion: ...

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

    def detectar_columnas(
        self, encabezados: list[str], filas_muestra: list[list[str]]
    ) -> ColumnasDetectadas: ...

    def categorizar_filas(
        self, descripciones: list[str], catalogo: Catalogo
    ) -> list[CategoriaMedioPagoFila]: ...


def _construir_historial_texto(historial: list[MensajeSalida] | None) -> str:
    if not historial:
        return ""
    turnos = [
        f"{'Usuario' if mensaje.rol == RolMensaje.USUARIO else 'Asistente'}: {mensaje.contenido}"
        for mensaje in historial
    ]
    return (
        "Conversación reciente, por si el mensaje del usuario es una respuesta de seguimiento a "
        "algo que el asistente preguntó (por ejemplo, un dato que faltaba):\n"
        + "\n".join(turnos)
        + "\n\n"
    )


def _construir_prompt_interpretacion(
    texto: str, hoy: date, catalogo: Catalogo, historial: list[MensajeSalida] | None = None
) -> str:
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
        f"{_construir_historial_texto(historial)}"
        f"Mensaje del usuario: {texto}"
    )


def _construir_prompt_extraccion(texto_documento: str, tipo: TipoComprobante, catalogo: Catalogo) -> str:
    categorias = ", ".join(catalogo.categorias)
    medios_pago = ", ".join(catalogo.medios_pago)
    if tipo == TipoComprobante.RESUMEN_TARJETA:
        instruccion = (
            "El documento es un resumen de tarjeta de credito con varias paginas. SOLO te interesan "
            "las lineas de la seccion de movimientos/consumos (compras hechas con la tarjeta, una "
            "por comercio). IMPORTANTE: ignorá por completo cualquier linea que sea saldo anterior, "
            "pagos realizados, impuesto, interes, cargo, percepcion o total a pagar — aunque tengan "
            "fecha y monto, NO son consumos y no van en la respuesta. Identificá CADA consumo real "
            "como un movimiento separado. Si un consumo esta en cuotas, completá cuota_numero y "
            "cuota_total, y usá como monto el valor de la cuota del periodo (no el total de las "
            "cuotas restantes)."
        )
    else:
        instruccion = (
            "El documento representa UN SOLO movimiento (el total del comprobante), no detalles "
            "línea por línea. Si el documento tiene varios montos (subtotales, parciales, "
            "descuentos, retenciones), usá el monto final neto — el que la persona efectivamente "
            "paga o cobra — nunca un subtotal ni un descuento ni un parcial intermedio."
        )
    return (
        "Sos un asistente que lee comprobantes de pago en español rioplatense.\n"
        f"Tipo de documento: {tipo.value}.\n"
        f"Categorías válidas: {categorias}.\n"
        f"Medios de pago válidos: {medios_pago}.\n"
        f"{instruccion}\n"
        "Respondé SOLO un JSON con esta forma exacta, sin texto adicional:\n"
        '{"movimientos": [{"monto": numero o null, "fecha": "AAAA-MM-DD" o null, '
        '"tipo": "INGRESO|EGRESO" o null, "medio_pago": "texto" o null, "descripcion": "texto" o null, '
        '"categoria": "texto" o null, "cuota_numero": numero o null, "cuota_total": numero o null}]}\n'
        f"Texto extraído del documento:\n{texto_documento}"
    )


def _construir_prompt_columnas(encabezados: list[str], filas_muestra: list[list[str]]) -> str:
    encabezados_texto = ", ".join(encabezados)
    filas_texto = "\n".join(", ".join(fila) for fila in filas_muestra)
    return (
        "Sos un asistente que identifica columnas en un extracto bancario importado desde CSV o Excel.\n"
        f"Encabezados: {encabezados_texto}.\n"
        f"Primeras filas de ejemplo:\n{filas_texto}\n"
        "Decime qué encabezado corresponde a la fecha, cuál al monto y cuál a la descripción del "
        "movimiento. Respondé SOLO un JSON con esta forma exacta, sin texto adicional:\n"
        '{"fecha": "<encabezado>" o null, "monto": "<encabezado>" o null, '
        '"descripcion": "<encabezado>" o null}'
    )


def _construir_prompt_categorizacion_filas(descripciones: list[str], catalogo: Catalogo) -> str:
    categorias = ", ".join(catalogo.categorias)
    medios_pago = ", ".join(catalogo.medios_pago)
    lineas = "\n".join(f"{indice + 1}. {descripcion}" for indice, descripcion in enumerate(descripciones))
    return (
        "Sos un asistente que categoriza movimientos de un extracto bancario importado desde CSV "
        "o Excel, en español rioplatense.\n"
        f"Categorías válidas: {categorias}.\n"
        f"Medios de pago válidos: {medios_pago}.\n"
        "Para cada línea de la lista de abajo, según su descripción, decime a qué categoría y "
        "medio de pago corresponde. Si no podés inferir alguno de los dos, dejalo en null — no "
        "inventes. Respondé SOLO un JSON con esta forma exacta, un ítem por línea en el mismo "
        "orden y la misma cantidad que la lista, sin texto adicional:\n"
        '{"filas": [{"categoria": "texto" o null, "medio_pago": "texto" o null}, ...]}\n'
        f"Líneas:\n{lineas}"
    )


class ProveedorGroq:
    """Implementacion real: llama a Groq en modo JSON y reintenta una vez si la respuesta no valida."""

    def __init__(
        self,
        cliente_json: Callable[[str], str] | None = None,
        cliente_chat: Callable[[list[dict]], str] | None = None,
    ):
        self._cliente_json = cliente_json or self._completar_con_groq
        self._cliente_chat = cliente_chat or self._completar_chat_con_groq

    def _completar_con_groq(self, prompt: str) -> str:
        def llamada(clave: str) -> str:
            cliente = Groq(api_key=clave)
            respuesta = cliente.chat.completions.create(
                model=settings.groq_modelo,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0,
                max_tokens=4096,
            )
            return respuesta.choices[0].message.content

        return self._llamar_rotando_api_key(llamada)

    def _completar_chat_con_groq(self, mensajes: list[dict]) -> str:
        def llamada(clave: str) -> str:
            cliente = Groq(api_key=clave)
            respuesta = cliente.chat.completions.create(
                model=settings.groq_modelo,
                messages=mensajes,
                temperature=0.3,
                max_tokens=1024,
            )
            return respuesta.choices[0].message.content

        return self._llamar_rotando_api_key(llamada)

    def _llamar_rotando_api_key(self, llamada: Callable[[str], str]) -> str:
        """Si GROQ_API_KEY se queda sin tokens (RateLimitError), reintenta con GROQ_API_KEY_2
        antes de darse por vencido — para no depender de una sola cuenta de Groq."""
        claves = [clave for clave in (settings.groq_api_key, settings.groq_api_key_2) if clave] or [None]
        for indice, clave in enumerate(claves):
            try:
                return llamada(clave)
            except RateLimitError:
                if indice == len(claves) - 1:
                    raise

    def clasificar_e_interpretar(
        self, texto: str, hoy: date, catalogo: Catalogo, historial: list[MensajeSalida] | None = None
    ) -> Interpretacion:
        prompt = _construir_prompt_interpretacion(texto, hoy, catalogo, historial)
        limite_tasa = False
        for _ in range(2):
            try:
                bruto = self._cliente_json(prompt)
                return Interpretacion.model_validate(json.loads(bruto))
            except RateLimitError:
                limite_tasa = True
            except (json.JSONDecodeError, ValidationError, APIError):
                continue
        raise ErrorInterpretacion(limite_tasa=limite_tasa)

    def extraer_movimientos(
        self, texto_documento: str, tipo: TipoComprobante, catalogo: Catalogo
    ) -> list[InterpretacionMovimiento]:
        prompt = _construir_prompt_extraccion(texto_documento, tipo, catalogo)
        limite_tasa = False
        for _ in range(2):
            try:
                bruto = self._cliente_json(prompt)
                datos = json.loads(bruto)
                return [InterpretacionMovimiento.model_validate(m) for m in datos["movimientos"]]
            except RateLimitError:
                limite_tasa = True
            except (json.JSONDecodeError, ValidationError, KeyError, TypeError, APIError):
                continue
        raise ErrorInterpretacion(limite_tasa=limite_tasa)

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
                "content": (
                    "Sos Qash, un asistente de finanzas personales. Respondé en español rioplatense, "
                    "de forma breve y natural, como si le hablaras directamente a la persona.\n"
                    "Formato: texto plano conversacional. PROHIBIDO usar el caracter asterisco (*) "
                    "en tu respuesta, para lo que sea — ni negrita, ni viñetas, ni ningún otro uso. "
                    "Tampoco uses numerales (#) ni guiones bajos (_) para dar formato. Si querés "
                    "remarcar algo importante, hacelo con las palabras, no con símbolos. Si "
                    "necesitás una lista, un ítem por renglón con un número y un punto, separados "
                    "por saltos de línea reales — nunca con asteriscos ni guiones como viñeta.\n"
                    "Vas a recibir 'Datos del usuario' y 'Fragmentos de documentación' como "
                    "contexto interno para vos. No repitas esas etiquetas ni esas secciones en tu "
                    "respuesta, y no cites los fragmentos entre comillas: usalos para fundamentar "
                    "un consejo propio, dicho con tus palabras. Si hay datos del usuario, arrancá "
                    "con una introducción breve que haga referencia a lo que ves en sus "
                    "movimientos (por ejemplo: 'Viendo tus últimos movimientos, noto que...') "
                    "antes de dar el consejo.\n"
                    "Respondé solo con los datos del usuario y los fragmentos de documentación que "
                    "se te pasan a continuación; si no alcanzan para responder con precisión, "
                    "decilo en vez de inventar información."
                ),
            }
        ]
        for mensaje in historial:
            rol = "user" if mensaje.rol == RolMensaje.USUARIO else "assistant"
            mensajes.append({"role": rol, "content": mensaje.contenido})

        partes_contexto = []
        if contexto_usuario:
            partes_contexto.append(f"Datos del usuario:\n{contexto_usuario}")
        if fragmentos:
            fragmentos_texto = "\n---\n".join(fragmentos)
            partes_contexto.append(f"Fragmentos de documentación:\n{fragmentos_texto}")
        contenido = f"{chr(10).join(partes_contexto)}\n\n{pregunta}" if partes_contexto else pregunta
        mensajes.append({"role": "user", "content": contenido})

        try:
            return self._cliente_chat(mensajes)
        except RateLimitError:
            return MENSAJE_LIMITE_TASA
        except APIError:
            return "No pudimos generar una respuesta en este momento. Probá de nuevo más tarde."

    def detectar_columnas(self, encabezados: list[str], filas_muestra: list[list[str]]) -> ColumnasDetectadas:
        prompt = _construir_prompt_columnas(encabezados, filas_muestra)
        limite_tasa = False
        for _ in range(2):
            try:
                bruto = self._cliente_json(prompt)
                return ColumnasDetectadas.model_validate(json.loads(bruto))
            except RateLimitError:
                limite_tasa = True
            except (json.JSONDecodeError, ValidationError, APIError):
                continue
        raise ErrorInterpretacion(limite_tasa=limite_tasa)

    def categorizar_filas(
        self, descripciones: list[str], catalogo: Catalogo
    ) -> list[CategoriaMedioPagoFila]:
        if not descripciones:
            return []
        prompt = _construir_prompt_categorizacion_filas(descripciones, catalogo)
        limite_tasa = False
        for _ in range(2):
            try:
                bruto = self._cliente_json(prompt)
                datos = json.loads(bruto)
                filas = [CategoriaMedioPagoFila.model_validate(f) for f in datos["filas"]]
                if len(filas) == len(descripciones):
                    return filas
            except RateLimitError:
                limite_tasa = True
            except (json.JSONDecodeError, ValidationError, KeyError, TypeError, APIError):
                continue
        raise ErrorInterpretacion(limite_tasa=limite_tasa)


def obtener_proveedor_llm() -> ProveedorLLM:
    return ProveedorGroq()
