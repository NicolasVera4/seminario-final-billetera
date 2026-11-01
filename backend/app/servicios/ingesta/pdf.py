import io

import pdfplumber
from pdf2image import convert_from_bytes

from app.servicios.ingesta.ocr import extraer_texto_imagen


def extraer_texto_pdf(contenido: bytes) -> str:
    with pdfplumber.open(io.BytesIO(contenido)) as pdf:
        texto = "\n".join(pagina.extract_text() or "" for pagina in pdf.pages)

    if texto.strip():
        return texto

    paginas = convert_from_bytes(contenido)
    textos_ocr = []
    for pagina in paginas:
        buffer = io.BytesIO()
        pagina.save(buffer, format="PNG")
        textos_ocr.append(extraer_texto_imagen(buffer.getvalue()))
    return "\n".join(textos_ocr)
