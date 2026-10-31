from app.modelos.usuario import Usuario
from tests.ayudantes import CORREO_DEFECTO, datos_registro


def test_hu01_ca4_datos_validos_crea_cuenta(cliente):
    respuesta = cliente.post("/api/auth/registro", json=datos_registro())

    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert cuerpo["correo"] == CORREO_DEFECTO
    assert cuerpo["nombre"] == "Luciano Vera"
    assert "contrasena" not in cuerpo
    assert "contrasena_hash" not in cuerpo


def test_hu01_ca1_correo_ya_registrado(cliente):
    cliente.post("/api/auth/registro", json=datos_registro())

    respuesta = cliente.post("/api/auth/registro", json=datos_registro())

    assert respuesta.status_code == 409


def test_hu01_ca2_contrasena_menos_de_8_caracteres(cliente):
    datos = datos_registro(contrasena="1234567")

    respuesta = cliente.post("/api/auth/registro", json=datos)

    assert respuesta.status_code == 422


def test_hu01_ca2_contrasena_mas_de_64_caracteres(cliente):
    datos = datos_registro(contrasena="a" * 65)

    respuesta = cliente.post("/api/auth/registro", json=datos)

    assert respuesta.status_code == 422


def test_hu01_ca2_contrasena_en_el_limite_valido(cliente):
    datos = datos_registro(contrasena="a" * 64)

    respuesta = cliente.post("/api/auth/registro", json=datos)

    assert respuesta.status_code == 201


def test_hu01_ca3_campo_obligatorio_vacio_nombre(cliente):
    datos = datos_registro(nombre="")

    respuesta = cliente.post("/api/auth/registro", json=datos)

    assert respuesta.status_code == 422


def test_hu01_ca3_campo_obligatorio_faltante_correo(cliente):
    datos = datos_registro()
    del datos["correo"]

    respuesta = cliente.post("/api/auth/registro", json=datos)

    assert respuesta.status_code == 422


def test_hu01_ca3_campo_obligatorio_faltante_contrasena(cliente):
    datos = datos_registro()
    del datos["contrasena"]

    respuesta = cliente.post("/api/auth/registro", json=datos)

    assert respuesta.status_code == 422


def test_hash_bcrypt_factor_12(cliente, sesion_bd):
    cliente.post("/api/auth/registro", json=datos_registro())

    usuario = sesion_bd.query(Usuario).filter_by(correo=CORREO_DEFECTO).one()
    assert usuario.contrasena_hash.startswith("$2b$12$")


def test_correo_normalizado_a_minusculas(cliente, sesion_bd):
    cliente.post("/api/auth/registro", json=datos_registro(correo="Luciano.Vera@Mail.COM"))

    usuario = sesion_bd.query(Usuario).filter_by(correo=CORREO_DEFECTO).one_or_none()
    assert usuario is not None
