from datetime import UTC, datetime, timedelta

from jose import jwt

from app.config import settings
from tests.ayudantes import registrar_y_loguear


def test_hu02_ca3_aislamiento_entre_dos_usuarios(cliente):
    token_a = registrar_y_loguear(cliente, nombre="Usuaria A", correo="a@mail.com")
    token_b = registrar_y_loguear(cliente, nombre="Usuario B", correo="b@mail.com")

    respuesta_a = cliente.get("/api/auth/yo", headers={"Authorization": f"Bearer {token_a}"})
    respuesta_b = cliente.get("/api/auth/yo", headers={"Authorization": f"Bearer {token_b}"})

    assert respuesta_a.json()["correo"] == "a@mail.com"
    assert respuesta_b.json()["correo"] == "b@mail.com"
    assert respuesta_a.json()["id"] != respuesta_b.json()["id"]


def test_hu02_ca4_token_vencido_devuelve_401(cliente):
    token_vencido = jwt.encode(
        {"sub": "1", "exp": datetime.now(UTC) - timedelta(minutes=1)},
        settings.jwt_secreto,
        algorithm="HS256",
    )

    respuesta = cliente.get("/api/auth/yo", headers={"Authorization": f"Bearer {token_vencido}"})

    assert respuesta.status_code == 401


def test_header_x_token_renovado_en_respuesta_autenticada(cliente):
    token = registrar_y_loguear(cliente, nombre="Usuaria A", correo="a@mail.com")

    respuesta = cliente.get("/api/auth/yo", headers={"Authorization": f"Bearer {token}"})

    assert "X-Token-Renovado" in respuesta.headers
    nuevo_token = respuesta.headers["X-Token-Renovado"]
    payload = jwt.decode(nuevo_token, settings.jwt_secreto, algorithms=["HS256"])
    assert payload["sub"] == str(respuesta.json()["id"])
