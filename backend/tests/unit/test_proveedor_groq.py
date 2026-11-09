from datetime import date
from types import SimpleNamespace

import httpx
import pytest
from groq import APIConnectionError, RateLimitError

from app.esquemas.movimientos import Catalogo
from app.modelos.enums import RolMensaje, TipoComprobante
from app.proveedores.llm import (
    MENSAJE_LIMITE_TASA,
    ErrorInterpretacion,
    ProveedorGroq,
    _construir_prompt_extraccion,
)

JSON_VALIDO = (
    '{"intencion": "REGISTRO", "movimiento": {"monto": 1000, "fecha": "2026-10-31", '
    '"tipo": "EGRESO", "medio_pago": "Efectivo", "descripcion": "test", "categoria": "Otros"}, '
    '"faltantes": []}'
)


def _fabricar_cliente(respuestas):
    respuestas_iter = iter(respuestas)
    return lambda prompt: next(respuestas_iter)


def test_reintenta_una_vez_si_el_primer_json_es_invalido():
    cliente = _fabricar_cliente(["esto no es json", JSON_VALIDO])
    proveedor = ProveedorGroq(cliente_json=cliente)
    catalogo = Catalogo(categorias=["Otros"], medios_pago=["Efectivo"])

    resultado = proveedor.clasificar_e_interpretar("gasté 1000", date(2026, 10, 31), catalogo)

    assert resultado.intencion == "REGISTRO"
    assert resultado.movimiento.monto == 1000


def test_si_los_dos_intentos_fallan_levanta_error_interpretacion():
    cliente = _fabricar_cliente(["esto no es json", "esto tampoco"])
    proveedor = ProveedorGroq(cliente_json=cliente)
    catalogo = Catalogo(categorias=[], medios_pago=[])

    with pytest.raises(ErrorInterpretacion):
        proveedor.clasificar_e_interpretar("gasté 1000", date(2026, 10, 31), catalogo)


JSON_VALIDO_MOVIMIENTOS = (
    '{"movimientos": [{"monto": 15000, "fecha": "2026-10-31", "tipo": "EGRESO", '
    '"medio_pago": "Débito", "descripcion": "Compra en el súper", "categoria": "Supermercado"}]}'
)


def test_extraer_movimientos_reintenta_una_vez_si_el_primer_json_es_invalido():
    cliente = _fabricar_cliente(["esto no es json", JSON_VALIDO_MOVIMIENTOS])
    proveedor = ProveedorGroq(cliente_json=cliente)
    catalogo = Catalogo(categorias=["Supermercado"], medios_pago=["Débito"])

    resultado = proveedor.extraer_movimientos("texto del ticket", TipoComprobante.TICKET, catalogo)

    assert len(resultado) == 1
    assert resultado[0].monto == 15000


def test_extraer_movimientos_si_los_dos_intentos_fallan_levanta_error():
    cliente = _fabricar_cliente(["mal", "mal"])
    proveedor = ProveedorGroq(cliente_json=cliente)
    catalogo = Catalogo(categorias=[], medios_pago=[])

    with pytest.raises(ErrorInterpretacion):
        proveedor.extraer_movimientos("texto del ticket", TipoComprobante.TICKET, catalogo)


def _error_groq():
    return APIConnectionError(request=httpx.Request("POST", "https://api.groq.com"))


def _error_rate_limit():
    respuesta = httpx.Response(429, request=httpx.Request("POST", "https://api.groq.com"))
    return RateLimitError("rate limited", response=respuesta, body=None)


def test_extraer_movimientos_si_groq_falla_con_un_error_de_api_levanta_error_interpretacion():
    def cliente(_prompt):
        raise _error_groq()

    proveedor = ProveedorGroq(cliente_json=cliente)
    catalogo = Catalogo(categorias=[], medios_pago=[])

    with pytest.raises(ErrorInterpretacion):
        proveedor.extraer_movimientos("texto largo del resumen", TipoComprobante.RESUMEN_TARJETA, catalogo)


def test_clasificar_e_interpretar_si_groq_falla_con_un_error_de_api_levanta_error_interpretacion():
    def cliente(_prompt):
        raise _error_groq()

    proveedor = ProveedorGroq(cliente_json=cliente)
    catalogo = Catalogo(categorias=[], medios_pago=[])

    with pytest.raises(ErrorInterpretacion):
        proveedor.clasificar_e_interpretar("gasté 1000", date(2026, 10, 31), catalogo)


def test_clasificar_e_interpretar_incluye_el_historial_para_mensajes_de_seguimiento():
    prompts_capturados = []

    def cliente(prompt):
        prompts_capturados.append(prompt)
        return JSON_VALIDO

    proveedor = ProveedorGroq(cliente_json=cliente)
    catalogo = Catalogo(categorias=["Otros"], medios_pago=["Efectivo"])
    historial = [
        SimpleNamespace(rol=RolMensaje.USUARIO, contenido="Pagué el gimnasio"),
        SimpleNamespace(rol=RolMensaje.ASISTENTE, contenido="Me falta el monto. ¿Cuánto fue?"),
    ]

    proveedor.clasificar_e_interpretar("5000", date(2026, 10, 31), catalogo, historial)

    assert "Pagué el gimnasio" in prompts_capturados[0]
    assert "Me falta el monto" in prompts_capturados[0]


JSON_VALIDO_COLUMNAS = '{"fecha": "Día", "monto": "Guita", "descripcion": "Qué fue"}'


def test_detectar_columnas_reintenta_una_vez_si_el_primer_json_es_invalido():
    cliente = _fabricar_cliente(["esto no es json", JSON_VALIDO_COLUMNAS])
    proveedor = ProveedorGroq(cliente_json=cliente)

    resultado = proveedor.detectar_columnas(["Día", "Qué fue", "Guita"], [["03/09/2026", "Nafta", "-20000"]])

    assert resultado.fecha == "Día"
    assert resultado.monto == "Guita"
    assert resultado.descripcion == "Qué fue"


def test_detectar_columnas_si_los_dos_intentos_fallan_levanta_error():
    cliente = _fabricar_cliente(["mal", "mal"])
    proveedor = ProveedorGroq(cliente_json=cliente)

    with pytest.raises(ErrorInterpretacion):
        proveedor.detectar_columnas(["Día"], [["03/09/2026"]])


def test_hu10_ca2_responder_incluye_los_fragmentos_recuperados_en_el_mensaje_al_modelo():
    mensajes_capturados = {}

    def cliente_chat(mensajes):
        mensajes_capturados["mensajes"] = mensajes
        return "respuesta"

    proveedor = ProveedorGroq(cliente_chat=cliente_chat)

    proveedor.responder(
        "¿cómo ahorro más?",
        "Gastaste 5000 en supermercado.",
        ["Fragmento sobre presupuesto.", "Fragmento sobre ahorro."],
        [],
    )

    contenido_usuario = mensajes_capturados["mensajes"][-1]["content"]
    assert "Fragmento sobre presupuesto." in contenido_usuario
    assert "Fragmento sobre ahorro." in contenido_usuario
    assert "Gastaste 5000 en supermercado." in contenido_usuario


def test_prompt_de_resumen_de_tarjeta_excluye_impuestos_saldo_y_pagos():
    catalogo = Catalogo(categorias=["Otros"], medios_pago=["Crédito"])

    prompt = _construir_prompt_extraccion("texto del resumen", TipoComprobante.RESUMEN_TARJETA, catalogo)

    prompt_normalizado = prompt.lower()
    assert "impuesto" in prompt_normalizado
    assert "saldo anterior" in prompt_normalizado
    assert "pago" in prompt_normalizado


def test_prompt_de_ticket_o_factura_pide_el_monto_final_no_un_subtotal():
    """Bug reportado en el ensayo de la demo: con documentos que tienen varios montos (p. ej. un
    recibo de sueldo con bruto, descuentos y neto), el monto elegido variaba de una corrida a
    otra — a veces tomaba un número que no era ni el total ni el neto."""
    catalogo = Catalogo(categorias=["Otros"], medios_pago=["Efectivo"])

    prompt = _construir_prompt_extraccion("texto del comprobante", TipoComprobante.TICKET, catalogo)

    prompt_normalizado = prompt.lower()
    assert "neto" in prompt_normalizado
    assert "subtotal" in prompt_normalizado or "parcial" in prompt_normalizado


def test_completar_con_groq_pide_temperature_cero_y_max_tokens_para_ser_deterministico(monkeypatch):
    llamadas = {}

    class _CompletionsFalsas:
        def create(self, **kwargs):
            llamadas.update(kwargs)

            class _Mensaje:
                content = '{"movimientos": []}'

            class _Choice:
                message = _Mensaje()

            class _Respuesta:
                choices = [_Choice()]

            return _Respuesta()

    class _ChatFalso:
        completions = _CompletionsFalsas()

    class _GroqFalso:
        def __init__(self, api_key=None):
            self.chat = _ChatFalso()

    import app.proveedores.llm as modulo_llm

    monkeypatch.setattr(modulo_llm, "Groq", _GroqFalso)
    proveedor = ProveedorGroq()

    proveedor.extraer_movimientos("texto", TipoComprobante.TICKET, Catalogo(categorias=[], medios_pago=[]))

    assert llamadas["temperature"] == 0
    assert llamadas["max_tokens"] >= 2048


def test_hu10_ca1_ca2_responder_instruye_al_modelo_a_usar_solo_los_datos_y_fragmentos_provistos():
    mensajes_capturados = {}

    def cliente_chat(mensajes):
        mensajes_capturados["mensajes"] = mensajes
        return "respuesta"

    proveedor = ProveedorGroq(cliente_chat=cliente_chat)

    proveedor.responder("¿cómo ahorro más?", None, [], [])

    mensaje_sistema = mensajes_capturados["mensajes"][0]["content"].lower()
    assert "datos del usuario" in mensaje_sistema
    assert "fragmentos" in mensaje_sistema


def test_responder_instruye_a_no_filtrar_las_secciones_internas_ni_citar_fragmentos_textuales():
    """Bug reportado en el ensayo de la demo: la respuesta de asesoramiento le mostraba al
    usuario los encabezados internos "Datos del usuario" / "Fragmentos de documentación que
    aplican" y citaba los fragmentos recuperados entre comillas en vez de dar un consejo propio,
    y el formato venía en markdown (asteriscos) en vez de texto plano con saltos de línea reales."""
    mensajes_capturados = {}

    def cliente_chat(mensajes):
        mensajes_capturados["mensajes"] = mensajes
        return "respuesta"

    proveedor = ProveedorGroq(cliente_chat=cliente_chat)

    proveedor.responder("¿cómo ahorro más?", None, [], [])

    mensaje_sistema = mensajes_capturados["mensajes"][0]["content"].lower()
    assert "no" in mensaje_sistema and "repi" in mensaje_sistema
    assert "comilla" in mensaje_sistema
    assert "markdown" in mensaje_sistema or "asterisco" in mensaje_sistema


def test_responder_prohibe_explicitamente_el_asterisco_en_la_respuesta():
    """Reportado en el ensayo de la demo (09/11/2026): a pesar de la instrucción de formato ya
    existente, de vez en cuando igual respondía con **negrita** en markdown. Se refuerza la
    instrucción para que sea una prohibición explícita del caracter, no solo "evitá markdown"."""
    mensajes_capturados = {}

    def cliente_chat(mensajes):
        mensajes_capturados["mensajes"] = mensajes
        return "respuesta"

    proveedor = ProveedorGroq(cliente_chat=cliente_chat)

    proveedor.responder("¿cómo ahorro más?", None, [], [])

    mensaje_sistema = mensajes_capturados["mensajes"][0]["content"].lower()
    assert "prohibido" in mensaje_sistema
    assert "asterisco (*)" in mensaje_sistema


def test_completar_chat_con_groq_pide_una_temperatura_baja_para_respuestas_mas_consistentes(monkeypatch):
    llamadas = {}

    class _CompletionsFalsas:
        def create(self, **kwargs):
            llamadas.update(kwargs)

            class _Mensaje:
                content = "respuesta"

            class _Choice:
                message = _Mensaje()

            class _Respuesta:
                choices = [_Choice()]

            return _Respuesta()

    class _ChatFalso:
        completions = _CompletionsFalsas()

    class _GroqFalso:
        def __init__(self, api_key=None):
            self.chat = _ChatFalso()

    import app.proveedores.llm as modulo_llm

    monkeypatch.setattr(modulo_llm, "Groq", _GroqFalso)
    proveedor = ProveedorGroq()

    proveedor.responder("¿cómo ahorro más?", None, [], [])

    assert llamadas["temperature"] <= 0.5


def test_extraer_movimientos_si_groq_devuelve_rate_limit_marca_el_error_como_limite_de_tasa():
    """Bug reportado: cuando Groq devuelve 429 (límite diario o por minuto agotado), el mensaje
    que le llegaba al usuario era "No pudimos leer el comprobante..." — como si el documento
    estuviera mal, cuando en realidad es temporal. Se distingue para poder dar un mensaje
    distinto en ese caso."""

    def cliente(_prompt):
        raise _error_rate_limit()

    proveedor = ProveedorGroq(cliente_json=cliente)
    catalogo = Catalogo(categorias=[], medios_pago=[])

    with pytest.raises(ErrorInterpretacion) as excinfo:
        proveedor.extraer_movimientos("texto largo del resumen", TipoComprobante.RESUMEN_TARJETA, catalogo)
    assert excinfo.value.limite_tasa is True


def test_clasificar_e_interpretar_si_groq_devuelve_rate_limit_marca_el_error_como_limite_de_tasa():
    def cliente(_prompt):
        raise _error_rate_limit()

    proveedor = ProveedorGroq(cliente_json=cliente)
    catalogo = Catalogo(categorias=[], medios_pago=[])

    with pytest.raises(ErrorInterpretacion) as excinfo:
        proveedor.clasificar_e_interpretar("gasté 1000", date(2026, 10, 31), catalogo)
    assert excinfo.value.limite_tasa is True


def test_detectar_columnas_si_groq_devuelve_rate_limit_marca_el_error_como_limite_de_tasa():
    def cliente(_prompt):
        raise _error_rate_limit()

    proveedor = ProveedorGroq(cliente_json=cliente)

    with pytest.raises(ErrorInterpretacion) as excinfo:
        proveedor.detectar_columnas(["Fecha", "Monto"], [["01/09/2026", "-1000"]])
    assert excinfo.value.limite_tasa is True


def test_responder_si_groq_devuelve_rate_limit_responde_con_el_mensaje_de_limite_en_vez_de_tirar_error():
    def cliente_chat(_mensajes):
        raise _error_rate_limit()

    proveedor = ProveedorGroq(cliente_chat=cliente_chat)

    respuesta = proveedor.responder("¿cómo ahorro más?", None, [], [])

    assert respuesta == MENSAJE_LIMITE_TASA


def test_si_la_primera_api_key_tiene_rate_limit_rota_a_la_segunda(monkeypatch):
    """El usuario tiene dos cuentas de Groq (GROQ_API_KEY y GROQ_API_KEY_2) para no quedarse sin
    poder usar el asistente cuando se agota el límite diario de tokens de la primera."""
    claves_usadas = []

    class _CompletionsFalsas:
        def __init__(self, clave):
            self._clave = clave

        def create(self, **_kwargs):
            if self._clave == "clave-1":
                raise _error_rate_limit()

            class _Mensaje:
                content = '{"movimientos": []}'

            class _Choice:
                message = _Mensaje()

            class _Respuesta:
                choices = [_Choice()]

            return _Respuesta()

    class _ChatFalso:
        def __init__(self, clave):
            self.completions = _CompletionsFalsas(clave)

    class _GroqFalso:
        def __init__(self, api_key=None):
            claves_usadas.append(api_key)
            self.chat = _ChatFalso(api_key)

    import app.proveedores.llm as modulo_llm

    monkeypatch.setattr(modulo_llm, "Groq", _GroqFalso)
    monkeypatch.setattr(modulo_llm.settings, "groq_api_key", "clave-1")
    monkeypatch.setattr(modulo_llm.settings, "groq_api_key_2", "clave-2")
    proveedor = ProveedorGroq()

    resultado = proveedor.extraer_movimientos(
        "texto", TipoComprobante.TICKET, Catalogo(categorias=[], medios_pago=[])
    )

    assert resultado == []
    assert claves_usadas == ["clave-1", "clave-2"]


def test_si_las_dos_api_keys_tienen_rate_limit_igual_marca_el_error_como_limite_de_tasa(monkeypatch):
    class _CompletionsFalsas:
        def create(self, **_kwargs):
            raise _error_rate_limit()

    class _ChatFalso:
        completions = _CompletionsFalsas()

    class _GroqFalso:
        def __init__(self, api_key=None):
            self.chat = _ChatFalso()

    import app.proveedores.llm as modulo_llm

    monkeypatch.setattr(modulo_llm, "Groq", _GroqFalso)
    monkeypatch.setattr(modulo_llm.settings, "groq_api_key", "clave-1")
    monkeypatch.setattr(modulo_llm.settings, "groq_api_key_2", "clave-2")
    proveedor = ProveedorGroq()

    with pytest.raises(ErrorInterpretacion) as excinfo:
        proveedor.extraer_movimientos(
            "texto", TipoComprobante.TICKET, Catalogo(categorias=[], medios_pago=[])
        )
    assert excinfo.value.limite_tasa is True


def test_sin_segunda_api_key_configurada_no_rota_y_se_comporta_como_antes(monkeypatch):
    intentos = []

    class _CompletionsFalsas:
        def create(self, **_kwargs):
            intentos.append(1)
            raise _error_rate_limit()

    class _ChatFalso:
        completions = _CompletionsFalsas()

    class _GroqFalso:
        def __init__(self, api_key=None):
            self.chat = _ChatFalso()

    import app.proveedores.llm as modulo_llm

    monkeypatch.setattr(modulo_llm, "Groq", _GroqFalso)
    monkeypatch.setattr(modulo_llm.settings, "groq_api_key", "clave-1")
    monkeypatch.setattr(modulo_llm.settings, "groq_api_key_2", None)
    proveedor = ProveedorGroq()

    with pytest.raises(ErrorInterpretacion):
        proveedor.extraer_movimientos(
            "texto", TipoComprobante.TICKET, Catalogo(categorias=[], medios_pago=[])
        )
    # extraer_movimientos ya reintentaba 2 veces por su cuenta antes de este cambio; sin una
    # segunda api key no hay rotación posible, así que el total de intentos no cambia.
    assert len(intentos) == 2


def test_responder_tambien_rota_de_api_key_si_la_primera_tiene_rate_limit(monkeypatch):
    class _CompletionsFalsas:
        def __init__(self, clave):
            self._clave = clave

        def create(self, **_kwargs):
            if self._clave == "clave-1":
                raise _error_rate_limit()

            class _Mensaje:
                content = "respuesta con la segunda cuenta"

            class _Choice:
                message = _Mensaje()

            class _Respuesta:
                choices = [_Choice()]

            return _Respuesta()

    class _ChatFalso:
        def __init__(self, clave):
            self.completions = _CompletionsFalsas(clave)

    class _GroqFalso:
        def __init__(self, api_key=None):
            self.chat = _ChatFalso(api_key)

    import app.proveedores.llm as modulo_llm

    monkeypatch.setattr(modulo_llm, "Groq", _GroqFalso)
    monkeypatch.setattr(modulo_llm.settings, "groq_api_key", "clave-1")
    monkeypatch.setattr(modulo_llm.settings, "groq_api_key_2", "clave-2")
    proveedor = ProveedorGroq()

    respuesta = proveedor.responder("¿cómo ahorro más?", None, [], [])

    assert respuesta == "respuesta con la segunda cuenta"


def test_categorizar_filas_le_pide_al_modelo_categoria_y_medio_de_pago_por_descripcion():
    cliente = _fabricar_cliente(
        [
            '{"filas": [{"categoria": "Supermercado", "medio_pago": "Débito"}, '
            '{"categoria": "Restaurantes", "medio_pago": null}]}'
        ]
    )
    proveedor = ProveedorGroq(cliente_json=cliente)
    catalogo = Catalogo(categorias=["Supermercado", "Restaurantes"], medios_pago=["Débito"])

    resultado = proveedor.categorizar_filas(
        ["Compra con tarjeta de débito - Supermercado Disco", "Pago con QR - Bar La Esquina"], catalogo
    )

    assert len(resultado) == 2
    assert resultado[0].categoria == "Supermercado"
    assert resultado[0].medio_pago == "Débito"
    assert resultado[1].categoria == "Restaurantes"
    assert resultado[1].medio_pago is None


def test_categorizar_filas_con_lista_vacia_no_llama_al_modelo():
    def cliente(_prompt):
        raise AssertionError("no debería llamarse al modelo con una lista vacía")

    proveedor = ProveedorGroq(cliente_json=cliente)
    catalogo = Catalogo(categorias=[], medios_pago=[])

    assert proveedor.categorizar_filas([], catalogo) == []


def test_categorizar_filas_si_la_cantidad_no_coincide_reintenta_y_despues_tira_error():
    cliente = _fabricar_cliente(
        [
            '{"filas": [{"categoria": "Supermercado", "medio_pago": "Débito"}]}',
            '{"filas": [{"categoria": "Supermercado", "medio_pago": "Débito"}]}',
        ]
    )
    proveedor = ProveedorGroq(cliente_json=cliente)
    catalogo = Catalogo(categorias=["Supermercado"], medios_pago=["Débito"])

    with pytest.raises(ErrorInterpretacion):
        proveedor.categorizar_filas(["Línea 1", "Línea 2"], catalogo)
