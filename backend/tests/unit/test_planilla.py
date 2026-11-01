from datetime import date
from decimal import Decimal

from app.servicios.ingesta.planilla import detectar_columnas_por_sinonimos, parsear_fecha, parsear_monto


def test_detecta_columnas_por_sinonimos_formato_a():
    resultado = detectar_columnas_por_sinonimos(["Fecha", "Descripcion", "Monto"])

    assert resultado == {"fecha": "Fecha", "monto": "Monto", "descripcion": "Descripcion"}


def test_detecta_columnas_por_sinonimos_formato_b():
    resultado = detectar_columnas_por_sinonimos(["F. Operacion", "Detalle", "Importe"])

    assert resultado == {"fecha": "F. Operacion", "monto": "Importe", "descripcion": "Detalle"}


def test_detecta_columnas_por_sinonimos_sin_coincidencia_devuelve_none():
    resultado = detectar_columnas_por_sinonimos(["Día", "Qué fue", "Guita"])

    assert resultado == {"fecha": None, "monto": None, "descripcion": None}


def test_parsear_fecha_formato_dia_mes_anio():
    assert parsear_fecha("31/10/2026") == date(2026, 10, 31)


def test_parsear_fecha_formato_iso():
    assert parsear_fecha("2026-10-31") == date(2026, 10, 31)


def test_parsear_fecha_invalida_devuelve_none():
    assert parsear_fecha("no es una fecha") is None


def test_parsear_monto_formato_argentino():
    assert parsear_monto("15.000,50") == Decimal("15000.50")


def test_parsear_monto_formato_estadounidense():
    assert parsear_monto("15,000.50") == Decimal("15000.50")


def test_parsear_monto_sin_separador_de_miles():
    assert parsear_monto("15000,50") == Decimal("15000.50")


def test_parsear_monto_con_signo_pesos():
    assert parsear_monto("$ 15000") == Decimal("15000")


def test_parsear_monto_invalido_devuelve_none():
    assert parsear_monto("no es un monto") is None
