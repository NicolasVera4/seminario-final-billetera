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
    raise NotImplementedError


def normalizar_descripcion(texto: str) -> str:
    raise NotImplementedError


def es_posible_duplicado(
    fecha: date,
    monto: Decimal,
    descripcion: str,
    existentes: list[tuple[date, Decimal, str]],
) -> bool:
    raise NotImplementedError


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
    raise NotImplementedError
