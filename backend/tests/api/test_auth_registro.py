def _datos_validos(correo="luciano.vera@mail.com"):
    return {"nombre": "Luciano Vera", "correo": correo, "contrasena": "contrasena123"}


def test_hu01_ca4_datos_validos_crea_cuenta(cliente):
    respuesta = cliente.post("/api/auth/registro", json=_datos_validos())

    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert cuerpo["correo"] == "luciano.vera@mail.com"
    assert cuerpo["nombre"] == "Luciano Vera"
    assert "contrasena" not in cuerpo
    assert "contrasena_hash" not in cuerpo


def test_hu01_ca1_correo_ya_registrado(cliente):
    cliente.post("/api/auth/registro", json=_datos_validos())

    respuesta = cliente.post("/api/auth/registro", json=_datos_validos())

    assert respuesta.status_code == 409


def test_hu01_ca2_contrasena_menos_de_8_caracteres(cliente):
    datos = _datos_validos()
    datos["contrasena"] = "1234567"

    respuesta = cliente.post("/api/auth/registro", json=datos)

    assert respuesta.status_code == 422


def test_hu01_ca2_contrasena_mas_de_64_caracteres(cliente):
    datos = _datos_validos()
    datos["contrasena"] = "a" * 65

    respuesta = cliente.post("/api/auth/registro", json=datos)

    assert respuesta.status_code == 422


def test_hu01_ca2_contrasena_en_el_limite_valido(cliente):
    datos = _datos_validos()
    datos["contrasena"] = "a" * 64

    respuesta = cliente.post("/api/auth/registro", json=datos)

    assert respuesta.status_code == 201


def test_hu01_ca3_campo_obligatorio_vacio_nombre(cliente):
    datos = _datos_validos()
    datos["nombre"] = ""

    respuesta = cliente.post("/api/auth/registro", json=datos)

    assert respuesta.status_code == 422


def test_hu01_ca3_campo_obligatorio_faltante_correo(cliente):
    datos = _datos_validos()
    del datos["correo"]

    respuesta = cliente.post("/api/auth/registro", json=datos)

    assert respuesta.status_code == 422


def test_hu01_ca3_campo_obligatorio_faltante_contrasena(cliente):
    datos = _datos_validos()
    del datos["contrasena"]

    respuesta = cliente.post("/api/auth/registro", json=datos)

    assert respuesta.status_code == 422


def test_hash_bcrypt_factor_12(cliente, sesion_bd):
    cliente.post("/api/auth/registro", json=_datos_validos())

    from app.modelos.usuario import Usuario

    usuario = sesion_bd.query(Usuario).filter_by(correo="luciano.vera@mail.com").one()
    assert usuario.contrasena_hash.startswith("$2b$12$")


def test_correo_normalizado_a_minusculas(cliente, sesion_bd):
    cliente.post("/api/auth/registro", json=_datos_validos(correo="Luciano.Vera@Mail.COM"))

    from app.modelos.usuario import Usuario

    usuario = sesion_bd.query(Usuario).filter_by(correo="luciano.vera@mail.com").one_or_none()
    assert usuario is not None
