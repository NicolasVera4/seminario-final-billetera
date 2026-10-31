from datetime import date, timedelta
from decimal import Decimal

from app.modelos.movimiento import Movimiento
from tests.ayudantes import auth, id_categoria, id_medio_pago, registrar_y_loguear

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
