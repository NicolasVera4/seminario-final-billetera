import pytest

from app.proveedores.transcripcion import ErrorTranscripcion
from app.servicios.ingesta.voz import ErrorAudio, transcribir_audio
from tests.dobles import FakeTranscriptor


def test_hu11_ca1_devuelve_el_texto_transcripto():
    transcriptor = FakeTranscriptor()
    transcriptor.respuesta_transcribir = "Gasté 15000 en el súper con débito"

    texto = transcribir_audio(transcriptor, b"audio falso", "audio/webm")

    assert texto == "Gasté 15000 en el súper con débito"
    assert transcriptor.llamadas == [b"audio falso"]


def test_formato_no_admitido_devuelve_415():
    transcriptor = FakeTranscriptor()

    with pytest.raises(ErrorAudio) as excinfo:
        transcribir_audio(transcriptor, b"contenido", "video/mp4")

    assert excinfo.value.status_code == 415


def test_audio_que_supera_el_tamano_maximo_devuelve_413():
    transcriptor = FakeTranscriptor()
    contenido = b"a" * (10 * 1024 * 1024 + 1)

    with pytest.raises(ErrorAudio) as excinfo:
        transcribir_audio(transcriptor, contenido, "audio/webm")

    assert excinfo.value.status_code == 413


def test_hu11_ca4_el_proveedor_no_puede_transcribir_devuelve_422():
    transcriptor = FakeTranscriptor()
    transcriptor.respuesta_transcribir = ErrorTranscripcion()

    with pytest.raises(ErrorAudio) as excinfo:
        transcribir_audio(transcriptor, b"audio falso", "audio/ogg")

    assert excinfo.value.status_code == 422


def test_hu11_ca4_transcripcion_vacia_devuelve_422():
    transcriptor = FakeTranscriptor()
    transcriptor.respuesta_transcribir = "   "

    with pytest.raises(ErrorAudio) as excinfo:
        transcribir_audio(transcriptor, b"audio falso", "audio/mpeg")

    assert excinfo.value.status_code == 422
