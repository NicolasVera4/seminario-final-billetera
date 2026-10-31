from app.db import SesionLocal
from app.modelos import Categoria, MedioPago, Origen

CATEGORIAS = [
    "Supermercado",
    "Hogar y servicios",
    "Restaurantes",
    "Transporte",
    "Salud y deporte",
    "Indumentaria",
    "Suscripciones",
    "Sueldo",
    "Otros",
]

MEDIOS_PAGO = [
    "Efectivo",
    "Débito",
    "Crédito",
    "Transferencia",
    "Billetera virtual",
]

ORIGENES = [
    "Texto",
    "Voz",
    "Comprobante",
    "Resumen",
    "Extracto",
]


def cargar_catalogos(sesion=None) -> None:
    sesion_propia = sesion is None
    if sesion_propia:
        sesion = SesionLocal()
    try:
        _cargar_si_falta(sesion, Categoria, CATEGORIAS)
        _cargar_si_falta(sesion, MedioPago, MEDIOS_PAGO)
        _cargar_si_falta(sesion, Origen, ORIGENES)
        sesion.commit()
    finally:
        if sesion_propia:
            sesion.close()


def _cargar_si_falta(sesion, modelo, nombres: list[str]) -> None:
    existentes = {nombre for (nombre,) in sesion.query(modelo.nombre).all()}
    for nombre in nombres:
        if nombre not in existentes:
            sesion.add(modelo(nombre=nombre))


if __name__ == "__main__":
    cargar_catalogos()
    print("Catálogos cargados.")
