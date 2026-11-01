"""Genera los fixtures binarios de la Fase 6 (HU-05). Correr una sola vez:

    python tests/fixtures/generar_fixtures.py

No se regeneran en cada test run: son archivos estáticos versionados en el repo.
"""

from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

DIRECTORIO = Path(__file__).parent

LINEAS_TICKET = [
    "SUPERMERCADO DIA",
    "Av. Siempre Viva 742",
    "Fecha: 31/10/2026",
    "Leche x2       $2.400,00",
    "Pan            $1.200,00",
    "Fideos         $1.400,00",
    "-------------------------",
    "TOTAL:        $15.000,00",
    "Pago con DEBITO",
]

LINEAS_FACTURA = [
    "EMPRESA DE SERVICIOS S.A.",
    "Factura de servicios - Luz",
    "Periodo: Octubre 2026",
    "Vencimiento: 05/11/2026",
    "Monto a pagar: $9.000,00",
]


def _dibujar_imagen_texto(lineas: list[str]) -> Image.Image:
    imagen = Image.new("RGB", (600, 400), color="white")
    dibujo = ImageDraw.Draw(imagen)
    y = 20
    for linea in lineas:
        dibujo.text((20, y), linea, fill="black")
        y += 30
    return imagen


def generar_ticket_supermercado() -> None:
    imagen = _dibujar_imagen_texto(LINEAS_TICKET)
    imagen.save(DIRECTORIO / "ticket_supermercado.png")


def generar_factura_con_texto() -> None:
    ruta = DIRECTORIO / "factura_servicio.pdf"
    lienzo = canvas.Canvas(str(ruta), pagesize=A4)
    y = 800
    for linea in LINEAS_FACTURA:
        lienzo.drawString(50, y, linea)
        y -= 20
    lienzo.save()


def generar_factura_escaneada() -> None:
    """PDF sin capa de texto: la misma factura, pero como imagen incrustada."""
    imagen = _dibujar_imagen_texto(LINEAS_FACTURA)
    buffer_imagen = BytesIO()
    imagen.save(buffer_imagen, format="PNG")
    buffer_imagen.seek(0)

    ruta = DIRECTORIO / "factura_escaneada.pdf"
    lienzo = canvas.Canvas(str(ruta), pagesize=A4)
    from reportlab.lib.utils import ImageReader

    lienzo.drawImage(ImageReader(imagen), 50, 500, width=400, height=267)
    lienzo.save()


def generar_archivo_no_admitido() -> None:
    (DIRECTORIO / "archivo_no_admitido.txt").write_text("esto no es un comprobante")


if __name__ == "__main__":
    generar_ticket_supermercado()
    generar_factura_con_texto()
    generar_factura_escaneada()
    generar_archivo_no_admitido()
    print("Fixtures generados en", DIRECTORIO)
