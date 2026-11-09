from datetime import date
from decimal import Decimal
from pathlib import Path

from app.esquemas.movimientos import InterpretacionMovimiento
from app.modelos.comprobante import Comprobante
from app.modelos.enums import TipoMovimiento
from app.modelos.movimiento import Movimiento
from tests.ayudantes import auth, id_categoria, id_medio_pago, registrar_y_loguear

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _movimientos_resumen():
    return [
        InterpretacionMovimiento(
            monto=Decimal("4599"), fecha=date(2026, 9, 21), tipo=TipoMovimiento.EGRESO,
            descripcion="Spotify", categoria="Suscripciones",
        ),
        InterpretacionMovimiento(
            monto=Decimal("32600"), fecha=date(2026, 9, 18), tipo=TipoMovimiento.EGRESO,
            descripcion="Restaurante La Nieta", categoria="Restaurantes",
        ),
        InterpretacionMovimiento(
            monto=Decimal("18300"), fecha=date(2026, 9, 12), tipo=TipoMovimiento.EGRESO,
            descripcion="Tienda deportiva zapatillas", categoria="Indumentaria",
            cuota_numero=2, cuota_total=6,
        ),
    ]


def _subir(cliente, token, nombre_archivo="resumen_tarjeta.pdf"):
    contenido = (FIXTURES / nombre_archivo).read_bytes()
    return cliente.post(
        "/api/archivos/resumen",
        files={"archivo": (nombre_archivo, contenido, "application/pdf")},
        headers=auth(token),
    )


def test_hu06_ca1_cada_consumo_es_un_movimiento_separado(cliente, proveedor_llm):
    token = registrar_y_loguear(cliente)
    proveedor_llm.respuesta_extraer = _movimientos_resumen()

    respuesta = _subir(cliente, token)

    assert respuesta.status_code == 200
    items = respuesta.json()["items"]
    assert len(items) == 3
    descripciones = {item["descripcion"] for item in items}
    assert descripciones == {"Spotify", "Restaurante La Nieta", "Tienda deportiva zapatillas"}


def test_hu06_ca2_se_leen_las_3_paginas(cliente, proveedor_llm):
    token = registrar_y_loguear(cliente)
    proveedor_llm.respuesta_extraer = _movimientos_resumen()

    respuesta = _subir(cliente, token)

    assert respuesta.json()["paginas_leidas"] == 3
    texto_recibido = proveedor_llm.llamadas_extraer[0]["texto_documento"]
    assert "Spotify" in texto_recibido
    assert "TOTAL DEL PERIODO" in texto_recibido


def test_hu06_ca3_consumo_en_cuotas_registra_numero_y_total(cliente, proveedor_llm):
    token = registrar_y_loguear(cliente)
    proveedor_llm.respuesta_extraer = _movimientos_resumen()

    respuesta = _subir(cliente, token)

    items = respuesta.json()["items"]
    zapatillas = next(i for i in items if i["descripcion"] == "Tienda deportiva zapatillas")
    assert zapatillas["cuota_numero"] == 2
    assert zapatillas["cuota_total"] == 6
    assert Decimal(zapatillas["monto"]) == Decimal("18300")


def test_todos_los_items_tienen_medio_de_pago_credito(cliente, proveedor_llm, sesion_bd):
    token = registrar_y_loguear(cliente)
    proveedor_llm.respuesta_extraer = _movimientos_resumen()

    respuesta = _subir(cliente, token)

    id_credito = id_medio_pago(sesion_bd, "Crédito")
    for item in respuesta.json()["items"]:
        assert item["medio_pago_id"] == id_credito


def test_hu06_ca5_item_con_fecha_y_monto_ya_registrado_se_marca_posible_duplicado(
    cliente, proveedor_llm, sesion_bd
):
    token = registrar_y_loguear(cliente)
    cliente.post(
        "/api/movimientos",
        json=[
            {
                "monto": "32600",
                "fecha": "2026-09-18",
                "tipo": "EGRESO",
                "descripcion": "Gasto en efectivo distinto",
                "categoria_id": id_categoria(sesion_bd, "Restaurantes"),
                "medio_pago_id": id_medio_pago(sesion_bd, "Efectivo"),
            }
        ],
        headers=auth(token),
    )
    proveedor_llm.respuesta_extraer = _movimientos_resumen()

    respuesta = _subir(cliente, token)

    items = respuesta.json()["items"]
    nieta = next(i for i in items if i["descripcion"] == "Restaurante La Nieta")
    spotify = next(i for i in items if i["descripcion"] == "Spotify")
    assert nieta["posible_duplicado"] is True
    assert spotify["posible_duplicado"] is False


def test_hu06_ca4_guardado_en_lote_solo_de_los_items_confirmados(cliente, proveedor_llm, sesion_bd):
    token = registrar_y_loguear(cliente)
    proveedor_llm.respuesta_extraer = _movimientos_resumen()
    subida = _subir(cliente, token)
    items = subida.json()["items"]
    spotify = next(i for i in items if i["descripcion"] == "Spotify")
    nieta = next(i for i in items if i["descripcion"] == "Restaurante La Nieta")

    lote = [
        {
            "monto": str(item["monto"]),
            "fecha": item["fecha"],
            "tipo": item["tipo"],
            "descripcion": item["descripcion"],
            "categoria_id": item["categoria_id"],
            "medio_pago_id": item["medio_pago_id"],
            "cuota_numero": item["cuota_numero"],
            "cuota_total": item["cuota_total"],
            "origen": "Resumen",
            "archivo_ref": subida.json()["archivo_ref"],
            "comprobante_tipo": subida.json()["comprobante_tipo"],
        }
        for item in (spotify, nieta)
    ]

    respuesta = cliente.post("/api/movimientos", json=lote, headers=auth(token))

    assert respuesta.status_code == 201
    assert len(respuesta.json()) == 2
    assert sesion_bd.query(Movimiento).filter_by(descripcion="Spotify").count() == 1
    assert sesion_bd.query(Movimiento).filter_by(descripcion="Tienda deportiva zapatillas").count() == 0


def test_comprobante_compartido_entre_items_del_mismo_lote(cliente, proveedor_llm, sesion_bd):
    token = registrar_y_loguear(cliente)
    proveedor_llm.respuesta_extraer = _movimientos_resumen()
    subida = _subir(cliente, token)
    items = subida.json()["items"]

    lote = [
        {
            "monto": str(item["monto"]),
            "fecha": item["fecha"],
            "tipo": item["tipo"],
            "descripcion": item["descripcion"],
            "categoria_id": item["categoria_id"],
            "medio_pago_id": item["medio_pago_id"],
            "cuota_numero": item["cuota_numero"],
            "cuota_total": item["cuota_total"],
            "origen": "Resumen",
            "archivo_ref": subida.json()["archivo_ref"],
            "comprobante_tipo": subida.json()["comprobante_tipo"],
        }
        for item in items
    ]

    respuesta = cliente.post("/api/movimientos", json=lote, headers=auth(token))

    assert respuesta.status_code == 201
    assert sesion_bd.query(Comprobante).count() == 1
    comprobante = sesion_bd.query(Comprobante).one()
    movimientos = sesion_bd.query(Movimiento).all()
    assert all(m.comprobante_id == comprobante.id for m in movimientos)


def test_resumen_escaneado_tambien_devuelve_items(cliente, proveedor_llm):
    token = registrar_y_loguear(cliente)
    proveedor_llm.respuesta_extraer = _movimientos_resumen()

    respuesta = _subir(cliente, token, nombre_archivo="resumen_tarjeta_escaneado.pdf")

    assert respuesta.status_code == 200
    assert len(respuesta.json()["items"]) == 3
    assert respuesta.json()["paginas_leidas"] == 3


def _generar_pdf_grande(paginas: int, lineas_por_pagina: int) -> bytes:
    from io import BytesIO

    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas

    buffer = BytesIO()
    lienzo = canvas.Canvas(buffer, pagesize=A4)
    for _ in range(paginas):
        y = 800
        for indice in range(lineas_por_pagina):
            lienzo.drawString(50, y, f"Consumo de prueba numero {indice} por $1.234,56 el 01/09/2026")
            y -= 15
            if y < 50:
                break
        lienzo.showPage()
    lienzo.save()
    return buffer.getvalue()


def test_hu06_resumen_grande_se_divide_en_varios_llamados_al_llm_y_los_une(cliente, proveedor_llm):
    token = registrar_y_loguear(cliente)
    proveedor_llm.respuesta_extraer = [_movimientos_resumen()[0]]
    contenido = _generar_pdf_grande(paginas=3, lineas_por_pagina=50)

    respuesta = cliente.post(
        "/api/archivos/resumen",
        files={"archivo": ("resumen_grande.pdf", contenido, "application/pdf")},
        headers=auth(token),
    )

    assert respuesta.status_code == 200
    assert len(proveedor_llm.llamadas_extraer) > 1
    assert len(respuesta.json()["items"]) == len(proveedor_llm.llamadas_extraer)
    for llamada in proveedor_llm.llamadas_extraer:
        assert len(llamada["texto_documento"]) <= 6000


def test_resumen_solo_admite_pdf(cliente, proveedor_llm):
    token = registrar_y_loguear(cliente)

    respuesta = cliente.post(
        "/api/archivos/resumen",
        files={"archivo": ("ticket.png", (FIXTURES / "ticket_supermercado.png").read_bytes(), "image/png")},
        headers=auth(token),
    )

    assert respuesta.status_code == 415
