from datetime import date
from decimal import Decimal

from app.esquemas.movimientos import Interpretacion, InterpretacionMovimiento
from app.modelos.conversacion import Conversacion
from app.modelos.enums import TipoMovimiento
from app.modelos.mensaje import Mensaje
from app.proveedores.llm import ErrorInterpretacion
from tests.ayudantes import CORREO_DEFECTO, NOMBRE_DEFECTO, auth, registrar_y_loguear


def _interpretacion_consulta():
    return Interpretacion(intencion="CONSULTA_DATOS", movimiento=None, faltantes=[])


def _enviar(cliente, token, texto, conversacion_id=None):
    cuerpo = {"texto": texto}
    if conversacion_id is not None:
        cuerpo["conversacion_id"] = conversacion_id
    return cliente.post("/api/chat/mensajes", json=cuerpo, headers=auth(token))


def test_hu03_ca1_identifica_los_campos_y_los_muestra_para_confirmar(cliente, proveedor_llm):
    token = registrar_y_loguear(cliente)
    proveedor_llm.respuesta_clasificar = Interpretacion(
        intencion="REGISTRO",
        movimiento=InterpretacionMovimiento(
            monto=Decimal("15000"),
            fecha=date(2026, 10, 31),
            tipo=TipoMovimiento.EGRESO,
            medio_pago="Débito",
            descripcion="Compra en el súper",
            categoria="Supermercado",
        ),
        faltantes=[],
    )

    respuesta = _enviar(cliente, token, "gasté 15000 en el súper con débito")

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    borrador = cuerpo["borrador"]
    assert Decimal(str(borrador["monto"])) == Decimal("15000")
    assert borrador["fecha"] == "2026-10-31"
    assert borrador["tipo"] == "EGRESO"
    assert borrador["descripcion"] == "Compra en el súper"
    assert borrador["categoria_id"] is not None
    assert borrador["categoria_sugerida"] is None
    assert borrador["medio_pago_id"] is not None
    assert cuerpo["mensaje"]["rol"] == "ASISTENTE"


def test_hu03_ca2_mensaje_sin_fecha_toma_la_fecha_del_dia(cliente, proveedor_llm, reloj):
    token = registrar_y_loguear(cliente)
    proveedor_llm.respuesta_clasificar = Interpretacion(
        intencion="REGISTRO",
        movimiento=InterpretacionMovimiento(
            monto=Decimal("500"),
            fecha=None,
            tipo=TipoMovimiento.EGRESO,
            medio_pago="Efectivo",
            descripcion="Café",
            categoria="Restaurantes",
        ),
        faltantes=[],
    )

    respuesta = _enviar(cliente, token, "pagué un café con efectivo")

    assert respuesta.status_code == 200
    assert respuesta.json()["borrador"]["fecha"] == reloj.ahora().date().isoformat()


def test_hu03_ca3_mensaje_sin_monto_pide_el_monto_y_no_genera_borrador(cliente, proveedor_llm):
    token = registrar_y_loguear(cliente)
    proveedor_llm.respuesta_clasificar = Interpretacion(
        intencion="REGISTRO",
        movimiento=InterpretacionMovimiento(
            monto=None,
            fecha=date(2026, 10, 31),
            tipo=TipoMovimiento.EGRESO,
            medio_pago=None,
            descripcion="Compra",
            categoria=None,
        ),
        faltantes=["monto"],
    )

    respuesta = _enviar(cliente, token, "compré cosas")

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["borrador"] is None
    assert "monto" in cuerpo["mensaje"]["contenido"].lower()


def test_hu03_ca4_mensaje_que_no_describe_un_movimiento_responde_como_consulta(cliente, proveedor_llm):
    token = registrar_y_loguear(cliente)
    proveedor_llm.respuesta_clasificar = _interpretacion_consulta()
    proveedor_llm.respuesta_responder = "No tenés movimientos registrados todavía."

    respuesta = _enviar(cliente, token, "¿cuánto gasté este mes?")

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["borrador"] is None
    assert cuerpo["mensaje"]["contenido"] == "No tenés movimientos registrados todavía."


def test_prompt_no_incluye_nombre_ni_correo(cliente, proveedor_llm):
    token = registrar_y_loguear(cliente)
    proveedor_llm.respuesta_clasificar = _interpretacion_consulta()

    _enviar(cliente, token, "hola")

    assert len(proveedor_llm.llamadas_clasificar) == 1
    texto_enviado = proveedor_llm.llamadas_clasificar[0]["texto"]
    assert NOMBRE_DEFECTO not in texto_enviado
    assert CORREO_DEFECTO not in texto_enviado


def test_json_invalido_responde_con_mensaje_amable(cliente, proveedor_llm):
    token = registrar_y_loguear(cliente)
    proveedor_llm.respuesta_clasificar = ErrorInterpretacion()

    respuesta = _enviar(cliente, token, "gasté 1000")

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["borrador"] is None
    assert cuerpo["mensaje"]["contenido"]


def test_persistencia_de_conversacion_y_mensajes(cliente, proveedor_llm, sesion_bd):
    token = registrar_y_loguear(cliente)
    proveedor_llm.respuesta_clasificar = _interpretacion_consulta()

    respuesta = _enviar(cliente, token, "hola")
    conversacion_id = respuesta.json()["conversacion_id"]

    conversacion = sesion_bd.get(Conversacion, conversacion_id)
    assert conversacion is not None
    mensajes = sesion_bd.query(Mensaje).filter_by(conversacion_id=conversacion_id).all()
    assert len(mensajes) == 2
    assert {m.rol.value for m in mensajes} == {"USUARIO", "ASISTENTE"}


def test_reutiliza_la_conversacion_si_se_pasa_conversacion_id(cliente, proveedor_llm):
    token = registrar_y_loguear(cliente)
    proveedor_llm.respuesta_clasificar = _interpretacion_consulta()

    primera = _enviar(cliente, token, "hola")
    conversacion_id = primera.json()["conversacion_id"]

    segunda = _enviar(cliente, token, "otra pregunta", conversacion_id=conversacion_id)

    assert segunda.json()["conversacion_id"] == conversacion_id


def test_aislamiento_no_se_puede_usar_conversacion_de_otro_usuario(cliente, proveedor_llm):
    token_a = registrar_y_loguear(cliente, nombre="Usuaria A", correo="a@mail.com")
    proveedor_llm.respuesta_clasificar = _interpretacion_consulta()
    respuesta = _enviar(cliente, token_a, "hola")
    conversacion_id = respuesta.json()["conversacion_id"]

    token_b = registrar_y_loguear(cliente, nombre="Usuario B", correo="b@mail.com")
    intento = _enviar(cliente, token_b, "hola", conversacion_id=conversacion_id)

    assert intento.status_code == 404


def test_listar_conversaciones_devuelve_las_del_usuario(cliente, proveedor_llm):
    token = registrar_y_loguear(cliente)
    proveedor_llm.respuesta_clasificar = _interpretacion_consulta()
    _enviar(cliente, token, "hola")

    respuesta = cliente.get("/api/chat/conversaciones", headers=auth(token))

    assert respuesta.status_code == 200
    assert len(respuesta.json()) == 1


def test_obtener_conversacion_devuelve_sus_mensajes_en_orden(cliente, proveedor_llm):
    token = registrar_y_loguear(cliente)
    proveedor_llm.respuesta_clasificar = _interpretacion_consulta()
    respuesta = _enviar(cliente, token, "hola")
    conversacion_id = respuesta.json()["conversacion_id"]

    detalle = cliente.get(f"/api/chat/conversaciones/{conversacion_id}", headers=auth(token))

    assert detalle.status_code == 200
    mensajes = detalle.json()
    assert len(mensajes) == 2
    assert mensajes[0]["rol"] == "USUARIO"
    assert mensajes[1]["rol"] == "ASISTENTE"


def test_obtener_conversacion_inexistente_devuelve_404(cliente):
    token = registrar_y_loguear(cliente)

    respuesta = cliente.get("/api/chat/conversaciones/99999", headers=auth(token))

    assert respuesta.status_code == 404
