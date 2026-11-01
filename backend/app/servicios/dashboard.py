from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.esquemas.dashboard import (
    AlertaSalida,
    AnomaliasSalida,
    CategoriaDistribucionSalida,
    DashboardSalida,
    MesAnomaloSalida,
    ProyeccionSalida,
    PuntoEvolucionSalida,
    TotalMesSalida,
)
from app.modelos.usuario import Usuario
from app.servicios.analisis import (
    alertas as calcular_alertas,
    detectar_anomalias,
    distribucion_por_categoria,
    evolucion as calcular_evolucion,
    mes_anterior,
    mes_siguiente,
    nombre_mes,
    proyeccion_gasto,
    texto_variacion,
    totales,
)
from app.servicios.consulta_movimientos import obtener_movimientos_analisis
from app.servicios.reloj import Reloj

CANTIDAD_MESES_EVOLUCION = 6


def _primer_dia_mes(anio: int, mes: int) -> date:
    return date(anio, mes, 1)


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
    anio_fin, mes_fin = mes_siguiente(anio, mes_num)
    ultimo_dia_incluido = _primer_dia_mes(anio_fin, mes_fin) - timedelta(days=1)

    movimientos = obtener_movimientos_analisis(
        sesion, usuario.id, desde=_primer_dia_mes(anio_inicio, mes_inicio), hasta=ultimo_dia_incluido
    )

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
    proyeccion = proyeccion_gasto(movimientos, anio, mes_num, CANTIDAD_MESES_EVOLUCION)
    anomalias = detectar_anomalias(movimientos, anio, mes_num, CANTIDAD_MESES_EVOLUCION)

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
        proyeccion=ProyeccionSalida(
            datos_suficientes=proyeccion.datos_suficientes,
            anio=proyeccion.anio,
            mes=proyeccion.mes,
            monto=proyeccion.monto,
        ),
        anomalias=AnomaliasSalida(
            datos_suficientes=anomalias.datos_suficientes,
            meses=[
                MesAnomaloSalida(
                    anio=m.anio,
                    mes=m.mes,
                    monto=m.monto,
                    promedio_otros_meses=m.promedio_otros_meses,
                    porcentaje_sobre_promedio=m.porcentaje_sobre_promedio,
                )
                for m in anomalias.meses
            ],
        ),
        hay_movimientos=hay_movimientos,
    )
