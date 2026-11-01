from pathlib import Path

import pytest

from app.proveedores.transcripcion import TranscriptorWhisper

pytestmark = pytest.mark.integracion

RUTA_AUDIO = Path(__file__).parent.parent / "fixtures" / "audio" / "gasto.ogg"


@pytest.mark.skipif(not RUTA_AUDIO.exists(), reason="Falta tests/fixtures/audio/gasto.ogg")
def test_hu11_ca1_transcribe_un_audio_real_con_whisper():
    contenido = RUTA_AUDIO.read_bytes()

    texto = TranscriptorWhisper().transcribir(contenido)

    assert texto.strip() != ""
