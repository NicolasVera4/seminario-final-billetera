import io

import pytesseract
from PIL import Image


def extraer_texto_imagen(contenido: bytes) -> str:
    imagen = Image.open(io.BytesIO(contenido))
    return pytesseract.image_to_string(imagen, lang="spa")
