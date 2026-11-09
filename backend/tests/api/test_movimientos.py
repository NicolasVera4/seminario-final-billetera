from datetime import date, timedelta
from decimal import Decimal

from app.esquemas.movimientos import Interpretacion
from app.modelos.movimiento import Movimiento
from tests.ayudantes import auth, id_categoria, id_medio_pago, registrar_y_loguear


def _crear_conversacion(cliente, proveedor_llm, token) -> int:
    proveedor_llm.respuesta_clasificar = Interpretacion(intencion="CONSULTA_DATOS", movimiento=None, faltantes=[])
    return cliente.post("/api/chat/mensajes", json={"texto": "hola"}, headers=auth(token)).json()[
        "conversacion_id"
    ]


HOY = date(2026, 10, 31)


def _movimiento_valido(sesion_bd, **overrides):
    base = {
        "monto": "15000",
        "fecha": HOY.isoformat(),
        "tipo": "EGRESO",
        "descripcion": "Compra en el súper",
        "categoria_id": id_categoria(sesion_bd, "Supermercado"),
        "medio_pago_id": id_medio_pago(sesion_bd, "Débito"),
    }
    base.update(overrides)
    return base


def test_get_catalogos_devuelve_categorias_medios_pago_y_origenes(cliente):
    token = registrar_y_loguear(cliente)

    respuesta = cliente.get("/api/catalogos", headers=auth(token))

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    nombres_categorias = {c["nombre"] for c in cuerpo["categorias"]}
    assert "Supermercado" in nombres_categorias
    assert any(m["nombre"] == "Efectivo" for m in cuerpo["medios_pago"])
    assert any(o["nombre"] == "Texto" for o in cuerpo["origenes"])


def test_hu04_ca1_monto_invalido_se_senala_en_validar(cliente, sesion_bd):
    token = registrar_y_loguear(cliente)
    datos = _movimiento_valido(sesion_bd, monto="0")

    respuesta = cliente.post("/api/movimientos/validar", json=datos, headers=auth(token))

    assert respuesta.status_code == 200
    assert "MONTO_INVALIDO" in respuesta.json()["errores"]


def test_hu04_ca1_fecha_futura_se_senala_en_validar(cliente, sesion_bd):
    token = registrar_y_loguear(cliente)
    manana = (HOY + timedelta(days=1)).isoformat()
    datos = _movimiento_valido(sesion_bd, fecha=manana)

    respuesta = cliente.post("/api/movimientos/validar", json=datos, headers=auth(token))

    assert respuesta.status_code == 200
    assert "FECHA_FUTURA" in respuesta.json()["errores"]


def test_hu04_ca2_categoria_fuera_de_catalogo_se_senala(cliente, sesion_bd):
    token = registrar_y_loguear(cliente)
    datos = _movimiento_valido(sesion_bd, categoria_id=999999)

    respuesta = cliente.post("/api/movimientos/validar", json=datos, headers=auth(token))

    assert respuesta.status_code == 200
    assert "CATEGORIA_INVALIDA" in respuesta.json()["errores"]


def test_hu04_ca3_sin_medio_de_pago_se_senala(cliente, sesion_bd):
    token = registrar_y_loguear(cliente)
    datos = _movimiento_valido(sesion_bd, medio_pago_id=None)

    respuesta = cliente.post("/api/movimientos/validar", json=datos, headers=auth(token))

    assert respuesta.status_code == 200
    assert "MEDIO_PAGO_FALTANTE" in respuesta.json()["errores"]


def test_hu04_ca4_mismo_dia_monto_y_descripcion_avisa_posible_duplicado(cliente, sesion_bd):
    token = registrar_y_loguear(cliente)
    datos = _movimiento_valido(sesion_bd)
    guardado = cliente.post("/api/movimientos", json=[datos], headers=auth(token))
    assert guardado.status_code == 201

    respuesta = cliente.post("/api/movimientos/validar", json=datos, headers=auth(token))

    assert respuesta.status_code == 200
    assert respuesta.json()["errores"] == []
    assert "POSIBLE_DUPLICADO" in respuesta.json()["advertencias"]


def test_hu04_ca5_movimiento_valido_confirmado_se_guarda(cliente, sesion_bd):
    token = registrar_y_loguear(cliente)
    datos = _movimiento_valido(sesion_bd)

    respuesta = cliente.post("/api/movimientos", json=[datos], headers=auth(token))

    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert len(cuerpo) == 1
    assert Decimal(str(cuerpo[0]["monto"])) == Decimal("15000")
    guardados = sesion_bd.query(Movimiento).all()
    assert len(guardados) == 1


def test_revalida_al_guardar_aunque_el_cliente_mande_categoria_inexistente(cliente, sesion_bd):
    token = registrar_y_loguear(cliente)
    datos = _movimiento_valido(sesion_bd, categoria_id=999999)

    respuesta = cliente.post("/api/movimientos", json=[datos], headers=auth(token))

    assert respuesta.status_code == 422
    assert sesion_bd.query(Movimiento).count() == 0


def test_lote_con_un_item_invalido_no_guarda_nada(cliente, sesion_bd):
    token = registrar_y_loguear(cliente)
    valido = _movimiento_valido(sesion_bd, descripcion="Uno")
    invalido = _movimiento_valido(sesion_bd, descripcion="Dos", monto="0")

    respuesta = cliente.post("/api/movimientos", json=[valido, invalido], headers=auth(token))

    assert respuesta.status_code == 422
    assert sesion_bd.query(Movimiento).count() == 0


def test_movimiento_guardado_queda_asociado_al_usuario(cliente, sesion_bd):
    token = registrar_y_loguear(cliente)
    datos = _movimiento_valido(sesion_bd)

    cliente.post("/api/movimientos", json=[datos], headers=auth(token))

    guardado = sesion_bd.query(Movimiento).one()
    respuesta_yo = cliente.get("/api/auth/yo", headers=auth(token))
    assert guardado.usuario_id == respuesta_yo.json()["id"]


def test_guardar_un_lote_de_resumen_deja_un_mensaje_de_cierre_en_la_conversacion(
    cliente, proveedor_llm, sesion_bd
):
    """Bug reportado: "Encontré 5 consumos en tu resumen de tarjeta, revisalos y confirmalos."
    quedaba como si nada se hubiera confirmado todavía, aunque el usuario ya los hubiera guardado
    desde la pantalla de revisión en lote. Se agrega un mensaje de cierre que confirma lo que
    efectivamente se guardó."""
    token = registrar_y_loguear(cliente)
    conversacion_id = _crear_conversacion(cliente, proveedor_llm, token)
    primero = _movimiento_valido(
        sesion_bd, descripcion="Spotify", origen="Resumen", conversacion_id=conversacion_id
    )
    segundo = _movimiento_valido(
        sesion_bd, descripcion="Restaurante", origen="Resumen", conversacion_id=conversacion_id
    )

    respuesta = cliente.post("/api/movimientos", json=[primero, segundo], headers=auth(token))

    assert respuesta.status_code == 201
    detalle = cliente.get(f"/api/chat/conversaciones/{conversacion_id}", headers=auth(token))
    mensajes = detalle.json()
    assert mensajes[-1]["rol"] == "ASISTENTE"
    assert mensajes[-1]["contenido"] == "Se cargaron 2 movimientos de tu resumen de tarjeta."


def test_guardar_un_lote_de_extracto_deja_un_mensaje_de_cierre_mencionando_el_extracto(
    cliente, proveedor_llm, sesion_bd
):
    token = registrar_y_loguear(cliente)
    conversacion_id = _crear_conversacion(cliente, proveedor_llm, token)
    datos = _movimiento_valido(sesion_bd, origen="Extracto", conversacion_id=conversacion_id)

    cliente.post("/api/movimientos", json=[datos], headers=auth(token))

    detalle = cliente.get(f"/api/chat/conversaciones/{conversacion_id}", headers=auth(token))
    mensajes = detalle.json()
    assert mensajes[-1]["contenido"] == "Se cargó 1 movimiento de tu extracto."


def test_guardar_un_movimiento_de_texto_no_agrega_mensaje_de_cierre(cliente, proveedor_llm, sesion_bd):
    """El mensaje de cierre es solo para la pantalla de revisión en lote (resumen/extracto): un
    movimiento confirmado desde el chat de texto o un comprobante puntual ya muestra su propio
    estado "Guardado" en la tarjeta, no necesita un mensaje aparte."""
    token = registrar_y_loguear(cliente)
    conversacion_id = _crear_conversacion(cliente, proveedor_llm, token)
    datos = _movimiento_valido(sesion_bd, conversacion_id=conversacion_id)

    cliente.post("/api/movimientos", json=[datos], headers=auth(token))

    detalle = cliente.get(f"/api/chat/conversaciones/{conversacion_id}", headers=auth(token))
    mensajes = detalle.json()
    assert len(mensajes) == 2  # solo "hola" + la respuesta del asistente, nada más
