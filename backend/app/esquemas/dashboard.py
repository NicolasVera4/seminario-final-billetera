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


class ProyeccionSalida(BaseModel):
    datos_suficientes: bool
    anio: int | None = None
    mes: int | None = None
    monto: Decimal | None = None


class MesAnomaloSalida(BaseModel):
    anio: int
    mes: int
    monto: Decimal
    promedio_otros_meses: Decimal
    porcentaje_sobre_promedio: int


class AnomaliasSalida(BaseModel):
    datos_suficientes: bool
    meses: list[MesAnomaloSalida]


class DashboardSalida(BaseModel):
    anio: int
    mes: int
    ingresos: TotalMesSalida
    egresos: TotalMesSalida
    saldo: Decimal
    evolucion: list[PuntoEvolucionSalida]
    distribucion_categorias: list[CategoriaDistribucionSalida]
    alertas: list[AlertaSalida]
    proyeccion: ProyeccionSalida
    anomalias: AnomaliasSalida
    hay_movimientos: bool
