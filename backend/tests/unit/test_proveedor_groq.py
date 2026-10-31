from datetime import date

import pytest

from app.esquemas.movimientos import Catalogo
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
