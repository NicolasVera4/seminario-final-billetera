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


DOCUMENTOS_REFERENCIA = {
    "oit_2019_economia_familiar.pdf": "OIT (2019). Economía familiar: herramientas para decidir mejor",
    "riveros_becker_2020_finanzas_personales.pdf": (
        "Riveros-Cardozo y Becker (2020). Introducción a las finanzas personales"
    ),
    "tejeda_hernandez_2021_salud_financiera.pdf": (
        "Tejeda-Hernández et al. (2021). Importancia de las finanzas personales en la salud financiera"
    ),
}


def cargar_documentos_referencia(sesion=None, cliente_chroma=None, embedder=None) -> None:
    from app.proveedores.embeddings import obtener_embedder
    from app.proveedores.vectorial import obtener_cliente_chroma
    from app.servicios.asesoramiento import cargar_documento
    from app.servicios.ingesta.pdf import extraer_texto_pdf

    sesion_propia = sesion is None
    if sesion_propia:
        sesion = SesionLocal()
    cliente_chroma = cliente_chroma or obtener_cliente_chroma()
    embedder = embedder or obtener_embedder()
    try:
        titulos_existentes = {d.titulo for d in sesion.query(DocumentoReferencia).all()}
        for nombre_archivo, titulo in DOCUMENTOS_REFERENCIA.items():
            if titulo in titulos_existentes:
                continue
            contenido = (DIRECTORIO_DATOS_REFERENCIA / nombre_archivo).read_bytes()
            texto = extraer_texto_pdf(contenido)
            cargar_documento(sesion, cliente_chroma, embedder, titulo, texto)
    finally:
        if sesion_propia:
            sesion.close()


if __name__ == "__main__":
    cargar_catalogos()
    print("Catálogos cargados.")
    cargar_documentos_referencia()
    print("Documentos de referencia cargados.")
