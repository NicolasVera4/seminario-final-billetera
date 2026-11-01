from datetime import date
from decimal import Decimal

from app.servicios.validacion import (
    es_posible_duplicado,
    es_posible_duplicado_lote,
    normalizar_descripcion,
    validar_campos,
)

HOY = date(2026, 10, 31)
CATEGORIAS_VALIDAS = {1, 2}
MEDIOS_PAGO_VALIDOS = {1, 2}


def test_hu04_ca1_monto_cero_es_invalido():
    errores = validar_campos(Decimal("0"), HOY, 1, 1, HOY, CATEGORIAS_VALIDAS, MEDIOS_PAGO_VALIDOS)
    assert "MONTO_INVALIDO" in errores


def test_hu04_ca1_monto_negativo_es_invalido():
    errores = validar_campos(Decimal("-5"), HOY, 1, 1, HOY, CATEGORIAS_VALIDAS, MEDIOS_PAGO_VALIDOS)
    assert "MONTO_INVALIDO" in errores


def test_hu04_ca1_fecha_posterior_a_hoy_es_invalida():
    manana = date(2026, 11, 1)
    errores = validar_campos(Decimal("100"), manana, 1, 1, HOY, CATEGORIAS_VALIDAS, MEDIOS_PAGO_VALIDOS)
    assert "FECHA_FUTURA" in errores


def test_hu04_ca2_categoria_nula_es_invalida():
    errores = validar_campos(Decimal("100"), HOY, None, 1, HOY, CATEGORIAS_VALIDAS, MEDIOS_PAGO_VALIDOS)
    assert "CATEGORIA_INVALIDA" in errores


def test_hu04_ca2_categoria_fuera_de_catalogo_es_invalida():
    errores = validar_campos(Decimal("100"), HOY, 999, 1, HOY, CATEGORIAS_VALIDAS, MEDIOS_PAGO_VALIDOS)
    assert "CATEGORIA_INVALIDA" in errores


def test_hu04_ca3_medio_de_pago_nulo_es_invalido():
    errores = validar_campos(Decimal("100"), HOY, 1, None, HOY, CATEGORIAS_VALIDAS, MEDIOS_PAGO_VALIDOS)
    assert "MEDIO_PAGO_FALTANTE" in errores


def test_movimiento_valido_no_tiene_errores():
    errores = validar_campos(Decimal("100"), HOY, 1, 1, HOY, CATEGORIAS_VALIDAS, MEDIOS_PAGO_VALIDOS)
    assert errores == []


def test_normalizar_descripcion_minusculas_sin_tildes_y_espacios_colapsados():
    assert normalizar_descripcion("  Compra EN el Súper  ") == "compra en el super"


def test_hu04_ca4_mismo_dia_monto_y_descripcion_es_duplicado():
    existentes = [(HOY, Decimal("15000"), "Compra en el súper")]
    assert es_posible_duplicado(HOY, Decimal("15000"), "compra en el súper", existentes) is True


def test_no_es_duplicado_si_difiere_el_monto():
    existentes = [(HOY, Decimal("15000"), "Compra en el súper")]
    assert es_posible_duplicado(HOY, Decimal("999"), "Compra en el súper", existentes) is False


def test_no_es_duplicado_si_difiere_la_fecha():
    existentes = [(HOY, Decimal("15000"), "Compra en el súper")]
    otro_dia = date(2026, 10, 30)
    assert es_posible_duplicado(otro_dia, Decimal("15000"), "Compra en el súper", existentes) is False


def test_hu06_ca5_duplicado_de_lote_misma_fecha_y_monto_sin_comparar_descripcion():
    existentes = [(HOY, Decimal("32600"))]
    assert es_posible_duplicado_lote(HOY, Decimal("32600"), existentes) is True


def test_no_es_duplicado_de_lote_si_difiere_el_monto():
    existentes = [(HOY, Decimal("32600"))]
    assert es_posible_duplicado_lote(HOY, Decimal("999"), existentes) is False
