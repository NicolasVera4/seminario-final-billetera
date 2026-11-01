from decimal import Decimal

from pydantic import BaseModel


class TotalMesSalida(BaseModel):
    monto: Decimal
    variacion_texto: str


class PuntoEvolucionSalida(BaseModel):
    anio: int
    mes: int
    ingresos: Decimal
    egresos: Decimal


class CategoriaDistribucionSalida(BaseModel):
    categoria: str
    categoria_id: int
    monto: Decimal
    porcentaje: int


class AlertaSalida(BaseModel):
    categoria: str
    categoria_id: int
    porcentaje: int
    monto_actual: Decimal
    promedio: Decimal


class DashboardSalida(BaseModel):
    anio: int
    mes: int
    ingresos: TotalMesSalida
    egresos: TotalMesSalida
    saldo: Decimal
    evolucion: list[PuntoEvolucionSalida]
    distribucion_categorias: list[CategoriaDistribucionSalida]
    alertas: list[AlertaSalida]
    hay_movimientos: bool
