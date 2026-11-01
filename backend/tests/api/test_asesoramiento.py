from datetime import date

from app.esquemas.movimientos import Interpretacion
from app.modelos.mensaje import Mensaje
from tests.ayudantes import auth, crear_movimiento, id_usuario, promover_a_administrador, registrar_y_loguear

DISCLAIMER = "Esto es orientativo y no reemplaza el asesoramiento de un profesional."


def _consulta_datos():
    return Interpretacion(intencion="CONSULTA_DATOS", movimiento=None, faltantes=[])


def _consulta_asesoramiento():
    return Interpretacion(intencion="CONSULTA_ASESORAMIENTO", movimiento=None, faltantes=[])


def _cargar_documento_admin(cliente, sesion_bd, titulo="Tips de ahorro", contenido=b"a" * 1700):
    registrar_y_loguear(cliente, nombre="Admin", correo="admin@mail.com")
    promover_a_administrador(sesion_bd, "admin@mail.com")
    token_admin = cliente.post(
        "/api/auth/login", json={"correo": "admin@mail.com", "contrasena": "contrasena123"}
    ).json()["access_token"]
    return cliente.post(
        "/api/admin/documentos",
        params={"titulo": titulo},
        files={"archivo": ("tips.txt", contenido, "text/plain")},
        headers=auth(token_admin),
    )


def test_hu10_ca1_pregunta_sobre_gastos_responde_con_datos_del_historial(cliente, proveedor_llm, sesion_bd):
    token = registrar_y_loguear(cliente)
    usuario_id = id_usuario(sesion_bd)
    crear_movimiento(sesion_bd, usuario_id, monto="5000", fecha=date(2026, 10, 15), categoria="Supermercado")
    proveedor_llm.respuesta_clasificar = _consulta_datos()
    proveedor_llm.respuesta_responder = "Gastaste 5000 en supermercado."

    respuesta = cliente.post(
        "/api/chat/mensajes", json={"texto": "¿cuánto gasté en supermercado?"}, headers=auth(token)
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["mensaje"]["contenido"] == "Gastaste 5000 en supermercado."
    llamada = proveedor_llm.llamadas_responder[0]
    assert llamada["contexto_usuario"] is not None
    assert llamada["fragmentos"] == []


def test_hu10_ca2_asesoramiento_combina_movimientos_y_documentacion(cliente, proveedor_llm, embedder, sesion_bd):
    subida = _cargar_documento_admin(cliente, sesion_bd)
    assert subida.status_code == 201

    token = registrar_y_loguear(cliente, nombre="Usuaria A", correo="a@mail.com")
    usuario_id = id_usuario(sesion_bd, "a@mail.com")
    crear_movimiento(sesion_bd, usuario_id, monto="5000", fecha=date(2026, 10, 15))
    proveedor_llm.respuesta_clasificar = _consulta_asesoramiento()
    proveedor_llm.respuesta_responder = "Para ahorrar más, separá un 10% apenas cobrás."

    respuesta = cliente.post(
        "/api/chat/mensajes", json={"texto": "¿cómo puedo ahorrar más?"}, headers=auth(token)
    )

    assert respuesta.status_code == 200
    llamada = proveedor_llm.llamadas_responder[0]
    assert llamada["contexto_usuario"] is not None
    assert len(llamada["fragmentos"]) > 0


def test_hu10_ca3_fuentes_se_guardan_en_mensajes_fuentes(cliente, proveedor_llm, embedder, sesion_bd):
    _cargar_documento_admin(cliente, sesion_bd)
    token = registrar_y_loguear(cliente, nombre="Usuaria A", correo="a@mail.com")
    usuario_id = id_usuario(sesion_bd, "a@mail.com")
    crear_movimiento(sesion_bd, usuario_id, monto="5000", fecha=date(2026, 10, 15))
    proveedor_llm.respuesta_clasificar = _consulta_asesoramiento()

    respuesta = cliente.post(
        "/api/chat/mensajes", json={"texto": "¿cómo puedo ahorrar más?"}, headers=auth(token)
    )

    fuentes = respuesta.json()["mensaje"]["fuentes"]
    assert any(f["tipo"] == "documento" for f in fuentes)
    assert any(f["tipo"] == "movimientos" for f in fuentes)

    mensaje_id = respuesta.json()["mensaje"]["id"]
    mensaje_db = sesion_bd.get(Mensaje, mensaje_id)
    assert mensaje_db.fuentes is not None
    assert len(mensaje_db.fuentes) == len(fuentes)


def test_hu10_ca4_usuario_sin_movimientos_responde_solo_con_documentacion(cliente, proveedor_llm, embedder, sesion_bd):
    _cargar_documento_admin(cliente, sesion_bd)
    token = registrar_y_loguear(cliente, nombre="Usuaria A", correo="a@mail.com")
    proveedor_llm.respuesta_clasificar = _consulta_asesoramiento()
    proveedor_llm.respuesta_responder = "Una idea general es ahorrar el 10%."

    respuesta = cliente.post(
        "/api/chat/mensajes", json={"texto": "¿cómo puedo ahorrar más?"}, headers=auth(token)
    )

    llamada = proveedor_llm.llamadas_responder[0]
    assert llamada["contexto_usuario"] is None
    assert len(llamada["fragmentos"]) > 0
    assert "no tenés movimientos" in respuesta.json()["mensaje"]["contenido"].lower()


def test_disclaimer_presente_en_respuestas_de_asesoramiento(cliente, proveedor_llm, embedder, sesion_bd):
    _cargar_documento_admin(cliente, sesion_bd)
    token = registrar_y_loguear(cliente)
    proveedor_llm.respuesta_clasificar = _consulta_asesoramiento()
    proveedor_llm.respuesta_responder = "Separá un 10% de tus ingresos."

    respuesta = cliente.post(
        "/api/chat/mensajes", json={"texto": "¿cómo ahorro más?"}, headers=auth(token)
    )

    assert DISCLAIMER in respuesta.json()["mensaje"]["contenido"]


def test_disclaimer_ausente_en_respuestas_de_consulta_de_datos(cliente, proveedor_llm, sesion_bd):
    token = registrar_y_loguear(cliente)
    proveedor_llm.respuesta_clasificar = _consulta_datos()
    proveedor_llm.respuesta_responder = "Gastaste 5000."

    respuesta = cliente.post("/api/chat/mensajes", json={"texto": "¿cuánto gasté?"}, headers=auth(token))

    assert DISCLAIMER not in respuesta.json()["mensaje"]["contenido"]


def test_hu10_ca5_retomar_una_conversacion_de_asesoramiento(cliente, proveedor_llm, sesion_bd):
    token = registrar_y_loguear(cliente)
    proveedor_llm.respuesta_clasificar = _consulta_datos()

    primera = cliente.post("/api/chat/mensajes", json={"texto": "¿cuánto gasté?"}, headers=auth(token))
    conversacion_id = primera.json()["conversacion_id"]

    detalle = cliente.get(f"/api/chat/conversaciones/{conversacion_id}", headers=auth(token))

    assert detalle.status_code == 200
    assert len(detalle.json()) == 2
