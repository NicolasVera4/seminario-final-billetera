from app.modelos.documento_referencia import DocumentoReferencia
from app.seed import DIRECTORIO_DATOS_REFERENCIA, cargar_documentos_referencia

TITULOS_ESPERADOS = {
    "OIT (2019). Economía familiar: herramientas para decidir mejor",
    "Riveros-Cardozo y Becker (2020). Introducción a las finanzas personales",
    "Tejeda-Hernández et al. (2021). Importancia de las finanzas personales en la salud financiera",
}


def test_seed_carga_los_tres_documentos_de_referencia_reales(sesion_bd, cliente_chroma, embedder):
    cargar_documentos_referencia(sesion_bd, cliente_chroma, embedder)

    documentos = sesion_bd.query(DocumentoReferencia).all()
    titulos = {d.titulo for d in documentos}

    assert titulos == TITULOS_ESPERADOS
    assert all(d.cantidad_fragmentos > 0 for d in documentos)


def test_seed_no_duplica_documentos_si_ya_estan_cargados(sesion_bd, cliente_chroma, embedder):
    for titulo in TITULOS_ESPERADOS:
        sesion_bd.add(DocumentoReferencia(titulo=titulo, cantidad_fragmentos=1))
    sesion_bd.flush()

    cargar_documentos_referencia(sesion_bd, cliente_chroma, embedder)

    documentos = sesion_bd.query(DocumentoReferencia).all()
    assert len(documentos) == 3


def test_el_documento_de_ejemplo_ficticio_ya_no_esta_en_el_repositorio():
    assert not (DIRECTORIO_DATOS_REFERENCIA / "tips_finanzas_personales.txt").exists()
