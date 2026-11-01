from app.proveedores.transcripcion import ErrorTranscripcion
from tests.ayudantes import auth, promover_a_administrador, registrar_y_loguear


def _subir(cliente, token, contenido=b"audio falso", content_type="audio/webm", nombre="audio.webm"):
    return cliente.post(
        "/api/voz/transcribir",
        files={"archivo": (nombre, contenido, content_type)},
        headers=auth(token),
    )


def test_hu11_ca1_audio_grabado_se_transcribe_a_texto(cliente, transcriptor):
    token = registrar_y_loguear(cliente)
    transcriptor.respuesta_transcribir = "Gasté 15000 en el súper con débito"

    respuesta = _subir(cliente, token)

    assert respuesta.status_code == 200
    assert respuesta.json()["texto"] == "Gasté 15000 en el súper con débito"


def test_hu11_ca4_audio_que_no_se_puede_transcribir_avisa_y_sugiere_repetir_o_escribir(cliente, transcriptor):
    token = registrar_y_loguear(cliente)
    transcriptor.respuesta_transcribir = ErrorTranscripcion()

    respuesta = _subir(cliente, token)

    assert respuesta.status_code == 422
    assert "transcribir" in respuesta.json()["detail"].lower()


def test_formato_no_admitido_devuelve_415(cliente):
    token = registrar_y_loguear(cliente)

    respuesta = _subir(cliente, token, content_type="video/mp4", nombre="audio.mp4")

    assert respuesta.status_code == 415


def test_requiere_autenticacion(cliente):
    respuesta = cliente.post(
        "/api/voz/transcribir", files={"archivo": ("audio.webm", b"audio falso", "audio/webm")}
    )

    assert respuesta.status_code == 401


def test_administrador_no_puede_transcribir_audio(cliente, sesion_bd):
    registrar_y_loguear(cliente, nombre="Admin", correo="admin@mail.com")
    promover_a_administrador(sesion_bd, "admin@mail.com")
    token_admin = cliente.post(
        "/api/auth/login", json={"correo": "admin@mail.com", "contrasena": "contrasena123"}
    ).json()["access_token"]

    respuesta = _subir(cliente, token_admin)

    assert respuesta.status_code == 403
