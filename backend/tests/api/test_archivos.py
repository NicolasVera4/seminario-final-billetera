from datetime import date
from decimal import Decimal
from pathlib import Path

from app.esquemas.movimientos import InterpretacionMovimiento
from app.modelos.comprobante import Comprobante
from app.modelos.enums import TipoMovimiento
from app.modelos.movimiento import Movimiento
from app.proveedores.llm import ErrorInterpretacion
from tests.ayudantes import auth, id_categoria, id_medio_pago, registrar_y_loguear

FIXTURES = Path(__file__).parent.parent / "fixtures"

MOVIMIENTO_TICKET = InterpretacionMovimiento(
    monto=Decimal("15000"),
    fecha=date(2026, 10, 31),
    tipo=TipoMovimiento.EGRESO,
    medio_pago="Débito",
    descripcion="Compra en el súper",
    categoria="Supermercado",
)


def _subir(cliente, token, nombre_archivo, content_type, contenido=None):
    contenido = contenido or (FIXTURES / nombre_archivo).read_bytes()
    return cliente.post(
        "/api/archivos/comprobante",
        files={"archivo": (nombre_archivo, contenido, content_type)},
        headers=auth(token),
    )


def test_hu05_ca1_imagen_se_interpreta_como_un_unico_movimiento_para_confirmar(cliente, proveedor_llm):
    token = registrar_y_loguear(cliente)
    proveedor_llm.respuesta_extraer = [MOVIMIENTO_TICKET]

    respuesta = _subir(cliente, token, "ticket_supermercado.png", "image/png")

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert Decimal(cuerpo["borrador"]["monto"]) == Decimal("15000")
    assert cuerpo["borrador"]["descripcion"] == "Compra en el súper"
    assert cuerpo["archivo_ref"]
    assert len(proveedor_llm.llamadas_extraer) == 1


def test_hu05_ca1_pdf_con_texto_se_interpreta_como_un_unico_movimiento(cliente, proveedor_llm):
    token = registrar_y_loguear(cliente)
    proveedor_llm.respuesta_extraer = [MOVIMIENTO_TICKET]

    respuesta = _subir(cliente, token, "factura_servicio.pdf", "application/pdf")

    assert respuesta.status_code == 200
    assert Decimal(respuesta.json()["borrador"]["monto"]) == Decimal("15000")
    texto_recibido = proveedor_llm.llamadas_extraer[0]["texto_documento"]
    assert "FACTURA" in texto_recibido.upper()


def test_hu05_ca2_pdf_escaneado_tambien_genera_un_borrador(cliente, proveedor_llm):
    token = registrar_y_loguear(cliente)
    proveedor_llm.respuesta_extraer = [MOVIMIENTO_TICKET]

    respuesta = _subir(cliente, token, "factura_escaneada.pdf", "application/pdf")

    assert respuesta.status_code == 200
    assert respuesta.json()["borrador"] is not None
    assert proveedor_llm.llamadas_extraer[0]["texto_documento"].strip() != ""


def test_hu05_ca3_formato_no_admitido_se_rechaza_con_415(cliente, proveedor_llm):
    token = registrar_y_loguear(cliente)

    respuesta = _subir(cliente, token, "archivo_no_admitido.txt", "text/plain")

    assert respuesta.status_code == 415
    assert "jpg" in respuesta.json()["detail"].lower() or "pdf" in respuesta.json()["detail"].lower()


def test_rate_limit_de_groq_da_un_mensaje_distinto_al_de_no_pudimos_leer_el_comprobante(cliente, proveedor_llm):
    """Bug reportado: con un 429 de Groq (límite de tokens por día agotado), el mensaje decía
    "No pudimos leer el comprobante", como si el documento estuviera mal, cuando es temporal."""
    token = registrar_y_loguear(cliente)
    proveedor_llm.respuesta_extraer = ErrorInterpretacion(limite_tasa=True)

    respuesta = _subir(cliente, token, "ticket_supermercado.png", "image/png")

    assert respuesta.status_code == 422
    assert "muchas solicitudes" in respuesta.json()["detail"].lower()


def test_hu05_ca4_sin_monto_legible_no_registra_nada(cliente, proveedor_llm):
    token = registrar_y_loguear(cliente)
    proveedor_llm.respuesta_extraer = [
        InterpretacionMovimiento(monto=None, descripcion="algo ilegible")
    ]

    respuesta = _subir(cliente, token, "ticket_supermercado.png", "image/png")

    assert respuesta.status_code == 422
    assert "monto" in respuesta.json()["detail"].lower()


def test_tamano_maximo_rechaza_con_413(cliente, proveedor_llm):
    token = registrar_y_loguear(cliente)
    contenido_grande = b"0" * (10 * 1024 * 1024 + 1)

    respuesta = _subir(cliente, token, "grande.png", "image/png", contenido=contenido_grande)

    assert respuesta.status_code == 413


def test_confirmar_movimiento_con_archivo_crea_fila_en_comprobantes(cliente, proveedor_llm, sesion_bd):
    token = registrar_y_loguear(cliente)
    proveedor_llm.respuesta_extraer = [MOVIMIENTO_TICKET]

    subida = _subir(cliente, token, "ticket_supermercado.png", "image/png")
    cuerpo = subida.json()

    datos_confirmacion = {
        "monto": "15000",
        "fecha": "2026-10-31",
        "tipo": "EGRESO",
        "descripcion": "Compra en el súper",
        "categoria_id": id_categoria(sesion_bd, "Supermercado"),
        "medio_pago_id": id_medio_pago(sesion_bd, "Débito"),
        "origen": "Comprobante",
        "archivo_ref": cuerpo["archivo_ref"],
        "comprobante_tipo": cuerpo["comprobante_tipo"],
    }

    respuesta = cliente.post("/api/movimientos", json=[datos_confirmacion], headers=auth(token))

    assert respuesta.status_code == 201
    movimiento = sesion_bd.query(Movimiento).one()
    assert movimiento.comprobante_id is not None
    comprobante = sesion_bd.query(Comprobante).one()
    assert comprobante.id == movimiento.comprobante_id
    assert comprobante.ruta_archivo == cuerpo["archivo_ref"]
