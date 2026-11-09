import io
from decimal import Decimal

import pandas as pd

from app.esquemas.movimientos import CategoriaMedioPagoFila, ColumnasDetectadas
from app.proveedores.llm import ErrorInterpretacion
from tests.ayudantes import auth, crear_movimiento, id_usuario, registrar_y_loguear


def _csv(filas: list[dict]) -> bytes:
    return pd.DataFrame(filas).to_csv(index=False).encode("utf-8")


def _xlsx(filas: list[dict]) -> bytes:
    buffer = io.BytesIO()
    pd.DataFrame(filas).to_excel(buffer, index=False)
    return buffer.getvalue()


def _subir(cliente, token, nombre_archivo, content_type, contenido):
    return cliente.post(
        "/api/archivos/extracto",
        files={"archivo": (nombre_archivo, contenido, content_type)},
        headers=auth(token),
    )


def test_hu14_ca1_detecta_columnas_por_sinonimos_formato_a(cliente):
    token = registrar_y_loguear(cliente)
    contenido = _csv(
        [
            {"Fecha": "01/09/2026", "Descripcion": "Supermercado", "Monto": "-15000"},
            {"Fecha": "05/09/2026", "Descripcion": "Sueldo", "Monto": "500000"},
        ]
    )

    respuesta = _subir(cliente, token, "extracto.csv", "text/csv", contenido)

    assert respuesta.status_code == 200
    items = respuesta.json()["items"]
    assert len(items) == 2
    assert Decimal(items[0]["monto"]) == Decimal("15000")
    assert items[0]["tipo"] == "EGRESO"
    assert items[0]["descripcion"] == "Supermercado"
    assert Decimal(items[1]["monto"]) == Decimal("500000")
    assert items[1]["tipo"] == "INGRESO"


def test_hu14_ca1_detecta_columnas_por_sinonimos_formato_b_en_excel(cliente):
    token = registrar_y_loguear(cliente)
    contenido = _xlsx(
        [
            {"F. Operacion": "02/09/2026", "Detalle": "Farmacia", "Importe": "-8000"},
        ]
    )

    respuesta = _subir(
        cliente,
        token,
        "extracto.xlsx",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        contenido,
    )

    assert respuesta.status_code == 200
    items = respuesta.json()["items"]
    assert len(items) == 1
    assert items[0]["descripcion"] == "Farmacia"
    assert Decimal(items[0]["monto"]) == Decimal("8000")


def test_hu14_ca1_encabezados_no_reconocidos_usa_el_fallback_del_llm(cliente, proveedor_llm):
    token = registrar_y_loguear(cliente)
    proveedor_llm.respuesta_detectar_columnas = ColumnasDetectadas(
        fecha="Día", monto="Guita", descripcion="Qué fue"
    )
    contenido = _csv([{"Día": "03/09/2026", "Qué fue": "Nafta", "Guita": "-20000"}])

    respuesta = _subir(cliente, token, "extracto.csv", "text/csv", contenido)

    assert respuesta.status_code == 200
    items = respuesta.json()["items"]
    assert len(items) == 1
    assert items[0]["descripcion"] == "Nafta"
    assert len(proveedor_llm.llamadas_detectar_columnas) == 1
    assert proveedor_llm.llamadas_detectar_columnas[0]["encabezados"] == ["Día", "Qué fue", "Guita"]


def test_hu14_columnas_no_detectables_ni_por_el_llm_devuelve_422(cliente, proveedor_llm):
    token = registrar_y_loguear(cliente)
    proveedor_llm.respuesta_detectar_columnas = ColumnasDetectadas(fecha=None, monto=None, descripcion=None)
    contenido = _csv([{"Día": "03/09/2026", "Qué fue": "Nafta", "Guita": "-20000"}])

    respuesta = _subir(cliente, token, "extracto.csv", "text/csv", contenido)

    assert respuesta.status_code == 422


def test_hu14_ca2_filas_sin_fecha_o_monto_validos_se_descartan_y_se_informan(cliente):
    token = registrar_y_loguear(cliente)
    contenido = _csv(
        [
            {"Fecha": "01/09/2026", "Descripcion": "Supermercado", "Monto": "-15000"},
            {"Fecha": "no es una fecha", "Descripcion": "Fila rota", "Monto": "-5000"},
            {"Fecha": "03/09/2026", "Descripcion": "Monto roto", "Monto": "no es un monto"},
        ]
    )

    respuesta = _subir(cliente, token, "extracto.csv", "text/csv", contenido)

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert len(cuerpo["items"]) == 1
    assert cuerpo["filas_descartadas"] == 2


def test_hu14_ca3_fila_igual_a_un_movimiento_existente_se_marca_como_posible_duplicado(cliente, sesion_bd):
    token = registrar_y_loguear(cliente)
    usuario_id = id_usuario(sesion_bd)
    from datetime import date

    crear_movimiento(sesion_bd, usuario_id, monto="15000", fecha=date(2026, 9, 1))
    contenido = _csv([{"Fecha": "01/09/2026", "Descripcion": "Supermercado", "Monto": "-15000"}])

    respuesta = _subir(cliente, token, "extracto.csv", "text/csv", contenido)

    assert respuesta.status_code == 200
    assert respuesta.json()["items"][0]["posible_duplicado"] is True


def test_hu14_ca4_los_items_son_borradores_y_no_se_guarda_nada_solo(cliente, sesion_bd):
    token = registrar_y_loguear(cliente)
    usuario_id = id_usuario(sesion_bd)
    contenido = _csv([{"Fecha": "01/09/2026", "Descripcion": "Supermercado", "Monto": "-15000"}])

    respuesta = _subir(cliente, token, "extracto.csv", "text/csv", contenido)

    assert respuesta.status_code == 200
    assert respuesta.json()["items"][0]["categoria_id"] is None
    assert "CATEGORIA_INVALIDA" in respuesta.json()["items"][0]["errores"]
    assert "MEDIO_PAGO_FALTANTE" in respuesta.json()["items"][0]["errores"]

    historial = cliente.get("/api/movimientos", headers=auth(token))
    assert historial.json()["total"] == 0


def test_el_extracto_tambien_se_categoriza_via_llm_igual_que_un_comprobante(cliente, proveedor_llm):
    """Bug reportado: al importar un extracto, categoría y medio de pago quedaban siempre en
    null — nunca se le pedía nada al LLM, a diferencia de un comprobante o un resumen de tarjeta,
    que sí lo hacen. El usuario tenía que completar las 18 filas a mano."""
    token = registrar_y_loguear(cliente)
    proveedor_llm.respuesta_categorizar_filas = [
        CategoriaMedioPagoFila(categoria="Supermercado", medio_pago="Débito"),
        CategoriaMedioPagoFila(categoria="Restaurantes", medio_pago="Crédito"),
    ]
    contenido = _csv(
        [
            {"Fecha": "01/09/2026", "Descripcion": "Supermercado Disco", "Monto": "-15000"},
            {"Fecha": "02/09/2026", "Descripcion": "Bar La Esquina", "Monto": "-8000"},
        ]
    )

    respuesta = _subir(cliente, token, "extracto.csv", "text/csv", contenido)

    assert respuesta.status_code == 200
    items = respuesta.json()["items"]
    assert items[0]["categoria_id"] is not None
    assert items[0]["errores"] == []
    assert items[1]["categoria_id"] is not None
    assert len(proveedor_llm.llamadas_categorizar_filas) == 1
    assert proveedor_llm.llamadas_categorizar_filas[0]["descripciones"] == [
        "Supermercado Disco",
        "Bar La Esquina",
    ]


def test_extracto_con_categoria_fuera_del_catalogo_queda_como_sugerencia_para_elegir(cliente, proveedor_llm):
    token = registrar_y_loguear(cliente)
    proveedor_llm.respuesta_categorizar_filas = [CategoriaMedioPagoFila(categoria="Gimnasio", medio_pago=None)]
    contenido = _csv([{"Fecha": "01/09/2026", "Descripcion": "Cuota gimnasio", "Monto": "-20000"}])

    respuesta = _subir(cliente, token, "extracto.csv", "text/csv", contenido)

    assert respuesta.status_code == 200
    item = respuesta.json()["items"][0]
    assert item["categoria_id"] is None
    assert item["categoria_sugerida"] == "Gimnasio"
    assert "CATEGORIA_INVALIDA" in item["errores"]


def test_si_la_categorizacion_del_extracto_falla_igual_se_importa_sin_categorizar(cliente, proveedor_llm):
    """Categorizar es una ayuda, no un requisito: si el LLM falla (rate limit, lo que sea), el
    extracto se sigue importando — el usuario completa a mano, como antes de este cambio."""
    token = registrar_y_loguear(cliente)
    proveedor_llm.respuesta_categorizar_filas = ErrorInterpretacion()
    contenido = _csv([{"Fecha": "01/09/2026", "Descripcion": "Supermercado", "Monto": "-15000"}])

    respuesta = _subir(cliente, token, "extracto.csv", "text/csv", contenido)

    assert respuesta.status_code == 200
    assert respuesta.json()["items"][0]["categoria_id"] is None


def test_formato_no_admitido_devuelve_415(cliente):
    token = registrar_y_loguear(cliente)

    respuesta = _subir(cliente, token, "extracto.txt", "text/plain", b"no es un extracto")

    assert respuesta.status_code == 415
