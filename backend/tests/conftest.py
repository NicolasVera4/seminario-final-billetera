from datetime import UTC, datetime

import chromadb
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.config import settings
from app.db import obtener_sesion
from app.main import app
from app.proveedores.embeddings import obtener_embedder
from app.proveedores.llm import obtener_proveedor_llm
from app.proveedores.transcripcion import obtener_transcriptor
from app.proveedores.vectorial import obtener_cliente_chroma
from app.seed import cargar_catalogos
from app.servicios.reloj import obtener_reloj
from tests.dobles import FakeEmbedder, FakeLLM, FakeTranscriptor, RelojFijo

engine_test = create_engine(settings.database_url_test)


@pytest.fixture(scope="session", autouse=True)
def _catalogos_seedeados():
    sesion = Session(bind=engine_test)
    try:
        cargar_catalogos(sesion)
    finally:
        sesion.close()


@pytest.fixture
def sesion_bd():
    conexion = engine_test.connect()
    transaccion = conexion.begin()
    sesion = Session(bind=conexion, join_transaction_mode="create_savepoint")
    yield sesion
    sesion.close()
    transaccion.rollback()
    conexion.close()


@pytest.fixture
def reloj():
    return RelojFijo(datetime(2026, 10, 31, 12, 0, tzinfo=UTC))


@pytest.fixture
def proveedor_llm():
    return FakeLLM()


@pytest.fixture
def embedder():
    return FakeEmbedder()


@pytest.fixture
def cliente_chroma():
    return chromadb.EphemeralClient()


@pytest.fixture
def transcriptor():
    return FakeTranscriptor()


@pytest.fixture
def cliente(sesion_bd, reloj, proveedor_llm, embedder, cliente_chroma, transcriptor):
    app.dependency_overrides[obtener_sesion] = lambda: sesion_bd
    app.dependency_overrides[obtener_reloj] = lambda: reloj
    app.dependency_overrides[obtener_proveedor_llm] = lambda: proveedor_llm
    app.dependency_overrides[obtener_embedder] = lambda: embedder
    app.dependency_overrides[obtener_cliente_chroma] = lambda: cliente_chroma
    app.dependency_overrides[obtener_transcriptor] = lambda: transcriptor
    with TestClient(app) as cliente:
        yield cliente
    app.dependency_overrides.clear()
