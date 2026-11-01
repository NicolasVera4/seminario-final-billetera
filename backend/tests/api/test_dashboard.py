from datetime import date

from tests.ayudantes import auth, crear_movimiento, id_usuario, registrar_y_loguear


def test_hu08_ca1_totales_del_mes(cliente, sesion_bd):
    token = registrar_y_loguear(cliente)
    usuario_id = id_usuario(sesion_bd)
    crear_movimiento(sesion_bd, usuario_id, monto="980000", fecha=date(2026, 9, 3), tipo="INGRESO")
    crear_movimiento(sesion_bd, usuario_id, monto="15000", fecha=date(2026, 9, 27))
    crear_movimiento(sesion_bd, usuario_id, monto="28000", fecha=date(2026, 9, 27))

    respuesta = cliente.get("/api/dashboard", params={"mes": "2026-09"}, headers=auth(token))

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["ingresos"]["monto"] == "980000.00"
    assert cuerpo["egresos"]["monto"] == "43000.00"
    assert cuerpo["saldo"] == "937000.00"
    assert cuerpo["hay_movimientos"] is True


def test_hu08_ca2_evolucion_mensual(cliente, sesion_bd):
    token = registrar_y_loguear(cliente)
    usuario_id = id_usuario(sesion_bd)
    crear_movimiento(sesion_bd, usuario_id, monto="10000", fecha=date(2026, 7, 10))
    crear_movimiento(sesion_bd, usuario_id, monto="15000", fecha=date(2026, 9, 27))

    respuesta = cliente.get("/api/dashboard", params={"mes": "2026-09"}, headers=auth(token))

    meses = [(p["anio"], p["mes"]) for p in respuesta.json()["evolucion"]]
    assert (2026, 9) in meses
    assert (2026, 7) in meses
    assert len(meses) == 6


def test_hu08_ca3_distribucion_por_categoria(cliente, sesion_bd):
    token = registrar_y_loguear(cliente)
    usuario_id = id_usuario(sesion_bd)
    crear_movimiento(sesion_bd, usuario_id, monto="20000", fecha=date(2026, 9, 5), categoria="Supermercado")
    crear_movimiento(sesion_bd, usuario_id, monto="10000", fecha=date(2026, 9, 5), categoria="Transporte")

    respuesta = cliente.get("/api/dashboard", params={"mes": "2026-09"}, headers=auth(token))

    distribucion = respuesta.json()["distribucion_categorias"]
    assert distribucion[0]["categoria"] == "Supermercado"
    assert distribucion[0]["porcentaje"] == 67


def test_hu08_ca4_sin_movimientos_indica_estado_vacio(cliente):
    token = registrar_y_loguear(cliente)

    respuesta = cliente.get("/api/dashboard", params={"mes": "2026-09"}, headers=auth(token))

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["hay_movimientos"] is False
    assert cuerpo["distribucion_categorias"] == []


def test_hu09_ca4_recalcula_tras_guardar_un_movimiento(cliente, sesion_bd):
    token = registrar_y_loguear(cliente)
    usuario_id = id_usuario(sesion_bd)
    for mes in (6, 7, 8):
        crear_movimiento(
            sesion_bd, usuario_id, monto="60000", fecha=date(2026, mes, 15), categoria="Restaurantes"
        )

    antes = cliente.get("/api/dashboard", params={"mes": "2026-09"}, headers=auth(token))
    assert antes.json()["alertas"] == []

    crear_movimiento(sesion_bd, usuario_id, monto="86400", fecha=date(2026, 9, 10), categoria="Restaurantes")

    despues = cliente.get("/api/dashboard", params={"mes": "2026-09"}, headers=auth(token))
    assert len(despues.json()["alertas"]) == 1
    assert despues.json()["alertas"][0]["categoria"] == "Restaurantes"


def test_mes_por_defecto_es_el_actual(cliente, reloj):
    token = registrar_y_loguear(cliente)

    respuesta = cliente.get("/api/dashboard", headers=auth(token))

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["anio"] == reloj.ahora().year
    assert cuerpo["mes"] == reloj.ahora().month


def test_aislamiento_por_usuario(cliente, sesion_bd):
    token_a = registrar_y_loguear(cliente, nombre="Usuaria A", correo="a@mail.com")
    usuario_a_id = id_usuario(sesion_bd, "a@mail.com")
    crear_movimiento(sesion_bd, usuario_a_id, monto="50000", fecha=date(2026, 9, 5))

    token_b = registrar_y_loguear(cliente, nombre="Usuario B", correo="b@mail.com")

    respuesta_b = cliente.get("/api/dashboard", params={"mes": "2026-09"}, headers=auth(token_b))

    assert respuesta_b.json()["hay_movimientos"] is False
