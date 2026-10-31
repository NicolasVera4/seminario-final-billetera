from datetime import date

from tests.ayudantes import auth, crear_movimiento, id_categoria, id_medio_pago, id_usuario, registrar_y_loguear


def _poblar(sesion_bd, usuario_id):
    crear_movimiento(
        sesion_bd, usuario_id, monto="15000", fecha=date(2026, 9, 27),
        descripcion="Compra en el súper", categoria="Supermercado", medio_pago="Débito",
    )
    crear_movimiento(
        sesion_bd, usuario_id, monto="28000", fecha=date(2026, 9, 27),
        descripcion="Cuota del gimnasio", categoria="Salud y deporte", medio_pago="Transferencia",
    )
    crear_movimiento(
        sesion_bd, usuario_id, monto="980000", fecha=date(2026, 9, 3), tipo="INGRESO",
        descripcion="Sueldo", categoria="Sueldo", medio_pago="Transferencia",
    )


def test_hu07_ca1_orden_descendente_con_todos_los_campos(cliente, sesion_bd):
    token = registrar_y_loguear(cliente)
    usuario_id = id_usuario(sesion_bd)
    _poblar(sesion_bd, usuario_id)

    respuesta = cliente.get("/api/movimientos", headers=auth(token))

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    fechas = [item["fecha"] for item in cuerpo["items"]]
    assert fechas == sorted(fechas, reverse=True)
    primero = cuerpo["items"][0]
    assert {"fecha", "descripcion", "categoria", "medio_pago", "origen", "monto"} <= primero.keys()


def test_hu07_ca2_filtro_por_rango_de_fechas(cliente, sesion_bd):
    token = registrar_y_loguear(cliente)
    usuario_id = id_usuario(sesion_bd)
    _poblar(sesion_bd, usuario_id)

    respuesta = cliente.get(
        "/api/movimientos", params={"desde": "2026-09-05", "hasta": "2026-09-30"}, headers=auth(token)
    )

    cuerpo = respuesta.json()
    assert cuerpo["total"] == 2
    assert all(item["fecha"] >= "2026-09-05" for item in cuerpo["items"])


def test_hu07_ca2_filtro_por_categoria(cliente, sesion_bd):
    token = registrar_y_loguear(cliente)
    usuario_id = id_usuario(sesion_bd)
    _poblar(sesion_bd, usuario_id)
    categoria_id = id_categoria(sesion_bd, "Sueldo")

    respuesta = cliente.get("/api/movimientos", params={"categoria_id": categoria_id}, headers=auth(token))

    cuerpo = respuesta.json()
    assert cuerpo["total"] == 1
    assert cuerpo["items"][0]["descripcion"] == "Sueldo"


def test_hu07_ca2_filtro_por_tipo(cliente, sesion_bd):
    token = registrar_y_loguear(cliente)
    usuario_id = id_usuario(sesion_bd)
    _poblar(sesion_bd, usuario_id)

    respuesta = cliente.get("/api/movimientos", params={"tipo": "INGRESO"}, headers=auth(token))

    cuerpo = respuesta.json()
    assert cuerpo["total"] == 1
    assert cuerpo["items"][0]["tipo"] == "INGRESO"


def test_hu07_ca2_filtro_por_medio_de_pago(cliente, sesion_bd):
    token = registrar_y_loguear(cliente)
    usuario_id = id_usuario(sesion_bd)
    _poblar(sesion_bd, usuario_id)
    medio_pago_id = id_medio_pago(sesion_bd, "Débito")

    respuesta = cliente.get("/api/movimientos", params={"medio_pago_id": medio_pago_id}, headers=auth(token))

    cuerpo = respuesta.json()
    assert cuerpo["total"] == 1
    assert cuerpo["items"][0]["medio_pago"] == "Débito"


def test_hu07_ca2_filtros_combinados_sin_coincidencias(cliente, sesion_bd):
    token = registrar_y_loguear(cliente)
    usuario_id = id_usuario(sesion_bd)
    _poblar(sesion_bd, usuario_id)

    respuesta = cliente.get(
        "/api/movimientos", params={"tipo": "INGRESO", "medio_pago_id": 999999}, headers=auth(token)
    )

    assert respuesta.json()["total"] == 0


def test_hu07_ca3_busqueda_por_texto(cliente, sesion_bd):
    token = registrar_y_loguear(cliente)
    usuario_id = id_usuario(sesion_bd)
    _poblar(sesion_bd, usuario_id)

    respuesta = cliente.get("/api/movimientos", params={"q": "gimnasio"}, headers=auth(token))

    cuerpo = respuesta.json()
    assert cuerpo["total"] == 1
    assert cuerpo["items"][0]["descripcion"] == "Cuota del gimnasio"


def test_hu07_ca3_busqueda_por_monto(cliente, sesion_bd):
    token = registrar_y_loguear(cliente)
    usuario_id = id_usuario(sesion_bd)
    _poblar(sesion_bd, usuario_id)

    respuesta = cliente.get("/api/movimientos", params={"q": "980000"}, headers=auth(token))

    cuerpo = respuesta.json()
    assert cuerpo["total"] == 1
    assert cuerpo["items"][0]["descripcion"] == "Sueldo"


def test_hu07_ca4_filtro_sin_resultados_informa_vacio(cliente, sesion_bd):
    token = registrar_y_loguear(cliente)
    usuario_id = id_usuario(sesion_bd)
    _poblar(sesion_bd, usuario_id)

    respuesta = cliente.get("/api/movimientos", params={"q": "inexistente-xyz"}, headers=auth(token))

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["items"] == []
    assert cuerpo["total"] == 0


def test_paginacion(cliente, sesion_bd):
    token = registrar_y_loguear(cliente)
    usuario_id = id_usuario(sesion_bd)
    for i in range(20):
        crear_movimiento(sesion_bd, usuario_id, descripcion=f"Movimiento {i}", fecha=date(2026, 9, 1 + i % 28))

    primera_pagina = cliente.get("/api/movimientos", params={"pagina": 1, "por_pagina": 15}, headers=auth(token))
    segunda_pagina = cliente.get("/api/movimientos", params={"pagina": 2, "por_pagina": 15}, headers=auth(token))

    assert primera_pagina.json()["total"] == 20
    assert len(primera_pagina.json()["items"]) == 15
    assert len(segunda_pagina.json()["items"]) == 5


def test_aislamiento_por_usuario(cliente, sesion_bd):
    token_a = registrar_y_loguear(cliente, nombre="Usuaria A", correo="a@mail.com")
    usuario_a_id = id_usuario(sesion_bd, "a@mail.com")
    crear_movimiento(sesion_bd, usuario_a_id, descripcion="Gasto de A")

    token_b = registrar_y_loguear(cliente, nombre="Usuario B", correo="b@mail.com")
    usuario_b_id = id_usuario(sesion_bd, "b@mail.com")
    crear_movimiento(sesion_bd, usuario_b_id, descripcion="Gasto de B")

    respuesta_a = cliente.get("/api/movimientos", headers=auth(token_a))
    respuesta_b = cliente.get("/api/movimientos", headers=auth(token_b))

    assert [i["descripcion"] for i in respuesta_a.json()["items"]] == ["Gasto de A"]
    assert [i["descripcion"] for i in respuesta_b.json()["items"]] == ["Gasto de B"]
