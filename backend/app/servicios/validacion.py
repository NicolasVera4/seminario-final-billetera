import unicodedata
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal


@dataclass
class ResultadoValidacion:
    errores: list[str] = field(default_factory=list)
    advertencias: list[str] = field(default_factory=list)


def validar_campos(
    monto: Decimal | None,
    fecha: date,
    categoria_id: int | None,
    medio_pago_id: int | None,
    hoy: date,
    categorias_validas: set[int],
    medios_pago_validos: set[int],
) -> list[str]:
    errores = []
    if monto is None or monto <= 0:
        errores.append("MONTO_INVALIDO")
    if fecha > hoy:
        errores.append("FECHA_FUTURA")
    if categoria_id is None or categoria_id not in categorias_validas:
        errores.append("CATEGORIA_INVALIDA")
    if medio_pago_id is None or medio_pago_id not in medios_pago_validos:
        errores.append("MEDIO_PAGO_FALTANTE")
    return errores


def normalizar_descripcion(texto: str) -> str:
    sin_tildes = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")
    return " ".join(sin_tildes.lower().split())


def es_posible_duplicado(
    fecha: date,
    monto: Decimal,
    descripcion: str,
    existentes: list[tuple[date, Decimal, str]],
) -> bool:
    descripcion_normalizada = normalizar_descripcion(descripcion)
    return any(
        f == fecha and m == monto and normalizar_descripcion(d) == descripcion_normalizada
        for f, m, d in existentes
    )


def es_posible_duplicado_lote(
    fecha: date,
    monto: Decimal,
    existentes: list[tuple[date, Decimal]],
) -> bool:
    """Regla de duplicado para lotes (resumen/extracto, HU-06 CA5 y HU-14 CA3):
    misma fecha y mismo monto, sin comparar descripcion (el canal cambia el texto)."""
    return any(f == fecha and m == monto for f, m in existentes)


def validar(
    monto: Decimal | None,
    fecha: date,
    descripcion: str,
    categoria_id: int | None,
    medio_pago_id: int | None,
    hoy: date,
    categorias_validas: set[int],
    medios_pago_validos: set[int],
    existentes: list[tuple[date, Decimal, str]],
) -> ResultadoValidacion:
    errores = validar_campos(
        monto, fecha, categoria_id, medio_pago_id, hoy, categorias_validas, medios_pago_validos
    )
    advertencias = []
    if monto is not None and es_posible_duplicado(fecha, monto, descripcion, existentes):
        advertencias.append("POSIBLE_DUPLICADO")
    return ResultadoValidacion(errores=errores, advertencias=advertencias)
