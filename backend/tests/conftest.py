import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.config import settings
from app.db import obtener_sesion
from app.main import app
from app.servicios.reloj import obtener_reloj
from tests.dobles import RelojFijo
from datetime import UTC, datetime

engine_test = create_engine(settings.database_url_test)


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
def cliente(sesion_bd, reloj):
    app.dependency_overrides[obtener_sesion] = lambda: sesion_bd
    app.dependency_overrides[obtener_reloj] = lambda: reloj
    with TestClient(app) as cliente:
        yield cliente
    app.dependency_overrides.clear()
