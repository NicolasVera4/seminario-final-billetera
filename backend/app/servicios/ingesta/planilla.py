import io
from datetime import date
from decimal import Decimal, InvalidOperation

import pandas as pd

from app.servicios.validacion import normalizar_descripcion

SINONIMOS: dict[str, list[str]] = {
    "fecha": ["fecha", "f. operacion", "f operacion", "date"],
    "monto": ["monto", "importe", "debito", "credito", "amount"],
    "descripcion": ["descripcion", "concepto", "detalle"],
}


def leer_filas(contenido: bytes, nombre_archivo: str) -> pd.DataFrame:
    if nombre_archivo.lower().endswith(".csv"):
        return pd.read_csv(io.BytesIO(contenido), dtype=str).fillna("")
    return pd.read_excel(io.BytesIO(contenido), dtype=str).fillna("")


def detectar_columnas_por_sinonimos(encabezados: list[str]) -> dict[str, str | None]:
    normalizados = {encabezado: normalizar_descripcion(encabezado) for encabezado in encabezados}
    resultado: dict[str, str | None] = {}
    for campo, sinonimos in SINONIMOS.items():
        resultado[campo] = next(
            (original for original, normalizado in normalizados.items() if normalizado in sinonimos),
            None,
        )
    return resultado


def parsear_fecha(valor: str) -> date | None:
    try:
        resultado = pd.to_datetime(valor, dayfirst=True, errors="coerce")
    except (ValueError, TypeError):
        return None
    if pd.isna(resultado):
        return None
    return resultado.date()


def parsear_monto(valor: str) -> Decimal | None:
    limpio = valor.strip().replace("$", "").replace(" ", "")
    if not limpio:
        return None
    if "," in limpio and "." in limpio:
        if limpio.rfind(",") > limpio.rfind("."):
            limpio = limpio.replace(".", "").replace(",", ".")
        else:
            limpio = limpio.replace(",", "")
    elif "," in limpio:
        limpio = limpio.replace(",", ".")
    try:
        return Decimal(limpio)
    except InvalidOperation:
        return None
