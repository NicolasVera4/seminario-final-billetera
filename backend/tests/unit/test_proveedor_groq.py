from datetime import date

import pytest

from app.esquemas.movimientos import Catalogo
from app.modelos.enums import TipoComprobante
from app.proveedores.llm import ErrorInterpretacion, ProveedorGroq

JSON_VALIDO = (
    '{"intencion": "REGISTRO", "movimiento": {"monto": 1000, "fecha": "2026-10-31", '
    '"tipo": "EGRESO", "medio_pago": "Efectivo", "descripcion": "test", "categoria": "Otros"}, '
    '"faltantes": []}'
)


def _fabricar_cliente(respuestas):
    respuestas_iter = iter(respuestas)
    return lambda prompt: next(respuestas_iter)


def test_reintenta_una_vez_si_el_primer_json_es_invalido():
    cliente = _fabricar_cliente(["esto no es json", JSON_VALIDO])
    proveedor = ProveedorGroq(cliente_json=cliente)
    catalogo = Catalogo(categorias=["Otros"], medios_pago=["Efectivo"])

    resultado = proveedor.clasificar_e_interpretar("gasté 1000", date(2026, 10, 31), catalogo)

    assert resultado.intencion == "REGISTRO"
    assert resultado.movimiento.monto == 1000


def test_si_los_dos_intentos_fallan_levanta_error_interpretacion():
    cliente = _fabricar_cliente(["esto no es json", "esto tampoco"])
    proveedor = ProveedorGroq(cliente_json=cliente)
    catalogo = Catalogo(categorias=[], medios_pago=[])

    with pytest.raises(ErrorInterpretacion):
        proveedor.clasificar_e_interpretar("gasté 1000", date(2026, 10, 31), catalogo)


JSON_VALIDO_MOVIMIENTOS = (
    '{"movimientos": [{"monto": 15000, "fecha": "2026-10-31", "tipo": "EGRESO", '
    '"medio_pago": "Débito", "descripcion": "Compra en el súper", "categoria": "Supermercado"}]}'
)


def test_extraer_movimientos_reintenta_una_vez_si_el_primer_json_es_invalido():
    cliente = _fabricar_cliente(["esto no es json", JSON_VALIDO_MOVIMIENTOS])
    proveedor = ProveedorGroq(cliente_json=cliente)
    catalogo = Catalogo(categorias=["Supermercado"], medios_pago=["Débito"])

    resultado = proveedor.extraer_movimientos("texto del ticket", TipoComprobante.TICKET, catalogo)

    assert len(resultado) == 1
    assert resultado[0].monto == 15000


def test_extraer_movimientos_si_los_dos_intentos_fallan_levanta_error():
    cliente = _fabricar_cliente(["mal", "mal"])
    proveedor = ProveedorGroq(cliente_json=cliente)
    catalogo = Catalogo(categorias=[], medios_pago=[])

    with pytest.raises(ErrorInterpretacion):
        proveedor.extraer_movimientos("texto del ticket", TipoComprobante.TICKET, catalogo)
