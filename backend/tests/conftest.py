import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def cliente():
    with TestClient(app) as cliente:
        yield cliente
