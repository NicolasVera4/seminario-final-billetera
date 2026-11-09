import io

import pdfplumber
from pdf2image import convert_from_bytes

from app.servicios.ingesta.ocr import extraer_texto_imagen


def extraer_texto_pdf(contenido: bytes) -> str:
    return "\n".join(extraer_texto_pdf_por_pagina(contenido))


def contar_paginas_pdf(contenido: bytes) -> int:
    with pdfplumber.open(io.BytesIO(contenido)) as pdf:
        return len(pdf.pages)


def extraer_texto_pdf_por_pagina(contenido: bytes) -> list[str]:
    with pdfplumber.open(io.BytesIO(contenido)) as pdf:
        paginas_texto = [pagina.extract_text() or "" for pagina in pdf.pages]

    if any(texto.strip() for texto in paginas_texto):
        return paginas_texto

    paginas = convert_from_bytes(contenido)
    textos_ocr = []
    for pagina in paginas:
        buffer = io.BytesIO()
        pagina.save(buffer, format="PNG")
        textos_ocr.append(extraer_texto_imagen(buffer.getvalue()))
    return textos_ocr
