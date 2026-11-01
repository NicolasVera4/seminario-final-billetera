from pathlib import Path
from unittest.mock import patch

from app.servicios.ingesta.ocr import extraer_texto_imagen
from app.servicios.ingesta.pdf import extraer_texto_pdf

FIXTURES = Path(__file__).parent.parent / "fixtures"


def test_extraer_texto_imagen_de_un_ticket_devuelve_texto_no_vacio():
    contenido = (FIXTURES / "ticket_supermercado.png").read_bytes()

    texto = extraer_texto_imagen(contenido)

    assert texto.strip() != ""


def test_hu05_ca1_pdf_con_texto_no_pasa_por_ocr():
    contenido = (FIXTURES / "factura_servicio.pdf").read_bytes()

    with patch("app.servicios.ingesta.pdf.convert_from_bytes") as doble_conversion:
        texto = extraer_texto_pdf(contenido)

    doble_conversion.assert_not_called()
    assert "FACTURA" in texto.upper()


def test_hu05_ca2_pdf_escaneado_aplica_ocr():
    contenido = (FIXTURES / "factura_escaneada.pdf").read_bytes()

    texto = extraer_texto_pdf(contenido)

    assert texto.strip() != ""
