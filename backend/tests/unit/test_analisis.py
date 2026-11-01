from datetime import date
from decimal import Decimal

from app.modelos.enums import TipoMovimiento
from app.servicios.analisis import (
    MovimientoAnalisis,
    alertas,
    detectar_anomalias,
    distribucion_por_categoria,
    evolucion,
    proyeccion_gasto,
    texto_variacion,
    totales,
)

EGRESO = TipoMovimiento.EGRESO
INGRESO = TipoMovimiento.INGRESO


def _mov(fecha, tipo, monto, categoria="Supermercado", categoria_id=1):
    return MovimientoAnalisis(
        fecha=fecha, tipo=tipo, categoria=categoria, categoria_id=categoria_id, monto=Decimal(monto)
    )


def test_totales_suma_ingresos_egresos_y_calcula_saldo():
    movimientos = [
        _mov(date(2026, 9, 3), INGRESO, "980000"),
        _mov(date(2026, 9, 27), EGRESO, "15000"),
        _mov(date(2026, 9, 27), EGRESO, "28000"),
    ]

    ingresos, egresos, saldo = totales(movimientos)

    assert ingresos == Decimal("980000")
    assert egresos == Decimal("43000")
    assert saldo == Decimal("937000")


def test_texto_variacion_igual():
    assert texto_variacion(Decimal("980000"), Decimal("980000"), "agosto") == "Igual que en agosto."


def test_texto_variacion_mas():
    assert texto_variacion(Decimal("612450"), Decimal("590000"), "agosto") == "3,8% más que en agosto."


def test_texto_variacion_menos():
    assert texto_variacion(Decimal("450000"), Decimal("600000"), "agosto") == "25,0% menos que en agosto."


def test_texto_variacion_sin_datos_del_mes_anterior():
    assert texto_variacion(Decimal("15000"), Decimal("0"), "agosto") == "Sin datos de agosto para comparar."


def test_evolucion_devuelve_los_ultimos_n_meses_con_huecos_en_cero():
    movimientos = [
        _mov(date(2026, 7, 10), EGRESO, "1000"),
        _mov(date(2026, 9, 5), INGRESO, "5000"),
    ]

    puntos = evolucion(movimientos, anio=2026, mes=9, cantidad=3)

    assert [(p.anio, p.mes) for p in puntos] == [(2026, 7), (2026, 8), (2026, 9)]
    assert puntos[0].egresos == Decimal("1000")
    assert puntos[1].ingresos == Decimal("0")
    assert puntos[1].egresos == Decimal("0")
    assert puntos[2].ingresos == Decimal("5000")


def test_distribucion_por_categoria_ordena_descendente_con_otros_al_final():
    movimientos = [
        _mov(date(2026, 9, 5), EGRESO, "5000", categoria="Otros", categoria_id=9),
        _mov(date(2026, 9, 5), EGRESO, "20000", categoria="Supermercado", categoria_id=1),
        _mov(date(2026, 9, 5), EGRESO, "10000", categoria="Transporte", categoria_id=4),
    ]

    resultado = distribucion_por_categoria(movimientos, anio=2026, mes=9)

    assert [c.categoria for c in resultado] == ["Supermercado", "Transporte", "Otros"]
    assert resultado[0].porcentaje == 57
    total_monto = sum((c.monto for c in resultado), Decimal(0))
    assert total_monto == Decimal("35000")


def _serie_mensual(montos, anio_inicio, mes_inicio, categoria="Varios", categoria_id=1):
    """Un movimiento de egreso por mes, empezando en (anio_inicio, mes_inicio)."""
    resultado = []
    anio, mes = anio_inicio, mes_inicio
    for monto in montos:
        resultado.append(_mov(date(anio, mes, 15), EGRESO, monto, categoria=categoria, categoria_id=categoria_id))
        anio, mes = (anio + 1, 1) if mes == 12 else (anio, mes + 1)
    return resultado


def _tres_meses_previos(categoria, categoria_id, montos, mes_base=9):
    return [
        _mov(date(2026, mes_base - i - 1, 15), EGRESO, monto, categoria=categoria, categoria_id=categoria_id)
        for i, monto in enumerate(reversed(montos))
    ]


def test_hu09_ca1_alerta_cuando_el_gasto_supera_30_por_ciento_el_promedio():
    movimientos = _tres_meses_previos("Restaurantes", 3, ["60000", "60000", "62400"]) + [
        _mov(date(2026, 9, 10), EGRESO, "86400", categoria="Restaurantes", categoria_id=3),
    ]

    resultado = alertas(movimientos, anio=2026, mes=9)

    assert len(resultado) == 1
    assert resultado[0].categoria == "Restaurantes"


def test_sin_alerta_si_no_supera_el_umbral():
    movimientos = _tres_meses_previos("Restaurantes", 3, ["60000", "60000", "60000"]) + [
        _mov(date(2026, 9, 10), EGRESO, "65000", categoria="Restaurantes", categoria_id=3),
    ]

    resultado = alertas(movimientos, anio=2026, mes=9)

    assert resultado == []


def test_hu09_ca2_sin_alerta_con_menos_de_3_meses_de_historial_de_la_categoria():
    movimientos = [
        _mov(date(2026, 8, 15), EGRESO, "10000", categoria="Restaurantes", categoria_id=3),
        _mov(date(2026, 9, 10), EGRESO, "86400", categoria="Restaurantes", categoria_id=3),
    ]

    resultado = alertas(movimientos, anio=2026, mes=9)

    assert resultado == []


def test_hu09_ca3_la_alerta_incluye_categoria_monto_actual_y_promedio():
    movimientos = _tres_meses_previos("Restaurantes", 3, ["60000", "60000", "60000"]) + [
        _mov(date(2026, 9, 10), EGRESO, "86400", categoria="Restaurantes", categoria_id=3),
    ]

    resultado = alertas(movimientos, anio=2026, mes=9)

    assert resultado[0].monto_actual == Decimal("86400")
    assert resultado[0].promedio == Decimal("60000")
    assert resultado[0].porcentaje == 44


def test_hu12_ca1_tendencia_creciente_proyecta_por_encima_del_ultimo_mes():
    movimientos = _serie_mensual(
        ["500000", "510000", "520000", "530000", "540000", "550000"], 2026, 4
    )

    resultado = proyeccion_gasto(movimientos, anio=2026, mes=9, cantidad=6)

    assert resultado.datos_suficientes is True
    assert (resultado.anio, resultado.mes) == (2026, 10)
    assert resultado.monto > Decimal("550000")


def test_hu12_ca2_sin_datos_suficientes_con_menos_de_3_meses():
    movimientos = _serie_mensual(["500000", "510000"], 2026, 8)

    resultado = proyeccion_gasto(movimientos, anio=2026, mes=9, cantidad=6)

    assert resultado.datos_suficientes is False
    assert resultado.monto is None


def test_hu12_proyeccion_negativa_se_recorta_a_cero():
    movimientos = _serie_mensual(["900000", "450000", "100000"], 2026, 7)

    resultado = proyeccion_gasto(movimientos, anio=2026, mes=9, cantidad=3)

    assert resultado.datos_suficientes is True
    assert resultado.monto == Decimal("0")


def test_hu13_ca1_detecta_el_mes_que_duplica_al_resto_con_6_meses_de_historial():
    movimientos = _serie_mensual(
        ["500000", "505000", "495000", "1000000", "510000", "495000"], 2026, 4
    )

    resultado = detectar_anomalias(movimientos, anio=2026, mes=9, cantidad=6)

    assert resultado.datos_suficientes is True
    assert [(m.anio, m.mes) for m in resultado.meses] == [(2026, 7)]


def test_hu13_ca3_el_mes_anomalo_incluye_monto_promedio_y_porcentaje():
    movimientos = _serie_mensual(
        ["500000", "505000", "495000", "1000000", "510000", "495000"], 2026, 4
    )

    resultado = detectar_anomalias(movimientos, anio=2026, mes=9, cantidad=6)

    anomalo = resultado.meses[0]
    assert anomalo.monto == Decimal("1000000")
    assert anomalo.promedio_otros_meses == Decimal("501000")
    assert anomalo.porcentaje_sobre_promedio == 100


def test_hu13_ca1_no_marca_meses_normales_sin_outlier():
    movimientos = _serie_mensual(
        ["500000", "505000", "495000", "510000", "490000", "500000"], 2026, 4
    )

    resultado = detectar_anomalias(movimientos, anio=2026, mes=9, cantidad=6)

    assert resultado.datos_suficientes is True
    assert resultado.meses == []


def test_hu13_ca2_sin_datos_suficientes_con_menos_de_4_meses():
    movimientos = _serie_mensual(["500000", "510000", "520000"], 2026, 7)

    resultado = detectar_anomalias(movimientos, anio=2026, mes=9, cantidad=6)

    assert resultado.datos_suficientes is False
    assert resultado.meses == []
