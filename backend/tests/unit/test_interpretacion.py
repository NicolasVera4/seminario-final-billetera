from app.modelos.categoria import Categoria
from app.modelos.medio_pago import MedioPago
from app.servicios.interpretacion import resolver_categoria, resolver_medio_pago

CATEGORIAS = [Categoria(id=1, nombre="Supermercado"), Categoria(id=2, nombre="Transporte")]
MEDIOS_PAGO = [MedioPago(id=1, nombre="Efectivo"), MedioPago(id=2, nombre="Débito")]


def test_resolver_categoria_en_el_catalogo_devuelve_su_id():
    categoria_id, categoria_sugerida = resolver_categoria(CATEGORIAS, "Supermercado")

    assert categoria_id == 1
    assert categoria_sugerida is None


def test_resolver_categoria_fuera_del_catalogo_devuelve_id_nulo_y_sugerida():
    categoria_id, categoria_sugerida = resolver_categoria(CATEGORIAS, "Gimnasio")

    assert categoria_id is None
    assert categoria_sugerida == "Gimnasio"


def test_resolver_categoria_ausente_devuelve_todo_nulo():
    categoria_id, categoria_sugerida = resolver_categoria(CATEGORIAS, None)

    assert categoria_id is None
    assert categoria_sugerida is None


def test_resolver_medio_pago_en_el_catalogo_devuelve_su_id():
    assert resolver_medio_pago(MEDIOS_PAGO, "Débito") == 2


def test_resolver_medio_pago_ausente_devuelve_id_nulo():
    assert resolver_medio_pago(MEDIOS_PAGO, None) is None


def test_resolver_medio_pago_fuera_del_catalogo_devuelve_id_nulo():
    assert resolver_medio_pago(MEDIOS_PAGO, "Criptomoneda") is None
