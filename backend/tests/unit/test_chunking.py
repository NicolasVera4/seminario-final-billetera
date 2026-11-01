from app.servicios.chunking import dividir_en_fragmentos


def test_texto_mas_corto_que_el_tamano_devuelve_un_solo_fragmento():
    texto = "Un texto corto de referencia."

    fragmentos = dividir_en_fragmentos(texto, tamano=800, solapamiento=100)

    assert fragmentos == [texto]


def test_divide_en_fragmentos_del_tamano_pedido():
    texto = "a" * 2000

    fragmentos = dividir_en_fragmentos(texto, tamano=800, solapamiento=100)

    assert len(fragmentos) > 1
    assert all(len(f) <= 800 for f in fragmentos)


def test_fragmentos_consecutivos_se_solapan():
    texto = "0123456789" * 200  # 2000 caracteres

    fragmentos = dividir_en_fragmentos(texto, tamano=800, solapamiento=100)

    # el final del primer fragmento coincide con el inicio del segundo (solapamiento)
    assert fragmentos[0][-100:] == fragmentos[1][:100]


def test_reconstruye_el_texto_completo_sin_perder_contenido():
    texto = "x" * 1750

    fragmentos = dividir_en_fragmentos(texto, tamano=800, solapamiento=100)

    # el ultimo fragmento llega hasta el final del texto original
    assert texto.endswith(fragmentos[-1])
    assert fragmentos[0] == texto[:800]
