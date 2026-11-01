from chromadb.api import ClientAPI
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.esquemas.chat import MensajeSalida
from app.modelos.documento_referencia import DocumentoReferencia
from app.modelos.usuario import Usuario
from app.proveedores.embeddings import Embedder
from app.proveedores.llm import ProveedorLLM
from app.proveedores.vectorial import COLECCION_FRAGMENTOS
from app.servicios.analisis import MovimientoAnalisis, distribucion_por_categoria, evolucion, mes_anterior, nombre_mes
from app.servicios.chunking import dividir_en_fragmentos
from app.servicios.consulta_movimientos import obtener_movimientos_analisis
from app.servicios.reloj import Reloj

DISCLAIMER = "Esto es orientativo y no reemplaza el asesoramiento de un profesional."
MENSAJE_SIN_MOVIMIENTOS = (
    "No tenés movimientos cargados todavía, así que esta respuesta se basa solo en la documentación."
)
CANTIDAD_FRAGMENTOS_RECUPERADOS = 4
CANTIDAD_MESES_CONTEXTO = 6


def cargar_documento(
    sesion: Session, cliente_chroma: ClientAPI, embedder: Embedder, titulo: str, texto: str
) -> DocumentoReferencia:
    fragmentos = dividir_en_fragmentos(texto)

    documento = DocumentoReferencia(titulo=titulo, cantidad_fragmentos=len(fragmentos))
    sesion.add(documento)
    sesion.flush()

    vectores = embedder.embeber(fragmentos)
    coleccion = cliente_chroma.get_or_create_collection(COLECCION_FRAGMENTOS)
    coleccion.add(
        ids=[f"{documento.id}-{indice}" for indice in range(len(fragmentos))],
        embeddings=vectores,
        documents=fragmentos,
        metadatas=[
            {"documento_id": documento.id, "titulo": titulo, "indice_fragmento": indice}
            for indice in range(len(fragmentos))
        ],
    )

    sesion.commit()
    sesion.refresh(documento)
    return documento


def eliminar_documento(sesion: Session, cliente_chroma: ClientAPI, documento_id: int) -> None:
    documento = sesion.get(DocumentoReferencia, documento_id)
    if documento is None:
        return

    coleccion = cliente_chroma.get_or_create_collection(COLECCION_FRAGMENTOS)
    coleccion.delete(where={"documento_id": documento_id})
    sesion.delete(documento)
    sesion.commit()


def listar_documentos(sesion: Session) -> list[DocumentoReferencia]:
    return (
        sesion.execute(select(DocumentoReferencia).order_by(DocumentoReferencia.creado_en.desc()))
        .scalars()
        .all()
    )


def responder_consulta(
    sesion: Session,
    usuario: Usuario,
    cliente_chroma: ClientAPI,
    embedder: Embedder,
    proveedor_llm: ProveedorLLM,
    reloj: Reloj,
    pregunta: str,
    intencion: str,
    historial: list[MensajeSalida],
) -> tuple[str, list[dict]]:
    hoy = reloj.ahora().date()
    movimientos = obtener_movimientos_analisis(sesion, usuario.id)
    hay_movimientos = len(movimientos) > 0

    contexto_usuario = None
    fuentes: list[dict] = []
    if hay_movimientos:
        contexto_usuario = _construir_resumen(movimientos, hoy)
        fuentes.append(_fuente_movimientos(hoy))

    fragmentos: list[str] = []
    if intencion == "CONSULTA_ASESORAMIENTO":
        fragmentos, fuentes_documentos = _recuperar_fragmentos(cliente_chroma, embedder, pregunta)
        fuentes.extend(fuentes_documentos)

    texto = proveedor_llm.responder(pregunta, contexto_usuario, fragmentos, historial)

    if intencion == "CONSULTA_ASESORAMIENTO":
        partes = [texto]
        if not hay_movimientos:
            partes.append(MENSAJE_SIN_MOVIMIENTOS)
        partes.append(DISCLAIMER)
        texto = " ".join(partes)

    return texto, fuentes


def _recuperar_fragmentos(
    cliente_chroma: ClientAPI, embedder: Embedder, pregunta: str
) -> tuple[list[str], list[dict]]:
    coleccion = cliente_chroma.get_or_create_collection(COLECCION_FRAGMENTOS)
    if coleccion.count() == 0:
        return [], []

    vector_pregunta = embedder.embeber([pregunta])[0]
    resultado = coleccion.query(
        query_embeddings=[vector_pregunta], n_results=min(CANTIDAD_FRAGMENTOS_RECUPERADOS, coleccion.count())
    )
    documentos = resultado["documents"][0] if resultado["documents"] else []
    metadatas = resultado["metadatas"][0] if resultado["metadatas"] else []
    fuentes = [
        {"tipo": "documento", "titulo": metadata["titulo"], "fragmento": metadata["indice_fragmento"]}
        for metadata in metadatas
    ]
    return documentos, fuentes


def _fuente_movimientos(hoy) -> dict:
    anio_desde, mes_desde = hoy.year, hoy.month
    for _ in range(CANTIDAD_MESES_CONTEXTO - 1):
        anio_desde, mes_desde = mes_anterior(anio_desde, mes_desde)
    return {
        "tipo": "movimientos",
        "desde": f"{anio_desde:04d}-{mes_desde:02d}",
        "hasta": f"{hoy.year:04d}-{hoy.month:02d}",
    }


def _construir_resumen(movimientos: list[MovimientoAnalisis], hoy) -> str:
    puntos = evolucion(movimientos, hoy.year, hoy.month, CANTIDAD_MESES_CONTEXTO)
    lineas = ["Resumen de los últimos 6 meses del usuario:"]
    for punto in puntos:
        lineas.append(
            f"- {nombre_mes(punto.mes)} {punto.anio}: ingresos ${punto.ingresos}, egresos ${punto.egresos}"
        )
        distribucion = distribucion_por_categoria(movimientos, punto.anio, punto.mes)
        if distribucion:
            detalle = ", ".join(f"{c.categoria} ${c.monto}" for c in distribucion)
            lineas.append(f"  Gastos por categoría: {detalle}")
    return "\n".join(lineas)
