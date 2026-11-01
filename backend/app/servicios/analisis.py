from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from app.modelos.enums import TipoMovimiento

MESES_ES = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
]

UMBRAL_ALERTA = Decimal("1.30")
MESES_HISTORIAL_ALERTA = 3


@dataclass
class MovimientoAnalisis:
    fecha: date
    tipo: TipoMovimiento
    categoria: str | None
    categoria_id: int | None
    monto: Decimal


@dataclass
class PuntoEvolucion:
    anio: int
    mes: int
    ingresos: Decimal
    egresos: Decimal


@dataclass
class CategoriaDistribucion:
    categoria: str
    categoria_id: int
    monto: Decimal
    porcentaje: int


@dataclass
class Alerta:
    categoria: str
    categoria_id: int
    porcentaje: int
    monto_actual: Decimal
    promedio: Decimal


def nombre_mes(mes: int) -> str:
    return MESES_ES[mes - 1]


def mes_anterior(anio: int, mes: int) -> tuple[int, int]:
    if mes == 1:
        return anio - 1, 12
    return anio, mes - 1


def totales(movimientos: list[MovimientoAnalisis]) -> tuple[Decimal, Decimal, Decimal]:
    ingresos = sum((m.monto for m in movimientos if m.tipo == TipoMovimiento.INGRESO), Decimal(0))
    egresos = sum((m.monto for m in movimientos if m.tipo == TipoMovimiento.EGRESO), Decimal(0))
    return ingresos, egresos, ingresos - egresos


def texto_variacion(actual: Decimal, anterior: Decimal, nombre_mes_anterior: str) -> str:
    if anterior == 0:
        if actual == 0:
            return f"Igual que en {nombre_mes_anterior}."
        return f"Sin datos de {nombre_mes_anterior} para comparar."

    variacion = (actual - anterior) / anterior * 100
    variacion_redondeada = variacion.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
    if variacion_redondeada == 0:
        return f"Igual que en {nombre_mes_anterior}."

    texto_pct = f"{abs(variacion_redondeada):.1f}".replace(".", ",")
    palabra = "más" if variacion_redondeada > 0 else "menos"
    return f"{texto_pct}% {palabra} que en {nombre_mes_anterior}."


def _del_mes(movimientos: list[MovimientoAnalisis], anio: int, mes: int) -> list[MovimientoAnalisis]:
    return [m for m in movimientos if m.fecha.year == anio and m.fecha.month == mes]


def evolucion(
    movimientos: list[MovimientoAnalisis], anio: int, mes: int, cantidad: int = 6
) -> list[PuntoEvolucion]:
    meses_objetivo = []
    a, m = anio, mes
    for _ in range(cantidad):
        meses_objetivo.append((a, m))
        a, m = mes_anterior(a, m)
    meses_objetivo.reverse()

    puntos = []
    for a, m in meses_objetivo:
        del_mes = _del_mes(movimientos, a, m)
        ingresos, egresos, _ = totales(del_mes)
        puntos.append(PuntoEvolucion(anio=a, mes=m, ingresos=ingresos, egresos=egresos))
    return puntos


def distribucion_por_categoria(
    movimientos: list[MovimientoAnalisis], anio: int, mes: int
) -> list[CategoriaDistribucion]:
    egresos_mes = [m for m in _del_mes(movimientos, anio, mes) if m.tipo == TipoMovimiento.EGRESO]
    total = sum((m.monto for m in egresos_mes), Decimal(0))

    por_categoria: dict[tuple[str, int], Decimal] = {}
    for m in egresos_mes:
        clave = (m.categoria, m.categoria_id)
        por_categoria[clave] = por_categoria.get(clave, Decimal(0)) + m.monto

    resultado = [
        CategoriaDistribucion(
            categoria=categoria,
            categoria_id=categoria_id,
            monto=monto,
            porcentaje=int((monto / total * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
            if total
            else 0,
        )
        for (categoria, categoria_id), monto in por_categoria.items()
    ]
    resultado.sort(key=lambda c: (c.categoria == "Otros", -c.monto))
    return resultado


def alertas(movimientos: list[MovimientoAnalisis], anio: int, mes: int) -> list[Alerta]:
    egresos_mes_actual = [m for m in _del_mes(movimientos, anio, mes) if m.tipo == TipoMovimiento.EGRESO]
    categorias_actuales: dict[tuple[str, int], Decimal] = {}
    for m in egresos_mes_actual:
        clave = (m.categoria, m.categoria_id)
        categorias_actuales[clave] = categorias_actuales.get(clave, Decimal(0)) + m.monto

    meses_previos = []
    a, m_mes = anio, mes
    for _ in range(MESES_HISTORIAL_ALERTA):
        a, m_mes = mes_anterior(a, m_mes)
        meses_previos.append((a, m_mes))

    resultado = []
    for (categoria, categoria_id), monto_actual in categorias_actuales.items():
        montos_meses_previos = []
        for a_prev, m_prev in meses_previos:
            monto_mes = sum(
                (
                    mv.monto
                    for mv in _del_mes(movimientos, a_prev, m_prev)
                    if mv.tipo == TipoMovimiento.EGRESO and mv.categoria_id == categoria_id
                ),
                Decimal(0),
            )
            if monto_mes == 0:
                montos_meses_previos = None
                break
            montos_meses_previos.append(monto_mes)

        if montos_meses_previos is None:
            continue

        promedio = sum(montos_meses_previos, Decimal(0)) / MESES_HISTORIAL_ALERTA
        if monto_actual > UMBRAL_ALERTA * promedio:
            porcentaje = int(
                ((monto_actual / promedio - 1) * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
            )
            resultado.append(
                Alerta(
                    categoria=categoria,
                    categoria_id=categoria_id,
                    porcentaje=porcentaje,
                    monto_actual=monto_actual,
                    promedio=promedio,
                )
            )

    return resultado
