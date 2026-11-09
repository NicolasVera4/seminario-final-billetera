from app.servicios.comprobantes import LIMITE_CARACTERES_BLOQUE, dividir_en_bloques


def test_paginas_cortas_se_combinan_en_un_solo_bloque():
    paginas = ["pagina uno", "pagina dos", "pagina tres"]

    bloques = dividir_en_bloques(paginas, limite=1000)

    assert bloques == ["pagina uno\npagina dos\npagina tres"]


def test_paginas_que_superan_el_limite_se_dividen_en_varios_bloques():
    pagina_grande = "x" * 700
    paginas = [pagina_grande, pagina_grande, pagina_grande]

    bloques = dividir_en_bloques(paginas, limite=1000)

    assert len(bloques) == 3
    assert all(len(b) <= 1000 for b in bloques)


def test_no_se_pierde_ni_se_duplica_texto_al_dividir():
    paginas = ["a" * 400, "b" * 400, "c" * 400, "d" * 400]

    bloques = dividir_en_bloques(paginas, limite=1000)

    texto_reunido = "".join(b.replace("\n", "") for b in bloques)
    assert texto_reunido.count("a") == 400
    assert texto_reunido.count("b") == 400
    assert texto_reunido.count("c") == 400
    assert texto_reunido.count("d") == 400


def test_pagina_vacia_no_genera_bloque_vacio():
    bloques = dividir_en_bloques(["contenido", "", "   ", "mas contenido"], limite=1000)

    assert "" not in bloques
    assert all(b.strip() for b in bloques)


def test_limite_por_defecto_es_conservador_respecto_al_tpm_de_groq():
    # Groq (plan actual) limita a 8000 tokens por minuto; ~4 caracteres por token en espanol
    # mas el resto del prompt (instrucciones, catalogo) deja margen para un bloque de este tamano.
    assert LIMITE_CARACTERES_BLOQUE <= 6000
