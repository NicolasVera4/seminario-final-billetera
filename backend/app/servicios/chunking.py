def dividir_en_fragmentos(texto: str, tamano: int = 800, solapamiento: int = 100) -> list[str]:
    if len(texto) <= tamano:
        return [texto]

    fragmentos = []
    paso = tamano - solapamiento
    inicio = 0
    while inicio < len(texto):
        fragmentos.append(texto[inicio : inicio + tamano])
        if inicio + tamano >= len(texto):
            break
        inicio += paso
    return fragmentos
