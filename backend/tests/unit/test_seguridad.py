from app.servicios.seguridad import hash_contrasena, verificar_contrasena


def test_hash_contrasena_usa_bcrypt_factor_12():
    hash_resultante = hash_contrasena("contrasena123")

    assert hash_resultante.startswith("$2b$12$")


def test_verificar_contrasena_correcta():
    hash_resultante = hash_contrasena("contrasena123")

    assert verificar_contrasena("contrasena123", hash_resultante) is True


def test_verificar_contrasena_incorrecta():
    hash_resultante = hash_contrasena("contrasena123")

    assert verificar_contrasena("otra-contrasena", hash_resultante) is False
