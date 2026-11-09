from datetime import date
from decimal import Decimal
from pathlib import Path

import pandas as pd

from app.esquemas.movimientos import InterpretacionMovimiento
from app.modelos.enums import TipoMovimiento
from tests.ayudantes import auth, registrar_y_loguear

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _subir(cliente, token, nombre_archivo, content_type, contenido=None, conversacion_id=None):
    contenido = contenido or (FIXTURES / nombre_archivo).read_bytes()
    datos = {"conversacion_id": conversacion_id} if conversacion_id is not None else {}
    return cliente.post(
        "/api/archivos/adjuntar",
        files={"archivo": (nombre_archivo, contenido, content_type)},
        data=datos,
        headers=auth(token),
    )


def test_una_imagen_se_procesa_como_comprobante(cliente, proveedor_llm):
    token = registrar_y_loguear(cliente)
    proveedor_llm.respuesta_extraer = [
        InterpretacionMovimiento(
            monto=Decimal("15000"), fecha=date(2026, 10, 31), tipo=TipoMovimiento.EGRESO,
            descripcion="Compra en el súper", categoria="Supermercado",
        )
    ]

    respuesta = _subir(cliente, token, "ticket_supermercado.png", "image/png")

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["modo"] == "COMPROBANTE"
    assert Decimal(cuerpo["borrador"]["monto"]) == Decimal("15000")


def test_un_pdf_de_una_sola_pagina_se_procesa_como_comprobante(cliente, proveedor_llm):
    token = registrar_y_loguear(cliente)
    proveedor_llm.respuesta_extraer = [
        InterpretacionMovimiento(
            monto=Decimal("15000"), fecha=date(2026, 10, 31), tipo=TipoMovimiento.EGRESO,
            descripcion="Compra en el súper", categoria="Supermercado",
        )
    ]

    respuesta = _subir(cliente, token, "factura_servicio.pdf", "application/pdf")

    assert respuesta.status_code == 200
    assert respuesta.json()["modo"] == "COMPROBANTE"


def test_un_pdf_de_varias_paginas_se_procesa_como_resumen_de_tarjeta(cliente, proveedor_llm):
    token = registrar_y_loguear(cliente)
    proveedor_llm.respuesta_extraer = [
        InterpretacionMovimiento(
            monto=Decimal("4599"), fecha=date(2026, 9, 21), tipo=TipoMovimiento.EGRESO,
            descripcion="Spotify", categoria="Suscripciones",
        ),
        InterpretacionMovimiento(
            monto=Decimal("32600"), fecha=date(2026, 9, 18), tipo=TipoMovimiento.EGRESO,
            descripcion="Restaurante La Nieta", categoria="Restaurantes",
        ),
    ]

    respuesta = _subir(cliente, token, "resumen_tarjeta.pdf", "application/pdf")

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["modo"] == "RESUMEN"
    assert cuerpo["paginas_leidas"] == 3
    assert len(cuerpo["items"]) == 2


def test_un_csv_se_procesa_como_extracto(cliente):
    token = registrar_y_loguear(cliente)
    contenido = pd.DataFrame(
        [
            {"Fecha": "01/09/2026", "Descripcion": "Supermercado", "Monto": "-15000"},
            {"Fecha": "02/09/2026", "Descripcion": "Farmacia", "Monto": "-3000"},
        ]
    ).to_csv(index=False).encode("utf-8")

    respuesta = _subir(cliente, token, "extracto.csv", "text/csv", contenido)

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["modo"] == "EXTRACTO"
    assert len(cuerpo["items"]) == 2


def test_formato_no_admitido_rechaza_con_415_mencionando_todos_los_formatos(cliente, proveedor_llm):
    token = registrar_y_loguear(cliente)

    respuesta = _subir(cliente, token, "notas.txt", "text/plain", b"hola")

    assert respuesta.status_code == 415
    detalle = respuesta.json()["detail"].lower()
    assert "pdf" in detalle
    assert "csv" in detalle or "excel" in detalle


def test_adjuntar_un_comprobante_persiste_un_mensaje_amigable_en_el_chat(cliente, proveedor_llm):
    """Bug reportado: el chat mostraba el nombre del archivo ("ticket_compra.png") en vez de un
    mensaje amigable, y además los datos desaparecían al navegar a otra conversación y volver."""
    token = registrar_y_loguear(cliente)
    proveedor_llm.respuesta_extraer = [
        InterpretacionMovimiento(
            monto=Decimal("15000"), fecha=date(2026, 10, 31), tipo=TipoMovimiento.EGRESO,
            descripcion="Compra en el súper", categoria="Supermercado",
        )
    ]

    respuesta = _subir(cliente, token, "ticket_supermercado.png", "image/png")

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["conversacion_id"] is not None
    assert cuerpo["mensaje_id"] is not None

    detalle = cliente.get(f"/api/chat/conversaciones/{cuerpo['conversacion_id']}", headers=auth(token))
    mensajes = detalle.json()
    assert len(mensajes) == 2
    assert mensajes[0]["rol"] == "USUARIO"
    assert mensajes[0]["contenido"] == "Cargaste una imagen: ticket_supermercado.png."
    assert mensajes[1]["rol"] == "ASISTENTE"
    assert mensajes[1]["id"] == cuerpo["mensaje_id"]
    assert mensajes[1]["movimiento"] is None  # todavía no se confirmó/guardó


def test_un_resumen_con_varios_consumos_persiste_un_mensaje_con_la_cantidad_encontrada(cliente, proveedor_llm):
    token = registrar_y_loguear(cliente)
    proveedor_llm.respuesta_extraer = [
        InterpretacionMovimiento(
            monto=Decimal("4599"), fecha=date(2026, 9, 21), tipo=TipoMovimiento.EGRESO,
            descripcion="Spotify", categoria="Suscripciones",
        ),
        InterpretacionMovimiento(
            monto=Decimal("32600"), fecha=date(2026, 9, 18), tipo=TipoMovimiento.EGRESO,
            descripcion="Restaurante La Nieta", categoria="Restaurantes",
        ),
    ]

    respuesta = _subir(cliente, token, "resumen_tarjeta.pdf", "application/pdf")

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["modo"] == "RESUMEN"
    detalle = cliente.get(f"/api/chat/conversaciones/{cuerpo['conversacion_id']}", headers=auth(token))
    mensajes = detalle.json()
    assert mensajes[0]["contenido"] == "Cargaste un archivo: resumen_tarjeta.pdf."
    assert "2" in mensajes[1]["contenido"]


def test_un_resumen_con_un_solo_consumo_se_trata_como_un_comprobante_puntual(cliente, proveedor_llm):
    """Bug reportado: un resumen con un solo consumo mandaba a la pantalla de revisión en lote y,
    al confirmarlo ahí, no quedaba mostrado como una tarjeta en el chat (a diferencia de un
    comprobante puntual). Con un solo consumo no hay nada que lotear: se trata igual que subir
    una imagen de un ticket."""
    token = registrar_y_loguear(cliente)
    proveedor_llm.respuesta_extraer = [
        InterpretacionMovimiento(
            monto=Decimal("4599"), fecha=date(2026, 9, 21), tipo=TipoMovimiento.EGRESO,
            descripcion="Spotify", categoria="Suscripciones",
        ),
    ]

    respuesta = _subir(cliente, token, "resumen_tarjeta.pdf", "application/pdf")

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["modo"] == "COMPROBANTE"
    assert Decimal(cuerpo["borrador"]["monto"]) == Decimal("4599")
    assert cuerpo["borrador"]["descripcion"] == "Spotify"

    detalle = cliente.get(f"/api/chat/conversaciones/{cuerpo['conversacion_id']}", headers=auth(token))
    mensajes = detalle.json()
    assert mensajes[1]["contenido"] == "Encontré este movimiento, revisalo y confirmalo."


def test_un_extracto_con_un_solo_movimiento_se_trata_como_un_comprobante_puntual(cliente):
    token = registrar_y_loguear(cliente)
    contenido = pd.DataFrame(
        [{"Fecha": "01/09/2026", "Descripcion": "Supermercado", "Monto": "-15000"}]
    ).to_csv(index=False).encode("utf-8")

    respuesta = _subir(cliente, token, "extracto.csv", "text/csv", contenido)

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["modo"] == "COMPROBANTE"

    detalle = cliente.get(f"/api/chat/conversaciones/{cuerpo['conversacion_id']}", headers=auth(token))
    mensajes = detalle.json()
    assert mensajes[0]["contenido"] == "Cargaste un archivo: extracto.csv."


def test_adjuntar_reutiliza_la_conversacion_pasada(cliente, proveedor_llm):
    token = registrar_y_loguear(cliente)
    proveedor_llm.respuesta_extraer = [
        InterpretacionMovimiento(
            monto=Decimal("15000"), fecha=date(2026, 10, 31), tipo=TipoMovimiento.EGRESO,
            descripcion="Compra en el súper", categoria="Supermercado",
        )
    ]
    primera = _subir(cliente, token, "ticket_supermercado.png", "image/png")
    conversacion_id = primera.json()["conversacion_id"]

    segunda = _subir(cliente, token, "ticket_supermercado.png", "image/png", conversacion_id=conversacion_id)

    assert segunda.json()["conversacion_id"] == conversacion_id
    detalle = cliente.get(f"/api/chat/conversaciones/{conversacion_id}", headers=auth(token))
    assert len(detalle.json()) == 4
