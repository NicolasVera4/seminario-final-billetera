from pathlib import Path

from app.db import SesionLocal
from app.modelos import Categoria, DocumentoReferencia, MedioPago, Origen

DIRECTORIO_DATOS_REFERENCIA = Path(__file__).parent / "datos_referencia"

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


def cargar_documentos_referencia(sesion=None, cliente_chroma=None, embedder=None) -> None:
    from app.proveedores.embeddings import obtener_embedder
    from app.proveedores.vectorial import obtener_cliente_chroma
    from app.servicios.asesoramiento import cargar_documento

    sesion_propia = sesion is None
    if sesion_propia:
        sesion = SesionLocal()
    cliente_chroma = cliente_chroma or obtener_cliente_chroma()
    embedder = embedder or obtener_embedder()
    try:
        titulos_existentes = {d.titulo for d in sesion.query(DocumentoReferencia).all()}
        for ruta in sorted(DIRECTORIO_DATOS_REFERENCIA.glob("*.txt")):
            titulo = ruta.stem.replace("_", " ").capitalize()
            if titulo in titulos_existentes:
                continue
            texto = ruta.read_text(encoding="utf-8")
            cargar_documento(sesion, cliente_chroma, embedder, titulo, texto)
    finally:
        if sesion_propia:
            sesion.close()


if __name__ == "__main__":
    cargar_catalogos()
    print("Catálogos cargados.")
    cargar_documentos_referencia()
    print("Documentos de referencia cargados.")
