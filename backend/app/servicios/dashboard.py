from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.esquemas.dashboard import (
    AlertaSalida,
    CategoriaDistribucionSalida,
    DashboardSalida,
    PuntoEvolucionSalida,
    TotalMesSalida,
)
from app.modelos.categoria import Categoria
from app.modelos.movimiento import Movimiento
from app.modelos.usuario import Usuario
from app.servicios.analisis import (
    MovimientoAnalisis,
    alertas as calcular_alertas,
    distribucion_por_categoria,
    evolucion as calcular_evolucion,
    mes_anterior,
    nombre_mes,
    texto_variacion,
    totales,
)
from app.servicios.reloj import Reloj

CANTIDAD_MESES_EVOLUCION = 6


def _primer_dia_mes(anio: int, mes: int) -> date:
    return date(anio, mes, 1)


def _mes_siguiente(anio: int, mes: int) -> tuple[int, int]:
    if mes == 12:
        return anio + 1, 1
    return anio, mes + 1


def obtener_dashboard(
    sesion: Session, usuario: Usuario, mes: str | None, reloj: Reloj
) -> DashboardSalida:
    if mes:
        anio, mes_num = (int(parte) for parte in mes.split("-"))
    else:
        hoy = reloj.ahora().date()
        anio, mes_num = hoy.year, hoy.month

    anio_inicio, mes_inicio = anio, mes_num
    for _ in range(CANTIDAD_MESES_EVOLUCION - 1):
        anio_inicio, mes_inicio = mes_anterior(anio_inicio, mes_inicio)
    anio_fin, mes_fin = _mes_siguiente(anio, mes_num)

    filas = sesion.execute(
        select(Movimiento, Categoria.nombre)
        .outerjoin(Categoria, Movimiento.categoria_id == Categoria.id)
        .where(
            Movimiento.usuario_id == usuario.id,
            Movimiento.fecha >= _primer_dia_mes(anio_inicio, mes_inicio),
            Movimiento.fecha < _primer_dia_mes(anio_fin, mes_fin),
        )
    ).all()

    movimientos = [
        MovimientoAnalisis(
            fecha=movimiento.fecha,
            tipo=movimiento.tipo,
            categoria=nombre_categoria,
            categoria_id=movimiento.categoria_id,
            monto=movimiento.monto,
        )
        for movimiento, nombre_categoria in filas
    ]

    ingresos_mes, egresos_mes, saldo = totales(
        [m for m in movimientos if m.fecha.year == anio and m.fecha.month == mes_num]
    )
    anio_ant, mes_ant = mes_anterior(anio, mes_num)
    ingresos_ant, egresos_ant, _ = totales(
        [m for m in movimientos if m.fecha.year == anio_ant and m.fecha.month == mes_ant]
    )
    nombre_mes_anterior = nombre_mes(mes_ant)

    evolucion_puntos = calcular_evolucion(movimientos, anio, mes_num, CANTIDAD_MESES_EVOLUCION)
    distribucion = distribucion_por_categoria(movimientos, anio, mes_num)
    lista_alertas = calcular_alertas(movimientos, anio, mes_num)

    hay_movimientos = any(m.fecha.year == anio and m.fecha.month == mes_num for m in movimientos)

    return DashboardSalida(
        anio=anio,
        mes=mes_num,
        ingresos=TotalMesSalida(
            monto=ingresos_mes,
            variacion_texto=texto_variacion(ingresos_mes, ingresos_ant, nombre_mes_anterior),
        ),
        egresos=TotalMesSalida(
            monto=egresos_mes,
            variacion_texto=texto_variacion(egresos_mes, egresos_ant, nombre_mes_anterior),
        ),
        saldo=saldo,
        evolucion=[
            PuntoEvolucionSalida(anio=p.anio, mes=p.mes, ingresos=p.ingresos, egresos=p.egresos)
            for p in evolucion_puntos
        ],
        distribucion_categorias=[
            CategoriaDistribucionSalida(
                categoria=c.categoria, categoria_id=c.categoria_id, monto=c.monto, porcentaje=c.porcentaje
            )
            for c in distribucion
        ],
        alertas=[
            AlertaSalida(
                categoria=a.categoria,
                categoria_id=a.categoria_id,
                porcentaje=a.porcentaje,
                monto_actual=a.monto_actual,
                promedio=a.promedio,
            )
            for a in lista_alertas
        ],
        hay_movimientos=hay_movimientos,
    )
